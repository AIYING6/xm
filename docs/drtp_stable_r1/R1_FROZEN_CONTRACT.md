# Stable-DRTP R1 独立可靠性验证：冻结合同

## 范围和边界

本合同仅为独立 development 研究准备 R1；它不改写任何历史结论：S1 的 `DRTP-TR` 为 `NO-GO`，S2 的 Conservative-DRTP 在原 S2 合同下为 `S2_NO_GO / STABILIZATION_LINE_CLOSED`。R1 不重跑、不替换、也不合并 S1/S2 结果。

R1 的可证伪问题是：在完全新训练 seed 上，已冻结的 Conservative-DRTP 能否保留原始 DRTP 的鲁棒收益，同时改善下尾风险与跨 seed 离散度。

## 冻结方法与训练单位

| Arm | sampler mode | 可变部分 |
|---|---|---|
| `utr_sg` | `utr` | uniform topology randomization |
| `drtp_sg` | `drtp` | 原始 DRTP |
| `conservative_drtp_sg` | `conservative_drtp` | 仅使用已冻结的保守采样器 |

Conservative-DRTP 的唯一语义为：`adaptive target → bounded-simplex projection → 0.80 adaptive + 0.20 uniform → final L1 trust region`。其 `delta_q_l1=0.02513300038143937`，uniform anchor 为 `0.20`。actor/critic、116,728 参数、PPO、reward、environment、observation、failure semantics、nominal 50% exposure 及训练预算均不改变。

R1 若获独立人工授权，将只运行 `3001–3005` 这五个干净 paired training seed；每个 arm/seed 从零开始到 `3,907` updates，即 `1,000,192` environment steps。固定 milestone：976/1953/2930/3907 updates（0.25/0.5/0.75/1M）。禁止 early stopping、checkpoint promotion、seed replacement、结果驱动 rerun、参数调整、delta/anchor sweep 和任何第四候选。

## 冻结评价

development-only tape：`configs/drtp_stable_r1_development_tape.json`，hash `74a760fe008e328745a4401f597c0f0b84195080491eafdcf484dcdbdf9eb8da`。五个条件为 Nominal、F0(44,80)、T28(28,80)、D120(44,120)、C28(28,120)，每个条件 100 个共享 episode IDs `540000–540099`。它不是 canonical、confirmatory 或 strict unseen tape。

主端点为 `J_pert_mean = mean(F0, T28, D120, C28-120)`；每个 seed 的 paired gain 为 `G = J_pert_mean(method) - J_pert_mean(UTR)`。

## 预冻结 1M Gate

`epsilon_J = 7.874919837916801` 是 S0 所得的同 checkpoint 跨 tape 波动 P90；practical downside improvement margin 取同值，且必须严格超过。

`R1_STABLE_SIGNAL_GO` 必须同时满足：

1. Advantage retention：Conservative-DRTP 的五 seed 平均 `J_pert_mean >= Original DRTP mean - epsilon_J`；
2. Downside protection：`min(G_conservative)-min(G_original) > epsilon_J`，且 Conservative catastrophic seed count 严格少于 Original；
3. Seed reliability：Conservative 的 `range(G)` 与 sample SD 都严格小于 Original；IQR/MAD 仅描述性报告；
4. Upper-tail retention：所有 `G_original > epsilon_J` 的 seed 都有 `J_pert_mean(conservative)-J_pert_mean(original) >= -epsilon_J`；
5. Direction consistency：至少 4/5 个 seed 有 `G_conservative >= 0`；
6. Safety：沿用 S1/S2 的 collision、timeout、constraint-violation 门槛。

任何上述核心条件失败即为 `R1_NO_GO`。`R1_INCONCLUSIVE` 仅可用于训练/评价完整且预先记录的时间尺度审计显示 1M 无法证伪时；本合同不授权自动续训或启动确认性 10M。R1 的最终决定仍须人工审查。

## S2 provenance 复核

S2 的训练执行源为 commit `5d1e3a3c`；`bd836ed2` 是其祖先，曾被旧运行 manifest 误作 source fallback 标签。该标签缺陷不改写历史 artifact，R1 仅在本合同中更正 provenance 解释。执行源关键文件 SHA256：

| file at `5d1e3a3c` | SHA256 |
|---|---|
| `algorithms/ri_gmappo/drtp_topology_sampler.py` | `469ef2ac5fc516a079b9f5fb182092db0d37bab02cf06534a8ed23eed218d2b5` |
| `scripts/run_drtp_stabilization_s2_single.py` | `496a36c661de4be956a7ffdff27330abd1af198447c3fffeb3183a4d44caa57e` |
| `configs/drtp_stabilization_s0_freeze.json` | `2e6c598d53106b396f6c498c4812530e2250e77aed47b29f09c2ae4b14d9db12` |
| `configs/drtp_stabilization_s1_development_tape.json` | `020bab81c22c32104a54526806c81ba37f5a78d57a89b6ab4554fa76f26e2c35` |

已核验的 S2 archive SHA256 为 `1c91360e5ac7e37876487442dce39fc9246a90717f9e2e0ad35808ebeee8e1f3`。S2 技术审计 PASS；其旧 `NO-GO` 仅因旧合同把 MAD 也作为 reliability veto，而新的 R1 在看新数据之前已明确只用 range 与 sample SD 作为主 reliability 判据。

## 资源与启动边界

R1 规模为 15 条 × 1,000,192 = 15,002,880 environment steps；最终评价为 15 arms/seeds × 5 conditions × 100 episodes = 7,500 raw episode records。基于 S1 已成功使用九路并行的实测经验，12 GB 3080 Ti 的推荐最大安全训练并发冻结为 9；评价 worker 建议 8。云端要求至少 25 GiB 可用磁盘，且只允许使用由后续授权生成的结果目录。

本文件完成即停止；不代表 R1 训练授权。
