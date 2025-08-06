#!/usr/bin/env python3
"""
训练数据收集脚本
功能：
1. 订阅车辆当前状态 (/localization/kinematic_state)
2. 订阅目标轨迹 (/planning/scenario_planning/trajectory)
3. 记录数据用于神经网络训练
4. 保存为适合训练的格式
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from autoware_auto_planning_msgs.msg import Trajectory
import numpy as np
import pandas as pd
import json
from datetime import datetime
import tf_transformations
import time

class TrainingDataCollector(Node):
    def __init__(self):
        super().__init__('training_data_collector')
        
        # 数据存储
        self.collected_data = []
        self.current_odometry = None
        self.current_trajectory = None
        self.start_time = time.time()
        
        # 数据收集参数
        self.collection_rate = 10.0  # Hz
        self.max_collection_time = 300.0  # 5分钟最大收集时间
        
        # 订阅者
        self.odom_subscriber = self.create_subscription(
            Odometry,
            '/localization/kinematic_state',
            self.odometry_callback,
            10
        )
        
        self.trajectory_subscriber = self.create_subscription(
            Trajectory,
            '/planning/scenario_planning/trajectory',
            self.trajectory_callback,
            10
        )
        
        # 定时器用于数据收集
        self.timer = self.create_timer(
            1.0 / self.collection_rate,
            self.collect_data_callback
        )
        
        self.get_logger().info("训练数据收集器已启动")
        self.get_logger().info(f"数据收集频率: {self.collection_rate} Hz")
        self.get_logger().info(f"最大收集时间: {self.max_collection_time} 秒")
        
    def odometry_callback(self, msg):
        """车辆状态回调"""
        self.current_odometry = msg
        
    def trajectory_callback(self, msg):
        """轨迹回调"""
        self.current_trajectory = msg
        
    def quaternion_to_yaw(self, quat):
        """四元数转欧拉角"""
        euler = tf_transformations.euler_from_quaternion([
            quat.x, quat.y, quat.z, quat.w
        ])
        return euler[2]  # yaw角
        
    def collect_data_callback(self):
        """数据收集回调"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # 检查是否超时
        if elapsed_time > self.max_collection_time:
            self.get_logger().info("达到最大收集时间，停止收集")
            self.save_collected_data()
            return
            
        # 检查数据是否可用
        if self.current_odometry is None or self.current_trajectory is None:
            return
            
        if len(self.current_trajectory.points) == 0:
            return
            
        try:
            # 提取车辆当前状态
            pose = self.current_odometry.pose.pose
            twist = self.current_odometry.twist.twist
            
            # 车辆位置
            vehicle_x = pose.position.x
            vehicle_y = pose.position.y
            vehicle_yaw = self.quaternion_to_yaw(pose.orientation)
            
            # 车辆速度
            vehicle_vx = twist.linear.x
            vehicle_vy = twist.linear.y
            vehicle_omega = twist.angular.z
            
            # 查找最近的轨迹点
            min_distance = float('inf')
            closest_point_idx = 0
            
            for i, point in enumerate(self.current_trajectory.points):
                dx = point.pose.position.x - vehicle_x
                dy = point.pose.position.y - vehicle_y
                distance = np.sqrt(dx*dx + dy*dy)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_point_idx = i
                    
            # 提取未来轨迹点（接下来20个点）
            future_points = []
            max_future_points = min(20, len(self.current_trajectory.points) - closest_point_idx)
            
            for i in range(max_future_points):
                point_idx = closest_point_idx + i
                if point_idx < len(self.current_trajectory.points):
                    point = self.current_trajectory.points[point_idx]
                    
                    # 转换为相对坐标
                    relative_x = point.pose.position.x - vehicle_x
                    relative_y = point.pose.position.y - vehicle_y
                    
                    # 旋转到车辆坐标系
                    cos_yaw = np.cos(-vehicle_yaw)
                    sin_yaw = np.sin(-vehicle_yaw)
                    
                    local_x = relative_x * cos_yaw - relative_y * sin_yaw
                    local_y = relative_x * sin_yaw + relative_y * cos_yaw
                    
                    future_points.append({
                        'local_x': local_x,
                        'local_y': local_y,
                        'target_speed': point.longitudinal_velocity_mps
                    })
            
            # 如果未来点不足20个，用最后一个点填充
            while len(future_points) < 20:
                if future_points:
                    last_point = future_points[-1].copy()
                    # 向前延伸
                    last_point['local_x'] += 1.0
                    future_points.append(last_point)
                else:
                    # 如果没有未来点，创建直线前进的点
                    future_points.append({
                        'local_x': 1.0,
                        'local_y': 0.0,
                        'target_speed': 5.0
                    })
            
            # 构建数据记录
            data_record = {
                'timestamp': current_time,
                'elapsed_time': elapsed_time,
                # 车辆状态（输入特征）
                'vehicle_x': vehicle_x,
                'vehicle_y': vehicle_y,
                'vehicle_yaw': vehicle_yaw,
                'vehicle_vx': vehicle_vx,
                'vehicle_vy': vehicle_vy,
                'vehicle_omega': vehicle_omega,
                'lateral_error': min_distance,
                # 未来轨迹（输出标签）
                'future_trajectory': future_points[:20]  # 确保只有20个点
            }
            
            self.collected_data.append(data_record)
            
            # 定期显示收集进度
            if len(self.collected_data) % 50 == 0:
                self.get_logger().info(
                    f"已收集 {len(self.collected_data)} 个数据点, "
                    f"运行时间: {elapsed_time:.1f}s, "
                    f"当前速度: {vehicle_vx:.2f}m/s"
                )
                
        except Exception as e:
            self.get_logger().error(f"数据收集错误: {str(e)}")
            
    def save_collected_data(self):
        """保存收集的数据"""
        if not self.collected_data:
            self.get_logger().warning("没有收集到数据")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存原始数据（JSON格式）
        json_filename = f"training_data_raw_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(self.collected_data, f, indent=2)
        
        # 转换为训练格式
        input_features = []
        output_labels = []
        
        for record in self.collected_data:
            # 输入特征：[vx, vy, omega, lateral_error]
            input_features.append([
                record['vehicle_vx'],
                record['vehicle_vy'], 
                record['vehicle_omega'],
                record['lateral_error']
            ])
            
            # 输出标签：未来轨迹点 [local_x, local_y, target_speed] * 20
            trajectory_flat = []
            for point in record['future_trajectory']:
                trajectory_flat.extend([
                    point['local_x'],
                    point['local_y'],
                    point['target_speed']
                ])
            output_labels.append(trajectory_flat)
        
        # 保存为numpy格式
        input_array = np.array(input_features, dtype=np.float32)
        output_array = np.array(output_labels, dtype=np.float32)
        
        np.savez(
            f"training_data_{timestamp}.npz",
            inputs=input_array,
            outputs=output_array,
            metadata={
                'num_samples': len(self.collected_data),
                'input_features': ['vx', 'vy', 'omega', 'lateral_error'],
                'output_shape': '20_points_x_3_features',
                'collection_time': time.time() - self.start_time
            }
        )
        
        self.get_logger().info(f"数据已保存:")
        self.get_logger().info(f"  原始数据: {json_filename}")
        self.get_logger().info(f"  训练数据: training_data_{timestamp}.npz")
        self.get_logger().info(f"  总样本数: {len(self.collected_data)}")
        self.get_logger().info(f"  输入维度: {input_array.shape}")
        self.get_logger().info(f"  输出维度: {output_array.shape}")
        
        # 停止节点
        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    
    collector = TrainingDataCollector()
    
    try:
        rclpy.spin(collector)
    except KeyboardInterrupt:
        collector.get_logger().info("用户中断，保存数据...")
        collector.save_collected_data()
    except Exception as e:
        collector.get_logger().error(f"运行错误: {str(e)}")
        collector.save_collected_data()
    finally:
        collector.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main() 