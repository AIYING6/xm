# Journal Matching — v1.5 manuscript (2026-08-07)

> Data from web search (2025/2026 JCR & 中科院分区); re-verify IF/分区 on the journal
> official page at submission time. Paper profile is locked (see PAPER_RESTRUCTURE_MAP_V1_5).

## 0. Paper profile (locked)

- Topic: multi-UAV / multi-agent coordination + MARL + graph relational reasoning +
  fault/post-failure recovery + semantic search (3DOF heterogeneous interception).
- Core selling point: **post-failure coordination recovery + task-graph relational
  modeling in complex unmanned systems** — NOT a pure RL-algorithm novelty, NOT pure vision.
- Strength: complete locked evidence chain (held-out/robustness/efficiency + two
  mechanism analyses), honest trade-offs, rigorous auditing.
- Must avoid: journals demanding strict stability proofs (pure control theory), hardware
  robot journals demanding real-flight platforms as the core, and top-AI journals whose
  bar is "novel MARL algorithm alone".

## 1. Candidate journals (A/B/C tiers)

### A tier — stretch / edge-Q1

| Journal | IF (latest) | 中科院 | Match | Recent similar work (verified) | Requires real flight? |
|---|---|---|---|---|---|
| **Engineering Applications of Artificial Intelligence** (EAAI, Elsevier) | ~9.0 (2025) | 1区Top (2025升) | High (applied AI, MARL/UAV common) | "Graph diffusion network for MARL" (EAAI 2025); MARL/UAV applications frequent | No |
| **Chinese Journal of Aeronautics** (CJA) | ~5-6 | 1区Top (2025) | High (aerospace, UAV cooperative search) | "Graph-based MARL for collaborative search" (CJA 2025) | No (sim accepted) |
| **IEEE Trans. SMC: Systems** | ~6-8 | 1区Top | Medium-High (systems/control; MARL articles) | MARL/autonomous-systems papers frequent | No |

### B tier — primary Q2 targets (best fit)

| Journal | IF (latest) | 中科院 | Match | Recent similar work | Requires real flight? |
|---|---|---|---|---|---|
| **IEEE Trans. Aerospace and Electronic Systems** (TAES) | ~4-5 | 2区Top | **Highest** (heterogeneous UAV interception, radar/sensing, communication degradation, MARL) | "MARL for Offloading Cellular Communications with Cooperating UAVs" (TAES 2024); UAV pursuit-evasion & cooperative articles frequent | No |
| **Neurocomputing** | ~5.5 | 2区 | High (GNN+MARL is a mainstay; UAV swarm MARL common) | "Graph-based MARL for collaborative search"; many GNN-MARL papers | No |
| **IEEE Robotics and Automation Letters** (RA-L) | ~5.2 | 2区Top | High (UAV/autonomous systems) | UAV MARL / swarm papers common | **Often expects platform/sim validation; our 3DOF sim OK but highlight fidelity** |

### C tier — safe / fallback

| Journal | IF (latest) | 中科院 | Match | Notes | Requires real flight? |
|---|---|---|---|---|---|
| **Applied Intelligence** (Springer) | ~3.5 (2026) | 2-3区 | Medium-High | Generic AI applications; accepts sim-based MARL | No |
| **Drones** (MDPI) | ~4.8 (2025) | 3区 | High (pure UAV venue) | OA; APC ~2000 CHF; loose page limits (good for our appendix) | No |
| **Journal of Intelligent & Robotic Systems** (Springer) | ~3.0-3.5 | 3区 | Medium-High | UAV/robotics venue | No |
| **Robotics and Autonomous Systems** (Elsevier) | ~4 | 3区 | Medium | Autonomous systems venue | No |

(备选：IEEE Trans. Intelligent Vehicles / Aerospace / 等，如 TAES 拒后同门。)

## 2. Recommendation & submission order

- **首选 TAES**：领域完全对口（异质 UAV 协同拦截 + 有限通信/间歇感知 + 故障恢复），
  2 区 Top 且接受应用型 MARL 文章，不要求真实飞行；我们最大的卖点（reliability–recovery-speed
  trade-off + 完整审计）在此刊语境最自然。风险：审稿周期较长（~3-6 月）。
- **二投 Neurocomputing**：GNN+MARL 主场，接受度与周期平衡，2 区；方法亮点（multi-relation
  task-graph attention + Gate Prior 机制分析）在此刊有天然读者。
- **三投 Applied Intelligence 或 Drones**：保底。Drones 版面宽松、纯 UAV 语境最省改写；
  Applied Intelligence 中规中矩。
- 冲刺选项（在 TAES 投出后并行评估）：EAAI（IF 高、应用匹配）或 CJA（航空航天语境）。

## 3. Per-journal adaptation

| Journal | Title/Abstract | Length/format | References | Extras |
|---|---|---|---|---|
| TAES | 保留 aerospace 语境（kill-chain/interception/target tracking）；摘要 ~200 词符合 | 篇幅可长（双栏，正文+附录）；IEEE 格式 | 补 5-8 篇 TAES 近期 UAV/MARL/数据链文章 | 强调"电子系统"视角：sensing/communication 退化模型细节可前置 |
| EAAI | 强调 engineering application + 系统级评价；摘要按 Elsevier 单栏 | 常规 25-35 页单栏 | 补工程 AI 应用类引用 | 加一段"与真实工程约束"讨论 |
| Neurocomputing | 方法贡献前置（multi-relation graph attention）；补 GNN/MARL 定位 | 常规 | 补 GNN-MARL 综述与经典（GAT/MARL） | Method 可加一小节伪代码 |
| RA-L | 突出机器人/自主系统；强调 decentralized execution | 篇幅受限（8 页正文+附录） | 补 RA-L/IROS/ICRA 相关 | 可能要求说明仿真保真度；不承诺实飞 |
| CJA | 航空航天语境；中文版同步考虑 | 双栏 | 补 CJA 无人机协同文章 | 中文稿可另投中文版 |
| Drones | 直白 UAV 语境；附录可全收 | 版面宽松 | MDPI 格式 | OA 费用；审稿快 |
| JIRS/RAS | 常规适配 | 常规 | 常规 | — |

## 4. Submit checklist before first submission

- [ ] 完整编译通过（在有 TeX 环境的机器上跑 main + supplementary 各 2 遍）
- [ ] 按目标刊格式压缩 Abstract（180–230 词；TAES 双栏）
- [ ] 参考文献补该刊近期 5-8 篇（提升"贴合度"信号）
- [ ] 补充图表分辨率（期刊要求 dpi）
- [ ] 数据可用性声明（canonical_results_v1_5.csv + 锁定资产可开放）
- [ ] 再次跑三层 audit（数值/机制/协议）+ 静态结构审计（scripts 已有）
