# LER-MAPPO 正式实验前状态

状态：`LER_PRE_FORMAL_BLOCKED__BASELINE_LEARNABILITY_NOT_ESTABLISHED`

## 已完成

- LER actor 已接入真实 v1.6R collector/PPO；
- legal evidence mask 与 role id 在真实 rollout 中正确传递；
- identity-preserving evidence gate 回归通过；
- `RMTN180 / max_steps=180` 两 seed、60 updates development pilot 已运行；
- 同配置 role-specific B1 对照已运行。

## 结果

LER 与 B1 在当前 strict actor-contract 配置下均为：

- geometry entry：0；
- neutralization：0；
- PPO ratio、梯度、参数更新正常；
- rollout evidence mean≈0.333，reward mean≈0.118，说明不是进程或 NaN 故障。

因此目前不能进入正式 F1/F2。缺失的不是算法实现，而是**在当前冻结配置下 vanilla role-specific baseline 的可学习性证据**。

## 硬门

只有当 B1 在同一 RMTN180、同一 strict actor contract 下出现稳定非零 geometry/mission signal，LER 才有资格进入正式实验。不得通过增加正式训练预算、改变 evaluation seeds 或加入新模块绕过该门。

下一步只允许做配置/任务可学习性差异定位，重点核对历史 L0 可学习运行与当前 pilot 的 reward、初始状态、target maneuver、action scaling 和终止语义；在该门通过前，正式论文实验保持冻结。

2026-08-12 已完成目标运动配置诊断，见 `docs/LER_BASELINE_LEARNABILITY_DIAGNOSIS_20260812.md`：`straight` 在 12 updates 的单点信号未能在 60 updates 保留，因此不能将问题归因于 target maneuver 单一因素。下一步回到最小 L0 可学习性重建，再逐层恢复异构团队因素。
