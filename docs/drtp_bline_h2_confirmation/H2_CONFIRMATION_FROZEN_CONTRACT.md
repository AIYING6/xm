# H2 独立新 seed 最小证伪合同

状态：`STAGE-1 AUTHORIZED`。本合同只检验 H2：早期策略/critic 脆弱性与原始
DRTP 自适应采样的相互作用，是否可在新 seed 上重复；不修改或稳定化 DRTP。

## 冻结对象

- 方法：UTR-SG-MAPPO 与 original DRTP-SG-MAPPO；
- 新 paired development seed：2801–2805；
- Stage-1：每条 1,953 updates × 4 env × 64 rollout = **499,968 env steps**；
- 里程碑：update 976（0.25M）和 1,953（0.50M）；
- 固定 development-only tape：`configs/drtp_h2_confirmation_development_tape.json`；
- 失败语义、环境、PPO、reward、网络、actor 信息边界、DRTP sampler 规则与
  failure-aware telemetry 均不得改变。

禁止 early stop、best checkpoint、seed replacement、性能驱动重跑、3M/10M、
Stable-DRTP、EGTR、R-DRTP、trust region、confidence gate、warmup 或任何 PPO/
reward/network 修改。所有十条轨迹必须保留。

## 资源调度修订 A（作者授权）

在任何可用训练结果出现前，作者于 2026-08-29 明确授权将云端 Stage-1 的并发数
由 6 调整为 **10**，使全部十条轨迹同时执行。该修订仅改变资源调度：seed、方法、
预算、里程碑、telemetry、tape、判据及停止规则均保持不变。此前刚启动但尚未产生
科学结果的 6 路批次必须停止；不得混合其不完整产物与修订后的 Stage-1 输出。

## 预注册 early signature

每个 DRTP seed 必须同时满足三层才计为 H2-positive：

1. **早期优化层**：0.25M `value_loss(DRTP)-value_loss(UTR) ≥ 0.10`，或
   0.50M `approx_KL(DRTP)/approx_KL(UTR) ≥ 3.0`；
2. **自适应层**：DRTP failure-group `q` 到均匀分布的 L1 距离在
   0–0.25M 至 0.25–0.50M 增加至少 0.20；
3. **行为/支持层**：0.25–0.50M 的 failure-relative `tau=60`，DRTP 相对
   paired UTR 的信息路径可用率差 `≤ -0.20` 且 task-support 差 `≤ -0.05`。

这里的 q 偏离不能单独构成 H2；第 3 层强制包含 paired UTR 对照。

## 0.5M gate

- `H2_EARLY_SIGNATURE_REPLICATED`：至少 2/5 DRTP seed 满足完整 signature；
- `H2_NO_GO`：不足 2/5。

launcher 在 0.5M gate 后无条件停止。即便结果为 replicated，也不自动运行 1M；
它仅使“全部原始十条 run 严格连续至 1M”的单独授权成为可能。
