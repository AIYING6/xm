# TGTR-PPO P0：文献—机制矩阵

本表只使用原始论文/会议页面作为方法基础。文献提供构件，不替代本项目的 empirical validation。

| 来源 | 可借用的原理 | 不能直接照搬的部分 | 对 TGTR-PPO 的具体作用 |
| --- | --- | --- | --- |
| Schulman et al., **TRPO**, ICML 2015 | 用策略分布散度限制更新，而不是只限制参数距离 | 标准 TRPO 只约束总体状态分布，不处理 topology group，也没有本项目的 nominal anchor | 提供 trust-region 解释基础 |
| Achiam et al., **CPO**, ICML 2017 | 在策略更新中显式加入约束，并以 divergence 连接更新与性能界 | CPO 的 cost constraint 与本项目逐 topology-group 的训练 surrogate 不是同一对象 | 支持“普通收益方向 + 显式非伤害约束”的结构 |
| Wang et al., **Truly PPO**, UAI 2020 | PPO clipping 不会严格限制 probability ratio，也不构成严格 trust region | 其 rollback/clipping 仍不是逐组、cross-fitted 证书；本项目 KLR 已证明全局 rollback 不可靠 | 解释为什么必须检查实际逐组 policy KL |
| Sener & Koltun, **Multi-Task Learning as Multi-Objective Optimization**, NeurIPS 2018 | 多组目标可以写成低维约束优化，而不必手工设一组固定 loss weights | Pareto training loss 不自动保证 RL 长期/OOD return | 支持在 7 个组梯度张成的低维空间求最小修正 |
| Liu et al., **CAGrad**, NeurIPS 2021 | 平均目标与最差局部改善可联合考虑 | TCR 已覆盖简单 gradient surgery；CAGrad 本身不约束实际 per-group policy drift | 作为相邻方法和必要 comparator，不作为新方法本体 |
| Queeney et al., **Uncertainty-Aware Policy Optimization**, AAAI 2021 | 有限样本的策略梯度/曲率不确定性不应被当作确定真值 | 其不确定性模型不是为固定拓扑组和多智能体 failure strata 设计；当前每组 stream 数也不足以声称正式置信界 | 支持 design/certificate stream 分离，但 P0 不照搬其置信界 |
| Zhou et al., **MOAC**, ICML 2024 | 随机样本上反复求共同梯度会累积估计偏差 | 理论设置与当前 PPO/MARL 不同 | 警告不能把 noisy per-group gradient 当作确定真值；要求独立 certificate |
| Sagawa et al., **Group DRO**, ICLR 2020 | 最坏组目标需要配合正则化；训练组损失最优不等于最坏组泛化 | 监督学习 group shift 不能直接等同于 training-seed reliability | 支持固定组定义与保守验证，同时反对 naive worst-group reweighting |

## 与已有方法的边界

TGTR-PPO 不是 PCGrad/TCR：TCR 只在 nominal 与聚合 failure 梯度冲突时投影，且不检查每个 failure group 的完整策略分布移动。

TGTR-PPO 不是 group-weighted PPO：它不根据 difficulty 给 loss 乘连续权重，而是从 ordinary PPO 候选出发，仅在训练内证书显示具体组受伤时求最小修正。

TGTR-PPO 不是 KLR：KLR 以全 batch sampled-action KL 超阈值触发 actor rollback；TGTR-PPO 在提交 optimizer state 之前检查每组 full-categorical KL，并优先保留满足约束的最大非零、最接近 ordinary PPO 的更新。

TGTR-PPO 不是 PVF：训练和部署都只有一个 actor/critic，不在最终模型之间选择。

## 参考链接

- TRPO: https://proceedings.mlr.press/v37/schulman15.html
- CPO: https://proceedings.mlr.press/v70/achiam17a.html
- Truly PPO: https://proceedings.mlr.press/v115/wang20b.html
- Multi-task learning as multi-objective optimization: https://proceedings.neurips.cc/paper_files/paper/2018/hash/432aca3a1e345e339f35a30c8f65edce-Abstract.html
- CAGrad: https://proceedings.neurips.cc/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html
- Uncertainty-Aware Policy Optimization: https://ojs.aaai.org/index.php/AAAI/article/view/17130
- MOAC: https://proceedings.mlr.press/v235/zhou24h.html
- Group DRO: https://arxiv.org/abs/1911.08731
