# LER 基线可学习性定位（2026-08-12）

状态：`LER_BASELINE_LEARNABILITY_DIAGNOSIS__TARGET_POLICY_NOT_SUFFICIENT`

## 本轮目的

在不改 LER、actor contract、reward、物理终点、PPO 超参数或正式评估协议的前提下，检查目标运动配置是否是当前 B1 零学习信号的唯一原因。

## 配对诊断

同一 B1 role-specific continuous-guidance 配置、strict actor contract、RMTN180、horizon=180：

| target policy | updates | seed 51001 | seed 51002 |
|---|---:|---:|---:|
| `straight` | 12 | 0/8 neutralized, 0 entry | 1/8 neutralized, 4 entry |
| `weaving_tiny` | 12 | 0/8, 0 entry | 0/8, 0 entry |
| `straight` | 60 | 0/8, 0 entry | 0/8, 0 entry |

结果文件：

- `results/ler_b1_diag_straight_u12.json`
- `results/ler_b1_diag_weaving_tiny_u12.json`
- `results/ler_b1_diag_straight_u60.json`

## 结论

`straight` 在 12 updates 的单个 seed 出现了短暂信号，但 60 updates 后两个 seed 均回到零；因此目标运动难度可能影响早期探索，却不能单独解释当前 baseline 的长期不可学习性。PPO ratio、梯度和 entropy 仍健康，说明不是数值崩溃。

当前仍不能进入 LER 正式 F1/F2。下一步应回到最小单拦截器 L0，对同一 strict mission endpoint 做可学习性重建；只有 B1 在 L0 获得跨 seed 稳定信号，才重新增加异构团队因素并恢复 LER 对照。

## 禁止的解释

- 不能把 `straight` 的 12-update 单点成功写成 baseline PASS；
- 不能通过延长训练、增加 seed 或修改正式 reward 来救当前结果；
- 不能把 LER 与零学习 baseline 的比较作为算法性能证据。
