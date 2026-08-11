# Q0-R2：多频率物理控制问题形式化与裁决

状态：`Q0_R2_NO_GO__MULTIRATE_PROBLEM_NOT_DISTINCT`

日期：2026-08-11

## 1. 候选数学对象

设基础物理时间步为 `δ`。agent `i` 的控制周期为 `Δ_i = m_i δ`，在其决策时刻 `t_k^i` 产生连续动作：

\[
a_i(t)=\pi_i(o_i(t_k^i)),\qquad t\in[t_k^i,t_k^i+\Delta_i).
\]

在动作保持区间内，环境仍以基础时间步演化，其他 agent 可继续更新。因此联合动力学在每个基础时间步使用当前各 agent 的保持动作：

\[
s_{t+1}=F(s_t, a_1(t),\ldots,a_n(t)).
\]

这确实表达了“异构 agent 的独立物理执行周期”，并且比简单同步 action-repeat 更明确地保留了联合动力学中的中间变化。

## 2. 与已有异步宏动作的等价性检查

但是，上述对象可以直接改写成异步 semi-MDP：对每个 agent，把持续 `m_i` 个基础步的保持控制视为一个 temporally extended macro-action；其他 agent 在该期间产生新的 macro-action 或 primitive action。此时奖励、折扣和终止时刻按实际经过的基础物理时间累计。

这不是纯粹的文字相似：

* ACAC 明确定义了“作为单次决策执行的动作序列”带来的异步，并针对 CTDE 的错位经验提出 agent-centric trajectory、集中式 critic 聚合和异步 GAE/PPO；[ACAC](https://proceedings.mlr.press/v267/jung25a.html)
* Xiao 等直接在 decentralized、centralized 与 CTDE 中处理 temporally extended macro-actions 的异步学习与策略梯度，并将其用于机器人任务。[Asynchronous MARL under partial observability](https://journals.sagepub.com/doi/abs/10.1177/02783649241306124)

因此，“慢 agent 保持上一次连续控制，而快 agent 在中间继续改变状态”不能单独构成与宏动作异步方法不同的数学问题。它是宏动作/半 MDP 表达的一种物理实例。

## 3. temporal-credit mismatch 的可检验形式

候选机制原本是：同步 MAPPO 在基础时间轴逐步计算 GAE，而 agent 的动作影响区间不同，导致 policy-gradient credit horizon 与物理控制 horizon 不匹配。

这个现象可以成立，但它本身不是新的算法缺口：只要把每个 agent 的有效 action duration 纳入异步轨迹、折扣累计和 advantage/GAE 计算，就落入已有异步宏动作 return estimation 的处理范围。若仍把保持期间的每个物理步都当作独立同频 transition，确实会产生错误或高方差的估计；但这更像一个 baseline 实现错误/应用适配问题，而不是已经证明独立于异步 MARL 的新学习问题。

## 4. Q0-R2 裁决

当前无法同时满足以下三项：

1. agent-specific physical control period 与 macro-action/semi-MDP 在数学上不等价；
2. 现有异步 return/GAE 方法不能直接覆盖该对象；
3. 所谓 cross-rate temporal credit 能形成独立于已有异步 MARL 的方法缺口。

因此裁决为：

> `Q0_R2_NO_GO__MULTIRATE_PROBLEM_NOT_DISTINCT`

不进入 Q1 benchmark 训练，不实现 frequency-consistent advantage，也不在 UAV 平台上继续变体化定义。

## 5. 项目后续边界

当前候选“多频率 MARL”关闭，但不能据此否定所有新算法方向。若继续做新算法，必须从第二候选重新进行问题选择，而不是把 action-repeat、macro-action、异步调度重新命名为 multi-rate credit assignment。

