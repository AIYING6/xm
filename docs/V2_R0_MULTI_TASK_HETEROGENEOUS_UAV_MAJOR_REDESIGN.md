# V2-R0：多任务异构 UAV 大修版任务与算法规范

状态：`V2_R0_MULTI_TASK_HETEROGENEOUS_UAV_MAJOR_REDESIGN__SPEC_FROZEN__NO_TRAINING`

日期：2026-08-11

## 1. 立项目标

当前 3-UAV/1-target 任务冻结为验证平台，不再承担自动产生新算法问题的职责。V2 的论文主问题改为：

> 在严格 recipient-specific 局部信息、受限通信和连续 3DOF 执行下，异构 UAV 团队如何对多个并发、能力需求不同且存在空间/时间冲突的任务进行动态 coalition/assignment，并把高层分配稳定地落实为物理任务完成。

这不是“首次研究异构任务分配”。2025 年 CASH 已研究 capability-aware heterogeneous multi-robot coordination、灵活共享策略和 unseen team generalization，因此 V2 不得把 capability encoding 或任务分配本身作为充分创新。[CASH](https://proceedings.mlr.press/v305/fu25a.html)

## 2. 环境规格

### 2.1 团队与能力

* 5–8 架 UAV，至少三类可解释 capability：sensing、relay/support、execution/interception；
* capability 是物理属性（感知半径/精度、通信范围、机动上限、执行窗口等），不是只喂给网络的标签；
* 至少部分 capability 重叠，避免责任分配退化成唯一合法角色映射；
* 所有 actor 继续遵守 recipient-specific information contract；critic 的 privileged state 只存在于训练路径。

### 2.2 并发任务

* 3–5 个空间分布的并发任务；
* 任务类型至少包括 sensing/track、relay/maintain-information、standoff-neutralization 或等价 physical endpoint；
* 每个任务具有 capability requirement、时间窗/截止期、空间位置和可测完成状态；
* 任务之间存在资源冲突：同一 UAV 不能同时执行冲突任务；移动到一个任务会改变其他任务的到达时间、通信可达性或完成风险；
* 任务完成必须由物理状态转移判定，禁止用 graph closure、assignment flag 或通信连通性作为成功代理。

### 2.3 通信与动力学

保留严格 actor contract、local sensing、delivered/cache-valid packet、range/loss/delay 和现有 3DOF dynamics。所有任务状态传播必须通过合法 sensing 或实际 packet/cache 到达，禁止全局任务 truth 旁路。

## 3. 动作接口

采用两层但不预设方法优越性：

* 高层 assignment/coalition action：在离散决策时刻选择任务、候选 coalition 或保持；动作必须经过 capability-feasibility mask；
* 低层 continuous guidance：在 assignment 有效期内输出 turn/climb/speed 等连续指令，仍由现有 3DOF 执行；
* assignment 不是环境自动重分配；任务切换有可测切换成本、冷却或执行延迟；
* 高层与低层都只能使用各自合法的信息。高层不得读取全局任务状态。

## 4. 必须比较的基线

### 4.1 分配基线

1. fixed assignment；
2. nearest/greedy capability-feasible assignment；
3. centralized matching oracle（仅作上界，不作为执行期 actor）；
4. rule-based coalition switch。

### 4.2 学习基线

1. flat MAPPO：把任务和 UAV 状态拼接到统一 actor；
2. hierarchical MAPPO：高层 assignment + 低层控制，但无结构化任务图；
3. capability-conditioned baseline：显式输入 capability/task requirement，但不使用 proposed 结构；
4. proposed hierarchical task–capability graph policy（具体机制须经过 R1 直接近邻审核后冻结）。

## 5. 预注册指标

* 全部任务 physical completion rate；
* deadline-weighted completion and makespan；
* coalition feasibility rate；
* assignment switch latency and switch count；
* communication load / information age；
* collision/constraint failure；
* 低层轨迹到达和任务执行成功率；
* 相同场景下 assignment regret（相对 centralized matching oracle）。

不能只报告总 reward 或单一 neutralization rate。

## 6. R0 kill conditions

直接关闭或重新设计，而不是局部缝补：

1. 多任务仍可由单一固定分工完成，任务冲突不真实存在；
2. capability mask 唯一决定 assignment，沒有状态依赖 coalition 决策；
3. flat MAPPO 与 proposed 接口实际看到的信息不等价，导致比较不公平；
4. oracle/ scripted 在 nominal 条件下无法稳定完成，说明任务底座不合格；
5. proposed 的唯一差异只是普通 capability embedding、普通 GNN 或已有 CASH 式共享策略；
6. 任务完成仍依赖内部 graph/assignment proxy，而非物理终态。

## 7. 固定流程（不再递归微修）

```text
R0  纸面任务与接口规范（当前）
 ↓
R1  一次直接近邻与创新边界审核
 ↓
R2  scripted/oracle + random 可达性与冲突验证
 ↓
R3  vanilla baseline 小规模 learnability
 ↓
M0  最小算法实现与消融
 ↓
M1  development pilot
 ↓
formal F1/F2
```

任何阶段发现底层构念不成立，只允许一次大修或关闭项目，不进入 R0A/R0B/NP 式递归。

