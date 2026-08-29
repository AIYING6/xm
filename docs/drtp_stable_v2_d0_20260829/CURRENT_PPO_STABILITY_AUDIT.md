# 当前 PPO 稳定性审计

## 审计边界

本审计只读取当前提交 `bec33fc2` 的源码和既有 R1 训练日志，不执行 rollout、训练、checkpoint 评价或参数搜索。R1 输入包 SHA256 为 `a54406e8d2d14c4bc9fa25ea43388595c19f41d476631e1c743512c6c30c0b10`。对 15 条轨迹共 58,605 个 update 的静态统计不使用 seed 的成功/失败标签，仅用于确认遥测范围和缺口。

## 当前实现

| 项目 | 当前状态 | 审计结论 |
|---|---|---|
| policy clipping | 存在，`clip_coef=0.2` | 使用标准 clipped surrogate；它限制目标函数贡献，不是最终策略位移的硬约束。 |
| value clipping | 不存在 | critic 使用 `0.5*(return-value)^2`，没有 clipped value loss。 |
| gradient clipping | 存在，`max_grad_norm=0.5` | 对 actor 与 critic 的合并梯度执行全局 L2 clipping。`clip_grad_norm_` 返回裁剪前范数，因此日志 `grad_norm` 是 raw/pre-clip norm。 |
| target KL | 代码路径存在，R1 中关闭 | `target_kl=None`；即使启用，当前逻辑也只在 epoch 末停止后续 epoch，不回滚已经发生的 optimizer step。 |
| optimizer | 单个 Adam | 默认 `lr=3e-4`、`eps=1e-5`；actor/critic 是独立模块，但由同一个 optimizer 管理。 |
| advantage normalization | 存在 | 每个 PPO batch 执行零均值、单位标准差变换。 |
| reward normalization | 不存在 | 原始 reward 进入 GAE。 |
| return/value normalization | 不存在 | runtime state 中的 normalization placeholder 为 `None`。 |
| entropy regularization | 存在 | `entropy_coef=0.01`。 |
| PPO epochs | 4 | 每个 rollout batch 重复 4 个 epoch。 |
| minibatch | 256 graph | R1 为 `4 env × 64 step = 256 graph`，因此每个 epoch 恰好一个完整 minibatch。 |
| recurrent state | 不存在 | actor/critic 均为前馈网络，无 RNN hidden state。 |
| save/resume | 完整 | runtime checkpoint 保存 model、optimizer、Python/NumPy/Torch/CUDA RNG、环境状态、观测、episode 计数与 sampler 状态；严格恢复路径要求完整字段。 |
| NaN/Inf guard | 不完整 | sampler/config 有有限性检查；普通 PPO backward、gradient clipping 和 Adam step 没有 `error_if_nonfinite=True` 或更新事务回滚。 |
| update telemetry | 部分充分 | 已记录 loss、KL、clip fraction、raw grad norm、advantage/return statistics；裁剪后 gradient norm 与实际 Adam parameter displacement 未记录。 |

## Gradient clipping 与 Adam 位移不是一回事

当前顺序为：

1. 计算 actor + critic 联合 loss；
2. backward；
3. `clip_grad_norm_(all_parameters, 0.5)`；
4. 单个 Adam optimizer step。

因此现有 `grad_norm` 只能说明裁剪前总梯度大小。裁剪后范数在有限情况下可推断为 `min(raw_grad_norm, 0.5)`，但不能据此得到 Adam 的实际参数位移。Adam 位移还取决于一阶/二阶动量、epsilon、参数尺度和历史 optimizer state。

R1 的 label-free 静态统计如下：

| 量 | 结果 |
|---|---:|
| update rows | 58,605 |
| raw grad norm > 0.5 | 94.664% |
| raw grad norm > 1.0 | 74.224% |
| pooled raw grad P90 / P95 / P99 / max | 4.905 / 6.200 / 9.174 / 18.847 |
| pooled logged mean KL P90 / P95 / P99 / P99.9 / max | 0.001756 / 0.002417 / 0.004298 / 0.008173 / 0.016054 |
| actor/critic actual update norm available | 0 / 58,605 |
| PPO epochs other than 4 | 0 |

结论：gradient clipping 已在绝大多数 update 上实际生效，但 seed 分叉仍存在；再次简单降低 `max_grad_norm` 与现有机制高度重复，也不能直接控制 Adam 位移。由于 actual displacement 遥测缺失，当前不能为“bounded parameter displacement”冻结一个有证据来源的阈值。

## KL 的现有语义缺口

日志 `approx_kl` 是每个 epoch 在 optimizer step 之前、相对于 rollout old log-probability 计算的估计值，最终写入 4 个 epoch 的均值。它不是：

- 第 4 次 optimizer step 后的最终 KL；
- 每个 step 的最大 KL；
- 超阈值 update 被回滚后的 accepted KL。

因此现有日志可以证明没有共同的 KL 爆炸先兆，但不能证明最后一次 Adam step 的实际策略变化被硬约束。

## 审计结论

当前 PPO 已有软 policy clip 和高频触发的 gradient clipping，但没有 post-step policy trust region、没有 rollback、没有 actual parameter-displacement telemetry，也没有训练张量级 non-finite transaction guard。可新增的机制必须与这些已存在措施区分，且不能把相关性改写为 PPO/critic 根因。
