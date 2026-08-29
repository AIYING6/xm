# Stable-v2 选中设计：DRTP-KLR

## 一句话定义

`DRTP-KLR = Original DRTP-SG-MAPPO + deterministic post-step actor KL rollback`。

它不保留 Conservative-DRTP 的 trust-region sampler 或 20% uniform anchor，不修改网络、reward、环境、PPO objective、训练条件、actor information boundary 或 DRTP sampler。

## 为什么属于 robust-by-design

该设计不假定 sampler、critic 或某个梯度指标已被证明是根因。它只建立一个训练不变量：每次被接受的 actor optimizer step，相对于产生当前 rollout 的行为策略，其 full-batch empirical approximate KL 不得超过冻结边界。

正常 update 不改变；只有越界 update 被精确拒绝。因此它比永久降低学习率、增强 anchor 或全程平均参数更有利于保留 Original DRTP 的高收益上尾，也直接回应 seed3004 所揭示的“不能为了保护下尾而长期压制正常学习”。

## 精确算法语义

R1 每个 rollout 含 256 graph，PPO 重用该完整 batch 四个 epoch。对每个 epoch：

1. 保存 actor 参数和 Adam 中仅属于 actor 参数的 state slot；critic 不共享 actor 参数；
2. 按 Original DRTP 完成 loss、backward、`max_grad_norm=0.5` clipping 和单次 Adam step；
3. 在同一 on-policy rollout batch、同一 recorded actions 和 old log-probabilities 上重新前向，计算

\[
\widehat D_{KL}=\operatorname{mean}\left[(r-1)-\log r\right],
\quad r=\exp(\log\pi_{new}(a|s)-\log\pi_{old}(a|s));
\]

4. 若 metric 有限且 `<= 0.02`，接受 actor step；
5. 若 `> 0.02`，恢复该 epoch 前的 actor 参数及其 Adam state，保留本 epoch已经完成且与 actor 参数分离的 critic step，并终止本 rollout 的后续 PPO epoch；
6. 若任意 actor 参数、optimizer state 或 KL 非有限，恢复整个 epoch 前的 model + optimizer transaction，并将运行标记为技术无效；不得把 NaN rollback 当作正常稳定化成功；
7. 下一次 rollout 只能由最后一个被接受的 actor 状态生成。

由于每个已接受 actor state 都经过 post-step 检查，越界时又恢复到上一个已接受状态，最终 actor 满足冻结边界。没有 interpolation、backtracking 或重复尝试，因此不存在隐藏的 step-size sweep。

## PPO / on-policy 合法性

- guard 只使用当前 rollout 的 states、actions 和 old log-probabilities；
- 不引入 replay buffer、旧 checkpoint 或未来 reward；
- 越界 actor step 在下一次 rollout 前被撤销；
- 被接受 actor 仍由标准 PPO clipped objective 产生；
- critic 与 actor 是代码中的分离模块，actor rollback 不恢复已接受的 critic parameter/state；
- 同一 optimizer 的 Adam state 按 parameter 保存，因此 actor state slot 可精确恢复；技术验收必须证明这点以及 save/resume 一致性。

## 计划修改文件（尚未实施）

| 文件 | 计划变更 |
|---|---|
| `algorithms/ri_gmappo/simple_ri_gmappo.py` | 增加 opt-in guard mode；实现 actor 参数/Adam state transaction、post-step full-batch KL、rollback 与 telemetry。默认关闭，保持所有历史路径不变。 |
| `scripts/run_drtp_stable_v2_technical_audit.py` | 只做技术语义测试：越界/不过界、Adam state 精确恢复、critic 保留、non-finite fail-fast、deterministic replay、mid-window save/resume。 |
| `scripts/run_drtp_stable_v2_single.py` | 未来经授权后构造冻结 pilot config；Original DRTP 与 UTR 路径不启用 guard。 |
| `scripts/run_drtp_stable_v2_evaluation.py` | 未来冻结 tape 评价；禁止 checkpoint promotion。 |
| `scripts/aggregate_drtp_stable_v2_pilot.py` | 实现预注册 pilot gate，不参与训练。 |
| `configs/drtp_stable_v2_pilot_tape.json` | 下一阶段才冻结新的 development-only tape。 |

## 必须新增的 telemetry

- `policy_kl_post_step`；
- `policy_kl_threshold`；
- `policy_guard_triggered`、`policy_guard_reason`、`policy_guard_epoch`；
- `policy_steps_attempted`、`policy_steps_accepted`；
- `actor_attempted_update_l2`、`actor_accepted_update_l2`（只读诊断，不作 gate）；
- `actor_optimizer_state_restored`；
- `critic_step_retained_after_actor_rollback`；
- per-run cumulative intervention count/rate；
- finite-state assertions。

这些字段不得进入 actor、critic、reward 或 sampler。

## 预期失败模式

1. intervention 始终为 0：设计在该预算下没有实际活动，pilot 不支持继续；
2. intervention 过于频繁：clip-derived boundary 对本实现过严，可能损害上尾；禁止调阈值补救；
3. KL 受控但 catastrophic 不减少：大更新不是足够的工程控制点，候选关闭；
4. seed3004 类型的高收益学习被削平：upper-tail gate 失败；
5. actor rollback 与 Adam state/save-resume 不完全一致：P2 技术 NO-GO，不得训练；
6. safety 通过 timeout/collision 恶化换取 reward：科学 gate 失败。

## 当前授权边界

本文件是设计规格，不是实现授权。没有源码机制被加入，也没有训练、rollout、checkpoint evaluation 或参数搜索被执行。
