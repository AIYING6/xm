# EGTR-DRTP P3 Development 合同

**状态：** `P3 1M EVALUATED — TECHNICAL/MECHANISM PASS — SAFETY REVIEW REQUIRED — 3M NOT AUTHORIZED`  
**日期：** 2026-08-26  
**绑定方法：** `docs/EGTR_DRTP_METHOD_CONTRACT.md`  
**绑定审计：** `docs/EGTR_DRTP_P2_TECHNICAL_AUDIT_REPORT.md`

## 1. 方法与独立单位

同时运行：

- UTR-SG-MAPPO；
- DRTP-SG-MAPPO；
- EGTR-DRTP-SG-MAPPO。

独立统计单位为 training seed。三种方法必须使用相同 backbone、PPO、环境、reward、failure semantics、actor information boundary、7 个 topology groups、50% nominal anchor、rollout 合同和评估协议。

唯一方法差异为：uniform sampler、原 DRTP sampler、冻结 EGTR sampler。

## 2. Development seeds

冻结三个此前未发现参与训练、调参或决策的 paired seeds：

`2501, 2502, 2503`

不得替换、删除或排除任何 seed。canonical seeds、历史 seed、held-out seeds 和此前 cohort 不得使用。

## 3. 预算与连续性

第一阶段每个 method×seed：

- from scratch；
- strict continuous；
- `1,000,192 env steps`；
- runtime persistence from step 0；
- final checkpoint 与固定 milestone 均保留；
- 禁止 early stopping、best-checkpoint promotion 和结果驱动调参。

若 1M technical/learnability gate PASS，三个方法和三个 seeds 必须共同从 1M 严格连续到 3M；不得只延长 EGTR 或更换预算。

## 4. Frozen EGTR settings

以下全部冻结，不得根据 1M/3M 结果修改：

- nominal-relative robust gap；
- MAD standard-error scaling `1.4826`；
- required sample count `8`；
- confidence EMA `kappa=0.20`；
- original DRTP EMA/difficulty/temperature/smoothing；
- bounded-simplex `[0.05,0.35]`；
- final sampler L1 trust region `delta_q=0.10`；
- update order与checkpoint state schema。

## 5. Evaluation tape

P3 使用独立 development-only tape：

`520000–520099`

已生成 manifest：`results/development/egtr_p3/tape/tape_manifest.json`。冻结 tape hash：
`4e4ebe743aa4b38c18374ba43eb0cb4faaa7e078b49adfec7c9d408c4f0cbb20`。

该 tape 只能用于 P3 development evidence，不得升级为 held-out 或 final confirmatory tape。未来 confirmatory 阶段必须重新创建独立 tape。

## 6. 1M screening purpose

1M 只用于 learnability/mechanism sanity screening，不作论文 superiority claim。必须报告：

- q trajectory；
- confidence EMA、rho、stale duration；
- `|q-uniform|_1`；
- final q step L1 与 trust-region active fraction；
- 实际 group exposure；
- return/PPO KL/clip/value diagnostics；
- collision、timeout、constraint；
- checkpoint/persistence 完整性。

1M 不能因为性能暂时不高而改 EGTR 参数。

## 7. 1M stop rules

以下任一项触发即停止，不续到 3M：

- technical invalid、continuation mismatch 或 telemetry 缺失；
- 最终 q 违反 simplex/bounds/L1 hard bound；
- 明显 catastrophic pattern 或 safety warning；
- EGTR 长时间完全等价于 uniform 且没有 adaptive signal；
- 需要修改冻结公式、阈值、window、EMA 或增加新机制。

单纯 1M return 暂时不高但训练健康，不自动判死。

## 8. 3M decision rules

3M 才进行稳定化 development 判定。若 EGTR 任一 seed 满足既有 catastrophic definition，立即：

`EGTR BRANCH = PERMANENT NO-GO`

不开发 EGTR-v2。以下任一情形也永久关闭 EGTR 稳定化路线：

- q 更平滑但 worst-seed/safety 没有改善；
- EGTR 长期退化为 UTR 且无额外扰动收益；
- 仍出现 DRTP 式严重 seed reversal；
- 必须增加第二套 gate、hysteresis、网络、loss 或调参搜索才能继续。

若 3M 通过，只能给出“eligible for separately authorized confirmatory study”，不得自动启动 5×10M。
