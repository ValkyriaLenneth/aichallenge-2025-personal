# 可用的topic list
(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic list
/autoware_orientation
/awsim/control_cmd
/awsim/control_mode_request_topic
/clock
/control/command/actuation_cmd
/control/command/control_cmd
/control/debug/lookahead_point
/diagnostics
/events/write_split
/joint_states
/localization/acceleration
/localization/biased_pose
/localization/biased_pose_with_covariance
/localization/debug
/localization/debug/measured_pose
/localization/estimated_yaw_bias
/localization/gyro_twist
/localization/gyro_twist_raw
/localization/imu_gnss_poser/pose_with_covariance
/localization/initial_pose3d
/localization/kinematic_state
/localization/pose
/localization/pose_with_covariance
/localization/twist
/localization/twist_estimator/twist_with_covariance
/localization/twist_estimator/twist_with_covariance_raw
/localization/twist_with_covariance
/map/vector_map
/map/vector_map_marker
/output/raw_control_cmd
/parameter_events
/planning/mission_planning/goal
/planning/mission_planning/route_state
/planning/scenario_planning/trajectory
/robot_description
/rosout
/sensing/gnss/gnss_fixed
/sensing/gnss/nav_sat_fix
/sensing/gnss/pose
/sensing/gnss/pose_with_covariance
/sensing/imu/imu_data
/sensing/imu/imu_raw
/sensing/vehicle_velocity_converter/twist_with_covariance
/system/system_monitor/cpu_monitor/cpu_usage
/tf
/tf_static
/vehicle/raw_vehicle_cmd_converter/debug/steer_pid
/vehicle/status/gear_report
/vehicle/status/gear_status
/vehicle/status/steering_status
/vehicle/status/velocity_status

# kinematic state 
(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /localization/kinematic_state
header:
  stamp:
    sec: 95
    nanosec: 944997855
  frame_id: map
child_frame_id: base_link
pose:
  pose:
    position:
      x: 89656.42915968792
      y: 43138.11827166477
      z: 6.373902589707166
    orientation:
      x: 0.0
      y: 0.0
      z: -0.7602774415903842
      w: 0.6495985004668497
  covariance:
  - 0.013623258229382684
  - -0.004495301085077942
  - 0.0
  - 0.0
  - 0.0
  - 0.002053282629607096
  - -0.0044953010850779474
  - 0.00889648773361733
  - 0.0
  - 0.0
  - 0.0
  - -0.0009705937578565475
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.002053282629607095
  - -0.0009705937578565472
  - 0.0
  - 0.0
  - 0.0
  - 0.0005411976198588203
twist:
  twist:
    linear:
      x: 3.8910607573946145
      y: 0.0
      z: 0.0
    angular:
      x: 0.0
      y: 0.0
      z: 0.2975748483010922
  covariance:
  - 0.1366280002703244
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 5.128183143152998e-25
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 5.128183143152998e-25
  - 0.0
  - 0.0
  - 0.0
  - 0.0
  - 0.030862820672945112
---

(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /map/vector_map
header:
  stamp:
    sec: 0
    nanosec: 0
  frame_id: map
map_format: 0
format_version: '1'
map_version: '30'
data:
- 22
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 115
- 101
- 114
- 105
- 97
- 108
- 105
- 122
- 97
- 116
- 105
- 111
- 110
- 58
- 58
- 97
- 114
- 99
- 104
- 105
- 118
- 101
- 18
- 0
- 4
- 8
- 4
- 8
- 1
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 218
- 3
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 1
- 0
- 0
- 0
- 3
- 0
- 1
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 11
- 38
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 2
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 7
- 0
- 0
- 0
- 0
- 0
- 0
- 0
- 108
- 111
- 99
- 97
- 108
- 95
- 120
- 0
- 0
- 0
- 0
- 0
- 9
- 0
- 0
- 0
- '...'
---

(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /tf
transforms:
- header:
    stamp:
      sec: 278
      nanosec: 904993765
    frame_id: map
  child_frame_id: base_link
  transform:
    translation:
      x: 89656.27190907716
      y: 43135.06940141163
      z: 6.370282190169584
    rotation:
      x: 0.0
      y: 0.0
      z: -0.6997983243075453
      w: 0.7143404687516672
---

(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /tf_static
transforms:
- header:
    stamp:
      sec: 0
      nanosec: 0
    frame_id: map
  child_frame_id: viewer
  transform:
    translation:
      x: 89648.208229919
      y: 43157.235950608505
      z: 6.5
    rotation:
      x: 0.0
      y: 0.0
      z: 0.0
      w: 1.0
---

# 备注：trajectory每次生成全部路径。这里只截取一小部分。
(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /planning/scenario_planning/trajectory
- time_from_start:
    sec: 0
    nanosec: 0
  pose:
    position:
      x: 89631.8625729
      y: 43128.3106974
      z: 6.5
    orientation:
      x: 0.0
      y: 0.0
      z: 0.8948576686430713
      w: 0.44635160229429816
  longitudinal_velocity_mps: 4.166666507720947
  lateral_velocity_mps: 0.0
  acceleration_mps2: 0.0
  heading_rate_rps: 0.0
  front_wheel_angle_rad: 0.0
  rear_wheel_angle_rad: 0.0
- time_from_start:
    sec: 0
    nanosec: 0
  pose:
    position:
      x: 89630.0674883
      y: 43130.6945594
      z: 6.5
    orientation:
      x: 0.0
      y: 0.0
      z: 0.8908735393706145
      w: 0.4542514026937883
  longitudinal_velocity_mps: 4.166666507720947
  lateral_velocity_mps: 0.0
  acceleration_mps2: 0.0
  heading_rate_rps: 0.0
  front_wheel_angle_rad: 0.0
  rear_wheel_angle_rad: 0.0
---

^C(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /vehicle/status/velocity_status
header:
  stamp:
    sec: 7
    nanosec: 344999835
  frame_id: base_link
longitudinal_velocity: 0.0
lateral_velocity: -0.0
heading_rate: -0.00037284253630787134
---

(AIC_DEV) ubuntu@ip-172-31-33-145:/aichallenge$ ros2 topic echo --once /vehicle/status/steering_status
stamp:
  sec: 31
  nanosec: 564999294
steering_tire_angle: -0.008295579813420773
---

# Topic 数据详解

## 1. `/localization/kinematic_state` (类型: `nav_msgs/Odometry`)

这是**最核心的输入数据**，描述了车辆在世界中的完整状态。

- **总体目的**: 告诉我们车辆**当前**的精确位置、姿态（朝向）、线速度和角速度。
- **数据解析**:
    - `header`:
        - `stamp`: 时间戳。`sec: 95, nanosec: 944...` 表示这个数据是在第 95.94 秒时被捕获的。所有数据都带有时间戳，这对于后续对齐不同来源的数据至关重要。
        - `frame_id: map`: 表示该消息中的所有数据都是相对于 `map` 这个固定的世界坐标系来描述的。
        - `child_frame_id: base_link`: 表示这个消息描述的是 `base_link`（通常指车辆的中心点）的状态。
    - `pose.pose`: 描述车辆的**位姿**。
        - `position (x, y, z)`: 车辆在 `map` 坐标系下的三维坐标。这是模型知道“我在哪里”的基础。
        - `orientation (x, y, z, w)`: 描述车辆朝向的**四元数 (Quaternion)**。它比欧拉角（俯仰、偏航、滚转）更稳定。对于平面运动的赛车，我们最关心的是由 `z` 和 `w` 决定的**偏航角 (Yaw)**，即车辆的航向。
    - `twist.twist`: 描述车辆的**速度**。
        - `linear.x`: **纵向速度 (m/s)**，即车辆前进的速度。这是您模型需要重点关注的输入特征之一。`3.89 m/s` 表示车辆当前的前进速度。
        - `angular.z`: **偏航角速度 (rad/s)**，即车辆的转向速率。这反映了车辆正在以多快的速度转弯，是判断车辆是否在弯心的关键特征。
- **对您任务的价值**: 这是您神经网络模型的**主要输入特征 (Input Feature)**。模型需要根据当前的 `pose` 和 `twist` 来决定下一个时刻的目标速度。

---

## 2. `/map/vector_map` (类型: `autoware_auto_mapping_msgs/HADLanelet2Map`)

这是**静态的环境信息**，描述了整个赛道的结构。

- **总体目的**: 提供高精地图，包含车道线、停止线、赛道边界等所有静态道路元素。
- **数据解析**:
    - `header`: `stamp: 0` 很常见，因为地图是静态的，通常在系统启动时加载一次，不会随时间变化。
    - `data`: 您看到的一长串数字（`[22, 0, 0, ...]`）是**二进制序列化后的 Lanelet2 地图数据**。它不是人类可直接阅读的格式。ROS 节点在内部会使用专门的库来反序列化和解析这些数据，从而构建出一个可操作的地图对象。
- **对您任务的价值**: 这是另一个**至关重要的输入特征**。虽然不能直接使用，但在您的数据处理脚本中，您需要：
    1.  解析这个地图数据。
    2.  根据车辆当前的 `kinematic_state`，在地图上找到车辆所在的赛道线 (Lanelet)。
    3.  提取前方的路径点、计算路径的曲率、到赛道边界的距离等。
    4.  将这些**提取出的、有意义的特征**（如“前方50米内最大曲率”）作为您模型的输入。

---

## 3. `/tf` 和 `/tf_static` (类型: `tf2_msgs/TFMessage`)

这是**坐标系之间的转换关系**。

- **总体目的**: `tf` (transform) 用于广播和监听不同坐标系之间的关系。这让系统可以将来自不同传感器、不同坐标系的数据统一起来。
    - `/tf`: 动态变换。例如，`map` -> `base_link` 的变换就是车辆的实时位姿，它一直在变。您会发现 `/tf` 中 `transform` 的内容与 `/localization/kinematic_state` 中的 `pose` 基本一致。
    - `/tf_static`: 静态变换。例如，`base_link` -> `lidar_sensor`（激光雷达）的相对位置。这些在车辆组装好后就不会变。
- **数据解析**:
    - `transform`:
        - `translation (x, y, z)`: 两个坐标系原点之间的位移。
        - `rotation (x, y, z, w)`: 两个坐标系之间的旋转关系（四元数）。
- **对您任务的价值**: 在进行数据预处理时**不可或缺**。您需要使用 `tf` 来确保所有输入数据（如车辆位置、目标轨迹点）都在同一个坐标系（通常是 `map`）中，并且时间戳是对齐的。

---

## 4. `/planning/scenario_planning/trajectory` (类型: `autoware_auto_planning_msgs/Trajectory`)

这是**我们希望模型学习的“正确答案”**。

- **总体目的**: 描述了现有规划器生成的、供车辆执行的未来一段时间的轨迹。
- **数据解析**:
    - 这是一个**点序列 (list of points)**。每个点都描述了轨迹上的一个状态。
    - `pose`: 该轨迹点的**目标位姿**（位置和朝向）。
    - `longitudinal_velocity_mps`: **该轨迹点的目标纵向速度 (m/s)**。**这正是您第一阶段任务需要学习和预测的目标！** 您可以看到，示例中所有点的速度都是 `4.166 m/s`，这说明原始的 planner 可能只是给了一个固定速度。您的 NN planner 的目标就是根据当前状态，生成一个更合理的、动态变化的速度。
    - 其他字段 (`lateral_velocity_mps`, `acceleration_mps2` 等) 提供了更详细的运动信息，在初期可以暂时简化，只关注纵向速度。
- **对您任务的价值**: 这是模仿学习的**训练标签 (Label)**。您的训练数据对将是：`(输入特征: kinematic_state, map_features, etc.) -> (输出标签: longitudinal_velocity_mps)`。

---

## 5. `/vehicle/status/*` (各种车辆底层状态)

这些是来自车辆（或模拟器）的**原始状态反馈**。

- **`/vehicle/status/velocity_status`**:
    - `longitudinal_velocity`: 车辆报告的自身前进速度。可以与 `/localization/kinematic_state` 中的速度进行交叉验证。
- **`/vehicle/status/steering_status`**:
    - `steering_tire_angle`: 车辆报告的当前前轮转角。
- **对您任务的价值**: **可选的辅助输入**。这些是更底层的原始数据，延迟可能更低。在构建更复杂的模型时，可以考虑将它们作为输入特征，以获得对车辆状态更细致的描述。

---

# 模型与数据格式定义

基于我们的讨论，最终确定模仿学习第一阶段的 LSTM 模型及其输入输出数据格式如下：

## 1. 模型架构

- **模型类型**: LSTM (Long Short-Term Memory)
- **LSTM 层数**: 2 层
- **隐藏单元数 (Hidden Size)**: 256
- **架构**: 这是一个 Sequence-to-Sequence (Seq2Seq) 模型。数据将流经两个堆叠的 LSTM 层，然后通过一个全连接层（Linear Layer）将每个时间步的隐藏状态映射到最终的预测速度值。

## 2. 数据格式与序列长度

系统的核心运行频率经确认为 **30 Hz**。基于此，我们定义输入输出序列长度如下：

### 模型输入 (X)
- **时间窗口**: **过去 3 秒** 的历史数据。
- **序列长度 `T_in`**: 3 秒 * 30 Hz = **90 个数据点**。
- **数据维度**: `(batch_size, 90, num_features)`
- **内容**: 过去90个连续时间点的、经过特征工程处理的车辆状态与环境特征向量。

### 模型输出 (Y)
- **时间窗口**: **未来 1 秒** 的目标速度。
- **序列长度 `T_out`**: 1 秒 * 30 Hz = **30 个数据点**。
- **数据维度**: `(batch_size, 30, 1)`
- **内容**: 模型需要预测的未来30个连续时间点的目标纵向速度 (`longitudinal_velocity_mps`)。

### 数据处理流程
我们的数据处理脚本需要实现一个总长度为 `120` (90+30) 个时间点的滑动窗口。每次滑动，从录制好的数据中切分出一个120个点的数据段，其中**前90个点**的特征向量作为模型输入 `X`，**后30个点**的目标速度作为标签 `Y`。

---

# 特征工程方案

为了让模型能够理解驾驶逻辑，我们不能直接使用原始的`kinematic_state`。必须设计一套特征工程方案，将原始数据转化为信息量丰富的特征向量。

## 1. 核心思想：从“固定距离”到“动态时间”

我们关心的路径范围应与车辆的速度和模型的预测时长相关。经计算，车辆在3秒（输入）+1秒（输出）的时间窗口内，最大行驶距离约为40米。因此，我们设定一个以车辆为中心、**前后各25米**的对称探测范围，并在此范围内进行密集采样，以构建一个描述周围路径几何形状的“特征指纹”。

## 2. 最终特征向量 (13维)

在每个时间点，我们将为车辆生成一个包含13个维度的特征向量。

#### a) 车辆自身状态 (2个特征)
1.  **`current_velocity_x`**: 车辆当前的前进速度 (m/s)。
2.  **`current_angular_velocity_z`**: 车辆当前的角速度 (rad/s)，即转向速率。

#### b) 路径相对位置 (2个特征)
3.  **`distance_from_centerline`**: 车辆当前位置到参考路径（一阶段为CSV赛车线）的最短横向距离。带有正负号，表示在路径左侧或右侧。
4.  **`heading_error`**: 车辆当前朝向与参考路径切线方向的角度差 (rad)。

#### c) 路径几何“指纹” (9个特征)
我们将在以车辆为中心的 `[-25m, +25m]` 范围内，选取9个采样点，计算其曲率。
5.  **`curvature_at_-25m`**: 后方25米处的路径曲率。
6.  **`curvature_at_-15m`**: 后方15米处的路径曲率。
7.  **`curvature_at_-10m`**: 后方10米处的路径曲率。
8.  **`curvature_at_-5m`**: 后方5米处的路径曲率。
9.  **`curvature_at_0m`**: 车辆当前位置的路径曲率。
10. **`curvature_at_+5m`**: 前方5米处的路径曲率。
11. **`curvature_at_+10m`**: 前方10米处的路径曲率。
12. **`curvature_at_+15m`**: 前方15米处的路径曲率。
13. **`curvature_at_+25m`**: 前方25米处的路径曲率。

## 3. 曲率计算步骤

对于每个采样点，其曲率的计算流程如下：
1.  **定位车辆**: 找到车辆当前位置在参考路径上的最近点索引 `current_path_index`。
2.  **定位采样点**: 从 `current_path_index` 出发，沿路径向前或向后移动相应距离（如+10m或-15m），找到目标采样点的索引 `sample_index`。
3.  **计算曲率**:
    - 在 `sample_index` 附近取三个点 `P1`, `P2`, `P3`（例如 `path[sample_index - 5]`, `path[sample_index]`, `path[sample_index + 5]`）。
    - 这三点定义了一个三角形，计算其外接圆的曲率（半径的倒数）。
    - 通过向量叉积判断方向，为曲率赋予正负号（例如，左转为正，右转为负）。

# 强化学习： SAC模型构建

我们最终确定的强化学习环境核心要素设计如下。

## 碰撞检测方案 (最终版): 基于指令与现实的矛盾

经过多轮探讨与实验，我们最终确定了一套不依赖于任何高层规划器状态、仅基于车辆物理行为的碰撞检测方案。该方案健壮且能有效避免起步时的误判。

### 核心逻辑
碰撞被定义为：**系统期望车辆前进，但车辆在物理世界中却卡住了。**
我们通过比较**指令速度**和**实际速度**的差异来捕捉这个矛盾。

- **指令速度 (`v_cmd`)**: 从 `/control/command/control_cmd` (类型 `AckermannControlCommand`) 中的 `longitudinal.speed` 字段获取。
- **实际速度 (`v_actual`)**: 从 `/localization/kinematic_state` (类型 `Odometry`) 中的 `twist.twist.linear.x` 字段获取。

### "卡住"条件的判定
在强化学习环境的每一步，我们检查以下条件是否满足：
`is_stuck = (v_cmd > V_threshold) and (abs(v_actual) < E_threshold)`

- `V_threshold`: 指令速度阈值，用于判断系统确实在命令车辆前进。推荐值: **1.0 m/s**。
- `E_threshold`: 实际速度阈值，用于判断车辆在物理上已接近静止。推荐值: **0.1 m/s**。

### 解决起步误判：延迟容忍机制

为了防止在车辆正常起步时（指令速度已发出，但车辆因惯性暂未移动）发生误判，我们引入一个“卡住计数器” (`stuck_counter`)。

1.  **计数器更新**:
    - 如果 `is_stuck` 条件为 **True**，则 `stuck_counter` 加 1。
    - 如果 `is_stuck` 条件为 **False**（车辆正常行驶或完全静止），则 `stuck_counter` **立刻清零**。
2.  **碰撞最终判定**:
    - 只有当 `stuck_counter` 累积超过一个“容忍步数”(`COLLISION_GRACE_STEPS`)时，我们才最终判定为碰撞。
    - `COLLISION_GRACE_STEPS`: 一个代表“容忍延迟”的帧数。例如，在30Hz的频率下，设定为 **15** 步，即代表系统可以容忍长达 **0.5秒** 的起步延迟。
3.  **环境重置**: `stuck_counter` 必须在每次环境重置时 (`env.reset()`) 被清零。

该方案可以完美区分**短暂的起步延迟**和**持续的碰撞卡住**两种状态。

## 奖励函数设计 (最终版)

奖励函数是引导智能体学习期望行为的核心。我们的设计旨在平衡速度、路径保持、安全规则和驾驶技巧，以达成以下学习目标：
1. 尽可能的加速，减少用时
2. 速度上限为35kmh，当超过上限的时候，会被惩罚降速到5km，因此严禁超速
3. 一阶段的开发中，输出路径是固定的，因此尽量保持车道
4. 而未来的二阶段的开发中，路径坐标不一定，所以如何适配最优行车线则是一个重点。这里的最优行车线的意思，不一定是始终在车道最中央，而是根据未来的车道的曲率来规划最优路径。
5. 严禁撞墙
6. 一阶段的重点是学会如何控制入弯速度，也就是Slow-in-Fast-out,即入弯之前的直道就减速，经过弯心后开始加速。

**总奖励 R = R_progress + R_lane_keeping + R_penalty**

### 1. `R_progress` (前进奖励)
- **目标**: `1. 尽可能加速，减少用时`。这是智能体探索的主要动力。
- **设计**: 与车辆的**纵向速度**成正比。
- **公式**: `R_progress = w_progress * current_velocity_x`
  - `w_progress`: 权重系数，例如 `1.0`。

### 2. `R_lane_keeping` (车道保持惩罚)
- **目标**: `3. 保持车道` & `6. 学会Slow-in-Fast-out`。
- **设计**: 对偏离中心线和航向错误施加二次方惩罚。这是**催生出 Slow-in-Fast-out 策略的关键**。当车辆高速入弯导致较大误差时，此项的巨大惩罚会迫使智能体学会在入弯前减速，以换取更小的路径误差和更高的长期回报。
- **公式**: `R_lane_keeping = -w_center * (distance_from_centerline)^2 - w_heading * (heading_error)^2`
  - `w_center`, `w_heading`: 权重系数，例如 `0.5`。

### 3. `R_penalty` (硬性规则惩罚)
- **目标**: `2. 严禁超速` & `5. 严禁撞墙`。
- **设计**: 对触犯关键安全规则的行为施加巨大的、固定的负奖励。

- **超速惩罚**:
  - **逻辑**: 当车辆实际速度 `current_velocity_x` 超过 35 km/h (约 9.72 m/s) 时触发。
  - **奖励**: `P_overspeed` (一个较大的负数, e.g., **-10**)。

- **碰撞惩罚**:
  - **逻辑**: 由我们上述的**碰撞检测方案**触发时。
  - **奖励**: `P_collision` (一个巨大的负数, e.g., **-500**)。
  - **效果**: 触发此惩罚时，环境应**立即终止**当前回合 (`done=True`)。

### (可选) `R_time` (时间惩罚)
- **目标**: 鼓励智能体用更少的时间完成任务，避免在原地不动等消极行为。
- **设计**: 在每一步都给予一个小的负奖励。
- **公式**: `R_time = P_time` (一个小的负常数, e.g., **-0.1**)。