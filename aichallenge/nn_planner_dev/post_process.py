import argparse
import numpy as np
import yaml
from pathlib import Path
from tqdm import tqdm

import rosbag2_py
from rosidl_runtime_py.utilities import get_message
from rclpy.serialization import deserialize_message as rclpy_deserialize
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d

# ======================================================================================
# Constants based on our analysis
# ======================================================================================
# We will use a more robust method to determine frequency from the data itself,
# but we can set target time windows.
IN_TIME_WINDOW_S = 3.0
OUT_TIME_WINDOW_S = 1.0

# Topics we need to read
TRAJECTORY_TOPIC = "/planning/scenario_planning/trajectory"
KINEMATIC_STATE_TOPIC = "/localization/kinematic_state"

# ======================================================================================
# Helper functions for reading rosbag
# ======================================================================================

def get_rosbag_options(path: str, storage_id='sqlite3'):
    """Helper function to create rosbag2 options."""
    options = rosbag2_py.StorageOptions(uri=path, storage_id=storage_id)
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )
    return options, converter_options

def deserialize_message(msg_bytes, msg_type_name):
    """Deserialize a ROS2 message from bytes."""
    msg_type = get_message(msg_type_name)
    return rclpy_deserialize(msg_bytes, msg_type)

# ======================================================================================
# Data Loading Functions
# ======================================================================================

def load_static_trajectory(bag_path: Path):
    """
    Opens the rosbag, finds the first trajectory message, and extracts it
    as the global reference path.
    """
    print("Loading static reference trajectory...")
    options, converter_options = get_rosbag_options(str(bag_path))
    reader = rosbag2_py.SequentialReader()
    reader.open(options, converter_options)

    topic_types = reader.get_all_topics_and_types()
    type_map = {topic.name: topic.type for topic in topic_types}

    while reader.has_next():
        (topic, data, t) = reader.read_next()
        if topic == TRAJECTORY_TOPIC:
            msg = deserialize_message(data, type_map[topic])
            points = msg.points
            
            ref_path_pts = np.array([[p.pose.position.x, p.pose.position.y] for p in points])
            ref_path_vel = np.array([p.longitudinal_velocity_mps for p in points])
            
            print(f"  + Loaded reference trajectory with {len(ref_path_pts)} points.")
            return ref_path_pts, ref_path_vel

    raise ValueError(f"Topic '{TRAJECTORY_TOPIC}' not found in the rosbag.")

def load_kinematic_data(bag_path: Path):
    """
    Loads all kinematic state messages from the rosbag into a structured numpy array.
    """
    print("Loading kinematic state data...")
    options, converter_options = get_rosbag_options(str(bag_path))
    reader = rosbag2_py.SequentialReader()
    reader.open(options, converter_options)

    topic_types = reader.get_all_topics_and_types()
    type_map = {topic.name: topic.type for topic in topic_types}

    kinematic_states = []
    while reader.has_next():
        (topic, data, t) = reader.read_next()
        if topic == KINEMATIC_STATE_TOPIC:
            msg = deserialize_message(data, type_map[topic])
            
            # Timestamp in seconds
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            
            # Position
            pos = msg.pose.pose.position
            
            # Orientation to Yaw
            quat = msg.pose.pose.orientation
            yaw = R.from_quat([quat.x, quat.y, quat.z, quat.w]).as_euler('xyz', degrees=False)[2]
            
            # Velocities
            vel_x = msg.twist.twist.linear.x
            ang_vel_z = msg.twist.twist.angular.z
            
            kinematic_states.append((timestamp, pos.x, pos.y, yaw, vel_x, ang_vel_z))

    # Sort by timestamp just in case
    kinematic_states.sort(key=lambda x: x[0])
    
    # Create a structured numpy array for easier access
    dtype = [('t', 'f8'), ('x', 'f8'), ('y', 'f8'), ('yaw', 'f8'), ('vx', 'f8'), ('wz', 'f8')]
    kinematic_array = np.array(kinematic_states, dtype=dtype)
    
    print(f"  + Loaded {len(kinematic_array)} kinematic states.")
    return kinematic_array
    
# ======================================================================================
# Feature Engineering Functions
# ======================================================================================

def find_closest_path_idx(state, path_pts):
    """Finds the index of the closest point on the path to the current state."""
    distances = np.linalg.norm(path_pts - np.array([state['x'], state['y']]), axis=1)
    return np.argmin(distances)

def get_path_point_at_distance(path_pts, start_idx, distance):
    """
    Travels along the path from a starting index for a given distance and returns
    the index of the destination point.
    """
    if distance == 0:
        return start_idx

    current_dist = 0.0
    
    if distance > 0: # Forward
        for i in range(start_idx, len(path_pts) - 1):
            current_dist += np.linalg.norm(path_pts[i+1] - path_pts[i])
            if current_dist >= distance:
                return i + 1
        return len(path_pts) - 1 # Reached the end
    else: # Backward
        for i in range(start_idx, 0, -1):
            current_dist += np.linalg.norm(path_pts[i-1] - path_pts[i])
            if current_dist >= abs(distance):
                return i - 1
        return 0 # Reached the beginning

def calculate_curvature(p1, p2, p3):
    """Calculates the curvature from three points using the Menger curvature formula."""
    # Using the formula for the circumradius of a triangle
    a = np.linalg.norm(p2 - p3)
    b = np.linalg.norm(p1 - p3)
    c = np.linalg.norm(p1 - p2)
    
    # Avoid division by zero for straight lines
    if a * b * c == 0:
        return 0.0

    # Area using Heron's formula
    s = (a + b + c) / 2
    area_sq = s * (s - a) * (s - b) * (s - c)
    if area_sq <= 0: # Numerically unstable for colinear points
        return 0.0
    area = np.sqrt(area_sq)
    
    # Curvature is 1/R, where R is the circumradius
    curvature = (4 * area) / (a * b * c)

    # Add sign based on cross product (left/right turn)
    cross_product_z = (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])
    return np.copysign(curvature, cross_product_z)

def compute_features(state, path_pts):
    """
    Computes the full 13-dimensional feature vector for a given kinematic state.
    """
    # Find vehicle's projection on the path
    closest_idx = find_closest_path_idx(state, path_pts)
    closest_pt = path_pts[closest_idx]

    # Feature 1 & 2: Ego state
    current_velocity_x = state['vx']
    current_angular_velocity_z = state['wz']
    
    # Feature 3: distance_from_centerline
    distance = np.linalg.norm(np.array([state['x'], state['y']]) - closest_pt)
    # Determine sign (left/right of the path)
    path_vec = path_pts[closest_idx + 1] - path_pts[closest_idx - 1] if closest_idx > 0 and closest_idx < len(path_pts) - 1 else path_pts[1] - path_pts[0]
    ego_vec = np.array([state['x'], state['y']]) - closest_pt
    cross_prod_z = np.cross(path_vec, ego_vec)
    distance_from_centerline = np.copysign(distance, cross_prod_z)
    
    # Feature 4: heading_error
    path_yaw = np.arctan2(path_vec[1], path_vec[0])
    heading_error = state['yaw'] - path_yaw
    # Normalize angle to [-pi, pi]
    heading_error = (heading_error + np.pi) % (2 * np.pi) - np.pi
    
    # Features 5-13: Path Curvature "Fingerprint"
    sample_distances = [-25, -15, -10, -5, 0, 5, 10, 15, 25]
    curvature_features = []
    for dist in sample_distances:
        sample_idx = get_path_point_at_distance(path_pts, closest_idx, dist)
        
        # Take 3 points around the sample point to calculate curvature
        p2 = path_pts[sample_idx]
        p1 = path_pts[max(0, sample_idx - 5)]
        p3 = path_pts[min(len(path_pts) - 1, sample_idx + 5)]
        
        # If points are the same, curvature is 0
        if np.array_equal(p1,p2) or np.array_equal(p2,p3):
            curvature_features.append(0.0)
        else:
            curvature_features.append(calculate_curvature(p1, p2, p3))
            
    return np.concatenate([
        [current_velocity_x, current_angular_velocity_z],
        [distance_from_centerline, heading_error],
        curvature_features
    ])

# ======================================================================================
# Main Processing Logic
# ======================================================================================

def main(bag_path: Path, output_dir: Path):
    if not bag_path.exists():
        raise FileNotFoundError(f"Rosbag not found at {bag_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Load static and time-series data
    ref_path_pts, ref_path_vel = load_static_trajectory(bag_path)
    kinematic_data = load_kinematic_data(bag_path)

    # Step 2: Create a continuous velocity profile for the reference path
    path_distances = np.cumsum(np.linalg.norm(np.diff(ref_path_pts, axis=0), axis=1))
    path_distances = np.insert(path_distances, 0, 0)
    # Use interpolation to get velocity at any point along the path
    velocity_interpolator = interp1d(path_distances, ref_path_vel, bounds_error=False, fill_value=(ref_path_vel[0], ref_path_vel[-1]))

    # Step 3: Compute features and labels for the entire run
    print("Calculating features and labels for all time steps...")
    all_features = []
    all_labels = []

    for state in tqdm(kinematic_data):
        # Calculate 13D features for the current state
        features = compute_features(state, ref_path_pts)
        all_features.append(features)
        
        # Calculate target velocity (label)
        closest_idx = find_closest_path_idx(state, ref_path_pts)
        dist_along_path = path_distances[closest_idx]
        label_velocity = velocity_interpolator(dist_along_path)
        all_labels.append(label_velocity)

    all_features = np.array(all_features)
    all_labels = np.array(all_labels).reshape(-1, 1)

    # Step 4: Create sequences using a sliding window
    print("Creating sequences using sliding window...")
    
    # Calculate sequence lengths based on actual data frequency
    avg_time_diff = np.mean(np.diff(kinematic_data['t']))
    freq = 1 / avg_time_diff
    print(f"  + Detected average frequency: {freq:.2f} Hz")
    
    IN_SEQ_LEN = int(np.ceil(IN_TIME_WINDOW_S * freq))
    OUT_SEQ_LEN = int(np.ceil(OUT_TIME_WINDOW_S * freq))
    TOTAL_SEQ_LEN = IN_SEQ_LEN + OUT_SEQ_LEN
    print(f"  + Using sequence lengths: Input={IN_SEQ_LEN}, Output={OUT_SEQ_LEN}")

    X, Y = [], []
    for i in tqdm(range(len(all_features) - TOTAL_SEQ_LEN + 1)):
        X.append(all_features[i : i + IN_SEQ_LEN])
        Y.append(all_labels[i + IN_SEQ_LEN : i + TOTAL_SEQ_LEN])
    
    X = np.array(X)
    Y = np.array(Y)

    # Step 5: Save processed data
    print("Saving processed data...")
    x_path = output_dir / "X_data.npy"
    y_path = output_dir / "Y_data.npy"
    np.save(x_path, X)
    np.save(y_path, Y)
    
    print(f"  + Saved X_data to {x_path} with shape {X.shape}")
    print(f"  + Saved Y_data to {y_path} with shape {Y.shape}")
    print("Processing complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process ROS2 bag files for NN planner training.")
    parser.add_argument("bag_path", type=str, help="Path to the rosbag directory to process.")
    parser.add_argument("--output_dir", type=str, default="processed_data", help="Directory to save the processed .npy files.")
    
    args = parser.parse_args()
    
    main(Path(args.bag_path), Path(args.output_dir)) 