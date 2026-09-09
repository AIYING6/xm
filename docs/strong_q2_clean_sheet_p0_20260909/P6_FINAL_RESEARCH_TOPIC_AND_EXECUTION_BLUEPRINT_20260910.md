# P6 最终研究选题与执行蓝图

日期：2026-09-10  
状态：`FINAL_TOPIC_SELECTED / ZERO_TRAINING_FOUNDATION_STAGE`

## 最终选题

**交互诱导偏移下的反事实响应效用学习：面向开放集多无人机团队对抗的无梯度适应**

英文工作题目：

**Counterfactual Response-Utility Learning under Interaction-Induced Shift for Open-Set Multi-UAV Team Adaptation**

自本文件生效起停止继续横向寻找选题。后续允许根据证据调整方法实现和论文标题，但不得退化回普通 opponent embedding、分类、策略库检索或“不确定时保守”的旧范式。

## 科学问题

开放集对手适应通常根据当前交互历史识别或表示对手，再生成响应。然而，历史不是对手策略的外生样本：对手在当前我方响应下采取的行为，与换用另一响应时可能不同。因此，从 `B_a` 诱导的历史直接估计 `B_k` 的价值面临反事实支持与交互混杂问题。

本文研究：

> 能否从有限、响应条件化的团队交互数据中估计未执行响应的任务效用与可信度，从而在开放集或策略切换对手下减少相对 oracle 的响应遗憾，而无需测试时梯度更新？

## 唯一核心创新

将 opponent adaptation 从“识别对手后选策略”改写为：

> **估计响应干预 `do(B_k)` 下的反事实团队效用，并用支持度感知的不确定性约束响应切换。**

编码器、策略库、置信下界和切换检测都不是独立创新；它们只服务于上述估计问题。

## 最接近工作与不可替代差异

- GSCU 已覆盖未知/非平稳对手、embedding posterior 和不确定时保守响应；本文不能以这些为新颖性。
- HOP、MBOM、OMIS 已覆盖目标推断、模型推演或决策时搜索；本文不能泛称首次推断未知对手的最佳响应。
- Bayesian policy reuse 与 Bayes-ToMoP 已覆盖策略库复用和切换检测；本文不能以“响应库选择”为贡献。
- Policy-conditioned beliefs 已考虑对手可能依赖我方策略；本文必须进一步给出可执行的反事实效用估计、支持度审计和 UAV 团队验证。

本文的最低创新成立条件是：普通 history-only/GSCU-style selector 在低支持、响应诱导偏移条件下出现系统性反事实排序误差，而 CIRU 在相同响应库和数据预算下显著降低该误差及 response regret。

## 方法冻结

设冻结蓝方团队响应库为 `B={B_1,...,B_K}`，对手策略为 `z`，当前执行响应为 `B_a`，合法可观测历史为 `h_t`。

目标量：

`Q_k(h_t)=E[G_t | do(B_k), h_t]`。

方法由四个必要部分构成：

1. **Permutation-aware team history encoder**：编码可变实体顺序下的双方可观测交互；
2. **Response-conditioned transition/outcome model**：显式输入候选响应，预测响应改变后的状态或任务结果；
3. **Counterfactual utility head**：输出每个候选响应的效用分布，而非 opponent ID；
4. **Support-aware selector**：根据数据支持度和校准不确定性选择响应或回退到 population policy。

动态对手的变化检测仅在静态版通过后加入，不提前堆叠。

## 研究问题

- RQ1：我方响应是否显著改变可观察的对手行为分布？
- RQ2：history-only 模型是否在未执行响应上产生反事实排序偏差？
- RQ3：CIRU 是否降低未见对手上的 response regret？
- RQ4：支持度感知不确定性是否改善低支持组合与最差 seed？
- RQ5：在回合内对手切换时，是否能减少恢复延迟和累计遗憾？
- RQ6：方法收益是否独立于网络容量、额外信息和训练预算？

## 决定性实验矩阵

| 证据 | 对照 | 回答的主张 |
|---|---|---|
| 同对手、同场景、多蓝方响应的交叉 rollout | 响应不变 | RQ1：响应诱导偏移存在 |
| factual/counterfactual 切分 | history-only vs response-conditioned | RQ2：普通 opponent embedding 不足 |
| 已见/未见/独立学习对手 | population、static mixture、GSCU-style、oracle、CIRU | RQ3：开放集效用 |
| 支持度分层 | CIRU w/ vs w/o support-aware uncertainty | RQ4：可信选择 |
| R7 策略切换 | w/ vs w/o change detector | RQ5：动态适应 |
| 等参数/等预算复核 | 容量匹配 GRU/Transformer | RQ6：排除容量解释 |

## 强制消融

1. history-only direct utility；
2. response-conditioned factual-only；
3. 去除 counterfactual consistency；
4. 去除 support-aware uncertainty；
5. full CIRU；
6. oracle selector 与 population policy 作为上下界。

不增加与核心机制无关的模块消融。

## 指标与统计

- 独立统计单位：训练种子；
- 主要决策指标：response regret；
- 任务指标：clean combat win、engagement return；
- 可靠性指标：worst seed、timeout、collision、boundary；
- 机制指标：counterfactual utility MAE、response ranking accuracy、calibration、coverage-risk、support-stratified regret；
- 动态指标：switch detection delay、recovery time、post-switch cumulative regret；
- 报告 seed 级配对差、均值/中位数、区间和 lower tail；episode 不作为独立重复。

## 执行阶段与停止条件

### Stage 0：零训练地基

- Z1 响应诱导偏移；
- Z2 行为混叠且最佳响应分歧；
- Z3 响应专门化的解析/脚本可行性；
- 最近邻与 claim matrix 冻结。

任一核心前提不存在：停止，不改阈值救题。

### Stage 1：低成本存在性实验

- 基线可学习性；
- B1–B4 专家 cross-play；
- held-out oracle headroom；
- response-condition coverage。

没有专门化或 oracle 余量：停止，不开发 CIRU。

### Stage 2：最小机制试验

- history-only；
- response-conditioned factual-only；
- CIRU prototype；
- 少量冻结种子和短预算，只判断机制差异。

若 CIRU 与容量匹配 GRU 的反事实误差和 regret 接近：停止，不扩大训练。

### Stage 3：正式实验

仅在 Stage 0–2 全部通过后，冻结正式种子、预算、对手划分和评价 tape，开展多 seed 主实验、消融、动态切换与运行开销测量。

### Stage 4：论文

按“交互诱导偏移 → 反事实估计缺口 → CIRU → 机制证据 → 开放集任务收益”组织论文，不写成 UAV 工程实验报告。

## 质量判断

该选题的创新上限高于 DRTP，也高于原 OSTA-v1。它不保证最终达到强二区；强二区资格取决于三项硬证据：

1. 交互诱导偏移与行为混叠真实存在；
2. 反事实建模相对强 history-only/GSCU-style 基线具有独立增益；
3. 增益在手工未见和独立学习未见对手上均转化为较低 response regret，而非只在定制脚本上成立。

当前决定是**正式选题，尚未授权训练**。下一步只执行 Stage 0 的零训练审计。

