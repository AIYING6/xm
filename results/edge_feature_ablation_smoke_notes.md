# Edge Feature Evaluation-Time Ablation

说明：该实验不重新训练模型，只在评估时将 EA-RG-MAPPO-S 的部分 edge feature 维度置零，用于诊断策略对不同边信息的依赖。结果只能作为机制分析和附录证据，不应替代训练期结构消融。

| Radius | Ablation | Zeroed dims | Success | Collision | Timeout | Avg steps |
|---:|---|---|---:|---:|---:|---:|
| 4 | none | none | 1.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 80.3 ± 3.7 |
| 4 | zero_all_edge_features | 0 1 2 3 4 5 6 7 8 9 | 0.833 ± 0.236 | 0.167 ± 0.236 | 0.000 ± 0.000 | 81.8 ± 3.6 |

边特征维度定义：

- `0`: rel_x/world
- `1`: rel_y/world
- `2`: distance/world
- `3`: distance/comm_radius
- `4`: cos(bearing)
- `5`: sin(bearing)
- `6`: rel_vx/1.5
- `7`: rel_vy/1.5
- `8`: comm_reachable
- `9`: target_node_flag

论文使用边界：

```text
可以写：评估时屏蔽边特征会改变策略表现，说明 EA-RG-MAPPO-S 确实利用了相对几何/速度/通信相关信息。
谨慎写：该结果不是独立训练的结构消融，不能单独证明某一类边特征在训练机制上必然最优。
```
