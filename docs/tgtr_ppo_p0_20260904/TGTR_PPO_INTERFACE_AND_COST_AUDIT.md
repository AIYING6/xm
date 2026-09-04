# TGTR-PPO 接口与成本审计

**Verdict:** `TGTR_P0_FEASIBLE_FOR_C1`

## 接口门

| 门 | 结果 | 证据 |
| --- | --- | --- |
| training-only group identity | PASS | rollout batch 已包含独立的 `condition_group`；它不属于 obs/graph 输入 |
| per-group actor quantities | PASS | `group_credit_telemetry.py` 已按组构造 clipped surrogate、advantage 与 actor gradients |
| old/new full policy probabilities | PASS WITH SMALL IMPLEMENTATION | actor forward 返回完整 logits；候选事务前后可直接计算 categorical KL |
| exact actor/Adam transaction | PASS | 现有 KLR/KLB 路径已实现 actor 参数和 optimizer slot 的复制、恢复与参数插值 |
| evaluation isolation | PASS | 训练配置不接收 formal evaluation tape；新机制只读当前 rollout |
| all groups in one current update | FAIL IN LEGACY 4-STREAM, SOLVABLE | 当前 sampler 每 update 至多两个 failure group；需 default-off 24-stream synchronized fixed sampler |
| matched comparator | PASS | Sync-UTR 使用同一 24-stream batch 与 ordinary PPO；只切换 actor update rule |

## 同步固定分层批次

| quantity | legacy UTR/TCR | proposed Sync-UTR/TGTR |
| --- | ---: | ---: |
| env streams | 4 | 24 |
| rollout steps | 64 | 64 |
| graphs/update | 256 | 1536 |
| nominal graphs/update | 128 | 768 |
| failure groups present/update | at most 2 | exactly 6 |
| graphs/failure group/update | 0 or about 64 | exactly 128 |
| design/certificate streams per failure group | unavailable | 1 + 1 |
| adaptive return feedback | no | no |

总 env-step budget不变时，update 数约降为原来的 1/6。每个样本的 ordinary PPO forward/backward 总量保持同阶；额外成本来自 active group gradients、QP 和 certificate forward。

## 成本上界与否决线

P0 不宣称实际云端倍率。C1 必须测量：

- rollout wall time；
- ordinary Sync-UTR update wall time；
- TGTR update wall time；
- peak GPU memory；
- active-set size；
- accepted alpha 与 zero-step rate。

进入 fresh-seed development 的成本硬边界：

- peak GPU memory 必须适配现有 10/12 GB GPU；
- TGTR 单 update wall time不得超过 matched Sync-UTR 的 4 倍；
- zero actor-step rate不得超过 25%；
- certificate 不能因缺组而降级为 pooled-only；
- 不允许用放宽 certificate、删除失败组或缩小 batch 来“修复”成本/通过率。

超过任一边界，返回 `TGTR_C1_NO_GO`，不训练 3-seed pilot。

## 主要工程风险

1. 24 个环境在单进程中可能使 CPU simulation 成为瓶颈。
2. actor gradients 的多次 autograd 可能使 optimizer-side cost 达到 2--4 倍。
3. certificate streams 仍来自同一训练 seed，不能提供 cross-seed 保证。
4. 频繁 zero step 会重现“过度保护导致学不动”的问题。
5. 大 batch 本身可能改变稳定性，因此所有性能结论必须以 Sync-UTR 为 primary comparator；legacy UTR 只能描述性报告。
