import rclpy
from rclpy.node import Node
from rclpy.time import Time

import numpy as np
import torch
import torch.nn as nn
from scipy.spatial.transform import Rotation as R
import time

from nav_msgs.msg import Odometry
from autoware_auto_planning_msgs.msg import Trajectory

# ======================================================================================
# Model Definition (Copied from nn_planner_dev/model.py)
# ======================================================================================

class SimplerVelocityLSTM(nn.Module):
    """
    A simpler version that directly maps the entire input sequence to output sequence.
    This approach is more straightforward and might work better initially.
    """
    def __init__(self, input_size=13, hidden_size=256, num_layers=2, output_seq_len=50, dropout=0.2):
        super(SimplerVelocityLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        self.output_layer = nn.Linear(hidden_size, output_seq_len)
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.lstm.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.lstm.hidden_size).to(x.device)
        lstm_out, _ = self.lstm(x, (h0, c0))
        last_output = lstm_out[:, -1, :]
        predictions = self.output_layer(last_output)
        return predictions.unsqueeze(-1)

# ======================================================================================
# Main ROS2 Node
# ======================================================================================

class NNPlannerNode(Node):
    def __init__(self):
        super().__init__('nn_planner_node')

        self.declare_parameter('model_path', '')
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        
        # 添加时空域映射相关参数
        self.declare_parameter('prediction_horizon_meters', 200.0)
        self.declare_parameter('transition_zone_length', 20)
        self.declare_parameter('dt', 0.1)
        self.declare_parameter('max_acceleration', 2.0)
        self.declare_parameter('enable_debug_logs', True)
        
        # 获取参数
        self.prediction_horizon_meters = self.get_parameter('prediction_horizon_meters').get_parameter_value().double_value
        self.transition_zone_length = self.get_parameter('transition_zone_length').get_parameter_value().integer_value
        self.dt = self.get_parameter('dt').get_parameter_value().double_value
        self.max_acceleration = self.get_parameter('max_acceleration').get_parameter_value().double_value
        self.enable_debug_logs = self.get_parameter('enable_debug_logs').get_parameter_value().bool_value
        
        self.trajectory_pub = self.create_publisher(Trajectory, "/planning/scenario_planning/trajectory", 1)
        self.kinematic_state_sub = self.create_subscription(Odometry, "/localization/kinematic_state", self._kinematic_state_callback, 1)
        self.original_trajectory_sub = self.create_subscription(Trajectory, "/planning/scenario_planning/original_trajectory", self._original_trajectory_callback, 1)

        self.current_odometry = None
        self.static_path_pts = None
        self.original_trajectory_msg = None  # 保存原始轨迹消息
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 时空域映射相关变量
        self.velocity_cache = {}
        self.last_update_position = None
        self.planning_start_time = None

        self.get_logger().info('NN Planner Node initializing with Time-Space Domain Mapping...')
        self.get_logger().info(f'Prediction horizon: {self.prediction_horizon_meters}m')
        self.get_logger().info(f'Transition zone length: {self.transition_zone_length} points')
        self.get_logger().info(f'Time step: {self.dt}s')
        self.get_logger().info(f'Max acceleration: {self.max_acceleration} m/s²')
        
        if model_path:
            self.load_model(model_path)
        else:
            self.get_logger().error("FATAL: Model path not provided. Cannot operate.")

        self.timer = self.create_timer(0.1, self.planner_callback) # 10 Hz

    def load_model(self, model_path):
        self.get_logger().info(f"--- Loading LSTM model from: {model_path} ---")
        try:
            self.model = SimplerVelocityLSTM().to(self.device)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            self.get_logger().info("--- LSTM model loaded successfully and set to evaluation mode. ---")
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {e}")
            self.model = None

    def _kinematic_state_callback(self, msg: Odometry):
        self.current_odometry = msg

    def _original_trajectory_callback(self, msg: Trajectory):
        self.get_logger().info(f"Received static path with {len(msg.points)} points.", once=True)
        self.static_path_pts = np.array([[p.pose.position.x, p.pose.position.y] for p in msg.points])
        self.original_trajectory_msg = msg  # 保存完整的原始轨迹

    def planner_callback(self):
        """
        使用时空域映射+路径拼接的主规划回调函数
        """
        self.planning_start_time = time.time()
        
        if self.static_path_pts is None or self.current_odometry is None or self.model is None or self.original_trajectory_msg is None:
            self.get_logger().info("Waiting for static path, odometry, original trajectory, and a loaded model...", throttle_duration_sec=5)
            return

        if self.enable_debug_logs:
            self.get_logger().info("=== TIME-SPACE DOMAIN MAPPING PLANNING CYCLE START ===")

        # 步骤1: LSTM推理
        predicted_velocities = self.run_model_inference()
        if predicted_velocities is None:
            if self.enable_debug_logs:
                self.get_logger().error("LSTM inference failed, falling back to original trajectory")
            self.publish_fallback_trajectory()
            return

        # 步骤2: 时空域映射
        velocity_mapping = self.time_to_space_mapping(predicted_velocities)
        if not velocity_mapping:
            if self.enable_debug_logs:
                self.get_logger().error("Time-space mapping failed, falling back to original trajectory")
            self.publish_fallback_trajectory()
            return

        # 步骤3: 构建混合轨迹
        hybrid_trajectory = self.create_hybrid_trajectory(velocity_mapping)
        if hybrid_trajectory is None:
            if self.enable_debug_logs:
                self.get_logger().error("Hybrid trajectory creation failed, falling back to original trajectory")
            self.publish_fallback_trajectory()
            return

        # 步骤4: 发布轨迹
        self.trajectory_pub.publish(hybrid_trajectory)
        
        planning_time = time.time() - self.planning_start_time
        if self.enable_debug_logs:
            self.get_logger().info(f"=== PLANNING CYCLE COMPLETE: {planning_time*1000:.2f}ms ===")

    def time_to_space_mapping(self, predicted_velocities):
        """
        将时间域的LSTM预测转换为空间域的速度映射
        """
        if self.enable_debug_logs:
            self.get_logger().info(f"Starting time-to-space mapping for {len(predicted_velocities)} velocity predictions")

        current_position_idx = self._find_closest_path_idx(self.current_odometry, self.static_path_pts)
        current_velocity = self.current_odometry.twist.twist.linear.x

        if self.enable_debug_logs:
            self.get_logger().info(f"Current position index: {current_position_idx}, current velocity: {current_velocity:.2f} m/s")

        # 确保速度连续性
        corrected_velocities = self.ensure_velocity_continuity(current_velocity, predicted_velocities)
        
        if self.enable_debug_logs:
            self.get_logger().info(f"Velocity correction applied. Original range: [{predicted_velocities.min():.2f}, {predicted_velocities.max():.2f}]")
            self.get_logger().info(f"Corrected range: [{np.array(corrected_velocities).min():.2f}, {np.array(corrected_velocities).max():.2f}]")

        # 计算累积距离
        cumulative_distances = [0]
        for i, velocity in enumerate(corrected_velocities):
            distance_increment = velocity * self.dt
            cumulative_distances.append(cumulative_distances[-1] + distance_increment)

        if self.enable_debug_logs:
            total_predicted_distance = cumulative_distances[-1]
            self.get_logger().info(f"Total predicted travel distance: {total_predicted_distance:.2f}m over {len(corrected_velocities)} time steps")

        # 映射到空间点
        space_velocity_map = {}
        valid_mappings = 0
        
        for i, total_distance in enumerate(cumulative_distances[1:]):  # 跳过起始点
            target_space_index = self._get_path_point_at_distance(self.static_path_pts, current_position_idx, total_distance)
            
            if target_space_index is not None and target_space_index < len(self.static_path_pts):
                space_velocity_map[target_space_index] = corrected_velocities[i]
                valid_mappings += 1
            else:
                if self.enable_debug_logs and i < 5:  # 只记录前几个失败的映射
                    self.get_logger().warn(f"Time step {i}: distance {total_distance:.2f}m mapped to invalid index {target_space_index}")

        if self.enable_debug_logs:
            self.get_logger().info(f"Space mapping complete: {valid_mappings}/{len(corrected_velocities)} valid mappings")
            if valid_mappings > 0:
                mapped_indices = list(space_velocity_map.keys())
                self.get_logger().info(f"Mapped index range: [{min(mapped_indices)}, {max(mapped_indices)}]")

        return space_velocity_map

    def ensure_velocity_continuity(self, current_velocity, predicted_velocities):
        """
        确保速度序列的物理可行性
        """
        corrected_velocities = []
        last_velocity = current_velocity

        continuity_violations = 0
        
        for i, predicted_v in enumerate(predicted_velocities):
            max_delta_v = self.max_acceleration * self.dt
            
            if abs(predicted_v - last_velocity) > max_delta_v:
                continuity_violations += 1
                if predicted_v > last_velocity:
                    corrected_v = last_velocity + max_delta_v
                else:
                    corrected_v = last_velocity - max_delta_v
                
                if self.enable_debug_logs and continuity_violations <= 3:  # 只记录前3个违规
                    self.get_logger().info(f"Velocity continuity correction at step {i}: {predicted_v:.2f} -> {corrected_v:.2f} m/s")
            else:
                corrected_v = predicted_v
                
            corrected_velocities.append(corrected_v)
            last_velocity = corrected_v

        if self.enable_debug_logs:
            self.get_logger().info(f"Velocity continuity check: {continuity_violations}/{len(predicted_velocities)} violations corrected")

        return corrected_velocities

    def create_hybrid_trajectory(self, velocity_mapping):
        """
        创建混合轨迹：LSTM预测区域 + 平滑过渡 + 原始CSV区域
        """
        if self.enable_debug_logs:
            self.get_logger().info("Creating hybrid trajectory with time-space mapped velocities")

        current_position_idx = self._find_closest_path_idx(self.current_odometry, self.static_path_pts)
        
        # 计算发布范围
        prediction_distance_points = int(self.prediction_horizon_meters / 2.0)  # 假设点间距2米
        end_idx = min(current_position_idx + prediction_distance_points, len(self.original_trajectory_msg.points))
        
        if self.enable_debug_logs:
            self.get_logger().info(f"Trajectory segment: points {current_position_idx} to {end_idx} (total: {end_idx - current_position_idx})")

        # 创建新轨迹
        output_trajectory = Trajectory()
        output_trajectory.header.stamp = self.get_clock().now().to_msg()
        output_trajectory.header.frame_id = "map"

        lstm_applied_count = 0
        transition_applied_count = 0
        original_used_count = 0

        for i in range(current_position_idx, end_idx):
            # 复制原始轨迹点
            original_point = self.original_trajectory_msg.points[i - current_position_idx] if i - current_position_idx < len(self.original_trajectory_msg.points) else self.original_trajectory_msg.points[-1]
            
            traj_point = type(original_point)()
            traj_point.pose = original_point.pose
            traj_point.lateral_velocity_mps = original_point.lateral_velocity_mps
            traj_point.acceleration_mps2 = original_point.acceleration_mps2
            traj_point.heading_rate_rps = original_point.heading_rate_rps

            # 决定使用哪种速度
            if i in velocity_mapping:
                # 使用LSTM预测速度
                traj_point.longitudinal_velocity_mps = velocity_mapping[i]
                lstm_applied_count += 1
            else:
                # 检查是否在过渡区域
                lstm_indices = list(velocity_mapping.keys())
                if lstm_indices:
                    max_lstm_idx = max(lstm_indices)
                    if max_lstm_idx < i <= max_lstm_idx + self.transition_zone_length:
                        # 平滑过渡区域
                        transition_progress = (i - max_lstm_idx) / self.transition_zone_length
                        lstm_velocity = velocity_mapping[max_lstm_idx]
                        original_velocity = original_point.longitudinal_velocity_mps
                        
                        mixed_velocity = (1 - transition_progress) * lstm_velocity + transition_progress * original_velocity
                        traj_point.longitudinal_velocity_mps = mixed_velocity
                        transition_applied_count += 1
                        
                        if self.enable_debug_logs and transition_applied_count <= 3:
                            self.get_logger().info(f"Transition at index {i}: progress={transition_progress:.2f}, mixed_vel={mixed_velocity:.2f}")
                    else:
                        # 使用原始速度
                        traj_point.longitudinal_velocity_mps = original_point.longitudinal_velocity_mps
                        original_used_count += 1
                else:
                    # 没有LSTM预测，使用原始速度
                    traj_point.longitudinal_velocity_mps = original_point.longitudinal_velocity_mps
                    original_used_count += 1

            output_trajectory.points.append(traj_point)

        if self.enable_debug_logs:
            total_points = len(output_trajectory.points)
            self.get_logger().info(f"Hybrid trajectory created: {total_points} points")
            self.get_logger().info(f"  - LSTM applied: {lstm_applied_count} points ({lstm_applied_count/total_points*100:.1f}%)")
            self.get_logger().info(f"  - Transition zone: {transition_applied_count} points ({transition_applied_count/total_points*100:.1f}%)")
            self.get_logger().info(f"  - Original CSV: {original_used_count} points ({original_used_count/total_points*100:.1f}%)")

        return output_trajectory

    def publish_fallback_trajectory(self):
        """
        发布后备轨迹（使用原始CSV速度）
        """
        if self.original_trajectory_msg is not None:
            fallback_trajectory = Trajectory()
            fallback_trajectory.header.stamp = self.get_clock().now().to_msg()
            fallback_trajectory.header.frame_id = "map"
            
            current_position_idx = self._find_closest_path_idx(self.current_odometry, self.static_path_pts)
            prediction_distance_points = int(self.prediction_horizon_meters / 2.0)
            end_idx = min(current_position_idx + prediction_distance_points, len(self.original_trajectory_msg.points))
            
            for i in range(current_position_idx, end_idx):
                if i - current_position_idx < len(self.original_trajectory_msg.points):
                    fallback_trajectory.points.append(self.original_trajectory_msg.points[i - current_position_idx])
            
            self.trajectory_pub.publish(fallback_trajectory)
            
            if self.enable_debug_logs:
                self.get_logger().warn(f"Published fallback trajectory with {len(fallback_trajectory.points)} points")

    def run_model_inference(self):
        """
        运行LSTM模型推理，包含详细的调试信息
        """
        if self.enable_debug_logs:
            self.get_logger().info("Starting LSTM model inference...")

        # 1. Compute the feature vector for the current state
        features = self._compute_features_now()
        if features is None:
            if self.enable_debug_logs:
                self.get_logger().error("Feature computation failed")
            return None

        if self.enable_debug_logs:
            self.get_logger().info(f"Feature vector computed: {len(features)} features")
            self.get_logger().info(f"Feature range: [{features.min():.3f}, {features.max():.3f}]")
            # 记录关键特征
            self.get_logger().info(f"  - Current velocity: {features[0]:.2f} m/s")
            self.get_logger().info(f"  - Angular velocity: {features[1]:.3f} rad/s")
            self.get_logger().info(f"  - Distance from centerline: {features[2]:.3f} m")
            self.get_logger().info(f"  - Heading error: {features[3]:.3f} rad")

        # 2. Create a dummy sequence for the model input
        # The model was trained on sequences, but for real-time inference,
        # we use the most current feature vector and replicate it.
        input_seq_len = 149 # Based on the training script (3s at ~50Hz)
        input_data = np.tile(features, (input_seq_len, 1))
        
        if self.enable_debug_logs:
            self.get_logger().info(f"Input sequence created: shape {input_data.shape}")
        
        # 3. Convert to tensor and add batch dimension
        input_tensor = torch.from_numpy(input_data).float().unsqueeze(0).to(self.device)
        
        if self.enable_debug_logs:
            self.get_logger().info(f"Input tensor: shape {input_tensor.shape}, device {input_tensor.device}")

        # 4. Run inference
        inference_start_time = time.time()
        try:
            with torch.no_grad():
                predictions_tensor = self.model(input_tensor)
        except Exception as e:
            if self.enable_debug_logs:
                self.get_logger().error(f"LSTM model inference failed: {e}")
            return None
            
        inference_time = time.time() - inference_start_time
        
        if self.enable_debug_logs:
            self.get_logger().info(f"LSTM inference completed in {inference_time*1000:.2f}ms")
            self.get_logger().info(f"Output tensor shape: {predictions_tensor.shape}")
        
        # 5. Convert back to numpy array and flatten
        predicted_velocities = predictions_tensor.squeeze().cpu().numpy()
        
        if self.enable_debug_logs:
            self.get_logger().info(f"Predicted velocities: {len(predicted_velocities)} values")
            self.get_logger().info(f"Velocity prediction range: [{predicted_velocities.min():.2f}, {predicted_velocities.max():.2f}] m/s")
            self.get_logger().info(f"Mean predicted velocity: {predicted_velocities.mean():.2f} m/s")
            
            # 显示前5个和后5个预测值
            if len(predicted_velocities) >= 10:
                first_5 = predicted_velocities[:5]
                last_5 = predicted_velocities[-5:]
                self.get_logger().info(f"First 5 predictions: {[f'{v:.2f}' for v in first_5]}")
                self.get_logger().info(f"Last 5 predictions: {[f'{v:.2f}' for v in last_5]}")
            
        return predicted_velocities

    # ======================================================================================
    # Feature Engineering (Copied from nn_planner_dev/post_process.py)
    # ======================================================================================
    
    def _compute_features_now(self):
        state_pose = self.current_odometry.pose.pose
        state_twist = self.current_odometry.twist.twist
        
        # Ego state
        current_velocity_x = state_twist.linear.x
        current_angular_velocity_z = state_twist.angular.z
        
        # Path-relative features
        closest_idx = self._find_closest_path_idx(self.current_odometry, self.static_path_pts)
        closest_pt = self.static_path_pts[closest_idx]
        
        distance = np.linalg.norm(np.array([state_pose.position.x, state_pose.position.y]) - closest_pt)
        path_vec = self.static_path_pts[min(closest_idx + 1, len(self.static_path_pts)-1)] - self.static_path_pts[max(closest_idx - 1, 0)]
        ego_vec = np.array([state_pose.position.x, state_pose.position.y]) - closest_pt
        cross_prod_z = np.cross(path_vec, ego_vec)
        distance_from_centerline = np.copysign(distance, cross_prod_z)
        
        quat = state_pose.orientation
        ego_yaw = R.from_quat([quat.x, quat.y, quat.z, quat.w]).as_euler('xyz', degrees=False)[2]
        path_yaw = np.arctan2(path_vec[1], path_vec[0])
        heading_error = (ego_yaw - path_yaw + np.pi) % (2 * np.pi) - np.pi
        
        # Curvature fingerprint
        sample_distances = [-25, -15, -10, -5, 0, 5, 10, 15, 25]
        curvature_features = []
        for dist in sample_distances:
            sample_idx = self._get_path_point_at_distance(self.static_path_pts, closest_idx, dist)
            p2 = self.static_path_pts[sample_idx]
            p1 = self.static_path_pts[max(0, sample_idx - 5)]
            p3 = self.static_path_pts[min(len(self.static_path_pts) - 1, sample_idx + 5)]
            curvature = self._calculate_curvature(p1, p2, p3) if not (np.array_equal(p1, p2) or np.array_equal(p2, p3)) else 0.0
            curvature_features.append(curvature)
            
        return np.concatenate([[current_velocity_x, current_angular_velocity_z, distance_from_centerline, heading_error], curvature_features])

    def _find_closest_path_idx(self, state, path_pts):
        pos = state.pose.pose.position
        return np.argmin(np.linalg.norm(path_pts - np.array([pos.x, pos.y]), axis=1))

    def _get_path_point_at_distance(self, path_pts, start_idx, distance):
        if distance == 0: return start_idx
        current_dist = 0.0
        if distance > 0:
            for i in range(start_idx, len(path_pts) - 1):
                current_dist += np.linalg.norm(path_pts[i+1] - path_pts[i])
                if current_dist >= distance: return i + 1
            return len(path_pts) - 1
        else:
            for i in range(start_idx, 0, -1):
                current_dist += np.linalg.norm(path_pts[i-1] - path_pts[i])
                if current_dist >= abs(distance): return i - 1
            return 0

    def _calculate_curvature(self, p1, p2, p3):
        a, b, c = np.linalg.norm(p2 - p3), np.linalg.norm(p1 - p3), np.linalg.norm(p1 - p2)
        if a * b * c == 0: return 0.0
        s = (a + b + c) / 2
        area_sq = s * (s - a) * (s - b) * (s - c)
        if area_sq <= 0: return 0.0
        area = np.sqrt(area_sq)
        curvature = (4 * area) / (a * b * c)
        cross_product_z = (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])
        return np.copysign(curvature, cross_product_z)


def main(args=None):
    rclpy.init(args=args)
    node = NNPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main() 