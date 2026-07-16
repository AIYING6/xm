# 论文实验部分初稿

日期：2026-07-13

## 1. 实验目的

本文实验旨在验证所提出的边特征增强角色图多智能体强化学习方法在有限通信无人机协同追逃任务中的有效性。

重点考察三个问题：

1. 在通信半径受限时，普通 MAPPO 是否容易出现性能下降和碰撞增加。
2. 普通图注意力 GAT-MAPPO 是否足以解决有限通信下的协同问题。
3. 引入相对边特征和分阶段随机通信半径微调后，策略是否能获得更稳定的跨半径性能。

## 2. 实验环境

实验采用二维异构无人机协同追逃环境。环境包含 3 架追击无人机和 1 个机动目标。追击无人机具有不同最大速度、感知范围和能耗系数，用于模拟异构协同条件。目标采用混合机动策略，包括远离最近追击者逃逸和随机转向机动。

环境状态包括：

```text
1. 每架无人机的局部观测；
2. 集中式 critic 使用的全局状态；
3. 图结构观测，包括无人机节点、目标节点、角色标记、邻接关系和相对边特征。
```

有限通信通过通信半径控制。当队友超出通信半径时，其局部观测槽位被置零，图邻接关系也相应受限。实验使用通信半径：

```text
4, 6, 8, 10
```

主评估场景为：

```text
target_policy = mixed
target_speed = 0.75
episodes = 300 per seed for final MAPPO/GAT/EA-RG-MAPPO-S comparison
seeds = 0, 1, 2
```

## 3. 对比方法

### 3.1 MAPPO

MAPPO 是无显式图结构的多智能体强化学习基线。所有智能体共享策略网络，critic 使用集中式状态。该方法用于衡量在无图协同表示下，策略在有限通信条件中的鲁棒性。

### 3.2 GAT-MAPPO

GAT-MAPPO 在 MAPPO 基础上加入图注意力模块。策略输入由局部观测编码和图节点嵌入拼接而成。该方法用于判断普通图注意力是否足以建模通信受限下的协同关系。

### 3.3 RG-MAPPO

RG-MAPPO 表示角色图版本，用于消融角色图结构和辅助行为分支的影响。该版本不使用相对边特征。

### 3.4 EA-RG-MAPPO

EA-RG-MAPPO 在角色图基础上加入相对边特征，包括相对位置、距离、相对方位、相对速度、通信可达标记和目标节点标记。边特征用于增强图注意力对空间关系和通信关系的建模能力。

### 3.5 EA-RG-MAPPO-S

EA-RG-MAPPO-S 在 EA-RG-MAPPO 基础上加入分阶段随机通信半径微调。第一阶段在固定通信半径下训练，第二阶段从第一阶段 checkpoint 出发，在随机通信半径区间内进行短程微调。

该设计的目的不是单纯增加训练量，而是缓解固定通信半径训练导致的跨半径泛化不足。

## 4. 训练协议

MAPPO 和 GAT-MAPPO 首先在低速直线目标上进行课程训练：

```text
target_policy = straight
target_speed = 0.45
```

课程训练用于让策略先掌握基础追击能力，再评估其对高速混合机动目标的迁移能力。

RI/EA-RG 系列方法在相同环境接口和评价指标下训练，并在通信压力测试中统一比较。

最终主表报告：

```text
300 evaluation episodes per seed
mean ± std over 3 seeds
```

消融表报告：

```text
100 evaluation episodes per seed
mean ± std over 3 seeds
```

## 5. 评价指标

使用以下指标：

| 指标 | 含义 |
|---|---|
| success_rate | 成功拦截目标的比例 |
| collision_rate | 追击无人机之间发生碰撞的比例 |
| timeout_rate | 未能在最大步数内完成任务的比例 |
| avg_steps | 任务结束平均步数 |

其中，collision_rate 是本文特别关注的安全性指标。在无人机协同任务中，单纯提高成功率并不足够；如果伴随高碰撞率，则策略缺乏实际可用性。

## 6. 主结果分析

通信压力测试表明，MAPPO 在部分 seed 中可以取得较高成功率，但方差较大，尤其在较小通信半径下容易出现碰撞。GAT-MAPPO 在 radius=4/6 下表现较好，说明普通图注意力能够缓解一部分有限通信问题；但其在 radius=8/10 下成功率和碰撞率仍不稳定。

300-episode 复评后，EA-RG-MAPPO-S 在四个通信半径下保持了更集中的表现：

```text
radius=4:  success=0.926 ± 0.004, collision=0.054 ± 0.007
radius=6:  success=0.919 ± 0.012, collision=0.064 ± 0.006
radius=8:  success=0.890 ± 0.021, collision=0.083 ± 0.012
radius=10: success=0.879 ± 0.017, collision=0.086 ± 0.020
```

与 MAPPO 相比，EA-RG-MAPPO-S 的优势主要体现在：

```text
1. collision_rate 更低；
2. seed 间波动更小；
3. 在低通信半径下更稳。
```

与 GAT-MAPPO 相比，EA-RG-MAPPO-S 的优势主要体现在：

```text
1. radius=8/10 下成功率更高；
2. collision_rate 更低；
3. 跨半径性能更均衡。
```

## 7. 消融分析

RI no-edge、RI edge fixed-r8 和 RI edge staged 的比较说明：

1. 相对边特征能降低 radius=4 下的碰撞率，并修复部分 seed 在 radius=8 下的不稳定问题。
2. 固定 radius=8 训练会损害 radius=10 泛化。
3. 分阶段随机通信半径微调能恢复 radius=10 表现，但会牺牲少量 radius=4/radius=8 的峰值性能。

因此，EA-RG-MAPPO-S 更适合作为最终主方法，因为它不是单点最优，而是在多个通信半径下更均衡。

## 8. 可视化分析

已生成两个轨迹案例图：

```text
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
```

这些案例显示，在相同环境种子下，基线方法可能出现碰撞，而 EA-RG-MAPPO-S 能保持成功追击。轨迹图应作为定性补充，与多 seed 统计结果配合使用。

同时生成了 per-seed 散点图：

```text
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
```

散点图用于展示不同 seed 的分布，有助于说明 MAPPO 的高方差和 EA-RG-MAPPO-S 的稳定性。

此外生成了 RI 注意力热力图：

```text
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

在 radius=4 下，部分队友边不可达，注意力主要集中在自身和目标节点；在 radius=10 下，通信图更密集，注意力在队友和目标之间分布更均匀。该结果可用于解释边特征角色图如何随通信条件变化调整信息聚合。

## 9. 关于目标意图分支的说明

当前实验曾加入目标意图辅助分支，但混淆矩阵显示该分支存在类别塌缩：

```text
plain accuracy = 0.587
balanced accuracy = 0.200
```

因此，当前论文不应把“准确目标意图识别”作为主结论。更合理的处理方式是：

```text
1. 将目标意图分支作为探索性辅助模块；
2. 在附录中报告 balanced accuracy；
3. 后续若继续强化该方向，应加入短时历史或目标运动状态估计。
```

## 10. 仍需补充的材料

最小补充项：

1. 在正文中加入主结果表。
2. 在附录中加入 per-seed 表。
3. 对图中每条曲线和散点图写简短分析。
4. 确认最终方法命名：建议使用 `EA-RG-MAPPO-S`。

可选增强项：

1. 注意力热力图。
2. 失败案例统计。
3. 5-seed 或 300 episode 评估。
4. LAG/JSBSim 小规模迁移验证。
