# R-DRTP-SG-MAPPO 稳定化机制设计合同（仅设计，未授权训练）

**状态：** `DESIGN-ONLY / NO TRAINING AUTHORIZED`

**日期：** 2026-08-26

## 1. 设计动机

历史 forensic 结果确认 DRTP 存在跨 tape、跨 failure family 可重复的 catastrophic training seed，但尚未证明唯一根因。当前最合理的可证伪假设是：return → EMA/difficulty → q → exposure → return 的自适应反馈在部分训练轨迹中形成 runaway reweighting，导致策略进入不利训练状态。

R-DRTP 不把该假设写成事实；它只提供一个最小、可审计的稳定化机制，用于检验“限制适应速度并恢复均匀扰动锚点，能否降低 catastrophic seed 风险”。

## 2. 冻结不变项

R-DRTP 必须保持：

- matched Single-Graph actor/critic 和 116,728 参数；
- PPO、学习率、奖励、S2 environment、failure semantics；
- actor information boundary、七个拓扑组和 50% nominal exposure；
- 推理期网络与计算量；
- UTR 与原 DRTP 的训练/评估合同和 final-checkpoint 规则。

禁止新增 encoder、critic 分支、reward term、recurrent memory、DRTP 之外的 return-adaptive sampler 或新的 PPO 超参数搜索。

## 3. 稳定化更新

保留原 DRTP 得到的候选分布 `q^cand_u`，但不直接使用。对每个 failure group `k`，在 adaptation window 中记录完成样本数 `n_{k,u}` 和组内回报离散度 `v_{k,u}`。离散度必须使用预先冻结的 robust statistic（例如 MAD 或截尾方差），不得由结果反向选择。

定义可信度：

`c_{k,u}=clip(n_{k,u}/(n_0+n_{k,u}),0,1) * exp(-lambda_v * clip(v_{k,u},0,v_max))`。

取 `c_u=min_k c_{k,u}`，自适应幅度为：

`alpha_u=alpha_max * c_u`。

最终 failure-group 分布为：

`q_{u+1}=(1-alpha_u) * uniform_6 + alpha_u * q^cand_u`。

因为 `uniform_6` 与 `q^cand_u` 均属于同一 bounded simplex，最终分布仍需通过已有质量断言和上下界断言。`alpha_u` 只控制适应幅度，不改变 nominal 50% anchor。

该更新有两个可检验性质：

1. 组样本不足或回报波动大时，`alpha_u` 下降，避免单个 seed 的短期回报强行改变长期 exposure；
2. 当估计稳定时，`alpha_u` 才允许接近 `alpha_max`，保留 DRTP 的难度聚焦能力。

`n_0`、`lambda_v`、`v_max`、`alpha_max`、MAD/截尾规则和更新窗口必须在任何训练前由独立 technical contract 冻结，不得根据当前 DRTP/SNR 数值调参。

## 4. 与已有方法的关系

| 方法 | 作用 |
|---|---|
| UTR | 稳定的条件均匀参考 |
| DRTP | 原始有界自适应方法，保留高平均收益与 seed sensitivity |
| SNR | 内部 fixed-nonuniform audit，不作为论文主比较 |
| R-DRTP | 仅针对自适应反馈稳定性的候选修复 |

R-DRTP 的创新主张不能写成“提出了新的通用鲁棒优化理论”。可主张的候选机制是：在 topology-perturbation adaptive exposure 中引入 uncertainty-gated uniform restoration，以抑制训练种子依赖的 runaway reweighting。

## 5. 必须先通过的零训练技术门

- 公式与代码映射审计；
- parameter equality 与 actor information boundary；
- seven-group exposure 合同；
- `alpha=0` 时与 UTR/原 DRTP bookkeeping 一致；
- `c_u=1` 时与原 DRTP 更新一致；
- 极端小样本/高方差时 `alpha_u` 单调下降；
- simplex、floor/cap、nominal mass 和 deterministic replay；
- save/reload/next-update continuation；
- logging 不改变训练路径；
- one-update finite-value smoke。

任何门失败都不得启动长训练。

## 6. 后续验证边界

技术门通过后，另行冻结 R-DRTP 与 UTR 的 paired development contract、训练 seeds、预算、tape 和 catastrophic rule。R-DRTP 只有在同时降低 catastrophic seed rate、保持 nominal competence、改善 F0/OOD 且不恶化 safety 时，才可被描述为“稳定化有效”。否则只保留原 DRTP 的“高平均收益、训练种子敏感”定位。

本合同不授权实现、训练、held-out、canonical seeds 或任何自动延长。
