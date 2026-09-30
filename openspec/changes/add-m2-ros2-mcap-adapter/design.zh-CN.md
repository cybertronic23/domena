## 状态

**已可开始实施——规范性规格与任务均已批准。**

English version: [design.md](design.md)

## 设计

### 边界与可选加载

`domena.rosbag2` 是外层适配器包，只依赖 M1a 契约；`mcap` 与 `mcap_ros2` 均延迟导入。导入 `domena` 或其他核心 API 不会导入这些依赖。调用 MCAP 读取但没有安装 extra 时，适配器给出明确提示：`pip install "domena[rosbag2]"`。

### 显式导入计划

`RosbagImportPlan` 包含非空任务 ID、来源命名空间、显式 `topic_bindings` 映射，以及且仅有一种边界模式：

- `whole_bag_episode_id`：整个 bag 对应一个 Episode；或
- `segments`：有序的 `RosbagSegment(episode_id, start_time_ns, end_time_ns)` 元组。

切分使用 bag 记录时间与半开区间 `[start_time_ns, end_time_ns)`。每段必须非空、有序且互不重叠，不做任何启发式自动切分。Topic 绑定明确指向 Domena 通道组（`observations`、`actions`、`state`、`feedback`）及非空、来源无关的通道名；消息类型不能静默决定其语义角色。

### 事件原生转换

适配器对每条被选中且已绑定的消息记录生成一个 `Step`，按 `(effective_step_timestamp_ns, record_time_ns, topic, source_sequence)` 确定性排序；不重采样、不自动同步模态。有 header stamp 时作为 step 时间戳，否则回退到 bag 记录时间。原始记录时间和是否发生回退保留在适配器命名空间的转换证据中。

### 已支持消息的物化策略

`sensor_msgs/msg/JointState`、`sensor_msgs/msg/Imu`、`geometry_msgs/msg/Twist` 与 `tf2_msgs/msg/TFMessage` 转为 JSON 兼容值。`sensor_msgs/msg/Image` 转为不提取、不复制字节的 `AssetReference`。资产 ID 由 bag SHA-256、topic、记录时间和来源序列号确定性生成；不透明 `mcap://` 定位符与图像元数据保留在 episode 资产及 `io.domena.rosbag2:conversion` 证据中。

尚未实现的消息类型（含 `PointCloud2`、力/触觉和自定义消息）不进行解码。调用者若绑定它们，仍会保留为带原始 ROS 类型的 MCAP 不透明资产引用。未绑定消息只记录在来源清单证据中，不能被推断为某个 Domena 通道。

### 溯源

每个输出 Episode 都记录来源 bag 路径、bag SHA-256、选用的分段模式/范围、topic 绑定、来源消息类型与适配器标识等 JSON 兼容的 provenance/extensions。适配器使用 `io.domena.rosbag2:conversion` 扩展键，满足核心扩展命名空间规则；核心层不新增来源解析器。

### 本地测试切面

消息枚举以内部记录协议表达。测试使用合成的已解码记录，不需要 ROS、MCAP 或硬件。生产枚举器委托 `mcap_ros2.reader.read_ros2_messages`，并在来源边界转换它的值。
