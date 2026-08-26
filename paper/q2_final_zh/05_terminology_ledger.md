# 05 Terminology Ledger

| Canonical term | First-use definition | Prohibited or legacy variants | Decision |
|---|---|---|---|
| DRTP-SG-MAPPO | 有界自适应拓扑扰动重加权单图 MAPPO | Distributionally Robust Topology-Perturbation Single-Graph MAPPO、DRTP Full、DRTP-Stable | 保留 `DRTP` 作为项目/代码缩写；正文不将其扩展为具有理论保证的 Distributionally Robust。 |
| UTR-SG-MAPPO | Uniform Topology Randomization Single-Graph MAPPO | ordinary SG when referring to the matched training baseline | Use full name once, then UTR. |
| matched Single-Graph MAPPO | shared 116,728-parameter actor/critic backbone | wider SG, old matched-SG without contract label | Always state the contract when ambiguity exists. |
| relay-node failure | failure of the Relay role under frozen semantics | information blackout, relay disconnection unless proven | Failure does not imply no legal direct path. |
| topology/path reconfiguration | change in legal communication-path and task-support composition | information restoration, strict recovery | Primary mechanism term. |
| nominal condition | no injected relay failure | normal scene, clean scene | Use “nominal.” |
| canonical F0 | onset 44, duration 80 frozen canonical failure | default failure without definition | Define once with onset and duration. |
| 跨扰动条件 | 十个已纳入训练扰动族、并在共同最终检查点下评价的时机/持续时间/复合条件 | OOD、未见条件、严格分布外条件 | 这些具体 onset--duration 成员曾用于训练；只可称跨扰动条件。 |
| `J_nominal` | mission score under nominal evaluation | nominal reward if the quantity is mission score | Keep symbol and definition stable. |
| `J_F0` | mission score under canonical F0 | failure reward | Keep symbol and definition stable. |
| `J_pert,mean` | 十个冻结跨扰动条件的共同合同平均任务得分；机器字段为历史 `J_OOD_mean` | generalization score、OOD 均值 | 正文使用前者，并给出机器字段映射。 |
| `J_pert,worst` | 十个冻结跨扰动条件中的最小任务得分；机器字段为历史 `J_OOD_worst` | worst-case robustness、OOD 最差 | 始终说明是冻结条件集合内的最差值。 |
| training seed | independent statistical unit | episode as replicate | Never treat episodes as training replicates. |
| risk-set trigger validity | trigger success among episodes alive immediately before onset | all-episode exposure as evaluator validity | Overall outcomes still retain all episodes. |
| training-seed sensitivity | reproducible difference in final policy outcomes across training seeds | proven policy-basin divergence | Basin is only a candidate explanation. |
| prospective formal confirmation | frozen paired UTR/DRTP experiment on seeds 2301–2305 at 10M steps | final experiment before completion; definitive proof | Primary prospective evidence, conditional on technical validity. |
| catastrophic training seed | a paired seed satisfying the training-pre-specified formal collapse rule | pre-registered seed、bad seed、outlier to be removed | 除非存在训练前公开时间戳，否则不用“预注册”；始终保留弱种子。 |
| 正常工况 | no injected relay failure; first use may include `(nominal)` | nominal condition throughout Chinese prose | Use Chinese after first definition; metric symbol `J_nominal` remains unchanged. |
| 配对评估样本带 | common base episode-ID namespace reused across methods, seeds, and conditions | evaluation tape, tape | Use Chinese prose; retain numeric namespace and machine file names. |
| 故障起始时刻存活风险集 | episodes alive immediately before scheduled failure onset | risk set, alive-at-onset set | Technical trigger validity denominator only. |
| 灾难性种子 | training seed satisfying the frozen paired collapse rule | catastrophic seed, bad seed, outlier | Never exclude; report adjacent to central effects. |
| 正式结果占位符（历史） | 正式结果归档前用于保护主稿的临时标记 | formal-result placeholder (historical) | 已在正式归档 SHA256 核验和 fail-closed 整合后全部移除；不得从实时日志回填。 |
