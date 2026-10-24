# P/17 — 内容验真保管模型：已批准的软件准备协议

日期：2026-10-24（America/New_York）。基线 main
`c9502cbe8302ffa8e41939347081e4c96599e019`。
[执行授权记录](p17_m2_content_verified_custody_protocol.json)。

**CUSTODY_MODEL_ADOPTED / PREPARATION_ACTIVE / FORMAL_CLOSED。**
所有者直接回复 `call_8e8daf47565a4691b1bdb20b0a407f4b/0`：
“批准草案及新6h/4h准备预算（推荐）”。这明确批准新合同、S1/S2/S3回归接口及全新准备预算。

## 采用的规范及明确替代

[原草案](p17_m2_content_verified_custody_proposal.md)第1–8节的技术、兼容、测试、
资源/STOP/计费及退出要求作为本协议规范，MD SHA256为
`4ba70b28826dd3443e936ad8a97112575bcea4af08b9019d17397d831899abd3`；
其[JSON快照](p17_m2_content_verified_custody_proposal.json) SHA256为
`8fa602f3d86be03da0c336f7569a35a68ce31052517249e0bf32b35f098aa7e0`。
原草案保留待批准时的字节，以下真实授权优先于其中历史not-granted字段：

- 新身份 `topolab.v2.p17-m2-content-verified-input.v1`的软件准备、内容验真模型及
  S1（同缓冲消费）、S2（实际公开编排）、S3（独立最终验收）均已批准。
- 执行者21600s、不同作者独立者14400s准备预算已批准；所有失败、等待、检查、PR/main CI、
  留存和实际最后返回连续计入。没有另加出版/结果预算，旧余额和旧600s核验不转移。
- 新公开fixture的软件实现、不同作者审查、完整回归及正常受保护发表已批准。
- 拟议AppSupport目标不stat/create/probe；旧原件stat/read/copy/临时解析、正式六角色、
  B/C、新安装/购买、全局同步变更、旧配额恢复均未批准。正式4500s及结果2h/1h仍是提案。

新模型保证每次消费的固定来源/内容/身份/角色正确；不保证目标从未同步/上传、外部进程
全期不改动或持续可用。Provider UNKNOWN如实记录，仅不作为该新模型的EXCLUDED前提。
原件/本地/备份四元组、同hash替换拒绝、短读、来源全量比较、4GiB实证资源、退出、窗口、
FULL、失败记录和计费规则全部保留。租约只协调登记TopoLab角色，并记录真实取得与最后reader返回。
旧协议/报告/身份及历史FAIL/UNKNOWN/成本/配额/封存不改，不解释旧第12次失败原因。

## 本次连续时钟与作者

执行者 `/root` 首工具2026-10-24T04:50:14.699320Z，monotonic2108089.633201083，
21600s截止2026-10-24T10:50:14.699320Z。
不同作者 `/root/content_verified_independent` 首工具2026-10-24T04:50:40.401679Z，
monotonic2108115.335872291，14400s截止2026-10-24T08:50:40.401679Z。
时间为UTC记录；独立者先冻结期望/算法再接触生产补丁，基线知识及NONBLIND审查如实披露。
批准前草案劳动为单独的UNKNOWN_NOT_ZERO，不追溯计入本预算。

本轮仅交付新公开完整调用链及独立证据；任何正式源/目标、六角色或科学接受仍未观察。
缺失必需实现/最大对象/原始返回/资源证据时记录具体INCOMPLETE，不由计划或PASS字段填空。
完成全部五项检查、精确PR/main四项CI、独立审查和本轮软件证据留存后关闭本切片并停止。
下一步仅为另行源访问/正式/结果授权评审；不自动尝试新目录、补跑角色或续预算。
