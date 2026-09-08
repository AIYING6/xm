# P0C：TIV 最近邻精确重叠矩阵

## 检索说明

检索覆盖 CrossRef/arXiv 可发现论文、出版社页面、IEEE/PMLR/AAAI 页面及作者公开稿。OpenAlex 无 MCP 回退脚本在本轮触发 HTTP 429，故继续使用已返回的出版社和原始论文页面。本表为选题否证用近邻矩阵，不宣称系统综述。

| ID | 工作 | 任务/状态 | 决策或证书 | 理论/证据 | 与 TIV 的直接重叠 | 剩余差异是否足以立项 |
|---|---|---|---|---|---|---|
| N1 | Ercetin et al., [Consolidate Viability and Information Theories for Task-Oriented Communications](https://arxiv.org/abs/2311.14917) | actor 目标、可行空间、信息流 | 按目标分配最低必要通信资源 | viability theory + transfer entropy | 直接把 viability 与 task-oriented communication 合并 | 否；TIV 高层概念已被覆盖 |
| N2 | Mostaani et al., [Task-Oriented Communication Design survey](https://orbilu.uni.lu/handle/10993/53991) | cyber-physical task 效果 | task-effective communication | 跨领域理论综述 | 覆盖“通信价值由任务决定” | 否；来源合法性只是更具体约束 |
| N3 | Soleymani et al., [Value of Information in Feedback Control](https://arxiv.org/abs/1812.07534) | 控制估计状态和包价值 | 发送/不发送 | VoI 阈值及性能保证 | 覆盖信息对未来控制价值 | 部分；不含多角色路径，但不能靠组合立项 |
| N4 | Zhang et al., [VIL2C](https://ojs.aaai.org/index.php/AAAI/article/view/40234) | MARL 延迟消息和任务回报 | VoI 资源分配与接收时长 | 理论优势 + 多场景实验 | 覆盖低时延任务价值通信 | 部分；不含 UAV 故障来源约束 |
| N5 | Kantaros et al., [Temporal Logic Task Planning and Intermittent Connectivity](https://arxiv.org/abs/1706.00765) | LTL 任务、通信会合 | 任务轨迹和通信事件 | 分散规划与正确性 | 覆盖任务、时间和未来通信机会 | 强；TIV 可被其形式语言编码 |
| N6 | Liu et al., [Communication-aware Motion Planning from STL](https://arxiv.org/abs/1705.11085) | 动力学、STL、无线 QoS | 连续运动 | MILP/控制综合 | 覆盖动作相关通信与任务完成 | 强 |
| N7 | Silva et al., [Probabilistic Multi-Robot Planning with Temporal Tasks and Communication Constraints](https://labs.sciety.org/articles/by?article_doi=10.21203%2Frs.3.rs-6649588%2Fv1) | 随机运动、时序任务、通信要求 | 未来会合与路径 | 风险约束规划 | 覆盖概率 TIV 的主要量词 | 强 |
| N8 | [CoCoPlan](https://ieeexplore.ieee.org/document/11361077/) | 动态任务与有限通信 | 联合任务计划和团队通信事件 | branch-and-bound + 硬件实验 | 覆盖任务完成前的通信机会联合设计 | 强，且证据上限高 |
| N9 | Cumberland et al., [Epistemic Planning for Multi-Robot Systems](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2023.1149439/full) | 机器人知识、断连和任务分配 | gossip 通信任务与执行计划 | epistemic state + heuristic | 覆盖“机器人必须知道任务信息才可执行” | 极强；分散 TIV 接近其问题结构 |
| N10 | Tardioli et al., [Enforcing Network Connectivity in Robot Team Missions](https://journals.sagepub.com/doi/10.1177/0278364909358274) | 任务、无线网络与运动 | 连通控制和任务分配 | 完整机器人系统 | 覆盖运动—通信—任务耦合 | TIV 可区别全连通，但不足以单独立项 |
| N11 | Yan & Mostofi, [Communication-Aware Robotics](https://www.annualreviews.org/content/journals/10.1146/annurev-control-071420-080708) | 真实信道、运动和信息流 | 运动—通信协同 | 理论综述与最优性保证 | 覆盖用运动塑造未来通信机会 | 强 |
| N12 | Kumar et al., [Minimally Disruptive Connectivity Enhancement](https://ieeexplore.ieee.org/document/9340733/) | 机器人任务和连接需求 | 最小扰动重构 | 可证明满足一般连接需求 | 覆盖保持任务同时恢复网络性质 | TIV 可换需求谓词，结构仍相似 |
| N13 | Capelli et al., [Decentralized Connectivity Maintenance with Time Delays using CBFs](https://arxiv.org/abs/2103.12614) | 分散位置与通信延迟 | 物理控制 | CBF + 实机 | 覆盖局部控制证书 | TIV 不是连通 CBF，但 learned barrier 不新 |
| N14 | Garg et al., [Learning Safe Control for Multi-Robot Systems](https://doi.org/10.1016/j.arcontrol.2024.100948) | 多机器人安全/可达集合 | shield、CBF、HJ、MARL | 系统综述 | 覆盖 viability/certificate 方法族 | 强 |
| N15 | Tarasyuk et al., [Modelling Resilient Collaborative Multi-Agent Systems](https://link.springer.com/article/10.1007/s00607-020-00861-2) | 故障、协作活动和系统目标 | 形式化恢复机制 | Event-B 验证 | 覆盖故障下协作可完成性的形式化 | 中强 |
| N16 | Lauri et al., [Multi-Robot Active Information Gathering](https://ieeexplore.ieee.org/document/7989104/) | 周期通信、目标跟踪 belief | 信息获取动作 | Dec-POMDP + 真实任务 | 覆盖主动信息机动 | TIV 的硬合法性不同，但非独立方法核心 |
| N17 | Tolstaya et al., [Learning Connectivity for Data Distribution](https://arxiv.org/abs/2103.05091) | 移动图、局部历史与 AoI | 发送对象和运动相关通信 | 分布式 GNN-RL | 覆盖信息新鲜度和机器人网络 | 中强 |
| N18 | Liu et al., [Multi-UAV Information Freshness](https://ieeexplore.ieee.org/document/10065524/) | UAV 轨迹、能量、AoI | 轨迹和调度 | Dec-POMDP/MARL | 覆盖 UAV 主动运动和新鲜度 | 强 |
| N19 | Li et al., [Scheduling With AoI Guarantee](https://doi.org/10.1109/TNET.2022.3156866) | 硬 AoI 阈值 | 可行调度 | 可调度性判据与算法 | 覆盖年龄约束可行域 | TIV 添加任务/来源，但组合不足 |
| N20 | Coletta et al., [A²-UAV](https://www.sciencedirect.com/science/article/pii/S1389128624007199) | UAV 节点故障、应用任务和资源 | 路由、预处理、目标分配 | NP-hard、算法、四机实验 | 覆盖故障下任务相关信息服务 | 极强系统近邻 |
| N21 | Weil et al., [Recurrent Message Passing for MARL Graph Generalization](https://www.ifaamas.org/Proceedings/aamas2024/pdfs/p1919.pdf) | 局部/陈旧动态图观测 | recurrent graph policy | 1000 图实验 | 覆盖动态图部分可观测学习 | 排除 RNN/GNN 作为 TIV 核心 |
| N22 | Lee et al., [Communicating Unexpectedness](https://arxiv.org/abs/2501.01140) | OOD 动态环境与预测误差 | unexpectedness 消息 | MARL 实验 | 覆盖故障/变化后的信息适应 | 排除预测误差通信换名 |
| N23 | Javad-Kalbasi & Valaee, [Re-configuration of UAV Relays](https://ieeexplore.ieee.org/document/9473723/) | UAV 中继故障、容量和路由 | 刷新与无中断迁移 | ILP 和充要条件 | 覆盖故障后信息路径恢复 | 排除重新加入路由/迁移逃避重叠 |

## 矩阵结论

没有单篇工作逐字段等同于“异构 UAV 的来源合法、时效约束 TIV”，但一区新颖性不能来自未被单篇论文同时写出的概念交集。N1 已直接覆盖 viability + task-oriented communication 的高层思想；N5–N9 覆盖任务、未来通信机会和知识状态；N10–N19 覆盖通信感知运动、证书、新鲜度与主动信息；N20/N23 覆盖 UAV 故障应用重构。

当前剩余差异是一个面向本地任务的约束实例，而不是已经发现的新问题结构。
