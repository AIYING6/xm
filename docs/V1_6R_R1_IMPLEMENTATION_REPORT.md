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
- 新增 `scripts/diagnose_v16r_behavior_cloning.py`，用合法 scripted action 做接口可表达性诊断。
- 新增 `scripts/diagnose_v16r_bc_warmstart_ppo.py`，检查 unchanged PPO 对合法 BC 初始策略的影响。
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

Behavior-cloning 对照显示：scripted 合法动作在当前 actor observation/action 接口上可拟合（平均绝对动作误差约 `0.024`），4 个新 episode 中有 `1` 个 neutralized。该诊断支持“接口可表达、PPO exploration/credit assignment 失败”的判断，但 BC 不属于 v1.6R baseline 或论文方法证据。

BC warm-start 后接原 PPO 20 updates 的诊断为 `0/4 neutralized`（BC fit loss 约 `0.007`）。这表明当前 PPO update 会破坏有限的 pursuit 控制，而不是稳定保留它；该结果只用于定位 optimization pathology，不授权增加模块或正式方法训练。

随后进行 actor-only 对照：从同一合法 behavior-cloning 起点复制两份 actor，一份执行完整 joint PPO update（actor+centralized critic），另一份仅更新 actor 参数，其他 batch、动作分布与环境条件完全一致。结果为：

```text
bc_loss = 0.00735
joint PPO:      1/2 neutralized
actor-only PPO: 0/2 neutralized
```

该结果不能支持“critic 更新单独造成退化”的解释；在本次小样本诊断中，actor-only 更新并未比 joint update 更稳定，反而未完成 neutralization。因此当前更保守的定位是：**原 PPO actor update / on-policy distribution shift 与 acquisition pursuit 控制之间存在不稳定耦合**，但尚未区分具体是 clipping、优势尺度、动作熵衰减还是 rollout 分布漂移。该诊断仍不授权调参、增加训练预算或实现新方法。

当前 R2 状态维持：

```text
R2_PARTIAL__PPO_UPDATE_STABILITY_BOTTLENECK_IDENTIFIED
```

为避免把问题误判为 PPO clipping 数值故障，又在现有 smoke/update 路径中加入只读稳定性指标：`adv_mean/std`、`ratio_std`、`clip_fraction` 与归一化优势绝对均值。12-update baseline smoke 的最后一次更新显示：

```text
ratio_mean ≈ 1.0
ratio_std < 2.3e-7
clip_fraction = 0
adv_std ≈ 0.56–0.59
actor_grad_norm > 0
actor_param_delta ≈ 0.007–0.011
```

因此当前短更新路径没有出现 ratio 爆炸或 clipping 饱和；优势也不是全零，actor 确实发生更新。该结果将“单步 PPO ratio/clip 数值失稳”从主要嫌疑中降级，但不能排除多轮 rollout 分布漂移、优势方向与 pursuit 目标错配或动作熵退化。后续若继续，只允许基于已有 checkpoint 做训练轨迹对齐分析，不授权调参或增加预算。

冻结 checkpoint 的动作健康审计也已完成。B0/B1/B2 两个 seed 的 deterministic turn/climb 均未出现边界饱和（`max_abs_action_fraction_gt_0.95 = 0`），连续动作仍有非零方差；learned `exp(log_std)` 约为 `0.60–0.61`，未塌缩为近零熵。由此可排除“最终 checkpoint 因动作边界或探索方差塌缩而失败”的简单解释。结合前面的动作对齐结果，当前更接近：策略输出虽然数值健康，但方向性 pursuit control 与物理几何进展不一致。

进一步进行了同一物理初态下的单步反事实动作比较。对每个 checkpoint，在合法 evidence 出现后分别执行 learned action 与 legal scripted pursuit action，比较 v1.6R reward 和几何分数。6 个 checkpoint 的 learned-minus-scripted 单步 reward gap 均为负，范围约 `-0.0020` 至 `-0.0036`；例如 B0-17101 为 `-0.00359`，B1-17101 为 `-0.00347`。该结果说明 learned action 并非被 reward 直接偏好，且 scripted action 在相同状态下稳定取得更高即时物理进展。它支持“策略方向性与任务进展不一致”的定位，但仍不能单独证明 reward 设计错误，因为差异也可能来自多步控制和动作后果的时序信用分配。

该反事实审计的实现为 `scripts/diagnose_v16r_one_step_action_value.py`，只读取冻结 checkpoint，不改变环境、奖励或训练协议。当前 R2 诊断链已覆盖：可达性、合法 evidence、动作接口可表达性、PPO 梯度更新、ratio/clipping 数值、动作熵/边界健康，以及同状态 learned-vs-scripted 即时物理价值差异。综合证据支持将 R2 归纳为：**任务可达且接口合法，但标准 PPO 尚未学会把合法 target evidence 转换为方向正确的持续 pursuit control。**

## R2R：competent-policy retention test

按照一次性冻结协议，从同一 behavior-cloning policy 出发，比较 BC-Frozen 与原 PPO 在 update `0/10/30/60` 的闭环表现。环境、reward、physics、PPO 超参数、评估 seeds 均未改变；该实验不实现 TEAR，也不追加正式训练资源。

关键结果（每个 checkpoint 8 个 matched evaluation episodes）：

```text
seed 17101: BC-Frozen geometry=1.00, neutralization=0.25
            PPO-10/30/60 geometry=0.25/0.25/0.25,
                         neutralization=0.00/0.00/0.00

seed 17102: BC-Frozen geometry=1.00, neutralization=0.125
            PPO-10/30/60 geometry=0.25/1.00/0.25,
                         neutralization=0.125/0.25/0.00
```

BC-Frozen 本身能够在闭环中进入 geometry，说明此前的 one-step BC 拟合并非完全虚假；而 PPO 更新后 geometry acquisition 在两个 seed 都明显下降，并在 update 60 时 neutralization 均为 `0/8`。因此 R2R 支持：**当前核心瓶颈更接近 PPO policy improvement 对已有物理上有用 pursuit 行为的破坏，而不是单纯无法发现任何 pursuit 行为。**

状态升级为：

```text
R2R_PASS__PPO_COMPETENT_BEHAVIOR_RETENTION_FAILURE_IDENTIFIED
```

该状态只授权一次后续学习机制设计；不授权 reward、physics、actor contract、horizon、evaluation protocol 或 TEAR 上游模块修改。

## R3：evidence-masked behavior-retention pilot

R3 实现了唯一授权的 behavior-retention 机制：在合法 evidence mask 为 1 的状态，对当前 PPO actor 与冻结 BC reference actor 的 deterministic guidance 施加 retention loss，`retention_coef=1.0` 预先冻结。所有其他训练与环境条件保持不变。collector、PPO 和 retention 单元回归均通过。

两 seed、8 个 matched evaluation episodes 的关键结果：

```text
seed 17301:
  vanilla PPO  geometry 1.00 → 0.625 → 0.00 → 0.00
  retention    geometry 1.00 → 0.00  → 0.00 → 0.875
  neutralization: vanilla 0.00 at update 60; retention 0.00

seed 17302:
  vanilla PPO  geometry 1.00 → 0.00 → 0.00 → 0.625
  retention    geometry 1.00 → 1.00 → 1.00 → 1.00
  neutralization: vanilla 0.00 at update 60; retention 0.00
```

R3 表明 evidence-masked retention 可以在部分 seed/阶段保留 geometry acquisition，但两个 seed 的 early trajectory 仍不稳定，且最终没有 neutralization endpoint 改善。因此不能判定 behavior-retention 机制已被支持，也不能进入正式 F1。当前状态更新为：

```text
R3_PARTIAL__ACQUISITION_RETENTION_WITHOUT_MISSION_GAIN
```

按预冻结止损条件，不再调 `retention_coef`、追加 seed/update 或增加第二个 retention 模块。若没有新的外部研究决策，v1.6R 算法线应在此关闭，转为平台/诊断成果或路线 C。

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
