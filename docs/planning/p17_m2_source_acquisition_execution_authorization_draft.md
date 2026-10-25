# P/17 正式采集授权草案 v1（待审批，未执行）

基线：2026-10-25 实际查询的最新 main `80f9eb8b44f8efb3ffbe158b33a48fe34ba94b64`，tree `f75963f322a5242fdc2b565c5f91e15c20cc81f4`，
[PR221](https://github.com/keith1117/TopoLab/pull/221)。
[机器可读草案](p17_m2_source_acquisition_execution_authorization_draft.json)，raw SHA256 **`401c32618ef6fb964d0efc425dc2f792ce92baf7a7e483d8bdbafa1c08906786`**。
本文件及 JSON 都是 **DRAFT_ONLY**；本轮只有只读核对和本地起草，不是授权文件，不启动任何新预算或角色。
批准前执行权限全部为 false；拟议权限仅列在 JSON 的未来模板中。
保留原工作区及历史工作区共25项未提交内容、两份既有提案原字节；不提交或推送本草案。

## 1. 本次批准能交付什么

唯一目标是 **`SOURCE_ATTESTED_LOCAL_INPUT_VERSION_ACCEPTED_SCIENCE_CLOSED`**：
两作者独立核对来源、完整字节、物理身份与受限转录，取得一个固定本地输入版本及独立备份，完成有限结果发表后停止。
它解除后续种子17修复的“没有获准且可追溯输入”这一前置阻塞；**不修复种子17，不运行B/C、H/FEM、推理、训练或科学面板，不通过科学Gate**。
[v2路线图第6节](TopoLab_v2_development_roadmap.md#6-current-sequence-after-the-delivery-reassessment)规定：
先输入，之后另行批准B资源准入和C固定P/17修复，再谈独立新样本确认、完整B4和B5。
固定P/17、uniform默认、FULL_V2_OPEN_NO_ADMITTED_ROUTE、历史all-paid超7200、full-fit PENDING4GiB及全部FAIL/STOP/UNKNOWN/费用/配额/封存保持。

## 2. 绑定已完成收尾，旧预算关闭

必须先对下面两份 **新公开软件准备收尾** 的普通文件作no-follow有界读取并核对完整raw SHA；本轮已读并核对一致，且为独立inode、0444文件：

- 主份：`/Users/keith1117/Documents/TopoLab-data/p17-m2-formal-adapter-preparation-20261025-0806-a4fc2e7f/publication-closure.json`
- 镜像：`/private/tmp/topolab-formal-binding-preparation-retention-0806-a4fc2e7f/publication-closure.json`
- SHA256：`62977ea64ae3241eac514304d3b06e3ba3ce40272ae47b01ddae18dee7b3ff3b`
- 要求状态：`FORMAL_BINDING_PREPARATION_COMPLETE_FORMAL_CLOSED`；协议SHA `ad3745d028931d5469e3be76467da391ef0289addbf46fbe909a808497c285f0`。

该收尾绑定 reviewed head `7ab3963329f31d046487371678eb77e01d8e4ca3`、上述main/tree；
[精确PR CI40179485353](https://github.com/keith1117/TopoLab/actions/runs/40179485353)及
[精确main CI40181787855](https://github.com/keith1117/TopoLab/actions/runs/40181787855)四job均PASS，最终本机2739通过/1平台skip。
执行者已封存保守费用12946.710839250125s/14400s，独立者实际最终返回保守费用9316.316365042236s/10800s；**两钟关闭，余额不转入本合同**。
独立者在原3h内对固定源及证据完成审查，执行者随后在原4h内核实后续CI；不补写独立者亲自观察未来CI的事实。

收尾披露的早期临时unit目录和pytest745目录缺失、保留日志/源码/回执、失败局部归档未获接受等限制继续保留；不重建、不改写封存记录。
它证明公开适配准备完成，40/558/1071公开链可运行；其中实际原件、正式目标、正式角色和B/C都是0，输入接受为false。
源码及报告的“待发表”措辞保留原作者时点，本收尾提供其后实际完成证据。

## 3. 新身份、作者与正式授权文件

- 执行身份：`topolab.v2.p17-m2-content-verified-source-acquisition.v1`；正式scope：`SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY`。
- 新授权实例：`p17-m2-source-acquisition-owner-grant-v1`，一次使用；复用已实现的软件身份，不复用任何旧调用机会。
- 拟新任命执行者 `/root`；拟新委派不同作者 `/root/formal_acquisition_independent_v1`。批准后才实际委派、登记调用者与命令；禁止恢复已关闭的独立审查作者/预算。作者名冲突或不能满足独立性即STOP，不自行换人。
- 正式实现源基线为上述main。未来授权文件加入前后，`source_freeze()`内除该授权文件外的源/合同字节必须等于该实现提交；仅第7节明确列出的测试fixture兼容改动可另行冻结进发表tree。需要生产逻辑变更就停止，不能悄悄更新基线。

实际入口只认 Git 内 **`docs/planning/p17_m2_source_acquisition_execution_protocol.json`**。
该文件目前不存在，**本轮不创建**；草案JSON采用不同schema和文件名，不能被当成实际授权。
批准后，在新准备预算内填入实际owner批准消息引用、独立预检原始SHA及本草案JSON原始SHA，登记上述新作者，经过审查和正常发表后才有条件进入T0。
未来文件的必要字段见 JSON `execution.future_authority_template_NOT_EFFECTIVE`；`permissions`严格为formal/old_original/target=true、B_C=false，formal4500、result7200/7200。
模板中的null代表尚未发生的事实，不能用任意非空字符串或假hash填空。

独立预检只绑定已知软件、拟授权内容、实际作者/runtime/命令；其原始回执hash写入授权文件。
后续精确授权文件SHA、实际最新main及四CI通过再由实际启动就绪检查核实；不让预检证明未来CI、不让文件hash自引用，也不把字符串存在当作证据已核验。
任何影响源、执行合同、权限、阈值、预算或正式命令的变化都使旧预检失效；不能边改边继续正式角色。

## 4. 源文件白名单与分阶段读取例外

唯一原根literal：`/Users/keith1117/Documents/TopoLab-data`。
仅下列四个受限子根中的指定文件可进入未来授权，**不枚举目录、不glob、不读旧backup/旧profile/额外index或封存内容**：
`b3-v1-fits`、`b4-5-weighted-terminal/fit`、`b3-v1-data`、`b4-30-z-reflection-repair-v2`。

内容规则只继承 `p17_m2_input_export_preparation_proposal.json` 的指定内容字段，raw SHA
`f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad`。
已冻结采集提案JSON SHA `2c7d0e9243b3ab6beda9344b06c7e88cfbf03910f7104fa43f91c54670a32304` 保留原字节；
其中原准备4h/3h、联合26100/22500和“必须在旧准备cap内进入T0”等预算/授权不继承。本草案第7节是唯一待审批的新预算。
JSON明确列出继承pointer和新基线文件hash；旧authorization、角色、旧输出目录许可和预算全部屏蔽。

**R0固定28个literal**（相对唯一原根，逐项，无省略的目录范围）：

| 相对路径 | 单文件bytes上限 | 预发表SHA256或来源约束 |
|---|---:|---|
| `b3-v1-fits/b3_training.json` | 16777216 | `229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7` |
| `b4-5-weighted-terminal/fit/progress.json` | 1048576 | `5e54f8cede96d9e4b60acc17586d25d29903bd4927461a8d6b4b18f3b49e43ac` |
| `b4-5-weighted-terminal/fit/summary.json` | 1048576 | `513064fe615456fe8204b511f850a71150895038c3541ad23f5cd35642b0cc6c` |
| `b4-30-z-reflection-repair-v2/context.json` | 1048576 | `cd0dffbb28347889726baacb8225efd9b2dadd94ea86f7485c843170b1ec2181` |
| `b4-30-z-reflection-repair-v2/sentinel/independent_audit.json` | 1048576 | `e9a8278b9a7d521992f7f5d62f3aef626e0767cd717f3ee134c2c4cc58b5ca2a` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/progress.json` | 1048576 | `UNKNOWN_FIRST_REGISTRATION_ONLY_AFTER_R_GRANT` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/summary.json` | 1048576 | `UNKNOWN_FIRST_REGISTRATION_ONLY_AFTER_R_GRANT` |
| `b4-5-weighted-terminal/fit/units/0000.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-5-weighted-terminal/fit/units/0001.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-5-weighted-terminal/fit/units/0002.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0000.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0001.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0002.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0003.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0004.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0005.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0006.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0007.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0008.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0009.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0010.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0011.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0012.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0013.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0014.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0015.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0016.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/units/0017.json` | 32768 | `REQUIRED_CONTEXT_ORDER_PREVIOUS_HEAD_CHAIN_NOT_FREE_FIRST_OBSERVATION` |

**另12个R0 selection**只来自下列固定模型/epoch和唯一pointer：

| 模型 | epoch | 唯一来源pointer |
|---|---:|---|
| C/17 | 168 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=C,seed=17]/selection` |
| C/29 | 137 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=C,seed=29]/selection` |
| C/43 | 92 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=C,seed=43]/selection` |
| P/17 | 123 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=P,seed=17]/selection` |
| P/29 | 134 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=P,seed=29]/selection` |
| P/43 | 169 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=P,seed=43]/selection` |
| W/17 | 93 | `b4-5-weighted-terminal/fit/units/0000.json#/payload` |
| W/29 | 156 | `b4-5-weighted-terminal/fit/units/0001.json#/payload` |
| W/43 | 142 | `b4-5-weighted-terminal/fit/units/0002.json#/payload` |
| S/17 | 65 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=S,seed=17]/selection` |
| S/29 | 115 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=S,seed=29]/selection` |
| S/43 | 127 | `b3-v1-fits/b3_training.json#/outcomes/[recipe=S,seed=43]/selection` |

C/P/S实际selection路径严格等于 `b3-v1-fits/artifacts/selection/<ref.sha256>.json`；
W严格等于 `b4-5-weighted-terminal/fit/artifacts/selection/<ref.sha256>.json`，每项≤262144bytes，同时核ref字节数/SHA/固定recipe与epoch、W weighted-terminal wrapper及内外checkpoint绑定。
这些名字只有获准R0可从指定pointer得到，现在不猜hash、不以模板路径扫描。
每作者R0顺序恰为7 bootstrap→3 W units→12 selections→18 reference units，共40，合计≤32MiB。
只有reference progress/summary两项允许按冻结规则登记当前观察hash；仍须核固定context、已发表audit、18例和完整顺序/previous/head链，不把首次观察当作过去来源证明。其余unit没有预填hash也不免除链核对。

**R1严格558个载荷**：

| 集合 | 数量与唯一来源 | 可保留内容 |
|---|---|---|
| checkpoint | 上表固定12模型；对应selection的checkpoint ref；对应root的 `artifacts/checkpoint/<ref.sha256>.safetensors` | 原字节12份，≤1MiB/份，10个F32 tensor/26433有限参数header与offset核对，不重存、不重选 |
| train label | 内嵌B3.4 index的精确role=train集合528：432个12×6×3、96个24×12×6；`b3-v1-data/artifacts/label/<case_id>/<artifact.sha256>.json` | 每例producer/audit两个受限视图，原F32/F64位值、指定字段与末窗；不留完整旧label/history。468/508/488重叠不新增原件 |
| uniform packet | reference固定18 unit的outcome ref；`b4-30-z-reflection-repair-v2/sentinel/reference/artifacts/outcome/<ref.sha256>.json`；18个具体case ID完整列于JSON | uniform成功、failure/fallback空、metrics=terminal；仅规定binary64 compliance及来源，不导出旧timing/candidate/密度/history，不作H选择oracle |

内嵌B3 index SHA `b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26`；W context SHA `0454eee24c1c72c051f10dce0162f0f41d5a5ade1fb3a4e5b42c9c82c9d11071`。
**当前12 selection实际名字及558 payload完整literal/声明bytes/SHA仍未取得**。
本批准若采用，即批准按上述唯一来源闭包延迟登记；不是“现在已有598个已知文件名”或任意读文件的许可。
两作者R0各自读取、独立核验并冻结558项完整literal、声明bytes/hash/context/role/pointer及metadata已观察元组后，才可stat/open任何R1载荷。
载荷实际四元组只在各自R1中首次观察，不能预先stat补表；成员缺失、重复、来源未闭合、超数/超限或mandatory未知即STOP，不能选其他模型/案例补齐。

每原件每作者最多一次完整有界读取，40+558=598，两作者合计最多1196；同一捕获缓冲做完整hash、临时parse和规定转录。
短读/失败不补读；shared、filing、release及将来消费者读取旧原件上限0。
每作者源读取≤884MiB（R0 32、checkpoint12、train768、uniform72MiB），两作者≤1768MiB；单label≤64MiB、uniform≤4MiB。
JSON `rejection_caps`列出所有文件/总量拒绝上限，不代表已测源大小或内存保证。

输出 `content/` 恰1071普通成员：registry1、checkpoint12、models1、NN-producer528、NN-audit528、scalars1。
`version_id=SHA256(canonical(content-manifest))`，manifest不含自身hash/version；source/local/backup物理四元组另记。
同hash换inode仍STOP；真实身份变化优先，身份未变的长度不一致保留read_size_consistency原因；两者都不重读。

## 5. 固定目标、租约与结果留存

沿用既有同一候选，不自动尝试新保管目录：

- parent：`/Users/keith1117/Library/Application Support/TopoLab-custody`
- generation：`/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-v2`
- 主内容：上述generation的 `/content`。
- 唯一独立inode备份：`/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-v2-independent-backup`；**直接包含1071成员，没有额外/content**。

这些路径本轮均未探测，存在性、owner/mode、local filesystem、空间、inode和实际lease均UNKNOWN。
采用既有内容验真模型：provider覆盖仍UNKNOWN，不承诺绝不同步/上传、外部应用不改写或持续可用；不再追求第三目录或全局同步控制证据。
已知owner声明只允许登记TopoLab工具写入此parent、仅列出的iCloud/OneDrive/TM/APFS机制继续作为声明保留，不能替代实际读取核验。

只有唯一T0后的setup≤300s可dirfd/nofollow逐级检查固定路径：私有parent不存在可0700创建；既存parent须属euid且0700，正常root所有系统祖先可接受；
Darwin fstatfs64须MNT_LOCAL/可写、可用≥2GiB，generation和backup都必须原先不存在。
setup实际创建generation、检查并预留backup，backup到shared才独占新建；新普通文件0600/single-link/O_EXCL/fsync。
任一不安全、已存在、越界或超时即STOP，不覆盖、改权限、更名、清理旧目标或换根。
正式namespace（主根/备份/本次公开fixture/helper/partial）合计≤2GiB、4096普通文件；主根evidence≤256MiB/512文件，单evidence≤16MiB。
backup逐文件独立inode；同设备可接受，不声称异设备灾难隔离。

“保管租约”是实际O_EXCL/no-follow协作锁及持有人、内容hash/四元组回执，**只约束登记的TopoLab参与者**。
writer结束后content冻结，独立者只读；锁保持到filing等最后登记reader真实返回，之后单独观察release。
未知cleanup/返回不能启动额外helper，也不能预写自己未来退出、release或PASS；失败generation保留私有隔离，不作可消费输入。

结果阶段另可仅为新metadata/log/有限归档创建以下固定留存目录；本轮不探测或创建，不可用作替代输入根：
`/Users/keith1117/Documents/TopoLab-data/p17-m2-source-acquisition-v1-results` 与
`/private/tmp/topolab-source-acquisition-v1-results-backup`。
每份≤2GiB/4096普通文件、单文件≤1GiB，显式NEW文件白名单、独立inode、无覆盖复用/搜索替代名，成稿后文件0444/目录0555。
只留新正式证据、软件检查日志、源码/test hash、实际CI/返回/保护及未提交改动保留回执；不整包checkout/venv/cache、不借归档读取旧原件。
必须保存的正式raw source/native/return/lease/cost证据丢失就不能接受；临时unit目录缺失单列披露，不伪造恢复。

## 6. 六角色启动条件和一次执行顺序

T0前必须同时满足：实际批准本草案；新作者/实际调用者及预算登记；第2节收尾和所有必要原始hash实际核对；
新授权冻结/独立预检完成；干净、locked、实际最新merged main且精确PR/main四CI PASS，保护规则不减；
解释器image SHA、`-I/orig_argv`、cwd、OS、lock/import origins及五个线程变量全部固定为1；
实际工具事件外层记录者就绪，六角色完整suffix/setup/协调/交接及两作者结果预算均可容纳。
**T0前只做元数据/新公开数据预检，不要求或伪填未来目标inode、原件身份、正式RSS/退出**。
唯一T0为就绪核查后的plan activation时间，紧接setup；git/gh/CI预检在T0前，不能塞进未画像payload。
setup后首dispatch须剩余≥4200s；setup绑定plan、authority、source-tree及真实锁，并由首次实际native public-check回传和独立核验。

| 顺序 | 一次角色 | FULL秒 | 原件读取上限/作者 | 派发前共同剩余秒 | 必须成立 |
|---:|---|---:|---:|---:|---|
| 1 | independent-public-check | 300 | 0 | 4200 | 新公开数据检验冻结实际入口、native全资源/退出及工具真实返回；通过前旧原件stat/read0 |
| 2 | exporter-r0 | 300 | 40 metadata | 3900 | 前驱完整PASS、lease有效；只登记载荷声明，不stat/open payload |
| 3 | independent-r0 | 300 | 独立40 metadata | 3600 | 自己的完整链/来源/成员核验；双方metadata bytes/SHA/元组一致，冻结558项literal registry |
| 4 | exporter-r1 | 1200 | 558 payload | 3300 | 独立R0接受，逐项一次读取并产1071受限成员，无科学计算 |
| 5 | independent-r1 | 1200 | 独立558 payload | 2100 | 独立源→新内容完整bytes/schema/IEEE/来源/元组比较及资源/费用/退出核验 |
| 6 | shared-closeout | 300 | 0 | 900 | NEW-only显式白名单备份，前序组/真实返回已证实；失败仅准冻结条件下的预付共享例外 |

每次用未完成完整suffix FULL＋协调240＋封存交接360检查剩余，不按上次跑得快削减。
各角色完整native链（controller/supervisor/sampler/helper/serializer及outer）RSS≤4294967296bytes，actual exits、cleanup、wall和工具返回齐全；公开峰值不能填正式缺口。
这是既有新M2经验资源标准，不是先验分配定理、旧I1/B准入或full-fit证明。

第一失败STOP_NO_RETRY，保留完整packet、原件ordinal/path/已有元组/bytes/hash/主错、次级错误、有效耗时和全额收费；后缀UNKNOWN_NOT_RUN。
仅当已有真实NEW前缀、所有启动组/返回已证实、窗口仍满足冻结要求时，可执行已经预付的唯一shared失败收尾；不恢复源后缀、不发证书、不退款。
没有前缀或cleanup未知就保留明确缺口，不为“补齐备份”再起helper。

## 7. 本次可一次审批的全新预算（当前全部未批准）

| 阶段 | 执行者 | 不同作者独立者 | 连续计时边界 |
|---|---:|---:|---|
| 授权冻结与启动准备 | 7200s/2h | 7200s/2h | 批准后各自新首个准备工具起，到共同T0或实际preformal STOP；包括最小测试兼容、失败/等待、五检查、独立预检、精确PR/main四CI及返回/留存；不访问原件或保管目标 |
| 正式采集 | 共同4500s/75min | 同一共同窗口 | 唯一T0起含setup，正式关闭或关闭失败最晚T0+4500；不得先开时钟等CI，不批准试跑部分前缀 |
| 结果/独立验收/发表 | 7200s/2h | 7200s/2h | 同一实际T_result立即起，至各自最后工具/消息实际返回；含失败报告、filing/release、每次commit前五检查、精确PR/main四CI、完整有限留存 |

每作者从新首工具到实际最后返回总上限 **18900s＝7200＋4500＋7200＝5h15m**，阶段交接间隙也计入；各阶段cap与整体cap同时约束。
未激活就STOP时formal FULL=0，但实际setup/准备成本仍保留，双方结果钟从真实preformal STOP立即起；不是等方便时再计时。
已激活时T_result为实际正式关闭或关闭失败STOP前沿，最迟T0+4500；等待、中断、晚发首工具均不能顺延。
上一轮独立意见只覆盖原固定源码与公开准备证据；新授权、测试兼容、启动预检及正式结果须在新预算内另行独立核验，不能套用旧意见或恢复旧作者的钟。后续CI与工具返回按实际发生的作者、时间和证据记录，不预写未来事实。

新增2h/2h不是重做适配器，也不是延长旧4h/3h：用于实际授权文件、不同作者元数据预检和正常发表。
静态已确认两处测试依赖“实际授权文件缺失”这一全局前提：
`tests/test_p17_m2_source_acquisition_control.py` 的 `test_formal_entry_denies_before_inspecting_any_scientific_path` 与
`test_formal_plan_metadata_uses_frozen_original_contract_without_touching_declared_paths`（显式assert None）。
加载器在正式文件存在时会读得raw，因此这个前提与未来发表状态不兼容；**尚未复现未来CI失败，本轮不修测试**。
新授权只准以新公开软件副本先补presence/absence回归，再最小隔离这两处fixture；保留无授权拒绝门和真实授权内容校验。需要生产修复/其他合同变更即STOP报告，不扩展成另一轮准备链。

预算依据：上一轮最终本机pytest1188.96s＋PR quality1898.91s＋main quality1639.92s＝4727.79s（78m47.79s），
只是测试耗时，未含其余job排队/检查/审查/留存/发表；2h留下2472.21s处理这些工作。
这使旧独立结果1h提案不足，也使新2h必须严格止损；没有必能完成的承诺。新预算不得追溯覆盖旧失败或超时。

六角色FULL固定300/300/300/1200/1200/300＝3600；setup300＋协调240＋交接360＝900，合计4500。
shared300首次派发前预付一次，shared派发不重复记；其他角色派发前各记FULL。失败、早退或shared未能执行均不退款。
接受须 `max(完整outer wall+10,独立核内部最低费)≤FULL`；失败/超窗费用保留
`max(FULL,ceil(有效whole-wall+10),ceil(已知内部最低费))`，缺测UNKNOWN_NOT_ZERO。
FULL3600只在共同正式账记一次，不再给每作者各加3600；结果filing180也不另加到7200之外。

结果最多一次filing：FULL180/native timeout160，派发时双方剩余≥4860＝180＋release180＋发表/返回reserve4500。
真实filing最后返回后最多一次release元数据动作：whole wall+10≤180、native timeout160、双方剩余≥4680；
只读新lease/plan/返回metadata，原件0/科学消费0，不是第七个正式角色、不另增FULL，按实际wall+10与内部最低费记录（未知保留）。
实际返回由外层核验，不能helper预写自己的退出。4860/4680/4500是冻结门槛，不放宽；
最新4727.79s的tests-only已超过4500 reserve，因此必须在正式关闭后及时filing/release，并在实际余下窗口内保守规划完整发表。
若队列/失败使完整发表不可容纳则STOP并保留未完成项，不能延长、转移预算或假称发表完成。
货币/CI/主机费用UNKNOWN_NOT_ZERO；不授权新安装、购买或付费服务承诺。

## 8. 剩余阻塞、验收和停止点

| 分类 | 当前事实 | 最小解除条件 |
|---|---|---|
| 已确认 | 上一轮已封存，源/目标/正式/结果新许可未批准；实际授权文件不存在 | 明确审批本草案，按新预算冻结并正常发表实际授权及新作者预检；不重开旧额度 |
| 已确认静态前提／运行待验证 | 上述两测试依赖实际文件缺失；其未来CI影响未复现 | 获新授权后仅以新公开文件先回归、最小fixture兼容；全检查/CI实际通过前不能T0 |
| 待setup验证 | 目标存在性/安全/locality/容量/lease未知 | 唯一获准T0的setup300；失败就停，不换目录 |
| 待R0验证 | 实际12 selection、558项literal/声明与完整来源链未知 | 两作者获准R0独立完整读取并冻结；不提前读取载荷或猜值 |
| 待真实采集验证 | 原件完整性/身份稳定、实际RSS/退出/wall/费用、1071成员/backup/filing/release未观察 | 每个角色一次实际证据＋不同作者独立验收；公开PASS不替代 |
| 下游仍关闭 | P/17未修复、B/C未批准、历史all-paid超限/full-fit缺口未解除 | 本轮输入接受后停止，再单独审批B/C；不声称科学进度增加 |

最终接受必须同时具备：完整来源/字段/IEEE与两端元组、1071成员及version manifest、独立inode备份、
六角色资源/费用/窗口/真实返回、实际filing/release、不可变双份有限证据、结果报告及精确PR/main四CI、两作者实际返回。
否则明确STOP或UNKNOWN，不能用serialized PASS、public证书或哈希字符串替代独立事实。
收尾外部JSON绑定最终main/tree、CI、plan/authority/preflight/version、全部失败/收费/租约及实际返回；
不把未来ack或自己的未来退出写成事实，也不自动再做一个after-CI提交循环。

历史第12次故障归因于iCloud/OneDrive、当前源必定完整、目标绝不同步、预算一定足够，以及“上述测试前提是唯一剩余缺陷”都仍是未经验证的假设。
本轮只完成本草案；未读旧原件、未探测目标、未委派新作者、未跑正式角色/B/C、未改源码/测试、未重开额度。

## 9. 可直接采用的审批文字

> 批准《P/17正式采集授权草案v1》及其JSON（SHA256 `401c32618ef6fb964d0efc425dc2f792ce92baf7a7e483d8bdbafa1c08906786`），绑定第2节两份收尾记录。
> 任命/root为执行者，授权新委派/root/formal_acquisition_independent_v1作不同作者独立者。
> 批准全新的授权冻结/启动准备各2h、共同正式窗口4500s（六FULL合计3600s）、结果阶段各7200s及其中唯一filing FULL180；从各自新首工具连续计时、总上限各18900s，失败/等待/检查/PR-main CI/归档/真实返回均计入。
> 按本草案精确源闭包批准一次完整有界读取和临时解析，以及唯一固定目标的setup/写入/独立备份和新结果留存；仅在全部门槛满足后一次进入六角色，独立R0接受前载荷stat/read为0。
> 同意授权发表前仅对第7节明确的测试缺失前提先回归再作最小fixture隔离，生产规则保持；若需其他生产修复则停止报告。
> 保留内容验真模型的provider UNKNOWN、全部身份/短读/STOP/窗口/计费/4GiB检查和未提交改动；不改全局同步、不读旧backup/封存内容、不重开旧额度、不运行B/C或科学计算。完成或首次STOP后有限结果收尾并停止，无自动后继。

只批准“75分钟正式/结果预算”而未批准新授权冻结/启动准备，不足以进行前置发表或委派；保持preformal STOP。
本草案本身不构成以上批准，实际审批后必须记录可追溯的owner消息引用。
