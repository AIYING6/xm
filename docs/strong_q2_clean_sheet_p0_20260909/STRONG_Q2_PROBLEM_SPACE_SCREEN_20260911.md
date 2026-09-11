# 强二区问题空间：一次性文献—可识别性筛选

**目的：** 终止“做一个小审计、失败后换一个近义机制”的循环。本文档不是候选方法清单；它首先记录哪些问题类已被直接覆盖，因而不能仅靠换成 MAPPO、UAV 或自建环境重新申报为创新。

## 固定选择标准

任何后续主线须同时满足：

1. **真实信息或优化缺口：** 两个执行期合法历史下，最优协同决策应不同；
2. **非同义复述：** 不能是既有机制换网络、换机器人载体或换指标；
3. **公开主证据：** 至少一个成熟公开 MARL/多机器人基准承载主要比较，自建 UAV 只做应用外推；
4. **训练前闭环：** 主对照、机制消融、失效边界、统计单位、停止门同时冻结；
5. **可负担性：** 首个阶段只能是明确的公开基准基线与信息价值测试，而非先建大环境或跑长训练。

## 已排除的高重合问题类

| 问题类 | 直接文献占位 | 结论 | 不可接受的“换名”方式 |
|---|---|---|---|
| 未知/演化队友能力下的任务重分配 | Emam et al., ICRA 2020, DOI: 10.1109/ICRA40945.2020.9197283 | **排除** | 将在线能力更新换成 MAPPO、局部历史或 UAV 应用 |
| 通用协作 belief / 隐状态推断 | *Belief States for Cooperative MARL under Partial Observability* (2025), arXiv:2504.08417；*Latent Inference for Effective MARL* (2025) | **排除** | 仅加 GRU、belief encoder 或 history embedding |
| 个体随机观测延迟补偿 | *Rainbow Delay Compensation*, NeurIPS 2025 | **排除** | 仅把消息时延或异步观察引入 UAV 环境 |
| 任意通信等级下的缺失观测填补 | Santos et al., *Artificial Intelligence* 2025, DOI: 10.1016/j.artint.2025.104404 | **排除** | 预测队友观测、掩码重建或链路故障补偿 |
| 不确定任务需求/能力的近端资源预留 | Rossano et al., IROS 2026, arXiv:2509.22469 | **排除** | 将能力不确定改为任务不确定、等待或资源预留 |
| 不可逆承诺/异步宏动作协同 | Xiao et al., IJRR 2025；Farjadnasab & Sirouspour, RAS 2025 | **排除** | 仅以“行动限制后续可行集”或异步宏动作作为新机制 |
| 持续多智能体协同/防遗忘 | MACPro, TNNLS 2025；RPG, IJCAI 2025；MEAL, ICML 2026 | **排除为主线** | 仅加 replay、蒸馏、关系表示或任务上下文以防遗忘 |

## 由矩阵导出的积极约束

下一候选不能以“推断队友、补全缺失观测、处理延迟、重新分配任务”作为单一句机制。若继续使用 UAV/MARL，问题必须来自一个**尚未被上述方法自然覆盖的决策结构**，并能在公开基准中形成受控比较。例如：执行动作本身不可逆地改变未来协同可行集，且不同智能体对这一可行集只有互补的、可验证的信息；但这一方向在立项前还需证明不等价于已知的宏动作、任务分配或一般 belief 方法。

## 当前决策

1. C1（潜在能力漂移）停止，不再修补。
2. 不再从自建 UAV 环境逆向寻找机制。
3. 下一轮工作先选择一个公开基准中的**明确可检验现象**，再由现象决定方法；不得先命名算法。
4. 在找到同时满足五项标准的候选前，不启动任何长期训练。
5. 协作 MARL 中“能力推断、一般 belief、延迟、宏动作、持续学习”五个最直观方向均已出现直接方法占位；下一轮检索须转向竞争/博弈任务或非协作单一机制无法自然覆盖的公开问题类，而不是在这五类内继续微调。

## 参考入口

- Emam et al., 2020: https://arxiv.org/abs/2003.03344
- Cooperative belief states, 2025: https://arxiv.org/abs/2504.08417
- Delayed observations, 2025: https://arxiv.org/abs/2505.03586
- Hybrid execution / imputation, 2025: https://www.sciencedirect.com/science/article/pii/S0004370225001237
- Uncertain capability allocation, 2025/2026: https://arxiv.org/abs/2509.22469
- Public MARL benchmark infrastructure: https://jmlr.org/papers/v25/23-1612.html
- Asynchronous macro-action MARL: https://journals.sagepub.com/doi/10.1177/02783649241306124
- Continual coordination relation patterns: https://www.ijcai.org/proceedings/2025/759
- MEAL continual-MARL benchmark: https://arxiv.org/abs/2506.14990
