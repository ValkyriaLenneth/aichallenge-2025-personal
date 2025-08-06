#!/bin/bash

# ==============================================================================
# New SAC GYM ENV Test Script
# This script is based on the official 'run_evaluation.bash' to test
# the functionality of the new_sac_gym_env node.
# It temporarily replaces the main launch file to load the new node.
# The original launch file is restored on exit.
# ==============================================================================

# --- Path Configuration ---
LAUNCH_DIR="/aichallenge/workspace/src/aichallenge_submit/aichallenge_submit_launch/launch"
ORIGINAL_LAUNCH_FILE="$LAUNCH_DIR/reference.launch.xml"
SAC_LAUNCH_FILE="$LAUNCH_DIR/reference_for_sac.launch.xml"
BACKUP_LAUNCH_FILE="$LAUNCH_DIR/reference.launch.xml.bak"

# --- Process ID Management ---
PID_AWSIM=""
PID_AUTOWARE=""
PID_FILE=$(mktemp) # Temporary file to store all related PIDs

# --- Cleanup Function ---
cleanup() {
    echo ""
    echo ">>> Termination signal received. Cleaning up all processes..."

    # Kill all processes listed in the PID file
    if [ -f "$PID_FILE" ]; then
        # Terminate processes gracefully first
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "Sending SIGTERM to PID $pid..."
                kill -SIGTERM "$pid"
            fi
        done < <(tac "$PID_FILE") # Terminate in reverse order
    fi

    # Wait a moment for graceful shutdown
    sleep 5

    # Force kill any remaining processes
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "Forcing shutdown of remaining PID $pid..."
                kill -SIGKILL "$pid"
            fi
        done < <(tac "$PID_FILE")
    fi
    
    # Restore the original launch file
    if [ -f "$BACKUP_LAUNCH_FILE" ]; then
        echo ">>> Restoring original launch file from backup."
        mv "$BACKUP_LAUNCH_FILE" "$ORIGINAL_LAUNCH_FILE"
    fi

    # Remove the temporary PID file
    rm -f "$PID_FILE"

    echo ">>> Cleanup complete."
    exit 0
}

# Trap Ctrl+C (SIGINT) and other termination signals to run the cleanup function
trap cleanup SIGINT SIGTERM EXIT

# --- Backup and Switch Launch File ---
echo ">>> Backing up original launch file to $BACKUP_LAUNCH_FILE"
cp "$ORIGINAL_LAUNCH_FILE" "$BACKUP_LAUNCH_FILE"

echo ">>> Switching to SAC launch file for this session."
cp "$SAC_LAUNCH_FILE" "$ORIGINAL_LAUNCH_FILE"


# --- Main Script Logic (Copied from run_evaluation.bash) ---

# Move working directory
OUTPUT_DIRECTORY=$(date +%Y%m%d-%H%M%S)
cd /output || exit
mkdir "$OUTPUT_DIRECTORY"
ln -nfs "$OUTPUT_DIRECTORY" latest
cd "$OUTPUT_DIRECTORY" || exit

# shellcheck disable=SC1091
source /aichallenge/workspace/install/setup.bash
sudo ip link set multicast on lo
sudo sysctl -w net.core.rmem_max=2147483647 >/dev/null

# Start AWSIM with nohup
echo "Start AWSIM"
nohup /aichallenge/run_simulator.bash > ./awsim.log 2>&1 &
PID_AWSIM=$!
echo "$PID_AWSIM" >> "$PID_FILE"
echo "    AWSIM started with PID: $PID_AWSIM"
sleep 3

# Start Autoware with nohup
echo "Start Autoware"
nohup /aichallenge/run_autoware.bash awsim >autoware.log 2>&1 &
PID_AUTOWARE=$!
echo "$PID_AUTOWARE" >> "$PID_FILE"
echo "    Autoware started with PID: $PID_AUTOWARE"
sleep 3

# Start recording rviz2
echo "Start screen capture"
until (ros2 service type /debug/service/capture_screen >/dev/null 2>&1); do
    echo "    Still waiting for capture_screen service..."
    sleep 5
done
echo "    ✓ Screen capture service is ready."

# Move windows
wmctrl -a "RViz" && wmctrl -r "RViz" -e 0,0,0,1920,1043
wmctrl -a "AWSIM" && wmctrl -r "AWSIM" -e 0,0,0,900,1043

bash /aichallenge/publish.bash all

# Wait for AWSIM to finish (this is the main process we're waiting for)
wait "$PID_AWSIM"

echo ">>> Main process finished." 