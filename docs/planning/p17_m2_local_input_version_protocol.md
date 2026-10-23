# P/17 — 可追溯的非同步本地输入版本：新保管模型及准备协议

日期：2026-10-23。评审基线：main `4d1d4a07986827d4d16e50a1b3819ee2da046241`。
**CUSTODY_MODEL_ADOPTED / PREPARATION_ONLY_AUTHORIZED。** 所有者2026-10-23明确批准新保管模型，
以及执行者4h、不同作者独立者3h的连续准备预算，包括新公开回归、最小实现、目标证据和正常PR/main CI。
本协议及[JSON](p17_m2_local_input_version_protocol.json)记录真实批准范围；
旧原件 stat/read/copy、六角色激活、结果预算及科学B/C仍未授权，旧额度不重开。
本轮目标证据核验仅一次≤600s，纳入准备预算。目标原件根和generation均不由软件准备创建。
原草案的字节身份留在JSON中，旧冻结合同/报告保留不变。

## 1. 评审结论及需要单独采用的改变

方案可作为下一条有界路线候选；实际采集可行性、目标路径保管及运行资源均未验证。
推荐交付“12个原样 checkpoint + 既有受限视图 + 来源/验收证据”，不交付旧目录镜像。
原合同只允许旧标签/packet 完整字节用于临时 hash/解析；其完整原件、完整 history、
位移/反力和非白名单内容不得写入新目录、备份、日志或错误转储。

| 项目 | 本轮已采用的新规则 | 对旧合同的影响 |
|---|---|---|
| 来源保管 | 以固定锚点、闭合引用链、两作者完整来源比较及受控本地版本为依据；不要求原件云目录整个区间已暂停 | 这是已明确采用的前瞻保管模型变更；不得调用旧 R-STABLE/R-CUSTODY 身份实施 |
| 原件身份 | 每次读取仍须 declared/before/after/closing 四元组完全相等；两作者对同一原件的观测四元组也须相等 | 不把 hash 相同当成身份变化的豁免；任一变化仍 STOP |
| 一致性主张 | 所有被选文件属于同一冻结的引用/上下文闭包，并分别符合其预期 hash 和语义字段 | 不声称所有原目录的同一时刻原子快照、全区间无写入或不可篡改历史 |
| 后续输入 | 后续另获准的实验只消费已接受本地版本的指定 role view | 本地文件的 inode 不冒充原件 inode；原件、输出、备份各有独立身份记录 |
| 原件位置及状态 | 原位置保留，只读打开；不移动、改名、chmod/chflags、快照、硬链接、clonefile 或递归复制 | 所有旧失败、成本、UNKNOWN、封存及关闭配额保持原样 |

此路线仍可能在首次采集时遇到真实身份变化并 STOP；它不保证六角色一定通过，
也不把旧第12次失败归因于云盘或已修复的软件缺陷。

## 2. 新身份、批准层次与进入条件

新执行身份：`topolab.v2.p17-m2-local-input-version.v1`，简称 R-LOCAL/v1。
schema：`topolab.v2.m2-local-input-contract.v1`。
独立逻辑角色：`p17-m2-local-input-version-v1/executor` 与
`p17-m2-local-input-version-v1/independent`；准备执行者为`/root`（委派生产工具作者`/root/local_input_binding`），
独立作者为`/root/local_input_independent`；不同作者先冻结预期、后NONBLIND复核。
这不任命未来六角色或授予其执行权。
独立者必须不同于生产工具作者/执行者，先冻结自己的期望和比较算法，再做 NONBLIND 交叉复核。

批准分层：①新保管模型=true；②软件实现/公开检查及目标证据准备=true；
③精确旧元数据/原件访问与临时解析例外=false；④六角色共同激活=false；
B/C及旧额度恢复=false。未来“继续”不能补齐缺失批准。正式入口不接受草案schema。
本轮新增的本地内容写入/manifest和独立核对接口是准备能力；实际六角色新编排/
完整原始资源返回绑定尚未实现时，必须明确报告`FORMAL_LAUNCH_BINDING_INCOMPLETE`，
不得由结构校验、旧控制器常量替换或自报PASS宣布`SOFTWARE_READY`。
content-manifest绑定新批准协议实际SHA，身份不代替执行授权。

进入正式共同窗口前必须具备：新批准记录和有限预算；已任命且就绪的两作者；
实际 source/tree/lock、解释器、原始 argv、cwd、线程环境、工具/helpers、角色命令及本合同
MD/JSON 字节 hash；所有字段冻结在新 launch plan。实现须先通过既有五项完整检查及
精确合并 main 的四项 CI。普通软件 CI 不代替本轮独立 public 角色或科学 B 预检。
不得改旧协议 actual_admission、删除旧 STOP 或给旧 --r-stable 换路径。

R0 所允许的有限首次登记字段不是虚构的启动前事实：实际558个 payload 路径/声明
大小/hash 及两份 reference metadata 的首次观察 hash，仅可在获准 R0 中获得。
它们必须在独立 R0 接受后、任何 R1 原件 stat/open 前全部闭合；未闭合即 STOP。

## 3. 精确来源及白名单

只继承 Git 内
[内容合同](p17_m2_input_export_preparation_proposal.json) 的内容规则，原始字节 SHA256：
`f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad`。
继承 /checkpoints、/NN、/scalars、/R0、/R1 的字段/格式/位值/来源规则及
/byte_caps_proposed；其中 /R0/authorization_now、/R1/authorization_now 等旧授权字段
一律屏蔽，不能因读取内容子树而成为执行许可。旧身份、输出根、时钟/预算和全区间保管要求不继承。
正文、JSON 或被继承规则存在实质冲突时拒绝执行，不能让实现者事后选择有利解释。

原件根的拟议 literal 位置为 `/Users/keith1117/Documents/TopoLab-data`，未作新 stat。
仅限 b3-v1-fits、b4-5-weighted-terminal/fit、b3-v1-data、
b4-30-z-reflection-repair-v2 的既定有限引用。

| 集合 | 数量及内容 |
|---|---|
| R0 | 恰好40个 metadata：7个 literal bootstrap、3个 W unit、18个 reference unit、12个 selection；只沿合同规定的引用派生，不扫描/枚举目录，不 stat/open payload |
| checkpoint | C/P/W/S ×17/29/43，恰好12个；固定 epoch 见 JSON；P/17=123，不重选、不重存、不用 A 替代 W |
| train label | 恰好528个唯一 train case，432个12×6×3、96个24×12×6；重叠训练成员视图不增加原件 |
| uniform packet | 原合同固定18例的成功 uniform 原 attempt，仅转录指定标量及来源，不导出旧 timing 或作为 H 选择 oracle |

五个预发表 bootstrap hash、嵌入 B3 index hash、固定 context/unit 链、固定 selection/
epoch、train 成员和18例闭包必须一致。两份 reference progress/summary 仅按旧内容合同
明确允许的首次登记范围接受“当前观察 hash”，须标明该类别及其来源声明，经独立者核对；
不得补造过去未发表的 hash，也不得因 origin UNKNOWN 换面板或读旧备份。

每个原件只允许生产者、独立者各一次完整有界读取；每个作者 R0=40、R1=558，
全片最多1196次原件内容读取。R1 不重读 R0 原件。共享收尾、filing 和后续消费者不读原件。
同一缓冲完成 hash/解析/转录；不再开一次文件补 hash、修复短读、恢复失败或重建证据。

## 4. 一致采集与来源证据

1. R0 从预登记 bootstrap 开始，独立验证 canonical JSON、context、闭合 unit 链、head、
   固定选择/成员，派生完整 source_registry。未知来源、缺失引用、额外源、别名/重复项或
   不一致均 STOP。新算出的 hash 本身不是来源证明。
2. 独立 R0 自己读完40个原件，不导入生产注册器/解析校验器作为 oracle；比较完整注册表、
   来源类别及各源的实际 bytes/SHA/四元组。接受的 registry 字节/hash 和558项声明冻结后
   才允许 R1。之后旧 metadata 即使变化，也不重新发现新版本；本次只主张已接受的固定闭包。
3. 每个 R1 原件在打开前核对 literal/nofollow/regular/type、声明大小、单文件和累计 cap。
   保留 declared/before/after/closing 的 dev、ino、size、mtime_ns。原件内容/mtime 不写；
   atime 可能由文件系统更新，不声称绝对零元数据写入。
4. before/after 身份变化先按原身份原因 STOP；身份未变但总返回长度不等于描述符大小，
   按独立的 read_size_consistency 原因 STOP。短读不得补读。关闭路径及祖先遍历检查、
   预期原件 SHA、schema、来源、字段、IEEE 和计数均继续适用。
5. 逐个处理原件，仅同时保留一个原 payload 的 raw/parsed 工作集；完成受限转录即释放
   非白名单字段。checkpoint 从这一缓冲写新普通文件；标签和 packet 只写限定视图。
   禁止旧 loader、模型实例化、推理、拟合、FEM、filter/projection 或重新计算标签/旧结果。
6. 每个源有 attempt ordinal、path、来源声明、预期/实际 bytes/SHA、可用四元组、阶段、
   changed_fields、原始主异常及 secondary recording_error；保留完整失败 packet/已完成前缀。
   禁止输出 raw JSON/history、异常 locals 或原件片段；未观察字段为 UNKNOWN/null，不写0。

## 5. 本地根、内容身份与发布

拟议新根 `/Users/Shared/TopoLab-input-versions/p17-m2-local-input-version-v1`，
拟议备份为其 `-independent-backup` 兄弟目录。两者在批准前未探测、未创建；本轮只核对目标父路径及新公开sibling fixture，
实际generation/备份仍不创建。新路径写权限通过正常工具权限审查。
正式计划只准一个 literal 新根/备份，不覆盖、不换名重试、不迁移到其他根继续。

本轮已获准的软件准备中，对目标父路径及新公开 sibling fixture 作一次≤600s的
有界验证，该时间包含在准备预算内：物理路径/无 symlink、local filesystem、创建者/
权限和独占写入、provider/备份覆盖证据以及责任人的完整目标 writer 声明。
必须有实际观测及可接受的明确依据，不能仅由“不在 Documents”、空进程列表、目录
pause mask=0、缺配置字段或 File Provider flag 单项阴性推断非同步。无证据即
NO_LOCAL_ROOT_ADMISSION，旧原件读取0，正式角色0；不追加暂停 API 探针。
此处只评估新目标，不重新调查旧 Documents 映射或改变全局同步设置。

共同激活前接受可实施的目标保管计划；激活后 setup300内实际取得新根独占 writer lease、
创建私有空 generation（新目录0700、新文件0600）、冻结计划/控制记录。lease 只声明本地目标写入权，不假称原云目录
已暂停。生产者退出后 content 不再写；独立者只读；共享者只写 evidence/closure。
目标保管跨正式关闭持续到结果阶段最后已登记 reader（包括 filing helper）真实退出。
共享只记录 formal_close 和 sealed handoff，不提前声称目标已释放；真实 lease release
由其后可信外层观察/保管人确认，在结果阶段记录。release 不解除已接受 content 的不变约定，
后续消费仍需登记目标保管。不能要求未来 release 先于激活或 helper 预写自己的退出/release。

`content/` 恰好1071个普通文件：source_registry.json 1、checkpoint 12、models.json 1、
NN producer 528、NN audit 528、uniform-scalars.json 1。checkpoint 字节同源；其余采用既有
受限 schema、字段 pointer、float32/float64 dtype/shape/长度/小端 IEEE digest，
每例最多11个获准原末窗状态。无完整旧标签/packet/history/raw metadata 的副本。

每次写入只建新文件，exclusive create、完整写/flush/fsync，并记录实际输出四元组。
部分 generation 留在私有未接受状态。无需把目录 rename 到另一路径来“发布”；计划中的
literal 路径始终不变。所有内容写入完成后，记录表固定，consumer 只能在最终接受后读取。

content-manifest 包含 schema、冻结合同 SHA、内容范围 SHA、registry SHA、固定排序的
每个成员 path/type/bytes/SHA 及拟议 role-view 表。
`version_id = SHA256(canonical(content-manifest))`；canonical 为项目现有 JSON 规则：
ASCII（非ASCII字符使用JSON转义）、sort_keys、紧凑分隔、ensure_ascii=True、allow_nan=False、末尾一个 LF。
manifest 不含自身 hash/version_id，避免自引用。实际原件/本地/备份的四元组、作者、
时间、运行记录和资源结果另存 evidence，不用于把不同物理文件伪装成同一 inode。
content identity 不自动赋予路径迁移或新消费者访问权限。

## 6. 独立验收、有限证据终点和消费者

独立 R1 必须按自己的实现读全部558个原件，完整比较12份字节副本及1056份视图/
18条标量；不抽样，不以生产者 PASS、manifest 或自报 hash 代替来源比较。
生产者/独立者对每个原件的四元组及实际 bytes/SHA 全量一致；实际原件与本地输出
之间比较规定字节/字段/位值和来源 pointer，不比较其物理 inode 相等。
所有新 content 文件也须 independently 读、hash、before/after/closing 核验，
并匹配生产端记录的新文件身份；不允许同 hash 的路径替换。

同时核对完整集合、schema、逻辑角色/尺度、epoch、tensor header/26433个有限 F32 参数、
两视图隔离和原始 IEEE 值；不重新做科学/完整旧轨迹验收。验证 content-manifest/hash、
新根保管、全部角色 FULL/时钟/4GiB/RSS/实际退出/清理、完整错误前缀及 NEW-only 备份。
备份只读已登记新产物，不第三次读原件；无隐式 include 或原目录快照。
只允许对新受控根/备份作受4096文件上限约束的清单，以拒绝额外内容；发现项不得自动
纳入白名单或扩展备份。旧根不枚举。备份写独立普通文件，不硬链接主根；“独立”指不同
作者逐成员核对的新目录，不声称异设备或灾难隔离，不授权额外存储购买。

状态次序为 DRAFT → SOFTWARE_READY → ARMED → ACTIVATED → R0_ACCEPTED →
CONTENT_VERIFIED_PENDING_RESOURCE_EXIT → FORMAL_CLOSED → LOCAL_INPUT_VERSION_ACCEPTED。
这是接受流程，不给出执行许可。任一失败进入 STOP_NO_RETRY，未运行后缀为 UNKNOWN_NOT_RUN。

共享角色实际最后返回由可信工具外层观察；它不能在自身退出前证明自己的完整退出。
在结果阶段允许一个新绑定、最多一次的 filing helper，FULL180/native timeout160，
仅接收真实共享返回 packet、核对新备份并记录有限证据终点；不读原件、不改 content，
不提前释放目标保管。只有真实新证据前缀存在、全部已启动组确认退出、前序工具已返回且
结果时限可覆盖 FULL180 时才可启动；清理 UNKNOWN 时不能为了备份另起 helper。
helper 同样需要4GiB完整包络、完整外层wall+10<=180、实际退出和清理证据，不能自报通过。
它的实际返回/退出仍由外层观察，不能以它预写的 READY/PASS 自证。
证据清单明确排除自身/未来 acknowledgment 的递归自清单；出版写入不伪装为另一正式角色。

最终可消费证书必须共同绑定：version_id、合同/源码/tree、独立内容比较报告、六角色
实际返回与完整资源/收费结果、共享封存交接、最后 reader 后的目标 release、新备份及
filing helper 的真实外层返回。
可信原始返回记录在结果发表时保存为不可变外部证据并以 hash/来源类别绑定；当前草案不
预设任何实际成功记录。自写 READY 文件单独无效；只有实际证据闭合并发表接受记录后，
才可声称 LOCAL_INPUT_VERSION_ACCEPTED。任何 content 改动、缺失最终返回或 filing 失败
都不准提升状态，保留隔离产物，不补跑源角色。

R-LOCAL 独立者本轮可读全部新 content 以比较。未来科学 producer 只可获准 weights/
models/NN producer 视图；NN audit/sensitivity/末窗只给另行登记的独立科学角色。
uniform 标量只给另获准的兼容核对角色，不进入 H 选择。B/C批准及实际角色调用表仍为0/
UNKNOWN_UNREGISTERED。后续读取须核对接受证书、计划 literal 本地根、成员 whitelist、
bytes/SHA/四元组及 role view；不得 fallback 到原根、旧 index、任意备份或未接受 generation。

## 7. 字节、磁盘、资源与拒绝上限

所有旧内容 cap 保留；MiB=1048576 bytes，不截断、不扩 cap、不换源。

| 类别 | 单文件上限 | 每作者原件累计/输出上限 |
|---|---:|---:|
| R0 index / 其余 literal / unit / selection | 16MiB / 1MiB / 32KiB / 256KiB | 恰好40个，总32MiB |
| checkpoint | 1MiB | 12MiB |
| label 原件 | 64MiB | 768MiB |
| uniform 原件 | 4MiB | 72MiB |
| NN producer / audit 输出 | 128KiB / 2MiB | 32MiB / 256MiB |
| models / registry / scalar 输出 | 1MiB / 8MiB / 64KiB | 各1份 |
| content-manifest | 2MiB | 1份 |
| evidence（不含 content） | 单个记录文件16MiB | 主根合计256MiB、最多512文件 |

每作者最多884MiB原件字节；两作者合计拒绝上限1768MiB，不是实际读量。
新正式 namespace（主根+唯一备份+public fixtures+helpers+临时文件）合计≤2GiB、
≤4096个普通文件；每次新增前核对累计，所有 partial 也计入。软件 checkout/cache 不混入
该 namespace；其普通工作成本另计，不声称这个 cap 约束全宿主磁盘。
这些是新增拒绝上限，未测实际文件大小、磁盘吞吐或峰值，不能证明预算内必定完成。

每个完整命名角色链保留新 M2 的4GiB=4294967296 bytes native RSS/完整退出实证口径，
包括规定的 controller/supervisor/sampler/helper 重叠包络、实际单位及区间。
独立 public 完整 PASS 在任何旧源 stat/read 前；每个真实源角色仍需自己的资源证据。
未知/缺测、超限、OOM、越域、退出或清理未确认均 STOP；不要求新内核/事前分配证明，
也不把软件峰值或 R public 验收当作科学 B 或历史 full-fit 的证明。

## 8. 新准备预算及未授权的正式/结果预算

| 阶段 | 执行者上限 | 独立者上限 | 计时起止 |
|---|---:|---:|---|
| 准备/实现/目标路径证据/公开回归/PR及main CI | 14400s（4h） | 10800s（3h） | 本轮各自首个工具动作至就绪或 STOP 的实际最后返回；连续计时，包含失败、等待、中断及CI，不另加出版额度 |
| 正式采集/验收 | 同一4500s共同窗口 | 同一窗口 | 完成软件/CI、双方就绪且新批准齐备后，唯一 T0 激活；不从 CI 前启动 |
| 结果审查/发表 | 7200s（2h） | 3600s（1h） | 同一 T_result 起至各自实际最后返回；含拟议 filing180，不额外增加180s |

本轮仅准备上限已授予；正式4500s及结果2h/1h仍是未授予的提案。各阶段不继承任何 R/F/A/D/B 的工时、窗口、未用余额或审查者。
准备中的目标验证≤600s已包含其中。双方必须在各自准备 cap 内共同就绪；超时零源角色
STOP，不为凑齐就绪暂停/重开时钟。阶段转换及各自起止必须预登记并按实际返回保留。
各作者视图/工具外层/CI时间有重叠时，不把它们算成额外额度或重复的同一费用。
T_result 为未激活时的实际 preformal STOP；若已激活，则为实际正式关闭/关闭失败的 STOP
前沿，最迟 T0+4500。结果 deadline 分别是 T_result+7200/+3600，不能因首次结果工具
较晚、等待或中断而后移。结果阶段不能补跑正式角色或把超窗补成 PASS。

| 顺序 | 唯一一次角色 | FULL |
|---:|---|---:|
|1|independent-public-check|300s|
|2|exporter-r0|300s|
|3|independent-r0|300s|
|4|exporter-r1|1200s|
|5|independent-r1|1200s|
|6|shared-closeout（NEW-only）|300s|

FULL合计3600s；独立不重叠的 setup/lease300、角色间协调总240、最后保留/封存交接360，
合计4500s。首发必须剩余≥4200s；每次后续启动须覆盖剩余完整序列及协调/收尾。
必须完整准备六角色，不批准只启动一个前缀试试。共享300在首次实际 dispatch 时预记一次，
即使后续失败/不能启动共享也不退；其他 FULL 在各自启动时记全额，不按实跑短时退款。
零 dispatch 不记六角色 FULL，但实际 setup/准备成本仍保留，不能计0或移到旧额度。

角色接受保留 `max(实际完整外层wall+10s, 独立核定内部最低收费)<=FULL`，
全部监督/序列化/工具间隙/失败/最后实际返回在包络内。超窗后仍保留有效 wall 与全额收费，
不能补字段变 PASS。线上最外层输出32768 bytes上限；完整记录存新证据目录并绑定其 hash，
截断、无效JSON或缺完整返回均拒绝。共享仅在真实前缀且相关进程组确认退出时可启动。

结果 helper FULL180仅在获准且实际启动时记入结果阶段；不占 B/C 配额。
author阶段上限不等于货币支出；已有电力/订阅/CI费用 UNKNOWN_NOT_ZERO，无新购买。
已知旧 paid12721.16417100014444982>7200、D1 FULL60及所有额外历史费用仍保留；
本次输入版本即使成功也不能通过原 all-paid 条件或产生新科学额度。

## 9. 正式冻结前必需的公开软件证据

只用新公开 fixtures，通过实际将冻结的命令/解释器/-I/原始argv/cwd/权限与模块来源验证：
完整40/558和1071输出集合及两种schema/IEEE；正确采集/独立原件比较；目录/成员越域、
错误source链/首次观察类别、hash/字节/tuple变化、0/部分短读、缺失行、同hash路径替换、
篡改受限视图及权重、角色越权/原目录fallback、部分写入文件/共享异常/二次记录错误、
超窗仍完整收费、关闭旧身份拒绝、新租约/新目标失败、未观察共享/helper退出不接受版本。
生产入口的授权/身份/argv/拒绝路径须用实际命令验证；正向完整矩阵仅走独立 public-only
入口或既有公开 register/export interface，以新 fixture 合同为输入。公开 fixture 身份不得
被正式入口接受，不增加 --skip-guards 或用旧白名单实际内容补齐公开测试。
边界尺寸/向量/末窗及被允许临时解析的最大对象须在公开准备中覆盖；不为原件失败现场改工具。
独立算法先于生产补丁完成期望；测试不调用生产 checker 作为比较 oracle。
软件提交前既有五项检查和精确PR/main四项CI全部通过；正式冻结后修改源码、合同、
输入域或cap即 STOP，不边修边续跑。失败软件/CI尝试及时间也保留。

## 10. 准备阶段真实时钟、状态和退出

执行者首个工具为2026-10-23T07:48:15Z，deadline11:48:15Z；
独立者首个工具07:49:32.069279Z，deadline10:49:32.069279Z。连续计时包含
失败、等待、中断、CI、审查及最后实际返回；双方须在各自时限内共同完成准备。
不另外启动结果预算、不自动延长或以首个结果工具重置时钟。
独立预期冻结07:50:54.538216Z，先于生产补丁接触；实际代码/测试/目标事实见
[准备报告](../validation/p17_m2_local_input_version_preparation.md)。

准备中缺失目标非同步/完整保管证据即`NO_LOCAL_ROOT_ADMISSION`；未闭合六角色
实际编排/资源/退出绑定即`FORMAL_LAUNCH_BINDING_INCOMPLETE`。保留可复现的
公开内容能力及具体缺口，不自动另起调查/guard链或读取原件填空。
本轮旧源stat/read/copy=0、正式角色=0、B/C=0，均不得因模型采用变为许可。
实际来源、尺寸和真实采集成功率仍UNKNOWN，不以新公开fixtures补造旧故障归因。
草案编写、旧软件及本轮全部成本保留，未完整计量为UNKNOWN_NOT_ZERO；
新准备预算不是历史成本豁免。下一步须依据实际报告作有限决定，无自动后继。
保留P/17 unrepaired、uniform默认、科学暂停、full-v2开放、4GiB/独立预检、
full-fit PENDING、B3两环境/两尺度、旧失败/成本/UNKNOWN/额度/封存及v2 Gate顺序。

依据：[来源准入旧协议](p17_m2_source_custody_export_protocol.md)、
[独立性/资源与收费模板](p17_m2_source_stability_export_protocol.md)、
[读取修复](../validation/p17_m2_source_read_completeness.md)、
[有效开发方法](TopoLab_v2_delivery_reassessment.md#4-effective-development-methods)、
[v2顺序](TopoLab_v2_development_roadmap.md#6-current-sequence-after-the-delivery-reassessment)。
