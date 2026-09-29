# Domena

[English](README.md)

**面向具身智能与物理 AI 的经验数据基础设施。**

Domena 是一个开源的 Python 数据平面项目，服务于机器人与智能体同物理世界交互时产生的经验数据：仿真、真实机器人及人类遥操作。

其目标数据闭环是：

> Experience（经验）→ Dataset（数据集）→ Training / Evaluation（训练 / 评估）→ Better Experience（更好的经验）

项目已启动 M1a：数据源无关的 Experience 契约实现。它尚未提供真实机器人或模拟器适配器、数据集格式或训练框架。

## 项目状态

Domena 目前处于首个实现阶段。面向用户与贡献者的公开文档会在对应接口和行为稳定后发布到 `docs/`。

已确定、可直接实施的变更设计记录在 [`openspec/`](openspec/)；探索性设计笔记与调研来源仅保存在本地，不属于仓库内容。

## 许可证

[MIT](LICENSE)
