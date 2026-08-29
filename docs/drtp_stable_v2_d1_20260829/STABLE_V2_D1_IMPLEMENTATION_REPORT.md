# Stable-v2 D1 实现报告

## 裁决

`D1_TECHNICAL_PASS — PILOT TRAINING NOT YET AUTHORIZED`

本阶段把 D0 唯一候选 `DRTP-KLR` 实现为默认关闭的 opt-in PPO actor update guard。实现没有改动 Original DRTP sampler、网络、环境、reward、actor information boundary 或 PPO loss；主线 A 的论文、正式结果和证据目录均未修改。

## 面向主线 B 目标的设计

主线 B 的目标不是单纯压低方差，而是同时满足：

1. 保留 Original DRTP 的平均收益与高收益 seed；
2. 抬升最差 seed，减少 catastrophic downside；
3. 降低跨 seed 离散度；
4. 不用 collision、timeout 或 constraint violation 的恶化换取分数；
5. 不影响主线 A 的投稿节奏和既有结论。

DRTP-KLR 保留 Original DRTP 的正常更新路径，仅在一次 actor Adam step 后、使用当前 rollout 的 full-batch states/actions/old log-probabilities 计算 empirical approximate KL。若 `KL > 0.02`，精确恢复该 epoch 前的 actor 参数及 actor Adam state，保留参数独立的 critic step，并终止当前 rollout 的剩余 PPO epoch。有限且不过界的更新与 Original DRTP 完全一致。

## 已实现内容

- 新增 `policy_update_guard_mode`，默认值为 `none`；
- 只允许 standard non-SAM PPO、有限正 `target_kl`、每 epoch 单个完整 rollout minibatch；
- actor 参数和 parameter-local Adam state 事务；
- post-step full-batch empirical KL；
- 越界 actor 精确 rollback，critic step 保留；
- model/optimizer/KL 非有限时整事务恢复并 fail-fast；
- 逐 update 与可续跑重建的累计 intervention telemetry；
- deterministic replay 与 checkpoint save/resume 合成验收。

## 技术验收结果

使用配置的 `cac` Python，仅执行 synthetic tensor tests 和静态审计，没有环境 rollout、训练或 checkpoint 评价：

- Stable-v2 guard tests：5 项；
- TC-SAM/optimizer 回归 tests：5 项；
- frozen DRTP/UTR formal-path tests：3 项；
- 合计：`13 passed`。

关键证明包括：

- 4 个不过界 PPO epoch 的最终 model 与 optimizer state 与未启用 guard 的原始路径逐 tensor 完全相等；
- actor Adam 已含非零 step/momentum 后，越界 rollback 仍逐 tensor 精确恢复；
- 同一越界事务中 critic optimizer step 从 1 增至 2，证明 critic 更新保留；
- 人工注入 NaN 后 model 与整个 optimizer transaction 恢复到 step 前状态并抛出技术错误；
- 相同输入、RNG 与 save/resume 路径产生完全一致的内部状态和 telemetry。

机器可复核记录见 `STABLE_V2_D1_TECHNICAL_AUDIT.json`。

## 仍未证明的内容

D1 只证明实现符合冻结语义，不证明 DRTP-KLR 能提高 return 或 seed reliability，也不证明大 KL update 是 DRTP 不稳定的科学根因。只有独立的三 seed paired pilot 能回答候选是否值得继续。

## 授权边界

下一步只允许 D2 零训练准备：clean seed provenance、development-only tape、evaluation noise margin、pilot launcher/aggregator 与 gate freeze。完成 D2 后仍须人工授权，才能在云端启动 0.5M pilot。
