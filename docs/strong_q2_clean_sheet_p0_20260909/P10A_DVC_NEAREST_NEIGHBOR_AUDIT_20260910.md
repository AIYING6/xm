# P10-A 决策有效性包络最近邻审查

**判定：** `DVE_NEAREST_NEIGHBOR_CONDITIONAL_PASS`  
**名称修订：** DVC-MARL 暂改为 DVE-MARL（Decision-Validity-Envelope MARL），避免与形式化多智能体 contract shielding 混淆。  
**训练：** 未授权。

## 1. 检索问题

本轮检索不以“论文是否提到 delay”为判据，而检查是否已有工作同时包含以下四项：

1. 物理系统在策略推理期间持续演化；
2. 策略为候选动作给出动作特定的状态—时间有效域；
3. 计算完成时根据当前合法状态执行 accept/reject/fallback；
4. 多智能体异步完成导致的联合动作兼容性进入学习与评价。

只有四项同时同构才构成直接阻断；单独覆盖时延、异步动作或安全过滤属于必须比较的近邻。

## 2. 最近邻矩阵

| 最近邻 | 主要对象 | 与 DVE 重合 | 未覆盖的 DVE 对象 | 影响 |
|---|---|---|---|---|
| Xiao et al., *Asynchronous Actor-Critic for MARL* | 不同时长 macro-action 的异步策略梯度 | 多智能体异步决策 | 不以推理完成后的旧决策有效性为对象；无动作特定有效域 | 强基线，不阻断 |
| Yu et al., AAMAS 2023, ACE | 异步多机器人探索与 action-delay randomization | 真实异步执行、延迟随机化 | 不输出或校准状态—时间有效域；没有 accept/fallback 机制 | 最强应用近邻，不阻断 |
| Thodoroff et al., *Benchmarking Real-Time RL* | 环境在推理期间演化的实时 RL 问题 | 直接覆盖 observation–computation–actuation mismatch | 是问题/benchmark 提案，不含多智能体动作有效域学习 | 奠基近邻，限制“首次提出实时 RL”表述 |
| *Learning to Act While Waiting*, 2026 | VLA 推理时延下异步执行，中途观测恢复近 Markov 性 | 推理期间继续行动、stale observation | 通过状态增强生成动作，不学习动作有效域或运行时拒绝包络 | 非常强近邻，必须实验比较其思想 |
| ActFovea, 2026 | 用视觉—动作时空一致性做 VLA runtime safeguard | 检测 stale/replayed observation，恢复或 safe failure | 冻结 VLA 的外部检测器；非多智能体，不学习每个动作的状态—时间包络 | 强近邻，限制 safeguard 主张 |
| Delay-aware MARL for CACC | 把时延纳入 MADA-MDP，并结合模型过滤 | 时延建模、稳定控制 | 不以推理所得动作在完成时是否仍有效为学习对象 | 主要 delay-aware 对照 |
| Contract-Based Compositional Shielding for Safe MARL, 2026 | LTL-safe assume–guarantee contract 与分散 shield | 团队动作兼容、fallback/过滤语义 | 合同是安全规范，不是旧快照动作的时变有效包络 | 术语冲突明显，故改名 DVE |
| 传统 runtime assurance / learned safe sets | 当前状态下的安全集合和备份控制器 | accept/reject 与 fallback | 通常不处理动作生成快照、随机推理完成时刻和团队任务兼容 | 必须作为安全基线 |

## 3. 条件通过的理由

截至本轮检索，四项联合对象尚未发现直接同构的同行评议或预印本方法。DVE 的潜在独立性不来自“延迟”“异步”“shield”或“UAV”，而来自下列闭环：

\[
\text{snapshot-conditioned action}
\rightarrow
\text{action-specific validity envelope}
\rightarrow
\text{completion-time admission}
\rightarrow
\text{team-compatible fallback}.
\]

这个判断只能称为条件通过，而不是新颖性证明。原因是 2026 年 ActFovea 和 ARLI 已经非常接近“时空失配 + 运行时恢复”，形式化 contract shielding 又覆盖团队兼容安全。如果 DVE 不能在数学对象和受控实验中同时区别三者，创新上限会快速下降。

## 4. 必须立即收紧的定义

### 4.1 不再使用 contract 作为主名称

“Contract”容易与社会契约 MARL、assume–guarantee contract 和 LTL contract shielding 混淆。主对象改为 **decision-validity envelope（决策有效性包络）**。

### 4.2 有效性不能等同于安全性

有效动作应同时满足：

- 在当前状态可执行且不违反硬约束；
- 对其原始团队战术意图仍有足够任务价值；
- 与其他尚在执行或刚完成的队友动作兼容。

只预测碰撞风险会退化为 learned shield；只预测任务价值会退化为 delay-aware critic。

### 4.3 包络必须是动作特定的

同一状态变化对不同动作影响不同。若模型只输出一个全局 stale score 或固定 TTL，则不能形成核心创新。

## 5. P10-B 解析门冻结要求

下一步只允许建立可枚举解析环境和 oracle，不训练神经网络。必须同时通过：

1. **同延迟异有效性：** 相同推理时延下，两个完成状态对同一旧动作分别有效和无效；固定 TTL 无法区分。
2. **同安全异任务价值：** 两个动作都安全，但其中一个因状态演化失去任务价值；纯 safety shield 无法区分。
3. **个体有效但联合无效：** 每个动作单独安全且有价值，异步组合后违反团队兼容条件；单智能体 admission 无法区分。
4. **非平凡回退：** always-fallback 严格次优，always-accept 存在严格损失。
5. **无未来泄漏：** admission 只使用完成时刻可得的本地状态、动作元数据和合法队友承诺摘要。

若 DVE 不能严格优于 fixed TTL、delay-aware action、current-state shield 中至少两类，题目关闭。

## 6. 允许的论文主张上限

若后续门全部通过，可主张：

> 本文研究随机推理时延下旧快照决策的动作特定有效性，并提出在多智能体异步执行中联合学习有效性包络与任务兼容回退的方法。

当前禁止主张：首次研究实时 RL、首次处理时延、提供确定性安全保证、适用于任意无人机平台或优于所有异步 MARL。

## 7. 结论

P10-A 有条件通过。DVE 是目前第一个没有在最近邻门立即被直接同构工作击穿的候选，但其创新空间较窄，下一步必须由解析反例证明它不是 delay-aware policy、ActFovea 式 safeguard 或 contract shield 的组合包装。

