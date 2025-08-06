#!/bin/bash

# ==============================================================================
# ROS2 Bag to CSV Exporter (Final, Corrected Command Version)
#
# This script uses `ros2 topic echo --bag`, the correct non-interactive tool,
# to export data into a simple, python-readable CSV format.
# ==============================================================================

# --- Configuration ---
BAG_DIRS=(
    "output/20250806-113931"
    "output/20250806-114838-sac"
    "output/20250806-114612-sac"
)

ODOMETRY_TOPIC="/localization/kinematic_state"
TRAJECTORY_TOPIC="/planning/scenario_planning/trajectory"

# --- Main Logic ---

# Source the ROS2 workspace to make sure `ros2` commands work
echo "Sourcing ROS2 workspace..."
# shellcheck disable=SC1091
source /opt/ros/humble/setup.bash
# shellcheck disable=SC1091
if [ -f /aichallenge/workspace/install/setup.bash ]; then
    source /aichallenge/workspace/install/setup.bash
fi
echo "Done."

for bag_dir in "${BAG_DIRS[@]}"; do
    echo ""
    echo "=============================================================================="
    echo "Processing Bag Directory: $bag_dir"
    echo "=============================================================================="

    if [ ! -d "$bag_dir" ]; then
        echo "  [ERROR] Directory not found. Skipping."
        continue
    fi

    # Find the bag directory, which contains the metadata.yaml file.
    inner_bag_dir=$(find "$bag_dir" -type f -name "metadata.yaml" -printf '%h' -quit)

    if [ -z "$inner_bag_dir" ]; then
        echo "  [ERROR] No metadata.yaml found in subdirectories of $bag_dir. Skipping."
        continue
    fi
    echo "  Found bag data in: $inner_bag_dir"


    # --- Export Odometry (Actual Path) ---
    OUTPUT_ODOM_CSV="$bag_dir/actual_path.csv"
    echo "  > Exporting actual path (Odometry) to $OUTPUT_ODOM_CSV..."
    
    ros2 topic echo --bag "$inner_bag_dir" --topic "$ODOMETRY_TOPIC" > "$bag_dir/odom.tmp"
    
    if [[ -s "$bag_dir/odom.tmp" ]]; then
        # Grep for x and y coordinates specifically under the 'position:' block
        grep -A 2 'position:' "$bag_dir/odom.tmp" | grep 'x:' | awk '{print $2}' > "$bag_dir/x.tmp"
        grep -A 2 'position:' "$bag_dir/odom.tmp" | grep 'y:' | awk '{print $2}' > "$bag_dir/y.tmp"

        if [[ -s "$bag_dir/x.tmp" && -s "$bag_dir/y.tmp" ]]; then
            echo "x,y" > "$OUTPUT_ODOM_CSV"
            paste -d, "$bag_dir/x.tmp" "$bag_dir/y.tmp" >> "$OUTPUT_ODOM_CSV"
            rm "$bag_dir/x.tmp" "$bag_dir/y.tmp"
            echo "    ...Done."
        else
            echo "    ...Could not extract x, y from odometry data."
            rm -f "$bag_dir/x.tmp" "$bag_dir/y.tmp"
        fi
        rm "$bag_dir/odom.tmp"
    else
        echo "    ...No odometry data found or exported."
        rm -f "$bag_dir/odom.tmp"
    fi


    # --- Export Trajectory (Planned Path) ---
    OUTPUT_TRAJ_CSV="$bag_dir/planned_path.csv"
    echo "  > Exporting planned path (Trajectory) to $OUTPUT_TRAJ_CSV..."

    # Use the --once flag which is designed for this purpose
    ros2 topic echo --bag "$inner_bag_dir" --topic "$TRAJECTORY_TOPIC" --once > "$bag_dir/traj.tmp"

    if [[ -s "$bag_dir/traj.tmp" ]]; then
        # Grep for all x and y coordinates in the trajectory message
        grep -A 1 'position:' "$bag_dir/traj.tmp" | grep 'x:' | awk '{print $2}' > "$bag_dir/traj_x.tmp"
        grep -A 1 'position:' "$bag_dir/traj.tmp" | grep 'y:' | awk '{print $2}' > "$bag_dir/traj_y.tmp"
        
        if [[ -s "$bag_dir/traj_x.tmp" && -s "$bag_dir/traj_y.tmp" ]]; then
            echo "x,y" > "$OUTPUT_TRAJ_CSV"
            paste -d, "$bag_dir/traj_x.tmp" "$bag_dir/traj_y.tmp" >> "$OUTPUT_TRAJ_CSV"
            rm "$bag_dir/traj_x.tmp" "$bag_dir/traj_y.tmp"
            echo "    ...Done."
        else
            echo "    ...Could not extract x,y from trajectory data."
            rm -f "$bag_dir/traj_x.tmp" "$bag_dir/traj_y.tmp"
        fi
        
        rm "$bag_dir/traj.tmp"
    else
        echo "    ...No trajectory data found or exported."
        rm -f "$bag_dir/traj.tmp"
    fi
done

echo ""
echo "✅ All bags processed." 