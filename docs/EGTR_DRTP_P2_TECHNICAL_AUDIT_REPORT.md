# EGTR-DRTP P2 技术审计报告

**协议：** `EGTR-DRTP-P2-TECHNICAL-AUDIT-V1`  
**状态：** `PASS — IMPLEMENTATION SEMANTICS VERIFIED`  
**日期：** 2026-08-26

## 1. 审计边界

本次只验证冻结 EGTR 方法合同的实现语义。未生成 evaluation tape，未使用 held-out/canonical seeds，未启动 development、1M 或 3M 长训练。one-update smoke 仅用于检查训练入口、日志和 checkpoint wiring。

机器可读结果：
`results/development/egtr_p2_technical_audit_v3/EGTR_DRTP_P2_TECHNICAL_AUDIT.json`

## 2. 结果

| 审计项 | 结果 |
|---|---|
| 单个空 group 不触发 global reset | PASS |
| per-group evidence 与 confidence EMA | PASS |
| nominal-relative robust gap | PASS |
| median 近零/跨正负回报有限性 | PASS |
| 平移不变性 | PASS |
| 正比例缩放不变性 | PASS |
| UTR/DRTP/EGTR q simplex 与 bounds | PASS |
| 最终输出 L1 trust-region hard bound | PASS |
| full-confidence DRTP recovery | PASS |
| deterministic replay | PASS |
| mid-window save/reload exact continuation | PASS |
| telemetry fields | PASS |
| EGTR one-update checkpoint smoke | PASS |
| 新 evaluation tape | NO |
| 长训练 | NO |

## 3. 关键修复记录

初次测试发现：如果复用旧 DRTP 的“所有 failure-group EMA 必须 ready”条件，单个空 group 仍会阻塞整个 adaptive update。这与 EGTR 的 per-group evidence 语义冲突。

当前实现已改为：nominal EMA ready 且至少存在一个 failure-group EMA 时即可更新；尚无 EMA 的 group 其 difficulty 置零，其 confidence 继续按冻结 EMA 规则衰减。这样单组数据缺失只影响该组，不再否决其他 group 的证据。

## 4. 投影顺序

当前严格执行：

\[
q^A\rightarrow z\rightarrow\Pi_{\mathcal Q}(q^*)
\rightarrow\text{L1 trust region}\rightarrow q_{u+1}.
\]

trust region 之后不再投影。最终输出同时满足：

\[
q_k\in[0.05,0.35],\qquad \sum_kq_k=1,
\qquad \lVert q_{u+1}-q_u\rVert_1\le0.10.
\]

## 5. 解释边界

`P2 PASS` 只表示 EGTR 严格实现了冻结合同，不表示 EGTR 已经改善性能、降低 catastrophic seed rate 或构成论文已验证主算法。上述问题必须由新的、合同冻结后的 UTR/DRTP/EGTR paired development 单独验证。

## 6. 当前停止点

EGTR P2 已 PASS。下一步只能冻结 P3 development contract；未经单独授权不得生成新 tape 或启动训练。
