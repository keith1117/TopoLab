# P/17 内容验真输入采集：具体源、目标、身份和阶段合同草案

基线：最新 main `ebf59a78c95e8279e4a9f444e856cf108b78ad0b`（PR220）；日期2026-10-24。
[机器可读草案](p17_m2_content_verified_source_acquisition_proposal.json)。**DRAFT_ONLY / 全部新执行预算、源读取、目标访问、角色激活均未批准。**
本轮只读源代码、Git内协议/报告及本轮新公开软件闭合记录，再编写这两份草案；未提交、推送或启动实现。
旧原件stat/read/copy/临时解析0、目标stat/probe/create0、正式角色0、B/C0、旧额度重开0。
不把本次草案编写计入已关闭准备钟，也不提前消耗尚未批准的新额度；未量化成本UNKNOWN_NOT_ZERO。

## 1. 目的、已完成能力及本次不能越过的界线

本合同拟取得的是**可追溯、独立来源核对的固定受限输入版本**，作为后续单独批准的P/17修复的输入。
它不运行H、B预检、C面板、FEM/推理/拟合，不修复P/17，不通过科学Gate。
依据[v2路线图第6节](TopoLab_v2_development_roadmap.md#6-current-sequence-after-the-delivery-reassessment)及
[有效开发方法](TopoLab_v2_delivery_reassessment.md#4-effective-development-methods)：先完成真实可执行软件和独立预检，再有限采集；阶段失败就保留证据并停止。

已完成：[公开准备协议](p17_m2_content_verified_custody_protocol.md)、
[报告](../validation/p17_m2_content_verified_custody_preparation.md)、PR220/main四CI。
新公开S1/S2/S3的40/558/1071链、同次缓冲消费和失败/收费/实际返回绑定已完成；本地2701通过/1平台skip。
外部`publication-closure.json`原始SHA256：
`42aace79c75d8d3f158e7fc5006b5d5e0d28408dd1259ea591928920dd31eb9a`；
闭合范围仅`NEW_PUBLIC_SOFTWARE_PREPARATION_ONLY`。前轮执行者6h/独立者4h全部关闭，余额不转移。

**已确认的实现阻塞**：main的`p17_m2_content_verified_control.py`只接受`PUBLIC_SOFTWARE_FIXTURE_ONLY`、
`formal_authority=False`与临时公开根；`p17_m2_verified_input.py`只接受`CheckedPublicInput`。
因此不能将本次批准写成一个布尔值、改路径或复用公开证书就开始正式运行。
需要新的正式scope适配、独立正式证书及源/目标/实际工具调用绑定，先用新公开数据补回归并完成受保护发表。
现有public拒绝门保持，不能增加skip-guards或把公开root改名伪装正式输入。

## 2. 新身份与权限分层

拟议执行身份：`topolab.v2.p17-m2-content-verified-source-acquisition.v1`。
拟议合同schema：`topolab.v2.m2-content-verified-source-acquisition-contract.v1`。
它区别于已关闭的public `topolab.v2.p17-m2-content-verified-input.v1`，不是旧R/v1/v2/v3的再试。
此刻运行身份/角色作者/activation token/新源码tree/plan SHA均未登记。

一次完整采用需明确确认：本草案及新保管模型适用范围、表中每阶段新预算、精确有限源的完整字节/临时解析例外、
固定目标的setup权限，以及新执行者和不同作者独立者。批准前一律不执行；批准后也按下述门槛逐阶段进入。
本草案提出的前置适配准备只有新公开数据，不读旧原件、不触碰真实目标；正式读/建仅在唯一T0后按角色发生。
B/C、安装/购买、全局同步修改、旧备份/配额/封存内容和自动后继始终不在本合同内。

旧内容合同仅继承字段/来源/格式/cap规则：
`p17_m2_input_export_preparation_proposal.json` raw SHA256
`f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad`。
JSON列出准确继承pointer及文件SHA；所有旧authorization/current_authority、身份、目录许可、作者和预算字段均屏蔽。
旧协议/报告原字节、FAIL/STOP/UNKNOWN、费用、已消耗配额和封存继续保留。

## 3. 具体源文件白名单：28个固定路径＋12个有来源约束的selection

唯一拟议原根：`/Users/keith1117/Documents/TopoLab-data`。
下表都是该根下的**单个literal**；不授权目录枚举、glob、旧backup或独立旧index文件。
`b3_training.json`内部已嵌入data index，不另读`b3-v1-data`的index。
表内未填hash的unit须满足固定context、顺序、previous/head闭合链，不是自由首次观察许可。
只有reference progress/summary两项允许按已冻结内容合同在获准R0中登记“当前观察hash”，
并结合已知context、固定18例、已发表audit和执行者来源声明独立核对；这不证明从未发表的过去hash。
mandatory来源/字段仍未知即STOP，不选其他面板补齐。

| 相对literal路径 | 单文件拒绝上限bytes | 预发表SHA256或约束类别 |
|---|---:|---|
| `b3-v1-fits/b3_training.json` | 16777216 | `229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7` |
| `b4-5-weighted-terminal/fit/progress.json` | 1048576 | `5e54f8cede96d9e4b60acc17586d25d29903bd4927461a8d6b4b18f3b49e43ac` |
| `b4-5-weighted-terminal/fit/summary.json` | 1048576 | `513064fe615456fe8204b511f850a71150895038c3541ad23f5cd35642b0cc6c` |
| `b4-30-z-reflection-repair-v2/context.json` | 1048576 | `cd0dffbb28347889726baacb8225efd9b2dadd94ea86f7485c843170b1ec2181` |
| `b4-30-z-reflection-repair-v2/sentinel/independent_audit.json` | 1048576 | `e9a8278b9a7d521992f7f5d62f3aef626e0767cd717f3ee134c2c4cc58b5ca2a` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/progress.json` | 1048576 | UNKNOWN_FIRST_REGISTRATION_ONLY_AFTER_R_GRANT |
| `b4-30-z-reflection-repair-v2/sentinel/reference/summary.json` | 1048576 | UNKNOWN_FIRST_REGISTRATION_ONLY_AFTER_R_GRANT |
| `b4-5-weighted-terminal/fit/units/0000.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-5-weighted-terminal/fit/units/0001.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-5-weighted-terminal/fit/units/0002.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0000.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0001.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0002.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0003.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0004.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0005.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0006.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0007.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0008.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0009.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0010.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0011.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0012.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0013.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0014.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0015.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0016.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0017.json` | 32768 | REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION |

其余12个R0文件只有以下固定逻辑模型的selection，不能预先猜测SHA或选择新epoch：

| 模型 | 固定epoch | 唯一来源 |
|---|---:|---|
| C/17 | 168 | B4.1 / recipe C |
| C/29 | 137 | B4.1 / recipe C |
| C/43 | 92 | B4.1 / recipe C |
| P/17 | 123 | B4.1 / recipe P |
| P/29 | 134 | B4.1 / recipe P |
| P/43 | 169 | B4.1 / recipe P |
| W/17 | 93 | W weighted-terminal / recipe P |
| W/29 | 156 | W weighted-terminal / recipe P |
| W/43 | 142 | W weighted-terminal / recipe P |
| S/17 | 65 | B4.1 / recipe S |
| S/29 | 115 | B4.1 / recipe S |
| S/43 | 127 | B4.1 / recipe S |

C/P/S的selection ref只取`b3_training.json#/outcomes`中精确(recipe,seed)对应项；
W只取`fit/units/0000..0002.json#/payload`的对应W/17、29、43，并核weighted-terminal wrapper、P recipe及内外checkpoint绑定。
实际路径必须等于对应root的`artifacts/selection/<ref.sha256>.json`，同时核ref.byte_size/SHA；每文件≤256KiB。
这是**有精确来源、精确数量的延迟绑定**，不是允许扫描的路径模式。
R0实际顺序为7 bootstrap→3 W units→12 selection→18 reference units；每作者恰好40文件、总≤32MiB。

## 4. 558个payload的冻结规则和输出

R0只读取上述40个metadata，派生payload声明；在独立R0完成自己的40次读取并接受之前，**不stat/open任何payload**。
完整558项literal path、声明bytes/SHA、上下文、逻辑角色、来源pointer及R0 metadata已观察身份须写入registry并冻结；
**payload实际四元组只在各自R1中首次观察并交叉比较，不能为填R0表而提前stat payload。**
不能把现在的null解释成通配授权。本草案JSON如实保留尚未登记的字段；本轮不为填表读取原件。

| R1集合 | 精确数量与来源约束 | 可持久化的新内容 |
|---|---|---|
| checkpoint | 上表12个固定模型；同一selection的checkpoint ref；`<root>/artifacts/checkpoint/<ref.sha256>.safetensors` | 原字节副本，不重存/重选；10 F32 tensor、26433有限参数的原header/offset检查 |
| train label | 冻结内嵌B3.4 index中唯一role=train集合528个：432个12×6×3、96个24×12×6；468/508/488重叠成员不增加原件；`b3-v1-data/artifacts/label/<case_id>/<artifact.sha256>.json` | 每例producer/audit两受限视图，保留角色/尺度/来源、原F32/F64位值及指定末窗，不持久化完整旧label/history |
| uniform packet | 固定18 case ID完整列于JSON；只能取reference固定18 unit的outcome ref：`.../artifacts/outcome/<ref.sha256>.json`；原uniform成功、failure/fallback空且metrics=terminal | 仅规定binary64 compliance/来源绑定等标量；无旧timing、candidate、密度或history导出，不作H选择oracle |

预发表embedded B3 index SHA：`b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26`；
W context：`0454eee24c1c72c051f10dce0162f0f41d5a5ade1fb3a4e5b42c9c82c9d11071`。
原件每作者每文件最多一次完整有界读取：40+558=598，两作者总上限1196；共享/filing/未来消费者原件读取0。
一次缓冲完成完整hash/临时parse/受限转录，短读或失败不补读，不执行旧loader、推理、拟合、FEM、filter/projection或完整旧轨迹验收。

本地`content/`恰好1071普通成员：registry1、checkpoint12、models1、NN-producer528、NN-audit528、scalars1。
`version_id=SHA256(canonical(content-manifest))`；manifest不含自身hash/version，真实物理身份另存evidence。
保留source/local/backup的declared/before/after/closing(dev,ino,size,mtime_ns)、完整长度/hash/来源/IEEE核对。
同hash换inode仍STOP；真实元组变化原因优先，身份不变的长度不一致单列read_size_consistency；都不修复后重读。
源失败保留ordinal/path/已有元组/已读bytes与hash/原始主错/次级记录错误/完整前缀和packet，未知不写0。

## 5. 固定目标与真实租约（此刻全部未探测）

沿用已提出的同一组literal，不另选第三个目录：

- parent：`/Users/keith1117/Library/Application Support/TopoLab-custody`
- generation：`/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-v2`
- backup：`/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-v2-independent-backup`

当前存在性、实际inode/local filesystem、owner/mode、可用空间、实际租约全为UNKNOWN_UNPROBED；
没有以路径名字推断非同步。采用的新模型明确保留provider覆盖UNKNOWN，**不保证绝不同步/上传、外部程序不写或持续可用**。
先前owner对这个parent的登记工具写入声明和有限备份清单可保留，不再把“证明不参加同步”作为本新模型的前提。

只有新授权＋唯一T0后setup≤300s可按dirfd/nofollow逐级检查并创建固定parent（若不存在且授权齐备）、
全新generation和backup；新目录0700、文件0600、普通单link、独占新建/fsync，local filesystem、身份/容量/cap需有实际证据。
正常root所有的系统祖先（例如`/Users`）可以接受，不要求所有系统祖先都属euid；只有固定TopoLab parent/generation/backup要求euid和私有0700。
现有不安全parent或已存在generation/backup即STOP，不更名/覆盖/修权限或换根续跑。
备份逐文件独立inode，不硬链接；同设备可接受，不声称异设备或灾难隔离，不准购买新存储。

真实O_EXCL/nofollow锁及持有人/内容/四元组回执只协调登记TopoLab读写者，不能锁住其他应用。
writer结束后content不再写；独立者只读，shared仅写限定evidence/backup。
保管跨正式关闭，覆盖filing等所有登记reader的实际最后返回；其后单独观察release。
不能在未来退出前预写自己的release/完整退出，也不能将UNKNOWN cleanup当作可另起helper备份的理由。
失败产物保留私有隔离，租约/清理未知不伪称已释放。

## 6. 六角色的具体启动门槛

T0之前必须全部满足：新批准、不同作者及实际调用者表、新正式适配器/独立正式证书、完整新公开正反回归、
五项本地检查、clean locked protected-merged新源码、精确PR/main四CI、实际解释器image/-I/orig_argv/cwd/OS/import/lock/线程1及完整native/工具观察绑定。
基线main仅提供公开能力，未来正式implementation commit/tree/plan SHA必须另行真实登记，当前不得预填。
合同/基本plan先冻结；允许明确登记的目标物理事实在setup、源558声明在R0取得，再以有hash的附加绑定冻结。
这两处延迟事实不允许改变白名单、阈值、cap、源码或运行身份。
新原件/目标访问授权以及角色表不齐，就零启动；不批准只试一个前缀。

启动条件按事实能实际取得的阶段分层，避免把未来事实误设为启动前提：

| 门槛 | 此时必须真实取得 | 不提前要求/伪填 |
|---|---|---|
| T0前 | 新授权/作者/预算、正式源码/runtime/基本plan冻结、新公开入口回归、精确PR/main四CI及机制预检 | 真实目标inode、原件身份、未来正式角色RSS/退出或release |
| T0内setup、首dispatch前 | 安全local私有目标、空间/cap、真实锁和物理绑定 | 旧源实际身份/资源PASS |
| 两R0接受、任何R1 payload stat前 | 各40 metadata完整来源/身份、558 literal声明大小/hash闭包、双方metadata元组一致 | payload实际四元组/header/读取结果 |
| 各R1/独立R1完成 | payload实际四元组/完整bytes/IEEE及1071成员完整独立比较 | 后续shared/filing/release的未来返回 |
| 每角色及最终filing/release真实返回后 | 原始完整native/工具/RSS/退出/清理/耗时/收费与最终有限接受 | 自己尚未发生的退出/消息或科学权限 |

setup≤300s并取得/接受真实目标锁和绑定后，首发剩余≥4200s。
每次正常派发都按“尚未结束的完整六角色suffix FULL＋协调240＋封存360”检查剩余，不用上次跑得快来削减reserve。

| 顺序 | 唯一一次角色 | FULL秒 | 原件内容读取上限 | 派发前共同窗口至少剩余秒 | 前驱和本角色条件 |
|---:|---|---:|---:|---:|---|
| 1 | `independent-public-check` | 300 | 0 | 4200 | 新公开数据的实际冻结启动/native/完整返回通过；旧原件stat/read必须为0。 |
| 2 | `exporter-r0` | 300 | 40 | 3900 | 前驱完整PASS、真实租约有效；仅读40 metadata，登记558项声明，不stat/open payload。 |
| 3 | `independent-r0` | 300 | 40 | 3600 | 独立再读40 metadata，独立验完整链/来源/成员及双方bytes/SHA/四元组；完整558 literal registry冻结后才放行R1。 |
| 4 | `exporter-r1` | 1200 | 558 | 3300 | 独立R0接受＋完整声明/预算；一次读取558原件，产1071受限成员，不做科学运算。 |
| 5 | `independent-r1` | 1200 | 558 | 2100 | 独立一次读取558原件及全部新content，逐项比较完整bytes/schema/IEEE/来源/四元组，核所有实际资源/退出/收费。 |
| 6 | `shared-closeout` | 300 | 0 | 900 | NEW-only显式白名单备份；各组确已退出且实际返回已观察。失败时仅准满足同等清理/窗口条件的预付共享例外，源后缀仍关闭。 |

独立public完整PASS之前旧原件stat/read=0；R0接受前payload stat/read=0。
正式入口、独立checker和证书均须区分新正式scope与公开scope，不能只信序列化PASS或调用生产checker自证。
各实际角色需要自己的完整≤4GiB native RSS包络、真实outer/helper/serializer退出与group cleanup，不能拿公开峰值填真实角色缺口。
首个失败STOP；只有已有真实前缀、所有已启动组清理/实际返回已证实、仍满足冻结窗口时，才能执行预付NEW-only shared例外。
这个例外不放行源后缀，不退款，不授予输入证书。

## 7. 全新阶段预算提案（均未批准）

| 阶段 | 执行者 | 不同作者独立者 | 启动和结束 |
|---|---:|---:|---|
| 正式scope适配/绑定准备 | 14400s（4h） | 10800s（3h） | 各自批准并新委派后的首工具起连续计时；含实现、失败/等待、中断、公开测试、五检查、PR/main四CI、独立审查和真实返回；不触碰目标/原件。双方须在各自准备cap内共同就绪并进入T0，否则preformal STOP |
| 正式采集/来源验收 | 同一4500s（75min） | 同一窗口 | 全部前提满足后的唯一T0起，正式关闭/关闭失败最晚T0+4500；不是CI前先启动时钟或先读源 |
| 结果审查/发表/有限封印 | 7200s（2h） | **7200s（2h）** | 同一T_result起至各自实际最后工具及消息返回；含下述filing180、报告/独立验收、每次commit前五检查、精确PR/main四CI、完整NEW证据留存和有限闭合 |

新增适配准备仅解决第1节已确认的formal-scope缺口，复用已完成S1/S2/S3，不重做整套准备或新目录/云控制研究。
它是拟议新预算，不开启旧6h/4h或任何旧4h/3h；若不单独采用它，当前代码缺口使正式0启动。
各作者从本次适配准备首工具至最终返回还受总连续上限约束：执行者26100s（7h15）、独立者22500s（6h15）；
阶段交接间隙和所有等待都计入，不暂停/重置/转移。FULL3600、filing180已经包含在阶段包络内，不能再次加为额外额度。

**结果独立预算的新采用点**：此前2h/1h只是未授予提案。本草案只建议独立者从1h改为2h，执行者仍2h，
正式4500、六FULL、STOP、4GiB和所有收费规则不变；需owner明确采用，不能现场延长。
可核对的最近实际时间：本地五检查07:31:16→07:49:58约18m42；PR CI07:50:23→08:16:40为26m17；
main CI08:17:33→08:35:40为18m07；合计约**63m06**，尚未含报告、filing、独立最终审查、归档和实际返回。
因此同起点独立1h不能覆盖这条已观察路径。新2h也是上限而非完成承诺；队列/失败用尽仍STOP，不补预算。
结果只作一个有完整检查的范围内commit；之后用不可变外部有限闭合绑定未来main CI/真实返回，不再自动追加一轮after-CI文档commit。

T_result：未激活时为真实preformal STOP；已激活则为真实正式关闭或关闭失败的STOP前沿，最迟T0+4500。
双方deadline由同一T_result固定，不能因为首个结果工具晚到、等待、中断、报告尚未写完而后移。
某作者较早完成自己的独立final后，执行者只能在自己的窗口完成已约定有限尾部；不能递归叫回独立者重审自己的未来回执。

六角色FULL固定300/300/300/1200/1200/300=3600；独立不重叠setup300＋协调240＋封存交接360=900，总4500。
shared300在首次dispatch前预记一次，shared自身不再重复记；其他角色在各自dispatch前记全额。
失败、启动失败、早退、共享未能执行均不退款；零dispatch不记六FULL，但实际setup/准备成本仍保留。
接受要求`max(真实完整外层wall+10, 独立核内部最低收费)≤FULL`；失败/超窗仍保留
`max(FULL,ceil(有效whole-wall+10),ceil(已知内部最低收费))`，缺测UNKNOWN_NOT_ZERO。
所有controller/supervisor/sampler/serializer/helper和工具间隙直到实际最后返回均在规定包络内。

结果最多一次filing helper，FULL180、native timeout160，**包含在两作者结果预算内，不额外增加180s**。
只读真实新共享packet/登记NEW backup，不读原件或改content；相关组/前序返回未知不得启动。
filing派发前，双方结果窗口都须至少剩余**4860s＝filing180＋lease-release180＋有限发表/最终返回reserve4500**。
其中4500s预留依据是最近检查/CI合计3786s＋714s审查/归档/返回裕量；它是操作预留，不保证未来队列或失败可容纳。
filing真实返回后，最多一次lease-release元数据动作，双方剩余须≥4680s；其完整outer wall+10≤180、native timeout160、完整4GiB/退出/清理也须外层核验。
lease-release只读新租约/plan/返回元数据，不消费科学content、不读原件，不是第七个正式角色、不另增冻结FULL；按实际完整wall+10及内部最低收费保留费用，未知不写0，计入结果预算。
filing及release的真实最后返回都被观察后，才可记录最终release和有限证书；不能由它们预写自己的退出。
货币、电力、订阅/CI费用UNKNOWN_NOT_ZERO；时间cap不是货币0。无新安装/购买/付费provider承诺；需要新支出时另行停止申请。

## 8. 大小/资源拒绝上限与最后验收

沿用每作者884MiB源读取拒绝上限（R0 32、checkpoint12、train768、uniform72MiB），两作者1768MiB。
单checkpoint≤1MiB、label≤64MiB、uniform≤4MiB；NN-producer≤128KiB且总≤32MiB，NN-audit≤2MiB且总≤256MiB。
registry/models/scalars≤8MiB/1MiB/64KiB；manifest≤2MiB；单evidence≤16MiB，主根evidence≤256MiB/512文件。
正式新namespace（主根＋唯一backup＋公开fixture/helper/临时partial）总≤2GiB、4096普通文件；不混入software checkout/cache。
这些是拒绝上限，不是已测真实源大小、磁盘速率、可完成性或内存定理。

全部原件来源、两端完整bytes/字段/IEEE及四元组、1071成员、独立inode NEW backup、六角色完整资源/收费/窗口/实际返回、
shared handoff、真实filing最后返回及lease release、不可变外部证据和已发表有限闭合共同齐备，
才可记`SOURCE_ATTESTED_LOCAL_INPUT_VERSION_ACCEPTED_SCIENCE_CLOSED`。
缺失/失败则STOP_NO_RETRY或具体UNKNOWN，保留原件上下文/完整packet/有效耗时/全额收费；后缀UNKNOWN_NOT_RUN。
证据清单明确排除自身及未来ack，实际工具返回由外层观察，不用helper预写PASS证明自己的退出。
后续科学消费者仍须另获批准、formal-scope证书＋实际opaque reader lease，只有核验的同次buffer可进入decoder；
不fallback旧根/旧index/backup/未接受generation。producer与audit视图权限继续分离，B/C均不开放。

## 9. 剩余阻塞和最小顺序

| 分类 | 阻塞 | 解除条件 |
|---|---|---|
| 已确认 B1 | 当前代码/证书严格PUBLIC-only，正式scope适配缺失 | 新授权后仅以新公开数据完成最小正式绑定、独立检查及完整受保护发表；此前不能登记正式plan |
| 已确认 B2 | 本轮仅草案，所有新预算、源/目标访问、作者及激活未批准 | 明确采用具体合同、读取例外和新阶段预算；新委派不同作者，绝不继承旧额度 |
| 待验证 B3 | 目标存在性/安全/locality/空间及真实lease未知 | 获准唯一T0的setup300内实际取得；失败即停，不试新目录或再追求provider EXCLUDED |
| 待验证 B4 | 12 selection、558 payload完整literal身份及两份reference当前来源未知 | 获准R0两作者完整独立核对并冻结registry；这是R1前提，不要求先越权读源填表 |
| 待验证 B5 | 真实源IO/完整资源/退出/总耗时/最终备份filing尚无证据 | 各获准角色一次执行，按实保留；公开PASS不能替代 |
| 新采用点 B6 | 既有独立结果1h提案不足以覆盖最近63m06的检查/CI路径 | 前瞻批准本草案独立结果2h或保持未激活，禁止事后延长旧窗 |
| 下游 B7 | P/17未修复、B/C未批准，旧all-paid已超7200且full-fit仍PENDING4GiB | 本合同不解除；输入成功后再单独审定科学B/C，不能自动推进 |

历史第12次身份变化的具体成员/原因仍UNKNOWN；归因于iCloud/OneDrive、实际源一定完整、目标绝不同步、预算必够均不是已确认事实。
最小顺序：**审定本草案→新公开数据的正式scope绑定准备→全部就绪才新T0六角色采集→结果有限闭合→停止**。
本轮止于草案，不启动上述准备、源读取、目标访问、角色或后继科学工作；不更改当前status/旧协议为已授权。
