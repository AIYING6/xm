# DRTP 稳定化候选：继续训练资格审计

**日期：** 2026-08-26  
**范围：** 零训练状态审计；不改变 EGTR、R-DRTP、UTR、DRTP 或 SNR 的实现、参数、种子与历史结论。

## 结论

**当前没有获得继续长训授权的 DRTP 稳定化候选。**

这不是对 EGTR 实现正确性的否定，而是现有冻结阶段门的正确作用。任何继续训练必须先有一个在训练前可执行、且不由既有结果倒推的安全决策规则；在此之前，启动 EGTR 1M→3M、复活 R-DRTP 或设计新的稳定化变体均不合规。

## 候选状态

| 候选 | 当前状态 | 可否启动新训练 | 理由 |
|---|---|---|---|
| scalar-min R-DRTP | `ARCHIVED` | 否 | P2 技术审计不等于长训授权；路线已由 EGTR 取代，不能将其作为备选重启。 |
| EGTR-DRTP | `P3_1M_TECHNICAL_AND_MECHANISM_PASS__SAFETY_REVIEW_REQUIRED` | 否 | 9/9 轨迹、10,800 条评估记录和运行时状态审计完整，但既有 P3 合同未量化“明显 safety warning”。 |
| 新的 DRTP 稳定化变体 | 未授权 | 否 | 不得以 EGTR 的结果为依据再搜索 EGTR-v2 或第四种稳定化机制。 |

## EGTR 的冻结事实

- P3 为 development-only 的 UTR/DRTP/EGTR × seeds 2501–2503 × 1M 训练；未使用 held-out 或 canonical seeds。
- 技术、风险集 trigger validity、sampler 语义、runtime-state 和 trust-region 审计通过；EGTR 不是静默的 UTR fallback。
- EGTR 未触发既有 catastrophic definition。
- 但 seed2503 相对 paired UTR 的 collision difference 为 `+0.141`，同时 timeout difference 为 `-0.211`。这是一项不可忽略的 collision–timeout 权衡；它不是 evaluator 缺陷，且不能由 pooled return 覆盖。
- 冻结 P3 合同没有把“明显 safety warning”写成能在该 1M 结果上机械判定的数值规则。因此，不能在观察结果后补写阈值并把 EGTR 自动放行到 3M。

## 当前允许的工作

1. 继续论文的无训练收口：完整呈现 UTR–DRTP 主消融、SNR 机制反例、MAPPO-NoGraph 外部参考、seed-level 可靠性和 collision–timeout 权衡。
2. 完善可复现材料：训练/评价合同、样本带哈希、配置、聚合与作图脚本、原始记录路径、归档 SHA256 和数据可用性清单。
3. 在不改变科学状态的前提下，完成目标中文期刊模板、参考文献、图表/统计一致性和投稿元数据。

## 当前禁止的工作

- EGTR 1M→3M continuation；
- R-DRTP 复活或重训；
- SNR-v2、DRTP-v2、EGTR-v2 或重新选择权重/阈值；
- 用既有 seed、checkpoint 或有利中间里程碑构造新确认性结论；
- 将 EGTR 的 development 结果混入 DRTP 正式主结论。

若作者未来希望恢复稳定化训练，必须先单独决定是把已记录的 EGTR collision trade-off 视为 stop，还是建立一个完全前瞻性的全新实验合同。后一种情况下，合同不得通过修改已见 P3 结果来选择安全阈值、预算或候选机制。
