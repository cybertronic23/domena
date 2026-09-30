## 状态

**已可开始实施——规范性规格与任务均已批准。**

English version: [proposal.md](proposal.md)

## 为什么做

M1a 建立了来源无关的 `Episode` 契约，M1b 使数据集成员关系可复现。下一条实际可用的数据边界是接入真实机器人数据。ROS 2 的 MCAP bag 能保存多模态机器人记录，同时又可以保持核心层与 ROS 解耦，因此适合作为第一个来源。

## 本次变更

- 新增可选、延迟加载的 `domena.rosbag2` 离线本地 ROS 2 MCAP 适配器。
- 在适配器边界把已支持的 ROS 消息转换为来源无关的 `Episode`。
- 同时支持“一个 bag 显式声明为一个 Episode”和“调用者提供不重叠的记录时间切分索引”。
- 小型数值消息物化为 JSON 通道值；图像与暂不解码的模态保留为可复现的 MCAP 不透明资产引用。
- 保留来源、时间、topic、类型与转换证据，但不向核心包引入 ROS 概念。

## 不做什么

- 不支持 ROS 1 bag、实时订阅、写 bag、回放控制、云端接入、UI、自动切分、自动同步、标定推断或质量打分。
- M2 不解码 `PointCloud2`、力/触觉或自定义消息。
- 不直接导出 LeRobot、RLDS、Open X-Embodiment、HDF5 或训练框架格式。

## 影响

- 新增可选 `rosbag2` 依赖 extra；基础 `domena` 保持无依赖，也不要求安装 ROS。
- 只新增适配器公开 API；M1a/M1b 契约与序列化保持来源无关且向后兼容。
