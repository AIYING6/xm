# Stable-v2 三种子 pilot 合同草案

## 状态

`DRAFT_ONLY — NOT AUTHORIZED`。

在独立实现审计 PASS、三个 clean seeds 的 provenance 审计完成、新 development tape 冻结并经人工再次授权前，不得启动训练。

## 科学问题

在不修改 DRTP sampler、网络、PPO objective、reward 和环境的条件下，DRTP-KLR 是否能减少 catastrophic downside，同时保留 Original DRTP 的平均收益和高收益上尾？

## 设计

- arms：`UTR / Original DRTP / DRTP-KLR`；
- independent unit：training seed；
- seeds：3 个全新 paired clean seeds，编号在 provenance audit 后冻结；
- budget：每条严格 `1,953 update = 499,968 env steps`；
- total：9 条 trajectory；
- tape：新的 development-only tape，训练前冻结 episode IDs、conditions、manifest 与 hash；
- checkpoint：统一 0.5M final；milestone 仅诊断，不 promotion；
- 禁止 early stop、seed replacement、performance rerun、threshold change 或自动续到 1M。

## 冻结比较

主要比较 `DRTP-KLR - Original DRTP`；`UTR` 只提供 paired reference 和 catastrophic 判定基准。评价至少包含 `J_nominal`、`J_F0`、`J_pert_mean`、`J_pert_worst`、collision、timeout、constraint violation，以及 intervention telemetry。

## Pilot gate 草案

全部条件同时满足才可形成后续授权建议：

1. **High return / advantage retention**：DRTP-KLR 的三种子平均 `J_pert_mean` 不低于 Original DRTP 超过已冻结 evaluation noise margin；
2. **Downside protection**：不得新增 catastrophic seed，且 worst paired gain 不低于 Original；
3. **Direction**：至少 2/3 seeds 的 `DRTP-KLR - Original DRTP >= -epsilon_J`；
4. **Upper tail**：凡 Original DRTP 相对 UTR 超过 `epsilon_J` 的 seed，DRTP-KLR 不得相对 Original 下降超过 `epsilon_J`；
5. **Safety**：pooled collision/timeout 劣化均不超过 0.05；每个 seed-condition 劣化不超过 0.10；constraint violation 不增加；
6. **Mechanism activity**：至少发生一次正常 KL intervention；pooled intervention rate 不得超过 10%。0 次表示机制未被实际测试，超过 10% 表示设计不是稀有保护；两者均不得通过改阈值补救；
7. **Integrity**：全部 9 条轨迹、统一 final checkpoint、raw records、telemetry、manifest 和 hash 完整，无 seed 删除或重跑。

`epsilon_J` 必须在新 tape 和 seed 结果产生前，使用同一 checkpoint 的重复/paired evaluation noise 冻结；不得沿用与新 tape 不同语义的数值而不审计。

## 裁决

- `PILOT_GO_SIGNAL`：全部 gate PASS；只允许提交是否续到更高 development budget 的人工审查，不自动续训；
- `PILOT_NO_GO`：任一科学、安全、上尾或完整性 gate FAIL；候选关闭，不改 0.02；
- `PILOT_TECHNICAL_INVALID`：实现/数据完整性失败；只允许修复同一冻结语义后重新技术验收，不允许看性能后改算法。

本草案不授权 Stable-v2a/v2b、第二阈值、EMA、sampler anchor、learning-rate 修改或第三候选。
