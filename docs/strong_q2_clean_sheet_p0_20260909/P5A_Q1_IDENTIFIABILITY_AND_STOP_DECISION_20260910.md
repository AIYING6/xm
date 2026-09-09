# P5-A-Q1：反事实可辨识性审查与停止决定

## 最终决定

`P5A_STOP_NOVELTY_AND_IDENTIFIABILITY_RISK`

P5-A 不进入方法实现和训练。停止原因不是预计效果不好，而是截至 2026-09-10，候选的核心组成
已经被相邻文献分别乃至组合覆盖，而剩余差异依赖强结构因果假设和人为基线选择，难以支撑一条
以强二区为目标、机制可清晰识别的新主线。

## 1. Q1 新增的直接碰撞

Q0 已确认以下近邻：

- *Do No Harm* 已定义相对默认安全策略的反事实损害；
- *Counterfactual Effect Decomposition* 已在多智能体序列决策中分解反事实效应并使用 Shapley
  归因；
- COMA、Difference Rewards 和 DAE 已使用反事实基线处理成员信用；
- Safe MARL 已提供约束策略优化框架。

Q1 检索又发现：

- 2026 年 CCPO 已通过反事实轨迹估计成员边际贡献，并直接形成 agent-specific learning signal
  用于策略优化；
- 2026 年 CAPO 已把序列团队的反事实信用推到闭式成员优势与策略优化；
- 2026 年概率多智能体系统工作已用 Shapley 定义反事实责任，并研究责任—回报权衡下的稳定策略。

因此，“反事实轨迹 + 成员边际责任 + 策略优化”也不能作为 P5-A 的独立创新核。剩余的“把
不可避免损害接到这一链条”更接近组合扩展，而不是一个足够独立的新问题与新机制。

## 2. 基线选择反例

考虑两个成员，实际联合动作固定为 `(1,1)`，仅当两人都取 1 时团队成本为 1。采用精确 Shapley
边际责任，但改变同样合法的默认联合动作：

| 默认动作 | 成员 0 责任 | 成员 1 责任 |
|---|---:|---:|
| `(0,0)` | 0.5 | 0.5 |
| `(1,0)` | 0.0 | 1.0 |
| `(0,1)` | 1.0 | 0.0 |

同一事实轨迹得到完全不同的责任分配。责任不是轨迹的内禀属性；它取决于默认策略这一规范性和
工程性选择。除非能从任务约束唯一推出参考策略，否则方法结果可能被审稿人解释为“换一个基线
即可换一个责任答案”。

## 3. 可辨识性反例

令动作 `A`、结果 `Y` 和未观测噪声 `U` 均为二元变量，`U` 等概率。比较两个 SCM：

- `M1: Y = A XOR U`；
- `M2: Y = U`。

对任意干预 `do(A=0)` 或 `do(A=1)`，两模型都有 `P(Y=1)=0.5`，所以完整干预分布相同；但在
共享同一个体噪声的反事实比较中，改变动作在 M1 中会改变结果，在 M2 中不会。由此可见，即使
知道转移分布，也不能自动识别个体轨迹上的反事实责任；必须额外冻结 SCM 的噪声耦合结构。

在可重置模拟器中可以人为复用随机 tape，但这只使“该模拟器 SCM 下的反事实”可计算，不能把
它提升为不依赖建模选择的责任事实。

## 4. 门控结果

| Q1 门 | 结果 |
|---|---|
| 默认策略唯一性 | 失败：多个合法基线产生不同责任 |
| 观察/干预数据可辨识性 | 失败：相同干预分布对应不同个体反事实 |
| 模拟器内可计算性 | 条件通过：已知 SCM 且共享随机 tape 时可计算 |
| 时间责任独立性 | 未解决：把成员—时间对作为参与者会指数增长并与 ICML 2025 高度重合 |
| 强二区新颖性 | 失败：剩余方案是多个强近邻的组合式扩展 |
| 训练资格 | **不通过** |

## 5. 对 P5 的影响

P5-A 的停止证明开放选题门发挥了作用：在任何学习器实现和算力投入前，已经发现创新核重合及
可辨识性问题。不得通过改名为“责任感知 MAPPO”、换一种 Shapley 近似或加入 UAV 场景重启。

下一步转入 P5-B-Q0，但候选 B 必须保持开放定义：研究对象是外生扰动前的**任务延拓选择空间**，
不是通信连通性、拓扑恢复或 DRTP 暴露分配。若其与 viability kernel、contingency planning、
option preservation 或 resilience control 无法形成严格差异，同样停止。

## 6. 文献锚点

- Vaskov et al., *Do No Harm*, L4DC 2024:
  <https://proceedings.mlr.press/v242/vaskov24a.html>
- Triantafyllou et al., *Counterfactual Effect Decomposition in Multi-Agent Sequential Decision
  Making*, ICML 2025: <https://proceedings.mlr.press/v267/triantafyllou25a.html>
- Oberst and Sontag, *Counterfactual Off-Policy Evaluation with Gumbel-Max SCMs*, ICML 2019:
  <https://proceedings.mlr.press/v97/oberst19a.html>
- Li et al., *Counterfactual Credit Policy Optimization for Multi-Agent Collaboration*, 2026:
  <https://arxiv.org/abs/2603.21563>
- Deshmukh et al., *CAPO: Counterfactual Credit Assignment in Sequential Cooperative Teams*,
  2026: <https://arxiv.org/abs/2604.17693>
- Mu and Najib, *Counterfactual Reasoning for Causal Responsibility Attribution in Probabilistic
  Multi-Agent Systems*, 2026: <https://arxiv.org/abs/2605.13077>

