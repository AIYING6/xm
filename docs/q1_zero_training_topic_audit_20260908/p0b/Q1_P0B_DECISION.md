# Q1-P0B 决策

**裁决：** `Q1_P0B_TIV_CONDITIONAL_GO_TO_P0C_ONLY`

## 为什么只保留 TIV

任务信息可行域是本轮唯一同时满足以下条件的候选：

- 研究对象可以被明确定义和反例判伪；
- 不要求伪造当前不存在的路由/中继动作；
- 三机 3DOF 物理动作会真实改变未来感知和通信机会；
- 已有合法来源、缓存新鲜度、动态故障和任务信息门控可以成为形式化资产；
- 如果理论失败，可以在零训练阶段及时关闭。

该裁决不表示 TIV 已具有一区新颖性，也不表示允许实现。它只允许下一轮 P0C 形式化与精确重叠审查。

## P0C 必须交付的六项证据

1. **最小定义。** 给出 TIV 的状态、故障集合、分散信息、任务期限和可行策略量词；明确 nominal、robust 和 local-observable 三种版本。
2. **三类严格反例。** 证明：(a) 连通不充分也不必要；(b) 更低 AoI 不保证 TIV；(c) 贪心任务进展动作会离开 TIV，而信息机动动作保持 TIV。
3. **任务信息割。** 定义 temporal task-information cut，并判断它只是时间展开图 cut，还是能由角色/来源/时效约束产生新的结构。
4. **至少三个命题候选。** 优先审查受限三角色拓扑上的充要条件、递归可行性和局部证书；每个命题必须标注是否新、是否非平凡、是否可计算。
5. **15–25 篇精确重叠矩阵。** 覆盖通信约束任务规划、VoI、task-oriented communication、CBF/reachability、formal resilient MAS 和 communication-aware MARL。
6. **本地可控性证明。** 用代码路径证明物理动作能在不新增路由变量的情况下改变至少一个反例的 TIV 真假；否则 `P0C_NO_GO`。

## 冻结的否证条件

出现任一项即关闭：

- TIV 等价于现有 connectivity、AoI-feasibility、temporal-logic feasibility 或标准 viability kernel 的直接实例；
- 任务信息割只产生已知时间扩展最小割，没有新结构或算法意义；
- 反例必须依赖全局 oracle、人工标签或当前接口不存在的动作；
- 无法构造局部可观测/可估计的证书；
- 唯一可行方法只是增加 critic、RNN/GNN 或 reward shaping；
- 理论成立所需环境假设使 UAV 任务失去现实意义。

## 资源纪律

P0C 仍然禁止环境修改、算法实现、训练、评估和云端运行。只有 `P0C_GO_TO_P1_DETERMINISTIC_PROTOTYPE` 才能进入确定性小规模原型；即使 P0C 通过，P1 也先做枚举/规划器，不训练神经网络。
