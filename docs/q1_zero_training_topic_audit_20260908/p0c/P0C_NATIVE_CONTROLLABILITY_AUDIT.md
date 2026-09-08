# P0C：现有 3DOF 接口的原生可控性审查

## 1. 真实可控作用链

现有三机环境存在以下真实转移链：

\[
u_t
\rightarrow x_{t+1}
\rightarrow G_{t+1}
\rightarrow Z_{t+1}
\rightarrow \mathcal A^{\mathrm{task}}_{t+1}.
\]

证据：

1. `ACTION3D_TABLE` 输出转弯、爬升和加速命令：`envs/uav_intercept_3d_env.py:61-67`；
2. `_move_blue` 更新航向、爬升角、速度和位置：`envs/uav_intercept_3d_env.py:472-492`；
3. `step` 在移动后调用 `_update_sensing_and_comm`：`envs/uav_intercept_3d_env.py:351-354`；
4. 通信可达由新位置间距离和通信半径决定：`envs/uav_intercept_3d_env.py:682-700`；
5. 令牌的合法性进一步由年龄、置信度和来源路径决定：`envs/uav_intercept_3d_env.py:987-1036`；
6. 任务执行者是否拥有目标信息由上述合法缓存决定：`envs/uav_intercept_3d_env.py:1465-1477`。

因此，可在通信边界附近构造两个物理动作，使一个动作保持/恢复直达信息路径，另一个动作使路径消失。P0B 所要求的“动作能改变 TIV 真假”在接口层面成立。

## 2. 不能夸大的部分

- 环境没有显式通信、路由或中继选择动作；信息沿所有当前可达边自动传播。
- 节点故障是环境外生配置，不是 actor 主动诊断或修复的对象。
- 通信模型主要由距离、固定范围、丢包和剪枝决定，不是高保真无线系统。
- 全局 TIV 计算所需的完整状态并不天然属于每个 actor 的合法观测。
- 物理动作“能够影响通信”不等于策略会学会维持可行域。

## 3. 裁决

`NATIVE_CONTROLLABILITY_PASS_BUT_NOT_NOVELTY`

原生接口足以承载一个通信感知物理控制问题，不需要新增虚假路由动作；但这只通过可实现性门槛，不能弥补理论与新颖性门槛失败。
