# v1.6R R2 诊断收束

状态：`R2_PARTIAL__PPO_UPDATE_STABILITY_BOTTLENECK_IDENTIFIED`

本文件记录 R2 development-only 诊断结论。所有结果均不是正式 F1/F2 性能证据，不授权增加训练预算、调 PPO 超参数或实现新方法。

## 已确认

| 检查项 | 结果 | 结论 |
|---|---:|---|
| 3DOF 物理可达性 | oracle 8/8；合法 scripted 7/8 | 任务不是物理不可达 |
| 合法 target evidence | checkpoint evidence rate=1.0 | 失败不在信息获取入口 |
| actor/action 接口 | scripted action BC MAE≈0.024 | 接口能够表达有效追击动作 |
| PPO 更新链 | grad norm>0，参数发生变化 | 不是 actor 未更新 |
| PPO ratio/clipping | ratio≈1，clip fraction=0 | 未发现单步 ratio 爆炸/clip 饱和 |
| 动作健康 | 无 `|action|>0.95` 饱和，`exp(log_std)≈0.60–0.61` | 不是最终动作边界/熵塌缩 |
| 单步动作反事实 | learned reward 比 scripted 低约 0.0020–0.0036 | learned 方向未形成稳定物理进展 |
| actor-only 对照 | joint PPO 1/2；actor-only 0/2 | 不能归因于 centralized critic 单独退化 |

## 失败阶段

```text
合法 target evidence
        ↓
持续 pursuit / attack-geometry acquisition 失败
        ↓
neutralization 未发生
```

R2 当前最保守解释是：标准 PPO 在合法 evidence 已存在时，尚未学会把 observation 转换为方向正确、可持续的 pursuit control。该解释仍不区分优势方向、长期时序信用与 rollout 分布漂移，因此不得包装成已验证的新算法问题。

## 冻结边界

- 不追加 updates、seed 或正式训练资源；
- 不调 reward、learning rate、entropy、clip、网络规模；
- 不以 scripted/BC 结果替代 RL baseline；
- 不把 R2 development 结果写入正式论文性能表；
- 后续若继续，只能做已有 checkpoint 的只读分析，或另立新的、预注册的学习接口实验。

## 工程回归

`smoke_test_env.py`、`smoke_test_intercept_3d_env.py` 与 `check_reproducibility_artifacts.py` 均通过。连续 guidance、oracle guidance 与 mission endpoint 回归也通过。
