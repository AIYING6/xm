# P9-A CRE 最近邻与解析反例审查

**结论：** `CRE_TOPIC_STOP_NEAREST_NEIGHBOR_OVERLAP`  
**训练：** 未授权，环境步数 0，PPO 更新 0。

## 1. 双门结果

| 门 | 结果 | 证据 |
|---|---|---|
| 解析可识别性 | PASS | `P9A_CRE_ANALYTIC_RESULT.json`；在相同信息与动作集下，posterior-mean 选择 `attack`、maximin-value 选择 `screen`、minimax-regret 选择 `split`；最坏后悔分别为 5、5、3 |
| 最近邻非重合 | **FAIL** | 2026 年预印本 *Beyond Bayesian Nash: Learning Minimax-Regret Equilibria for Adversarial Team Games under Asymmetric Information* 已直接研究非对称信息对抗团队博弈中的 minimax-regret equilibrium，并以 robust double-oracle/PSRO 学习策略 |

解析反例说明 minimax regret 与后验均值及 maximin value 可以产生严格不同的决策，因此问题具有数学可识别性。但这不能抵消核心优化对象已被直接近邻覆盖的事实。

## 2. 最近邻差异矩阵

| 最近邻 | 已覆盖内容 | CRE 尚可声称的差异 | 是否足以支撑强二区新核 |
|---|---|---|---|
| Rigter et al., AAAI 2021 | 不确定 MDP 上的 minimax-regret 规划与 Bellman 递推 | 多无人机团队与对手策略版本空间 | 否，仅应用化 |
| Xu et al., UAI 2021 | 不确定攻击者模型下的 minimax-regret robust RL | 连续团队战术与动作条件响应预测 | 否，仍是领域/实现差异 |
| *Beyond Bayesian Nash*, arXiv 2026 | 非对称信息 adversarial team games、隐藏对手类型、minimax-regret equilibrium、population-based learning | UAV 动力学、连续控制、有限时域响应包络 | **不足**；问题、准则和博弈结构均高度接近 |
| GSCU, ICML 2022 | 未知和非平稳对手的潜变量推断及保守/贪婪策略切换 | set-valued regret 而非点潜变量 | 单独看有差异，但被上述 minimax-regret team-game 工作覆盖 |
| HSVI for POSGs, L4DC 2024 | 部分可观测随机博弈的在线 minimax 求解 | 学习式动作响应包络 | 算法工程差异，不构成独立问题 |

## 3. 为什么现在停止是正确的

若继续，论文最可能退化为“把 minimax-regret adversarial team game 应用于多无人机，并用神经响应模型近似”。这可能形成一篇应用论文，但不满足本项目已经冻结的强二区要求：新方法不能只是既有决策准则的 UAV 实现，也不能依赖更复杂环境掩盖理论对象重合。

因此不通过以下方式挽救：

- 不把 CRE 改名后继续；
- 不用“连续动作”“3DOF”“多无人机”宣称算法创新；
- 不立即添加 conformal prediction、transformer 或 world model 堆叠差异；
- 不启动小试验寻找好看的性能结果。

## 4. 对后续选题的新增硬约束

P9 证明，仅有严格反例仍不够。下一个题必须先通过“核心数学对象检索”，再设计方法。下一轮不再以 opponent model、belief、minimax、regret、PSRO、hierarchical policy 或 target assignment 作为创新名词。候选必须改变至少一个更基础的研究对象，例如：

1. 可验证的团队策略契约或运行时保证；
2. 学习系统与飞行动力学/实时计算之间的闭环资源约束；
3. 多任务、多载荷或开放团队中的可组合能力接口；
4. 仿真到现实可测偏差下的任务级保证。

下一阶段为 `P10_PROBLEM_FIRST_LANDSCAPE`：先选真实未解决问题与可验证端点，再决定是否需要 MARL；仍不训练。

## 5. 可复核资产

- 选题卡：`docs/strong_q2_clean_sheet_p0_20260909/P9_CLEAN_SHEET_ADVERSARIAL_TOPIC_SELECTION_20260910.md`
- 解析脚本：`scripts/p9a_cre_analytic_counterexample.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P9A_CRE_ANALYTIC_RESULT.json`
- 冻结合同：`configs/p9_cre_topic_gate_20260910.json`

