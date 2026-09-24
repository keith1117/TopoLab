# TopoLab Numerical Core 重写策略

English version: [Numerical Core Reimplementation Strategy](./TopoLab_reimplementation_strategy.en.md)

相关文档：[美研申请匹配度评估](./TopoLab_admissions_fit_assessment.md) · [开发周期与资源评估](./TopoLab_development_timeline_and_resources.md)

## 核心决策

TopoLab 不应完全建立在 Jiangce 的原始 `3D_SIMP_Topology_Optimization_Numpy` 代码上继续堆叠功能。

推荐采用：

> **原仓库作为参考基线与验证对象，TopoLab 的 Numerical Core 独立重新设计、实现和验证。**

当前固定的参考版本是：

- 仓库：`https://github.com/Jiangce2017/3D_SIMP_Topology_Optimization_Numpy`
- commit：`584cb8ee570d375f8ba9b10272020c5c2daa8c30`
- 许可证：截至 2026-09-17，GitHub 未显示任何开源许可证

因此不能把“公开可见”理解为“允许复制和再分发”。TopoLab 应提交独立实现、标准算法引用和行为对照结果，不提交上游源文件或其改写版本。

原仓库适合教学、理解算法流程和快速生成结果，但不适合作为一个长期维护、可扩展、可测试的软件平台核心。重新实现能够同时提高个人贡献可证明性、代码质量、扩展能力和美研申请价值。

## 为什么建议重写

当前 3D SIMP 仓库规模较小，主要由三个 Python 文件组成，但已经发现以下问题或限制：

- `direction=-1` 被当作自由度索引偏移，而不是载荷的负方向。
- 调用方和载荷函数内部可能重复均分总载荷。
- history 中记录的 compliance 和 density 可能来自不同迭代状态。
- 使用稠密全局刚度矩阵，扩大网格后运行时间和内存成本迅速增长。
- density filter 使用全元素两两距离矩阵，扩展性有限。
- 求解器、优化器、绘图和入口脚本缺少清晰接口。
- 缺少自动化数值验证和回归测试。
- 当前结构不适合直接接入异步任务、数据库、实验追踪和 ML 数据生成。

在现有结构上持续打补丁容易保留历史耦合，并增加后续平台开发成本。重写可以从一开始建立：

- 明确的数据模型；
- 稀疏有限元装配；
- 独立可测试的数值模块；
- 可序列化的输入输出；
- 可暂停、恢复和追踪的优化状态；
- 适合 API、worker 和 ML 调用的稳定接口。

## 原始仓库的角色

原仓库不应被忽略或删除，而应作为 reference implementation 使用。

需要记录：

- 原仓库 URL；
- 使用的 commit SHA；
- 默认网格、材料、载荷、边界条件和优化参数；
- 原始运行输出；
- 已发现的问题及其影响范围。

原仓库可以保存在 TopoLab 仓库之外用于本地对照。除非获得明确的公开修改和再分发授权，否则不应把完整原代码复制进新的公开仓库。

## 推荐实施步骤

### 1. 冻结原始基线

在修改任何逻辑之前保存：

- 原始配置；
- 原始 density、compliance 和 volume history；
- 原始输出图；
- 运行环境；
- 上游 commit SHA；
- 已知 bug 列表。

这组结果只作为历史基线，不应直接作为 TopoLab 的最终成果。

### 2. 建立小型基准案例

从原项目提取问题定义，而不是复制具体实现：

- 小型 cantilever；
- 固定端支撑；
- 单点载荷；
- 面分布载荷；
- 不同体积分数；
- 少量迭代的 density 和 compliance 结果。

保存少量、可验证的数值 fixture，用于新旧实现交叉对比。不需要迁移全部历史图片和输出。

### 3. 独立实现 Numerical Core

不要在第一天就建立十个只有少量代码的模块。第一阶段采用最小结构：

```text
src/topolab/
├── model.py       # problem/config/result 数据模型
├── mesh.py        # structured Hex8 mesh
├── fem.py         # element、assembly、BC/load、solve
├── simp.py        # filter、sensitivity、OC、optimization loop
└── io.py          # 可复现的配置与结果序列化
```

当单个文件职责已经稳定且明显过大时，再演化为目标结构：

```text
src/topolab/core/
├── mesh.py
├── elements.py
├── materials.py
├── boundary_conditions.py
├── loads.py
├── assembly.py
├── solver.py
├── sensitivities.py
├── filters.py
├── optimizer.py
└── result.py
```

这个拆分是目标架构，不是预先完成的工作清单。每次拆分都必须由测试边界或两个以上调用者证明其必要性。

在编码前先冻结以下数值约定，并写入 `docs/numerical_conventions.md`：

- 右手坐标系、节点编号和 Hex8 局部节点顺序；
- 每个节点的 DOF 顺序为 `(ux, uy, uz)`；
- `direction` 只允许 `x/y/z` 或 `0/1/2`，载荷正负由 signed magnitude 表示；
- SI 单位与所有输入量纲；
- density 范围、`E_min/E_0` 的定义和 penalization 公式；
- 使用 density filter 还是 sensitivity filter，以及 OC 中过滤发生的位置；
- compliance、reaction、history 和终止条件对应更新前还是更新后的 density。

推荐实现顺序：

1. 结构化 Hex8 网格；
2. 单元刚度矩阵；
3. 稀疏全局刚度矩阵装配；
4. 边界条件和载荷模型；
5. 位移求解和 compliance；
6. sensitivity；
7. density/sensitivity filter；
8. Optimality Criteria 更新；
9. SIMP 迭代与收敛逻辑；
10. 结果序列化和实验状态。

第一版只支持结构化长方体网格、各向同性线弹性、小变形、一个载荷工况和面/点载荷。多材料、非结构网格、动态载荷、多物理场和 GPU 求解不属于初版范围。

### 4. 进行交叉验证

在原代码已知问题不影响结果的 case 上，对比：

- 节点坐标；
- 单元连接关系；
- 总载荷；
- 节点位移；
- compliance；
- sensitivity；
- 单次 density update；
- 每轮体积分数；
- 小网格最终结构。

在此基础上增加独立验证：

- 有限差分 sensitivity check；
- 载荷与反力平衡；
- 刚度矩阵对称性；
- 边界条件完整性；
- 网格收敛实验；
- 稠密与稀疏求解器结果对比；
- 最终 density 的重新求解与 compliance 检查。

建议把验收阈值写成测试常量，并在验证报告中记录硬件、网格和数值尺度。初始目标为：

| 检查 | 初始验收标准 |
|---|---|
| 单元/全局刚度对称性 | `||K-Kᵀ|| / ||K|| ≤ 1e-10` |
| 稠密与稀疏小网格位移/compliance | `rtol ≤ 1e-9` |
| 载荷与支座反力平衡 | 相对残差 `≤ 1e-8` |
| 中心有限差分 sensitivity | 大多数非边界设计变量相对误差 `≤ 1e-4`，最大值 `≤ 1e-3` |
| OC 后体积分数 | 与目标绝对误差 `≤ 5e-3` |
| 最终状态一致性 | 返回的 density 重新求解后与记录的 final compliance 在 `rtol ≤ 1e-9` 内一致 |
| 确定性 | 相同输入、环境和版本得到相同 history（浮点容差内） |

若某一阈值因条件数或量纲不合理，需要在报告中解释并调整，不能静默放宽。

对于没有许可证且存在已知 bug 的上游实现，交叉验证只能作为辅助。新实现不能为了匹配上游错误而修改正确行为；分歧应通过独立物理/数值检查裁决。

### 5. 建立稳定的上层接口

Numerical Core 稳定后，为 API、worker、前端和 ML 提供统一入口，例如：

```python
problem = TopologyProblem(
    mesh=mesh,
    material=material,
    supports=supports,
    loads=loads,
    volume_fraction=0.2,
)

result = optimize(problem, config)
```

Web 层不应直接操作底层有限元数组。FastAPI、后台 worker、实验管理和 ML 数据生成均应通过统一的 problem/result 接口工作。

`optimize` 从第一版起应接受可选的 `initial_density`，并返回逐轮同状态的 metrics。进入平台阶段时，再通过窄接口增加进度 callback 和 cancellation token，而不把 Web/ML 依赖引入 Numerical Core。checkpoint/resume 可以在状态模型稳定后增加，不作为第一个核心版本的阻塞条件。

### 6. 在新核心上建设平台与 ML

只有在以下条件满足后，再开始大规模平台和 ML 开发：

- 小网格数值测试通过；
- sensitivity 验证通过；
- 稀疏与稠密结果一致；
- 载荷、体积分数和最终 compliance 记录正确；
- 优化过程可以稳定序列化和恢复。

随后再建设异步任务、数据库、3D 前端、数据集生成和 learned warm-start。

### 7. 冻结 ML 实验契约

在生成大规模数据之前先提交一份 `docs/ml_experiment_contract.md`，至少固定：

- 一个 case 的唯一 ID、网格、材料、支撑、载荷和体积分数 schema；
- 输入表示：按轴区分的支撑/载荷体素通道、坐标通道和广播后的体积分数；
- 输出表示：`[0,1]` density，并在进入 SIMP 前投影/归一到目标体积分数；
- 标签来自哪个 solver/data-generator 版本和终止条件；
- 以完整物理 case 分割 train/validation/test，禁止把同一优化轨迹的不同迭代拆到不同集合；
- uniform、物理启发式和 nearest-neighbor baseline 的固定定义；
- 质量约束：最终 compliance、体积分数和失败判据；
- 成本指标：数据生成、模型推理、SIMP refinement 和端到端总时间；
- OOD 轴：至少选择载荷位置、方向、支撑方式或体积分数中的一个，且在看测试结果前固定；
- 多随机种子、置信区间和模型失败时回退到 uniform initialization 的规则。

第一版模型只验证“预测初始 density 是否缩短达到同等质量解的时间”。不同时加入 compliance surrogate、生成式模型、强化学习或端到端替代求解器。

## 可以借鉴的内容

可以借鉴并明确引用：

- 问题设置；
- 标准 SIMP 算法流程；
- Hex8 有限元公式；
- Optimality Criteria 更新思想；
- 默认参数；
- 示例载荷和边界条件；
- 结果展示方式；
- 原仓库暴露出的实现难点。

### 优先使用的标准资料

- Kai Liu and Andrés Tovar, [*An efficient 3D topology optimization code written in Matlab*](https://doi.org/10.1007/s00158-014-1107-x), 2014：3D Hex8、minimum compliance、sensitivity、filter 与 OC 的主要理论和数值参考；
- Andrés Tovar 的 [Top3d documentation](https://www.top3d.app/)：用于核对标准 3D 问题设置与论文勘误；
- Ole Sigmund, [*A 99 line topology optimization code written in MATLAB*](https://doi.org/10.1007/s001580050176), 2001：经典 density-based SIMP、filter 与 OC 教学参考。

实现时优先依据论文公式和独立推导，而不是逐行翻译任何参考代码。每个公式、约定和偏离文献之处都在数值文档中注明。

## 不建议直接复制的内容

- 完整 Python 文件；
- 原始函数结构和模块划分；
- 大段注释；
- 原始变量命名体系；
- 绘图和运行入口脚本；
- 已知存在问题的载荷逻辑；
- 未经授权的原始代码片段。

如果某一段代码确实需要直接使用，应先取得 Jiangce 针对公开修改和重新分发的明确授权，并在对应文件中保留来源、作者和适用许可证。

## 来源与贡献记录

TopoLab 仓库应包含 `PROVENANCE.md`，记录：

- Jiangce 原始仓库的链接和 commit SHA；
- 相关 SIMP/FEA 论文与技术资料；
- 哪些行为通过原实现进行对照；
- 哪些模块由 TopoLab 独立实现；
- 是否使用任何获得授权的原始代码；
- 新旧实现的数值与性能差异。

不应把重写描述成发明了新的拓扑优化算法。更准确的项目描述是独立重新实现、验证并工程化标准算法。

TopoLab 自身应在首个 commit 中选择明确许可证。若未来获得上游作者许可并引入任何代码，必须重新核对许可证兼容性，并在具体文件和 `PROVENANCE.md` 中标注；仅有口头许可不应被当成通用开源许可证。

## “Scalable”的可验证定义

`Scalable` 不能仅由使用 SciPy sparse 推断。至少需要：

- 在不少于三个递增网格上报告元素数、DOF、装配时间、求解时间、峰值内存和总时间；
- 在小网格上与稠密实现验证数值一致；
- 展示稠密实现开始受内存限制时，稀疏实现仍可完成更大 case；
- 固定硬件、线程数、容差和 solver 配置，并提供生成 benchmark 的脚本；
- 分别报告 cold run 和重复 run，避免把缓存或一次性预计算隐藏在结果中。

在这些证据完成前，README 和简历使用 `sparse` 或 `performance-oriented`，不使用 `scalable`。

## 仓库首个可审查里程碑

首个 milestone 只包含：

1. README 中的问题定义、范围和非目标；
2. `PROVENANCE.md` 与上游固定 commit；
3. 环境锁定、代码质量配置和 CI smoke test；
4. 数值约定文档；
5. structured Hex8 mesh 与 element stiffness；
6. 刚度对称、节点/DOF 编号、面载荷总和和固定自由度测试。

不要在该 milestone 同时加入 FastAPI、React、Redis 或 PyTorch。这样第一批提交可以直接证明 Numerical Core 的设计与验证，而不是技术栈堆叠。

## 推荐简历表述

完成后可使用：

> Independently reimplemented and validated a 3D SIMP topology-optimization engine, using the original Hack3D NumPy implementation as a reference baseline; introduced sparse finite-element assembly, typed boundary/load models, finite-difference sensitivity checks, and regression benchmarks.

不建议使用：

- `Invented a new topology-optimization algorithm.`
- `Implemented entirely from scratch.`
- `Developed the original 3D SIMP method.`

`Independently reimplemented and validated` 能够准确表达个人贡献，同时承认算法和参考实现的来源。

## 时间与申请价值

相较于直接沿用原代码并增加 UI，重新实现 Numerical Core 预计增加约 **1–2 周**开发时间，但能够带来：

- 更清楚的个人代码 ownership；
- 更可靠的数值正确性；
- 更容易维护的系统结构；
- 更可信的性能 benchmark；
- 更稳定的 ML 数据生成基础；
- 更充分的 CS/SWE 技术面试内容；
- 更清晰的代码授权边界。

直接沿用原代码并增加网页，容易被理解为给导师代码增加 wrapper。独立重新实现、验证和稀疏化核心，则可以证明从数值算法、软件架构到 ML 系统的完整工程能力。

## 最终建议

TopoLab 不应成为 Jiangce 原仓库的 Web wrapper。

应使用原仓库作为历史基线、学习材料和交叉验证对象，独立实现经过验证、稀疏化和模块化的 3D SIMP Numerical Core，再在新核心上建设软件平台和 ML acceleration。

这条路线能够同时改善代码授权、个人贡献、工程质量和美研申请含金量。
