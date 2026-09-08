# P0C：三个严格反例

## 反例 1：连通性既不充分也不必要

### 连通不充分

三节点 (S\rightarrow R\rightarrow A) 在当前时刻连通，但 (S) 尚未获得目标观测，且距离截止只剩一步，无法完成“感知—转发—执行”。因此图连通而状态不在 TIV 中。

另一个本地原生实例是物理路径存在但缓存已超过 `max_target_message_age_steps`；`_has_fresh_target_cache` 返回 false，任务信息不可用。

### 连通不必要

当前图断连，但 (A) 已持有来源和路径均合法、在剩余任务时间内不会过期的令牌，并已进入执行窗口。它可在无新增通信的情况下完成任务。因此状态可属于 TIV，但当前图不连通。

### 能证明什么

连通性不能替代任务信息可行性。它不能证明 TIV 的计算或控制方法新颖。

## 反例 2：更低 AoI 不保证任务信息可行

考虑同一物理状态和任务状态下的两个令牌：

- (kappa_0)：年龄 0，但来自故障前的非法 Scout→Attacker 直达路径；
- (kappa_1)：年龄 1，来自当时合法的 Scout→Relay→Attacker 路径。

由路径来源约束，(L_A(\kappa_0,t)=0)，而 (L_A(\kappa_1,t)=1)。所以

\[
\operatorname{AoI}(\kappa_0)<\operatorname{AoI}(\kappa_1),
\qquad
\mathcal A_A^{\mathrm{task}}(\kappa_0)
\subset
\mathcal A_A^{\mathrm{task}}(\kappa_1).
\]

该构造直接对应 `envs/uav_intercept_3d_env.py:1025-1036`：relay-dependent 任务中的直达恢复路径只在中继故障后、且令牌在故障开始后交付时合法。

### 能证明什么

单一 AoI 排序无法代表任务价值。它不能证明“来源 + 年龄”的联合约束未被 task-oriented communication 或时序规划覆盖。

## 反例 3：贪心任务进展可破坏未来信息可行性

考虑一维简化几何。Scout 位于 0，Attacker 位于 (r-\epsilon)，当前仍处于通信半径 (r) 内；目标在 Attacker 右侧。中继刚失效，下一时刻必须获得一条故障后生成的直达恢复令牌。

- 贪心动作 (u^+) 向目标移动距离 (Delta>\epsilon)，使下一时刻 Scout–Attacker 距离超过 (r)。恢复令牌无法交付；旧令牌因路径故障而失效，任务在截止前不可完成。
- 信息保持动作 (u^0) 暂时保持或向 Scout 偏转，使距离不超过 (r)，接收合法新令牌；若剩余时域满足 (H-t\ge 1+T_{\mathrm{attack}})，随后仍可进入执行窗口并完成任务。

因此即时距离目标更近的 (u^+) 严格劣于短暂牺牲任务进展的 (u^0)。

本地接口能够表达这一作用链：动作先改变位置（`envs/uav_intercept_3d_env.py:351-354, 472-492`），新位置随后决定通信与缓存更新（`envs/uav_intercept_3d_env.py:682-718`）。

### 能证明什么

问题存在非短视性，且物理动作能够控制未来信息机会。该反例仍属于通信感知运动规划的已知一般结构。

## 综合边界

三个反例证明 TIV 具有解释价值，但没有任何一个反例导出新的复杂性类别、分解性质、近似界或控制定理。它们不足以单独支撑一区主线。
