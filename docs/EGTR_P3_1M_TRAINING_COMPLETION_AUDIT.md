# EGTR P3 1M 训练完成审计

## 1. 审计范围

本报告审计用户提供的 `egtr_p3_1m_results.tar.gz`，仅覆盖 P3 第一阶段的训练完整性与机制运行状态。未启动新训练，未运行 evaluator，未使用 held-out 或 canonical seeds。

归档 SHA256：

```text
6441a6e6330edd4ede189fef3c575d604925017acccf8a711e03f479913414c2
```

P3 固定 tape：`520000–520099`，SHA256：

```text
4e4ebe743aa4b38c18374ba43eb0cb4faaa7e078b49adfec7c9d408c4f0cbb20
```

归档中的运行来源为云端无 `.git` 打包环境，因此 run manifest 将 `source_commit` 记为 `package-provenance-only`；该包对应的源代码提交为 `288ede9`。

## 2. 训练完整性

| 方法 | seed2501 | seed2502 | seed2503 | 统一配置 |
|---|---:|---:|---:|---|
| UTR-SG | 完成 | 完成 | 完成 | 1,000,192 steps / 3,907 updates |
| DRTP-SG | 完成 | 完成 | 完成 | 1,000,192 steps / 3,907 updates |
| EGTR-SG | 完成 | 完成 | 完成 | 1,000,192 steps / 3,907 updates |

9/9 run 均满足：

- `status=completed`；
- `parameter_count=116,728`；
- from scratch，未 resume；
- runtime-state persistence 从 step 0 开启；
- 500k、750k、1M checkpoint 和 runtime-state 均存在；
- 训练日志为 3,907 个有效 update，无重复表头或非法 update 行；
- 使用同一 P3 tape hash；
- 未使用 canonical seeds 0–4；
- 未发生 checkpoint promotion、early stopping 或 seed exclusion。

## 3. 最终 checkpoint SHA256

| 方法 | seed2501 | seed2502 | seed2503 |
|---|---|---|---|
| UTR-SG | `2d781b29e3530c43cc0cd1019c460f18b39cde128fa65c1935bd033238c710d4` | `1c70e712ac18f4567f88e3db3e4e6803f7899e2a61e93592fbc859094711e2b1` | `58c2e70dcf5f40e877ede3a63fba99471f56f02d9c7d612eea76518575fe9683` |
| DRTP-SG | `5abda7bbda15998e40e7ae1a5ccace6ddaeaa1a9ebda9d5c53d98a98f9b04677` | `8297dc3ac1792af608bcff07832baa10d916d18ab71037b844192ba26f572c3b` | `a280f218beb77cbe79302420ce993abba34d7afdef4354a289badb07be0644ca` |
| EGTR-SG | `76e370d64fb11a38639f77177524f78500fc4938fec24cbd997e25d4b8576fb3` | `e420205b4709afb5bb352ff5f4efa91c450d2c4904db0eefc6116cad61cb96f2` | `e1290f456bd5b3a501c5e18a723ef0ad2494ba06c30e4084c6fad4d914729c76` |

## 4. EGTR 机制 sanity

每条 EGTR 轨迹产生 122 条 sampler boundary 记录，其中 118 条完成自适应更新，说明 EGTR 并未退化为始终不更新的 uniform sampler。

| seed | 最终 `rho` | `max ||q-q_uniform||_1` | `max step L1` | trust-region active |
|---:|---:|---:|---:|---:|
| 2501 | 0.127396 | 约 0.02215 | 约 0.00940 | 0 |
| 2502 | 0.144739 | 约 0.02215 | 约 0.00940 | 0 |
| 2503 | 0.093211 | 约 0.02215 | 约 0.00940 | 0 |

三条 EGTR 轨迹的 q 都只发生温和偏移，且最终仍接近 uniform；实际步长远低于冻结的 `L1 <= 0.10` trust-region 上限。trust region 未被激活不等于实现失败，当前数据表明候选更新本身没有接近该硬边界。

最终 confidence EMA 均已记录，三条轨迹的组间置信度存在差异，说明 per-group evidence/confidence 路径在工作。空窗口只影响对应 group 的 stale 状态，没有发现 global reset 证据。

## 5. PPO 与数值健康性

最终 update 的平均诊断如下：

| 方法 | 平均 reward | 平均 entropy | 平均 KL | 平均 clip fraction | 平均 grad norm | 平均 explained variance |
|---|---:|---:|---:|---:|---:|---:|
| UTR-SG | 0.1577 | 2.2535 | 0.00104 | 0.00586 | 2.8403 | 0.9215 |
| DRTP-SG | 0.1227 | 2.3049 | 0.00051 | 0.00130 | 2.0918 | 0.9565 |
| EGTR-SG | 0.1482 | 2.4615 | 0.00031 | 0 | 3.9858 | 0.8740 |

现有 PPO telemetry 未显示明显 KL 爆炸、clip 饱和或 NaN/Inf。EGTR 的 explained variance 低于 UTR/DRTP，属于需要在统一评估中继续观察的诊断信号，不能单凭它判定失败。

## 6. Runtime-state persistence

抽查 EGTR、DRTP、UTR 的最新 runtime-state，均包含：

- model 与 optimizer state；
- global update；
- Python、NumPy、PyTorch CPU/CUDA RNG；
- environment state 与每个环境 RNG；
- current observation、share observation、graph observation；
- episode counters；
- sampler state；
- DRTP/EGTR q、EMA、difficulty 或 confidence/stale state；
- adaptation-window returns/counts；
- normalization state 字段（当前为 `None`，与配置一致）。

因此，训练产物满足 P3 规定的 runtime-state 保存结构。

## 7. 尚未完成的部分

本归档不包含 P3 1M evaluation 的 raw episode records、统一指标或最终裁决文件。因而当前不能据此报告或判断：

- `J_nominal`、`J_F0`、`J_OOD_mean`、`J_OOD_worst`；
- collision、timeout、constraint；
- risk-set validity；
- catastrophic seed；
- 3M continuation eligibility。

这不是训练失败，而是当前归档只包含训练阶段。按照冻结合同，下一步应先对 9 个 1M final checkpoint 使用同一 development tape 做统一评估；评估结果出来前不得进入 3M。

## 8. 当前结论

```text
P3 1M TRAINING INTEGRITY: PASS
P3 MECHANISM SANITY: PROVISIONALLY PASS
P3 SCIENTIFIC 1M GATE: PENDING UNIFIED EVALUATION
3M CONTINUATION: NOT AUTHORIZED BY THIS AUDIT
```

当前最重要的事实是：9 条训练轨迹完整、EGTR 确实产生了受控的非均匀适应、runtime-state 结构完整；但尚无性能和安全评估证据，因此不能宣布 P3 GO，也不能自动启动 3M。
