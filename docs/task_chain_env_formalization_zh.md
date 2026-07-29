# 任务链恢复、3DOF 动力学与通信模型形式化说明

日期：2026-07-29

目的：补齐预审意见中指出的 P0 问题，包括任务链恢复定义不严格、3DOF 动力学描述不足、通信模型不可复现等问题。本文档依据当前代码实现整理，主要对应：

- `envs/uav_intercept_3d_env.py`
- `scripts/evaluate_ri_gmappo_3d.py`
- `docs/formal_protocol_freeze.md`

## 1 任务链闭合定义

本文将异构无人机任务链定义为：

```text
Detection -> Information Delivery -> Fresh Target Information -> Attack Window -> Chain Closure
```

在时间步 \(t\)，定义任务链闭合指示量：

\[
C_t =
I_{\mathrm{track}}^t
I_{\mathrm{info}}^t
I_{\mathrm{win}}^t
I_{\mathrm{hold}}^t .
\]

其中：

- \(I_{\mathrm{track}}^t=1\) 表示至少一个蓝方平台在当前时刻直接探测到目标；
- \(I_{\mathrm{info}}^t=1\) 表示攻击平台具有有效目标信息链；
- \(I_{\mathrm{win}}^t=1\) 表示至少一个攻击平台满足攻击窗口几何条件；
- \(I_{\mathrm{hold}}^t=1\) 表示上述条件已连续保持 \(K\) 步。

当前代码中：

```text
K = attack_hold_steps = 4
```

每个环境步执行：

```text
if attack_window and tracking and comm_has_chain_to_attacker:
    attack_hold += 1
else:
    attack_hold = 0

chain_closed = attack_hold >= attack_hold_steps
```

因此，本文中的任务链闭合不是单步几何接近，而是连续满足目标跟踪、攻击窗口和攻击平台目标信息链后的闭合状态。

## 2 中继失效与恢复时间

设中继通信功能失效开始时间为 \(t_f\)，失效持续时间为 \(D_f\)。当前 formal protocol 中：

```text
failed_blue_agent = 1
node_failure_duration_steps = 80
```

训练阶段失效开始时间随机采样：

```text
t_f ~ UniformInteger(25, 70)
```

评估阶段使用 early、standard、delayed、late 四种固定失效时机。

定义失效后首次恢复时间：

\[
T_{\mathrm{rec}} =
\inf \{ \tau \geq 0 : C_{t_f+\tau}=1 \}.
\]

由于 \(C_t\) 已包含连续 \(K\) 步保持条件，\(T_{\mathrm{rec}}\) 表示首次达到持续闭合要求的时间，而不是第一次瞬时满足攻击窗口。

若 episode 在失效后从未恢复，则：

\[
T_{\mathrm{rec}}^{\mathrm{censored}} =
\max(0, T_{\mathrm{final}} - t_f).
\]

当前评估脚本同时记录：

- `post_failure_chain_recovered`：失效后是否出现链闭合；
- `post_failure_chain_recovery_steps`：恢复时间，未恢复时为截断时间；
- `post_failure_chain_recovered_only_steps`：仅对已恢复样本记录恢复时间，未恢复为 -1；
- `post_failure_chain_maintained`：失效开始时链已经闭合；
- `post_failure_chain_recovered_after_loss`：失效后曾丢链并重新闭合；
- `post_failure_chain_unrecovered`：失效后未恢复；
- `post_failure_first_chain_step`：首次闭合步数。

论文中应优先报告：

```text
delayed recovery = post_failure_chain_recovered_after_loss
```

并将未恢复样本作为截断样本处理，不应简单丢弃。

## 3 有效目标信息定义

攻击平台具有有效目标信息，当且仅当满足以下任一条件：

1. 本机直接探测到目标；
2. 本机存在新鲜目标缓存；
3. 在 actor 可见通信关系下，目标信息已通过有效通信路径传递到本机。

新鲜目标缓存定义为：

\[
V_i^t =
\mathbf{1}
\left[
\mathrm{valid}_i^t=1
\land
g_i^t \geq 0
\land
t-g_i^t \leq T_{\mathrm{TTL}}
\land
c_i^t \geq \tau_c
\right],
\]

其中：

- \(g_i^t\) 为目标信息生成时间；
- \(T_{\mathrm{TTL}}\) 为最大消息年龄；
- \(c_i^t\) 为置信度；
- \(\tau_c\) 为最小置信度阈值。

当前 formal protocol 默认：

```text
max_target_message_age_steps = 80
min_target_confidence = 0.2
```

多跳消息传播时，置信度按每跳衰减：

```text
confidence <- 0.95 * confidence
```

## 4 3DOF 状态与动作

每个平台状态为：

\[
s_i^t =
(x_i^t, y_i^t, z_i^t, v_i^t, \psi_i^t, \gamma_i^t),
\]

其中：

- \((x,y,z)\) 为三维位置；
- \(v\) 为速度；
- \(\psi\) 为航向角；
- \(\gamma\) 为航迹倾角。

每个蓝方智能体动作由三维离散指令组成：

\[
a_i^t = (u_{\psi,i}^t, u_{\gamma,i}^t, u_{v,i}^t),
\quad
u_{\psi},u_{\gamma},u_v \in \{-1,0,1\}.
\]

动作空间大小为：

```text
3 * 3 * 3 = 27
```

## 5 蓝方 3DOF 动力学

时间步长：

```text
dt = 1.0 s
```

航向更新：

\[
\psi_i^{t+1}
=
\mathrm{wrap}
\left(
\psi_i^t
+ u_{\psi,i}^t \omega_{i,\max}\Delta t
\right).
\]

航迹倾角更新：

\[
\gamma_i^{t+1}
=
\mathrm{clip}
\left(
\gamma_i^t
+0.35u_{\gamma,i}^t\gamma_{i,\max}\Delta t,
-\gamma_{i,\max},
\gamma_{i,\max}
\right).
\]

速度更新：

\[
v_i^{t+1}
=
\mathrm{clip}
\left(
v_i^t
+u_{v,i}^t a_{i,\max}\Delta t,
v_{i,\min},
v_{i,\max}
\right).
\]

速度向量：

\[
\dot{x}_i =
v_i \cos\gamma_i \cos\psi_i,
\quad
\dot{y}_i =
v_i \cos\gamma_i \sin\psi_i,
\quad
\dot{z}_i =
v_i \sin\gamma_i.
\]

位置更新：

\[
p_i^{t+1}
=
p_i^t
+
\begin{bmatrix}
\dot{x}_i\\
\dot{y}_i\\
\dot{z}_i
\end{bmatrix}
\Delta t.
\]

高度边界：

```text
min_altitude = 1000 m
max_altitude = 9000 m
altitude_protection_margin = 750 m
```

当平台接近高度边界且仍向边界方向运动时，航迹倾角会被保护性调整。

水平战区边界：

```text
world_radius = 50000 m
boundary_protection_margin = 12000 m
```

接近边界时，航向会被保护性转向战区中心，并触发减速指令。

## 6 红方目标运动

formal protocol 主实验使用：

```text
target_policy = straight
```

在 straight 策略下：

\[
u_{\psi,r}^t = 0,\quad u_{\gamma,r}^t=0.
\]

红方目标保持当前航向和航迹倾角，并按同样 3DOF 速度向量更新位置。

代码中还包含 evasive、break-turn、weaving、weaving-mild、weaving-tiny 等策略。它们只能作为场景深度或 OOD 补充，不能用于选择正式主结果。

## 7 平台异构参数

| 角色 | \(v_{\max}\) | \(v_{\min}\) | \(a_{\max}\) | \(\omega_{\max}\) | \(\gamma_{\max}\) | 雷达距离 | 通信距离 | 攻击距离 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Scout | 245 | 120 | 18 | 0.035 | 0.26 | 17500 | 9500 | 1800-6500 |
| Relay | 220 | 115 | 14 | 0.030 | 0.22 | 12000 | 15500 | 2000-5800 |
| Attacker | 270 | 135 | 22 | 0.052 | 0.31 | 11000 | 8500 | 1400-5200 |
| Target | 255 | 130 | 18 | 0.046 | 0.28 | 10000 | 0 | 0 |

单位：

- 速度：m/s；
- 加速度：m/s²；
- 角速度/角度：rad 或 rad/s；
- 距离：m。

## 8 感知模型

平台 \(i\) 对目标可见，当且仅当：

\[
d_{i,r}^t \leq R_i^{\mathrm{radar}},
\]

\[
|\Delta \psi_{i,r}^t|
\leq
\frac{1}{2}\mathrm{FOV}_{h,i},
\]

\[
|\Delta \gamma_{i,r}^t|
\leq
\frac{1}{2}\mathrm{FOV}_{v,i}.
\]

若满足上述条件，还需要通过雷达随机失效：

\[
\xi_{\mathrm{radar}}^t \geq p_{\mathrm{radar\_dropout}}.
\]

formal protocol 中主实验：

```text
radar_dropout_prob = 0.0
```

严格感知模式下，未直接感知或未收到有效消息的 actor 使用 target prior，而不是目标真实状态。

## 9 通信模型

通信边以 receiver-sender 方向表示：

```text
A[receiver, sender] = 1
```

蓝方节点 \(j\) 到 \(i\) 的物理通信候选条件：

\[
d_{ij}^t
\leq
\rho_c
\min(R_i^{\mathrm{comm}}, R_j^{\mathrm{comm}}),
\]

其中 \(\rho_c\) 为通信距离缩放系数。

丢包按有向边和时间步随机采样：

\[
\xi_{ij}^t \geq p_{\mathrm{dropout}}.
\]

formal protocol 中：

```text
communication_dropout_prob = 0.30
message_delay_steps = 2
```

当 `message_delay_steps = d > 0` 时，消息不会立即可见，而是进入 pending queue：

```text
deliver_step = current_step + d
```

只有在 `deliver_step <= current_step` 且发送方和接收方通信功能均未失效时，消息才被投递。

## 10 中继失效模型

通信失效函数：

\[
F_i^t =
\mathbf{1}
[i = i_f]
\mathbf{1}
[t_f \leq t < t_f + D_f].
\]

若 \(F_i^t=1\)，则节点 \(i\) 不能作为 sender 或 receiver 完成通信投递。

当前实现中，中继失效影响：

- 已排队但尚未投递的普通通信消息；
- 已排队但尚未投递的目标缓存消息；
- 当前时间步新通信候选；
- task-support relation；
- union graph adjacency。

中继失效不影响：

- 平台机动；
- 平台能量更新；
- 本机雷达感知本身。

这意味着“中继失效”是通信功能失效，而不是飞机坠毁或完全失能。

## 11 消息缓存与多跳传播

每个目标缓存包含：

- 目标位置；
- 目标速度；
- 原始 source；
- generation step；
- delivery step；
- hop count；
- confidence；
- path。

当节点 \(j\) 有有效缓存并成功向 \(i\) 发送时：

\[
\mathrm{hop}_i = \mathrm{hop}_j + 1,
\]

\[
c_i = 0.95 c_j.
\]

若收到更旧的信息，或同一生成时间下 hop count 更长的信息，则不会覆盖当前缓存。

多跳传播每个 delay cycle 只能前进一跳。该行为由测试：

```text
test_target_message_cache_propagates_one_hop_per_delay_cycle
```

固定。

## 12 攻击窗口

攻击窗口仅对 Attacker 或 Interceptor 角色有效。平台 \(i\) 满足攻击窗口，当且仅当：

\[
R_{i,\min}^{\mathrm{atk}}
\leq
d_{i,r}^t
\leq
R_{i,\max}^{\mathrm{atk}},
\]

\[
|\Delta \psi_{i,r}^t|
\leq
\theta_i^{\mathrm{atk}},
\]

\[
|\Delta z_{i,r}^t|
\leq
1600 \mathrm{m},
\]

\[
v_{\mathrm{closure}} > -30 \mathrm{m/s}.
\]

攻击窗口不是导弹命中模型，只是主训练环境中的攻击几何代理。在线导弹或 JSBSim 回放只能作为后续真实性补充。

## 13 终止条件

episode 在以下任一条件满足时终止：

1. `success=True`：任务链闭合且步数达到 `min_success_step`；
2. `collision=True`：蓝方平台间距离小于碰撞半径；
3. `constraint_violation=True`：飞行约束违规；
4. `timeout=True`：达到最大步数。

formal protocol 中：

```text
max_steps = 260
min_success_step = 80
collision_radius = 120 m
```

## 14 当前实现边界

本文主实验不声称：

- 完整 6DOF 飞行动力学；
- 在线导弹闭环；
- 高保真雷达信号处理；
- 红蓝双方自博弈；
- 有人机协同完整系统。

本文主实验声称：

```text
在通信可行、严格感知、消息时延和中继通信功能失效的 3DOF 3v1 异构无人机任务链恢复环境中，比较多关系角色图与公平 baseline 的恢复性能。
```

## 15 论文 Methods 可直接采用的表述

```text
The environment uses a tactical 3DOF model rather than a full flight-control simulator. Each UAV state contains position, speed, heading and flight-path angle, and each action consists of discrete turn, climb and acceleration commands. Communication is directional and delayed: a message generated at time \(t\) is visible only after \(d\) steps if both sender and receiver remain communication-functional. Target messages are stored in local caches with generation time, delivery time, hop count, confidence and path. A cache is valid only if its age is below \(T_{\mathrm{TTL}}\) and its confidence exceeds \(\tau_c\). Relay failure disables the relay's communication sending and receiving functions but does not remove the aircraft from the kinematic simulation.
```

中文稿可采用：

```text
本文环境采用战术层三自由度模型，而不是完整飞控级仿真。每架无人机状态包括三维位置、速度、航向角和航迹倾角，动作由离散转向、爬升和加减速指令组成。通信为有向且存在时延，消息只有在发送方和接收方通信功能均有效并经过指定延迟后才对接收方可见。目标消息以本地缓存形式保存生成时间、投递时间、跳数、置信度和传播路径；只有消息年龄低于 TTL 且置信度高于阈值时，该缓存才被视为有效。中继失效表示中继节点通信发送和接收功能失效，不表示飞机从动力学仿真中消失。
```
