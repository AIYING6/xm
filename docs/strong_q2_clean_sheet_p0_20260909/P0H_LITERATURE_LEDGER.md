# P0H 文献台账：新课题最近邻与排除性证据

本台账用于零训练选题排重，不是论文最终参考文献表。预印本与同行评议论文分开解释；当前检索未支持任何“首次提出”表述。

| 文献簇 | 代表性原始来源 | 已覆盖内容 | 对 P0H 的约束 |
|---|---|---|---|
| 公共知识与分散协调 | Schroeder de Witt et al., *Multi-Agent Common Knowledge Reinforcement Learning*, NeurIPS 2019, [proceedings](https://papers.neurips.cc/paper_files/paper/2019/hash/f968fdc88852a4a3a27a81fe3f57bfc5-Abstract.html) | 用可重建的 common knowledge 驱动分层联合策略 | “公共知识有用”不是新颖性；新课题必须处理公共知识无法可靠形成的情形 |
| 不可靠通信的公共知识极限 | Klein and Rendsvig, *Converging on Common Knowledge*, IJCAI 2019, DOI 10.24963/ijcai.2019/241, [proceedings](https://www.ijcai.org/proceedings/2019/241) | 说明不可靠通信下有限时间公共知识的根本困难 | 支持构造 epistemic coordination 反例，但不直接提供学习算法 |
| 不一致信念与动作一致性 | *Towards Optimal Performance and Action Consistency Guarantees in Dec-POMDPs with Inconsistent Beliefs and Limited Communication*, arXiv:2512.20778, [preprint](https://arxiv.org/abs/2512.20778) | 显式处理不一致 belief、动作一致性保证和选择性通信 | 是候选一的最强直接近邻；若无法给出不同的执行语义或理论对象，候选一必须关闭 |
| 有成本的信息请求 | *Asking for Information by Evaluating the Communication and Coordination Trade-Off in Multi-Agent POMDPs*, IEEE RA-L 2026, DOI 10.1109/LRA.2026.3703246, [publisher](https://doi.org/10.1109/LRA.2026.3703246) | 在 Dec-POMDP 中评估通信价值并决定是否请求信息 | 排除“何时通信/请求信息”作为新决策对象 |
| 有噪信道联合通信学习 | Kilinc and Montana, *Effective Communications*, arXiv:2101.10369, [preprint](https://arxiv.org/abs/2101.10369) | 将消息纳入动作并联合建模 noisy channel | 排除简单 learned communication protocol |
| 开放团队 | Rahman et al., *Towards Open Ad Hoc Teamwork Using Graph-based Policy Learning*, ICML 2021, [PMLR](https://proceedings.mlr.press/v139/rahman21a.html) | 用 GNN 适应成员动态加入/离开 | 排除“动态图团队 + GNN”本身 |
| 开放团队理论 | Wang et al., *Open Ad Hoc Teamwork with Cooperative Game Theory*, ICML 2024, [PMLR](https://proceedings.mlr.press/v235/wang24an.html) | 从合作博弈解释开放团队联合价值表示 | 候选若处理 team composition，必须超过表示层变化 |
| 突发队友策略变化 | Zhang et al., *Fast Teammate Adaptation in the Presence of Sudden Policy Change*, UAI 2023, [PMLR](https://proceedings.mlr.press/v216/zhang23a.html) | episode 内识别并适应队友策略突变 | 排除普通 context inference / fast adaptation |
| 未见故障恢复 | Findik et al., *Collaborative Adaptation for Recovery from Unforeseen Malfunctions*, CDC 2024, DOI 10.1109/CDC56724.2024.10885831, [publisher](https://ieeexplore.ieee.org/document/10885831/) | 利用 agent 关系加速离散与连续域故障恢复 | 候选二不能只声称“适应未见故障” |
| 连续域关系式恢复 | Findik et al., *Relational Q-Functionals*, arXiv:2407.19128, [preprint](https://arxiv.org/abs/2407.19128) | 用关系网络处理连续动作域的未知故障 | 排除关系编码作为核心创新 |
| 崩溃率课程 | Zhao et al., *Coach-assisted MARL Framework for Unexpected Crashed Agents*, arXiv:2203.08454, [preprint](https://arxiv.org/abs/2203.08454) | 自适应崩溃率训练与重采样 | 与 DRTP 类暴露分配高度邻近，永久排除 |
| 分散 world model | Zeng and Zhang, *Efficient Information Sharing for Training Decentralized Multi-Agent World Models*, RLC 2025, [paper page](https://rlj.cs.umass.edu/2025/papers/Paper103.html) | 带宽约束下训练分散 world model | “分散 world model + 重要信息共享”不是空白 |
| 多智能体 transformer world model | Deihim et al., *Transformer World Model for Sample Efficient MARL*, arXiv:2506.18537, [preprint](https://arxiv.org/abs/2506.18537) | 分散 imagination、队友预测与优先经验 | 候选二必须围绕可证伪的 graph intervention，而非模型架构 |
| 遮蔽重建部分观测 | Kang et al., *MA2E*, ICLR 2025, [proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33301bb40020a56ef56b8b5081e5c4d5-Abstract-Conference.html) | 从局部观测重建全局信息 | 排除“恢复隐藏全局状态”作为主张 |
| 主动分布外检测 | Sontakke et al., *GalilAI*, AISTATS 2022, [PMLR](https://proceedings.mlr.press/v151/sontakke22a.html) | 通过主动实验识别任务分布变化 | 与已停止的 active diagnosis 紧邻，不再启动 |
| 主动通信防御 | Yu et al., *Robust Communicative MARL with Active Defense*, AAAI 2024, DOI 10.1609/aaai.v38i16.29708, [proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/29708) | 估计消息可靠性并降低可疑消息影响 | 排除通用 trust weighting / message filtering |
| 可认证对抗通信鲁棒性 | Sun et al., *Certifiably Robust Policy Learning against Adversarial Multi-Agent Communication*, ICLR 2023, [OpenReview](https://openreview.net/pdf?id=dCOL0inGl3e) | 对对抗消息提供认证鲁棒性 | Byzantine/对抗通信方向需要新的威胁模型和更强理论，性价比低 |
| Byzantine cooperative MARL | Li et al., *Byzantine Robust Cooperative MARL as a Bayesian Game*, arXiv:2305.12872, [preprint](https://arxiv.org/abs/2305.12872) | Bayesian adversarial Dec-POMDP、类型 belief 与鲁棒均衡 | 排除“belief + Byzantine type”作为新组合 |
| UAV Byzantine MARL | *Robust Multiagent Reinforcement Learning for UAV Systems: Countering Byzantine Attacks*, Information 2023, DOI 10.3390/info14110623, [publisher](https://www.mdpi.com/2078-2489/14/11/623) | UAV 场景中的几何中值共识和鲁棒状态更新 | UAV + Byzantine 已有直接近邻 |
| 异步多机器人 MARL | Xiao et al., *Asynchronous Multi-Agent Deep Reinforcement Learning under Partial Observability*, IJRR 2025, DOI 10.1177/02783649241306124, [publisher](https://journals.sagepub.com/doi/10.1177/02783649241306124) | 用 macro-action Dec-POMDP 处理异步长时动作 | 排除“异步宏动作”本身；候选若用 option，必须服务于独立的新问题 |
| 安全 shield | Cai et al., *Safe MARL through Decentralized Multiple Control Barrier Functions*, arXiv:2103.12553, [preprint](https://arxiv.org/abs/2103.12553) | 基于局部信息的分散 CBF shield | 候选三不能仅把 CBF 接到 MARL 上 |
| 多层优雅降级 | D'Ippolito et al., *Robust Degradation and Enhancement of Robot Mission Behaviour in Unpredictable Environments*, 2015, [paper](https://cs.unibg.it/esecfse_proceedings/fsews15ctse/p26-dippolito.pdf) | 任务要求不可满足时切换到可保证的较低服务层 | “优雅降级”已有形式化传统；必须加入新的学习/可识别对象 |

## 检索结论边界

1. 开放团队、Byzantine 防御、故障恢复、world model、通信请求、公共知识和优雅降级均不是空白领域。
2. 当前只发现一个仍可能形成新问题的窄交叉点：**通信故障造成的 epistemic mismatch 如何影响具身团队承诺，以及在通信无法保证可用时如何学习可验证的 commit/defer/fallback 决策。**
3. 该交叉点受到 arXiv:2512.20778 的直接压力，不能在未完成全文级差异审计前宣布新颖性。

