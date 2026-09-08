# DRTP 投稿图表合同 V1（证据冻结版）

## 使用规则

本合同以 `DRTP_FINAL_EVIDENCE_REGISTER_20260908.md` 为唯一结果来源治理文件。每幅图必须按 cohort 分层展示训练 seed；不得把 episode、条件或时间步绘成训练重复数。未完成或未审计的 6-UAV v2、2×2 消融与运行开销不制作“临时结果图”。

## 图1｜中继拓扑退化的任务问题

- **位置**：引言第 1 节后。
- **结论功能**：说明本文研究的是故障后合法感知、通信与任务支撑路径的改变，而不是向策略提供隐含拓扑真值。
- **内容**：正常 relay 路径、relay 故障后失效路径、允许的本地观测和合法消息、任务协同后果。
- **禁止元素**：最短路真值、未授权的全局图输入、任何性能数值。

## 图2｜UTR、DRTP 与 PLR-style 的训练暴露机制

- **位置**：方法第 4 节后。
- **结论功能**：清楚隔离唯一主要变化项：reset 阶段的故障组暴露分配。
- **内容**：共同 MAPPO 主干与共同 nominal anchor；UTR 的均匀故障质量；DRTP 的名义相对难度和有界更新；PLR-style 作为外部定位而非主因果对照。
- **必须标注**：actor、critic、PPO、奖励、观测、动作和执行期信息边界均不改变。

## 图3｜最终 A/B cohort 的主受控比较

- **位置**：结果 6.1--6.3，紧邻表2与表3。
- **数据**：`configs/drtp_stabilization_final_method_selection_20260906.json` 与 A/B 最终结果包。
- **图形**：两个并列 panel；每个 panel 用同 seed 连线展示 UTR 与 DRTP 的 `J_perturbed`，再叠加 cohort 均值与 95% 非推断性范围（若画误差线，图注必须写明其为种子离散性、非 episode CI）。
- **允许表述**：A/B 中均观察到正的 cohort 平均差；配对正向数分别为 3/5 与 4/5。
- **禁止表述**：逐 seed 保证、pooled n=10 显著性或全面安全优势。

## 图4｜训练排除 structural 条件带上的 endpoint

- **位置**：结果 6.4，紧邻表4。
- **数据**：`drtp_final_evidence_heldout_ood_results.tar.gz` 内的 `FINAL_HELDOUT_OOD_COHORT_SUMMARY.csv` 与 paired deltas。
- **图形**：A/B 分 panel，分别展示 `structural_J_mean`、`structural_J_worst`、timeout 与 collision；种子为点，cohort 均值为粗线。
- **允许表述**：在四个预先冻结、训练未读取的 structural 条件聚合上观察到正的 cohort 平均与下尾回报差。
- **禁止表述**：将 parameter 条件称为 structural OOD，或概括为任意未知拓扑的泛化保证。

## 图5｜PLR-style 外部定位比较

- **位置**：结果 6.5，紧邻表5。
- **数据**：`drtp_plr_matched_ab_results.tar.gz` 内的 `PLR_MATCHED_AB_COHORT_SUMMARY.csv` 与 paired deltas。
- **图形**：A/B 分 panel，方法为 UTR、DRTP、PLR-style；回报与 timeout 分别编码，不使用单一综合分数。
- **允许表述**：A cohort 倾向 DRTP；B cohort 中 PLR-style 回报更高而 DRTP success/timeout 组合更有利。
- **禁止表述**：DRTP 全面击败 PLR-style，或将该外部比较写成与 UTR--DRTP 完全相同的因果隔离。

## 图6｜6-UAV cross-scale（等待有效 v2）

- **纳入条件**：仅限 `fault-step=3` 的 v2 运行完成，并核验每个非 nominal 条件均有实际故障注入、固定 endpoint、A/B 等价训练/评价合同与可追溯原始指标。
- **旧版本**：`fault-step=9` 旧运行永久排除，不得绘图或以任何形式汇入补充材料的性能结果。

## 图7｜2×2 语义与自适应消融（等待全因子完成）

- **纳入条件**：共同训练种子、共同 tape、UTR/DRTP/Fixed-DRTP/Random-DRTP 的完整全因子汇总已审计。
- **写作边界**：若效应未能分离，只报告“训练暴露操纵敏感性”，不将任何单个分量写成因果必要条件。

## 表6｜运行开销（等待实测）

- **纳入条件**：同硬件、同并发、同预算下的 wall-clock、sampler update time、峰值 GPU memory。
- **禁止表述**：未实测前不得称为零开销或可忽略开销。
