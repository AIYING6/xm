# 09 核心引用核验账本

**检索日期：** 2026-08-27

**检索范围：** 不限定 CNS；优先原始算法论文、官方会议/期刊页面和 DOI 元数据。

**用途：** 本文件是中文稿的核心引用账本，用于约束每条文献支撑的论断。`main_zh.md` 已纳入 16 条真实参考文献；目标期刊确定后仅调整格式，不删除或伪造条目。

## 1. 已核验核心文献

| ID | 文献 | 主要支撑位置 | 支撑等级 | 允许表述 | 不允许表述 |
|---|---|---|---|---|---|
| R1 | Yu C, Velu A, Vinitsky E, et al. *The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games*. NeurIPS 2022, 35. DOI: 10.52202/068431-1787. | MAPPO/合作 MARL 基础 | 强支撑 | MAPPO 是合作 MARL 的强基线；实现细节影响性能 | MAPPO 在本文任务中必然最优 |
| R2 | Veličković P, Cucurull G, Casanova A, et al. *Graph Attention Networks*. ICLR 2018. | GAT 消息聚合基础 | 强支撑 | GAT 可对图邻居学习不同注意权重 | GAT 本身解决拓扑故障鲁棒性 |
| R3 | Lou X, Zhang J, Norman T J, et al. *TAPE: Leveraging Agent Topology for Cooperative Multi-Agent Policy Gradient*. AAAI 2024, 38(16):17496–17504. DOI: 10.1609/aaai.v38i16.29699. | 拓扑感知策略梯度定位 | 部分支撑 | 智能体拓扑可影响合作策略梯度和协同 | TAPE 与 DRTP 是同合同公平对比方法 |
| R4 | Li S, Wu Y, Cui X, et al. *Robust Multi-Agent Reinforcement Learning via Minimax Deep Deterministic Policy Gradient*. AAAI 2019, 33(1):4213–4220. DOI: 10.1609/aaai.v33i01.33014213. | 鲁棒 MARL 背景 | 背景支撑 | MARL 策略可能对训练伙伴/环境变化敏感；minimax 是一类鲁棒路线 | M3DDPG 直接解决本文的中继拓扑扰动 |
| R5 | Liu Z, Bai Q, Blanchet J, et al. *Distributionally Robust Q-Learning*. ICML 2022, PMLR 162:13623–13643. | 分布鲁棒强化学习知识基础 | 背景支撑 | 分布鲁棒 RL 可针对环境分布扰动优化最坏分布下策略 | DRTP 具有该文的理论收敛保证 |
| R6 | Zhao B, Huo M, Li Z, et al. *Graph-based multi-agent reinforcement learning for collaborative search and tracking of multiple UAVs*. Chinese Journal of Aeronautics, 2025, 38(3):103214. DOI: 10.1016/j.cja.2024.08.045. | 图结构无人机 MARL | 强背景支撑 | GNN/GAT 已用于动态未知环境中的多无人机协同搜索跟踪 | 本文仅因使用图网络即具有充分创新性 |
| R7 | Zhao B, Huo M, Li Z, et al. *Graph-based multi-agent reinforcement learning for large-scale UAVs swarm system control*. Aerospace Science and Technology, 2024, 150:109166. DOI: 10.1016/j.ast.2024.109166. | 大规模无人机图 MARL | 背景支撑 | 图表示和局部信息已用于无人机集群运动控制 | 本文已经证明规模扩展 |
| R8 | Lv Z, Xiao L, Du Y, et al. *Multi-Agent Reinforcement Learning Based UAV Swarm Communications Against Jamming*. IEEE Transactions on Wireless Communications, 2023, 22(12):9063–9075. DOI: 10.1109/TWC.2023.3268082. | 通信扰动下无人机 MARL | 部分支撑 | MARL 已用于干扰条件下的中继选择和功率分配 | 抗干扰通信等同于中继节点故障后的任务协同 |
| R9 | Bai H, Wang H, He R, et al. *Multi-hop UAV relay covert communication: A multi-agent reinforcement learning approach*. Chinese Journal of Aeronautics, 2025, 38(10):103440. DOI: 10.1016/j.cja.2025.103440. | 多跳中继与 MAPPO 应用 | 部分支撑 | MAPPO 已用于多跳无人机中继通信的轨迹与功率联合决策 | 该文验证了本文的拓扑路径鲁棒性 |
| R10 | Schulman J, Wolski F, Dhariwal P, et al. *Proximal Policy Optimization Algorithms*. arXiv:1707.06347, 2017. | PPO 裁剪目标与训练设置 | 强支撑 | PPO 的裁剪策略优化是本文共同训练器的直接来源 | PPO 自动保证多智能体或拓扑鲁棒性 |
| R11 | Sagawa S, Koh P W, Hashimoto T B, Liang P. *Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization*. ICLR 2020. | 组鲁棒重加权定位 | 背景支撑 | 预定义组的最坏组/重加权思想可作为 DRTP 的知识背景 | DRTP 等价于 group DRO，或获得其理论保证 |
| R12 | Mehta B, Diaz M, Golemo F, et al. *Active Domain Randomization*. CoRL 2020, PMLR 155:1162–1176. | 自适应场景参数采样定位 | 部分支撑 | 训练期可根据学习过程选择环境参数/场景 | DRTP 与该方法使用同一目标或同一采样器 |
| R13 | Narvekar S, Peng B, Leonetti M, et al. *Curriculum Learning for Reinforcement Learning Domains: A Framework and Survey*. JMLR, 2020, 21(181):1–50. | 训练分布/课程术语背景 | 背景支撑（综述） | 训练任务分布与任务序列会影响 RL 优化过程 | 该综述直接证明 DRTP 的性能优势 |
| R14 | Lowe R, Wu Y, Tamar A, et al. *Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments*. NeurIPS 2017, 30. arXiv:1706.02275. | CTDE 与执行信息边界 | 强背景支撑 | actor 可在执行期只用局部信息，而 critic 可在训练期使用额外信息 | 本文的 CTDE 设置必然保证拓扑鲁棒性 |
| R15 | Luo J, Wang Z, Xia M, et al. *Path Planning for UAV Communication Networks: Related Technologies, Solutions, and Opportunities*. ACM Computing Surveys, 2023, 55(9):1–37. DOI: 10.1145/3560261. | UAV 通信拓扑、节点失效与重组背景 | 背景支撑（综述） | 多无人机通信网络可在链路/节点失效后重构路径或拓扑 | 该综述验证本文的任务奖励、策略或数值优势 |
| R16 | Xiao H, Yang Y, Yu D, et al. *3D Self-Triggered-Organized Communication Topology Based UAV Swarm Consensus System With Distributed Extended State Observer*. IEEE TNSE, 2025, 12(5):3985–4000. DOI: 10.1109/TNSE.2025.3567462. | UAV 单元失效下的通信拓扑改变 | 强背景支撑 | UAV 单元失效/损失可造成需要重构的通信拓扑改变 | 共识控制结论可直接迁移为本文 MARL 性能保证 |

## 2. 正文引用映射

| 正文论断 | 建议引用 | 说明 |
|---|---|---|
| MAPPO 是合作 MARL 的有效基础 | R1 | 原始 MAPPO 经验研究 |
| 图注意力可按邻接关系聚合并学习邻居权重 | R2 | 原始 GAT 论文 |
| 智能体拓扑可进入多智能体策略优化 | R3 | 与本文有关，但优化对象不同 |
| 鲁棒 MARL 研究策略对训练伙伴或环境变化的敏感性 | R4 | 仅作鲁棒 MARL 背景 |
| 分布鲁棒 RL 优化分布扰动下的策略 | R5 | 不把理论保证迁移到 DRTP |
| GNN/GAT 已进入多无人机协同与集群控制 | R6、R7 | 支撑“使用图本身不足以构成创新” |
| 通信干扰、多跳中继和轨迹/功率联合决策已有 MARL 研究 | R8、R9 | 支撑应用背景和区别，不作直接性能基线 |
| PPO 裁剪目标与共同优化器 | R10 | 说明两种方法采用相同 PPO 训练器 |
| 组重加权与自适应采样的知识来源 | R11、R12 | 仅作方法定位，不转移理论保证 |
| 训练分布会影响强化学习优化过程 | R13 | 综述性术语背景，不作为性能因果证据 |
| CTDE 下 actor 的执行信息边界 | R14 | 只支撑一般训练/执行范式，不证明本文环境语义 |
| UAV 节点故障与通信拓扑重组的工程背景 | R15、R16 | 不作为当前任务或算法的性能对照 |

## 3. 投稿前可选补充

- 目标中文期刊近 3–5 年的高度相关论文，用于投稿定位；
- 作者选定目标期刊后的格式化引用、中文网络首发页码及其近年专题文献。

这些属于期刊适配，而不是本稿主张成立的前置条件。新增条目必须逐条写明支撑位置和不可推断的结论，不能为增加引用数量而堆砌无关文献。

## 4. 引用纪律

- 每篇文献只支撑其实际研究范围内的论断；
- 不用标题相关性代替摘要或正文核验；
- 不把 R3–R9 写成已在本文合同下被 DRTP 击败的外部基线；
- 不把 R5 的 Q-learning 理论保证移植到 DRTP；
- 不使用“首次”或“尚无研究”等排他性措辞，除非完成可复核的系统检索；
- 主稿已采用顺序编码 `[1]--[16]`；投稿前只按目标期刊的标点、作者截断和刊名格式做机械转换。
