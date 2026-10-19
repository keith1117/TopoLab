# 新R身份：有限计费绑定修正及输入准备合同提案

日期：2026-10-18（America/New_York）。基线：`3459dd523d1fcf8b278b3a056f167095042e2077`。
提案身份：`topolab.v2.p17-m2-input-export-billing-revision.proposal.v1`，修订1。
拟执行身份：`topolab.v2.p17-m2-input-export-preparation.v2`，下称**新R/v2**；旧R/v1保持关闭。
结构化伴随：[JSON](p17_m2_input_export_billing_revision_proposal.json)。
当前状态：**AUTHORIZED_FINITE_R_V2；B_C_NOT_AUTHORIZED**（2026-10-19后续明确授权）。
所有者已批准本草案和JSON的完整新R/v2：`/root`3小时，新不同作者`/root/review_r_v2`2小时，
六角色FULL共1860秒，白名单40元数据和12/528/18原件完整字节核验、临时解析及规定字段提取。
实施细化见[新协议](p17_m2_input_export_billing_revision_protocol.md)，实际记录见
[报告](../validation/p17_m2_input_export_billing_revision.md)及[独立报告](../validation/p17_m2_input_export_billing_revision_independent_review.md)。
须先源码合并/四项main CI/冻结后一次独立公开入口，再R0、独立R0、R1及独立R1；
首次命名失败STOP、不重试；只允许一次新前缀共享收尾。不B/C、扩大输入、旧备份或自动后继。
下面保留最初文档提案的历史拟议语境；其“未授权/未来”由本后续明确授权在新身份范围内取代，
不修改旧R/v1合同、失败、成本、配额及封存。采样口径为目标<=0.5秒并保留实际间隔，
不把目标写成每次实际调度间隔的保证。

<details><summary>2026-10-18最初文档提案授权快照</summary>

状态：**PROPOSED_NOT_AUTHORIZED；DOCUMENTS_ONLY；B_C_NOT_AUTHORIZED**。

所有者本次只授权提出合同、预算和同步文档。新实现工时、独立子代理、命名调用及旧输入权限当前均为0；
本次旧源stat/读取集合为空。执行者仍拟为本对话`/root`；未来独立者须另行授权任命为不同作者，
旧`/root/review_r_exports`已结束的角色/工时不能沿用。本文没有启动独立审查、回归、发布或任何运行阶段。


</details>

## 1. 直接问题、证据及交付范围

实际核对本窗口分配的ec0b工作树：从干净分离HEAD上述提交开始，无已有修改或未跟踪文件；
只在本工作树创建`docs/m2-r-billing-revision-contract`。只读GitHub核对main仍为该提交、无开放PR；
[PR205](https://github.com/keith1117/TopoLab/pull/205)已合并，
[main CI39191422887](https://github.com/keith1117/TopoLab/actions/runs/39191422887)的
quality、frontend、clean-linux-smoke、i1-native-software全部成功。未重新触发工作流。

以[旧R实际报告](../validation/p17_m2_input_export_preparation.md#actual-r-execution-supplement--stopped-before-source-access)
及[独立报告](../validation/p17_m2_input_export_preparation_independent_review.md)为据：

- 旧首次公开I/O角色完整外层109.224秒；原收据使用7.01521454192698秒旧观察值，固定收费20秒。
  必需的完整外层加10秒为119.224秒，超过20秒，最终序列化器实际退出1。
- 内层fixtures字段检查通过不能覆盖上述失败；部分RSS188301312字节缺最终失败序列化器的峰值，
  完整RSS为`UNKNOWN_INCOMPLETE_FAILED_SERIALIZER`，不是已测超4GiB或不可行。
- 保留`STOP_NO_RETRY / FAIL_FULL_NAMED_WALL_CHARGE_BINDING`、原20秒收据、失败FULL120及共享FULL60，
  已付180/1860秒、1680秒关闭余量；R0/R1未启动且关闭，旧源stat/读取0，没有12/528/18导出。
  不诊断未有证据的调度/宿主延迟原因，不改写旧收据、报告、冻结计划或备份。

新R拟交付同一受限输入准备能力，只修正上述**外层收费绑定及失败证据缺口**。
不改变H/17算法、训练/终态定义、输入集合、容差、4GiB口径或科学验收。
新公开入口先通过，才可能按新授权执行R0再R1；成功也只记准备完成，不记P/17修复或科研Gate。

## 2. 最小未来源码改动及复用边界

下表仅为将来获准后的修改清单；本次不改源码、不执行任何入口。

| 位置 | 仅需的改动 / 原样复用 |
|---|---|
| `scripts/p17_m2_input_export_control.py` | 为新v2绑定新根、合同和新授权；六角色FULL收费表；将收据写入/最终完成序列化及一次新产物归档收尾纳入版本化冻结源码和实际调用表；记录完整外层事件并核对固定收费；失败也先保留可得RSS/退出。不得向v1根续写或接收v1的PASS |
| `scripts/p17_m2_input_export.py` | 仅新执行身份/新输出根及固定合同hash的入口绑定；`register`、字段提取、数组位值、来源/读取/字节保护及导出schema保持语义不变 |
| `scripts/p17_m2_input_export_independent.py` | 仅新入口身份/根绑定；由不同作者补齐完整外层收费、最终序列化器、实际退出及失败前缀的独立核对；原R0全表重建、R1逐原件比较和公开fixture语义复用 |
| 对应公开测试 | 只加计费/退出/身份绑定的回归及破坏控制，不新增求解、推理或科学样本；原来源/字段测试保留 |
| `scripts/p17_m2_resource_control.py`、`scripts/p17_m2_homotopy.py` | 复用已有stdio/原子写入及native记录原语；不改变其数值路径或新增证明后端。独立内层收据核对仍不代表完整外层通过 |

已提交源码的旧controller固定`ROOT=...preparation-v1`、固定旧冻结文件集；两个来源CLI也固定v1输出根。
因此不能仅换命令行路径或重用旧`owner_R_authorized=true`，声称已经是新身份。上述入口绑定是必要小改动；
旧数值/字段算法无须重做。未来改动属于新提交/新冻结；旧v1源码以PR204/main43ffed0和原hash保留，
不在旧冻结身份下修补、运行或覆盖旧根。
伴随JSON的历史快照hash仅标识本次所读版本；未来v2的实际源码hash必须重新填实，不能冒用旧源码hash。
旧未提交外部胶水仅有版本化报告的行为记录可用，不在本片重开；未来依据这些记录独立写有限绑定/新产物归档逻辑，
不读取旧R根、备份或旧临时脚本，也不把未见文本说成已经审查的最小补丁。

原B4.30及A/R公开软件证据仅说明已有实证方法/记录器和字段工具可复用，不能转移一次角色的内存PASS。
旧R公开fixture字段结果可指导软件回归，不能替代新v2独立实际公开I/O入口；旧失败RSS不能补零。
不新增事前完整分配、内核、ELF、全宿主证明、平台后端或观察器递归链。

## 3. 完整外层耗时与不可变计费绑定

每个命名角色在首次分派前即冻结`charged_wall_seconds = FULL(role_cap)`，不再用一个尚未结束的局部
耗时估算20秒收费。FULL是保守计费，不是速度测量；完整原始实测时间另存。不得用FULL作为客户查询速度。

1. **完整区间。** 外层可信执行工具/调用者在角色首次分派前记T0，到该角色最后一个已登记的计时、
   控制、核对、收据/序列化/flush、失败清理及实际最终退出均观察后记T1；`whole_wall=T1-T0`。
   包含启动/import、排队/工具往返、轮询、等待、角色内各工具调用间隙及所有binder/observer；不把几个不相交区间
   取max冒充全程，不在最后工具调用前封口。正式角色内不插入人工评审空档；实际发生的空档仍计费。
2. **时钟与事件。** 冻结外层时钟来源/单位/分辨率及时间域，保存有序原始工具事件、调用ID、开始/结束、
   实际exit和UTC交叉锚。子进程monotonic用于子区间，不与另一时钟直接相减。每事件须落入完整区间，
   正常核对`whole_wall`覆盖各实际子wall；缺开始/末尾、时钟倒退或无法闭合则UNKNOWN/STOP。
3. **成功判据。** 每角色检查`max(whole_wall+10, independently_reconciled_minimum_charge) <= frozen_FULL`。
   内层已包含的wall不重复相加；10秒是最低收费余量，不抵扣实际墙钟，不替代最后binder工作或实际退出。
   native wall、内层收据与外层事件都须一致；单看inner PASS或native wall不够。
4. **先记后判。** pending、冻结FULL值先于启动；收据与最后序列化器先保留可得的测量/失败记录，
   再检查收费和RSS。内部完成记录只记`PENDING_EXTERNAL_EXIT`，不得自证未来退出。
   实际外层工具返回事件与内部记录共同构成终态，明确使用旧R已采用的有限外层观察信任边界；
   不为了给最后观察工具自身再次出具证明而加无穷层observer。
   后继只接受绑定新身份/计划/FULL、完整外层费用/RSS/实际退出的终态；仅inner PASS或PENDING不得开门。
5. **失败费用不截断。** 一旦角色启动即记FULL，即使失败也不退回。若实测最低费用超过FULL，
   保留原FULL冻结/支出记录，再追加超支：已知部分至少为`max(FULL, ceil(whole_wall+10), ceil(inner_minimum))`，
   未测部分记`UNKNOWN_NOT_ZERO`；记录cap violation并STOP，不能以补记超支把该角色改判PASS。
   未启动角色记0并关闭，其FULL预留不能挪给失败角色。整个新执行未启动时预留不冒充已付。

新外层终态schema为`topolab.v2.m2-input-export-exit.v2`：至少绑定execution_identity、role、plan_sha256、
pending_sha256、frozen_FULL_seconds、clock_domain/T0/T1/whole_wall_seconds、raw_tool_event_ids/hashes、
inner_minimum_charge_seconds、native/helper_profiles、RSS_envelope_bytes及其组成/单位、actual_exit_codes、
cleanup、charge_record_sha256、status/reason。成功终态用`PASS_R_V2_FULL_ROLE`，只由完整外层绑定得出；
`charge_before_binder_wall_seconds`等旧字段只能留作内层诊断。失败中缺失项为null加具体UNKNOWN原因，
不得构造数值0。独立者核对原始工具事件而不是信任该派生终态；后继须同时满足来源字段接受和完整角色接受。

将来实际启动表须把外部调用胶水也纳入冻结：完整literal argv/cwd、调用/等待/观察顺序、源码或literal
脚本文本hash、所有helper/收据写入器和各自RSS/实际exit归属。优先把现有外部收据/完成逻辑收进同一
版本化入口，减少分离工具间隙；不能省略仍实际存在的调用。若在限定改动/预算内无法闭合，STOP并报告缺项，
不增观察层、变更标准或延长额度。新计划不得依赖未登记的临时脚本或v1外部记录作为oracle。

旧109.224秒仅是已发表故障用例：算术上119.224<=FULL120，余量仅0.776秒，
不证明新入口必能在120秒完成。保留原120秒上限；以后真实超时就停止，不能凭此历史数调大cap。

## 4. 4GiB RSS、完整退出及独立公开I/O预检

沿用新M2身份已获采用的**RSS/完整退出实证**，阈值`4294967296`字节，保留独立预检。
覆盖本次payload、控制器、计时、采样器、来源核对、binder、最终序列化器和已登记观察进程；
不是事前完整分配或整台Mac≤4GiB保证，也不替代旧I1/D1或B客体容量标准。

- 保留`/usr/bin/time -l`高水位、实际wait4峰值/exit、进程组/控制器采样及真实间隔，Darwin RSS为bytes，
  `ps`为KiB×1024，目标间隔<=0.5秒。保守相加可能重叠的峰值，不扣共享页；同一监督进程序列化前后取max，
  不重复累计该进程；不同helper不漏项，不能只取所有不相交命令的RSS最大值。
- 最终完成序列化器在拒绝收费/资源判据前，保留其可取得的峰值、原生退出profile及失败原因；
  外层工具再观察它实际退出。异常、OOM或写盘失败不能保证证据必得：缺一个必需项仍为UNKNOWN/STOP，
  失败外层事件/原日志保留，不能以`finally`或成功启动声称已经闭合。
- 每个实际来源角色分别取得本次完整链RSS/退出证据。公开入口通过不证明真实528标签解析会通过。
  继承inner watchdog `cap-20s`、outer supervisor `cap-10s`的有限清理留量，
  但最后完整外层仍须满足第3节；只清理本次登记树，组清理未确认即UNKNOWN/STOP。
- 新v2首次命名角色由不同作者进行一次公开I/O预检，只用新公开JSON/Safetensors fixtures和新输出根。
  复用两尺度、C/W权重及标量字段检查，再独立核对完整费用/RSS/退出；不是B的正式FULL180预检，不消耗B配额。
  任一失败/UNKNOWN关闭新R的全部来源后缀，不修补冻结代码再试。

公开回归至少包含：旧7.015/20对109.224的漏计反例；冻结FULL120下的119.224算术接受、
whole+10恰等于/略超cap；多个不相交helper区间；末尾serializer退出非0/缺RSS/缺exit；
测量/失败记录先于判定；写入失败、时钟倒退、旧身份收据/根及更改FULL值拒绝。
仅inner PASS但缺完整外层终态时，后继R0/R1必须拒绝。
时间边界用新合成事件测试，不为重现109秒故障进行无意义等待；冻结后的实际入口仍只有一次。

## 5. 输入权限及两步来源闭合

**当前旧输入权限为0。** 将来所有者若只批准修正软件/公开测试，仍不得进入R0/R1；
只有明确批准“新v2合同的3h+2h/1860秒、不同作者、下述完整字节/临时解析例外及R0/R1”才授予整次新R执行。
旧v1授权、unused cap或旧JSON的历史授权字段均不能提供新权限。

输入内容范围按原[JSON](p17_m2_input_export_preparation_proposal.json)精确字节快照约束，
SHA-256=`f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad`。
只继承伴随新JSON列明的**内容/上限字段**；不继承原授权、状态、执行根、工时、调用、STOP或旧结果。
无需复制/重论证原长提案。明确保持：

- R0每来源角色最多40个metadata/32MiB：7个literal bootstrap、固定21个unit、12个selection，各一次；
  原已发表hash与允许首次登记的reference progress/summary当前身份分开。R0不stat/open科学payload。
  独立者重建并比较完整登记表后才准R1；未知必需来源/不一致即STOP，不把新hash当历史防篡改证明。
- 12个固定checkpoint：C/17,29,43的epoch168,137,92；P为123,134,169；W为93,156,142；S为65,115,127。
  W仍来自B4.5；不替成A/P、不重新选择。每个10个F32 tensor/26433参数/105732数据体字节，原样副本。
- 528个train-only原标签：432个`12×6×3`及96个`24×12×6`；468/508/488为重叠成员。
  输出528生产+528独立视图，保留实际stored F32、原F64终态及至多11个原更新状态、来源pointer及IEEE位摘要。
  不重滤波、投影、FEM、敏感度、推理或完整旧轨迹分析；未来C每标签两次终态FEM仍未运行。
- 18个固定B4.30 sentinel原uniform成功/no-fallback packet，只取原binary64 compliance及最小来源/solver身份，
  不输出时间、密度、候选或旧轨迹；未来C仍需18个新uniform计时及rtol1e-9/atol0兼容核对。
- 原件每文件执行者、独立者各一次有界完整字节hash/临时普通JSON解析；语义仅上述原白名单。
  完整history可能临时物化，不能隐瞒此例外；不持久化/打印完整原label/packet或追随未获准指针。
  所有原路径/来源/字段/字节/次数/symlink/竞态保护不放宽；来源缺失不补读备份或换源。

原字节上限不变：checkpoint1MiB/合计12MiB；标签64MiB/合计768MiB；packet4MiB/合计72MiB；
生产视图128KiB/合计32MiB；审查视图2MiB/合计256MiB；标量总64KiB。这是拒绝上限，不是实测RSS。
科学A/B/C角色权限不因准备角色例外扩大；final/条件48/720/unused48及旧备份保持封存。

## 6. 新预算、命名角色及来源冻结

**全部待批准，当前新执行工时/调用/IO授权0。** 提议新执行者<=10800秒（3小时），不同作者<=7200秒（2小时），
含最小改动、公开调试、独立核对、登记/导出、定向等待、失败及收尾。各自不互借，也不借旧R/A余额。
本次文档成本另记UNKNOWN_NOT_ZERO，不消耗这些拟预算。

| 顺序 | 新v2命名角色 | 冻结收费/上限 | 前提 |
|---|---|---:|---|
| 1 | independent-public-check | FULL120秒 | 明确新R授权、干净锁定已合并且全CI成功源码、新公开fixture、新计划冻结 |
| 2 | exporter-r0 | FULL120秒 | 本次独立公开I/O的费用/RSS/实际退出全部接受；新源读取例外明确获准 |
| 3 | independent-r0 | FULL120秒 | 执行者R0来源登记完成、无STOP |
| 4 | exporter-r1 | FULL780秒 | 独立R0完整表及其hash通过 |
| 5 | independent-r1 | FULL660秒 | 执行者全部受限导出完成 |
| 6 | shared-closeout | FULL60秒 | 一次成功收尾或一次失败前缀收尾；只读新产物 |

执行者900、独立者900、共享FULL60，合计**1860秒**，六角色各至多一次、严格串行。
共享FULL60在新执行开始时全记，未用仍收费；未启动来源角色0，首次失败关闭余下来源额度。
角色一旦启动按FULL收费，没有额外失败重试名额；未超cap的全执行就计1860，不能事后挑较小费用。
共享收尾不是修复/重复入口，收尾失败也停止，不再添第七命名角色。尚未开始的新执行只有预留请求，没有已付。

拟新根`/Users/keith1117/Documents/TopoLab-data/p17-m2-input-export-preparation-v2`及
`p17-m2-input-export-preparation-v2-independent-backup`：本次未stat或创建，不复用任何旧v1根/备份。
将来冻结前须确认独占新根；已存在则停止，不覆盖/清空/挑另一个名字重试。
实际merged commit/tree、uv.lock、解释器/版本、M2 OS/arch、五线程变量=1、模块来源/hash、
新合同/内容快照hash、所有实际调用/计时/写入/观察者身份、不同作者及费用/权限表、四项exact-main CI、
新计划hash必须填实后才首次启动。R0新增的有限source registry是唯一预声明的登记增量。
这些实际绑定当前为`UNKNOWN_UNFROZEN`；不能拿本次文档基线当未来已冻结实现。

每次未来提交均先完成`uv sync --dev --locked`、`uv run ruff check .`、`uv run mypy src`、
完整`uv run pytest`、`git diff --check`，逐路径审查/暂存、发布守卫及全部上传提交审查。
最新PR头的四项适用CI全部成功才合并，再核对main/CI；干净锁定已发布源码先于命名角色。
结果也按正常发布流程，保留本工作树，只清理本片已合并且无新增工作的分支。
规定回归/CI/发布另记实际软件成本，不从1860秒扣或当零；角色作者投入及定向等待仍计各自工时，
重叠账本视图不相加冒充不相交墙钟。新采购/付费扩容上限USD0；已有CI/电力/订阅费用UNKNOWN_NOT_ZERO，
如需新增实际付款/配额，须先取得币种、费率、金额及付款人明确授权，否则停该付费动作。

## 7. 不同作者审查、验收及STOP

未来明确委派独立作者，先从冻结范围及公开故障事件独立写外层费用/退出核对，不以执行者PASS、
其派生elapsed或manifest为oracle；记录完成自己核对逻辑的hash/时间，再接触执行者新逻辑交叉审查。
后续交叉审查明示非盲。可以复用原独立字段/位值比较器及native记录原语，不需重写528标签算法；
但必须独立读取实际外层工具事件、FULL冻结值和完整RSS/helper/退出记录，不能仅比较两个派生PASS。

验收分开记录，不能跳步：

1. **软件交付**：最小修改、故障/边界控制、规定回归、独立源码审查及正常GitHub发布通过。
   这本身不接受一次命名I/O角色。
2. **新公开入口**：一次真实、冻结的independent-public-check全部字段、FULL120费用、<=4GiB完整RSS和
   实际末尾退出通过；内部PENDING与外部实际事件正确绑定。只开新R获准后缀，不开B/C。
3. **来源准备**：新R0全表独立接受，R1全部12/528/18来源/位值/限定视图/次数/字节及每角色费用/RSS/退出通过，
   新产物独立备份逐项bytes/SHA/无额外或symlink成员通过，才可记`PREPARATION_COMPLETE_SOURCE_BOUND`。
   未全部完成时分别记录完成量和UNKNOWN；不得把公开通过写成来源准备完成。

缺新授权/不同作者/精确已发布冻结；旧身份/根/收据混用；任何冻结源码/argv/收费/权限变更；
外层墙钟或helper/最终序列化器RSS/实际退出缺失；费用/RSS/工时/字节/次数超限；OOM、逃逸、清理不明；
来源/字段/集合/hash不符、禁止访问或公开入口失败，均**STOP_NO_RETRY**，禁止后续旧读取。
保存不可变pending/成功或失败前缀、实际退出、已知成本+UNKNOWN、完成/未启动数量及STOP；
不得为成功补造证据、修改旧收据、继续冻后调试、扩大额度、换源、重试/reset或转移余量。
唯一允许的后缀是已预留的一次只读新产物收尾；安全清理不授予新实验或额外调用机会。

## 8. 历史保留、未完成项及本次停止

FULL_V2_OPEN_NO_ADMITTED_ROUTE、固定P/17未修复、uniform默认、科研暂停、完整训练PENDING/4GiB保持。
B4.51 FAIL_PROCESS_SOURCE_FREEZE/已消耗1/1配额、D1 STOP/未启动0/1/FULL60、所有者关闭救援、
I1软件及资源UNKNOWN、B4.52 NOT_SELECTED_BY_R1、所有原失败/费用/封存不变。
K=12721.16417100014444982>7200、D1已付FULL60、旧R已付180秒及额外软件/CI成本分别保留，
新1860只是拟上限，不是旧7200的重置或总项目费用。旧B4.30两次行政调用/一个campaign/无第三次及reflection停止不变；
新身份只有明确新授权才可能执行，不能冒充旧B4.30续跑。
B客体容量采用仍独立有效、环境未准入、宿主额外开销UNKNOWN；不安装/探测/启动环境。
B3的M2+独立Ubuntu24.04、两尺度及最终独立复现义务不变；当前M2/CI不足以替代最终全部环境。

实际新source registry、528个case路径/hash、原件真实字段/bytes及新角色RSS/退出均UNKNOWN_NOT_RUN；
不是已证明超限/不可行，也不是获准试读。B正式预检FULL180、C科学14580秒及完整科学角色/调用/费用/视图
准入仍未批准；新准备通过也不自动授予这些阶段。

本次仅版本化文档及必要已提交源码文本、只读GitHub发布元数据；未实现/安装/试启动、
未stat/open旧数据或备份、未运行R公开入口/独立预检/B/C/实验。只做JSON、双份合同数量/预算/权限、
相对链接、历史字节保留及差异检查；草案保持未提交供审阅，不启动回归/CI/发布。
未正式委派独立子代理，不把本文自检写成独立审查通过。后续若提交仍完整遵守既有五项检查/发布规则。

**唯一下一项：所有者决定是否授权上述新v2的一次3小时执行+2小时不同作者、1860秒及明确的
40 metadata/12 checkpoint/528 train/18 uniform完整字节与临时解析例外；或只批准软件/公开部分，
此时R0/R1继续禁止。** 未有明确决定就停止；任何有限批准均不自动开启B/C或后继。
