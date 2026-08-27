# 22 投稿主线证据层级冻结审计

**状态：** `PASS — FORMAL_COHORT_PLUS_TRANSPARENT_INDEPENDENT_REPLICATION`

**当前投稿目标（2026-08-27）：** 后续完成的 SNR 三方法 cohort 不再作为内部路线选择材料隐藏。它以“独立三方法重复 / 跨 cohort 可靠性”层完整进入正文第6.9节和补充材料S4：UTR、固定非均匀 SNR 与 DRTP 的全部五个训练种子、共同 10M 终点、全部端点、完整安全结果、原始记录、archive SHA256 与共同评价 tape 均一起披露。该 cohort 不与正式主 cohort 合并，也不得选择性引用单个有利或不利种子。

**目的：** 防止旧 9 页草稿、内部路线筛选材料或机器归档字段重新混入中文投稿主稿，造成主实验、指标和方法层级相互矛盾。

## 1. 唯一主实验

投稿主证据唯一指向 `DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1`：

- 方法：UTR-SG-MAPPO 与 DRTP-SG-MAPPO；
- 种子：2301--2305，五个从零开始的配对训练种子；
- 预算：每条轨迹 10,000,128 environment steps；
- 检查点：共同 10M final checkpoint，禁止 promotion；
- 评价：共同 episode ID 490000--490099 样本带，12 个条件、12,000 条原始记录；
- 因果解释：仅限“有界自适应故障组加权”相对于“均匀故障组加权”。

主文的可靠性部分保留完整的历史 strata：开发 3M 的 seed1902 方向不利，以及 held-out 10M 的 seed2001/2003 获益与 seed2002 严重反转。独立三方法 cohort（2401--2405）则作为另一个完整 strata 披露。它们均不与正式五种子合并为同质统计样本，也不用于回写正式主 cohort 的合同内事实。

## 2. 明确排除的内部材料

| 材料 | 当前定位 | 不得进入主文的原因 |
|---|---|---|
| SNR-SG-MAPPO 固定非均匀对照与同 cohort UTR/DRTP | 独立三方法重复与可靠性证据 | 必须整套披露而非只摘局部结果；它的方向反转限制跨 cohort 主张，但不替代正式主 cohort 的参数匹配主消融。 |
| scalar-min R-DRTP | 已归档候选 | 不再是当前研究方法，且无投稿级完整验证。 |
| EGTR-DRTP | 后续稳定化研究候选 | P3 仅完成 1M 技术/机制筛查，存在未量化的 collision--timeout 权衡，未获得 3M 或正式确认授权。 |

因此，主稿不展示 R-DRTP 或 EGTR 的方法公式、训练曲线或局部 seed；它们不是本研究的投稿方法。SNR 三方法 cohort 已按上述完整性规则披露：不得只摘取对任一方法有利或不利的单个种子。

## 3. 指标冻结

论文正文只使用：

- `J_nominal`；
- `J_F0`；
- `J_pert,mean`；
- `J_pert,worst`。

十个时机、持续时间和复合条件的具体成员属于训练扰动支持集。因此 `J_pert,mean` 与 `J_pert,worst` 是冻结条件集合内的跨扰动汇总指标，不是严格未见 OOD 指标。`J_OOD_mean` 和 `J_OOD_worst` 仅是两处归档映射说明中的机器字段名，不改变数值或扩大主张。

## 4. 自动防回退检查

`scripts/check_q2_final_zh_manuscript.py` 对投稿主稿执行 fail-closed 检查：

1. 要求独立 SNR 三方法 cohort 在主稿第6.9节和补充材料S4完整出现，同时禁止 R-DRTP、EGTR 和 Reliability-Gated 等未完成稳定化路线术语进入主稿；
2. 要求 `J_pert,mean` 与 `J_pert,worst` 为正文指标；
3. 限制机器字段 `J_OOD_*` 只出现于两处归档映射；
4. 要求明确声明跨扰动条件不是严格 OOD；
5. 要求历史可靠性 strata、独立重复 cohort 与正式五种子证据分层呈现，且明确禁止跨 cohort 拼接为 `(n=10)`。

该审计不授权新训练，也不重新解释任何历史实验。
