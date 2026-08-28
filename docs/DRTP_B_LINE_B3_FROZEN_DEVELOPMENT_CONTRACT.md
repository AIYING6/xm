# DRTP B线 B3：冻结的机制探索 Development 合同

状态：`B3_PREPARATION_COMPLETE — TRAINING_NOT_AUTHORIZED`

## 1. 科学问题

本阶段唯一问题是：原始 DRTP 是否存在可跨 development seed 重复观察、且早于后续结果退化的训练分叉链：

`adaptive sampler state → actual exposure → coordination behavior/task support degradation → poor outcome`。

B3 **不**回答“DRTP 是否比 UTR 分数高”，也不生成投稿主结论。

## 2. 冻结对象与禁止项

| 项目 | 冻结值 |
|---|---|
| 方法 | `utr_sg`、原始 `drtp_sg` |
| 新 paired seeds | `2701, 2702, 2703` |
| 训练预算 | 每条 `3,907 × 4 × 64 = 1,000,192` environment steps |
| milestone | update `976/1953/2930/3907`（约 `0.25/0.50/0.75/1.00M`） |
| 初始代码基线 | `69117b628fe85026e0638abb73dcfbfb04e4a64c`（作者授权的冻结提交） |
| development tape | `configs/drtp_b3_development_tape.json`，SHA256 `e01c905b04257fd6b373dbbe3ca25cf5f0dece0864e89b6713bd7647107ce9ed` |

算法、PPO、reward、环境、故障语义、观测、actor/critic、DRTP 参数与训练支持集均冻结。禁止 EGTR、R-DRTP、trust region、confidence gate、warm-up、新网络、辅助 loss、checkpoint promotion、early stop、换 seed、删差 seed 和 10M 训练。

## 3. 遥测与评价

每条训练必须启用 B2 通过的 read-only telemetry，包含 sampler 状态与实际 exposure、现有 PPO CSV 指标、failure-relative behavior、信息路径、path-switch、pairwise geometry、task support、终止和环境真实 reward components。训练期日志按 0.25M block 汇总；每个 milestone 都使用冻结 development-only tape 进行同一批诊断评价。

tape 有 5 个条件（Nominal / F0 / T28 / D120 / C28-120）、每条件 100 个相同 base episode IDs；共 `2 methods × 3 seeds × 5 conditions × 100 = 3,000` episodes。它是机制诊断资产，不是 held-out 或 confirmatory OOD。

## 4. 历史时间尺度与 1M 裁决

历史 timing audit 以固定的 500-update paired train-reward proxy 规则发现首个持续 cohort 方向分离在约 `0.384M` steps 结束处。该代理不等同最终评价性能，也不是机制证据；它只说明 1M 时间窗足以观察历史训练状态的持续分离。因此：

- `MECHANISM_CANDIDATE`：在 1M 内出现预定义链的候选证据，可严格续至 3M；
- `MECHANISM_NO_GO`：六条轨迹正常完成、遥测完整，但在 1M 内无至少 2/3 DRTP seed 可重复的时间领先候选链，或关键链层无法建立；停止；
- `INCONCLUSIVE_TIME_HORIZON`：只允许在确有预先记录的观测障碍、而非“结果不够好”时使用；否则不得把 1M 无信号升级为自动续训。

## 5. 候选与最终机制门

候选只能来自预定义指标族：

1. sampler/exposure：q 距均匀分布、group weights、selected group/member、实际 group exposure；
2. behavior/support：direct/relay/no-path、valid target information、cache age/source、chain support、attack window、pairwise geometry、action/entropy；
3. outcome：mission score、completion、timeout、collision、constraint violation。

`MECHANISM_CANDIDATE` 至少要求：同一方向的 DRTP 特异候选在 2/3 seeds 出现，且在一个 outcome 变化之前出现；中间层必须由至少两个同构的 behavior/support 指标支持，不能由单一 proxy 或任意阈值触发。

若续至 3M，`MECHANISM_GO` 必须同时满足：

1. **Temporal precedence**：异常在对应 outcome 退化前出现；
2. **Replication**：至少 2/3 DRTP seeds 有同方向、相似结构；
3. **Specificity**：paired UTR 没有同强度、同时间结构；
4. **Chain completeness**：至少连接 `sampler/exposure → behavior/support → outcome` 三层；
5. **Robustness to metric choice**：中间层由至少两个相关指标共同支持，不依赖单一人为阈值或 proxy。

任何一项失败即 `MECHANISM_NO_GO`，该机制链永久关闭；不得据此开发 Stable-DRTP。

## 6. 运行纪律与边界

若之后获授权，B3 的大规模训练和统一评估仅能在云端按硬件允许的最大安全并发运行。每一 run 启动前必须断言：请求 seed、`cfg.seed`、sampler seed、runtime RNG seed 与 telemetry seed 一致；该断言是此前 2601--2603 `TECHNICAL_INVALID` 事故的不可绕过修复。

本合同本身不构成训练授权。B3 完成后只有 `MECHANISM_GO` 才允许撰写一个最小干预建议；仍不自动授权该干预的实现或 10M 验证。
