from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('nn_planner_node')
    
    # Declare launch arguments
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='/aichallenge/nn_planner_dev/training_output/best_model.pth',
        description='Path to the trained PyTorch model file'
    )

    # Simple trajectory generator
    simple_trajectory_generator_node = Node(
        package='simple_trajectory_generator',
        executable='simple_trajectory_generator_node',
        name='simple_trajectory_generator',
        output='screen',
        parameters=[{
            'csv_path': os.path.join(
                get_package_share_directory('simple_trajectory_generator'), 
                'data', 
                'raceline_awsim_15km_improved.csv'
            ),
            'z': 6.5
        }],
        remappings=[
            ('trajectory', '/planning/scenario_planning/original_trajectory')
        ]
    )

    # NN Planner Node
    nn_planner_node = Node(
        package='nn_planner_node',
        executable='planner',
        name='nn_planner_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path')
        }],
        remappings=[
            ('/planning/scenario_planning/trajectory', '/planning/scenario_planning/trajectory')
        ]
    )

    return LaunchDescription([
        model_path_arg,
        simple_trajectory_generator_node,
        nn_planner_node,
    ]) 