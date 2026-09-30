## 新增需求

English version: [spec.md](spec.md)

### Requirement: 可选来源适配器边界

系统 SHALL 仅从外层适配器模块暴露 ROS 2 MCAP 导入能力。导入 Domena 核心契约 SHALL NOT 要求安装 ROS 2、MCAP 或 ROS 消息包。

#### Scenario: 报告缺失的可选适配器依赖

- **WHEN** 调用者在未安装 `rosbag2` 可选依赖时调用本地 MCAP 读取
- **THEN** 适配器抛出明确错误，并说明 `domena[rosbag2]` 安装 extra

### Requirement: 显式 Episode 边界与 topic 语义

系统 SHALL 接受且仅接受一种导入边界模式：一个显式的整 bag Episode，或一组调用者提供的有序记录时间分段。分段区间 SHALL 为半开、非空且不重叠。每个导入 topic SHALL 使用显式的 Domena 通道组和通道名绑定。

#### Scenario: 导入多个已声明分段

- **WHEN** 调用者提供两个不重叠、Episode ID 不同的分段区间
- **THEN** 每条记录只在所属半开区间转换为其声明的 Episode，且不发生自动分段

#### Scenario: 拒绝模糊的导入边界

- **WHEN** 调用者同时提供整 bag Episode ID 和分段，或者两者均未提供
- **THEN** 导入计划校验在读取来源前失败

### Requirement: 事件原生时间保留

系统 SHALL 把选中记录作为确定性有序的事件原生 steps 输出，不进行自动同步或重采样。有可用消息 header 时间戳时 SHALL 使用该时间，否则使用 bag 记录时间，并在适配器证据中保留两者和回退状态。

#### Scenario: 无 header 时间戳时回退

- **WHEN** 被选消息不含有效 header 时间戳
- **THEN** 其 step 使用 bag 记录时间，且转换证据标记发生了回退

### Requirement: 已支持与不透明载荷转换

系统 SHALL 将 `JointState`、`Imu`、`Twist` 和 `TFMessage` 物化为 JSON 兼容值。系统 SHALL 将 `Image` 与延后处理的消息族表示为确定性的 `AssetReference`；资产包含不透明 MCAP 定位符及来源元数据，默认不复制其 payload 字节。

#### Scenario: 保留图像但不物化字节

- **WHEN** 导入一个已绑定的 ROS 图像记录
- **THEN** step 通道包含 `AssetReference`，相应资产能标识 MCAP 记录但不嵌入图像字节

#### Scenario: 保留延后处理的点云记录

- **WHEN** 调用者绑定一个 `sensor_msgs/msg/PointCloud2` 记录
- **THEN** 适配器保留带原始 ROS 类型的不透明资产引用，而不尝试解码

### Requirement: 可复现的来源证据

系统 SHALL 在来源适配器命名空间的 Episode 元数据中记录 bag 校验和、选择的边界、绑定、来源消息类型清单和转换证据。

#### Scenario: 标识已转换 Episode 的来源

- **WHEN** 适配器转换一个本地 MCAP 来源
- **THEN** 结果 Episode 含有足以标识来源 bag 与转换配置的 JSON 兼容证据，且不要求核心层提供来源解析器
