# DRTP 中文稿项目侧收口审计

**状态：** `PROJECT_SIDE_COMPLETE_AUTHOR_ACTION_REMAINS`
**审计日期：** 2026-08-27
**范围：** 仅核验项目可由代码、版本库和冻结证据完成的工作；不虚构作者身份、目标期刊、外部匿名托管地址或许可证。

## 1. 结论

DRTP 中文主稿的项目侧科学收口已完成。主 cohort、无图 MAPPO 性能参考和独立三方法反向 cohort 均被完整保留为彼此分层的证据，且明确禁止跨 cohort 合并为 `n=10`。本次审计未启动训练、未重选 checkpoint、未删除种子，也未改变任何冻结结果。

当前投稿 release gate 的正确状态仍为：

```text
TECHNICAL_READY_AUTHOR_ACTION_REQUIRED
```

它表示科学证据、文稿、补充材料和本地匿名复现 staging 均已就绪；它不是科学失败，也不是对主 cohort 结果的否定。

## 2. 项目侧完成矩阵

| 工作项 | 项目侧状态 | 可核验资产 | 结论边界 |
|---|---|---|---|
| 正式主比较 | PASS | `main_zh.md` 第 6 节、`formal_results/` | 仅 UTR--DRTP 是参数匹配的主因果消融。 |
| 独立反向 cohort | PASS | `main_zh.md` 第 6.9 节、`supplementary/S4_independent_three_arm_replication.md` | 2401--2405 完整披露；不得与 2301--2305 合并。 |
| 外部性能参考 | PASS | `formal_results/external_reference_summary.md` | MAPPO-NoGraph 仅作性能定位，不能用于图结构或自适应机制的单独因果归因。 |
| 主张--证据审计 | PASS | `23_claim_evidence_audit.md` | 禁止 strict OOD、一般 DRO、跨 cohort 稳定优越及 adaptive necessity 主张。 |
| 方法公式与术语 | PASS | `main_zh.md` 第 4 节；终稿 PDF | 难度、EMA、平滑和有界单纯形投影均按真实实现表达。 |
| 图表与补充材料 | PASS | `11_chinese_figure_table_plan.md`、`supplementary/S1--S4`、八张受控图 | 图表服务于主论证；未以额外图表扩大结论。 |
| 真实文献与新颖性定位 | PASS | `references_core.enw`、`09_citation_ledger.md`、`26_novelty_and_prior_art_positioning.md` | 仅完成核心文献层；目标刊格式化在选刊后执行。 |
| 本地匿名复现包 | PASS | `24_anonymous_reproducibility_package.md`、`28_anonymous_package_staging_audit.md` | 本地 staging 与 checksum 已验；不能替代真实外部匿名访问。 |
| 最终证据冻结 | PASS | `25_final_evidence_manifest.json` | 保留三层证据并禁止新训练与跨 cohort pooling。 |
| 中文终稿视觉核验 | PASS | `output/DRTP_SG_MAPPO_中文论文终稿_投稿前审稿版.pdf` | 已检查 19 页 PDF 的标题页、方法/公式页、结果/表格页、独立 cohort 页和声明页。 |
| 审稿人预演 | PASS | `27_presubmission_reviewer_simulation.md`、`30_final_scientific_version_reviewer_assessment.md` | 已将新颖性、static nonuniform 缺失、三无人机范围、非 strict OOD 和可靠性限制纳入边界。 |

## 3. 本次 PDF 质量核验

终稿 PDF 由 `scripts/build_q2_chinese_draft_pdf.py` 可重复生成。此次复核确认：

1. 公式中的下标、难度/投影记号和表格端点采用论文排版，而非代码字段形式；
2. 表 2、表 2b 与配对效应表未出现截断、重叠或孤立表头字符；
3. 18,000 条独立三方法 cohort 记录及其反向结果在正文中完整呈现，且与正式 cohort 分层；
4. 页眉、正文和讨论没有将内部稳定化候选写入本篇 DRTP 主方法；
5. PDF 仍为“投稿前审稿版”，尚未假装符合任何未选定期刊的最终模板。

## 4. 可重复核验命令

```powershell
$py = 'C:/Users/96251/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py scripts/check_q2_final_zh_manuscript.py
& $py scripts/build_q2_chinese_draft_pdf.py
& $py scripts/check_drtp_submission_release_gate.py
```

预期结果：前两项通过；第三项在作者动作未完成时输出 `TECHNICAL_READY_AUTHOR_ACTION_REQUIRED`。

## 5. 有意保留的作者侧动作

以下事项由作者在实际投稿前完成，当前不阻塞项目侧收口，也不得由代码或 AI 猜测填入：

1. 从官方范围清单中选择目标期刊和文章类型；
2. 建立真实匿名仓库、执行外部下载/校验，并决定许可证、永久标识符和 checkpoint 访问策略；
3. 填写作者、单位、通讯作者、基金、CRediT、利益冲突和原创性事实；
4. 迁移到目标期刊模板并做最终人工版面核验。

在这些动作前，主稿应被称为“科学终稿/投稿前审稿版”，而不是“已可提交的目标刊终稿”。
