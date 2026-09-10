# P12 开放集团队战术响应 Stage-0 结果

## 判定

`DEVELOPMENT_PROTOTYPE_STOP / TOPIC_NOT_FROZEN / NO_TRAINING`

本轮按照“普通但可靠的中科院二区贡献”标准，不再要求顶级理论创新。候选问题是：在 3v3 双目标无人机对抗任务中，根据对手可观测行为从冻结团队战术库中选择响应，并以 response regret 衡量测试时无梯度适应。

## 最近邻边界

公开研究已经覆盖 opponent modeling、未见对手适应、策略复用和层级响应。P12 不主张这些概念首次出现。若后续成立，最低可发表差异只能是：团队级 UAV 战术响应、开放集与回合内切换评价、冻结响应库上的 response regret，以及不依赖测试时梯度更新的选择。

主要近邻包括：

- Vezhnevets et al., *OPtions as REsponses*（ICML 2020）；
- Yu et al., *Model-Based Opponent Modeling*（NeurIPS 2021）；
- Huang et al., *Hierarchical Opponent Modeling and Planning*（ICML 2024）；
- Wang et al., *Generalizable Agent Modeling for Agent Collaboration-Competition Adaptation*（arXiv 2025）。

## Stage-0 设计

- 96 个随机初始几何；
- 4 类红方战术 × 4 类蓝方团队响应；
- 1,536 条无训练 counterfactual cross-play；
- 所有组合共享运动速度、交战半径、目标判定和任务效用；
- 红方标签、未来动作和反事实结果均不进入可部署观测；
- 环境步数与 PPO 更新数均为 0。

## 结果

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| 不同最佳响应数 | 1 | ≥3 | FAIL |
| 单一响应占优比例 | 100% | ≤60% | FAIL |
| oracle 相对最佳静态响应增益 | 0.000 | ≥0.080 | FAIL |
| 具有明确响应 margin 的战术数 | 1 | ≥3 | FAIL |
| 决策时刻之前未终止比例 | 100% | ≥95% | PASS |

`split_screen` 对 left-mass、right-mass、split-raid 和 feint-switch 均为最佳响应。当前简化动力学采用统一的对称接触交换规则，均匀分区防守因而成为通用解，任务没有形成测试时选择需求。

## 科学处理

这不是正式 OSTA 结果，也不否定开放集 UAV 对抗适ौती的研究方向；它否定的是当前双目标原型。不得在该原型上训练选择器，也不得通过修改评价权重或挑选战术制造互补性。

下一次环境开发若继续，必须先改变真实动力学表达能力，而不是调结果：至少加入交战几何、速度/航向优势、目标时窗或弹药/再交战约束中的一种，使“集中拦截、分区防守、机动预备队”承担真实且不同的机会成本。新原型仍须使用独立初始场景和同样的 Stage-0 门；通过前不冻结论文题目。

## 证据

- `configs/p12_open_set_tactical_response_stage0_20260910.json`
- `scripts/p12_open_set_tactical_response_stage0.py`
- `artifacts/diagnostics/p12_open_set_tactical_response_stage0_20260910/P12_STAGE0_RESULT.json`
- `artifacts/diagnostics/p12_open_set_tactical_response_stage0_20260910/P12_STAGE0_CROSSPLAY.csv`
