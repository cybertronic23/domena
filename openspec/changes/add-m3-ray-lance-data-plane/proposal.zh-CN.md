## 状态

**已可开始实施——Ray Data 与 Lance 已确认为一期的计算和存储引擎。**

English version: [proposal.md](proposal.md)

## 为什么做

M1a、M1b 与 M2 已能描述、版本化和导入具身经验数据，但项目仍不能执行分布式处理，也不能将多模态数据集物化为可训练、可检索的存储形态。一期需要一套统一的数据平面，而不是一批与引擎强耦合的脚本。

## 本次变更

- 新增基于 Ray Data 的可选分布式、有界数据处理集成。
- 新增基于 Lance 的可选多模态数据物化集成，支持不可变输出引用和面向训练的扫描。
- 新增由 Domena 拥有、而非由 Ray 或 Lance 拥有的来源无关处理任务和物化引用契约。
- 新增一个用于确定性测试与本地兜底的小型本地执行器；一期的唯一分布式执行引擎是 Ray，并固定 Daft 的后续执行器接入契约但不引入 Daft 依赖。
- 新增 `domena[ray]`、`domena[lance]` 与 `domena[ray,lance]` 可选依赖。

## 能力

### 新增能力

- `data-plane-execution`：来源无关的有界处理计划、任务生命周期记录，以及本地/Ray Data 执行。
- `lance-materialization`：Domena 数据集 Release 的确定性 Lance 物化与校验。

### 修改能力

- 无。

## 影响

- 新增执行计划/运行记录、Lance 物化相关公开模块，以及可选 Ray 和 Lance 依赖。
- M1a `Episode`、M1b `DatasetManifest` 与 M2 适配器保持来源无关和向后兼容。
- 本变更不实现 Spark、Flink 或 Daft；Daft 仅固定执行器接入点，Spark/Flink 不保留实现入口。也不引入云端控制平面、流式采集或可变数据目录。
