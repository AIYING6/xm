# Q2 论文 Post-SNR 路线重构审计

**状态：** `PAPER_ROUTE_C — DRTP ALGORITHM WITH EXPLICIT SEED-SENSITIVITY LIMITATION`

**日期：** 2026-08-26
**训练授权：** 无。本次路线恢复和稳定化机制设计均为零训练工作。

## 1. 不可改写的历史事实

此前 DRTP 的 development、held-out 和可靠性审计结论保持原样；它们不能因后续结果而被回写为 PASS。尤其是历史 seed1902 与 seed2002 的反转必须继续保留。SNR 机制对照的前瞻性五种子结果也不能被选择性忽略：它是当前论文对训练分布加权能否泛化的最高等级证据。

本审计不以旧的高收益 cohort 与新 cohort 混合成单一 pooled result，也不把“不同 cohort 的差异”解释为某个算法获胜或失败的充分原因。

## 2. 最高等级的前瞻性证据

`DRTP-SNR-Q2-MECHANISM-COMPARATOR-V1` 对 UTR、SNR、DRTP 同时训练，使用新训练种子 2401–2405、每条轨迹 10,000,128 environment steps、同一 116,728-参数 Single-Graph MAPPO、同一 PPO/S2 环境/奖励/信息边界、固定 50% nominal exposure，以及同一非 canonical tape `500000–500099`。三种方法唯一差异是六个扰动组的条件权重：

- **UTR：** 条件均匀，`q_k=1/6`；
- **SNR：** 固定非均匀，`(F0,TE,TL,DS,DL,CP)=(0.15,0.20,0.10,0.10,0.20,0.25)`；
- **DRTP：** 由已完成 episode return 驱动的有界在线自适应权重。

预检通过、15/15 final checkpoint 完整、18,000/18,000 原始评估记录完整，risk-set failure-trigger validity 通过。因此下表是可用于主结论的前瞻性对比，而非技术无效或选择性样本。

| 方法 | `J_nominal` | `J_F0` | `J_OOD_mean` | `J_OOD_worst` | collision | timeout |
|---|---:|---:|---:|---:|---:|---:|
| UTR | 225.700 | 199.399 | 200.484 | 181.978 | 0.0093 | 0.6460 |
| SNR | 184.641 | 183.072 | 177.998 | 159.630 | 0.0138 | 0.6609 |
| DRTP | 187.352 | 166.131 | 166.413 | 149.613 | 0.0516 | 0.6778 |

对 UTR 的配对方向进一步表明：SNR 的 nominal 为 0/5 有利、F0 与 OOD mean 各为 1/5、OOD worst 为 2/5；DRTP 的 nominal 为 1/5、F0/OOD mean/OOD worst 均为 2/5。SNR 出现 1 个 catastrophic seed，DRTP 出现 1 个 catastrophic seed。故该 cohort 不支持固定非均匀权重或自适应权重优于均匀拓扑随机化的主张。

## 3. 重构后的中心论点

**一语论点：** 在冻结的中继故障拓扑重构任务中，前瞻性三方法、五训练种子和 12 个评估条件表明，固定均匀拓扑随机化在该新样本中优于固定非均匀和自适应扰动加权；因此，拓扑鲁棒 MARL 的结论必须同时报告路径重构、安全和训练种子可靠性，而不能由单一高收益 cohort 推出。

论文恢复 DRTP 算法主线，但采用受限表述：DRTP 是一个具有较高平均收益、同时存在明确训练种子敏感性的拓扑扰动训练策略。SNR 保留为内部机制审计材料，不作为论文主比较；其结果用于防止把 DRTP 的高收益过度解释为“自适应必然必要”。

## 4. 证据层级与写作使用规则

| 证据层 | 作用 | 可支持的结论 | 不可支持的结论 |
|---|---|---|---|
| S1/S2 环境与合法性审计 | 问题有效性 | 中继故障会改变合法通信—任务支持路径并影响协同 | 完全信息黑障、任意实飞结论 |
| UTR/DRTP formal paired comparison | 主性能与算法比较 | DRTP 在部分 formal/development cohort 上的平均扰动收益 | DRTP 对所有初始化稳定优越 |
| 历史 DRTP development/held-out/REL-A0 | 可靠性与反例 | 自适应权重曾产生高收益，也存在可重复的训练种子反转 | DRTP 稳定优越、旧均值可覆盖新 cohort |
| 轨迹/路径/安全遥测 | 机制边界 | 性能变化需与路径、任务支持、timeout/collision 联合解释 | 单一根因已被证明 |

## 5. 允许与禁止的主张

### 允许

- 在受控三方法五种子前瞻性比较中，UTR 的 pooled absolute performance 和安全终止率优于 SNR 与 DRTP。
- 固定非均匀权重并未解释或复制 DRTP 的历史高收益；在线自适应权重也未在新 cohort 中显示可靠的总体优势。
- 历史与前瞻性结果共同显示，训练分布加权的收益具有训练种子敏感性，必须按 training seed 报告。
- 中继故障后的问题是合法通信—任务支持路径重构及其协同后果，而非默认的信息完全丢失。

### 禁止

- “DRTP/SNR 一致优于 UTR”“DRTP 已被证明有效”或“自适应本身必要”。
- “UTR seed-stable”“均匀随机化普适最优”或“新 cohort 证明所有场景结论”。
- 把旧 cohort 的 DRTP 高收益和新 cohort 的 UTR 优势做跨合同平均。
- 删除或淡化任何灾难性/反向 seed，或把其称为可忽略异常。

## 6. 稿件与图表重构

建议中文稿定位为“中继故障拓扑重构中的自适应扰动训练与训练可靠性”。正文最小结构为：

1. 合法拓扑—任务支持重构问题及其评价语义；
2. 匹配 SG backbone、UTR 基线与 DRTP 自适应扰动训练；
3. 冻结合同、risk-set trigger validity、seed-level 统计；
4. DRTP/UTR 主结果与 paired seed-level 统计；
5. 每 seed 配对差值与安全终止图；
6. 历史 DRTP 高收益与 catastrophic seed 作为可靠性反例；
7. 将高平均收益与 seed sensitivity 同时写入主结论；

主图应优先展示 (i) 故障前后合法路径/任务支持重构示意，(ii) 三方法五 seed 的 paired endpoint 图，(iii) timeout/collision 与 survival-to-onset/risk-set validity 图。算法权重轨迹可放补充材料，不能代替绝对性能与 seed-level 结果。

## 7. 后续边界

下一步只允许对 R-DRTP 进行零训练技术合同审计；不得直接长训，不得做 SNR 变体或无合同调参。若 R-DRTP 技术门通过，再单独授权前瞻性 paired development；若失败，保留原 DRTP 论文路线，不继续搜索新算法。

**归档来源：** `D:/File/Downloads/drtp_snr_q2_mechanism_comparator_10way_results.tar.gz`

**SHA256：** `86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1`
