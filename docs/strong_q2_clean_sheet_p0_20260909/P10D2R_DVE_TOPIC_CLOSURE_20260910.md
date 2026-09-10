# P10-D2R 真实 fallback 时序审计与 DVE 题目关闭

**判定：** `P10D2R_REALISTIC_FALLBACK_STOP`

**题目状态：** `DVE_TOPIC_CLOSED_AFTER_D2R_IDENTIFIABILITY_STOP`

**训练：** 未启动。

## 1. 审计设计

本轮只修正 P10-D2 已识别的 fallback 时间语义，不修改候选方法，也不调节奖励或门槛：

- accept 在第一次慢推理完成时立即执行已冻结的旧机动；
- reject 后立即进入共享的有界保持动作；
- fresh replan 从第一次推理完成时开始，并承担与原提议相同的慢推理时延；
- 新机动仅在第二次推理完成后执行；
- 零时延重规划不作为公平对照。

## 2. 结果

| 指标 | 结果 | 预设门槛 | 判定 |
|---|---:|---:|---|
| oracle 选择 accept | 60.17% | 20%–80% | PASS |
| oracle 选择 replan | 39.83% | 20%–80% | PASS |
| 同时延有效性分叉对 | 43.81% | ≥20% | PASS |
| 联合不兼容状态 | 17.00% | ≥10% | PASS |
| always-accept 相对 oracle 差距 | 56.56% | ≥10% | PASS |
| always-replan 相对 oracle 差距 | 5.00% | ≥10% | **FAIL** |

always-accept、always-replan 和逐条件 oracle 的平均价值分别为 -3.922、-2.630 和 -2.505。

## 3. 科学判断

真实 fallback 时序解决了“零成本即时重规划”的接口错误，并证明任务中确实存在双向的 accept/replan 决策。然而，固定 always-replan 仍取得了 oracle 可达价值的大部分，候选有效性机制剩余的平均增益空间不足以通过事前设定的可识别性门。

继续通过加大重规划时延、改变目标运动分布、提高碰撞惩罚或降低门槛来制造差距，会把题目演化为围绕候选机制调任务。因此，本轮结果不能授权学习实验。

## 4. 最终决定

按 P10-D2 停止报告中冻结的唯一修订合同，D2R 未通过后关闭 DVE 题目线：

- 不实现 DVE 候选学习器；
- 不训练基线或候选方法；
- 不继续调整任务分布；
- 保留 P10-A 至 P10-D2R 作为零训练选题否证链；
- 下一课题必须重新建立问题缺口和可识别性，而不是继承 DVE 名称继续包装。

## 5. 证据边界

本结果否定的是当前连续双 UAV 拦截构造对 DVE 方法差异的实验可识别性，不是否定实时决策有效性这一普遍研究问题。由于未启动训练，本结果不提供任何学习算法性能比较。

## 6. 资产

- 环境：`envs/dve_continuous_intercept.py`
- 配置：`configs/p10d2r_dve_realistic_fallback_audit_20260910.json`
- 审计：`scripts/p10d2r_dve_realistic_fallback_audit.py`
- 结果：`docs/strong_q2_clean_sheet_p0_20260909/P10D2R_DVE_REALISTIC_FALLBACK_RESULT.json`
