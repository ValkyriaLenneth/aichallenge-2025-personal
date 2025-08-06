from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('new_sac_gym_env')
    
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='/aichallenge/nn_planner_dev/training_output/best_model.pth',
        description='Path to the trained PyTorch model file'
    )

    # 添加时空域映射相关参数
    prediction_horizon_arg = DeclareLaunchArgument(
        'prediction_horizon_meters',
        default_value='200.0',
        description='Prediction horizon in meters for LSTM velocity mapping'
    )
    
    transition_zone_arg = DeclareLaunchArgument(
        'transition_zone_length',
        default_value='20',
        description='Length of transition zone between LSTM and CSV velocities'
    )
    
    dt_arg = DeclareLaunchArgument(
        'dt',
        default_value='0.1',
        description='Time step for LSTM predictions (seconds)'
    )
    
    max_accel_arg = DeclareLaunchArgument(
        'max_acceleration',
        default_value='2.0',
        description='Maximum allowed acceleration for velocity continuity (m/s²)'
    )
    
    debug_logs_arg = DeclareLaunchArgument(
        'enable_debug_logs',
        default_value='true',
        description='Enable detailed debug logging for time-space mapping'
    )

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

    new_sac_gym_env_node = Node(
        package='new_sac_gym_env',
        executable='planner',
        name='new_sac_gym_env_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'prediction_horizon_meters': LaunchConfiguration('prediction_horizon_meters'),
            'transition_zone_length': LaunchConfiguration('transition_zone_length'),
            'dt': LaunchConfiguration('dt'),
            'max_acceleration': LaunchConfiguration('max_acceleration'),
            'enable_debug_logs': LaunchConfiguration('enable_debug_logs')
        }],
        remappings=[
            ('/planning/scenario_planning/trajectory', '/planning/scenario_planning/trajectory')
        ]
    )

    return LaunchDescription([
        model_path_arg,
        prediction_horizon_arg,
        transition_zone_arg,
        dt_arg,
        max_accel_arg,
        debug_logs_arg,
        simple_trajectory_generator_node,
        new_sac_gym_env_node,
    ]) 