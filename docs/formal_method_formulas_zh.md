# 中文方法公式稿：问题建模与 EA-RG-MAPPO

日期：2026-07-29

用途：为中文论文初稿和后续 LaTeX 正文提供可复用的问题建模、关系图、消息传播和 MAPPO 目标公式。本文档只写已经由正式协议支持的方法定义，不写未完成实验结论。环境动力学、通信模型和任务链恢复的更完整定义见 `docs/task_chain_env_formalization_zh.md`。

## 1 问题建模

将有限通信条件下的异构无人机任务链恢复建模为 Dec-POMDP：

```text
M = <I, S, {O_i}, {A_i}, P, R, gamma>
```

其中：

- \(I=\{1,\ldots,N\}\) 为蓝方无人机集合；
- \(S\) 为全局状态空间；
- \(O_i\) 为第 \(i\) 个智能体的局部观测空间；
- \(A_i\) 为第 \(i\) 个智能体的动作空间；
- \(P(s^{t+1}|s^t,a^t)\) 为状态转移；
- \(R(s^t,a^t)\) 为团队奖励；
- \(\gamma\) 为折扣因子。

蓝方三架无人机角色为：

```text
role_0 = Scout
role_1 = Relay
role_2 = Attacker
```

每个智能体在时刻 \(t\) 根据局部可用信息选择动作：

```text
a_i^t ~ pi_theta(a_i^t | o_i^t, G_i^t)
```

其中 \(G_i^t\) 为 actor 在分散执行条件下可见的图观测。训练阶段使用 centralized critic：

```text
V_phi(s^t)
```

critic 可使用全局状态，但 actor 不允许使用不可获得目标状态、不可达队友状态、未来消息和评估专用全局链路变量。

## 2 任务链状态

定义任务链状态：

```text
Detection -> Information Delivery -> Attack-Window Formation -> Reclosure
```

目标信息对智能体 \(i\) 可用，当且仅当满足以下条件之一：

```text
direct_sense_i^t = 1
```

或

```text
received_msg_i^t = 1,
age_i^t <= TTL,
confidence_i^t >= tau_c
```

其中 \(age_i^t\) 为消息年龄，\(TTL\) 为消息最大有效期，\(\tau_c\) 为置信度阈值。

任务链闭合指示量定义为：

```text
C_t = I_track^t * I_info^t * I_win^t * I_hold^t
```

其中：

- \(I_{\mathrm{track}}^t\) 表示当前存在有效目标跟踪；
- \(I_{\mathrm{info}}^t\) 表示攻击平台具有有效目标信息链；
- \(I_{\mathrm{win}}^t\) 表示攻击平台满足攻击窗口；
- \(I_{\mathrm{hold}}^t\) 表示上述条件连续保持 \(K\) 步。

当前代码中 \(K=\) `attack_hold_steps = 4`。

中继失效后，恢复事件定义为：

```text
recover^t = 1 if C_t = 1 and t >= t_f
```

由于 \(C_t\) 已经包含连续保持条件，恢复不是单步攻击窗口命中，而是任务链持续闭合后的恢复。

## 3 多关系角色图

每个时间步构建多关系图：

```text
G^t = (V^t, E_p^t, E_c^t, E_s^t)
```

其中：

- \(V^t\) 为无人机及任务相关节点集合；
- \(E_p^t\) 为感知关系；
- \(E_c^t\) 为通信关系；
- \(E_s^t\) 为任务支援关系。

### 3.1 感知关系

感知关系表示平台是否直接获得目标信息：

```text
A_{p,ij}^t = 1
```

当且仅当发送节点 \(j\) 在时刻 \(t\) 具备有效目标感知，并且该信息可作为接收节点 \(i\) 的可用任务信息来源。

### 3.2 通信关系

通信关系表示消息是否经过物理通信约束后到达：

```text
A_{c,ij}^t = C_{ij}^t * D_{ij}^t * F_j^t
```

其中：

- \(C_{ij}^t\) 表示通信半径和拓扑可达性；
- \(D_{ij}^t\) 表示丢包和时延后消息是否可见；
- \(F_j^t\) 表示发送节点通信功能是否有效。

若中继节点失效，则对应发送或转发功能被禁用。

### 3.3 任务支援关系

任务支援关系表示角色之间对当前任务链恢复的潜在支援依赖，但其激活必须只依赖 actor 合法可见的信息。不得使用环境全局真值、评估专用链路状态或 centralized critic 输入来构造 actor 侧任务支援边。

```text
A_{s,ij}^t = f_s(role_i, role_j, b_{ij}^t)
```

其中 \(b_{ij}^t\) 只能由以下信息组成：

- 发送方和接收方角色；
- 物理通信是否已经有效投递；
- 接收方可见的消息缓存；
- 消息年龄；
- 消息置信度；
- 直接感知标志；
- 本地攻击窗口标志；
- 节点通信功能是否可用。

换言之，任务支援关系不是由全局任务链阶段直接切换的边。它是“角色兼容 + 通信可达 + 合法可见信息有效”的 actor 侧 masked relation。

在当前实现中，任务支援边需要满足：

```text
role_compatible(src, dst) = 1
and delivered_communication(dst, src) = 1
and visible_support_evidence(src) = 1
```

该约束用于防止任务支援图绕过物理通信链路成为隐藏信息通道。

## 4 角色对条件消息传播

对每类关系 \(r \in \{p,c,s\}\)，节点 \(j\) 向节点 \(i\) 发送消息：

```text
m_{ij,r}^t = W_{r, role_i, role_j} h_j^t
```

其中：

- \(h_j^t\) 为发送节点表示；
- \(W_{r, role_i, role_j}\) 为由关系类型和角色对决定的消息映射。

边权重可写为：

```text
alpha_{ij,r}^t =
softmax_j(q_i^T k_{j,r} + g_r(e_{ij}^t) + b_{role_i,role_j})
```

其中：

- \(q_i\) 为接收节点 query；
- \(k_{j,r}\) 为关系特定 key；
- \(e_{ij}^t\) 为边特征；
- \(b_{role_i,role_j}\) 为角色对门控或先验项。

节点更新：

```text
\tilde{h}_{i,r}^t = sum_j alpha_{ij,r}^t m_{ij,r}^t
```

多关系融合：

```text
\bar{h}_i^t = F([h_i^t, \tilde{h}_{i,p}^t, \tilde{h}_{i,c}^t, \tilde{h}_{i,s}^t])
```

最终 actor 输入：

```text
u_i^t = [f_o(o_i^t), \bar{h}_i^t]
```

动作分布：

```text
pi_theta(a_i^t | o_i^t, G_i^t) = softmax(f_pi(u_i^t))
```

## 5 MAPPO 目标函数

定义概率比：

```text
rho_i^t(theta) =
pi_theta(a_i^t | o_i^t, G_i^t) /
pi_{theta_old}(a_i^t | o_i^t, G_i^t)
```

策略损失：

```text
L_policy =
- E_t [
  min(
    rho_i^t(theta) A_i^t,
    clip(rho_i^t(theta), 1-epsilon, 1+epsilon) A_i^t
  )
]
```

价值损失：

```text
L_value = E_t[(R_t - V_phi(s^t))^2]
```

熵正则：

```text
L_entropy = E_t[H(pi_theta(. | o_i^t, G_i^t))]
```

总损失：

```text
L = L_policy + c_v L_value - c_H L_entropy
```

正式协议中 `chain_aux_coef=0.0`，因此链路辅助预测不作为当前主方法损失项。

## 6 评价指标公式

任务链恢复率：

```text
RecoveryRate = (# episodes with post-failure recovery) / (# episodes)
```

延迟恢复率：

```text
DelayedRecoveryRate =
(# episodes recovered after min_success_step) / (# episodes)
```

限制平均恢复时间：

```text
RMRT(tau) = E[min(T_recover, tau)]
```

平均消息年龄：

```text
MsgAge = mean_t mean_i age_i^t
```

通信连通率：

```text
ConnRate = mean_t 1[communication graph contains a feasible path to attacker]
```

碰撞率：

```text
CollisionRate = (# episodes with collision) / (# episodes)
```

## 7 论文中需要避免的表述

不要写：

```text
本文实现了完整空战智能决策系统。
本文方法保证杀伤链闭合。
本文方法在所有通信条件下均优于现有方法。
role-gate prior 是本文核心创新。
规则策略是本文主要创新。
```

应该写：

```text
本文在三自由度异构无人机任务链恢复环境中，验证多关系角色图在有限通信与中继失效条件下的恢复能力。
```

## 8 待转 LaTeX 内容

后续转入论文正文时，需要将本文档中的公式改成 LaTeX：

- Dec-POMDP 定义；
- 多关系图定义；
- 三类邻接矩阵；
- 角色对条件消息传播；
- MAPPO 损失；
- 恢复指标定义。

对应正文位置建议：

- 第 3 节：问题建模；
- 第 5 节：方法；
- 第 6 节：实验指标与统计。
