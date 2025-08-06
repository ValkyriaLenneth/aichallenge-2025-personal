import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse

def calculate_curvature_from_points(x, y, window_size=3):
    """
    Calculate curvature using finite differences with smoothing.
    
    Args:
        x, y: Arrays of waypoint coordinates
        window_size: Window size for smoothing
    
    Returns:
        curvature: Array of curvature values
    """
    # Smooth the path first
    def smooth_array(arr, window):
        return np.convolve(arr, np.ones(window)/window, mode='same')
    
    if len(x) > window_size:
        x_smooth = smooth_array(x, window_size)
        y_smooth = smooth_array(y, window_size)
    else:
        x_smooth = x
        y_smooth = y
    
    # Calculate first and second derivatives
    dx = np.gradient(x_smooth)
    dy = np.gradient(y_smooth)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    
    # Calculate curvature using the formula: κ = |x'y'' - y'x''| / (x'² + y'²)^(3/2)
    curvature = np.abs(dx * ddy - dy * ddx) / np.power(dx*dx + dy*dy, 1.5)
    
    # Handle potential division by zero
    curvature = np.nan_to_num(curvature, nan=0.0, posinf=0.0, neginf=0.0)
    
    return curvature

def generate_speed_profile(curvature, base_speed=6.0, min_speed=3.0, max_speed=8.0, 
                          curvature_factor=5.0, smoothing_factor=0.3):
    """
    Generate speed profile based on curvature.
    
    Args:
        curvature: Array of curvature values
        base_speed: Base speed for straight sections (m/s)
        min_speed: Minimum allowed speed (m/s)
        max_speed: Maximum allowed speed (m/s)
        curvature_factor: How much curvature affects speed
        smoothing_factor: Smoothing factor for speed transitions
    
    Returns:
        speed: Array of speed values
    """
    # Calculate raw speed based on curvature
    # Higher curvature -> lower speed
    raw_speed = base_speed - curvature_factor * curvature
    
    # Clip to bounds
    raw_speed = np.clip(raw_speed, min_speed, max_speed)
    
    # Apply exponential smoothing for gradual speed changes
    speed = np.zeros_like(raw_speed)
    speed[0] = raw_speed[0]
    
    for i in range(1, len(raw_speed)):
        speed[i] = smoothing_factor * raw_speed[i] + (1 - smoothing_factor) * speed[i-1]
    
    return speed

def apply_acceleration_constraints(speed, max_accel=2.0, max_decel=3.0, dt=0.1):
    """
    Apply acceleration and deceleration constraints to speed profile.
    
    Args:
        speed: Initial speed array
        max_accel: Maximum acceleration (m/s²)
        max_decel: Maximum deceleration (m/s²)
        dt: Time step estimate
    
    Returns:
        constrained_speed: Speed array with acceleration constraints applied
    """
    constrained_speed = speed.copy()
    
    for i in range(1, len(speed)):
        prev_speed = constrained_speed[i-1]
        desired_speed = speed[i]
        
        # Calculate maximum possible speed change
        if desired_speed > prev_speed:
            # Accelerating
            max_speed_change = max_accel * dt
            constrained_speed[i] = min(desired_speed, prev_speed + max_speed_change)
        else:
            # Decelerating
            max_speed_change = max_decel * dt
            constrained_speed[i] = max(desired_speed, prev_speed - max_speed_change)
    
    return constrained_speed

def process_trajectory_file(input_file, output_file, speed_params=None):
    """
    Process a trajectory CSV file to generate improved speed profile.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        speed_params: Dictionary of speed generation parameters
    """
    if speed_params is None:
        speed_params = {
            'base_speed': 6.0,
            'min_speed': 3.5,
            'max_speed': 8.0,
            'curvature_factor': 8.0,
            'smoothing_factor': 0.4
        }
    
    print(f"Processing {input_file}...")
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Extract coordinates
    x = df['x'].values
    y = df['y'].values
    
    print(f"  + Loaded {len(x)} waypoints")
    
    # Calculate curvature
    curvature = calculate_curvature_from_points(x, y)
    print(f"  + Curvature range: {curvature.min():.4f} to {curvature.max():.4f}")
    
    # Generate speed profile
    speed = generate_speed_profile(curvature, **speed_params)
    
    # Apply acceleration constraints
    # Estimate dt based on distance between points
    distances = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    avg_distance = np.mean(distances)
    estimated_dt = avg_distance / speed_params['base_speed']  # rough estimate
    
    speed = apply_acceleration_constraints(speed, dt=estimated_dt)
    
    print(f"  + Speed range: {speed.min():.2f} to {speed.max():.2f} m/s")
    print(f"  + Speed std: {speed.std():.2f} m/s")
    
    # Update the dataframe
    df['speed'] = speed
    
    # Save the result
    df.to_csv(output_file, index=False)
    print(f"  + Saved to {output_file}")
    
    return df, curvature, speed

def visualize_trajectory(df, curvature, speed, output_dir):
    """Create visualization plots for the trajectory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Track layout with speed coloring
    ax1 = axes[0, 0]
    scatter = ax1.scatter(df['x'], df['y'], c=speed, cmap='RdYlGn', s=20)
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_title('Track Layout (colored by speed)')
    ax1.set_aspect('equal')
    plt.colorbar(scatter, ax=ax1, label='Speed (m/s)')
    
    # Plot 2: Speed profile
    ax2 = axes[0, 1]
    waypoint_idx = np.arange(len(speed))
    ax2.plot(waypoint_idx, speed, 'b-', linewidth=2)
    ax2.set_xlabel('Waypoint Index')
    ax2.set_ylabel('Speed (m/s)')
    ax2.set_title('Speed Profile')
    ax2.grid(True)
    
    # Plot 3: Curvature profile
    ax3 = axes[1, 0]
    ax3.plot(waypoint_idx, curvature, 'r-', linewidth=2)
    ax3.set_xlabel('Waypoint Index')
    ax3.set_ylabel('Curvature (1/m)')
    ax3.set_title('Curvature Profile')
    ax3.grid(True)
    
    # Plot 4: Speed vs Curvature correlation
    ax4 = axes[1, 1]
    ax4.scatter(curvature, speed, alpha=0.6)
    ax4.set_xlabel('Curvature (1/m)')
    ax4.set_ylabel('Speed (m/s)')
    ax4.set_title('Speed vs Curvature Relationship')
    ax4.grid(True)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = output_dir / f"trajectory_analysis.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  + Visualization saved to {plot_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate improved trajectory with physics-based speed profile")
    parser.add_argument("--input_dir", type=str, 
                       default="aichallenge/workspace/src/aichallenge_submit/simple_trajectory_generator/data",
                       help="Input directory containing CSV files")
    parser.add_argument("--base_speed", type=float, default=6.0, 
                       help="Base speed for straight sections (m/s)")
    parser.add_argument("--min_speed", type=float, default=3.5, 
                       help="Minimum speed (m/s)")
    parser.add_argument("--max_speed", type=float, default=8.0, 
                       help="Maximum speed (m/s)")
    parser.add_argument("--curvature_factor", type=float, default=8.0, 
                       help="How much curvature affects speed")
    parser.add_argument("--visualize", action="store_true", 
                       help="Generate visualization plots")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    
    speed_params = {
        'base_speed': args.base_speed,
        'min_speed': args.min_speed,
        'max_speed': args.max_speed,
        'curvature_factor': args.curvature_factor,
        'smoothing_factor': 0.4
    }
    
    # Process each CSV file
    csv_files = [
        ("raceline_awsim_15km.csv", "raceline_awsim_15km_improved.csv"),
        ("raceline_awsim_30km.csv", "raceline_awsim_30km_improved.csv"),
        ("raceline_awsim_safe.csv", "raceline_awsim_safe_improved.csv"),
        ("raceline_awsim_improved.csv", "raceline_awsim_improved_v2.csv")
    ]
    
    for input_name, output_name in csv_files:
        input_path = input_dir / input_name
        output_path = input_dir / output_name
        
        if input_path.exists():
            try:
                df, curvature, speed = process_trajectory_file(input_path, output_path, speed_params)
                
                if args.visualize:
                    viz_dir = input_dir / f"visualizations_{input_name.replace('.csv', '')}"
                    visualize_trajectory(df, curvature, speed, viz_dir)
                    
            except Exception as e:
                print(f"Error processing {input_name}: {e}")
        else:
            print(f"File {input_name} not found, skipping...")
    
    print("\nProcessing completed!")
    print(f"Speed parameters used:")
    for key, value in speed_params.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 