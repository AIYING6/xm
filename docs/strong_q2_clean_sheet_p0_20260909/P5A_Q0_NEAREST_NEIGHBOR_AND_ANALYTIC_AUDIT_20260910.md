# P5-A-Q0：团队可避免损害的最近邻与解析非退化审查

## 结论

`P5A_CONDITIONAL_SURVIVAL_IDENTIFIABILITY_OPEN`

P5-A 没有因直接重复已有论文而立即淘汰，最小解析对象也不是普通共享成本的同义改写；但它尚未
获得方法实现或训练资格。决定性风险已经从“有没有这个问题”转为“反事实参考与成员责任能否在
部分可观测序列决策中被合法识别和稳定估计”。

## 最近邻差异矩阵

| 最近邻 | 已解决的问题 | 与 P5-A 的重合 | 尚未覆盖的严格剩余空间 | 风险 |
|---|---|---|---|---|
| Do No Harm（L4DC 2024） | 相对默认安全策略定义反事实损害，只惩罚策略造成的额外违规 | “不可避免 vs 可避免损害”完全重合 | 原文实验为单智能体；没有异构成员间责任分解或分散执行学习 | 高：P5-A 不能宣称发明反事实损害 |
| Counterfactual Effect Decomposition（ICML 2025） | 在多智能体序列决策中分解动作经不同代理传播的反事实效应，并用 Shapley 归因 | 多智能体反事实效应、责任和 Shapley 高度重合 | 目标是解释反事实结果，并非针对不可避免安全损害的约束策略学习 | 很高：P5-A 不能宣称发明多智能体反事实责任 |
| COMA / Difference Rewards / DAE | 用反事实基线分配团队奖励信用，改善策略梯度 | 成员边际贡献及反事实替换重合 | 关注回报信用和方差，不区分不可避免安全成本，也不定义损害基线 | 高：责任优势不能只是 difference cost 改名 |
| Safe MARL / MAPPO-Lagrangian | 在约束 Markov 博弈中优化团队回报并控制成本 | 安全约束与策略优化重合 | 通常直接约束累计成本，不分离外生不可避免部分和成员责任 | 中高：优化器本身不能作为贡献 |
| 博弈论责任分配（IJCAI 2021） | 在不完全信息扩展式博弈中定义前向、后向、战略与因果责任 | 责任公理和多人归因重合 | 未提供面向连续协作控制的可训练安全策略目标 | 高：必须说明采用/修改哪种责任概念 |

因此，唯一可能成立的创新交集是：

> 在部分可观测协作控制中，将相对合法默认策略的“可避免安全损害”与序列化成员责任分解共同
> 转化为可估计的约束优势，并在不泄漏执行期真值的条件下用于策略学习。

这是一个组合式候选差异，不是已经成立的新颖性结论。若最终方法只是把 Do No Harm 的成本替换
成 Shapley/difference reward 后送进 MAPPO-Lagrangian，则创新不足，必须停止。

## 解析博弈

审计脚本枚举两个智能体、二元动作和二元外生危险，共三个成本结构、24 个情形：

1. `joint_causation`：只有两名成员同时采取危险动作才产生额外损害；
2. `agent0_only`：只有成员 0 的动作能造成额外损害，成员 1 是空参与者；
3. `no_avoidable_harm`：策略动作不会造成额外损害。

团队成本为 `C(a,u)`，合法默认联合动作为 `a0=(0,0)`，可避免损害定义为：

`H(a,u) = [C(a,u) - C(a0,u)]_+`。

对成员责任使用精确枚举的二人 Shapley 边际贡献。审计通过以下四项：

- 当外生危险使成本不可避免时，团队成本为 1，而可避免损害和全部成员责任均为 0；
- 当损害需要两名成员共同造成时，两人责任各为 0.5；
- 当成员 1 对损害无边际影响时，其责任为 0；
- 所有 24 个情形中，责任之和严格等于可避免损害。

这证明共享团队成本、可避免损害和成员责任是三个可区分对象。它不证明反事实量能从轨迹中辨识，
也不证明将其用于训练会改善安全或任务表现。

## Q0 门状态

| 门 | 状态 | 说明 |
|---|---|---|
| 最近邻初筛 | 条件通过 | 未发现“不可避免损害 + 多智能体责任 + 约束策略学习”的完全同构工作，但两个组成部分均有强近邻 |
| 数学非退化 | 通过 | 解析枚举区分共享成本、可避免损害和空参与者责任 |
| 责任公理 | 初步通过 | 效率与空参与者通过；对称性、时间一致性尚未定义 |
| 反事实可辨识性 | **未通过** | 尚未明确共享外生噪声、默认策略和模型误差条件 |
| 执行信息边界 | 未通过 | 尚未区分训练期反事实计算与部署期输入 |
| 可学习任务 | 未开始 | 禁止据当前环境推定可用 |
| 因子消融 | 概念通过 | 已有四格对照，但尚未证明优化目标与参数量可匹配 |

## 下一步：P5-A-Q1（仍然零训练）

只允许完成以下工作：

1. 定义结构因果 Markov 博弈中的外生变量共享规则；
2. 比较“默认联合策略”“逐成员默认动作”和“可行安全参考策略”三种反事实基线；
3. 给出有限时域团队损害与成员责任的时间一致定义；
4. 分别写明模型已知、可重置模拟器和纯观察数据三种条件下的可辨识边界；
5. 构造至少一个反例，证明错误反事实基线会把不可避免损害误归因给成员；
6. 若定义成立，再设计一个与 UAV 无关的最小任务；不得先接入现有 UAV 环境。

P5-A-Q1 通过前，仍禁止实现学习器、调参和训练。

## 文献锚点

- Vaskov et al., *Do No Harm*, L4DC 2024:
  <https://proceedings.mlr.press/v242/vaskov24a.html>
- Triantafyllou et al., *Counterfactual Effect Decomposition in Multi-Agent Sequential Decision
  Making*, ICML 2025: <https://proceedings.mlr.press/v267/triantafyllou25a.html>
- Li et al., *Difference Advantage Estimation for Multi-Agent Policy Gradients*, ICML 2022:
  <https://proceedings.mlr.press/v162/li22w.html>
- Castellini et al., *Difference Rewards Policy Gradients*, AAMAS 2021:
  <https://arxiv.org/abs/2012.11258>
- Ding et al., *Provably Efficient Generalized Lagrangian Policy Optimization for Safe MARL*,
  L4DC 2023: <https://proceedings.mlr.press/v211/ding23a.html>
- Baier et al., *A Game-Theoretic Account of Responsibility Allocation*, IJCAI 2021:
  <https://doi.org/10.24963/ijcai.2021/244>

