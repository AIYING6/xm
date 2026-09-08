# Q1-P0B 广域零训练选题搜索

日期：2026-09-08

状态：`P0B_COMPLETE`

资源消耗：0 环境步、0 PPO 更新、0 评估回合、0 GPU 小时

## 1. 本轮目的

上一候选“故障 + AoI + 路由 + 服务重构”已在 C0R 因组合式新颖性、理论靶点不足和动作接口缺失被关闭。本轮不再从算法模块出发，而从三类可能达到一区上限的学术核心出发：

1. 一个不同于连通性和 AoI 的新决策对象；
2. 一个可由反例和定理界定的形式问题；
3. 一个能够利用现有 UAV 物理动作、合法信息边界和动态故障语义的控制问题。

本轮只决定是否允许进入下一轮零训练形式化审查，不授权实现或训练。

## 2. 本地事实基础

| 事实 | 本地证据 | 对选题的约束 |
|---|---|---|
| 三机动作是转弯、爬升和加速，动作会改变 UAV 位置 | `envs/uav_intercept_3d_env.py:61-67, 475-492` | 可以研究通过物理机动改变未来感知/通信条件 |
| 通信边由位置、通信半径、丢包和节点故障共同决定 | `envs/uav_intercept_3d_env.py:640-729` | 图不是静态输入，而是受运动影响的时变信息通道 |
| 目标缓存具有生成时刻、交付时刻、跳数、置信度和来源路径 | `envs/uav_intercept_3d_env.py:619-638, 659-718, 1494-1536` | 可定义任务相关的信息证书，而非只用邻接矩阵 |
| 新鲜度、置信度和路径合法性共同决定信息是否可用于任务 | `envs/uav_intercept_3d_env.py:987-1036, 1465-1477` | “连通”不等于“当前任务可执行” |
| 六机环境能计算合法路径、可达任务对和 cut-set，但路由自动完成、中继动作不控制转移 | `envs/redundant_topology_uav_env.py:169-203, 224-260`; `docs/q1_zero_training_topic_audit_20260908/c0r/C0R_INTERFACE_GAP.md` | 六机资产只适合验证定义/构造反例，不能冒充主动路由控制 |
| 当前项目已正式关闭直接重启拓扑记忆、风险 PPO 和采样器修补 | `docs/q1_zero_training_topic_audit_20260908/Q1_ZERO_TRAINING_TOPIC_NOVELTY_INFORMATION_GAP_AUDIT.md` | 新主线不能是 TATG、CVaR 或 DRTP-vN 的换名版本 |

## 3. 文献检索范围

本轮对以下概念簇进行交叉检索：communication-aware robotics、intermittent connectivity、task-oriented communication、value of information、multi-robot temporal planning、connectivity certificates、safe/viability control、active fault diagnosis、graph OOD MARL。优先使用出版社、IEEE、PMLR、AAAI 和作者/会议原始页面。

专用学术数据库 MCP 在当前会话中不可用，因此本轮是“高召回的定向近邻攻击”，不是可发表的系统综述。“没有检索到同名概念”不得被解释为新颖性已经成立。

## 4. 检索得到的边界

### 4.1 已被充分覆盖的表述

- **保持连通或恢复连通。** 通信感知机器人已有联合运动—通信优化和性能保证的系统综述；多机器人连通保持、最小扰动重构和 CBF 证书均是成熟方向：[Communication-Aware Robotics](https://www.annualreviews.org/content/journals/10.1146/annurev-control-071420-080708)、[Enforcing Network Connectivity in Robot Team Missions](https://journals.sagepub.com/doi/10.1177/0278364909358274)、[Minimally Disruptive Connectivity Enhancement](https://ieeexplore.ieee.org/document/9340733/)。
- **任务与间歇通信联合规划。** LTL/STL 任务、通信事件、会合位置和风险约束已有联合规划：[Temporal Logic Task Planning and Intermittent Connectivity Control](https://arxiv.org/abs/1706.00765)、[Probabilistic Multi-Robot Planning with Temporal Tasks and Communication Constraints](https://labs.sciety.org/articles/by?article_doi=10.21203%2Frs.3.rs-6649588%2Fv1)、[Communication-aware Motion Planning from STL Specifications](https://arxiv.org/abs/1705.11085)。
- **按任务价值调度通信。** task-oriented communication 和 VoI 已直接把通信选择与控制回报或任务效果联系起来：[TOCD survey](https://orbilu.uni.lu/handle/10993/53991)、[Value of Information in Feedback Control](https://arxiv.org/abs/1812.07534)、[VIL2C](https://ojs.aaai.org/index.php/AAAI/article/view/40234)。
- **动态图记忆与 OOD 通信 MARL。** 递归消息传递、意外性通信和动态图上的跨图适应已有强近邻：[Recurrent Message Passing](https://www.ifaamas.org/Proceedings/aamas2024/pdfs/p1919.pdf)、[Communicating Unexpectedness](https://arxiv.org/abs/2501.01140)。
- **安全/可行域本身。** CBF、可达性、预测安全过滤和多机器人验证已形成成熟方法族：[Learning Safe Control for Multi-Robot Systems](https://doi.org/10.1016/j.arcontrol.2024.100948)。因此“给 MARL 加一个 safety shield”不构成新课题。

### 4.2 仍值得严格审查的交集

文献通常把以下对象作为目标：物理连通、链路质量、平均/最大 AoI、通信成本、任务回报或时序逻辑满足。当前仍可能存在的窄缺口是：

> 在异构协作任务中，定义一个同时依赖任务角色、合法来源、信息年龄、当前运动状态和未来可达通信机会的“任务信息可行性”对象，并研究策略如何在动态故障下保持或恢复该对象。

该对象若成立，应能严格区分：

- 图连通但关键任务信息无法合法、及时到达执行者；
- 图暂时不连通但凭借合法新鲜缓存和未来会合仍可完成任务；
- AoI 更低但来源/角色不合法，反而不具备任务可行性；
- 当前任务进展更快的动作破坏未来信息可行性，而信息机动动作保持完成可能。

这不是新颖性结论，只是进入 P0C 的可证假设。

## 5. 本轮总结

广域搜索没有发现可直接进入训练的一区题目。唯一值得继续零训练审查的方向是“任务信息可行域（Task-Information Viability, TIV）”，因为它同时满足：

- 不依赖当前缺失的显式路由动作；
- 物理动作可以真实影响未来通信机会；
- 现有环境已有来源、新鲜度、故障和任务动作合法性；
- 核心可以被反例和形式命题判伪。

但 TIV 与通信约束任务规划、VoI、连通性 CBF 和一般 viability kernel 有高重叠风险。只有下一轮证明其不是这些概念的重命名，才有资格立项。
