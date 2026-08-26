# EGTR-DRTP P2 技术审计计划

**状态：** `P2 PASS — NO TRAINING AUTHORIZED`  
**绑定合同：** `docs/EGTR_DRTP_METHOD_CONTRACT.md`

## 1. 必须通过的硬门

### 合同与公平性

- UTR/DRTP/EGTR 的 SG backbone、参数量和 actor information boundary 完全一致；
- EGTR 只改变 sampler，不新增 policy/critic 参数；
- 七组 topology exposure、50% nominal anchor、failure semantics 一致；
- SNR、历史 DRTP checkpoints、held-out 和 canonical seeds 不参与选择。

### 数学与边界

- median/MAD/robust gap 在空组、单样本、median 近 0、跨正负回报时有限；
- `r_k`、confidence EMA 和 `rho` 均在 `[0,1]`；
- 单组缺样本不会触发 global uniform reset；
- stale duration 只作 telemetry，不引入额外 stale hyperparameter；
- q 始终满足 `[0.05,0.35]` 与总质量 1；
- 最终 q 严格满足 `L1(q_new-q_old) <= 0.10`；
- trust region 后不得再次投影。

### 恒等性与不变性

- 全部 confidence=1 且 trust-region 未触发时，EGTR 必须等于原 DRTP；
- 全部 confidence=0 时，EGTR 必须按合同退回 uniform target；
- positive return translation 不改变 gap-based evidence；
- positive return scaling 不改变 normalized evidence 方向；
- 相同 return stream、seed 和 boundary 顺序产生完全相同 q；
- logging on/off 不改变训练路径。

### 持久化与 smoke

- mid-window raw return buffer save/reload 后 next boundary bitwise/deterministic 一致；
- confidence EMA、stale duration、q、difficulty 和 RNG 完整恢复；
- one-update finite-value smoke；
- graph-legality、information-boundary 和 parameter-count regression。

## 2. 审计输出

P2 必须生成：

- machine-readable audit JSON；
- `docs/EGTR_DRTP_P2_TECHNICAL_AUDIT_REPORT.md`；
- 不生成 evaluation tape；
- 不生成 development performance result；
- 不启动长训练。

## 3. P2 结果解释

- `PASS`：仅表示实现和合同可执行，不表示 EGTR 性能有效；
- `REVISE`：只允许修复合同/实现一致性，不允许看性能调参；
- `FAIL`：关闭 EGTR 稳定化路线，保留原 DRTP 的高平均收益与 seed sensitivity 结论。

## 4. P2 之后的预注册 development 方向

只有 P2 PASS 并获得单独授权，才可冻结 UTR/DRTP/EGTR 三臂 paired development。默认先使用 3 个全新 development seeds、1M 初筛，再按预冻结规则决定是否严格续到 3M；不自动进入 5M/10M。
