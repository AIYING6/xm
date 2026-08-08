# 参考文献核验台账（P2）

**范围：** `paper_latex_3d_en/references.bib` 的 21 条目。核验日期 2026-08-08。优先顺序为 DOI 的 Crossref 元数据，其次为出版方/会议论文集或 arXiv 的一手记录。此台账不修改 `references.bib`；格式修订必须在论文生产后续阶段以独立补丁进行。

## 摘要

- 已核验书目信息：19/21（其中会议/预印本以一手会议页或 arXiv 记录核验）。
- 必须修正：2/21（`royston2011rmst` 的卷期页；`zhou2023racer` 的 DOI）。
- 未发现 DOI 张冠李戴；`ou2024air_combat_gcn_drl` 的 DOI 不由 Crossref 返回，但已由期刊出版方 PDF 核验。
- 现有 21 条仅能覆盖基础 MARL、图/通信和少量 UAV 应用背景；在最终稿完成前仍须按主张矩阵补充/替换，而非机械扩大数量。

| BibTeX key | 核验状态 | 核验来源 | 结论 / 后续处理 |
|---|---|---|---|
| schulman2017ppo | 已核验 | [arXiv:1707.06347](https://arxiv.org/abs/1707.06347) | 预印本记录与作者、题名、年份一致。 |
| yu2022mappo | 已核验 | [NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/9c1535a02f0ce079433344e14d910597-Abstract-Datasets_and_Benchmarks.html) | 题名、作者、年份一致。 |
| velickovic2018gat | 已核验 | [ICLR/OpenReview](https://openreview.net/forum?id=rJXMpikCZ) | 题名、作者、年份一致。 |
| liu2024gnn_marl | 已核验（预印本） | [arXiv:2404.04898](https://arxiv.org/abs/2404.04898) | 可作综述入口，不应作为关键实证依据。 |
| lowe2017maddpg | 已核验 | [NeurIPS 2017](https://proceedings.neurips.cc/paper/2017/hash/68a9750337a418a86fe06c1991a1d64c-Abstract.html) | 题名、作者、年份一致。 |
| zhu2024comm_madrl_survey | 已核验 | [Crossref](https://api.crossref.org/works/10.1007/s10458-023-09633-6) | 期刊、卷期、题名一致。 |
| ding2024magi | 已核验 | [Crossref](https://api.crossref.org/works/10.1609/aaai.v38i16.29682) | 38(16):17346--17353 与条目一致。 |
| wang2024air_combat_drl_review | 已核验（早期在线年提示） | [Crossref](https://api.crossref.org/works/10.1007/s10462-023-10620-2) | Crossref 记录 online 2023、卷期归入 2024；Bib 采用卷年 2024 可接受，最终格式按目标期刊统一。 |
| ou2024air_combat_gcn_drl | 已核验（出版方） | [期刊 PDF](https://cje.ustb.edu.cn/cn/article/pdf/preview/10.13374/j.issn2095-9389.2023.09.25.004.pdf) | Crossref DOI 查询 404，但出版方确认 46(7):1227--1236、题名与作者一致。 |
| huo2025graph_air_combat | 已核验 | [Crossref](https://api.crossref.org/works/10.1038/s41598-025-00463-y) | 题名、作者、期刊、卷年一致；文章号以出版方最终记录为准。 |
| kuba2022happo | 已核验 | [ICLR/OpenReview](https://openreview.net/forum?id=R1gRIs5yQ6) | 题名、作者、年份一致。 |
| rashid2018qmix | 已核验 | [PMLR](https://proceedings.mlr.press/v80/rashid18a.html) | 题名、作者、页码、年份一致。 |
| sukhbaatar2016commnet | 已核验 | [NeurIPS 2016](https://proceedings.neurips.cc/paper_files/paper/2016/hash/55b1927fdafef39c48e5b73b5d61ea60-Abstract.html) | 题名、作者、年份一致。 |
| jiang2018i2c | 已核验 | [NeurIPS 2018](https://proceedings.neurips.cc/paper/2018/hash/6a8018b3a00b69c008601b8becae392b-Abstract.html) | 题名、作者、年份一致；Bib key 中的 `i2c` 只是键名，不应在正文误称为 2020 年的 I2C 工作。 |
| das2019tarmac | 已核验 | [PMLR](https://proceedings.mlr.press/v97/das19a.html) | 题名、作者、页码、年份一致。 |
| qiu2023resilience | 已核验 | [Crossref](https://api.crossref.org/works/10.1016/j.apenergy.2023.120826) | 336:120826 与条目一致。 |
| kaplan1958 | 已核验 | [Crossref](https://api.crossref.org/works/10.1080/01621459.1958.10501452) | 53(282):457--481 与条目一致。 |
| royston2011rmst | **必须修正** | [Crossref](https://api.crossref.org/works/10.1002/sim.4274) | DOI 所指题名正确，但正式元数据为 *Statistics in Medicine* **30(19):2409--2421**；当前条目的 30(17):2080--2098 错误。 |
| uno2014rmst | 已核验 | [Crossref](https://api.crossref.org/works/10.1200/JCO.2014.55.2208) | 32(22):2380--2385 与条目一致。 |
| tian2022kimeramulti | 已核验 | [Crossref](https://api.crossref.org/works/10.1109/TRO.2021.3137751) | 38(4):2022--2038 与条目一致。 |
| zhou2023racer | **必须修正** | [Crossref title query](https://api.crossref.org/works?query.title=RACER%3A%20Rapid%20Collaborative%20Exploration%20With%20a%20Decentralized%20Multi-UAV%20System) | 正确 DOI 是 **10.1109/TRO.2023.3236945**；当前 `10.1109/TRO.2023.3237670` 返回 404。卷期页 39(3):1816--1835 正确。 |

## 引用内容适配性

文献身份正确不等于可支撑论文陈述。具体支持范围受 [主张—参考文献绑定矩阵](literature/CLAIM_REFERENCE_MATRIX.md) 约束。尤其是 Ou (2024) 与 Huo (2025) 必须用于限制“图 MARL 空战首创”语言；Royston--Parmar 和 Uno 仅支持 KM/RMST 的统计背景，不能支持项目结果本身。
