# M2 H/17：有限输入登记与受限导出准备合同提案

日期：2026-10-18（America/New_York）。核对基线：`65bbbd3da9440250243886a8aaf142968bbca674`。
身份：`topolab.v2.p17-m2-input-export-preparation.proposal.v1`，修订1。
结构化伴随：[JSON](p17_m2_input_export_preparation_proposal.json)。
当前状态：**R_AUTHORIZED；TOOLS_PUBLICATION_REQUIRED_BEFORE_OLD_ACCESS；B_C_NOT_AUTHORIZED**。

后续所有者明确授权按本合同执行，执行者`/root`及不同作者独立子代理`/root/review_r_exports`，
3/2小时及内部I/O1860秒、白名单完整字节核验/临时解析均已批准。执行细则见
[授权R协议](p17_m2_input_export_preparation_protocol.md)。下方保留提出时的未批准语境；
其“本次不执行/尚未授权”只描述原文档切片，不覆盖本段后续授权。B/C及扩大/重试/后继仍禁止。

所有者已指定本对话的主执行者`/root`担任未来导出执行者。本条指令只批准提出合同和预算，
没有批准下述工时、旧元数据/原件读取、工具实现、导出、预检或科学调用；本次旧输入读取集合为空。
独立准备审查者尚未任命，须由不同于执行者/导出工具作者的角色担任；无需另外聘请外部人员。
本提案不建立TEXT科研Gate，不重开A、B4.30、I1或D1。B/C及其FULL180/14580秒仍须分别授权。

## 1. 目的及已完成基线

[A软件](../validation/p17_m2_native_homotopy_a.md)经PR202及权限表勘误PR203合并。
当前main上述提交，CI39172866765的quality、frontend、clean-linux-smoke、i1-native-software均成功；
开工核对无开放PR。A只实现公开软件；历史P/17仍未修复，真实H/17质量、速度和资源准入仍UNKNOWN/NOT_RUN。

本准备交付只消除“真实输入身份、受限视图与来源未登记”的阻塞，不能声称已使B/C可执行。
沿用新M2身份的4GiB RSS/完整退出实证口径和独立预检，不增加事前完整分配、内核或旧组件证明工程。
只用当前M2及已有软件CI；不安装、租赁、另选提供方、运行VM、FEM、推理、拟合或科学面板。

## 2. 精确逻辑范围

### 2.1 固定12个checkpoint

每一行只取已发表历史选择的原Safetensors字节，不再择优、不重新保存权重或修改header。

| 逻辑身份 | 原始来源 | 固定已选epoch |
|---|---|---:|
| C/17 | B4.1，`b3-v1-fits`，recipe C | 168 |
| C/29 | 同上 | 137 |
| C/43 | 同上 | 92 |
| P/17 | B4.1，`b3-v1-fits`，recipe P | 123 |
| P/29 | 同上 | 134 |
| P/43 | 同上 | 169 |
| W/17 | B4.5，`b4-5-weighted-terminal/fit`，weighted-terminal目标 | 93 |
| W/29 | 同上 | 156 |
| W/43 | 同上 | 142 |
| S/17 | B4.1，`b3-v1-fits`，recipe S | 65 |
| S/29 | 同上 | 115 |
| S/43 | 同上 | 127 |

W不是B4.1的A模型，也不是未加权P模型。W selection内部借用`recipe=P`的history schema，
但其外层版本/目标、context及文件来源必须绑定B4.5。S被各路由复用，仍只有3个原件，不重复计成9个。
每行登记：逻辑family/seed、selection路径/bytes/SHA、源context/source、选定epoch、checkpoint路径/
bytes/SHA、Safetensors格式/解析器版本/header/tensor names/shapes/dtypes及26,433个有限CPU float32参数。
固定tensor key/shape为`network.0.weight=(16,13,3,3,3)`、`network.0.bias=(16,)`；
`network.{2,4,6}.weight=(16,16,3,3,3)`及各`bias=(16,)`；
`network.8.weight=(1,16,1,1,1)`、`network.8.bias=(1,)`，恰好10个F32 tensor，无额外tensor。
按原Safetensors header/data offsets检查，数据体共105,732字节；原header保留不改写。
R只检查格式、有限性、来源和字节一致性，不实例化模型、不运行推理或重算selection MSE。
未来科学生产视图只获checkpoint与最小绑定元数据，不获训练history或fit-validation标签。

### 2.2 528个train-only NN逻辑导出

固定为B3.4原训练并集：小网格`12×6×3`的432个，大网格`24×12×6`的96个。
按原catalog的`role=train`完整集合及case_id排序；468/508/488是重叠训练成员视图，不是额外标签。
不包含32个fit-validation、48个screen reference、test/OOD/final或任何其他历史标签。
保持NN原10通道`encode_case`、原分尺度集合、float64 MSE和case_id平局规则；模型输入仍为原13通道。
准确528个case_id及文件身份须由未来R0登记，当前为UNKNOWN_UNREGISTERED，不编造hash或扩大集合。

每个逻辑case生成两个明确schema的JSON视图（合计1056个文件，不是1056个案例）：

- **生产视图**：schema、case/train/scale身份、完整获准problem定义、原label/context/manifest来源引用、
  实际`stored.design_density`及其float32 dtype、`(1,nz,ny,nx)` shape和位值摘要。仅此为NN消费字段。
- **独立视图**：上述来源；原`result.design_density/physical_density/compliance/converged`；
  总更新数和原`stored`中的design/physical/sensitivity_weight、compliance、physical_volume_fraction、
  iterations、terminal_density_change、stop_reason、dtype/shape；原`result.history`最后min(11,n)个
  更新状态的iteration、compliance、volume_fraction、density_change及两种density。
  少于11态只可保留原设计变化终止；physical_plateau须有11个真实更新后状态。原初态若证书确实需要，
  只能登记原初始化身份/既有值，不能新求解补造；缺必需字段即STOP。
- 仅转录实际原f64终态和实际存储f32终态，记录JSON pointer、IEEE位值/数组摘要及source SHA→view SHA。
  禁止从f64重新滤波、投影、求解、生成敏感度或“修复”存储终态后冒充导出。
  可作IEEE float32转换一致性核对；`float32(filter(f32 design as f64))`、物理量及敏感度数值重算
  留给另获准的C审查，保留每标签两次终态FEM的原请求，不在R偷跑1056次FEM。
- 不导出完整history、位移/反力、其他case、旧运行时间/费用或额外训练特征；不声称重新审计了完整旧轨迹。

字段选择从原JSON的`/entry/case/{case_id,problem}`、`/entry/{role,training_sets,source_case_id,physical_fingerprint}`、
`/context`、`/manifest_sha256`、`/initialization`绑定身份；从`/stored`逐项取上述实际存储字段，
从`/result`只取上述终态及`/result/history`原末窗。向量保持原扁平顺序，
`stored.tensor_axis_order=channel,z,y,x`，`stored.tensor_shape=(1,nz,ny,nx)`；不重排或补插值。
位摘要规定为逐元素little-endian IEEE-754 F32或F64字节的SHA-256，另绑dtype/shape/长度；
不是原JSON字节SHA的替代。完整获准problem/训练成员、source_case_id和原初始化身份须同时出现在两视图，
不能在训练并集中丢失原分尺度/成员信息；source/model选择metadata的旧费用/history字段不得传播到科学视图。

### 2.3 固定18个uniform标量

只取版本化[B4.30 v2合同](b4_30_paid_continuation_contract.json)的`population.sentinel.case_ids`
完整18例，JSON伴随列全ID；不能换成fresh/条件48/720或从有利控制/回退中选数。
来源限定为`b4-30-z-reflection-repair-v2/sentinel/reference`的18个uniform原attempt。
只导出case_id、原compliance的binary64值/位摘要、初始化/solver身份和源context、unit、packet的
路径/bytes/SHA/JSON pointer；原attempt须succeeded、无failure且无fallback，metrics和state终态标量一致。
不导出时间、候选结果、轨迹或密度；不重解、不重算分母。未来C的18个新uniform仍是配对计时分母，
旧标量只用于原rtol1e-9/atol0兼容检查，不作H选择oracle。R只证明转录来源与位值一致。

## 3. 两步有限来源登记；本次均不执行

拟根：`/Users/keith1117/Documents/TopoLab-data/p17-m2-input-export-preparation-v1`，**尚未创建**。
未来仅在另获R执行授权、独立公开I/O预检通过、工具已干净锁定合并且全部适用CI通过后，进入R0。
R0是本准备合同的元数据步骤，不是B，不允许科学payload探读。

### R0：固定元数据白名单及身份冻结

下列路径均相对于`/Users/keith1117/Documents/TopoLab-data`，只是拟授权路径，当前不得stat/open。

| 固定metadata文件 | 版本化来源中的预期SHA-256 |
|---|---|
| `b3-v1-fits/b3_training.json` | `229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7` |
| `b4-5-weighted-terminal/fit/progress.json` | `5e54f8cede96d9e4b60acc17586d25d29903bd4927461a8d6b4b18f3b49e43ac` |
| `b4-5-weighted-terminal/fit/summary.json` | `513064fe615456fe8204b511f850a71150895038c3541ad23f5cd35642b0cc6c` |
| `b4-30-z-reflection-repair-v2/context.json` | `cd0dffbb28347889726baacb8225efd9b2dadd94ea86f7485c843170b1ec2181` |
| `b4-30-z-reflection-repair-v2/sentinel/independent_audit.json` | `e9a8278b9a7d521992f7f5d62f3aef626e0767cd717f3ee134c2c4cc58b5ca2a` |
| `b4-30-z-reflection-repair-v2/sentinel/reference/progress.json` | UNKNOWN：仅未来R0允许首次登记当前字节身份 |
| `b4-30-z-reflection-repair-v2/sentinel/reference/summary.json` | UNKNOWN：同上，不冒充已发表hash |

B3 fitting index嵌入的data-index须匹配已发表`b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26`，
并匹配原catalog/manifest/source身份。其非目标A模型、validation、screen/final的引用/定义可能随完整
metadata字节被读取，但不得追踪其文件、作为查询输入或导出；不调用旧index loader展开整个旧输入树。

仅再允许固定W的3个`fit/units/0000..0002.json`、reference的18个`units/0000..0017.json`和
12个选定selection metadata。W链须回接预期progress hash和context
`0454eee24c1c72c051f10dce0162f0f41d5a5ade1fb3a4e5b42c9c82c9d11071`；12个selection按来源
内容寻址，B3只取C/P/S各3个。除此不沿指针递归，不运行旧`upstream_fits`或campaign。
R0合计最多40个旧metadata文件，每角色各一次有界读取；上限和严格路径派生见JSON。

reference的既往progress/summary hash当前未知。未来R0如获准，可在已知context、18例/顺序、
闭合链、已发表独立audit及执行者来源声明下登记其**当前观察身份**，由独立者核对并冻结；
这不重建历史未发表的字节锚或证明未被篡改的时间历史。来源/context/链不一致或独立者不能接受该
明确来源边界则STOP，不能把新计算的SHA本身当作来源证明，也不改用另一个旧面板。

产出`source_registry.json`：全部12模型、528训练原件、18标量原packet、每个来源metadata及链成员的
literal path、来自已读metadata的声明bytes/SHA、版本化预期schema/shape、case/role/scale、选择来源及字段/读取上限；
区分预先已发表hash与R0首次登记hash。R0只确认metadata链及其payload引用，不提前stat/open科学payload；
payload实际文件字节/header/字段存在性在R1各自唯一一次读取中核对，不能把R0预期写成实测通过。
独立者接受完整登记表之后才可进入R1；必需引用不齐或超域即停止，不假定任何占位值可执行。

### R1：只读原件、受限转录及来源比较

未来须明确批准以下**新的准备角色例外**，不能说成A或C原有权限：
528个指定train标签和18个指定uniform packet的**完整文件字节**会为hash和JSON解析而读取；
有界普通JSON解析也会临时物化原完整history字段。语义使用仅限第2节白名单，随后丢弃其余字段；
不分析全轨迹、不调用带全history验证的B3 model/旧读入函数，不保存/打印原件或完整history。
不为规避这项实情临时开发流式证明工程。若所有者不批准这项完整字节/临时解析例外，R1不能执行。
C生产者/科学审查者仍只能读取新受限视图，原拒绝集合不追溯改变。

每个原payload只允许执行者和独立者各一次完整有界读取（同一缓冲完成hash/解析/字段核对），原件只读；
不扫描目录、枚举其他文件、读取备份或执行序列化对象。输出须独占新根、不可覆盖，pending先于启动，
terminal接受在实际观察退出后，缺失退出保持UNKNOWN。共享收尾只读新产物和登记表，不第三次打开旧原件。
原件读取不改变mtime/内容；实际文件系统可能更新atime，不据此伪称绝对零元数据写入。
每个文件打开前拒绝非普通文件、symlink/路径逃逸、登记外路径及超限尺寸，读取后核对长度/SHA与源身份；
竞态/中途变更拒绝，不自动再读。新导出及独立备份只存12个获准checkpoint原样副本、新受限视图/登记/收据，不复制完整旧label或packet。

## 4. 字节、形状及权限上限（提议，不是已测资源保证）

| 类别 | 单文件上限 | 每角色原件总字节上限 / 输出上限 |
|---|---:|---:|
| R0的B3 fitting index | 16MiB | R0全部旧metadata合计32MiB，最多40文件 |
| 其余6个固定metadata | 各1MiB | 同上 |
| 21个unit metadata | 各32KiB | 同上 |
| 12个selection metadata | 各256KiB | 同上；最多200条既有epoch记录，仅绑定固定选择 |
| checkpoint | 1MiB | 12MiB；12个逐字节原样副本 |
| train label原件 | 64MiB | 768MiB；恰好528个、总更新<=360、每向量216或1728 |
| uniform packet原件 | 4MiB | 72MiB；恰好18个 |
| NN生产视图 | 128KiB | 合计32MiB |
| NN独立视图 | 2MiB | 合计256MiB；每case最多11个原更新状态 |
| 18标量单一导出 | 64KiB | 恰好18条 |

这些是拒绝上限，不是对未知文件尺寸或未来RSS的测量。B3.4已发表608个原artifact合计772,490,763字节，
只支持选择768MiB训练原件总上限的规划合理性，不证明单文件、Python对象或完整角色链峰值。
引用路径/声明大小及预期schema与上限在R0核对，实际payload在R1核对；超限不截断、不放大、不换源。JSON拒绝重复key、NaN/Inf、
深度>64、越界维度、超长向量及未登记外部引用；所有source字段/两视图schema须在R工具冻结前列齐。

## 5. 拟预算、资源及有限调用

**全部为请求，当前获准执行秒数为0。** 建议一次准备能力最多**5主动小时：执行者3小时、独立者2小时**。
包含登记、最小只读转录/比较工具、公开fixture调试、实际有界I/O、失败/等待及收尾；不用A剩余工时。
这是投资上限，不是完成时间预测。只限有限字段/位值工具，不新增算法、通用平台或证明后端。

| 内部执行子预算 | 提议上限及归属 |
|---|---|
| 执行者完整非科研I/O角色 | <=900 charged wall秒；R0<=120、R1<=780，合计<=900，在3主动小时内 |
| 独立者完整角色 | <=900秒；一次公开I/O预检<=120、R0<=120、R1<=660，在2主动小时内 |
| 共同控制/最终退出/归档 | FULL60，实际<=60，未用仍全记；主执行者负责，计入其3小时，独立者自身参与计入2小时；与角色已包络工作不重复加 |
| 总受限I/O预留 | **1860秒=900+900+FULL60**，不互借；不是B/C的180/14580，也不计作已付 |
| 规定回归/CI/正常发布 | 如未来实现/提交则全部既有检查仍执行，另记实际软件成本；不使用旧源实验充当守卫 |
| 新采购/付费扩容 | 拟上限USD0，仅已有M2/CI；已有电力、订阅及实际CI费用UNKNOWN_NOT_ZERO，不能据此声称总费用0 |

未来最多6个命名外层命令：独立公开I/O预检、执行者R0、独立者R0、执行者R1、独立者R1、共同收尾。
每命令完整收费至少`max(native wall, observed outer wall)+10s`，内部已收费更高则取高者；启动、hash、
解析、写入/flush、失败、所有helper及观察退出均计费，10秒在各子cap内。公开I/O预检只测有限读写工具/
新合成fixture和记录链，不进行FEM或科学B预检，不消耗B配额；其失败/UNKNOWN即关闭R，不补跑。
开发期普通公开调试计入对应3/2小时；冻结后上述来源处理每角色一次，首次失败停止，无自动retry/reset。
实际argv/cwd/runtime/thread/模块来源、source读取表、helper/native单位/重叠/profile/观察退出及预算归属
须在R0前冻结为完整调用表；R0新增的source身份是预声明的有限登记步骤，不得扩展白名单。

R的全部同时角色/控制/计时/记录链仍<=4294967296字节，以已采用的native RSS高水位、组/控制器采样、
保守重叠及完整退出作实证核验。不同作者先完成上述公开I/O独立预检；每次真实旧输入处理仍记录本次
RSS/退出，公开通过不保证原件处理必过。在线或退出后超限、OOM、逃逸、helper覆盖/最后退出UNKNOWN即STOP。
不要求事前完整分配/内核证明，不将R的I/O检查称作B的PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL。
已有CI若需新增实际付费或超出现有配额，须先由所有者接受币种/费率/金额/付款人上限，否则停止该付费动作。

## 6. 独立审查与验收

未来独立者须不同于`/root`及转录工具作者，单独编写源字段/位值比较逻辑，不把导出者的PASS或manifest当oracle。
可接触公开规划/源码，明确非盲审；不调用候选H驱动、旧campaign、旧全label validator、Torch推理或FEM。
按自己的旧来源白名单读取全部获准原件，并全量核对：

1. 12个family/seed/epoch/来源与tensor header准确；checkpoint输出逐字节同源，无A替代W或重选。
2. 528个逻辑case唯一且集合完整、432/96尺度分布正确、均train；两视图字段/schema和数组位值/顺序/来源
   一致，敏感度只出现在独立视图。原f64与实际f32分别保存，原末窗不冒充完整轨迹审查。
3. 18个scalar恰为固定sentinel、原uniform成功attempt、无fallback取代；旧C值按原位值转录；
   生产角色看不到其他候选或旧时间，后续仍需18个新uniform兼容检查。
4. 每个导出有source path/bytes/SHA、原字段pointer、view bytes/SHA、执行者来源声明及独立比较记录；
   哈希不能单独证明字段来源，必须比较原件。声明当前源观察范围，不能伪称重建历史冻结证据。
5. 4GiB实证、所有有界读取/费用/失败/观察退出及新产物独立备份完整；旧原件/报告/封存未改动。

全部满足才可记`PREPARATION_COMPLETE_SOURCE_BOUND`，只是准备交付，不是科研Gate、模型正确性或B/C准入。
完整B/C调用/费用/角色表仍未闭合的字段必须单列UNKNOWN；不能因导出完成删审查或默认获准B。

## 7. STOP与收尾

缺R执行授权/独立任命/数据-free I/O预检/干净锁定合并全CI源码；来源、集合、SHA、字段、schema或位值不符；
实际文件超字节/次数/工时/费用/RSS cap；任一禁止访问、冻结后修改、失败/OOM、未确认退出或来源UNKNOWN，
均停止相应树和后续旧读取。保留不可变失败前缀、尝试/完成数量、已付费用和未执行后缀；不补读备份，
不替换案例/文件、不重新生成标签/权重、不调整cap、不自动重试或启动B/C。
STOP所称来源UNKNOWN指R0结束仍未闭合的必需出处/字段；第3节明确允许的首次登记hash在登记前为UNKNOWN，
不是要求另造历史证明或禁止按未来R0范围登记。任何未获源角色例外的旧读取仍禁止。

当前唯一下一步是所有者审阅本提案的5小时/1860秒、完整原件字节/临时解析例外、有限元数据链及独立角色权限；
如将来明确批准R，也只执行R后停止。B需另授权一次FULL180公开正式预检；C需再另授科学/视图/14580秒。
FULL_V2_OPEN_NO_ADMITTED_ROUTE、固定P/17未修复、uniform默认、完整训练PENDING4GiB、B4.51失败/已消耗配额、
D1 STOP/未启动0/1/FULL60、关闭的救援、I1资源UNKNOWN、B4.52 NOT_SELECTED_BY_R1及全部旧失败/UNKNOWN/封存保留。
K=12721.16417100014444982>7200及D1已记FULL60不变；R1860若全部计费只是新的上限场景，另加工程/软件/CI，
不修复旧all-paid7200。B3的M2+独立Ubuntu24.04、两尺度/最终独立复现及B客体容量方案的独立边界保持。

## 8. 本次文档检查及停止

本次只读取版本化文档/必要源码文本及GitHub状态，未沿上述来源路径读取任何旧metadata/payload，未创建数据根，
未实现或执行导出/资源预检/B/C。仅检查JSON、两份合同及父草案的权限/数量/预算一致性、相对链接和差异。
本次文档/核对成本单列UNKNOWN_NOT_ZERO，不从未批准的R预算扣除，也不并入旧科学账本。
文档保持未提交工作树供审阅；未启动规定回归、CI或发布。任何未来提交前仍必须运行既有五项完整检查，
审查逐项暂存/上传提交并遵守全部PR/main CI保护，不因“只改文档”豁免。
