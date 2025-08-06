import rclpy
from rclpy.node import Node
from rclpy.time import Time

import numpy as np
import torch

from nav_msgs.msg import Odometry
from autoware_auto_planning_msgs.msg import Trajectory
from geometry_msgs.msg import PoseStamped, AccelWithCovarianceStamped

class NNPlannerNode(Node):
    def __init__(self):
        super().__init__('nn_planner_node')

        # Parameters
        self.declare_parameter('model_path', '')
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        
        # Publishers
        self.trajectory_pub = self.create_publisher(
            Trajectory, "/planning/scenario_planning/trajectory", 1)

        # Subscribers
        self.kinematic_state_sub = self.create_subscription(
            Odometry, "/localization/kinematic_state", self.kinematic_state_callback, 1)
        self.original_trajectory_sub = self.create_subscription(
            Trajectory, "/planning/scenario_planning/original_trajectory", self.original_trajectory_callback, 1)

        # Node state
        self.current_odometry = None
        self.static_path = None
        self.model = None

        self.get_logger().info('NN Planner Node has been initialized.')
        if model_path:
            self.get_logger().info(f"Loading model from: {model_path}")
            # self.load_model(model_path) # Placeholder
        else:
            self.get_logger().warn("Model path not provided. Operating in passthrough mode.")

        # Timer to run planner logic
        self.timer = self.create_timer(0.1, self.planner_callback) # 10 Hz

    def kinematic_state_callback(self, msg: Odometry):
        self.current_odometry = msg

    def original_trajectory_callback(self, msg: Trajectory):
        self.get_logger().info(f"Received static path with {len(msg.points)} points.", once=True)
        self.static_path = msg

    def planner_callback(self):
        """
        Main planner loop.
        """
        if self.static_path is None or self.current_odometry is None:
            self.get_logger().info("Waiting for static path and odometry...", throttle_duration_sec=5)
            return

        # --- Stage 1: Passthrough original trajectory for testing ---
        # In this stage, we simply forward the trajectory from the original planner
        # to ensure the communication pipeline is working correctly.
        
        output_trajectory = Trajectory()
        output_trajectory.header = self.get_clock().now().to_msg()
        output_trajectory.header.frame_id = "map"
        
        # For now, just copy the points from the static path
        output_trajectory.points = self.static_path.points

        # In a real scenario, we would update the velocity profile here
        # For example:
        # predicted_velocities = self.run_model_inference()
        # for i, point in enumerate(output_trajectory.points):
        #     if i < len(predicted_velocities):
        #         point.longitudinal_velocity_mps = predicted_velocities[i]
        
        self.get_logger().info(f"Publishing trajectory with {len(output_trajectory.points)} points.", throttle_duration_sec=5)
        self.trajectory_pub.publish(output_trajectory)

def main(args=None):
    rclpy.init(args=args)
    node = NNPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main() 