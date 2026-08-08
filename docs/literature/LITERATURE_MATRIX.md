# P2 文献证据矩阵

**审计日期：** 2026-08-08。检索采用 Crossref（DOI/书目信息）、出版方或会议论文集（内容与发表状态）和 arXiv（预印本）交叉核对。本文只记录可支撑当前收束主张的最小文献集；不以检索结果证明“首次”或“没有任何既有工作”。

## 支持、反证与最接近工作检索结果

| ID | 经核验工作 | 可安全支持的背景/方法语句 | 对本稿的反证或边界 | 证据级别与出处 |
|---|---|---|---|---|
| L1 | Kaplan & Meier (1958); Uno et al. (2014); Royston & Parmar (2011) | 右删失事件时间可用 Kaplan--Meier 曲线估计；RMST 是指定截断点前生存曲线下面积的可解释汇总量。 | 这些是统计学文献，不能替代本项目对独立训练种子和环境 episode 的设计说明。 | T1 Crossref / 出版方。见 [Kaplan--Meier](https://doi.org/10.1080/01621459.1958.10501452)、[Uno et al.](https://doi.org/10.1200/JCO.2014.55.2208)、[Royston--Parmar](https://doi.org/10.1002/sim.4274)。 |
| L2 | Yu et al. (2022), MAPPO；Kuba et al. (2022), HAPPO | CTDE 的 PPO 类多智能体方法是合理的比较背景。 | 不能把图模型带来的变化归因于 PPO/MAPPO 本身；HAPPO 已是异构协作的强对照，不可遗漏。 | 一手会议记录：[MAPPO](https://proceedings.neurips.cc/paper_files/paper/2022/hash/9c1535a02f0ce079433344e14d910597-Abstract-Datasets_and_Benchmarks.html)、[HAPPO](https://openreview.net/forum?id=R1gRIs5yQ6)。 |
| L3 | Veličković et al. (2018), GAT；Liu et al. (2024), graph-MARL survey | 图注意力和图式信息聚合为关系感知的策略表示提供方法背景。 | 图注意力、图通信或图 MARL 都不是本稿可主张的独创点。Liu et al. 为预印本综述，只适合作背景检索入口。 | 一手会议记录：[GAT](https://openreview.net/forum?id=rJXMpikCZ)；[综述预印本](https://arxiv.org/abs/2404.04898)。 |
| L4 | Sukhbaatar et al. (2016), CommNet；Jiang & Lu (2018), attentional communication；Das et al. (2019), TarMAC；Ding et al. (2024), MAGI | 学习式通信与有目标的信息传递是 MARL 的既有路线；可用于说明受限通信下协调问题的重要性。 | “学习通信”“注意力通信”或“鲁棒通信”均已有先例，不能作为 EA-RG 的新颖性结论。MAGI 的鲁棒性目标也说明不能暗示本方法自动获得跨分布通信鲁棒性。 | 一手会议/出版方：[CommNet](https://proceedings.neurips.cc/paper_files/paper/2016/hash/55b1927fdafef39c48e5b73b5d61ea60-Abstract.html)、[attentional communication](https://proceedings.neurips.cc/paper/2018/hash/6a8018b3a00b69c008601b8becae392b-Abstract.html)、[TarMAC](https://proceedings.mlr.press/v97/das19a.html)、[MAGI](https://doi.org/10.1609/aaai.v38i16.29682)。 |
| L5 | Ou et al. (2024)；Huo et al. (2025) | 已有工作将图神经网络/图卷积与强化学习用于多机协同空战；可用于建立具体应用背景。 | 这是最关键的反证：不能声称“首次将 GNN/图 MARL 用于协同空战”。两者的已报告终点是机动/对抗表现或胜率，而非本稿的中继失效后任务链恢复时间。 | 出版方全文：[Ou et al.](https://cje.ustb.edu.cn/cn/article/pdf/preview/10.13374/j.issn2095-9389.2023.09.25.004.pdf)、[Huo et al.](https://doi.org/10.1038/s41598-025-00463-y)。 |
| L6 | Zhou et al. (2023), RACER | 多 UAV 在异步、有限通信下维持协同任务是已有工程问题。 | RACER 是去中心化探索/规划工作，非 MARL、非异构拦截、非节点失效后的事件时间恢复；仅可作相邻应用背景，不能作直接算法比较。 | 一手论文：[IEEE T-RO DOI](https://doi.org/10.1109/TRO.2023.3236945)，[作者预印本](https://arxiv.org/abs/2209.08533)。 |
| L7 | Qiu et al. (2023), multi-energy microgrid resilience | MARL 可被用于系统受损后的任务恢复/调度问题。 | 领域、动力学、观测与指标均不同；该工作不能支撑“UAV 任务链恢复已被充分研究”，也不能构成直接基线。 | T1 Crossref / 出版方：[Applied Energy](https://doi.org/10.1016/j.apenergy.2023.120826)。 |
| L8 | Zhu et al. (2024), communication-MARL survey；UAV swarm anti-jamming MARL | 通信质量与抗干扰是 UAV MARL 的活跃研究方向。 | 反证“通信受损情形尚无人研究”的强说法。所见工作主要优化吞吐、功率、继电选择或抗干扰，而非失效暴露匹配的恢复时间分布。 | T1 Crossref：[Zhu et al.](https://doi.org/10.1007/s10458-023-09633-6)；出版方：[UAV anti-jamming](https://doi.org/10.1109/TWC.2023.3268082)。 |

## 有界检索结论

检索覆盖了五个必要维度：异构/多 UAV 协作、图或关系 MARL、受限通信/失效韧性、任务依赖，以及恢复时间/事件时间评估。已找到图式协同空战、学习通信、有限通信 UAV 协作和非 UAV 系统恢复调度等相邻研究；在本次可核验的检索集内，**未定位到同时具备**“严格间歇感知 + 中继节点失效 + 三关系任务图 + 匹配失效暴露的 KM/RMST 恢复终点”的工作。

这是一项**范围受限的差异化核对**，不是“first”或“no prior work”的证据。最终中文稿应使用“区别于……，本文聚焦……”的陈述，而非“首次”“尚无研究”或“填补空白”。

## 停止准则

当前矩阵已为统计终点、MARL 对照、图/通信背景、UAV 图式空战和失效韧性提供一手或 T1 元数据来源，也已纳入最直接的反证工作。除非新稿提出新的强文学缺口或目标期刊要求系统综述，否则停止扩张引用数量，转入主张—引用绑定与逐条格式修正。
