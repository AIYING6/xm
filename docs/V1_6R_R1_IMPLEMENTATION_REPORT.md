# v1.6R R1 实现报告

状态：`R1_PARTIAL__LEGAL_INTERFACE_INITIAL_PASS__FULL_REGRESSION_PENDING`

日期：2026-08-11

## 已完成

- 新增 `envs/v16r_legal_interface.py`；
- 新增 `LegalObservationInterface`；
- 新增 `LegalTargetEvidence`，统一表达 local sensing / delivered cache / none；
- 新增 recipient-specific graph builder；
- 禁止 interface 读取 `last_detected_target_*` 和 `_estimated_target_state()`；
- graph 仅使用当前 recipient 合法 evidence，并携带 source/path/age/confidence；
- 新增 `scripts/test_v16r_legal_observation_interface.py`。
- 新增 legacy-safe 的 `step_guidance()` continuous turn/climb 接口；旧 `step(int_actions)` 保持不变；
- 新增 `scripts/test_v16r_continuous_guidance.py`。
- 新增 `envs/v16r_env_adapter.py`，将 continuous guidance 与 recipient-specific graph 接入标准 reset/step 外观；
- 新增 `scripts/test_v16r_env_adapter.py`。
- 新增 `algorithms/mappo/continuous_guidance_distribution.py`，采用 tanh-squashed Gaussian 与 Jacobian 修正；
- 新增 `scripts/test_v16r_continuous_distribution.py`。
- 新增最小 `ContinuousGuidanceActor` vanilla actor；
- 新增 `scripts/test_v16r_continuous_policy.py`。
- 新增 `scripts/smoke_v16r_actor_env_rollout.py`，完成 actor→adapter→environment 无训练 rollout smoke。
- 新增 `algorithms/mappo/v16r_rollout.py`，保存 recipient graph、continuous action、old log-prob 和 reset mask；
- 新增 `scripts/test_v16r_rollout_collector.py`。
- 新增 `algorithms/mappo/v16r_ppo.py`，包含 GAE、clipped PPO loss 和 centralized critic；
- 新增 `scripts/test_v16r_ppo_update.py`。
- 新增透明 B2 `RecipientGraphGuidanceActor`（统一图池化，不含 TEAR 机制）；
- 新增 `scripts/test_v16r_recipient_graph_actor.py`。
- 增加独立 `v16r_mission_mode`：物理攻击几何连续 4 步后才 `NEUTRALIZED`，legacy mode 不变；
- 新增 `scripts/test_v16r_mission_endpoint.py` 与 `scripts/test_v16r_oracle_guidance.py`。
- 新增 `scripts/test_v16r_legal_scripted_controller.py`，验证严格合法信息下的 scripted 可达性。
- 新增 `scripts/diagnose_v16r_r2_failure_stages.py`，对保存的 R2 checkpoint 做 evidence→geometry→neutralization 阶段定位。
- 新增 `scripts/diagnose_v16r_action_alignment.py`，比较合法 scripted pursuit 与 checkpoint guidance。
- rollout/PPO 显式支持 `graph_conditioned` 模式；
- 新增 `scripts/test_v16r_b0_b2_smoke.py`。
- rollout 支持固定合法 history window；
- 新增 `scripts/test_v16r_b1_history_smoke.py`。

## 当前验证

```text
PYTHONPATH=. D:/Anaconda/envs/.conda/envs/cac/python.exe \
  -m scripts.test_v16r_legal_observation_interface

 checks=11, failed=0
```

Continuous guidance 回归：

```text
checks=5, failed=0
```

Adapter 端到端回归：

```text
checks=5, failed=0
```

Continuous distribution 回归：

```text
checks=4, failed=0
```

已验证 sampled action 与重算 log-prob 一致、动作有界、梯度有限。该分布尚未接入 PPO collector。

Continuous actor 回归：

```text
checks=4, failed=0
```

已验证 stochastic/deterministic 输出、log-prob 和梯度；该 actor 尚未进入训练循环。

Actor→环境 rollout：

```text
checks=4, failed=0
```

Collector 回归：

```text
checks=6, failed=0
```

已验证 collector old log-prob 可重算、recipient graph 维度保留、reset mask 为二值。该 collector 目前只收集，不执行 PPO update。

PPO synthetic update 回归：

```text
checks=2, failed=0
```

已验证 GAE、clipped ratio、centralized critic、梯度更新和有限数值。该测试使用合成 batch，不代表环境 learnability。

B2 graph actor 回归：

```text
checks=3, failed=0
```

该 baseline 只做 legal graph pooling，不包含 temporal alignment 或 conflict-aware fusion。

B0/B2 one-update smoke：

```text
checks=2, failed=0
```

B0 flat actor 与 B2 unified-graph actor 均完成一次无正式结论的 PPO update。

B1 history baseline smoke：

```text
checks=2, failed=0
```

B1 当前使用固定 4-step legal observation history，仅作为透明 baseline，不含 latent stage 或 progress conditioning。

## R2 初筛（development-only）

在修正 continuous guidance 的 deterministic closure controller 后，scripted guidance 校准为：

```text
oracle episodes=8, oracle_neutralized=8
```

这证明 v1.6R 物理任务可达。随后 B0/B2 各 2 个 seed、12 updates、horizon=32 的短初筛均为 `0/8` neutralization。该结果不是 NO-GO：预算是初筛预算，B1 尚未加入，且需要先检查 reward/trajectory learning signal。当前不追加训练、不改变超参数，先做现有 rollout 的 reward 与动作诊断。

R2 只读诊断显示：未训练 actor 仍有正的 range-progress reward（mean reward 约 0.06–0.08），target evidence 出现比例约 0.52–0.72，动作没有边界饱和；但四组轨迹的 attack geometry score 最大值均为 0。当前解释是“基础接近信号存在，但尚未进入物理攻击几何”，不能把短预算 0% 写成 benchmark NO-GO。

PPO 梯度诊断进一步确认实现链正常：4-update smoke 中 B0/B2 的 `actor_grad_norm` 均为正，`actor_param_delta` 约 0.009–0.015；因此当前 0% 不是“actor 没有更新”的工程 bug。仍不能据此判定任务不可学，下一步应完成 B1 history-matched baseline，并分析 acquisition 轨迹。

补充的合法 scripted controller 只使用 local sensing/delivered cache，在 8 个 episode 中 `7/8 neutralized`。因此严格信息任务物理可完成；但 B0/B1/B2 在冻结的 60-update、2-seed protocol 下均为 `0` neutralization。当前状态冻结为：

```text
R2_NO_GO__BASELINE_LEARNABILITY_NOT_ESTABLISHED__FAILURE_LOCALIZATION_REQUIRED
```

这不是 TEAR 的性能结论，也不是立即修改 reward/训练预算的授权。下一步只允许用已有 rollout/新增透明诊断定位 acquisition 前的 policy-gradient 失败阶段；在 baseline learnability 建立前不实现 TEAR。

R2 checkpoint 阶段定位结果：

```text
evidence_rate = 1.0（所有 B0/B1/B2 checkpoint）
seed 17101 geometry_entry_rate ≈ 0.5
seed 17102 geometry_entry_rate = 0.0
neutralization_rate = 0.0
```

因此失败发生在 `legal evidence → attack geometry acquisition`，不是 target evidence 获取失败，也不是 physical endpoint 不可达。当前状态细化为：

```text
R2_PARTIAL__EVIDENCE_TO_GEOMETRY_ACQUISITION_BOTTLENECK_IDENTIFIED
```

动作对齐诊断进一步显示：evidence 到达后，checkpoint policy 与同一合法状态下 scripted pursuit guidance 的二维动作误差约为 `1.1–1.7`（归一化 turn/climb）；range 仍有缓慢下降，但没有稳定进入 attack geometry。该结果支持“合法证据到达后，policy 没有学会将证据转换为正确 pursuit control”的 failure localization，不构成新方法结果。

已覆盖：

1. 无合法 evidence 时改变 global target 不改变 actor evidence；
2. local sensing 可更新对应 recipient；
3. valid delivered cache 可更新 recipient，source/path 保留；
4. expired cache 不进入 actor；
5. recipient graph 形状和有限值；
6. graph 不使用全局 target fallback；
7. source/provenance relation 可追溯。
8. recipient-0 cache 不泄漏到 recipient-1；
9. recipient-0 local sensing 不泄漏到 recipient-1。
10. recipient graph stack 显式保留 recipient 维度；
11. relation 维度与 graph schema 一致。

## 尚未通过的门

这不是 R1 完成。静态检查现有 MAPPO collector 后确认：当前 rollout 是前馈的，没有 recurrent hidden state；因此现阶段没有 hidden-state 绕过 expiry 的实际路径，但未来接入 GRU/recurrent actor 时必须显式加入 reset mask。

同时发现两个明确的 R1 集成阻塞：

1. legacy collector 仍接收环境返回的共享 graph，而不是 `[recipient, node, node, feature]` 的 recipient-specific graph；
2. legacy 3DOF 环境默认仍使用离散 27-action；v1.6R 已有独立 continuous guidance collector/PPO update，但 legacy MAPPO collector 仍不改动。

这两个差异不能通过字段别名掩盖，必须在 R1 适配层中显式解决。仍需补充 graph provenance 对照、neutralization precedence 和 continuous-action 接口回归。全部通过前禁止 B0/B1/B2 训练。

## 备注

当前旧环境仍保留 legacy discrete action 与旧兼容字段；本次没有修改动力学、reward 或训练器。v1.6R 的 continuous guidance 与最终 actor graph 接口必须在后续 R1 适配层中显式冻结，不能把 legacy 字段自动当作新证据。
