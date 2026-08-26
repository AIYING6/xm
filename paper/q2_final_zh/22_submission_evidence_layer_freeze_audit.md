# 22 投稿主线证据层级冻结审计

**状态：** `PASS — DRTP_PRIMARY_LINE_ONLY`

**目的：** 防止旧 9 页草稿、内部路线筛选材料或机器归档字段重新混入中文投稿主稿，造成主实验、指标和方法层级相互矛盾。

## 1. 唯一主实验

投稿主证据唯一指向 `DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1`：

- 方法：UTR-SG-MAPPO 与 DRTP-SG-MAPPO；
- 种子：2301--2305，五个从零开始的配对训练种子；
- 预算：每条轨迹 10,000,128 environment steps；
- 检查点：共同 10M final checkpoint，禁止 promotion；
- 评价：共同 episode ID 490000--490099 样本带，12 个条件、12,000 条原始记录；
- 因果解释：仅限“有界自适应故障组加权”相对于“均匀故障组加权”。

主文的历史可靠性小节只保留完整的历史 strata：开发 3M 的 seed1902 方向不利，以及 held-out 10M 的 seed2001/2003 获益与 seed2002 严重反转。它们不与正式五种子合并为同质统计样本，也不用于改写正式裁决。

## 2. 明确排除的内部材料

| 材料 | 当前定位 | 不得进入主文的原因 |
|---|---|---|
| SNR-SG-MAPPO 静态非均匀对照 | 内部机制与可靠性路线选择证据 | 新 cohort 中 UTR 占优且 SNR/DRTP 均出现灾难性种子；不能摘取局部结果支持 DRTP 主结论，也不构成投稿主合同的一部分。 |
| scalar-min R-DRTP | 已归档候选 | 不再是当前研究方法，且无投稿级完整验证。 |
| EGTR-DRTP | 后续稳定化研究候选 | P3 仅完成 1M 技术/机制筛查，存在未量化的 collision--timeout 权衡，未获得 3M 或正式确认授权。 |

因此，主稿不展示这些方法公式、训练曲线或局部 adverse seed。若未来选择另行披露任何一个独立 cohort，必须同时给出该 cohort 的全部方法、全部种子、共同终点、完整安全指标和合同边界；不得只摘取对任一方法有利或不利的单个种子。

## 3. 指标冻结

论文正文只使用：

- `J_nominal`；
- `J_F0`；
- `J_pert,mean`；
- `J_pert,worst`。

十个时机、持续时间和复合条件的具体成员属于训练扰动支持集。因此 `J_pert,mean` 与 `J_pert,worst` 是冻结条件集合内的跨扰动汇总指标，不是严格未见 OOD 指标。`J_OOD_mean` 和 `J_OOD_worst` 仅是两处归档映射说明中的机器字段名，不改变数值或扩大主张。

## 4. 自动防回退检查

`scripts/check_q2_final_zh_manuscript.py` 对投稿主稿执行 fail-closed 检查：

1. 禁止 SNR、R-DRTP、EGTR 和 Reliability-Gated 等内部路线术语进入主稿；
2. 要求 `J_pert,mean` 与 `J_pert,worst` 为正文指标；
3. 限制机器字段 `J_OOD_*` 只出现于两处归档映射；
4. 要求明确声明跨扰动条件不是严格 OOD；
5. 要求历史可靠性 strata 与正式五种子证据分层呈现。

该审计不授权新训练，也不重新解释任何历史实验。
