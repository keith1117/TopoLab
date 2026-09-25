# TopoLab v1.x 后续开发路线图

English version: [v1.x Development Roadmap](./TopoLab_post_v1_development_roadmap.en.md)

状态：**v1.x 路线图，起点为已发布的 `v1.0.0`；Gate A1 于 2026-09-25 通过**

制定日期：2026-09-24

相关文档：

- [美研申请匹配度评估](./TopoLab_admissions_fit_assessment.md)
- [开发周期与资源评估](./TopoLab_development_timeline_and_resources.md)
- [v1.0.0 发布验证](../validation/v1_release_validation.md)
- [M1 held-out 评估](../validation/m1_held_out_evaluation.md)
- [M2 materialization 结果](../validation/m2_catalog_materialization.md)
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

## 2. 总体目标与优先级

后续工作分成两条相互独立的轨道：

- **轨道 A：产品化与科学软件工程**——提高可复现性、可演示性、运行隔离、恢复能力
  和性能证据，增强 CS/SWE/Scientific Computing 申请价值。
- **轨道 B：M3 learned warm-start**——在有限、预注册预算内解决数据可用性和
  泛化问题，争取建立新的正面 ML 结果；失败时仍保留可审计结论。

推荐优先级：

| 优先级 | 阶段 | 原因 |
|---|---|---|
| P0 | A1 可复现演示 | 成本低、申请展示收益最高，不依赖新的实验结果 |
| P0 | M3.0 诊断与预注册 | 在再次消耗训练资源前先冻结边界和预算 |
| P1 | A2 进程隔离与恢复 | 补足最明显的平台工程缺口 |
| P1 | M3.1 数据 gate | 决定 M3 是否有资格进入训练 |
| P1 | A3 性能与跨环境证据 | 扩大证据范围，但仍避免宽泛的 scalability 声明 |
| P2 | M3.2–M3.4 训练与最终评估 | 仅在数据 gate 通过后执行 |
| P2 | A4 受控部署与外部反馈 | 在运行隔离和资源限制完成后再开放 |

粗略工作量用于排期，不是完成承诺；生产数据生成和评估等待时间另计：

| 阶段 | 预计有效开发时间 |
|---|---:|
| A1 可复现演示 | 4–7 天 |
| A2 进程隔离与恢复 | 8–15 天 |
| A3 性能工程 | 4–8 天 |
| A4 受控部署 | 3–7 天 |
| M3.0 诊断与预注册 | 2–4 天 |
| M3.1 数据 gate | 3–6 天，加 materialization 时间 |
| M3.2–M3.3 训练与冻结 | 7–14 天，加训练时间 |
| M3.4 final evaluation | 2–4 天，加评估时间 |

两个轨道可以交错推进，但一次 PR 只处理一个可验证行为。不得把平台改造、数值
语义变化、数据生成和模型训练混入同一切片。

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

建议里程碑：`v1.2.0`。若公开 API 出现不兼容变化，再考虑 `v2.0.0`，不要为了
“看起来重要”提前升级主版本。

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

## 4. 轨道 B：M3 learned warm-start

### M3 的证据边界

M3 是新实验，不是对 M2 的补跑或“修复”。必须遵守：

- M1 的 6 个 ID-test 和 80 个 OOD case 已暴露，只能用于诊断；
- M2 的 materialization 结果、失败分布和所有已检查统计均属于开发信息；
- M2 成功 labels 可以在新契约明确记录 provenance 后作为开发 train/validation
  候选，但不能把 M2 重新宣布为通过；
- M3 必须建立物理 case 不重叠的新 final ID-test 和 OOD 集；
- final labels 不参与训练、模型选择、可靠性阈值或停止决策；
- M1/M2 artifact 和报告保持不可变。

### M3.0：失败诊断与预注册

目标：在写新模型代码或启动训练前，回答失败来自数据、表示、目标、优化预算还是
warm-start 方法本身。

允许的诊断：

- 对 M1/M2 已暴露数据按方向、体积分数、载荷位置和收敛状态分层；
- 比较预测 density 的体积投影前后变化、初始 compliance、最终 quality failure 和
  refinement iteration；
- 分析 10 个 M2 非收敛 case 的共同结构，但不把它们静默改成成功 label；
- 估算理想 warm start 的可获得加速上限，判断继续训练是否值得；
- 用 train/validation-only pilot 验证数据读取和损失计算，不打开新 final evidence。

预注册文档必须冻结：

- M3 的单一主问题和成功指标；
- case schema、catalog、split、exposure ledger 和 artifact version；
- label 成功/失败政策与最大 solver budget；
- 最多两个模型候选、一个主损失和一个预先定义的 ablation；
- 固定 seed、epoch、early stopping、选择规则和硬件预算；
- reliability/fallback 策略的有限候选集合；
- final ID/OOD gate 和一次性开启顺序。

Gate M3.0：诊断能够提出一个可证伪的主要假设，并证明 M3 的预算有限。若无法说明
为什么新干预可能改善端到端时间，则停止 M3，继续轨道 A。

### M3.1：数据可用性与新证据边界

目标：先让数据 gate 成立，再允许拟合。

建议切片：

1. 建立 M3 exposure ledger，列出所有 M0/M1/M2 已暴露 physical case；
2. 冻结新的 train/validation/final-ID/OOD 生成规则和 content-derived catalog ID；
3. 把 solver termination budget、失败保留规则和可训练样本政策写入契约；
4. 先执行 read-only production plan，再经授权 materialize 到仓库外目录；
5. 审计 manifest、index、checksum、split counts、失败分布和 label quality；
6. 只有 data gate 通过后才实现或运行 M3 fitting。

M3 不必强制“所有 case 都成功”，但必须在看结果前定义以下二选一规则：

- **完整标签 gate**：每个 train/validation case 都必须收敛；或
- **预注册可用性 gate**：保留每个失败记录，按预先固定且与 split 无关的规则决定
  哪些成功 label 可训练，并为各 strata 设定最低覆盖率。

不得再次因为观察到特定失败 case 而提高迭代数、删例、换 split 或生成第二个同名
catalog。

Gate M3.1：所有 artifact 审计通过，train/validation 满足预注册覆盖要求，final case
仍未被模型开发路径读取。否则停止 M3，不训练。

### M3.2：有限模型改进

目标：验证一个主要干预，而不是进行无边界架构搜索。

建议实验预算：

1. **Control**：在 M3 训练数据上重训 M1 轻量 CNN，用于分离数据规模收益；
2. **Primary candidate**：根据 M3.0 诊断选择一个明确改进，例如方向/几何感知表示、
   更适合 solution quality 的目标，或一个小型多尺度网络；
3. **One ablation**：只移除 primary candidate 的核心新增部分；
4. 每个候选使用同一组固定 seeds、相同数据访问边界和相同选择规则；
5. 训练成本、参数量、峰值内存和 checkpoint 均完整记录。

不在 M3 同时加入大模型、生成式模型、强化学习、surrogate solver 和 GPU FEM。
如果 primary candidate 在 validation 上不能同时改善质量可靠性和端到端时间前景，
不要开启 final test。

Gate M3.2：选择规则只使用 train/validation，所有 seed 保留，validation 上不存在
通过删 seed、删 case 或忽略 fallback 得到的收益。

### M3.3：可靠性策略与冻结

目标：在不隐藏成本的前提下减少低质量 warm start。

- 可靠性分数和阈值候选在预注册文档中有限枚举；
- 阈值只在 validation 上选择；
- reject-to-uniform 计入推理、判断和 uniform 全部成本；
- accepted failure 继续保留，并完整计费 fresh uniform fallback；
- 模型、checkpoint、阈值、统计代码和 runtime 在 final evaluation 前冻结。

Gate M3.3：冻结 artifact 可以从 clean revision 和锁定环境重建；任何 final case 在
冻结前均不可执行 learned comparison。

### M3.4：一次性 final evaluation

目标：在新的 untouched evidence 上回答 learned warm start 是否真实有效。

最低报告内容：

- uniform、physics heuristic、training-only nearest neighbor、M1 control 和 M3
  candidate；
- setup、inference、projection、refinement、fallback 和端到端时间；
- compliance、volume error、iteration、失败、拒绝和 fallback 率；
- 以 physical case 为 cluster 的 bootstrap interval；
- ID 与 OOD 分开报告，不用一方替代另一方。

建议 claim gate 延续 M2 的保守标准：

- ID mean candidate/uniform time ratio 的 95% 区间上界 `< 1.0`；
- accepted learned attempts 零 quality failure/fallback；
- 所有 operational result 满足 convergence、volume 和 compliance 质量边界；
- 没有在观察后删除 case、seed、方法或计时阶段。

只有 OOD failure 为零且 OOD mean-ratio 95% 区间上界 `<= 1.05`，才可额外使用
`OOD-safe`。未满足时发布负结果，uniform 继续为默认；不得启动未预注册的 M3.5
搜索来追逐正结果。

## 5. 版本、分支与验证规则

- 每一切片从最新 `main` 创建短期分支，通过 PR 和 CI 合并；
- 新平台契约、新 checkpoint 和新 ML artifact 都使用新的显式版本；
- 每个数值行为改动先写失败测试或独立验收，再修改实现；
- 所有生产执行先提交 contract/runner，再从 clean merged revision 做 read-only plan；
- dataset、checkpoint、数据库、日志、截图和运行结果不得提交；
- 每个阶段以独立 validation report 结束，报告失败同样视为有效阶段结论；
- 只有实际通过相应 gate 后才更新 README、简历和项目标题中的 claim。

## 6. 推荐执行顺序

按申请收益、风险和依赖关系，建议依次推进：

1. **A1.1 canonical demo case 与端到端 smoke**；
2. **A1.2 Docker/Compose 本地栈**；
3. **A1.3 架构图、演示视频与 clean-machine 报告**；
4. **M3.0 诊断与预注册 contract**；
5. **A2.1–A2.2 独立进程 worker 与 durable ownership**；
6. **M3.1 新 catalog、exposure ledger 与 data gate**；
7. 根据 M3.1 结果决定是否执行 **M3.2–M3.4**；
8. 再根据 profile 和部署需求选择 **A2.3、A3、A4**。

第一个实现切片 **A1.1** 已完成：版本化 canonical demo problem、窄运行入口和
端到端测试均已通过，输出保留在 Git 之外。下一个独立切片是 **A1.2**，只建立
API 与前端的本地 Docker/Compose 运行路径，不同时引入 worker、ML 或托管部署。

## 7. 阶段完成定义

后续优化不是以“增加了多少功能”为完成标准，而是以证据为准：

| 目标 | 完成证据 |
|---|---|
| 更容易复现 | 干净环境的一条路径、固定 demo、smoke test 和运行报告 |
| 更可靠的平台 | 崩溃/重启/取消/并发/重复领取测试与明确状态机 |
| 更强的性能 | 固定协议下的分阶段 profile、跨环境 benchmark 和数值等价性 |
| 更可信的 ML | 新 exposure boundary、预注册预算、一次性 final evaluation |
| 更好的申请展示 | 所有简历数字可回溯，演示与 README 不超过证据边界 |

若 M3 再次失败，但 A1–A3 完成，TopoLab 仍然会成为更强的 CS/SWE/Scientific
Computing 项目。ML 正结果是加分项，不再作为后续整体开发是否成功的单点条件。
