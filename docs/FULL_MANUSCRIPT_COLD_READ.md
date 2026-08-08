# Full Manuscript Cold Read A

**Read scope:** title, abstract, keywords, Sections 1–7, both main figures, Tables 1–3, Supplementary S1–S5 and the active BibTeX source. This read preceded the targeted convergence edits and did not use historical drafts as evidence.

- **一句话研究问题：** 在严格间歇感知、环境受限通信和中继失效共同存在时，异构无人机编队何时重新形成稳定任务链？
- **一句话 central claim：** 在锁定 nominal held-out 的 matched failure exposure 下，EA-RG 相对 MAPPO 在预设故障活动窗口内更早恢复任务链。
- **一句话方法思想：** 将可感知、环境已递送和任务相关的依赖分为三类图关系，再以边特征调制的关系专属聚合与联合图残差供去中心化 actor 使用。
- **三项以内核心创新：** 任务链恢复的事件时间问题化；三关系任务图表征；匹配失效暴露下的 KM/RMST80 主证据。
- **最强证据：** RMST80 11.81（EA-RG）对 15.51（MAPPO），三个 seed 差异均为负，hierarchical paired-bootstrap 95% CI 为 [−7.16, −1.05] 步。
- **最关键 trade-off：** 早期优势并不构成相对 HAPPO/宽单图的全时域统一排序。
- **最大适用边界：** 零样本迁移随变化族而变，通信拓扑变化可反转比较；证据限于 3DOF 受控仿真。
- **最容易记住的内容：** 以故障持续期的任务链恢复，而非终局成功率，评价协同质量。
- **最容易误解的内容：** 将图聚合误读为策略控制物理通信，或将 EA-RG 的 P1 比较扩展为对所有基线和 OOD 的优越。

**Blueprint comparison:** the manuscript now reads in the same P1→P2→P3 order as `PAPER_BLUEPRINT.md` and `NARRATIVE_HIERARCHY.md`; its claim ceiling agrees with `SCIENTIFIC_CLAIM_STATE_LEDGER.md`. No macro-story contradiction was found.
