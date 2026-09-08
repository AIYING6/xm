# P0D：历史路线排除矩阵

## 目的

本文件只回答一个问题：哪些看似“新”的强二区候选，实际上已经在本仓库中被实现、审计或否决。历史开发实验不作为当前 DRTP 正式结果，但可用于避免重复选题。

| 候选机制 | 仓库内既有证据 | 排除理由 | P0D 决策 |
|---|---|---|---|
| 拓扑条件信用分配 / 反事实 critic | `configs/cv_drtp_d0_design_freeze.json`；`configs/drtp_bline_mechanism_discovery_freeze.json`；`docs/drtp_bline_state_20260831/B_LINE_PORTFOLIO_DECISION.md` | CV-DRTP 已直接检验反事实 critic；两个 fresh cohort 均损失回报并新增 catastrophic seeds | 永久排除，不改名重启 |
| group-robust / constrained PPO 更新 | `docs/racg_ppo_c1_20260904/RACG_C1_FINAL_RESULT.md`；`docs/tgtr_ppo_c1_20260904/TGTR_C1_FINAL_RESULT.md` | RACG 仅 2/5 满足 worst-group gate 且成本 6.84--11.05 倍；TGTR 的 actor 更新为 0 | 排除 |
| 坏 seed 动力学根因与早期 precursor | `docs/drtp_b5_final_review_20260830/B5_FINAL_MECHANISM_REVIEW.md` | residual、TD error、advantage、梯度冲突和组行为没有形成跨坏 seed 重复且控制组缺失的 precursor | 排除重复审计 |
| 拓扑转变记忆 / snapshot+recurrent encoder | `docs/tatg_mappo_p0_20260904/audit-rerun/TATG_P0_REPORT.md` 及后续 TATG 实现资产 | 已形成独立 TATG 路线并进入实现/试验，不再是干净的新问题 | 排除 |
| 可控路由、任务重规划或通信干预价值 | `docs/c_line_c0_20260905/C_LINE_C0_FINAL_STATUS.md` 及 P0C/TIV 审计 | 当前动作接口没有原生路由/通信决策；若保持现接口，干预对象不可控 | 当前仓库内排除；仅可作为接口扩展后的新课题 |
| 继续修 sampler、gate、confidence 或稳定化模块 | DRTP/EGTR/GA-EGTR 历史开发合同与最终冻结决策 | 属于既有算法的局部修补，创新上限低且已消耗大量试错 | 排除 |

## 使用边界

- 上表中的历史负结果是**选题排重证据**，不是当前正式 A/B 结果。
- 它们不得与当前正式 cohort 合并统计，也不得写成最终算法的确认性失败。
- 它们只支持“不要再次投入同一机制”的资源决策。

