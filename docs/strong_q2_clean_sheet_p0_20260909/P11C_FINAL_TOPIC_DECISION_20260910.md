# P11-C 具身主动揭示选题最终判定

## 判定

`P11_TOPIC_NO_GO / NO_TRAINING`

P11 不是当前可进入训练的强二区新选题。

## 已通过的部分

- P11-A 证明抽象的 commit / reserve / inspect 模型存在非平凡决策区域；
- P11-B 排除了“需求不确定、稀缺专家、延迟确认、提前占位”等已被 AURA 覆盖的伪创新，只保留“具身主动揭示”作为候选差异；
- P11-C 证明几何会改变最优动作，带噪观测会改变联盟承诺，因此审查过程不是静态标签查询。

## 停止原因

在冻结的 288 个组合条件中：

| 指标 | 结果 |
|---|---:|
| 主动揭示成为最优策略 | 0/288 |
| 主动揭示击败最佳非主动策略 | 0/288 |
| 主动揭示相对最佳非主动策略平均差 | -0.943 |
| 几何诱发的最优动作分叉 | 25.00% |
| 噪声信号诱发的承诺翻转 | 24.31% |

最强非主动策略由 AURA-style 前摄占位与直接保留共同覆盖了任务价值。主动侦察虽然产生有效信息，却没有产生决策上可识别的净收益。因此继续设计 MARL 方法只会学习一个被强基线支配的动作。

## 为什么不修参数继续

降低侦察成本、延长外生揭示延迟、提高传感精度或改变先验都可能人为创造主动揭示优势，但这会在观察结果后重塑任务。除非未来存在独立的现实任务来源能够外生确定这些量，否则不允许用参数扫描复活 P11。

## 资源决策

- 不建正式训练环境；
- 不训练 baseline 或候选方法；
- 不把 P11 包装为论文贡献；
- 保留 P11-A/B/C 作为选题排除记录，防止以后重复投入。

## 证据文件

- `configs/p11_active_revelation_commitment_topic_gate_20260910.json`
- `configs/p11a_active_revelation_analytic_audit_20260910.json`
- `configs/p11c_embodied_revelation_identifiability_20260910.json`
- `scripts/p11a_active_revelation_analytic_audit.py`
- `scripts/p11c_embodied_revelation_identifiability.py`
- `docs/strong_q2_clean_sheet_p0_20260909/P11B_AURA_PAPER_CARD_20260910.md`
- `docs/strong_q2_clean_sheet_p0_20260909/p11c_embodied_identifiability/P11C_EMBODIED_IDENTIFIABILITY_RESULT.json`

最终结论：P11 已完成“能否作为真正选题”的判断，答案为否；停止发生在零训练阶段。
