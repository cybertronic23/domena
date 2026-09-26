# Domena

[English](README.md)

**面向具身智能与物理 AI 的经验数据基础设施。**

Domena 是一个开源的 Python 数据平面项目，服务于机器人与智能体同物理世界交互时产生的经验数据：仿真、真实机器人及人类遥操作。

其目标数据闭环是：

> Experience（经验）→ Dataset（数据集）→ Training / Evaluation（训练 / 评估）→ Better Experience（更好的经验）

项目当前处于架构与领域设计阶段，尚未提供公开的经验 Schema、模拟器适配器或数据集格式。

## 项目方向

Domena 将提供从数据来源，经由经验校验和处理，到训练与评估可消费数据集的清晰边界；同时保持对任何单一模拟器或机器人平台的独立性。

请参阅[架构说明](docs/architecture.zh-CN.md)、[经验模型讨论](docs/experience-model.zh-CN.md)、[路线图](docs/roadmap.zh-CN.md)和首份[工程规范](docs/specs/001-experience-schema.zh-CN.md)。

## 许可证

[MIT](LICENSE)
