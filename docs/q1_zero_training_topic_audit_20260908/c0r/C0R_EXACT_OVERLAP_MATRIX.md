# C0R 最近邻精确重叠矩阵

日期：2026-09-08

## 检索范围与限制

本轮围绕五个概念簇做定向检索：UAV 故障重构、信息新鲜度/AoI 调度、路由—任务联合优化、动态通信 MARL、部分可观测历史表征。优先采用出版社、会议论文集、PMLR 和 arXiv 原始页面。专用 academic-search MCP 在当前会话中不可用，因此本表不宣称系统综述或穷尽性；其用途是主动寻找足以压低候选新颖性的最近邻。

候选问题记为 IV-ASRS：动态拓扑故障下，联合决定主动感知（S）、有限容量路由/中继（R）与任务服务（S），并用信息新鲜度/来源有效性作为硬动作可行性条件，同时考虑切换或迁移代价。

## 精确重叠矩阵

| ID | 原始工作 | 状态/输入 | 决策变量 | 约束与目标 | 方法/理论 | 对 IV-ASRS 的覆盖 | 仍可能保留的差异 |
|---|---|---|---|---|---|---|---|
| N1 | Javad-Kalbasi & Valaee, *Re-configuration of UAV Relays in 6G Networks*, ICCW 2021, [DOI/IEEE](https://ieeexplore.ieee.org/document/9473723/) | UAV 多跳网络、链路故障、并发连接、有限链路容量 | 路由刷新、资源分配、连接迁移 | 降低中断和资源占用 | ILP；无中断迁移存在的充要条件 | 直接覆盖 UAV 故障、有限容量、路由刷新和 make-before-break 迁移 | 未把任务动作合法性绑定到信息新鲜度 |
| N2 | Yuan et al., *Toward resilient communication architecture: Online network reconfiguration for UAV failure*, Computer Networks 2025, [DOI](https://doi.org/10.1016/j.comnet.2025.111210) | UAV 故障、轨迹、连接和服务状态 | 在线轨迹与连接重构 | 保持覆盖/连接并控制移动和运行代价 | Lyapunov 在线优化 | 直接覆盖故障触发的在线 UAV 网络重构 | 未见来源有效性证书或硬任务动作门控 |
| N3 | Coletta et al., *A²-UAV: Application-Aware Resilient Edge-Assisted UAV Networks*, Computer Networks 2025, [出版社](https://www.sciencedirect.com/science/article/pii/S1389128624007199) | 多跳 UAV、带宽、位置、能量、CV 任务和节点故障 | 路由、数据预处理、目标分配 | 最大化正确完成的应用任务 | NP-hard；多项式算法；四机实测 | 极强覆盖“节点故障 + 应用任务 + 路由 + 目标分配”，且证据等级高 | 未以消息年龄/来源合法性定义硬动作可行集 |
| N4 | Hu et al., *Joint Trajectory Control, Frequency Allocation, and Routing for UAV Swarm Networks*, IEEE TMC 2024, [IEEE](https://ieeexplore.ieee.org/document/10535707/) | 动态拓扑、两跳邻居、链路稳定性、SINR、队列和能量 | 轨迹、频率、路由/中继选择 | 链路效用、时延、交付率和能耗 | LSTM actor + 多头 critic 的 MADRL | 覆盖动态图上的 UAV 路由—控制联合学习 | 未研究硬新鲜度证书和故障后可行性保持 |
| N5 | Liu et al., *Cooperative Data Collection With Multiple UAVs for Information Freshness in IoT*, IEEE TCOM 2023, [IEEE](https://ieeexplore.ieee.org/document/10065524/) | 多 UAV、局部传感器状态、能量和碰撞 | 轨迹、传输调度 | 最小平均 AoI，满足运动/能量/碰撞约束 | Dec-POMDP、CTDE MARL、动作掩码 | 覆盖多 UAV 主动采集、调度、AoI 与合法动作掩码 | 不含中继故障重构和任务服务门控 |
| N6 | Tolstaya et al., *Learning Connectivity for Data Distribution in Robot Teams*, IROS 2021, [arXiv](https://arxiv.org/abs/2103.05091) | 移动机器人拓扑、局部传输历史、信息年龄 | 何时向谁发送最新状态 | 降低团队 AoI/通信代价 | 分布式 GNN + RL，跨规模测试 | 覆盖机器人团队中主动通信、路由和新鲜度 | 任务无关；不把新鲜度作为服务动作硬约束 |
| N7 | Liu et al., *Aion: A Bandwidth Optimized Scheduler with AoI Guarantee*, INFOCOM 2021, [会议页面](https://infocom.info/infocom21/day/2) | 多源 AoI 阈值 | 周期调度与所需带宽 | 保证 AoI 并最小带宽 | FCD 结构下最优，一般情形有界 | 直接覆盖硬 AoI 约束、结构条件与理论保证 | 无 UAV 故障、路由迁移或应用动作 |
| N8 | Li et al., *Scheduling With Age of Information Guarantee*, IEEE/ACM ToN 2022, [DOI](https://doi.org/10.1109/TNET.2022.3156866) | 每源最大 AoI 阈值 | 可行调度 | 判断可调度性并构造调度 | 小规模精确 CSD；大规模 FPM 与负载保证 | 直接覆盖硬新鲜度可行性、证书与低复杂度算法 | 无拓扑重构和多阶段任务动作 |
| N9 | Li et al., *On Scheduling With AoI Violation Tolerance*, INFOCOM 2021, [论文](https://chengzhang17.github.io/files/Li21_INFOCOM_AoI.pdf) | AoI 截止、允许违约率和丢包率 | 源调度 | 判定可调度并满足违约约束 | 负载必要条件与调度构造 | 覆盖带丢包的新鲜度可靠性约束 | 无 UAV 主动路由/服务 |
| N10 | Tripathi, Talak & Modiano, *Information Freshness in Multi-Hop Wireless Networks*, [arXiv](https://arxiv.org/abs/2111.09217) | 多跳无线图和各节点信息年龄 | 调度与路由策略 | 最小 AoI | 随机、age-difference、age-debt 策略 | 覆盖多跳网络中新鲜度与路由调度耦合 | 无故障迁移和应用服务合法性 |
| N11 | Carpio et al., *Don’t interrupt me when you reconfigure my Service Function Chains*, Computer Communications 2021, [出版社](https://www.sciencedirect.com/science/article/abs/pii/S0140366421000712) | 容量网络、业务需求、SFC/VNF 状态 | 重路由、VNF 迁移 | make-before-break、不中断服务 | Break-Free ILP 与启发式 | 覆盖跨时隙迁移、容量预留和服务连续性 | 非 UAV；无 AoI 与感知动作 |
| N12 | Takahashi et al., *Jointly Determining SFC Routes and Update Scheduling with State Consistency*, IEICE 2024, [DOI](https://doi.org/10.23919/transcom.2023EBP3203) | SFC 路由、VNF 实例和状态一致性 | 路由及更新时序 | 避免迁移中的处理状态不一致 | 联合优化模型 | 覆盖“路径 + 状态有效性 + 更新顺序”结构 | 非机器人感知/任务服务语义 |
| N13 | Goeckner et al., *GNN-based MARL for Resilient Distributed Coordination of Multi-Robot Systems*, [arXiv](https://arxiv.org/abs/2403.13093) | 机器人图、agent attrition、通信扰动和部分可观测 | 分布式机器人动作 | 维持全局协同任务 | GNN + MAPPO，ROS2 仿真 | 覆盖通信扰动下图 MARL 鲁棒协同 | 不显式控制路由/新鲜度证书 |
| N14 | Weil et al., *Towards Generalizability of MARL in Graphs with Recurrent Message Passing*, AAMAS 2024, [论文](https://www.ifaamas.org/Proceedings/aamas2024/pdfs/p1919.pdf) | 多种图与局部图观测 | 分布式策略动作 | 跨图泛化和稀疏奖励任务 | recurrent message passing + RL | 覆盖动态图/跨图表征和递归消息传播 | 不处理 UAV 任务动作的硬信息合法性 |
| N15 | McClusky, *Dynamic Graph Communication for Decentralised MARL*, [arXiv](https://arxiv.org/abs/2501.00165) | 动态包路由网络和节点故障 | 通信目标/多轮传递 | 在节点故障下完成路由 | GAT + recurrent message passing | 直接覆盖节点故障、动态图和递归通信 MARL | 不含 UAV 应用服务和 AoI 硬约束 |
| N16 | Phan et al., *AERIAL*, ICML 2023, [PMLR](https://proceedings.mlr.press/v202/phan23a.html) | 随机部分可观测环境和多智能体历史 | 策略/价值学习 | 更准确表征分散决策历史 | recurrent memory + attention | 覆盖历史补偿随机部分可观测性 | 不控制网络重构或信息服务链 |
| N17 | Morad et al., *Graph-Based Memory and Topological Priors*, L4DC 2022, [PMLR](https://proceedings.mlr.press/v168/morad22a.html) | POMDP 历史与人工拓扑先验 | 控制策略 | 从历史形成上下文记忆 | graph convolutional memory | 覆盖“拓扑先验 + 历史记忆”方法空间 | 不含主动网络/服务决策 |
| N18 | Zhang et al., *Succinct and Robust Multi-Agent Communication With Temporal Message Control*, NeurIPS 2020, [论文](https://papers.nips.cc/paper/2020/hash/c82b013313066e0702d58dc70db033ca-Abstract.html) | 消息历史、发送价值和丢包 | 何时通信 | 降低通信量并抵抗传输损失 | temporal smoothing/message control | 覆盖通信时序控制和丢包鲁棒性 | 不含拓扑故障重构和任务可行性证书 |
| N19 | Wang et al., *Learning Efficient Multi-agent Communication: An Information Bottleneck Approach*, ICML 2020, [PMLR](https://proceedings.mlr.press/v119/wang20i/wang20i.pdf) | 局部状态、有限带宽 | 消息内容、发送者、接收者和调度 | 任务性能—通信代价权衡 | 信息瓶颈与权重调度器 | 覆盖有限带宽下通信对象/内容/时序联合学习 | 不处理故障迁移和硬新鲜度动作门控 |
| N20 | Sebastian et al., *Physics-Informed MARL for Distributed Multi-Robot Problems*, IEEE T-RO 2025, [arXiv](https://arxiv.org/abs/2401.00212) | 时变交互图和局部机器人状态 | 分布式物理控制 | 可扩展协同与通信缺陷鲁棒性 | port-Hamiltonian actor + attention SAC | 覆盖时变图、跨规模和真实/Robotarium 级验证 | 不控制信息路由或服务合法性 |
| N21 | You et al., *Dynamic Communication in MARL via Information Bottleneck*, GLOBECOM 2024, [IEEE](https://ieeexplore.ieee.org/document/10901017/) | 移动智能体和动态通信可达性 | 通信压缩/交互 | 降低通信开销并保持任务性能 | 多平均场 MARL + 信息瓶颈 | 覆盖动态拓扑通信学习 | 不含硬新鲜度、迁移和任务可行性 |
| N22 | *JCAS-MARL: Joint Communication and Sensing UAV Networks via Resource-Constrained MARL*, 2026 preprint, [arXiv](https://arxiv.org/abs/2603.20265) | UAV 动态图、感知、通信、能量 | 轨迹与感知/通信资源 | 感知—通信—能量权衡 | 资源约束 MARL | 覆盖 UAV 主动感知—通信联合学习 | 尚未覆盖故障迁移与来源有效性硬门控；预印本状态 |
| N23 | *Quick Gateway Switching for Reliable Data Collection in Multi-Gateway UAV Networks With Gateway Failures*, IEEE TVT 2026, [IEEE](https://ieeexplore.ieee.org/document/11159168/) | 多网关 UAV、网关故障、邻居发现 | 网关切换和链路层路由 | 降低切换时延、丢包，提高吞吐 | 系统协议与室内/室外实验 | 覆盖故障后的快速路径切换和真实系统证据 | 不联合任务服务或 AoI 约束 |

## 攻击性综合判断

没有单篇工作逐字覆盖 IV-ASRS 的全部交集，但这不足以形成一区新颖性：

1. N1、N2、N3、N4 已覆盖 UAV 故障后的路由、连接、任务和资源联合重构；
2. N7–N10 已覆盖硬信息新鲜度的可行性、调度与理论保证；
3. N11–N12 已覆盖状态保持、make-before-break 和更新时序；
4. N13–N22 已覆盖动态图、部分可观测、主动通信、感知—通信联合学习和跨规模图 MARL。

候选当前唯一未被直接完整覆盖的表述是“将来源/新鲜度证书作为 UAV 任务动作的硬合法性条件”。但它目前只是一种约束建模选择；若不能产生新的结构定理、可行性证书或算法界，就属于已有模块的组合，而不是一区级方法缺口。
