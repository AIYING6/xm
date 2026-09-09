# P3 新颖性邻近工作差异矩阵

## 审查结论

原始表述“信息集方法根据 ACK 决定等待或承诺”不能作为强创新点。已有工作已经覆盖延迟感知
等待、common belief、common knowledge、inconsistent beliefs、action consistency、belief-space
planning 和 value of information。P3 只有升级为可校准、风险约束、模型自由的认知承诺学习
框架，才保留进一步验证的价值。

更新后的结论是 `NOVELTY_COLLISION_STOP`，不是 `NOVELTY_PASS`。2026-09-10 的扩展检索发现
SafeCommit（arXiv:2608.04289）已经公开“校准潜在世界集合—对集合中所有世界执行安全承诺
证书—证书失败时探测或回退”的同构决策结构。应用对象不同不足以支撑强二区方法创新，因此
当前 CEC-MAPPO 定义不得直接进入实现或训练。

## 差异矩阵

| 邻近工作 | 已解决的问题 | 与 P3 的重叠 | P3 必须提供的不可替代差异 |
|---|---|---|---|
| DACOM (2022) | 学习消息等待时间，权衡通信收益与动作延迟 | `defer` 等待机制高度重叠 | 不以等待时间为创新；显式估计计划一致性集合并约束错误承诺风险 |
| MACKRL (2019) | 基于 common/probabilistic common knowledge 的分层协调 | 共同知识驱动协调高度重叠 | 研究不可靠 ACK 下尚未成为共同知识的计划，并输出可校准集合与承诺决策 |
| CBMA (2022) | 用变分循环模型推断 common belief | 显式/隐式共同信念重叠 | 不只学习 latent belief；报告覆盖率、集合宽度和错误承诺风险 |
| MR-BSP Action Consistency (IROS 2024) | 不一致信念下的多机器人 belief-space planning 与通信触发 | 问题设定和 action consistency 高度重叠 | 从已知模型规划转向 CTDE/MAPPO 的模型自由闭环学习，并隔离表示与门控机制 |
| Dec-POMDP Action Consistency (2025 preprint) | 不一致信念下的联合动作一致性和性能概率保证 | 与“信念不一致导致危险动作”几乎正面重叠 | 不宣称首次处理不一致信念；贡献必须是可校准学习近似、期权价值和物理 UAV 任务证据 |
| Belief Representation RL (ICML 2023) | 从训练期状态学习任务相关 belief representation | 训练期辅助真值和显式 belief 重叠 | 集合输出必须具有独立校准覆盖，而非仅作为 latent feature |
| VoI POMDP planning (NeurIPS 2020) | 用信息价值组织 belief-dependent macro-action | 等待信息的期权价值重叠 | VoI 不是创新；创新候选是其与去中心化一致性集合、风险门和 MAPPO 的联合实现 |
| Bayesian ambiguity-set robust MDP (NeurIPS 2019) | ambiguity set 下的稳健决策 | support-wise downside 约束重叠 | 不声称发明 ambiguity set；证明其用于错误联合承诺而非一般转移不确定性 |
| SafeCommit (2026 preprint) | 从校准潜在世界集合构造全支持承诺证书，失败时探测或回退 | 与 CEC-MAPPO 的“集合—承诺—探测/回退”核心结构近乎同构 | 仅换成 UAV/MAPPO 不构成充分方法差异；当前创新核失效 |

## 暂定创新核

以下是已被冻结但被最近邻工作击穿的候选定义，不再视为可投稿创新核：

1. 从各智能体合法通信历史估计计划一致性 posterior，并通过独立 calibration split 输出具有
   冻结覆盖目标的 agreement set；
2. 将 `commit` 的支持集下行风险约束与 `defer/fallback` 的 posterior expected option value
   联合起来，避免把 pure maximin 退化为永久 fallback；
3. 在完全配对的 MAPPO 四格实验中，分别识别 calibrated set representation 与 commitment
   gate 的增量作用。

SafeCommit 已同时覆盖其中最关键的第一、二项，并给出概率风险界。第三项四格消融只是识别
工程组件贡献，不能恢复方法新颖性。因此 P3 按预先约定停止：保留 Q0/Q0B 任务资产和实验
设计知识，但不实现、不训练当前 CEC-MAPPO。若重开，只能提出与 SafeCommit 在优化对象、
信息获取方式或多智能体耦合结构上可形式化区分的新机制，并重新执行本审计。

## 关键来源

- DACOM：<https://arxiv.org/abs/2212.01619>
- MACKRL：<https://arxiv.org/abs/1810.11702>
- CBMA：<https://doi.org/10.1016/j.neucom.2022.09.144>
- Multi-Robot Communication-Aware Cooperative Belief Space Planning with Inconsistent Beliefs：
  <https://arxiv.org/abs/2403.05962>
- Towards Optimal Performance and Action Consistency Guarantees in Dec-POMDPs with Inconsistent
  Beliefs and Limited Communication：<https://arxiv.org/abs/2512.20778>
- Learning Belief Representations for Partially Observable Deep RL：
  <https://openreview.net/pdf?id=4IzEmHLono>
- Belief-Dependent Macro-Action Discovery using the Value of Information：
  <https://proceedings.neurips.cc/paper/2020/hash/7f2be1b45d278ac18804b79207a24c53-Abstract.html>
- Beyond Confidence Regions: Tight Bayesian Ambiguity Sets for Robust MDPs：
  <https://proceedings.neurips.cc/paper/2019/hash/b994697479c5716eda77e8e9713e5f0f-Abstract.html>
- SafeCommit: Certifying When Memory-Grounded Agents May Safely Act：
  <https://arxiv.org/abs/2608.04289>
