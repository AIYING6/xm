# P0C：Temporal Task-Information Cut 审查

## 1. 构造

固定物理轨迹、故障序列和任务期限后，构造时间展开图 (mathcal G^T)：

- 节点 ((i,t,\kappa)) 表示时刻 (t) 的 UAV (i) 持有令牌 (kappa)；
- 感知边表示角色 (S) 在时刻 (t) 生成合法令牌；
- 传输边表示 ((j,t,\kappa)\rightarrow(i,t+1,\kappa')) 在有效通信边上成立；
- 存储边表示令牌在下一时刻仍满足年龄与置信度阈值；
- 服务边把拥有合法令牌且满足物理任务窗口的状态连接到任务终点。

所谓 temporal task-information cut，是删除后切断所有合法来源节点到服务终点路径的最小边集或机会集。

## 2. 固定轨迹下的判定

在单令牌、确定性传输、无共享容量竞争的条件下：

> 任务在截止前具有信息可行性，当且仅当时间展开图中存在一条从合法感知源到合法服务终点的时间尊重路径。

该命题可由路径与执行序列逐步映射直接证明。其对偶 cut 也是标准时间展开网络的可达性 cut。来源、角色和时效约束只负责删边或删点，并未改变基本图论结构。

## 3. 动作相关图

当 UAV 动作改变未来通信边时，时间展开图本身依赖动作。此时问题成为联合运动—通信—任务规划；这正是 communication-aware motion planning、intermittent-connectivity task planning 和时序逻辑规划的研究对象。

## 4. 分散未知状态

若各 UAV 不知道完整故障和令牌分布，需要在知识/信念状态上规划。此时问题属于 epistemic planning、Dec-POMDP 或 belief-space planning。单纯把全局时间展开路径称为“局部证书”并不能解决共同知识与策略一致性。

## 5. 裁决

`TASK_INFORMATION_CUT_NOT_INDEPENDENTLY_NOVEL`

任务信息 cut 是一个有用的解释图，但在当前最小模型中，它没有形成独立的新组合结构：

- 固定轨迹：时间展开可达性/最小割；
- 动作相关：通信感知任务与运动规划；
- 分散未知：epistemic planning/Dec-POMDP；
- 容量与多任务：时间扩展流或调度，而这又回到已关闭的 C0R。
