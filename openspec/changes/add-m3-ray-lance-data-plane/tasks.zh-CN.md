## 1. 核心执行契约

- [x] 1.1 新增不可变处理计划、分别记录引擎与运行时身份的任务运行记录、物化引用和最小 `BoundedExecutor` 协议，提供规范指纹和校验。
- [x] 1.2 实现确定性的本地有界执行器及聚焦的核心测试。

## 2. Lance 数据湖集成

- [x] 2.1 增加可选 `lance` extra 与延迟加载集成边界。
- [x] 2.2 实现 staging Lance 物化、校验和 Release 范围读取。
- [x] 2.3 使用经筛选的 M1b/M2 兼容 Fixture Release 增加 Lance 集成测试。

## 3. Ray Data 执行集成

- [x] 3.1 增加可选 `ray` 和组合 `ray,lance` extra，以及延迟导入错误。
- [x] 3.2 为首批有界处理集合实现 Ray Data 执行，包括显式批处理/资源配置。
- [x] 3.3 增加 Ray/本地一致性测试，以及失败运行发布安全测试。

## 4. 验证

- [x] 4.1 在未安装可选依赖时运行核心测试，安装 extra 时运行引擎集成测试。
- [x] 4.2 严格校验该 OpenSpec 变更。

## 后续迭代预留（不在 M3 实现）

- [ ] D1 实现 `DaftExecutor`：将相同的 `TransformPlan` 映射到 Daft DataFrame，复用 `JobRun`、Lance 物化和发布校验。
