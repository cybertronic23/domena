## 状态

**已批准——M3.5 完成产品边界准备，M4 交付 Web Public Alpha。**

English version: [proposal.md](proposal.md)

## 背景

M1–M3 已建立 Domena 的数据源无关 Experience 契约、数据集血缘、ROS 2 MCAP 接入、Ray Data 执行和 Lance 物化能力，但这些能力目前主要以 Python 库形式存在。Domena 面向公众的核心产品应当是 Web 平台：用户无需理解内部 Python API，也可以导入具身数据、定义 Episode 边界、运行处理任务、检查数据质量并发布可追溯的数据集版本。

因此，对外开放节点调整到 M4 结束。CLI 继续作为高级工程师和自动化场景的入口，但不是主要产品形态。

## 变更内容

- 在 M3.5 增加控制面/数据面交换契约，并在服务开发前固定面向产品的任务生命周期。
- 增加以 PostgreSQL 为基础的 Go 控制面，负责身份、工作空间、项目、数据源、数据集、任务、审计状态和 API 编排。
- 增加 TypeScript 单页 Web 产品，覆盖完整的 ROS 2 MCAP 到 Lance 工作流。
- 增加由既有 Ray/Lance 数据面执行的 Python 质量算子和持久化质量报告。
- 明确对象存储边界：原始资产、Lance Release 和报告附件存入对象存储；PostgreSQL 只保存元数据。
- 增加次要的 CLI/API 客户端入口，与 Web 使用同一套控制面 API 和领域语义。
- 增加可复现的单节点部署，以及 Public Alpha 所需的安全、可观测和端到端验证能力。

## 能力范围

### 新增能力

- `control-plane-orchestration`：产品级任务规格、生命周期、租约、幂等、项目隔离，以及 Go/Python 编排。
- `web-product-workflow`：浏览器中的数据源注册、Episode 规划、处理、Release 发布、质量检查和血缘工作流。
- `quality-reporting`：带版本、可复现的 Episode/Release 质量指标和失败切片。
- `public-alpha-deployment`：安全、可观测、可复现的单节点部署与发布门禁。

### 修改能力

- `data-plane-execution`：将 M3 的终态 `JobRun` 证据纳入更长生命周期的控制面任务，同时不改变 Release 或物化语义。

## 里程碑边界

- **M3.5**：规格、交换契约、API/状态机夹具、示例工作流和数据面加固；仍不对外开放。
- **M4a**：Go 控制面与 PostgreSQL 持久化。
- **M4b**：TypeScript Web 工作流。
- **M4c**：质量算子与质量报告产品。
- **M4d**：部署、安全、恢复、文档和端到端测试。
- **M4e**：发布 Public Alpha。

## 影响

- 仅在 M3.5 协议验证完成后增加 `control-plane/`（Go）、`web/`（TypeScript）和部署资产。
- `src/domena/` 继续作为权威 Python 数据面。
- 控制面数据库确定为 PostgreSQL；M4 不以 MySQL 为目标。
- 部署环境需要兼容 S3 的对象存储，本地测试可使用文件系统。
- M4 不引入 Kafka、Spark、Flink、Kubernetes、通用工作流引擎、协同标注、计费或完整训练服务。
