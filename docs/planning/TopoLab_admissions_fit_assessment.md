# TopoLab 美研申请匹配度评估

相关文档：[开发周期与资源评估](./TopoLab_development_timeline_and_resources.md) · [Numerical Core 重写策略](./TopoLab_reimplementation_strategy.md)

## 项目定位

**TopoLab — Reproducible 3D Topology Optimization Platform**

项目由三层组成：

1. **Numerical Core**：修复并验证 3D SIMP/有限元求解器，加入灵敏度、载荷守恒和体积分数测试，并将稠密矩阵改为稀疏装配。
2. **Software Platform**：使用 FastAPI、后台 worker、数据库和 3D 前端，实现异步运行、进度展示、取消、失败恢复、实验版本化和并发任务隔离。
3. **ML Acceleration**：生成不同支撑、载荷和体积分数的数据，训练 density-field warm-start 模型，并与 uniform initialization、物理启发式和 nearest-neighbor baseline 比较，同时测试未见过的载荷情况。

## 当前状态与表述边界（2026-09-17）

- 新仓库 [`keith1117/TopoLab`](https://github.com/keith1117/TopoLab) 已创建，但目前是公开空仓库：没有 commit、README、许可证或代码。
- 本文所有高分评价都是**完成条件下的项目方向匹配度**，不是当前项目完成度，也不是录取概率预测。
- 在 Numerical Core 通过验证之前，不使用 `validated`；在完成多网格性能测试之前，不使用 `scalable`；在 ML 与 baseline 的同等质量比较完成之前，不使用 `accelerated`。
- 如果 learned warm start 没有稳定改善总运行时间，最终标题改为 **TopoLab — Reproducible 3D Topology Optimization Platform**，ML 部分写成 evaluation/negative result，不继续保留暗示已加速的标题。

## v1.0.0 最终结果（2026-09-24）

- 数值内核、SIMP 优化、平台契约与 M0 数据基础 gate 已通过，并有仓库内验证报告。
- 四档稀疏 benchmark 已完成，但证据不足以支持对整个平台使用宽泛的 `scalable` 表述。
- M1 的固定五 seed 对照在 ID-test 上结论不确定，在 OOD 上慢于 uniform 且有 25% learned failure/fallback；M2 又因 756 个 case 中 10 个未收敛而未通过预注册 data gate，因此没有开始 M2 拟合。
- 最终标题按原停止规则降级为 **TopoLab — Reproducible 3D Topology Optimization Platform**。ML 成果定位为可复现实验、负结果和严格停止规则，不声称 learned acceleration。
- v1.0.0 是可在本地运行和复现的研究软件发布，不包含分布式 worker、认证、容器化或托管在线 demo。

这个项目对应的科研与工程领域是：计算力学、结构拓扑优化、有限元、数值优化、科学计算、Scientific ML / AI for Engineering，以及长时间计算任务的软件平台工程。对 CS/SWE/AI/ML/Information Systems 的价值来自可验证的算法、系统和实验贡献，而不是机械工程主题本身。

## 完整实现后的申请匹配度

以下评分假设三层均已真正完成，并具有数值验证、系统测试、性能指标、ML 对照实验和 OOD 测试。

评分用于比较叙事覆盖范围，不应放入简历、SOP 或项目 README。

| 申请方向 | 匹配度 | 主要支撑 |
|---|---:|---|
| Computer Science | **9/10** | 数值算法、稀疏矩阵、性能工程、机器学习和后端系统形成完整技术链路 |
| Software Engineering / SDE | **9–9.5/10** | API、异步任务、并发隔离、失败恢复、自动测试、CI/CD、容器化和可观测性 |
| Machine Learning | **8.5–9/10** | 数据生成、warm-start 模型、基线比较、消融实验、OOD 泛化和物理约束 |
| Artificial Intelligence | **8–8.5/10** | AI for Science、学习辅助优化以及 ML 与传统物理求解器结合 |
| Information Systems | **8–8.5/10** | 计算工作流、实验数据管理、版本追踪、输入验证和结果管理 |
| Scientific Computing | **9.5–10/10** | 有限元、数值优化、稀疏求解、性能分析和科学计算平台高度匹配 |
| Computational Engineering / AI for Science | **9.5–10/10** | 物理求解器与 ML 加速紧密结合，方向高度对应 |
| Data Science | **7.5–8/10** | 包含数据生成、实验分析和模型评估，但不是典型商业数据分析项目 |

## 高评分成立条件

### 最低证据包

完整旗舰项目至少应在公开仓库中提供：

- 可复现的环境锁定文件、安装命令和一条端到端运行命令；
- `PROVENANCE.md`，记录上游 commit、无许可证状态、参考资料和独立实现边界；
- 数值验证报告，包括容差、失败案例和原始结果；
- 三档网格的稀疏/稠密时间与峰值内存 benchmark；
- API/worker 的状态机和并发隔离测试；
- 固定数据划分、baseline、OOD、消融和多随机种子的 ML 结果；
- 能从干净环境复现关键表格/图形的脚本，而不仅是静态截图；
- 架构图、限制说明、演示视频和明确的个人贡献说明。

招生材料中的每个数字都应能回溯到仓库内的配置、日志或生成脚本。

### Numerical Core

- 修复载荷方向、总载荷和最终 compliance 记录问题。
- 使用有限差分验证 sensitivity。
- 验证体积分数、载荷守恒和最终状态 compliance。
- 对比稠密与稀疏实现的运行时间、内存占用和可支持网格规模。
- 对最终 density 重新执行有限元求解，避免结果与历史记录错位。

仅仅让现有代码成功运行不足以形成高含金量的 Numerical Core。

### Software Platform

- 使用后台 worker 执行长时间优化任务。
- 提供 run ID、进度、取消、失败和恢复状态。
- 使用明确的输入 schema，并验证非法边界条件和刚体运动情况。
- 确保并发任务之间的参数、状态和输出相互隔离。
- 使用数据库或结构化方式保存实验参数、代码版本、日志和结果。
- 加入 Docker、自动测试、CI 和部署说明。
- 最好提供在线演示或完整录制 demo。

只有一个可以启动 Python 脚本的 FastAPI 页面，不能体现完整的软件工程能力。

### ML Acceleration

- 建立清晰的训练、验证和测试划分。
- 按完整物理 case 划分数据，避免同一优化轨迹在训练集和测试集之间泄漏。
- 与 uniform initialization、物理启发式和 nearest-neighbor baseline 比较。
- 测试未见过的载荷位置、方向、支撑方式或体积分数。
- 报告最终 compliance、体积分数、迭代数、总运行时间和失败率。
- 把模型推理开销计入总加速结果。
- 当模型预测失败时，能够回退到标准 SIMP 初始化。

只有在相同物理质量约束下减少总运行时间，才能合理声称 ML 实现了加速。

## ML 没有取得有效提升时

如果数值内核和软件平台完成度较高，但 ML 未能稳定优于 baseline，项目仍然具有较强价值：

| 申请方向 | 匹配度 |
|---|---:|
| Computer Science | **8.5/10** |
| Software Engineering / SDE | **9–9.5/10** |
| Artificial Intelligence / Machine Learning | **6.5–7/10** |
| Information Systems | **8/10** |
| Scientific Computing | **9/10** |

ML 实验失败不会破坏整个项目。只要如实分析失败原因，可靠的 3D 求解器和完整的软件平台依然能够构成强 CS/SWE 项目；但申请 AI/ML 时，需要严谨且有效的模型结果才能达到更高匹配度。

建议预先设定停止规则：完成一个轻量 3D CNN、一个合理超参数预算和至少三个随机种子后，如果它在 held-out case 上不能在同等 compliance/volume 容差内减少端到端运行时间，就冻结该结果并转入失败分析，不进行无边界的模型搜索。

## 只有表面技术整合时

如果项目只是用 FastAPI 启动原始脚本，再附加一个缺少基线和评估的神经网络，预计匹配度会下降为：

| 申请方向 | 匹配度 |
|---|---:|
| Computer Science | **约 7/10** |
| Software Engineering / SDE | **6.5–7/10** |
| Artificial Intelligence / Machine Learning | **5–6/10** |
| Information Systems | **约 6.5/10** |

项目含金量主要来自正确性验证、对照实验、量化性能结果和系统完整性，而不是技术栈数量。

## 不同申请方向的简历侧重点

### CS / SWE / SDE

推荐顺序：

1. 稀疏求解器、数值验证与性能提升。
2. 异步任务、并发隔离、失败恢复和实验版本化。
3. ML warm-start 的实际加速结果。

### AI / ML

推荐顺序：

1. 数据集构建、warm-start 模型和物理 case 划分。
2. baseline、OOD 测试、消融实验与失败分析。
3. 模型如何与标准 SIMP 求解器结合并保持可靠 fallback。

### Information Systems

推荐顺序：

1. 计算任务工作流和用户输入验证。
2. 实验数据、代码版本和结果的可追溯性。
3. 异步运行、状态管理、结果展示和失败恢复。

## 最终项目组合

当 TopoLab 达到完整实现标准时，它可以与 Airline AgentOps 并列成为旗舰项目：

- **Airline AgentOps**：证明通用后端、Agent/RAG、可靠性和系统设计能力。
- **TopoLab**：证明数值计算、科学软件、性能工程、ML 实验和跨学科问题解决能力。
- **Hack3D MNN VIP**：作为研究经历，展示 PyTorch/VAE 科研代码适配、目标场扩展和机械设计背景。

这一组合能够较完整地覆盖 CS、SWE/SDE、AI、ML 和 Information Systems 申请方向，同时保留 Scientific Computing 与 AI for Science 的独特辨识度。

## 面向申请的阶段性可用状态

| 状态 | 可以合理使用的定位 | 暂时不能声称 |
|---|---|---|
| Numerical Core 尚未验证 | Work in progress / independent reimplementation | validated、scalable、production-ready |
| Core 验证完成 | Validated 3D SIMP engine | ML-accelerated、full-stack platform |
| 平台与性能评估完成 | Reproducible topology-optimization platform | learned acceleration（除非实验完成） |
| ML 评估完成且结果为正 | Platform with learned warm starts | 超出实际测试分布的泛化能力 |
| ML 结果为负或不稳定 | Platform + rigorous warm-start evaluation | accelerated optimization |

这套表述边界应同步用于简历、GitHub README、SOP 和面试回答，避免项目标题先于证据。
