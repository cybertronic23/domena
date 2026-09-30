## 新增需求

### 需求：已校验的 Lance 物化
系统必须将有效的 Domena Dataset Release 物化至 staging Lance 数据集，其中包含 Domena 成员身份、Release 血缘、Step 表示及显式资产定位符。发布前必须校验输出行数、输入 Release 指纹和输出模式指纹。

#### 场景：物化不可变 Release
- **当** 向 Lance 物化器提交成功的有界处理结果
- **则** 系统先写入并校验 staging Lance 数据集，之后才发布

#### 场景：拒绝不完整输出
- **当** staging Lance 输出不匹配预期行数或指纹
- **则** 系统不得发布物化引用

### 需求：Domena Release 身份仍是权威
系统必须在每个 Lance 物化引用中保留 Domena Release 指纹，并单独记录 Lance URI 和后端版本或快照。系统不得将 Lance 版本用作 Domena Release 标识。

#### 场景：引用物理 Lance 输出
- **当** Lance 物化成功发布
- **则** 引用同时包含 Domena Release 指纹和独立标识的 Lance 输出

### 需求：可选 Lance 集成
Lance 物化器和读取器必须只通过可选 Lance 依赖提供，且不得使核心 Episode 或 Manifest 的导入依赖 Lance 或 PyArrow。

#### 场景：未安装 Lance 时使用核心
- **当** Lance 未安装
- **则** 仍可导入和使用 M1a、M1b 和 M2 的公开 API

#### 场景：读取已发布 Lance 输出
- **当** 已安装 Lance，调用者提供已发布物化引用
- **则** 读取器只返回该引用的 Domena Release 行，并保留来源命名空间和 Episode 身份
