# TopoLab 开发周期与资源评估

相关文档：[美研申请匹配度评估](./TopoLab_admissions_fit_assessment.md) · [Numerical Core 重写策略](./TopoLab_reimplementation_strategy.md)

## 目标项目

**TopoLab — Scalable 3D Topology Optimization Platform with Learned Warm Starts**

本报告评估从当前 Hack3D/3D SIMP 代码基础出发，在大量使用 Codex 辅助开发的情况下，把 TopoLab 建设为符合美研申请高标准的完整项目所需的时间、开发阶段、计算资源和现实世界条件。

## 当前起点（2026-09-17）

- [`keith1117/TopoLab`](https://github.com/keith1117/TopoLab) 已完成 G0 仓库准备，包含 README、MIT License、provenance 记录、锁定环境、最小包结构、测试和 CI。
- 上游参考仓库固定为 `Jiangce2017/3D_SIMP_Topology_Optimization_Numpy@584cb8ee570d375f8ba9b10272020c5c2daa8c30`。
- 上游仓库没有声明开源许可证。因此 TopoLab 只把它作为行为参考和审计基线，不复制或重新分发源文件；新核心依据标准 SIMP/Hex8 资料独立实现，并在 `PROVENANCE.md` 中记录来源。
- 当前本地已有上游代码、运行图和前期审计，但这些不属于新 TopoLab 的实现成果。

### G0 执行记录（2026-09-17）

- [x] 克隆 TopoLab 仓库并保留既有初始 README commit；
- [x] 为 TopoLab 原创代码和文档选择 MIT License；
- [x] 添加 README、`PROVENANCE.md`、`.gitignore`、`pyproject.toml` 与贡献规则；
- [x] 锁定 Python 3.12、NumPy、SciPy、Pydantic、pytest、Ruff 和 mypy 依赖；
- [x] 添加 GitHub Actions CI 配置与包导入 smoke test；
- [x] 记录开发机器的非敏感硬件信息和数值约定；
- [x] 将三份规划文档复制到新仓库 `docs/planning/`；
- [x] 推送 G0 commit，并确认远端 GitHub Actions run `35275304334` 通过。

G0 只建立开发与审计基础，不计作 Numerical Core 实现。

## Git 分支与版本管理策略

TopoLab 采用轻量级 **GitHub Flow**。项目由单人主导且处于快速迭代期，不维护长期 `develop`、`release/*` 或 `hotfix/*` 分支，以免增加合并成本和分支漂移。

### 分支规则

- `main` 始终保持可运行、可测试，作为唯一长期分支；禁止 force push。
- 每个独立、可审查的改动从最新 `main` 创建短期分支，建议在半天到 3 天内完成。
- 分支前缀使用 `feat/`、`fix/`、`docs/`、`test/`、`bench/` 或 `experiment/`，名称描述交付内容而非人员姓名。
- 一个分支只处理一个明确切片；数值实现、平台功能和 ML 实验不混在同一 PR 中。
- 即使单人开发也通过 PR 合并，以保留设计说明、CI 结果和审查记录；CI 全部通过后 squash merge，并删除远端分支。
- `main` 建议启用 required status checks、合并前必须与主分支同步和禁止 force push；单人阶段不强制 reviewer，后续有稳定协作者再启用审批要求。

### 近期分支顺序

| 分支 | 范围 |
|---|---|
| `feat/n1-hex8-mesh` | 结构化 Hex8 网格、节点/单元/DOF 索引约定及相应测试 |
| `feat/n1-element-stiffness` | 材料矩阵、Hex8 单元刚度和局部数值验证 |
| `feat/n1-sparse-assembly` | COO/CSR 全局装配、边界条件和线性求解 |
| `feat/n1-boundary-load-models` | 支撑、点载荷/面载荷模型和载荷守恒测试 |
| `feat/n2-sensitivity` | compliance、解析 sensitivity 与有限差分检查 |
| `feat/n2-simp-optimizer` | filter、OC 更新和完整 SIMP 循环 |
| `feat/p1-api-jobs` | N2 通过后的 API、任务状态与运行隔离 |
| `feat/platform-run-persistence` | SQLite 运行持久化、终态恢复和进程中断语义 |
| `feat/platform-run-history` | UTC 生命周期时间、稳定游标分页与运行历史 API |
| `feat/frontend-run-history` | React/TypeScript 运行历史、状态和结果详情页面 |
| `feat/frontend-density-visualization` | 最终 physical density 的交互式 3D 结果可视化 |
| `feat/frontend-run-submission` | 结构化问题配置、运行提交和所选活动运行的终态刷新 |
| `feat/frontend-convergence-visualization` | 同状态 compliance、体积分数和 density change 收敛曲线 |
| `feat/frontend-run-cancellation` | 活动运行取消请求、请求中反馈和 cooperative cancellation 终态轮询 |
| `bench/sparse-solver-performance` | 四档稀疏装配/求解时间、峰值内存和稠密存储对照 |
| `experiment/m1-warm-start-cnn` | M0 通过后的 learned warm-start 对照实验 |

分支列表是当前执行顺序，不是必须提前创建的固定结构。只有前一切片的接口和测试稳定后，才创建下一分支；发现独立缺陷时，从最新 `main` 创建 `fix/*` 分支。

### 里程碑版本

里程碑使用 annotated Git tag 标记，不另设 release 分支：

- `v0.1.0`：Gate N1 通过；
- `v0.2.0`：Gate N2 通过；
- `v0.3.0`：Gate P1 通过；
- `v1.0.0`：公开演示、复现实验和文档达到发布标准。

Gate P1 已通过。SQLite 持久化、重启恢复、稳定游标分页、运行历史、结果详情、
最终 physical density 的交互式 3D 可视化，以及首版问题配置与运行提交已经完成。
同状态 compliance、physical volume fraction 和 density change 收敛曲线，以及
前端 cooperative run cancellation 控制也已完成。四档稀疏装配/求解性能与峰值
内存 benchmark 也已完成；其方法、结果和限制记录在
`docs/validation/sparse_solver_benchmark.md`。下一阶段进入 M0，冻结 case schema、
生成器版本、数据分割和 baseline。前十二个 M0 切片已在
`docs/ml_experiment_contract.md` 冻结这些契约、加入 typed case identity，实现
确定性 case encoding 与 filtered-volume projection，并加入验证分区、cohort、
OOD 配对和 provenance 元数据的 typed dataset manifest，以及拒绝未收敛和
不一致终态的单 case label generator、canonical JSON、SHA-256、内容寻址路径与
原子 label artifact 写入，并冻结可恢复、append-only、完整覆盖 case 的
manifest-to-label materialization index，以及按 canonical case 顺序执行、逐 case
原子 checkpoint、可中断恢复的单进程 materialization executor；并已冻结 160 个
case 的有界、content-identified production catalog，以及从 clean Git revision 和
locked environment 构建 manifest、默认只规划、显式执行且强制仓库外输出的
production entrypoint。首次完整外部执行已记录 156 个成功 label 和 4 个因 100
次迭代内未收敛而被正确拒绝的 OOD case；验证结果见
`docs/validation/m0_catalog_materialization.md`。第十一个切片已将 termination
budget 独立版本化为 120，冻结新的 catalog v2、case identities 与分区计数，而不
放宽 `0.01` 收敛容差或移除 case。catalog v2 随后从 clean revision 完整生成并经
artifact 审计，160 个 case 全部成功、零失败；证据见
`docs/validation/m0_catalog_v2_materialization.md`。因此 M0 gate 已通过。固定的
uniform、物理启发式和 training-only nearest-neighbor baseline runner 及其
成本/质量、失败和回退核算也已实现。下一独立切片应先冻结 M1 的轻量模型、损失、
训练预算和 checkpoint 选择规则，并建立只读取 train/validation artifacts 的
PyTorch dataset adapter；该切片现已完成，且尚未打开 test/OOD labels 或启动正式
训练。五个固定 seed 的确定性拟合循环、epoch history 和内容寻址
checkpoint/selection artifacts 现已实现。只允许 clean revision、固定外部 v2
materialization、锁文件和仓库外 artifact root，且默认仅规划的生产入口也已完成。
该入口已从合并后的 clean `main` revision 正式运行，五个 seed 均完成并通过 artifact
审计，证据见 `docs/validation/m1_training.md`；test/OOD 仍未打开。下一独立切片实现并
测试 learned inference、filtered-volume projection、SIMP refinement、fallback 和
成本/质量核算边界，然后才执行冻结的 held-out comparison。

## 总体时间估计

如果目标是完成独立 Numerical Core、数值验证、软件平台、ML warm-start、对照实验、OOD 测试、部署和文档，建议预留：

| 每日有效开发时间 | 预计周期 |
|---|---:|
| 每天 6–8 小时 | **约 8–11 周** |
| 每天 3–5 小时 | **约 10–14 周** |
| 每天 1–2 小时 | **约 16–22 周** |

更稳妥的整体预算是 **10–14 周、约 250–400 小时有效开发时间**。如果只完成强 CS/SWE 版本，不等待 ML 正向结果，目标可以压缩到约 6–9 周。

当前已经具备 3D SIMP 基础代码、已有运行输出和前期代码审计结果，因此无需从零开始。但 Codex 只能缩短代码实现、重构、测试编写、前端和文档工作的时间，不能完全消除以下成本：

- 验证数值结果是否正确；
- 定位稀疏求解器中的数值误差；
- 等待数据生成和模型训练；
- 判断 ML 模型是否真正优于 baseline；
- 完成 OOD、消融和多随机种子实验；
- 理解系统并准备申请材料和技术面试。

## 分阶段时间规划

| 阶段 | 预计时间 | 主要产物 |
|---|---:|---|
| 项目整理与基线冻结 | 2–3 天 | 独立仓库、环境配置、原始结果、项目规范和可复现实验入口 |
| 修复数值问题 | 5–8 天 | 载荷方向、总载荷、compliance、最终状态和边界条件修复 |
| 数值验证与测试 | 5–8 天 | 有限差分 sensitivity、载荷守恒、体积分数和小网格测试 |
| 稀疏化与性能优化 | 7–12 天 | 稀疏刚度矩阵、邻域过滤、运行时间和内存 benchmark |
| FastAPI 与异步任务系统 | 8–12 天 | API、worker、run ID、进度、取消、失败状态和数据库 |
| 3D 前端与结果管理 | 5–8 天 | 参数配置、3D 可视化、收敛曲线和历史实验页面 |
| 数据生成流水线 | 4–7 天开发，另加后台计算时间 | 不同载荷、支撑和体积分数的数据集 |
| ML warm-start | 7–12 天 | 模型训练、推理、SIMP 接入和可靠 fallback |
| Baseline、OOD 与消融实验 | 7–12 天 | 可用于简历和报告的量化实验结果 |
| 部署、CI、文档与演示 | 4–7 天 | Docker、CI、README、架构说明和演示视频 |

部分阶段可以并行。例如在后台生成数据时，可以继续开发前端、实验管理和文档，因此总体时间并非所有阶段的简单相加。

数值核心、平台和 ML 不能从第一天三线并行。只有 Numerical Core 达到 Gate N2 后，平台和数据生成才具有可信基础；大规模 ML 训练必须等数据生成与分割规则冻结。

## 开发门槛与放行条件

| Gate | 必须满足的条件 | 放行内容 |
|---|---|---|
| G0 仓库就绪 | README、许可证选择、`PROVENANCE.md`、环境锁定、CI smoke test、上游基线信息 | Numerical Core 开发 |
| N1 FEM 正确 | 小网格刚度对称、位移与稠密参考一致、载荷/反力平衡 | SIMP 与 sensitivity |
| N2 优化正确 | 有限差分 sensitivity、体积分数、最终状态 compliance、确定性回归测试通过 | API、worker、数据生成 |
| P1 平台可信 | 任务状态机、取消、失败、结果隔离和两任务并发测试通过 | 前端与公开 demo |
| M0 数据冻结 | case schema、生成器版本、train/val/test 分割和 baseline 固定 | ML 训练 |
| M1 ML 结论成立 | 同等质量约束下完成多种子、OOD 和端到端耗时比较 | 使用 learned/accelerated 表述 |

任何 Gate 未通过时，优先修复该层，不用上层功能掩盖底层问题。

## 三个完成等级

### Level 1：可运行 MVP

**预计周期：3–5 周**

完成内容：

- 修复主要数值问题；
- 建立基本数值测试；
- 提供 FastAPI 接口；
- 提供简单的 3D 结果页面。

这个阶段可以演示完整流程，但尚未达到高标准旗舰项目要求。预计整体项目强度约为 **6.5–7.5/10**。

### Level 2：强 CS/SWE 项目

**预计周期：6–9 周**

完成内容：

- 稀疏有限元求解器；
- 性能和内存 benchmark；
- 异步任务和状态管理；
- 数据库和结果版本化；
- 并发任务隔离；
- Docker、自动测试和 CI；
- 完整的 3D 前端和实验历史。

即使 ML 尚未取得有效结果，这一阶段对 CS/SWE 申请也可以达到约 **8.5–9/10**。

### Level 3：完整旗舰项目

**预计周期：10–14 周**

在 Level 2 基础上进一步完成：

- 可复现的数据生成流水线；
- ML density-field warm-start 模型；
- uniform、物理启发式和 nearest-neighbor baseline；
- OOD 测试；
- 消融实验；
- 多随机种子评估；
- 总运行时间、迭代数、compliance、体积分数和失败率统计；
- 部署、技术报告和演示。

达到这一等级后，预计申请匹配度为：

| 申请方向 | 匹配度 |
|---|---:|
| Computer Science | **约 9/10** |
| Software Engineering / SDE | **9–9.5/10** |
| Artificial Intelligence / Machine Learning | **8.5–9/10** |
| Information Systems | **8–8.5/10** |
| Scientific Computing / AI for Science | **约 9.5/10** |

## 主要时间风险

最大的时间不确定性是 ML 模型能否稳定优于传统初始化方法。

如果第一版模型没有优于 uniform initialization 或物理启发式 baseline，可能需要额外 **2–4 周**用于：

- 调整输入表示；
- 改变模型结构；
- 扩大或重新平衡训练数据；
- 检查数据泄漏；
- 调整训练目标；
- 分析不同物理 case 的失败模式。

ML 未取得正向结果不会破坏整个项目。只要数值内核和软件平台完成度足够高，它仍然可以作为很强的 CS/SWE 项目；但 AI/ML 申请匹配度会受到影响。

## 是否需要现实世界设备或材料

按照当前项目标准，**全部必要开发都可以直接在电脑上完成**。

不需要：

- 3D 打印机；
- 实体材料；
- 拉伸机或压力机；
- 传感器；
- 实验室环境；
- 真实结构破坏测试；
- 商业有限元软件许可证。

项目数据可以由有限元/SIMP 求解器自动生成，无需人工标注。数值正确性可以通过以下方式验证：

- 简单梁或小网格的解析结果；
- 有限差分 sensitivity check；
- 单元刚度的对称性与六个刚体模态、施加充分约束后系统刚度的正定性；
- 载荷与反力平衡；
- 体积分数约束；
- 网格收敛实验；
- 与原始稠密求解器交叉验证；
- 必要时与开源有限元工具交叉验证。

3D 打印和实体受力实验属于可选加分项，不是达到当前 CS/SWE/AI 项目标准的必要条件。只有在项目进一步扩展成机械工程研究，并需要声明模拟结果具有制造或实验意义时，才需要实体实验。

## 计算资源要求

普通个人电脑足以完成：

- 求解器开发和单元测试；
- 中小规模 3D SIMP；
- FastAPI、数据库和前端；
- 小规模数据生成；
- 基础 warm-start 模型实验。

以下情况可能受益于 GPU 或云计算资源：

- 大规模 3D CNN 或 3D U-Net；
- 数千至数万组 3D 优化样本；
- 大体素网格；
- 多随机种子和大规模超参数搜索。

建议第一版使用较小网格和轻量模型，先验证方法是否有效。Mac 的 CPU 或 MPS 可以完成原型；如果训练时间过长，再临时使用学校服务器、Google Colab 或按小时计费的云 GPU。

GPU 是提高效率的可选资源，不是完成项目的硬性条件。部署也可以先在本地或普通云主机完成。

## 建议锁定的第一版技术栈

为了控制范围，第一版只使用一套明确栈：

- **环境与质量**：Python 3.12、`uv`、Ruff、mypy、pytest、GitHub Actions；
- **Numerical Core**：NumPy、SciPy sparse；
- **API**：FastAPI、Pydantic；
- **持久化**：SQLAlchemy + SQLite 起步，数据量或部署需求出现后再考虑 PostgreSQL；
- **后台任务**：先用独立进程定义稳定的 job/state 接口；进入 Level 2 后采用 Redis + RQ，不在 MVP 阶段引入 Celery；
- **前端**：React + TypeScript；第一版用 Plotly 展示收敛曲线和体素结果，只有交互需求明确时再引入 vtk.js/Three.js；
- **ML**：PyTorch，先训练轻量 3D CNN，不从大型 3D U-Net 或超参数搜索开始；
- **制品**：小型 fixture 纳入 Git，大型运行结果和数据集放在 Git 之外，通过 manifest、校验和与生成脚本复现。

技术栈可以在阶段 Gate 复审，但不应在项目开始前同时准备多个可替代框架。

## 开始前的 0 号阶段（1–2 天）

1. 克隆仓库并建立首个短期工作分支（已完成仓库克隆；首个开发分支为 `feat/n1-hex8-mesh`）。
2. 添加 README、`PROVENANCE.md`、`LICENSE`、`.gitignore`、`pyproject.toml` 和最小 CI。
   同时把本目录中的三份规划文档迁移到新仓库的 `docs/planning/`，作为可追踪的设计记录。
3. 在 provenance 中固定上游 URL、commit SHA、无许可证状态和“不复制上游源文件”的边界。
4. 记录开发机器的 CPU、内存、操作系统和 Python 版本，供性能实验使用。
5. 保存上游默认 case 的参数与输出摘要，但不把无许可证源代码提交到 TopoLab。
6. 写下第一批可执行验收测试：Hex8 刚度对称、面载荷总和、固定自由度、稀疏/稠密小网格一致性。

完成以上内容后即可开始 Numerical Core；不需要等待 GPU、云服务器、3D 打印设备或额外数据。

## 前两周的具体目标

### 第 1 周

- 完成仓库 G0；
- 定义坐标、节点顺序、DOF 顺序、单位、载荷符号和 density 约定；
- 实现结构化 Hex8 mesh、材料矩阵、单元刚度和小网格稠密参考；
- 建立刚度对称、刚体模态、固定自由度和载荷守恒测试。

### 第 2 周

- 实现 SciPy COO/CSR 全局装配与约束求解；
- 实现 compliance 与解析 sensitivity；
- 完成中心有限差分检查和稠密/稀疏交叉验证；
- 只有这些测试通过后，才开始 filter、OC 和完整 SIMP 循环。

两周结束时的成功标准不是生成漂亮的 3D 图片，而是 Numerical Core 的关键量可以被独立测试和重复验证。

## ML 停止与降级规则

- 先完成 uniform、物理启发式和 nearest-neighbor 三个 baseline，再训练神经网络。
- 第一轮仅允许一个轻量模型族、有限超参数预算和至少三个随机种子。
- warm start 必须满足相同体积分数与最终 compliance 容差，并把推理时间计入端到端耗时。
- 如果 held-out/OOD case 上没有稳定收益，冻结结果并写失败分析；项目标题降级为不带 `with Learned Warm Starts` 的平台名称。
- 不为追求简历数字无限扩充数据、模型或云计算预算。

## 推荐实施策略

最稳妥的安排是：

1. 用 **6–9 周**优先完成强 CS/SWE 版本，确保数值内核、平台架构、测试和性能结果已经能够独立支撑项目价值。
2. 再使用 **3–5 周**完成 ML warm-start、baseline、OOD 和消融实验。
3. 如果 ML 未能产生稳定加速，如实报告结果和失败分析，保留传统 SIMP fallback，不影响核心平台交付。

这种顺序可以避免把整个项目的成败绑定在 ML 实验上，同时为 CS、SWE、AI、ML 和 Information Systems 申请保留不同的项目叙事角度。
