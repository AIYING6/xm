# 论文方向修正版路线图

日期：2026-07-13

## 1. 为什么需要修正方向

最新意图混淆矩阵显示：

```text
RI edge staged intent head:
plain accuracy = 0.587
balanced accuracy = 0.200
```

这说明当前意图分支基本塌缩为多数类预测，不能支撑“准确目标意图识别”这一强结论。

因此，现阶段不应把论文主创新写成：

```text
目标意图识别驱动的协同决策方法
```

更现实、证据更扎实的主线应调整为：

```text
面向有限通信无人机协同追逃的边特征增强角色图多智能体强化学习方法
```

其中意图分支保留为辅助模块或扩展实验，不作为当前主创新核心。

## 2. 当前可支撑的论文主张

已有 3-seed 通信压力主表：

```text
MAPPO: 3 seeds
GAT-MAPPO: 3 seeds
RI no-edge: 3 seeds
RI edge fixed-r8: 3 seeds
RI edge staged: 3 seeds
```

可支撑主张：

```text
1. 普通 MAPPO 在有限通信下方差较大，低通信半径下碰撞率较高。
2. GAT-MAPPO 能缓解部分有限通信问题，但在 radius=8/10 下仍不稳定。
3. 加入相对边特征后，RI-GMAPPO 在多数通信半径下降低碰撞率。
4. 分阶段随机通信半径微调能改善固定半径训练在 radius=10 上的泛化问题。
```

更适合论文标题的方向：

```text
Edge-Aware Role Graph Multi-Agent Reinforcement Learning for UAV Cooperative Pursuit under Limited Communication
```

中文可写为：

```text
面向有限通信无人机协同追逃的边特征增强角色图多智能体强化学习方法
```

## 3. 当前不应夸大的内容

不要写：

```text
模型实现了高精度目标意图识别。
意图预测是性能提升的主要原因。
RI-GMAPPO 全面大幅超过 MAPPO。
```

可以写：

```text
本文探索了目标行为辅助分支，但当前主要性能收益来自角色图表示、相对边特征和通信半径适应训练。
```

如果审稿人追问意图分支：

```text
把它放入消融或附录，并报告 balanced accuracy。
```

## 4. 建议最终方法命名

当前建议主方法命名：

```text
EA-RG-MAPPO
```

含义：

```text
Edge-Aware Role Graph MAPPO
```

如果保留 staged fine-tuning：

```text
EA-RG-MAPPO-S
```

含义：

```text
Edge-Aware Role Graph MAPPO with Staged Random-Radius Fine-Tuning
```

不建议继续用 `RI-GMAPPO` 作为论文主方法名，除非后续修复 intent head 的 balanced accuracy。

## 5. 最小可投稿实验包

### 5.1 主结果表

已基本具备：

```text
results/paper_result_tables.md
results/paper_comm_results.csv
```

还需补：

```text
per-seed appendix table
```

目的：

```text
防止审稿人质疑 3-seed 均值掩盖波动。
```

### 5.2 消融表

建议保留以下方法：

| 方法 | 作用 |
|---|---|
| MAPPO | 无图基线 |
| GAT-MAPPO | 普通图注意力基线 |
| RI no-edge | 角色图 + intent branch 的历史版本 |
| RI edge fixed-r8 | 相对边特征消融 |
| RI edge staged | 分阶段随机半径微调 |

论文中命名时可以改为：

| 当前实验名 | 论文名 |
|---|---|
| RI no-edge | RG-MAPPO |
| RI edge fixed-r8 | EA-RG-MAPPO |
| RI edge staged | EA-RG-MAPPO-S |

### 5.3 图表

已生成：

```text
results/figures/comm_success_rate.png
results/figures/comm_collision_rate.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
```

还建议补：

```text
1. per-seed success/collision scatter plot
2. radius-robustness summary bar
3. optional attention heatmap
```

## 6. 下一步执行顺序

优先级从高到低：

1. 生成 per-seed appendix table，把 MAPPO/GAT/RI 的每个 seed 结果展开。
2. 生成 per-seed scatter plot，展示 MAPPO 方差大、RI 更稳定。
3. 确定主方法采用 `EA-RG-MAPPO-S`，还是用 `EA-RG-MAPPO` 作为主方法、staged 作为鲁棒训练技巧。
4. 如果还有时间，再做 intent 修复；否则不要把 intent 放到主创新。
5. 开始写论文方法部分和实验设置部分。

## 7. 当前最现实的投稿策略

从二区目标出发，建议聚焦：

```text
有限通信 + 异构角色 + 相对边特征 + 稳定性实验
```

原因：

```text
1. 已有数据支撑。
2. 实验可复现，成本低。
3. 与无人机协同决策方向贴合。
4. 后续可自然扩展到 6DOF、雷达、导弹和有人机协同。
```

不要在当前阶段强行扩成完整空战系统。先把低维结果写扎实，再迁移 LAG/JSBSim。
