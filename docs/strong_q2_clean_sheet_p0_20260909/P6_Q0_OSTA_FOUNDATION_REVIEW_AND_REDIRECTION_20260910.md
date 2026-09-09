# P6-Q0 OSTA 地基预审与方向修正

日期：2026-09-10  
结论：`OSTA_V1_STRONG_Q2_NO_GO / CIRU_OSTA_Q0_CANDIDATE`

## 1. 决策摘要

原始 OSTA-v1（行为历史编码、未知对手适应、不确定性、响应策略选择）**不应直接进入训练**。它与 GSCU、HOP、OMIS、MBOM、Bayesian policy reuse 和 open-set opponent modeling 的问题与机制重叠过大。即使在 UAV 场景得到正结果，也更像已有 opponent-adaptation 范式的领域实现，不能稳定满足“强二区、创新性在训练前站得住”的要求。

保留 3v3 UAV 对抗问题，但将核心科学问题升级为：

> **交互诱导分布偏移下的反事实响应效用推断（Counterfactual Response-Utility Inference under Interaction-Induced Shift, CIRU）**。

关键观察是：对手轨迹并非外生标签。我们观察到的对手行为由“对手策略 × 当前我方响应 × 状态历史”共同生成。若只在当前响应产生的历史上判断其他候选响应的价值，就会把响应诱导的行为差异误认为对手固有类型，并对未执行响应的效用作无支撑外推。

## 2. 新论文核心

### 暂定题目

**交互诱导偏移下的反事实响应效用学习：面向开放集多无人机团队对抗的无梯度适应**

英文暂名：

**Counterfactual Response-Utility Learning under Interaction-Induced Shift for Open-Set Multi-UAV Team Adaptation**

### 单句论题

开放集对手适应的关键不只是识别对手，而是估计“如果换用另一团队响应，后续交互与任务效用将如何变化”；显式建模这种响应条件化反事实可减少由当前策略诱导轨迹造成的选择偏差。

### 不作为创新的内容

- GRU/Transformer 行为编码器；
- opponent ID 或 embedding；
- 普通策略库与 argmax 选择；
- 不确定性估计本身；
- change detector 本身；
- UAV 对抗环境本身。

### 最多三项贡献

1. 形式化**交互诱导的响应效用偏移**：同一对手在不同我方响应下产生不同可观测轨迹，单一路径 opponent embedding 不足以识别未执行响应的价值。
2. 提出响应条件化的反事实效用模型，对冻结团队响应库估计效用分布，并以支持度/不确定性限制无梯度切换。
3. 构建行为混叠、响应专门化、未见学习型对手和回合内切换的 3v3 UAV 评价，使用 response regret、反事实排序误差和安全代价检验机制。

## 3. 最近邻压力测试

| 最近邻 | 已覆盖内容 | 对原 OSTA-v1 的威胁 | CIRU 必须保留的区别 |
|---|---|---:|---|
| DRON / agent modeling | 从局部历史学习对手表示并改善决策 | 高 | 不以表示或动作预测为终点，显式评价未执行响应的反事实效用 |
| GSCU | 未知、非平稳对手；embedding posterior；greedy/conservative 不确定性选择 | 极高 | 不把“不确定时保守”作为主创新，而处理响应改变观测分布所致的 counterfactual selection bias |
| HOP | 目标推断、goal-conditioned policy、MCTS best response | 高 | 冻结响应库和严格配对反事实效用；不依赖在线规划 |
| MBOM / OMIS | 模型推演或 decision-time search 适应未知对手 | 高 | 主要估计对象是响应条件化任务效用及其支持度，并隔离 factual 与 counterfactual 误差 |
| Bayesian policy reuse / Bayes-ToMoP | 策略信念、策略库复用、未知/切换策略检测 | 极高 | 不假定已知类型对应的性能模型可直接迁移；测试行为混叠且响应会改变证据生成过程 |
| active probing opponent model | 付费探测与类型推断 | 高 | 探测不是默认模块；核心是自然任务响应本身造成的干预与反事实外推问题 |
| OSOM | 开放集显式识别与响应 | 高 | 不要求生成开放集身份标签；评价 counterfactual utility calibration 与 response regret |

据此，论文不能再使用“首次处理开放集对手”或“首次无梯度适应”等表述。可争取的创新是**响应诱导轨迹与未执行响应价值之间的可识别性问题及其估计方法**。

## 4. 数学问题定义

设对手团队潜在策略为 `z`，我方冻结响应库为 `B={B_1,...,B_K}`。在响应 `B_a` 下观察历史

`h_t ~ p(h_t | z, B_a)`。

目标不是预测 `z`，而是估计所有候选响应的条件效用

`Q_k(h_t)=E[G_t | do(B_k), h_t]`。

当 `k != a` 时，`Q_k` 是未执行响应的反事实量。原 OSTA-v1 隐含地把 `p(h|z,B_a)` 当作只由 `z` 决定；CIRU 显式输入响应、建模响应条件化转移，并对低支持反事实给出不确定性界。选择规则为

`k* = argmax_k (mu_k(h_t) - beta * sigma_k(h_t))`，

其中该下置信界只是决策规则，不是创新本身；创新是否成立取决于 `mu_k, sigma_k` 对反事实响应的校准与可识别性。

## 5. 零训练存在性与可识别性门

以下全部通过前，禁止 G2 续跑、专家训练和方法训练。

### Z1 响应诱导性

固定同一对手和初始场景，使用至少两种合法我方响应 rollout；对手可观测行为分布必须随我方响应显著改变。若不改变，则“交互诱导偏移”在该环境不存在。

### Z2 行为混叠

构造或发现至少两种对手，在前缀历史上难以区分，但其最优响应不同。必须以预冻结距离/分类上界和 response-ranking disagreement 联合判定，不能凭轨迹图主观判断。

### Z3 响应专门化

4×4 或更充分的 cross-play 必须显示多个响应各有优势，且不存在单一响应对所有对手占优。

### Z4 反事实余量

相对于 population/static baseline，oracle response selector 在至少两个未见对手上具有预设最小余量；否则没有值得估计的反事实效用。

### Z5 可支持性

训练数据中的响应—对手覆盖必须足以估计 held-out 组合；报告 overlap/support，禁止让模型对完全无支持区域给出伪确定预测。

### Z6 任务可学习性

任务基线可学习、不饱和，并且 clean win、engagement、timeout、collision/boundary 分开报告。

## 6. 方法与消融在训练前的冻结要求

### 主方法组件

1. 团队集合/图历史编码；
2. 响应条件化动态或结果模型；
3. 多响应反事实效用头；
4. 支持度感知的不确定性；
5. 无梯度响应选择；
6. 仅在动态 R7 必要时启用变化检测。

### 决定性消融

| 变体 | 回答的问题 |
|---|---|
| history-only utility selector | 普通历史编码是否已足够？ |
| response-conditioned factual-only | 响应条件化本身是否足够？ |
| CIRU without counterfactual consistency | 反事实约束是否贡献？ |
| CIRU without support-aware uncertainty | 低支持回退是否贡献？ |
| oracle selector | 剩余可利用上限是多少？ |
| static/population policy | 适应是否必要？ |

若完整方法只与普通 GRU 接近，结论是机制未获支持，而不是继续添加模块。

## 7. 证据与统计合同

- 独立单位：训练种子；
- 所有方法使用同一响应库、场景 tape、对手集合和预算；
- 主端点：response regret、clean combat win、engagement return；
- 可靠性端点：worst seed、timeout、collision、boundary；
- 机制端点：factual/counterfactual utility error、response ranking、uncertainty coverage、support-stratified regret；
- 动态端点：切换检测延迟、切换后累计 regret；
- 已见、手工未见、独立学习未见和动态切换分层报告；
- 不把 episode 数当训练重复，不按结果选择对手或 seed。

## 8. 三位审稿人预审

### Reviewer 1（技术可靠性）

**总体判断：** 原 OSTA-v1 技术链完整但缺少独特的可识别估计对象；CIRU 将问题推进到可检验的反事实效用层面。

- Concern ID: R1-M1
- Axis: experimental-design
- Claim pointer: 未执行响应效用可由当前响应产生的历史估计。
- Evidence pointer: 本文第 4–5 节；本地 `research/P0_SCIENTIFIC_CONTRACT_V1.md` 尚未处理响应诱导分布。
- Concern and resolution test: 必须通过 Z1、Z2、Z5，并在交叉响应数据上验证 counterfactual calibration。

- Concern ID: R1-M2
- Axis: statistical-rigor
- Claim pointer: 方法改善开放集适应。
- Evidence pointer: 本文第 7 节。
- Concern and resolution test: 以训练 seed 为单位报告配对差和区间，不能用大量 episode 夸大样本量。

**建议姿态：** 零训练大修后再决定是否立项。

### Reviewer 2（新颖性与意义）

**总体判断：** OSTA-v1 与 GSCU、HOP、OMIS 高度重叠；CIRU 的新颖性取决于能否证明交互混杂真实存在且现有 selector 受其影响。

- Concern ID: R2-M1
- Axis: novelty-significance
- Claim pointer: 响应效用推断区别于既有 opponent adaptation。
- Evidence pointer: 本文第 3–5 节。
- Concern and resolution test: 提供最近邻逐模块矩阵，并用 history-only/GSCU-style baseline 证明差异不是换名。

- Concern ID: R2-M2
- Axis: mechanism-evidence
- Claim pointer: 反事实建模降低选择偏差。
- Evidence pointer: 本文第 4、6 节。
- Concern and resolution test: 必须按 factual/counterfactual、支持度和行为混叠程度分层展示误差与 regret。

**建议姿态：** 若 Z1–Z5 通过，具有强二区潜力；否则停止。

### Reviewer 3（可读性与影响）

**总体判断：** “对手行为会被我方策略改变，因此看到的行为不能直接代表换策略后的结果”是清晰且跨领域可理解的问题；UAV 只是验证载体，不能成为唯一价值来源。

- Concern ID: R3-M1
- Axis: interdisciplinary-readership
- Claim pointer: 方法解决一般开放集团队适应问题。
- Evidence pointer: 本文第 2、7 节。
- Concern and resolution test: 至少用多类未见对手和独立学习型 R8，避免只对手工脚本成立。

- Concern ID: R3-M2
- Axis: writing-clarity
- Claim pointer: counterfactual utility 与 opponent identity 的区别。
- Evidence pointer: 本文第 4 节。
- Concern and resolution test: 论文图 1 必须用同一对手、两种我方响应、两条不同未来轨迹直观说明。

**建议姿态：** 问题叙事优于原 OSTA，但尚未有存在性证据。

### Cross-review synthesis

共识优势是问题具有明确的决策后果、可形成独立机制指标，并能利用现有 3v3 UAV 环境。共识风险是原 OSTA 与已有工作过近，且 CIRU 的核心前提尚未由当前环境证明。最重要的下一步不是训练，而是实现只读/脚本策略的 Z1–Z2 解析审计，再用 cross-play 验证 Z3–Z4。

## 9. 当前状态与下一步

当前：

> `TRAINING_PROHIBITED`

唯一下一步是开发**零学习 Z1–Z2 审计器**：复用冻结环境与脚本对手，对同一初始场景执行多种合法脚本响应，量化 response-induced behavior shift、前缀行为混叠和最优响应排序分歧。该审计不训练网络、不消耗 GPU 大预算。

若 Z1 或 Z2 失败，CIRU 停止；若通过，再设计 Z3–Z4 专家 cross-play。G2 seed-2 续跑包继续保持未授权。

