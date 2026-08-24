# DRTP/SNR Q2 机制对照执行合同

**协议：** `DRTP-SNR-Q2-MECHANISM-COMPARATOR-EXECUTION-V1`  
**状态：** `FROZEN — AUTHORIZED FOR PROSPECTIVE CLOUD EXECUTION`

本合同执行并补充既有 [SNR 训练前合同](DRTP_STATIC_NONUNIFORM_COMPARATOR_PRETRAINING_CONTRACT.md)，但不改变其中的 SNR 权重、环境、策略信息边界或历史结论。

## 1. 唯一授权的运行

三个方法均严格从零开始，连续运行至 `39,063` updates（`10,000,128` environment steps）：

| arm | sampler | training seeds |
|---|---|---|
| UTR-SG-MAPPO | conditional-uniform | 2401–2405 |
| SNR-SG-MAPPO | frozen static nonuniform | 2401–2405 |
| DRTP-SG-MAPPO | bounded adaptive reweighting | 2401–2405 |

共 `15` 条轨迹、`150,001,920` environment steps。每条均使用 4 env × 64 rollout、相同的 20 个保存里程碑、完整 runtime-state persistence，且只以共同的 10M 最终 checkpoint 作正式比较。

禁止：warm restart、历史 checkpoint 初始化、提前停止、best-checkpoint promotion、seed exclusion、canonical seeds 0–4、历史正式 seeds 2301–2305、SNR 权重再搜索，以及任何环境、reward、PPO、网络、failure semantics 或 actor information boundary 修改。

## 2. 三臂公平性与 SNR 隔离

三臂均固定为 116,728 参数 Single-Graph MAPPO，使用相同 PPO、critic、7 个 topology groups 与 50% nominal anchor。唯一差异为训练 reset 时的 conditional failure-group distribution：UTR 为均匀，SNR 为固定 `(0.15,0.20,0.10,0.10,0.20,0.25)`，DRTP 为冻结的动态 `q_u`。

SNR 不得接收 completed return，不得保存或更新 EMA/difficulty/adaptation window，也不得改变固定权重。其 runtime state 仅用于绑定 seed、预算及固定权重的严格续训校验。

## 3. 新评价带与技术有效性

训练完成后生成并冻结 `500000–500099` 的新配对评价带，12 个条件 × 100 episodes。三臂、五个 training seed 共评估 18,000 原始 episode records。所有 scheduled episode 计入总体 return 与 safety；failure-trigger 技术有效性只在 onset 前存活的 risk set 内判定。

技术有效性要求：所有 15 条 run 完整、18,000 raw records 完整、每个非 nominal method×seed×condition risk-set 中的 scheduled failure 均被正确触发。任一失败只可标为 `TECHNICAL_INVALID`，不得删除 episode 或换 seed。

## 4. 预注册判读规则

训练 seed 是唯一独立单位。对每个配对比较均完整报告五个 paired differences、mean、median、IQR/MAD、wins、worst reversal 与 safety。

主要鲁棒端点为 `J_F0`、`J_pert_mean` 与 `J_pert_worst`。一个方向性经验支持需在三个端点上同时满足：paired mean > 0、paired median > 0、至少 3/5 training seeds > 0；且比较方法没有超过一个冻结 catastrophic seed、collision/timeout 没有系统性恶化、constraint violation 保持为零。catastrophic 定义沿用正式五种子合同的 F0/OOD-worst/safety-associated collapse 规则。

- 若 SNR 对 UTR 的方向性支持成立，记为**静态非均匀分配支持**；
- 若 DRTP 对 SNR 的方向性支持成立，记为**动态反馈附加价值支持**；
- 两者均成立，结论为 `DYNAMIC_ADDITIONAL_VALUE_SUPPORTED`；
- 前者成立、后者不成立，结论为 `STATIC_NONUNIFORM_SUFFICIENT_FOR_OBSERVED_GAIN`；
- SNR 对 DRTP 的反向方向性支持成立，结论为 `DYNAMIC_MECHANISM_NOT_SUPPORTED`；
- 其余完整有效情形为 `NO_CLEAR_MECHANISM_SEPARATION`。

这些结论只限定在冻结的 UAV relay-failure task；不改写历史 DRTP held-out failure、seed2002 catastrophic reversal 或既有正式五种子结果。
