# R-DRTP 路线 B 项目阶段合同

**状态：** `R-DRTP ARCHIVED — EGTR P1 FROZEN — EGTR P2 AUDIT REQUIRED`

**日期：** 2026-08-26  
**训练授权：** 无

## 1. 科学问题

本阶段不再把问题表述为“让 DRTP 更强”，而是检验：

> 可靠性门控的自适应拓扑扰动训练，能否在不牺牲扰动性能的前提下降低训练种子敏感性？

当前证据支持“DRTP 存在高平均收益并伴随真实 seed sensitivity”，但不证明唯一根因是 policy basin divergence。`return → EMA/difficulty → q → exposure → return` 是待检验的机制假设，不得写成已证实事实。

## 2. 历史证据边界

- DRTP 历史高收益、catastrophic seed、held-out 反转和 REL-A0 结果全部保留；不得回写历史结论。
- SNR 作为 fixed-nonuniform 内部证据保留，不作为论文主比较，也不作为 R-DRTP 调参数据。
- 已使用的 cohort（包括 2301–2305、2401–2405 及此前所有 development/held-out seed）不得冒充 R-DRTP 的前瞻性确认 cohort。
- 不得用当前结果倒推 R-DRTP 的统计量、常数、窗口或训练 seeds。

## 3. R-DRTP 最小修改

R-DRTP 只允许修改 training sampler 的 failure-group exposure update：

\[
q^R_{u+1}=(1-\alpha_u)q^{uniform}+\alpha_u q^{cand}_u,
\qquad \alpha_u=\alpha_{max}c_u.
\]

`q_cand` 沿用原 DRTP 候选分布；`c_u` 只能由当前 adaptation window 的组样本充分性与 robust return dispersion 计算。不得新增 encoder、RNN、critic、reward、auxiliary loss、PPO 参数或 actor 输入。

## 4. 阶段门

### P0 — 机制假设冻结

已完成：明确 instability hypothesis、证据边界和可证伪目标。

### P1 — 方法合同冻结

已完成初版设计合同：
`docs/R_DRTP_STABILITY_MECHANISM_DESIGN_CONTRACT.md`

在 P2 开始前必须补齐并冻结：

- robust dispersion 的唯一计算定义；
- `n_0`、`lambda_v`、`v_max`、`alpha_max`；
- adaptation window 与 warm-up/empty-window 处理；
- floor/cap、simplex、nominal anchor 和 update timing；
- exact code mapping 与 provenance hash。

这些内容必须在看到 R-DRTP 性能前冻结。

### P2 — 零训练技术审计

P2 仅检查实现与数学合同，不产生正式 development tape，不启动长训练。至少包括：

- 参数量与 actor information boundary；
- UTR/原 DRTP/R-DRTP sampler 合同映射；
- 七组 exposure 与 50% nominal anchor；
- `alpha=0` 的 uniform identity；
- `c_u=1` 的 DRTP identity；
- 小样本/高离散度时门控幅度单调下降；
- bounded simplex、floor/cap、质量断言；
- deterministic replay 与 save/reload/next-update continuation；
- logging invariance 与 one-update finite-value smoke。

任一技术门失败，停止，不得进入训练。

## 5. 后续训练授权边界

只有 P2 全部 PASS 并由单独授权后，才可冻结新的 paired development contract。该合同必须重新指定：

- 未使用过的 R-DRTP/UTR/DRTP seeds；
- 统一预算、evaluation tape、milestones；
- catastrophic、nominal、F0/OOD、安全和 exposure 判据；
- 不得删除差 seed、挑 checkpoint 或自动扩展预算。

默认候选路线为 UTR/DRTP/R-DRTP 三臂对比；不允许只训练 R-DRTP 后宣称稳定化有效。

## 6. 预注册成功条件

R-DRTP 只有在同时满足以下条件时，才可描述为“稳定化有效”：

- catastrophic seed 数下降；
- worst paired degradation 与 seed dispersion 改善；
- nominal competence 不明显下降；
- F0/OOD 性能不被显著牺牲；
- collision、timeout、constraint 和 pre-trigger safety 不恶化。

若 R-DRTP 仅接近 UTR，则结论只能是“降低不稳定性但牺牲自适应收益”；若仍接近 DRTP 的不稳定表现，则关闭该稳定化路线。两种情况都不得继续无合同搜索新算法。

## 7. 当前停止点

本文件与 `EGTR_DRTP_METHOD_CONTRACT.md` 完成路线 B 的 P0/P1 归档。当前不训练、不生成新 tape、不使用 held-out/canonical seeds，等待 EGTR P2 技术审计完成。
