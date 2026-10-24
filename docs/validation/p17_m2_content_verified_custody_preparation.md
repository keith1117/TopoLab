# P/17 — 内容验真保管：公开软件准备

基线 main：`c9502cbe8302ffa8e41939347081e4c96599e019`。
[采用协议](../planning/p17_m2_content_verified_custody_protocol.md)及
[授权/时钟](../planning/p17_m2_content_verified_custody_protocol.json)记录直接批准的新6h/4h切片。
原[草案](../planning/p17_m2_content_verified_custody_proposal.md)与JSON保留批准时的字节；
协议明确替代草案的历史not-granted字段，旧协议、报告、停止和额度不改。

## 目的与实际范围

本轮准备可独立验收的固定输入版本及同缓冲消费能力，解除“必须证明目标绝不参与同步”
这一新路线的前提。它不修复数值算法，也不把旧故障归因于云同步。Provider覆盖仍UNKNOWN。
新模型不保证从未同步/上传、外部程序全期不写或持续可用；发生变化时按身份/内容规则STOP。
租约只协调登记的TopoLab写入者/读取者，并跨越实际工具返回；它不能锁住其他应用。

实际操作仅限本轮新公开数据、版本化软件及正常回归/发表。拟议Application Support目标
未stat/probe/create，旧科学原件未stat/read/copy/解析，正式六角色0/6，B/C0，旧配额重开0。
固定P/17未修复、uniform默认、full v2开放、原质量/Gate次序、4GiB实证/独立预检、
known-paid12721.16417100014444982>7200及full-fit PENDING4GiB全部保留。

## 三个已批准接口与独立性

| 接口 | 实现及实际检查 | 不证明的事项 |
|---|---|---|
| S1 | `VerifiedInput`仅接受进程内独立证书及实际opaque reader lease；角色白名单、普通单link/0600、root与成员四元组、完整长度/hash检查后，解码器只收到这一次读取的bytes；解码前后再核租约 | 正式源授权、科学接受、永不改变的文件系统 |
| S2 | 新public CLI冻结新身份、完整source-tree/lock/实际Python image/argv/cwd/OS/线程环境；实际native六段编排、失败前缀/共享收尾、计费、有限filing、实际返回后的租约交接 | 正式激活或旧额度重试 |
| S3 | 不同作者从原始native/profile/log/helper/外层工具返回重新比较源/本地/备份，核收费/窗口/最后reader；返回限定PUBLIC范围的进程内证书 | 序列化PASS有消费权限、fixture可代表旧科学输入 |

`/root/content_verified_independent`于04:51:53.956972Z先冻结独立期望/算法，
`expectations.md` SHA256 `67dc5d69ba5e8f4f51fcf638924135d01c65f395d365162ebea0a16c7c30a60f`。
随后双方NONBLIND交叉审查；不声称盲审。独立者拥有新的验收模块及其测试，执行者拥有
编排、fixture和消费模块及其测试。复用的是TopoLab既有独立比较/字段转录/native算法，
不以生产checker作为独立oracle；旧helper身份在适配证据中明确披露，不重标旧执行为新角色。

## 实现约束

- 新actor：`topolab.v2.p17-m2-content-verified-input.v1`，仅PUBLIC软件范围。
  未批准的formal入口在解析/探测路径之前拒绝。
- 图的实际内容为新40元数据、558源payload、1071本地成员，双作者分别完整比较。
  12 checkpoint、528训练case的两种受限视图、18uniform scalar转录均不执行模型/FEM。
- 独立R0接受前不能开始R1；前驱PASS重新从raw facts验算。直接payload不能绕过实际
  registered native parent/group。每个计划、attempt和输出独占新路径，不重试失败身份。
- 本地/备份root及文件四元组都冻结；同hash换inode、root替换、短读、symlink、权限或
  hardlink异常都STOP。hash不代替来源全量核对。S1不重开路径交给decoder。
- 实际外层record返回的pending/completion canonical摘要由可信工具观察者记录。
  completion同时绑定inner record/profile/log、每个helper profile及outer profile的摘要；
  S3从实际raw buffer重算。修改wire或替换另一次packet不能靠PASS被接受。
- 新临时namespace含partial文件计2GiB/4096普通文件，证据子集256MiB/512文件。
  新写入及采样前检查/保留失败尾部容量；超限STOP，不删除失败证据腾额度。
- 六段PUBLIC模拟保留300/300/300/1200/1200/300 FULL，共3600s；shared300在首派发前
  预记，dispatch不再重复收费，也不退款。filing FULL180在结果窗口内另行预记。
  metadata动作不创造formal额度，实际wall/native最低内账保留，未知成本不写0。
- 公共actor4500s，setup≤300、首派发剩余≥4200、协调≤240及sealed handoff预留保持。
  超窗先保留有效whole-wall及max(FULL,ceil(whole+10),ceil(inner minimum))，再STOP。
- native4GiB实证包含实际timer/wait4/controller/supervisor/serializer及sampler；未知RSS、
  退出或cleanup不能PASS。watchdog更短的公开fault只用于失败回归，FULL300仍付，不形成证书。
- 初始协调锁是实际O_EXCL/no-follow私有文件，内容及物理身份绑定。最后filing实际返回后
  才释放。新consumer再次取得opaque lease；消费结束只产生PENDING_ACTUAL_OUTER_RETURN，
  另一个ack进程重验实际退出/资源/原始stdout后才删锁；ack本身没有新的读取权。

## 已确认并修正的公开软件缺陷

| 已确认现象 | 行为RED→GREEN证据 | 最小修正 |
|---|---|---|
| 直接payload可跳过实际native启动 | S2-31/32 | 要求已登记active、native started实际parent/group/argv |
| 租约在读期间失效仍可能进入decoder | S1-06/07 | 解码前后核对opaque held lease |
| 消费失败后重建consumer可复用同capability | S1-11/12 | 在任何再次open前锁定该证书STOP，保留原异常及次错 |
| 非私有/多link成员可能被消费 | S1-08/09 | 四个身份阶段验证普通文件/euid/0600/单link |
| 新适配失败时源读取上下文没有终端落盘 | S2-34/35 | 保留原attempt/read table/facts/全部可用元组及次级记录错误 |
| 共享collector写失败丢失整个stdout packet | S2-40/41 | 返回完整STOP packet并记录collector/wire写失败；未知指针不造hash |
| 已知保管锁丢失仍会开始新公开IO | S2-51/52 | 复用原锁字节/四元组，在已有payload入口/返回处核对 |
| wire自报cleanup可错误清active | S2-53/54 | 独立核actual-return/原始退出/全部group cleanup后才清生命周期 |
| 证据namespace上限未执行 | S2-36/37 | 只扫描新root的no-follow计数/大小，写入和采样前拒绝 |
| 失败前缀被共享收尾的前驱检查挡住 | S2-42；修复后结果见最终检查日志 | 仅在非空实际前缀、完整返回和group_gone后允许已预记shared，不开放源suffix |
| shared备份proof写异常仅剩traceback | S2-47/48中错误分支通过 | 保留全部已复制成员、源facts、租约/账和次错，返回完整STOP |
| supervisor timeout存在第二次wait4风险 | S2-44/45公开fault及源码审查 | 复用一次性native poll/wait4统计，保存实际退出/已观察group清理 |

独立者还用变异回归确认：错误的实际completion摘要、改成0的shared预记、过早release、
仅替换root但保留成员inode、伪造PASS、缺失/不一致native证据均不能形成消费证书。
具体独立日志/审查结论随外部软件证据留存。所有失败仍保留，不重标为历史故障解释。

## 回归记录的准确含义

先补测试，再作最小实现；仅使用已批准S1/S2/S3接口。测试中的合成UTC/native事实明确属于
unit fixture，不能代替真正functions工具观察。独立的actual-public-run另存真实每次tool
request/result、Date.now端点、最终退出、pending/completion及native摘要。

日志文件名的RED/GREEN只是发起时标签，真实exit才是结果。保留以下非目标RED/失败：
S1-01缓存权限；S2-11曾用了未采用的内部接口后改为真实CLI；S2-14/15并发改源触发正确
SOURCE_FREEZE_STOP；S2-16标RED但实际通过；S2-22测试clock分辨率错误；S2-25依赖未完成；
S2-28 macOS launcher改写orig_argv；S2-30标签GREEN但filing字段校验失败；S2-33测试字段名错；
S2-46共享前驱误挡自身ACTIVE；S2-43新snapshot完整正向通过。
S2-43/48的prefix分支先暴露metadata默认40上限误用，后因unit事件0644被正确拒绝；
明确NEW-prefix分组后保留原R0上限，修正unit事件为0600，S2-50失败prefix通过。初次style问题及缓存权限失败也留存。
这些都计入原准备钟，不是正式重试。macOS以实际`sys.orig_argv[0]`解析得到的Python app image
冻结并启动，仍精确比较argv，不放宽为任意解释器。

## 边界尺寸与真实资源

公开图覆盖64MiB label、16MiB fits index、1MiB context、256KiB selection、200项selection
history、360项label history、1728单元/最近11项、32KiB journal unit、4MiB scalar原packet。
固定权重body为26433个float32（105732bytes），合法最大65536bytes header的checkpoint共
171276bytes；1MiB是文件拒绝上限，不虚构固定schema可合法填满1MiB。
额外padding仅在允许的原packet公开字段，不进入受限本地科学视图。新raw/native统计是这些
公开对象的实证，不填补历史或full-fit4GiB缺口，不实际分配4GiB做拒绝测试。


## 第一版冻结软件的真实公开执行

这是单独的functions工具观察，不是pytest合成事件。第一版runtime复制自当时冻结源码，
`actual-source-freeze.json`文件原始SHA256为
`11a96768d78fa40026d2d36424f6a33b7b4993818c5803a4f99afff7fc41b984`，
含18个源/合同/lock文件及基线/路径。它与`canonical(plan.source_tree)`的17项映射摘要
`6991f33a85239a44393b48d68b9cd62abc3bf1f6ff9f740974009e21a42c44b0`
是不同对象；lock另由runtime字段绑定。实际采用协议JSON SHA256为
`8ecc3716306cd2e49d7d5fd46f61eb43b4d2740861a702e5bc8745b9500e3381`。

正向plan `bad98921c367ac72a503fe0cf393308ae784f6959ae7ad3fdba88c943a60b6c1`：
六段PUBLIC native、filing、release、独立证书、1069成员同缓冲消费及实际返回后ack全部接受。
版本 `4e8d9fa95071a4160b23098cb7f8150840fc8bfa8562fb67cd8698f06444f2d3`。
六段实际first-tool→shared-last-return为125.94900012016296s，保守最大native RSS envelope
1369767936bytes＜4294967296。independent-r1的首工具返回running session，继续等待同一
进程至真实退出；原始exec/write_stdin trace与63.037999868392944s whole-wall全部保留，
未重新启动payload。新root最终3036普通文件/223524599bytes；lease与active都已清空。
`actual-positive-summary.json` SHA256为
`97d0a6d2767ad76f1e2423bb04130e767d4f4a7792f1c5cb8eb190c8f4d5f43d`。
这些资源/时间只属于公开图，不是正式源或full-fit证据。

独立新失败plan `faafce5d10346e0fa4c5d7df154427d1973420430e633034c890deabafb55a0a`：
仅新公开第一个bootstrap改成3bytes，exporter-r0按固定SHA拒绝；原path/ordinal、
declared/before/after/closing、returned_bytes=3、hash及完整失败表都保留。
后续源角色不启动，只做预付shared的NEW-only显式prefix48文件独立备份；shared仍STOP，
active已清，初始锁保留HELD隔离。filing/release及源suffix均UNKNOWN_NOT_RUN，
无INPUT_VERSION_ACCEPTED/消费证书。这是按停止规则保留隔离产物，镜像不是该输入的接受备份。
模拟第一角色300＋失败R0 FULL300＋首派发前shared预记300=900s全部保留，退款0；
不记入旧formal额度。`actual-failure-prefix-summary.json` SHA256为
`43ccc296e645cb7c5f0312b6802d4ce280bab4d93e01a9b72e15849a4b41e69c`。
正向/失败的额外prepare/bind/certify真实工具返回文件SHA为
`faa8ec8258d8aa6be24c49961964ede4cc72d6401c847ce590145f5aa4da9076`。

不同作者另从原始工具出口独立重放正向链：
`actual-public-independent-replay.json` SHA256
`bc770cabfae4ebdce92d95ae9e19cf837ad05f7526f0bbd13ca90a59f5f4ee0a`。
实际失败链重放 `actual-failed-prefix-independent-replay.json` SHA256
`7d93bc418c7668623860287e268c160a9f4c897de67e79835d12ce128a481787`，
48显式成员共130165bytes，两端逐字节/完整tuple及exact backup inventory再次匹配。
这些重放不只信执行者的PASS摘要。不同作者
`source-review-final.json` SHA256
`08f1f68aff244d8fab4dcbb84e0e81e9e868ae2c247b7d3c7c77b58b53891971`。

第一版S1/S2 focused22 passed（202.69s，外层205.489727916196s）；当时独立S3 54 passed
（114.45s）。后续同一切片最终复核发现下述超时边界阻塞；这些第一版证据保留原字节，
不冒充修正后最终源码的验证。独立审查保留首次freeze文件摘要与plan映射摘要混用的
断言失败，不当成代码行为RED。另有red23缓存权限、green24并发freeze、green25命令节点
名错、green35临时语法错误及撤回的red37规范假设（把生产160s裕度推断为新合同硬上限）；
均未冒充有效行为RED，失败及成本完整留存。54例对应精确S3源码
`aee8b79d91222e66a33ecdc73cceab65cb6f7b15ebbf01548ac3375af33b804d`；
第一版公开冻结runtime及原始证据没有改写；最终修正另用v2 runtime/公开root/观察命名空间。

## 最终复核：超时清理与失证据后的计费

源码复核确认同一生命周期边界的三处缺陷，均保留STOP：

- S2-RED-55：外层超时且`started.json`缺失时，已观察到的内层独立进程组未被清理。
  GREEN-56覆盖正常、缺失和损坏三种公开fixture；现在先按本次真实进程树观察登记后清理，
  无论namespace/sampler/started记录异常都在finally终止自己的外层launch。
- S2-RED-57：内层资源文件缺失时，`audit_saved`在S3计算前抛错，丢掉有效whole wall。
  GREEN-58保留实际外层span、FULL300及次级资源读取错误；缺失退出/资源保持UNKNOWN，
  active不清除，共享收尾不获准。
- 不同作者RED38：只有外层watchdog cleanup未知，其余证据完整时，S3仍可能判closed。
  最小校验要求外层、真实sampler和所有已观察独立进程组清理均已证实；UNKNOWN不能放行。
  watchdog额外sampler未纳入原完整RSS包络时，完整RSS仍UNKNOWN，不产生资源PASS。

首次完整pytest因上述已确认阻塞主动中断：1817 passed/1平台skip，exit2，pytest811.86s，
实际外层817.313088750001s。`LOCAL-PYTEST.log`及中断记录完整保留；这不是全量通过。
原连续准备钟不暂停、不重置。最终版本须使用独立v2软件冻结/新公开root重新观察，
完成完整五项检查及正常受保护发表才可闭合。

## v2软件冻结与新公开重放（后续仅bind持久化边界再修正）

最终18项源/合同/lock按新路径`actual-v2-frozen-runtime`冻结；
`actual-v2-source-freeze.json` SHA256
`673fc98ecd2f741f656e6fdef40041e28b7d0af857d4ee4a54d209ce38d01913`。
S2源码SHA256 `9796eb586af0ff44bdcbd1ba006023e5f7e27757f659f26dd92c81461915c1b9`；
S3源码SHA256 `94be807c78d3dfd5654a921646035b04d0ebdf13877ea585a2ec2d7b80480750f`。
所有v1 runtime、摘要、raw工具观察及独立回执保持原字节。

新公开正向root为`topolab-public-actual-v2-chain`，planSHA256
`4c926285a9b9075a9604d5664b0e13593a52f9a0e36707823073f1dfabf283f8`。
从首工具至共享最后返回105.05299997329712s，最大完整公开RSS包络1084243968bytes<4GiB。
六PUBLIC段、filing/release、证书、1069成员/40590471bytes同缓冲消费及实际返回后ack
全部独立核对，active及reader租约已释放。内容version仍为同一新公开图的
`4e8d9fa95071a4160b23098cb7f8150840fc8bfa8562fb67cd8698f06444f2d3`；
这不表示复用旧原件、旧formal身份或额度。
`actual-v2-positive-summary.json` SHA256
`5b130aaf8370553a3af1012dc3a76e4357cc3f915671f16e748e00a9ea45a572`；
其中顶层plan字段未填（null），真实plan由每段原始pending/receipt及独立回执绑定，未用摘要替代。
不同作者20次真实工具返回/原始profile/退出/来源图/消费/ack重放
`actual-v2-public-independent-replay.json` SHA256
`c1324a8bda7281a3b30265d3e8bf1c68f267bea3b8236833ff2b74eca449b026`。

另一新root`topolab-public-actual-v2-failure-prefix`仅将新公开bootstrap文件改为3bytes，
planSHA256 `2e7ceffad9513998ed3802f9944e1e5544a688cf916a652b810bb555380bac86`。
first PUBLIC PASS→R0源SHA STOP→唯一预付NEW-only共享失败前缀归档，保留4次tuple、
返回bytes/hash、主次错误和实际返回。后续源段/filing/release UNKNOWN_NOT_RUN，
48显式成员共130533bytes归档通过，无输入接受证书；HELD lease保守隔离失败root，
active清除。PUBLIC模拟FULL900，正式派发0。
`actual-v2-failure-prefix-summary.json` SHA256
`18ba0c91a32725ba44cb2e8f980889a081426670a17e9749660105c487ede5d0`。
不同作者重新逐字节/元组及6次实际返回核对的
`actual-v2-failed-prefix-independent-replay.json` SHA256
`3069b4877fe8a54a526849400953e3c46209e18093765ffc28aa10581c722d98`。

独立S3最终63 passed/323.17s，脚本及测试精确SHA冻结；S1/S2 focused24 passed/391.60s，
最终全仓回归另外核验精确最终源码。源复核回执`source-review-watchdog-v2.json` SHA256
`8614e839d1aa144abe961f0e12090bdd0ebdfadce6542acd868c56115295635c`。
S3 RED38/39分别证明未知outer清理误放行及额外watchdog sampler漏出完整RSS包络；
green40第一次只因预期11.0与原fixture真实11.2不符而失败，green40b修正测试预期后通过。
新增非行为错误包括lambda绑定/行长ruff告警、v2独立重放脚本把lock_sha256误写为
uv_lock_sha256，以及一次certify漏传冻结--role参数而被argv入口拒绝；日志/耗时都保留。
正确补齐调用后证书成功，未修改源码、重跑PUBLIC角色或改变STOP/argv规则。

## 最终v3：已有验收结果落盘异常保账

v2完整回归实际2699 passed/1平台skip（1427.60s，外层1440.369217458181s）后，
不同作者终审静态指出bind落盘异常会覆盖已有result。S2-RED-60经新公开CLI证实：
验收文件路径被占用后，已独立计算的whole_wall_seconds丢失。
最小修正保留已有whole/inner/资源/FULL/主次错误；追加落盘故障并强制STOP及两个
accepted=false，已有完整共享packet以unfiled_shared_packet保留。缺wire仍UNKNOWN，
没有从计划伪造账单或放宽独立closed/源访问/窗口规则。
GREEN61两种fault通过（7.91s），GREEN62共享packet同分支通过（40.16s），
完整raw_packets/role_results及计费保留，后续filing未运行。只有这一已复现边界被追加，
没有新一般guard或额外预算。v1/v2全量及实际原始证据继续保留原快照范围。

v3 S2源码SHA256 `ce6c46bde3b75b1f704670d84b41f806c16e00a5edc3122e726970a5db5d918d`，
S3仍为94be807…；`actual-v3-source-freeze.json` SHA256
`64d9cdf6fa6bdf4af68ae191f8bdc20bd4733f9953bb8d3724029edd515ccb57`，18项源/合同/lock。
不同作者补丁复核`source-review-bind-persistence-v3.json` SHA256
`d6e23f61036a5c8426dda72b53d9a68a829907be970d30d7d4df5d1f3a8136e1`。

新v3正向root`topolab-public-actual-v3-chain`的planSHA256
`dfe464691cd9cc1de21b1c0e8bcbb54ba9023b5127ef7054d5e27bc01956c060`。
20次原始工具返回、所有native/helper/计费/租约及1069成员40590471bytes同缓冲消费/ack
完整通过；首工具至shared最后返回64.15400004386902s，最大公开RSS包络1195884544bytes。
`actual-v3-positive-summary.json` SHA256
`9636a8857fbf2a5b027d7feda7e387e4e445a39aa765e9ac86e50128c6e2e851`；
不同作者原始重放`actual-v3-public-independent-replay.json` SHA256
`952ccc9c18aabeea054a0d3be51753d7e1c80752eab07ff52aa1b982c6ccb3bb`。
额外prepare/10bind/certify均实际exit0，没有v2遗漏参数问题。

v3新失败root`topolab-public-actual-v3-failure-prefix`的planSHA256
`2b52083e7d944e0c800088f81be8581bf3f161328277d6530fd019ce4109da66`；
新公开3bytes源SHA STOP后，仅一次预付共享归档48files/130522bytes，HELD隔离、active清除、
无证书或后续源段/filing/release。PUBLIC模拟FULL900，正式派发0。
`actual-v3-failure-prefix-summary.json` SHA256
`99b949bbea41c646a42fe0f79d570a54da3e5cafc76feea4de733d3dddea8e7f`。
不同作者最终失败链重放`actual-v3-failed-prefix-independent-replay.json` SHA256
`8cee25679254b6361577d21a984b6c79932ce1156240d8ea5e30a125d1bebc8d`。
最终精确v3软件镜像`v3-immutable-manifest.json` SHA256
`fc112285c14eb8fff81ad9902687715dfaf78cec1f04039c6cdfa0379cbab2cd`，
11785files/1009145477bytes；不同作者全量核对回执
`software-mirror-independent-verification-v3.json` SHA256
`d3442a47619050aeafe9bdd093a682b315f32777e947cde007b31ad2a97f065d`。
最终精确v3全量和受保护发表在本切片原连续钟内完成后方可闭合。

## 验证、证据及连续成本

工作树：`/private/tmp/topolab-failure-evidence-tgcbfpst`。两个原有dirty工作树由首尾逐文件
摘要/HEAD/index核对保留，不stash/reset/pull。已有未提交文件不进入本切片提交。
执行者证据：`/private/tmp/topolab-content-verified-preparation-ua91jmvi`；
独立者：`/private/tmp/topolab-content-verified-independent-k0k77ax2`。
新持久软件镜像（不是正式保管目标/输入备份）：
`/Users/keith1117/Documents/TopoLab-data/software-content-verified-preparation-2026-10-24-ua91jmvi`。
只复制本轮新软件/公开证据。`v2-immutable-manifest.json` SHA256
`72c624b87f8adf4e52e62a9e1fb9394e6bb47c3fab501986c835662518b53b2f`，
7939files/673097791bytes；不同作者逐文件/size/SHA/不同inode独立核验回执
`software-mirror-independent-verification-v2.json` SHA256
`c4133c06057105b1e945f5dd97ecfc16393b54b0f603673b19238fa7010aaa28`。
最终检查/CI/发表及closure另行append，不覆盖已留存字节。

执行者04:50:14.699320Z/monotonic2108089.633201083，cap21600s；
独立者04:50:40.401679Z/monotonic2108115.335872291，cap14400s。
所有实现、失败、等候、审查、完整本地检查、PR/main CI、留存/发表及实际最后返回连续计费。
没有暂停、转移、重置或额外出版额度。批准前草案、未量化机器/货币/CI成本UNKNOWN_NOT_ZERO。
PUBLIC模拟FULL不重开或记入任何旧formal额度；formal实际派发收费0不等于本轮准备成本0。

本节的最终本地检查、actual-public-run、独立审查及发布回执在发表前更新。
在实际观察完五项检查、精确PR/main四CI、镜像和最后返回之前，准备完成状态仍PENDING。
最终外部`publication-closure.json`封印实际PR/main SHA、四CI、manifest、原dirty文件保留
以及两方最后连续elapsed；它不能在事实发生前由计划或测试PASS代填。

## 最终本地检查与发表边界

最终v3锁定环境uv sync --dev --locked、ruff check .、mypy src均实际exit0；
完整pytest实际2701 passed/1平台skip，1256.87s，外层1260.3898968328722s，
开始06:38:44.179490Z至06:59:44.584193Z。平台skip只针对Darwin上的Linux x86-64
freestanding程序，不当作该表面的通过；PR/main的i1-native-software另外在Ubuntu24.04运行。
无数值算法或容差变化。最终git diff --check及精确19路径暂存检查必须exit0才能提交。

main发表前再核仍为c9502cbe8302ffa8e41939347081e4c96599e019，无开放PR；
严格保护、enforce_admins、3个required contexts保留，并额外要求i1-native-software。
源提交后仅在精确head四CI成功、受保护合并、精确main四CI成功、最终证据尾部及独立返回
实际观察完成后，外部publication-closure.json才可闭合本切片；本报告不事先填写未来CI结果。
旧工作树/25文件保留、代码与actual-v3冻结一致、所有实际连续成本由closure绑定。

## 唯一下一步

本轮在上述证据闭合后只关闭PREPARATION_COMPLETE_FORMAL_CLOSED并STOP；有必需缺口则
报告具体INCOMPLETE/STOP。下一步是另行批准明确源白名单/实际目标绑定、正式4500s和
结果7200s/3600s（含filing FULL180）的有限授权合同及独立启动计划；此前不开始正式源访问。
之后才可能依既定顺序进入B资源预检、C固定P/17修复。不得自动换目录、增加guard链、续钟、
重跑旧正式角色或复用任何旧配额。软件准备能力不是种子17科学修复，也不是full v2完成。
