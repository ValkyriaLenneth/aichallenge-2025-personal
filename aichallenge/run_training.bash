#!/bin/bash

# ==============================================================================
# SAC Model Training Script (Simplified, Evaluation-Style)
#
# This script mimics the startup sequence of the official 'run_evaluation.bash'
# to ensure a stable and correctly initialized environment before training.
#
# Order of Operations:
# 1. Start AWSIM (Simulator)
# 2. Start Autoware
# 3. Initialize Autoware state with `publish.bash`
# 4. Wait for essential services to be ready
# 5. Start SAC training Python script
# ==============================================================================

# --- Process ID Management ---
PID_AWSIM=""
PID_AUTOWARE=""
PID_ROSBAG=""
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

    # Compress the rosbag
    echo ">>> Compressing rosbag..."
    if [ -d "nn_planner_rosbag-sac" ]; then
        tar -czf nn_planner_rosbag-sac_$(date +%Y%m%d-%H%M%S).tar.gz nn_planner_rosbag-sac
        rm -rf nn_planner_rosbag-sac
        echo "    Rosbag compressed."
    else
        echo "    No rosbag directory found to compress."
    fi

    # Remove the temporary PID file
    rm -f "$PID_FILE"

    echo ">>> Cleanup complete."
    exit 0
}

# Trap Ctrl+C (SIGINT) and other termination signals to run the cleanup function
trap cleanup SIGINT SIGTERM EXIT

# --- Main Script Logic ---

echo "================================================================"
echo "SAC+LSTM TRAINING STARTUP - SIMULATOR-FIRST APPROACH"
echo "================================================================"

# 1. Source the Autoware workspace
echo ">>> Step 1: Sourcing Autoware workspace..."
# shellcheck disable=SC1091
source /aichallenge/workspace/install/setup.bash

# CRITICAL: 添加与官方评估脚本相同的网络配置
echo ">>> Step 1.5: 配置网络设置 (与官方评估脚本一致)..."
sudo ip link set multicast on lo
sudo sysctl -w net.core.rmem_max=2147483647 >/dev/null
echo "    网络配置完成"

# CRITICAL: Disable Autoware's default NN Planner to prevent trajectory conflicts.
# This ensures that our SAC agent is the sole provider of trajectories.
export DISABLE_NN_PLANNER=true
# ADDITION: This variable likely re-configures Autoware's control gate
# to accept trajectories directly from our topic, which is necessary
# when the default planner is disabled.
export SAC_DIRECT_CONTROL=true

# Move to a dedicated output directory
echo ">>> Setting up output directory..."
OUTPUT_DIRECTORY=$(date +%Y%m%d-%H%M%S)-sac
cd /output || exit
mkdir -p "$OUTPUT_DIRECTORY"
ln -nfs "$OUTPUT_DIRECTORY" latest-sac
cd "$OUTPUT_DIRECTORY" || exit
echo "    Working directory: $(pwd)"

# 2. Start AWSIM (Simulator first)
echo ">>> Step 2: Starting AWSIM (与官方时序一致)..."
nohup /aichallenge/run_simulator.bash endless > ./awsim.log 2>&1 &
PID_AWSIM=$!
echo "$PID_AWSIM" >> "$PID_FILE"
echo "    AWSIM started with PID: $PID_AWSIM"
sleep 3  # 改为与官方相同的3秒

# 3. Start Autoware
echo ">>> Step 3: Starting Autoware (与官方时序一致)..."
nohup /aichallenge/run_autoware.bash awsim > ./autoware_train.log 2>&1 &
PID_AUTOWARE=$!
echo "$PID_AUTOWARE" >> "$PID_FILE"
echo "    Autoware started with PID: $PID_AUTOWARE"
sleep 3  # 改为与官方相同的3秒

# 4. 启动rosbag记录 (与官方时序一致)
echo ">>> Step 4: Starting rosbag recording (与官方时序一致)..."
TOPICS_TO_RECORD="/planning/scenario_planning/trajectory /localization/kinematic_state /tf /tf_static /control/command/control_cmd /vehicle/status/velocity_status /vehicle/status/steering_status"
nohup ros2 bag record -o nn_planner_rosbag-sac $TOPICS_TO_RECORD > ./rosbag_record.log 2>&1 &
PID_ROSBAG=$!
echo "$PID_ROSBAG" >> "$PID_FILE"
echo "    Rosbag recording started with PID: $PID_ROSBAG"
sleep 5  # 与官方相同的5秒等待

# 5. CRITICAL: 等待关键服务就绪 (模拟官方脚本的服务等待)
echo ">>> Step 5: 等待关键服务就绪 (与官方评估脚本一致)..."
echo "    等待屏幕录制服务 (模拟官方流程)..."
until (ros2 service type /debug/service/capture_screen >/dev/null 2>&1); do
    echo "    Still waiting for capture_screen service..."
    sleep 5
done
echo "    ✓ 屏幕录制服务就绪"

# 6. CRITICAL: Initialize Autoware state using publish.bash (与官方完全相同的时机)
echo ">>> Step 6: Initializing Autoware state (与官方完全相同的时机)..."
bash /aichallenge/publish.bash all
echo "    ✓ Autoware状态初始化完成"

# 7. Wait for essential Autoware services to confirm readiness
echo ">>> Step 7: Waiting for essential Autoware services..."
CONTROL_SERVICE="/control/control_mode_request"
echo "    Waiting for service: $CONTROL_SERVICE"
until ros2 service list | grep -q "$CONTROL_SERVICE"; do
    echo "    Still waiting for $CONTROL_SERVICE..."
    sleep 2
done
echo "✓ Service $CONTROL_SERVICE is available."
echo "✓ Autoware is ready!"

# 8. Start SAC training
echo ">>> Step 8: Starting SAC training Python script..."
echo ""
echo "================================================================"
echo "LAUNCHING PYTHON TRAINING"
echo "================================================================"
# The Python script will now take over
python3 /aichallenge/sac_gym_env/train_sac.py

echo ">>> Training script finished." 