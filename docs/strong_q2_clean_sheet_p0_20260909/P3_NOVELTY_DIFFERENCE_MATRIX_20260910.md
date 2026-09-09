# P3 新颖性邻近工作差异矩阵

## 审查结论

原始表述“信息集方法根据 ACK 决定等待或承诺”不能作为强创新点。已有工作已经覆盖延迟感知
等待、common belief、common knowledge、inconsistent beliefs、action consistency、belief-space
planning 和 value of information。P3 只有升级为可校准、风险约束、模型自由的认知承诺学习
框架，才保留进一步验证的价值。

当前结论是 `CONDITIONAL_NOVELTY_CANDIDATE`，不是 `NOVELTY_PASS`。本轮完成最邻近方向检索，
但尚需导出式 CrossRef/arXiv/Scopus 检索、去重和逐篇全文核对。

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

## 暂定创新核

候选方法更名为 **CEC-MAPPO（Calibrated Epistemic-Commitment MAPPO）**。其可检验创新核为：

1. 从各智能体合法通信历史估计计划一致性 posterior，并通过独立 calibration split 输出具有
   冻结覆盖目标的 agreement set；
2. 将 `commit` 的支持集下行风险约束与 `defer/fallback` 的 posterior expected option value
   联合起来，避免把 pure maximin 退化为永久 fallback；
3. 在完全配对的 MAPPO 四格实验中，分别识别 calibrated set representation 与 commitment
   gate 的增量作用。

若后续全文检索发现已有工作同时具备以上三项，则 P3 必须停止或再次重构，不能靠 UAV 应用
场景包装为方法创新。

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
