## 状态

**已可开始实施——Ray Data 与 Lance 是已批准的一期后端组合。**

English version: [design.md](design.md)

## 背景

M1a 提供不可变且来源无关的 Episode，M1b 提供不可变的数据集成员关系和血缘，M2 将 ROS 2 MCAP 导入该边界。M3 在不让既有契约依赖具体框架的前提下，补齐第一套计算与存储数据平面。

## 目标 / 非目标

**目标**

- 本地和 Ray Data 均可执行有界、以 Episode 为单位的处理计划。
- 将不可变 Dataset Release 的一个已校验物化版本持久化为 Lance。
- Domena 的 Release 身份、血缘和质量证据仍是权威；Lance 版本仅是物理输出引用。
- Ray/Lance 均为可选依赖，未安装时核心导入仍可用。

**非目标**

- 不实现 Daft、Spark、Flink、流式数据平面、云端调度器、分布式目录、向量检索 API 或训练执行器；其中 Daft 的执行器接入点会在本次变更中固定。
- M3 不把全部来源模态解码成列式负载；尚未处理的大型资产保留稳定定位符。
- 不把 Ray Object Store 当作持久数据存储。

## 决策

### 1. Domena 拥有计划、运行记录和物化身份

`TransformPlan` 标识不可变输入 `DatasetManifest`、带版本的确定性处理声明及目标输出模式。`JobRun` 分别记录逻辑处理引擎（`engine_name`）和执行运行时（`runtime_name`），以及状态、输入 Release 指纹、处理指纹、时间和失败证据。这样后续 Daft 引擎既可在本地运行，也可使用 Ray 作为分布式运行时，而无需修改任务运行契约。`MaterializationReference` 将完成的运行绑定到 Domena Release 指纹、后端名、URI、后端快照/版本、模式指纹和校验和。

Domena Release 指纹永远不由 Lance 表版本推导；一个 Release 在未来可以对应多个物理物化版本。

### 2. Ray Data 是一期唯一的分布式执行器

`RayDataExecutor` 把有界计划转换为 Ray Data 数据集，使用显式批处理/资源选项执行获批准的处理函数。它只能写入独立的 staging 输出；协调者校验输出元数据后，才原子性地写入成功的 Domena 物化引用。失败或取消的任务不能成为已发布物化版本。

本地执行器实现同一可观察计划契约，用于单元测试与开发者本地流程；它有意保持单进程和有界。

### 3. Lance 是一期的多模态数据湖格式

`LanceMaterializer` 将 Release 转换为 Arrow 兼容行。每一行包含 Domena 身份/血缘字段，以及来源无关的 Step 与资产定位符表示。已解码的标量通道可表达为 Arrow 类型；媒体、点云、ROS payload 和尚不支持的数据必须以带校验和的显式定位符保留，不能静默复制或解码。

物化器先写入 staging Lance 数据集，再校验行数、Release 指纹与模式指纹，成功后才发布 `MaterializationReference`。初始读取器支持按 Release 扫描，及按 `(source_namespace_id, episode_id)` 查询；不提供通用查询服务。

### 4. 依赖与包边界

`domena.core`、Episode 和 Manifest 模块不得导入 Ray、Lance 或 PyArrow。引擎模块是延迟加载的可选集成。公开 extra 为 `ray`、`lance` 与二者组合。需要这些 extra 的测试独立标记，依赖缺失时给出清晰跳过原因；核心测试无需引擎即可运行。

### 5. 固定 Daft 执行器接入点，但不实现 Daft

Domena 自有的计划/运行/物化契约不以 Ray 或 Lance 命名。核心会定义最小 `BoundedExecutor` 协议：接收不可变 `TransformPlan` 与显式执行选项，产生不可变 `JobRun`；只有验证通过的物化才可发布。`LocalExecutor` 与 `RayDataExecutor` 必须实现它，`DaftExecutor` 预留为下一个迭代的同等实现，且不允许其绕过计划、指纹、staging 或发布校验。

这不是预先抽象 Daft 的算子 API：一期处理函数仍以 Ray Data 的可执行约束为准。接入 Daft 时，只需要实现计划到 Daft DataFrame 的映射、将执行状态写回 `JobRun`，并复用 Lance 物化与发布边界。Spark/Flink 既不保留实现入口，也不在一期设计中承诺。

## 风险与权衡

- [Ray/Lance 在本地的安装与 ABI 差异] → 使用可选 extra、延迟导入、兼容版本约束和集成测试标记。
- [大型资产解码或复制成本高] → M3 保留定位符，后续以显式的格式适配物化器处理。
- [分布式部分输出可能被误认为 Release] → staging URI、校验和协调者控制的单点发布。
- [通用执行器抽象过度设计] → `BoundedExecutor` 仅包含计划提交、状态与结果引用；不抽象 Ray/Daft 的算子图或优化器。

## 迁移计划

1. 增加无外部依赖的契约和本地实现。
2. 增加可选的 Lance 物化与校验。
3. 增加对同一有界计划的可选 Ray Data 执行。
4. 用一个来自 M2 MCAP 的本地 Manifest 演示 M3 物化路径；既有 JSON Manifest 工作流继续可用。

## 开放问题

- 一期边界没有待确认项。首批 Arrow 列命名和处理函数集合由实现决定，但必须遵守规范性规格。
