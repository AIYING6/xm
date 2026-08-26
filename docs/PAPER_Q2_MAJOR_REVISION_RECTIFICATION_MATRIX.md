# DRTP 论文 Major-Revision 整改矩阵

**状态：** 零训练审查；本文件不改变任何历史实验裁决，也不授权新训练。  
**审查对象：** `DRTP-SG-MAPPO` 正式五种子共同 10M 证据（种子 2301--2305）。  
**核心判断：** 外部审稿意见的关键风险成立。当前稿件具有可核验的正式配对性能证据，但若不收紧术语和补足方法定位，`OOD`、`Distributionally Robust` 和“自适应性因果归因”会成为最可能导致大修的三处问题。

## 1. 已核验事实（不可回写）

- 正式比较为同容量、同 PPO、同七组训练条件、同 50% nominal anchor、同 10M 预算的 `UTR-SG-MAPPO` 与 `DRTP-SG-MAPPO`；唯一预定差异为均匀与自适应故障组加权。
- 五个训练种子均保留。DRTP 相对 UTR 的正式配对均值（中位数）为：`J_F0 +52.13 (+35.04)`、`J_OOD_mean +55.00 (+33.00)`、`J_OOD_worst +63.01 (+38.40)`，上述三个鲁棒端点均为 5/5 正向。
- 正式五种子未出现灾难性反转；但历史 development/held-out 中的负向种子与 seed sensitivity 仍是有效限制，不能改写为“稳定优越”。
- 当前十个被称为 `OOD` 的 timing/duration/compound 条件，其**具体 onset--duration 成员也曾被训练 sampler 使用**。它们不是对训练条件集合严格未见的 OOD 测试；共同 episode ID 的新颖性不能改变这一事实。
- 当前 DRTP 采用有界、EMA 平滑的回报缺口驱动指数重加权。它受 group-DRO 思想启发，但现有实现和实验**不构成**求解一般 min--max/分布鲁棒 RL 的理论证明。

## 2. 逐项整改结论

| 审稿问题 | 判断 | 无训练整改 | 若要保留更强主张所需证据 | 优先级 |
|---|---|---|---|---|
| 把已见的十个条件称为 OOD | **完全成立** | 主文统一改称“跨扰动条件 / perturbation-condition”；机器字段名可保留以维持可追溯性，但正文不再将其解释为未见分布。 | 用固定的现有 10M checkpoint，在**评价前冻结**的未见 onset--duration 组合上作独立评估；该结果只能称为探索性 unseen-configuration generalization，不能回溯写成原正式合同的 confirmatory OOD。 | P0 |
| `Distributionally Robust` 名称过强 | **成立** | 明确 DRTP 是“有界、自适应拓扑扰动重加权”，而非具有最坏分布保证的算法；保留 DRTP 代码名只作可追溯缩写。 | 若坚持严格 DRO 名称，需要给出假设、不确定集、内层问题和指数更新近似该内层解的理论或可验证推导。 | P0 |
| 指数更新与 min--max 的联系不够严谨 | **成立，但稿件已有部分公式** | 删除“求解/实现内层对手”的语句；改为“受鲁棒组重加权启发的经验训练分布控制器”。明确 q 有下上界、EMA、投影与 nominal anchor，因而是启发式受约束重加权。 | 理论分析或严格的优化等价性证明；这不应作为当前投稿前的默认补项。 | P0 |
| 只有 UTR 对照不足 | **部分成立** | 保留 UTR--DRTP 为主消融：它确实隔离了“均匀 vs 自适应训练程序”。补充外部基线不可公平移植的合同审计，而不是堆不可比表格。 | 要单独证明“**动态自适应**优于任何静态非均匀分布”，需新增预先冻结的 static-nonuniform sampler，对齐五个 seed、10M 预算、其余合同；其权重不得从正式五种子结果反推。 | P1（高价值新实验） |
| 需要 nominal-only、no-anchor、no-EMA 等更多消融 | **非全部必要** | 明确 nominal anchor 并非独立创新，且 UTR/DRTP 共同持有；因此主消融回答的仅是 adaptive-vs-uniform。 | 仅当论文额外声称 anchor、EMA 或 bounds 分别必要时，才应做对应移除实验。避免为审稿而开展无预注册的模块穷举。 | P2 |
| n=5 种子偏少 | **成立但非致命** | 主文报告每种子、均值、中位数、IQR/MAD、最差值、历史失败，训练种子为独立单位；不用 episode 数伪装重复数。 | 新的 5 个 untouched paired 10M seeds 可把正式证据扩至 n=10；成本高，适合更高目标而非当前最低投稿门槛。 | P2 |
| 安全性尤其碰撞上升未充分处理 | **完全成立** | 基于现有 12,000 raw records增补种子级 collision/timeout/constraint、pre-trigger collision、risk-set survival 表和图；结论同时写入“timeout 改善、collision 小幅上升”。 | 不需要重训。 | P0 |
| “预注册”表述可能不严谨 | **完全成立** | 除非能证明合同在训练前已公开时间戳发布，否则改为“训练前冻结（pre-specified and version-controlled）”。附录列出合同文件、Git commit 时间、tape/checkpoint hash 与裁决规则。 | 若需使用 preregistered，必须提供公开、训练前、不可篡改的时间戳证据。 | P0 |
| 可复现细节不足 | **成立** | 增加算法框、伪代码、环境/动作/观测/网络/PPO/采样器参数表、评价样本带与 artifact hash 表。 | 不需要新训练。 | P0 |
| `difficulty` 命名有歧义 | **成立** | 全文改为“相对正常工况的性能缺口（performance deficit）/ 鲁棒性缺口”，不暗示已测量 learning difficulty。 | 不需要新训练。 | P0 |
| 相关工作、标题与适用范围过宽 | **成立** | 补 Group DRO、curriculum、adaptive domain randomization 与通信故障 UAV 文献；标题限定到“中继节点故障、三角色异构 UAV、仿真”。 | 不需要新训练。 | P0 |

## 3. 推荐的投稿口径

### 可支持的结论

在冻结的中继故障条件集合内，受约束的自适应拓扑扰动重加权相对 uniform topology randomization 提升了正式五个配对训练种子的平均与中位任务鲁棒表现，并降低平均 timeout；该收益应与历史训练种子敏感性和小幅碰撞增加一并报告。

### 不可支持的结论

- 严格未见拓扑的 confirmatory OOD generalization；
- 一般分布鲁棒或严格 min--max 最优性；
- 对所有初始化可靠优越；
- 自适应性必然优于任意静态非均匀采样；
- 对 4/5 UAV、真实飞行或任意通信故障的泛化。

## 4. 三档收口路线

### 路线 A：当前最优性价比（推荐）

不再开展长训练；完成 P0 全部文字、可复现性与安全整改，并在现有 final checkpoints 上运行一次事前冻结的**未见配置探索性评价**。论文主张改为“受约束的自适应拓扑扰动重加权在固定扰动族上的鲁棒性收益”，而非 strict DRO/OOD。该路线适合稳妥的中文二区/应用型控制与智能系统投稿。

### 路线 B：最有价值的一项补训

在路线 A 基础上，新建静态非均匀 sampler 的五种子 10M 配对合同。静态权重必须在启动前由 development-only 信息或与性能无关的规则冻结，不能用正式 DRTP 的终态 q 反推。若 DRTP 仍优于 UTR 与 static sampler，才能更强地说收益来自动态适应而非单纯非均匀曝光。

### 路线 C：高成本高强度

路线 B 加新的五个 untouched UTR--DRTP paired 10M seeds，或以全新 train/test condition split 重建 confirmatory unseen-condition 协议。这一档才面向更高审稿门槛；当前没有证据要求必须完成它才能投稿。

## 5. 立即执行顺序（无训练）

1. 全文替换 OOD、DRO、difficulty、pre-registered 的高风险表述，并保留旧机器字段名的映射说明；
2. 生成安全性种子级主表/补充表和完全的运行合同附录；
3. 重写方法伪代码与数学定位，明确其是 bounded adaptive reweighting；
4. 完成相关工作和 title 的范围收紧；
5. 只在上述整改结束后，由作者决定是否授权路线 A 的新评价或路线 B 的 static-sampler 补训。

## 6. 最终审稿结论

本稿当前应被定位为 **“有扎实正式配对结果、但需要术语收紧和可复现性补强的 Major Revision”**，而不是推倒重来。最严重的风险不是正式五种子结果，而是把已见条件误称为 OOD、把经验重加权写成理论 DRO、以及未充分报告安全权衡。上述 P0 整改完成后，证据链会显著更诚实、更抗审稿；static sampler 是最值得考虑但非自动授权的唯一高价值长训练补项。
