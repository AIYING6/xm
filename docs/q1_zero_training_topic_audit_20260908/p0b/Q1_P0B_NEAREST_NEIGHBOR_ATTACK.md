# Q1-P0B 最近邻攻击摘要

## 1. TIV 的强近邻

| 类别 | 代表工作 | 已覆盖内容 | TIV 必须额外证明的差异 |
|---|---|---|---|
| 通信感知运动 | [Communication-Aware Robotics](https://www.annualreviews.org/content/journals/10.1146/annurev-control-071420-080708) | 用运动改善连接/信息流，讨论理论保证 | 对象不是信道/连通，而是任务、来源和时效共同决定的未来可行性 |
| 任务+连通 | [Enforcing Network Connectivity in Robot Team Missions](https://journals.sagepub.com/doi/10.1177/0278364909358274) | 联合运动控制、任务分配与网络层 | 证明全局连通既非 TIV 必要也非充分 |
| 间歇通信任务规划 | [Kantaros et al.](https://arxiv.org/abs/1706.00765) | 联合局部 LTL 任务、通信事件和会合地点 | 信息来源/年龄应直接改变任务动作合法性，而非只要求周期性交换 |
| 风险约束间歇通信 | [Probabilistic Multi-Robot Planning](https://labs.sciety.org/articles/by?article_doi=10.21203%2Frs.3.rs-6649588%2Fv1) | 随机运动、时序任务、通信要求和风险约束 | TIV 必须有不同的证书或结构，而非另一种 temporal constraint |
| 动态协同通信 | [CoCoPlan](https://ieeexplore.ieee.org/document/11361077/) | 联合任务规划与间歇通信事件 | 证明故障后合法信息证书带来其模型没有的判定结构 |
| 任务导向通信 | [TOCD survey](https://orbilu.uni.lu/handle/10993/53991) | 以任务效果而非比特准确率设计通信 | TIV 不只是任务效用权重，而是任务完成的硬未来可行集合 |
| 信息价值 | [VoI in Feedback Control](https://arxiv.org/abs/1812.07534) | 用控制价值决定是否发送 | TIV 不是单包边际价值或通信成本阈值 |
| MARL 信息价值 | [VIL2C](https://ojs.aaai.org/index.php/AAAI/article/view/40234) | 低时延、VoI 资源分配及性能分析 | TIV 必须覆盖故障、合法来源与运动诱导未来路径 |
| 连通屏障 | [CBF connectivity maintenance](https://arxiv.org/abs/2103.12614) | 通信延迟下保持连接 | 证明保持 λ2>0 不能保证任务信息可行，且 TIV 可允许暂时断连 |
| 最小扰动重构 | [Minimally Disruptive Connectivity Enhancement](https://ieeexplore.ieee.org/document/9340733/) | 满足任意连接需求并尽量不扰动原任务 | TIV 的需求不能只是另一种 connectivity demand |
| 多机器人安全学习 | [Safe multi-robot control survey](https://doi.org/10.1016/j.arcontrol.2024.100948) | shield、CBF、HJ reachability、验证与 safe MARL | 方法不能只是标准 reachability/CBF 套壳 |
| 形式化韧性 | [Modelling resilient collaborative MAS](https://link.springer.com/article/10.1007/s00607-020-00861-2) | 形式化协作活动、故障与系统目标 | TIV 应给出控制/学习可用的计算对象，而非只有规范模型 |
| 图 MARL 泛化 | [Recurrent graph MARL](https://www.ifaamas.org/Proceedings/aamas2024/pdfs/p1919.pdf) | 局部/陈旧图观测上的跨图泛化 | 不以新网络结构作为主要贡献 |
| OOD 通信 | [Communicating Unexpectedness](https://arxiv.org/abs/2501.01140) | 用预测误差通信应对动态与 OOD 情形 | 不把“故障惊讶度”换名为可行性 |
| 主动信息获取 | [Multi-Robot Active Information Gathering](https://arxiv.org/abs/1703.02610) | 周期通信条件下的 Dec-POMDP 信息采集 | TIV 的任务信息不是一般熵/估计误差目标 |
| UAV 应用韧性 | [A²-UAV](https://www.sciencedirect.com/science/article/pii/S1389128624007199) | 节点故障下路由、预处理、目标分配和真实四机验证 | 避免回到已被 C0R 否决的主动路由—服务组合 |

## 2. 最危险的“伪创新”形式

以下任一结果都会使 TIV 关闭：

1. 把连通阈值、AoI 阈值和任务可达性简单相交后命名为 TIV；
2. 用全局仿真真值计算证书，却声称分散可执行；
3. 只训练一个 value/critic 去预测成功率，没有新的可验证结构；
4. 把现有 `_has_fresh_target_cache` 掩码本身写成方法贡献；
5. 证明内容只是“viability kernel 按定义递归可行”；
6. 需要新增路由、容量和迁移动作才能让反例成立，重新落回已关闭的 C0R。

## 3. 当前未被证实的点

- 尚未证明“任务信息割”在现有受限三角色图上有独立于时间扩展可达图的结构；
- 尚未证明 TIV 能由每个 actor 的合法局部信息近似或认证；
- 尚未证明保持 TIV 与最终任务回报之间存在可辨识的经验关系；
- 尚未证明一个 learned policy + certificate 的方法能超过强 MPC、通信感知规划和普通 recurrent MARL；
- 尚未形成一区所需的跨环境或更高保真证据路线。
