## 状态

**已批准，可分阶段实现。**

English version: [design.md](design.md)

## 背景

Domena 的 Python 数据面已经拥有不可变 Experience、Dataset Release、有界处理计划、终态执行证据和经验证的 Lance 物化。M4 将在不把这些语义迁入 Web 框架、也不在 Go 中重复实现的前提下，增加面向用户的完整产品。

## 目标 / 非目标

**目标**

- Web 应用作为默认产品入口，CLI/API 作为高级入口。
- 保持严格的 Go 控制面 / Python 数据面边界。
- 让用户在一个产品工作流中完成 ROS 2 MCAP 注册、显式 Episode 切分、数据处理、Lance 发布、质量检查和血缘检查。
- PostgreSQL 事务化保存权威产品状态，对象存储/Lance 保存大体积不可变数据。
- M4 结束时交付可邀请用户使用的单节点 Public Alpha。

**非目标**

- PostgreSQL 不保存原始多模态载荷或 Lance 表。
- Go 或 TypeScript 不实现 MCAP 解析、质量计算或 Lance 写入。
- 浏览器不得直接访问 Ray、Python Worker、PostgreSQL 或无限制对象存储凭据。
- M4 不引入 Kafka、Kubernetes、多地域高可用、计费、匿名公开注册、协同标注、模型训练服务、Spark 或 Flink。
- Daft 仍是首个 Web 垂直闭环之后的执行器扩展，不得阻塞 M4 Public Alpha。

## 决策

### 1. 一个产品，三个有意区分的入口

TypeScript Web 应用是默认用户体验；带版本的 HTTP API 是共享自动化边界；CLI 和 SDK 的远程模式调用该 API，明确区分的本地模式可以为离线工程工作直接调用 Python 包。浏览器和 CLI 不得各自实现独立业务行为。

### 2. Go 负责控制面，Python 负责数据面

Go 服务负责认证集成、工作空间、项目、数据源注册、Episode 规划元数据、数据集/Release 目录、任务命令、幂等、租约、审计事件和面向用户的 API 响应。

Python Worker 负责数据源检查、MCAP 解码、Episode 构建、处理执行、质量计算、Ray Data 执行和 Lance 发布。Worker 接收带版本、不可变的任务规格，返回带版本的进度与终态证据。Go 将既有 Domena `JobRun` 和 `MaterializationReference` 视为数据面证据，而不重新实现其规则。

Python Worker 不直接写 PostgreSQL，而是通过经过认证的 Go 内部接口租用任务并上报进度/结果，从而保持数据库单一所有者并缩小 Worker 凭据范围。

### 3. PostgreSQL 是权威元数据存储

PostgreSQL 保存账户/身份、工作空间、项目、数据源注册、Episode 规划、数据集目录元数据、Release 指纹、任务、执行尝试、质量报告摘要、审计事件、幂等记录和对象引用。

数据库迁移按顺序执行，发布后不可修改。所有租户数据行都带 `workspace_id`；服务执行授权检查，数据库约束进一步保证隔离。JSONB 可用于带版本的配置和证据，但不得替代核心关系身份或状态迁移约束。

### 4. 对象存储和 Lance 保存数据，而不是产品状态

原始 MCAP/HDF5/媒体、生成的 Episode 资产、完整质量报告和 Lance 数据集存入兼容 S3 的对象存储。本地开发可在相同对象引用契约后使用文件系统实现。上传使用短时、限定范围的 URL；浏览器永远不能获得通用对象存储凭据。

Lance 继续作为物理多模态数据集格式。已发布产品 Release 必须引用 Domena Release 指纹和经验证的 `MaterializationReference`，不能只用对象路径或 Lance 版本标识。

### 5. 产品任务生命周期包裹不可变执行尝试

控制面任务状态机为：

`queued → leased → running → succeeded | failed | cancelling → cancelled`

只有在租约过期且未接收终态结果后，`leased` 任务才可回到 `queued`。取消在 Worker 确认之前是控制面请求状态。每次重试创建新的不可变 attempt，同时保留稳定的产品 job 身份。会发布 Release 的任务只有携带经验证的物化证据才能成功。迟到或重复事件必须幂等接受或拒绝，且不得使状态倒退。

M3.5 固定 JSON 兼容的交换信封，包括模式版本、任务身份、工作空间/项目身份、任务类型、输入引用、确定性配置、请求的 engine/runtime、输出目标、attempt 编号和幂等键。只允许秘密引用，不得嵌入凭据。

### 6. 在消息代理之前使用 PostgreSQL 调度

M4 通过事务化任务创建以及 Go 内部 API 暴露的有界 Worker 租约进行调度。PostgreSQL 锁和租约过期提供初始可靠分发，事务发件箱记录需要对外传播的事件。只有在实测规模或交付需求出现后，才可以引入 Kafka/NATS 或工作流引擎，且不得改变任务交换契约。

### 7. Web 应用采用轻量 TypeScript SPA

默认实现使用 TypeScript、React、Vite、TanStack Query、由 OpenAPI 生成的类型化客户端和小型无障碍组件层。认证后的数据应用不需要服务端渲染。信息架构包括：

- 登录与工作空间选择；
- 项目概览；
- 数据源与源数据检查；
- MCAP Topic/时间线检查与 Episode 切分；
- 数据集与不可变 Release；
- Pipeline/Job 与运行诊断；
- 质量报告与失败切片；
- 数据血缘；
- 工作空间设置。

### 8. 质量报告是带版本的数据产品

第一版报告记录通道存在性、Step/时间覆盖、时间戳单调性、观测频率、间隙、Episode 时长和校验问题。指标必须标识算子 ID/版本、配置指纹、源 Episode/Release 指纹和生成时间。Release 聚合报告链接到 Episode 证据。基于阈值的质量策略必须显式且带版本，指标不得被静默转成通过/失败。

### 9. Public Alpha 先支持受邀用户与单节点部署

参考部署使用容器运行 Web 静态资产、Go API、Python Worker、PostgreSQL、兼容 S3 的对象存储和 Ray Runtime。它必须支持健康/就绪检查、迁移、有界上传、结构化日志、请求/任务关联 ID、控制元数据备份、取消、重试和有文档的恢复流程。M4 不要求 Kubernetes。

初始认证可以使用受邀 OIDC，不要求匿名公开注册。工作空间授权、上传限制、内容类型校验、受限对象访问、审计记录和资源配额都是发布阻断项。

## 兼容性

- 既有 M1–M3 Python 公开契约继续受支持。
- 新交换模式从 `v0.1` 开始，1.0 前的演进也必须显式版本化。
- Web 和 CLI 使用同一带版本 API；本地 CLI 行为必须明确区分，且不能暗示远程持久化。
- M4 不重命名 Domena Release 指纹、Episode 复合身份或 Lance 发布证据。

## 风险 / 权衡

- [M4 范围过大] → 只交付一条 ROS 2 MCAP 到 Lance 的垂直闭环，推迟通用工作流构建器。
- [Go 与 Python 重复领域逻辑] → Go 保存和编排带版本证据，Python 继续对数据校验与执行负责。
- [PostgreSQL 调度达到规模瓶颈] → 保持消息代理无关的租约契约，只在实测需要后增加代理。
- [对象存储造成不安全访问] → 使用受限上传/下载授权、校验和验证、协议白名单，浏览器不持有凭据。
- [Web UI 隐藏可复现信息] → 每个 Run/Release 都展示指纹、版本、配置、证据和血缘。
- [质量分数产生误导] → 发布指标证据和带版本策略，不提供单一不透明分数。

## 实现顺序

1. M3.5：交换契约、状态迁移测试、任务示例夹具、API 资源词汇和数据面质量报告契约。
2. M4a：Go 服务骨架、PostgreSQL 迁移/仓储、OpenAPI、认证/工作空间边界、任务租约和 Python Worker 集成。
3. M4b：TypeScript 产品骨架及数据源/Episode/数据集/任务端到端工作流。
4. M4c：质量算子、质量报告持久化，以及报告/失败切片页面。
5. M4d：容器部署、安全加固、可观测性、恢复、文档和端到端测试。
6. M4e：打标并发布 Web Public Alpha。

## 待定问题

M4 架构边界没有待定问题。具体 OIDC 提供方和视觉组件库属于部署选择，不得改变本规格规定的安全或 API 行为。
