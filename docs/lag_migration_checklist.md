# EA-RG-MAPPO-S 迁移到 LAG/JSBSim 检查清单

日期：2026-07-13

目标：把当前 2D 有限通信协同追逃方法迁移到 LAG/JSBSim 时，先验证“状态到图表示”的可行性，再决定是否进行 6DOF 训练。第一轮不追求完整空战论文结果，避免过早进入导弹、雷达和有人机协同导致调试成本失控。

## 1. LAG 当前可用接口

LAG 路径：

```text
C:/Users/96251/Documents/Codex/2026-07-12/ni/work/LAG
```

最新自动探针：

```text
scripts/probe_lag_jsbsim_migration.py
docs/lag_jsbsim_migration_probe.md
results/lag_jsbsim_migration_probe.csv
```

当前探针结论：

```text
1. MultipleCombat env/task/base env/simulator wrapper 文件存在；
2. MultipleCombatTask 静态接口可读取，动作空间为 MultiDiscrete([41, 41, 41, 30])；
3. 单机观测长度为 9 + (num_agents - 1) * 6，共享观测为 num_agents * obs_length；
4. LAG synthetic role graph smoke test 已有 400 行，无 NaN/Inf；
5. 真实 JSBSim reset/step 仍被阻塞，因为 envs/JSBSim/data 子模块缺失；
6. 当前 multiplecombat_env import 还暴露 `envs.JSBSim.human_task` 缺失问题，需要在真实 reset 探针前处理。
```

关键模块：

| 用途 | 文件 |
|---|---|
| MAPPO policy | `algorithms/mappo/ppo_policy.py` |
| MAPPO actor | `algorithms/mappo/ppo_actor.py` |
| 共享 MAPPO runner | `runner/share_jsbsim_runner.py` |
| 2v2 多机空战环境 | `envs/JSBSim/envs/multiplecombat_env.py` |
| 2v2 任务定义 | `envs/JSBSim/tasks/multiplecombat_task.py` |
| 状态打包/集中状态 | `envs/JSBSim/envs/env_base.py` |

## 2. LAG 任务与状态结构

`MultipleCombatTask` 当前是 4 机 2v2 任务：

```text
num_agents = 4
action_space = MultiDiscrete([41, 41, 41, 30])
obs_length = 9 + (num_agents - 1) * 6 = 27
share_obs_length = num_agents * obs_length = 108
```

单机局部观测结构：

| 区间 | 含义 |
|---|---|
| `0:9` | ego altitude、roll/pitch sin-cos、body velocity、vc |
| 每个相对对象 6 维 | relative body speed、altitude difference、AO、TA、range、side flag |

底层原始状态量包括：

```text
longitude, latitude, altitude,
roll, pitch, heading,
v_north, v_east, v_down,
v_body_x, v_body_y, v_body_z,
vc,
pilot acceleration x/y/z
```

这足够构造 EA-RG-MAPPO-S 的 6DOF 版节点和边特征。

## 3. 迁移时优先复用的部分

当前 2D 项目中可以复用：

1. 角色图思想：友机、敌机、目标均作为带 role embedding 的节点。
2. 边特征注意力：相对距离、方位、速度差、通信可达性仍然成立。
3. 通信半径 mask：从 2D 距离半径扩展为 3D NED 距离半径。
4. staged random-radius fine-tuning：仍可作为有限通信鲁棒训练策略。
5. 评估指标框架：成功率、碰撞/失效率、平均步数、种子方差、半径鲁棒性。
6. 可视化思路：轨迹、注意力热力图、per-seed scatter。

## 4. 必须重写或适配的部分

| 模块 | 需要改动 |
|---|---|
| 环境接口 | LAG 返回 `obs, share_obs, rewards, dones, infos`，不同于当前 2D 环境 |
| 图构建 | 需要从 JSBSim 原始状态或 LAG obs 中恢复 node/edge features |
| 动作头 | LAG 是 `MultiDiscrete([41,41,41,30])`，不能直接复用当前 9 动作头 |
| critic 输入 | LAG 使用 `share_obs_space`，需要决定是否仍用集中 state 或加图 critic |
| reward/termination | LAG 已有姿态优势、极端状态、低高度、超时等条件，不能照搬 2D reward |
| 训练规模 | JSBSim 明显更慢，应先 smoke test，再短训练，不直接大规模调参 |

## 5. LAG 图特征设计

第一版建议不要过度复杂，先构造：

```text
node_feat_i = [
    altitude_norm,
    sin(roll), cos(roll),
    sin(pitch), cos(pitch),
    sin(heading), cos(heading),
    v_north_norm, v_east_norm, v_down_norm,
    v_body_x_norm, v_body_y_norm, v_body_z_norm,
    alive_flag,
    team_flag
]
```

边特征：

```text
edge_feat_ij = [
    rel_north_norm,
    rel_east_norm,
    rel_down_norm,
    range_norm,
    range / comm_radius,
    line_of_sight_unit_n,
    line_of_sight_unit_e,
    line_of_sight_unit_d,
    rel_v_north_norm,
    rel_v_east_norm,
    rel_v_down_norm,
    same_team_flag,
    comm_reachable
]
```

邻接矩阵：

```text
adj_ij = 1 if i == j
adj_ij = 1 if same_team and distance_3d <= comm_radius
adj_ij = 1 if enemy node is observable
adj_ij = 0 otherwise
```

第一轮建议先不做雷达遮挡和链路质量，只用 3D 距离半径。规则不能作为创新点，但可以作为通信 mask 的工程约束。

## 6. 第一轮 Smoke Test

目标：不训练，只验证 LAG 状态能稳定转换成 EA-RG-MAPPO-S 图输入。

最低标准：

1. 能 reset `MultipleCombatEnv`。
2. 能从每个 step 取到 4 个 agent 的状态。
3. 能构造：

```text
node_feat: [num_agents, node_dim]
edge_feat: [num_agents, num_agents, edge_dim]
adj:       [num_agents, num_agents]
role:      [num_agents]
```

4. 所有 tensor 无 NaN/Inf。
5. 通信半径从小到大时，team edge 数量单调不下降。
6. 能保存一段 100 step 的图统计 CSV。

建议输出文件：

```text
docs/lag_migration_checklist.md
scripts/lag_graph_smoke_test.py
results/lag_graph_smoke_stats.csv
```

当前已新增 `scripts/lag_graph_smoke_test.py`。默认 `--mode synthetic` 不依赖 JSBSim，可先验证图构建；`--mode lag` 会尝试读取真实 LAG `MultipleCombatEnv`。

当前还新增了 duck-typed 适配层：

```text
envs/lag_role_graph_adapter.py
envs/lag_role_graph_wrapper.py
scripts/test_lag_role_graph_adapter.py
scripts/test_lag_role_graph_wrapper.py
docs/lag_role_graph_adapter_test.md
docs/lag_role_graph_wrapper_test.md
results/lag_role_graph_adapter_test.csv
results/lag_role_graph_wrapper_test.csv
```

该适配层把 LAG-like simulator 的 `get_position()`、`get_velocity()`、`get_rpy()`、`get_property_values()` 转换为 EA-RG-MAPPO-S 使用的 15 维节点特征、13 维边特征、邻接矩阵和 role 向量。wrapper 进一步提供 `reset/step -> graph` 的最小调用链。测试使用 fake simulator，不声称真实 JSBSim reset/step 已通过。

当前验证状态：

```text
python scripts/lag_graph_smoke_test.py --mode synthetic --steps 100
```

结果：

```text
wrote 400 rows to results/lag_graph_smoke_stats.csv
nan_count=0, inf_count=0
```

```text
python scripts/test_lag_role_graph_adapter.py
```

结果：

```text
checks=26, failed=0
node_feat=(4, 15), edge_feat=(4, 4, 13), adj=(4, 4)
enemy_edges=8 for each tested radius
team edge count is monotonic with radius
nan_count=0, inf_count=0
```

```text
python scripts/test_lag_role_graph_wrapper.py
```

结果：

```text
checks=11, failed=0
reset/step passthrough OK
last_graph cache update OK
step 后图特征刷新 OK
nan_count=0, inf_count=0
```

真实 LAG 模式已经确认 `jsbsim` Python 依赖可加载，但当前复制的 LAG 缺少：

```text
work/LAG/envs/JSBSim/data
work/LAG/envs/JSBSim/JSBSim-Team
```

因此 `--mode lag` 暂时会停止在 JSBSim data root 检查。下一步如果要跑真实 LAG，需要补完整 JSBSim data/submodule。

## 7. 第一轮训练建议

只有 smoke test 通过后再训练。第一轮训练不要引入导弹和雷达：

```text
task = MultipleCombat NoWeapon
algorithm = MAPPO baseline first
then = EA-RG-MAPPO-S actor encoder only
num_env_steps = small budget
eval = posture advantage / survival / timeout
```

不要一开始做：

```text
missile launch policy
radar detection model
human-unmanned mixed command hierarchy
full intent recognition
```

这些可以作为后续系统扩展，不适合作为当前论文主实验入口。

## 8. 迁移判断

当前项目不是要另起炉灶。正确路线是：

```text
2D 环境：证明有限通信边特征角色图机制有效
LAG smoke：证明 6DOF 状态可以构造成同类图表示
LAG short training：验证趋势是否保留
后续系统：再逐步加入雷达、导弹、有人机协同
```

如果 LAG smoke test 成功，即使短训练效果一般，也能在论文中作为“可扩展性讨论/初步迁移验证”；如果短训练也出现碰撞率或失效率下降趋势，则可以作为附加实验增强投稿质量。
