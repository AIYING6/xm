# DRTP 最终论文证据台账（2026-09-08）

## 目的

本台账规定 DRTP 论文的证据身份。实验是否可以进入主结论，取决于其是否属于当前最终冻结合同，而不取决于其运行时间、文件夹名称、结果是否完整或数值是否有利。论文、图表、摘要和补充材料均以本台账为准。

## 术语与统计单位

- **主方法**：Original DRTP（`drtp_sg`）。这是双 cohort 完成后由方法选择文件指定的 principal method；早期 `Global-Anchored EGTR` 冻结候选并非本文最终主方法。
- **主要比较**：参数、环境、PPO、奖励、观察、动作、故障支持、训练预算和固定终点评价匹配的 `UTR` 与 `DRTP`；唯一设计差异为训练期冻结拓扑故障组的暴露分配。
- **独立单位**：训练种子。单个 seed 下的 episode、条件和时间步不作为额外的独立训练重复。
- **推断规则**：A、B 两个 cohort 分开报告；任意合并的十种子量仅可作描述性展示，不得表述为 pooled confirmatory inference。

## A. 论文主结论允许使用的最终冻结证据

| 证据 | 合同、种子与端点 | 可支持的表述上限 | 可核验来源 |
|---|---|---|---|
| 最终正式 cohort A | 种子 `78011--78015`；4 个冻结 arm；10M；7 个条件、每条件 100 episode；固定 endpoint | DRTP 相比 UTR 的 perturbed return cohort 平均差为 `+39.64`；3/5 配对 seed 为正；DRTP 的观测最差 seed 和平均 timeout 均优于 UTR | `configs/drtp_stabilization_evidence_governance_20260906.json`；`D:/File/Downloads/drtp_stabilization_A_complete_results.tar.gz`（SHA256 `429f...275f`）；其 reaggregation report |
| 最终独立 cohort B | 种子 `78021--78025`；与 A 相同的冻结方法和 10M 预算、独立训练与 endpoint tape | DRTP 相比 UTR 的 perturbed return cohort 平均差为 `+23.15`；4/5 配对 seed 为正；DRTP 的观测最差 seed 和平均 timeout 均优于 UTR | `configs/drtp_stabilization_independent_replication_freeze.json`；`D:/File/Downloads/drtp_stabilization_B_complete_results.tar.gz`（SHA256 `d5c4...ef73`）；其 reaggregation report |
| 双 cohort 方法选择 | A/B 分层审查；不 pooled inference | Original DRTP 是最终 principal method；该结论不意味着每个 seed 均胜出，亦不构成普适保证 | `configs/drtp_stabilization_final_method_selection_20260906.json`；`docs/drtp_stabilization_final_freeze_20260905/DRTP_STABILIZATION_DOUBLE_COHORT_METHOD_SELECTION_20260906.md` |

### 可用于摘要与结论的核心命题

在两个相互独立、训练前冻结的 10M cohort 中，Original DRTP 相对于匹配 UTR 基线均获得更高的扰动条件 cohort 平均回报；A/B 的平均差分别为 `+39.64` 与 `+23.15`。这种重复的 cohort 级优势应与 seed 内方向、下尾表现、超时和碰撞指标一并报告，而不写成所有 seed 均提升或无条件安全改进。

## B. 已审计的支撑性证据

下列证据不改变 A/B 中 UTR--DRTP 受控比较作为主因果对照的地位，但其来源哈希、端点、独立单位和报告口径均已复核，可在主稿的对应研究问题中分层使用。

| 证据 | 已核验的设计与结果 | 可支持的表述上限 | 明确不能推出的结论 | 可核验来源 |
|---|---|---|---|---|
| 预先冻结的 held-out structural topology 评价 | 固定 A/B 10M checkpoint；训练不读取评价 tape；4 个明确标为 `structural_ood` 的结构条件，每条件 100 episode；A/B 分开汇总。相对 UTR，DRTP 的 structural perturbed-return 平均差在 A/B 分别为 `+22.77` / `+11.96`；结构条件最差值差为 `+32.48` / `+20.03`。A 的 structural timeout 更低；B 的 structural timeout 更高而 collision 更低。 | 在该预先冻结的、训练未读取的结构条件带上，DRTP 观察到跨 cohort 的 cohort 平均回报与下尾回报增益；可靠性权衡并非所有指标同向。 | 不把 parameter 条件称为 structural OOD；不外推为任意未知故障上的普适泛化；不将 episode 视为额外训练重复。 | `configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json`；`D:/File/Downloads/drtp_final_evidence_heldout_ood_results.tar.gz`（SHA256 `68ae5c54da53b64f0ac3e8ecb5a909f9cd5af38920b16543be777b570eef0bf1`）；包内 `DRTP_FINAL_EVIDENCE_HELDOUT_OOD_REPORT.json` 与 cohort summary |
| PLR-style matched A/B 外部比较 | PLR-style 从头训练，使用 A/B 相同种子、10M 预算、任务环境、网络维度和 PPO 超参数；UTR/DRTP 为相同冻结 endpoint。A 中 DRTP / PLR 的 perturbed-return 均值为 `216.66 / 203.87`，DRTP 的 timeout 更低；B 中为 `210.34 / 220.03`，PLR 回报更高，而 DRTP success 更高、timeout 更低。 | DRTP 与通用优先级式采样具有竞争力；结果显示机制定位而非跨 cohort 的全面支配：A 倾向 DRTP，B 呈回报与成功/超时的权衡。 | 不以 PLR 替代 UTR--DRTP 主对照；不宣称 DRTP 全面优于 PLR，也不由两种 sampler 的表现归因于某个单独内部组件。 | `D:/File/Downloads/drtp_plr_matched_ab_results.tar.gz`（SHA256 `a9ce5eeb977bfe024f98277d69e443e06bb8b59b60403ed277442f218da965f4`）；包内 `PLR_MATCHED_AB_FINAL_REPORT.json`、`PLR_MATCHED_AB_COHORT_SUMMARY.csv`、各 PLR `run_manifest.json` |

## C. 待审计或待完成的补强证据

| 证据 | 当前身份 | 写入前必须完成的检查 | 暂不允许的主张 |
|---|---|---|---|
| 6-UAV v2 cross-scale | `fault-step=3` 正式协议仍待结果与故障触发审计 | 验证每个非 nominal 条件实际注入、固定 endpoint、UTR/DRTP 成对汇总和条件定义 | 不使用旧 `fault-step=9` 训练结果；不将单一规模迁移写成普适规模保证 |
| 2×2 semantic/adaptive ablation completion | 云端运行中 | 核对新增 UTR/DRTP 与已有 Fixed/Random 的共同 seed、同一 tape、全因子汇总 | 在完成前不声称拓扑语义和自适应更新分别具有已识别的因果必要性 |
| 运行开销 | 尚未形成统一测量 | 同硬件、同并发、同训练预算下测量 wall-clock、采样更新时间与峰值显存 | 不写“零开销”或“可忽略开销” |

## D. 历史、开发和诊断证据：保留但不进入主结论

| 证据 | 身份 | 论文允许位置 | 禁止用途 |
|---|---|---|---|
| `2301--2305` 旧正式五种子结果 | 早期项目主线的历史合同，不是当前最终 A cohort | 补充材料中的项目演变/历史风险说明；必要时一段简要背景 | 不再称为当前论文的正式主 cohort，不与 A/B 合并 |
| `2401--2405` 三方法队列 | 早期历史独立队列，不是当前最终 B cohort | 补充材料中的历史训练敏感性说明 | 不再称为本文最终独立确认 cohort；不压过 A/B 双 cohort 主结论 |
| 机制根因、rollback、KL、PPO、q 等审计 | 事后诊断 | 补充材料或内部审计，且仅按其原始证据范围解释 | 不作为主方法效果的确认性结果；不把相关性写成根因 |
| EGTR、GA-EGTR、PVF 及其他稳定化尝试 | 已冻结的开发候选或探索路线 | 补充材料中的候选筛选/历史演变 | 不改写 Original DRTP 的最终 principal-method 选择 |

## E. 永久排除的结果

早期 6-UAV `fault-step=9` 训练不进入性能证据。Q0 审计表明 episode 常在该时刻之前结束，非 nominal 组的有效故障注入为零；即使训练与汇总文件完整，也不能回答跨规模拓扑故障鲁棒性问题。相关 read-only timing 审计只能证明后续 `fault-step=2/3` 的故障时机可行，不能将旧结果追认为有效。

## F. 论文编辑规则

1. 标题、摘要、主结果表、结论首先引用 A/B 最终冻结证据；不再引用 `2301--2405` 作为当前正式比较。
2. 历史队列不删除，但不得在摘要、图 1--图 5、主结果章节或结论中承担“独立反向”的角色。
3. 可靠性表述采用“两个独立冻结 cohort 中重复观察到的 cohort 级收益”；同时报告 3/5 与 4/5 配对方向，不把均值改写为逐 seed 保证。
4. 碰撞、超时和任务回报独立报告。A 的 collision 增量不允许被回报或 timeout 改善掩盖。
5. 任何新结果导入前，都必须补入本台账的来源、协议、独立单位、允许 claim 与禁止 claim。

## 版本关系

`configs/drtp_stabilization_final_freeze.json` 记录的是 A 启动时的候选冻结；其中 `Global-Anchored EGTR` 的候选地位已被 A/B 完成后的 `configs/drtp_stabilization_final_method_selection_20260906.json` 覆盖。后者是本文当前 principal-method 选择的唯一依据。
