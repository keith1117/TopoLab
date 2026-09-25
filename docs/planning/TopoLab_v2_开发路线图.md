# TopoLab v2 开发路线图

英文工作版：[v2 Development Roadmap](./TopoLab_v2_development_roadmap.md)

状态：**v2 旗舰项目交付路线图；Gate A1 已通过；ML 加速是必需的交付 Gate，
并非可选增强。** 已发布的 `v1.0.0` 及 M1/M2 的负面结论仍是历史证据。

制定日期：2026-09-24
修订日期：2026-09-25

相关文档：

- [美研申请匹配度评估](./TopoLab_美研申请匹配度评估.md)
- [开发周期与资源评估](./TopoLab_开发周期与资源评估.md)
- [v1.0.0 发布验证](../validation/v1_release_validation.md)
- [M1 held-out 评估](../validation/m1_held_out_evaluation.md)
- [M2 materialization 结果](../validation/m2_catalog_materialization.md)
- [M3 v1 预注册](../m3_preregistration.md)
- [开发用 warm-start 可行性诊断](../validation/ml_feasibility_probe.md)
- [A1.1 canonical demo 验证](../validation/a1_1_canonical_demo.md)
- [A1.4 clean Linux 验证与 Gate A1 结论](../validation/a1_4_clean_linux_smoke.md)

## 1. 当前基线

`v1.0.0` 已经完成以下可信基础：

- N1、N2、P1 和 M0 gate 通过；
- 独立实现并验证 structured Hex8 FEM 与 3D SIMP；
- 稀疏装配/求解及四档单机 benchmark；
- FastAPI、进程内异步 run、取消、SQLite 持久化和重启恢复；
- React 问题配置、运行历史、收敛曲线和 3D physical-density 可视化；
- 可追溯的数据生成、训练、评估、checkpoint 和恢复流程；
- M1 负面/不确定结论与 M2 data-gate 失败均被完整保留；
- 锁定环境、CI、262 项 Python 测试、22 项前端测试和可安装 wheel。

当前短板分为两类：

1. **非 ML 短板**：缺少一键演示、容器化、托管 demo、进程隔离、真正的优化
   checkpoint/resume、多机器性能证据和真实用户反馈。
2. **ML 短板**：M1 未建立稳定加速，M2 因 10 个 label 不收敛而未进入拟合；当前
   模型的数据覆盖、跨方向泛化、solution-quality 可靠性和收益上限仍不足。

后续开发不修改或覆盖 `v1.0.0`、M1、M2 的历史结论。任何新实验、数值约定或
平台契约都必须使用新的版本标识和独立验证报告。

## 2. 旗舰项目交付条件与优先级

**只有在预先定义的实际工作负载上，learned 方法实现可复现、同等质量的端到端
加速，v2 旗舰项目才算完成交付。** 已完成的平台与诚实记录的 ML 负结果依然有
工程价值，但不能代替这一交付条件。ML Gate 未通过时，不把整个项目描述为
“已完成交付”。已发布的 `v1.0.0` 不撤销，也不追溯改名。

最低 ML 交付 Gate 要求：

- 使用全新、物理 case 不重叠的 final cohort；与优化后的 uniform 基线以及固定的
  非 ML 基线在相同版本下比较；
- 成对端到端耗时包含推理、体积投影、决策、SIMP refinement、拒绝与回退的
  全部成本，保持冻结的 compliance、收敛和体积分数质量检查；
- accepted learned attempt 的质量失败数为零；在**至少两个预先定义的 3D 网格
  规模**上，主要平均时间比的 95% 置信区间上界均须 `< 1.0`；
- 预先定义的 OOD cohort 同样不能有 accepted 质量失败，且平均时间比的 95%
  置信区间上界须 `<= 1.05`；允许安全拒绝，但计入其全部成本。

新的实验契约必须在 final evaluation 之前冻结有实际意义的重复查询工作负载、
网格/体积分数/载荷分层、硬件、随机种子、值得宣称的最小效果、独立复现及 OOD
定义。数据生成、训练和 checkpoint 加载费用单独报告，并分析摊销。评估后发现的
有利子群不能替代预先声明的主 cohort。`accelerated` 只能用于实际通过 Gate 的
特定工作负载和环境；更宽泛的稳定性说法需要额外证据。

轨道 A 继续改进平台。轨道 B 是**以实现 ML 加速为目标的工程计划**：每一版
实验都有有限预算和明确 Gate。Gate 失败后诊断原因，并为下一干预建立新的独立
预注册；失败不能算作项目交付，也不能在已暴露 final 集上无边界搜索。后续时间与
算力估计暂定；增加训练轮数无法保证产生正结果。

| 优先级 | 阶段 | 原因 |
|---|---|---|
| P0 | B0 warm-start 可行性测量 | 用开发用 case 确认求解器实际加速空间 |
| P0 | B1 收敛与 learned 失败诊断 | 扩大训练前修复数值失败并定位质量瓶颈 |
| P0 | A3 影响基线的求解器性能优化 | 先冻结公平的优化后 uniform 比较分母 |
| P0 | B2 工作负载与规模试点 | 选择端到端收益有空间的真实重复查询任务 |
| P0 | B3 新版本实验契约 | 拟合前冻结数据、模型/损失、算力、可靠性和最终证据 |
| P1 | A2 进程隔离与恢复 | 保证较长运行的平台安全性 |
| P1 | B4 数据、拟合与验证 | 在不查看 final 数据的条件下改进并筛选 learned 方法 |
| P1 | B5 一次性 final 评估与复现 | 用新证据判定 ML 交付 Gate |
| P2 | A4 部署与反馈 | 等隔离和资源限制完成后推进 |

每个切片仍须独立可审查。数值语义修改、平台工作、数据 materialization 与模型
训练使用不同 PR。每个 Gate 报告实际时间、内存和数据生成成本；旧时间估计不是
正结果的承诺。

## 3. 轨道 A：非 ML 优化

### A1：可复现演示与作品呈现

目标：让没有项目背景的评审者在干净环境中完成一个小型端到端优化，并能快速理解
架构、结果和限制。

建议切片：

1. **A1.1 canonical demo case**
   - 增加一个小型、版本化、可快速完成的公开示例问题；
   - 提供单条命令启动 API 和运行示例，或提供等价的窄 CLI；
   - 输出 run ID、终态、compliance、volume 和结果位置；
   - 测试示例输入与公开 `TopologyProblem` 契约完全一致。
2. **A1.2 local stack packaging**
   - 为 API 与前端建立最小 Docker/Compose 本地运行路径；
   - 使用非 root 进程、固定依赖和持久化 volume；
   - 不把数据库、结果或模型 artifact 构建进镜像。
3. **A1.3 architecture and demo evidence**
   - 增加一张原创架构图和一段 2–4 分钟演示视频；
   - 展示问题提交、进度、取消、恢复、收敛曲线和 3D 结果；
   - README 只保留可回溯到验证报告的数字。
4. **A1.4 clean-machine smoke**
   - 在干净 Linux 环境执行安装、启动、提交、完成、重启读取和前端构建；
   - 把命令、耗时、环境和限制写入验证报告。

Gate A1：

- 一条有文档的路径可在干净 Linux 环境启动完整本地栈；
- canonical case 能在规定时间内达到有效终态；
- smoke test 验证 API、SQLite 和前端契约；
- 所有生成结果仍在 Git 之外；
- 演示不暗示 hosted、production-ready、scalable 或 accelerated。

建议里程碑：`v1.1.0`。

### A2：进程隔离、持久任务与数值恢复

目标：把当前线程池和“中断即失败”语义升级为可验证的进程边界，并区分任务恢复与
优化器 checkpoint/resume。

建议切片：

1. **A2.1 worker protocol**
   - 冻结 API/manager 与 worker 之间的最小序列化消息协议；
   - 先实现本机独立进程，不立即引入 Redis、RQ 或 Celery；
   - 保持 Numerical Core 不依赖 Web 或队列框架。
2. **A2.2 durable ownership and recovery**
   - 为 queued/running run 增加 lease、heartbeat 或等价的明确所有权语义；
   - 验证 API 进程和 worker 进程分别崩溃时不会产生重复成功或永久 running；
   - 引入正式数据库迁移机制，而不是继续累积内联迁移。
3. **A2.3 optimizer checkpoint contract**
   - 独立版本化设计 density、迭代号、history、problem identity 和 solver contract；
   - 原子写入，拒绝不同代码/问题/环境的 checkpoint；
   - 验证 resumed run 与 uninterrupted run 在冻结容差内一致。
4. **A2.4 cancellation and resource bounds**
   - 验证 queued、running、solve 中和 resume 后的取消语义；
   - 增加并发数、网格规模、运行时间和 artifact 大小限制；
   - 记录结构化日志，但不记录完整密度数组或敏感输入。

Gate A2：

- worker 崩溃、API 重启、重复领取和取消均有确定性测试；
- 两个并发 run 的内存、结果、错误和 checkpoint 相互隔离；
- resume 结果通过最终 compliance、volume 和 density 一致性检查；
- 默认配置不会启动无限并发或接受无边界问题规模。

建议中间里程碑：`v1.2.0`。将 `v2.0.0` 项目里程碑保留给完整旗舰交付 Gate；
公开 API 兼容性另行记录。

### A3：性能工程与证据扩展

目标：先用 profiling 定位主要成本，再做一个有限优化，并扩大 benchmark 的环境与
规模证据。

建议切片：

1. 记录装配、factorization/solve、filter、OC 和序列化的分阶段 profile；
2. 根据 profile 只选择一个主要瓶颈，例如重复稀疏结构构建或线性求解；
3. 为候选优化增加数值等价测试和回退路径；
4. 在 Apple arm64 与 Linux x86-64 上重复固定 mesh ladder；
5. 报告 cold/repeated time、峰值 RSS、DOF、非零元数量和失败边界。

Gate A3：

- 优化前后使用同一问题、环境、线程数和测量协议；
- 小网格数值结果保持冻结容差；
- 主要目标指标有稳定改善，且其他规模没有明显回退；
- 只在证据覆盖范围内使用 `faster` 或 `lower-memory`；跨平台和更大规模证据不足时
  仍不使用宽泛的 `scalable`。

任何影响 uniform 求解器计时或数值行为的 A3 修改，都必须先于 B2 工作负载试点
和 B3 ML 契约冻结。之后的测量不得暗中改变最终比较的分母。

建议里程碑：`v1.3.0`。

### A4：受控部署与外部验证

目标：在 A2 的隔离和资源限制之后提供安全、低成本的公开演示或完整录制替代品。

建议切片：

1. 先完成部署威胁模型：CPU/内存耗尽、超大输入、数据库增长和滥用；
2. 只开放预设 mesh 范围和固定并发额度；
3. 加入健康检查、结构化日志、错误率和任务耗时指标；
4. 若部署成本或安全边界不合适，保留本地 Compose 与录制 demo，不强行上线；
5. 收集少量真实试用反馈，区分软件缺陷与功能愿望。

Gate A4：

- 部署不能绕过 Numerical Core 的输入验证和资源限制；
- 不公开内部路径、设备标识、数据库或外部实验 artifact；
- 有明确的关闭、清理和成本上限；
- README 准确区分 local demo、hosted demo 和 production service。

## 4. 轨道 B：必需的 learned acceleration

### 历史证据边界与 M3 v1 处置

M1 的 6 个 ID-test 和 80 个 OOD case 已暴露；M2 的完整 756-case outcome index
属于开发信息。M1/M2 的 artifact、负面结论和原 Gate 保持不变。有界的
`topolab.m3.experiment.v1` 契约虽然通过了**规划 Gate**，但在 M3.1、拟合及
final evaluation 之前已经**被新方案取代**。它的 425-label MSE control 与单个
11,281 参数的 dilated CNN 是合理的小实验，却没有解决 M2 收敛问题，也未证明
预测质量能接近实际 warm-start 加速空间。M3 v1 的 final label 或 learned 结果
均未打开。由于契约公布了其 final case 定义，这些 case 视为**设计已暴露**，
不能进入下一轮 final cohort。不得静默修改历史预注册，或把其规划 Gate 当作
加速 Gate。下一实验必须有新的 contract/catalog identity、完整的开发已暴露
physical case ledger；新的 final label 和结果在冻结前保持封存。

### B0：实际 warm-start 可行性——开发用诊断已完成

[只读诊断](../validation/ml_feasibility_probe.md)只使用了 36 个 M2 validation label
作为不可能在真实推理中获得的、已知正确答案的初始化，以及 7 个失败的 M2 training
case 定义。36 个 oracle 初始化均在一次 SIMP 迭代后通过冻结的质量检查；两次本地
测量的成对平均“投影初始化/uniform”时间比约 `0.072`。这证明：**如果已有几乎
精确的答案，当前求解器有条件性的 warm-start 空间**；它没有证明可部署的 learned
加速。7 个失败的 training case 在 120 次迭代内仍未达到容差。它们最后十次的
设计密度变化和 compliance 均下降，提示终段进展缓慢，但尚不能断言普遍的求解器
修复办法。

### B1：修复数值与 learned 失败瓶颈

1. 复现 7 个仅用于开发的 `y, 0.45` 轨迹，并分析 10 个已暴露的 M2 终态失败；
   不读取 M2 test/OOD label 数值。
2. 用设计密度与 compliance 轨迹及独立体积分数检查，区分有限预算下的缓慢收敛、
   周期行为和优化器不稳定。
3. 若证据支持修改求解器，先定义数值验收测试，版本化求解器和 label，再用同一
   revision 重新运行**每一个被比较的方法**。不得静默增加迭代预算或放宽容差。
4. 在仅用于开发的 case 上重放 M1 预测，对比原始场与投影场、初始 compliance、
   最终质量和 refinement 轨迹，并以已知 label oracle 为参照。判定数据覆盖、
   表示方式、density MSE 或 warm-start 吸引域行为中，哪个主导了差距。

**Gate B1：**记录可复现的失败机制，以及经过测试的修正或明确的“不修改求解器”
决定。下一次模型干预必须针对测得的瓶颈；单纯将 epoch 翻倍不算修正。

### B2：选择确有可测收益空间的工作负载

完成会影响基线的 A3 修改之后，在一组小型、固定、仅用于开发的 mesh ladder 和
代表性重复查询载荷/支撑/体积分数族上做试点。保持数值设置一致，比较优化后的
uniform、冻结的非 ML 基线、已知 label 的 oracle 初始化与当前 learned 初始化。
记录逐迭代 FEM、推理、投影、内存及 fallback 成本。纳入困难的体积分数层，不得
只选有利的低体积分数 case。在任何新 final label 或结果存在之前，选定有实际
意义的工作负载和网格范围。

**Gate B2：**质量可行的 oracle 和至少一个可达到的开发原型，都有足够的实测
收益，才值得进入训练和最终评估。如果精确 label 初始化在目标工作负载上都不能
胜过优化后的 uniform 基线，应转向另行版本化的 learned optimizer-step 或数值
成本干预；继续训练 final-density MSE 模型没有依据。

### B3：新版本契约、暴露记录与数据 Gate

冻结新的实验 identity，而不是修改 M3 v1。规定主工作负载、train/validation/
final-ID/OOD 的全部 physical-case 分层、内容派生 catalog、求解器 revision、
label 成功规则和完整的 exposure ledger。新 final case 在物理定义上必须不重叠，
其 label/结果不能进入模型开发。新数据生成必须先有 clean-revision 的只读计划、
仓库外 artifact root、固定计算预算，并在拟合前审计 checksum。保留每个失败
case 及其分母。求解器修复或新工作负载需要新 label；旧 M2 成功 label 只有在
明确的 provenance 与兼容规则下才能重用。

有界模型方案必须直接回应 B1/B2 证据。候选干预可以是物理条件化输入、中间
状态目标或与质量对齐的损失，而不默认选择更大的 CNN。
[理论引导学习](https://arxiv.org/abs/1807.10787)、
[3D 算法感知中间状态学习](https://arxiv.org/abs/2012.05359)以及
[应变能条件化](https://arxiv.org/abs/2305.10460)仅作为可检验选项的启发；
论文中的结果不是 TopoLab 的证据。训练前冻结小规模 control/candidate/ablation
组合、seed、epoch、选择指标、硬件/内存预算、停止规则和有限的可靠性策略。
若查询时计算物理特征需要 FEM 求解，该成本必须计入。

**Gate B3：**provenance、不重叠性、label 质量、各层数据可用性和算力预算都
通过审计；否则不拟合。

### B4：只使用开发数据拟合、筛选与冻结

在包含 fallback 的 validation 时间、独立 compliance、收敛、体积分数和失败
分层上，将每个模型与 uniform 及非 ML 基线比较。只校准预先定义的可靠性阈值。
被拒绝的候选计入推理/决策加完整 uniform 时间；被接受但失败的尝试仍须计入
完整 fallback。只改善图像 MSE、却未改善实际质量与时间的候选不能晋级。
保留所有 case 和 seed。在 final evaluation 前冻结代码、checkpoint、阈值、
统计方法、环境与源码 revision。

**Gate B4：**在全部成本与质量检查之下，validation 对优化后的 uniform 和
固定非 ML 方案仍有有意义的收益。否则诊断、为新假设另建版本，并保持 final
证据封存。

### B5：一次性 final 比较与项目交付 Gate

B4 通过后，只打开一次新的 ID cohort，再按冻结顺序评估预定义 OOD 和独立
复现。报告分阶段成本、以 physical case 配对的 bootstrap 区间、质量、体积分数、
迭代次数、失败/拒绝/fallback case、内存、训练/生成成本和摊销。工作负载专属
claim Gate 必须已在 B3 固定，并满足第 2 节的最低条件。若任一必需分层或独立
复现失败，发布负结果，不修改 cohort、阈值、求解器或模型。项目仍**处于研发中**，
不宣布完整交付。依据诊断原因规划下一次有界且另行版本化的实验，并保留新的
final 证据。不得对 B5 结果展开未预注册搜索。

## 5. 版本、分支与验证规则

- 每一切片从最新 `main` 创建短期分支，通过 PR 和 CI 合并；
- 新平台契约、新 checkpoint 和新 ML artifact 都使用新的显式版本；
- 每个数值行为改动先写失败测试或独立验收，再修改实现；
- 所有生产执行先提交 contract/runner，再从 clean merged revision 做 read-only plan；
- dataset、checkpoint、数据库、日志、截图和运行结果不得提交；
- 每个阶段以独立 validation report 结束，报告失败同样视为有效阶段结论；
- 只有实际通过相应 gate 后才更新 README、简历和项目标题中的 claim。

## 6. 推荐执行顺序

用户指定的 ML 交付条件改变执行顺序，但不扩大 PR 粒度或改变 Gate：

1. **A1.1–A1.4 与 Gate A1**：已分别完成。
2. **M3 v1 规划 Gate**：曾通过，但该方案无法满足完整交付目标，已在拟合和
   final 证据开启之前被取代。
3. **B0 仅用于开发的可行性诊断与路线图修订**：已完成。
4. **B1 数值收敛与 learned 质量问题溯因**：下一切片；不进行新训练或 final
   证据评估。
5. **影响基线的 A3 求解器性能工程**：在选择 ML 工作负载之前冻结数值修改和
   公平的优化后 uniform 基线。
6. **B2 工作负载/网格加速空间试点**：一个有界、仅用于开发的切片。
7. **B3 新版本 ML 契约和数据 Gate**：先冻结新的 final 边界，再分成独立可审查
   的切片实现和审计数据。
8. **A2.1–A2.2 进程隔离**：在昂贵的最终 ML 评估之前，以独立 PR 完成。
9. **B4 拟合、可靠性策略与冻结**仅在 B3 通过后执行；**B5 final 评估**仅在
   B4 通过后执行。
10. **A2.3–A2.4 与 A4**按平台要求及资源情况推进。

每完成一个独立切片，就报告其 Gate、证据、限制与下一切片，然后等待用户再次
指示开始。

## 7. 阶段完成证据

后续工作以证据而非功能数量衡量：

| 目标 | 完成证据 |
|---|---|
| 更容易复现 | 干净环境的一条运行路径、固定 demo、smoke 与运行报告 |
| 更可靠的平台 | 崩溃/重启/取消/并发/重复领取测试与明确的状态机 |
| 更强的性能 | 分阶段 profile、跨环境 benchmark 和数值等价性 |
| 必需的 ML 加速 | 正确数值基线、实测加速空间、新暴露边界、有界干预和通过的全新端到端 claim Gate |
| 更好的申请展示 | 简历数据可追溯；演示与 README 不超过证据边界 |

平台与数值里程碑仍有独立价值，也应如实报告，但不能代替完整 v2 旗舰项目
交付所必需的 ML 正结果。失败的 ML 实验是后续有界干预的证据，而非项目完成
声明的依据。
