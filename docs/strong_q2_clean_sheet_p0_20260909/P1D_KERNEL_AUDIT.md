# P1D：信息集承诺决策核零训练审计

## 结论

`P1D_COMMITMENT_KERNEL_AUDIT_PASS`

候选决策核及容量匹配 recurrent 对照通过孤立实现审计。该结论仅允许进入可训练任务接口设计，仍不授权性能训练或云端打包。

## 通过项

1. 候选 actor 的前向接口只有 `local_history` 和 recurrent `hidden`，不接收真实 delivery、ack、global state、share observation 或队友 belief。
2. 对相同发送方合法历史，潜在送达状态改变不会改变候选 actor 的任何输出。
3. 概率区间始终有序并限制在 `[0,1]`。
4. 在 P1B 冻结反例上，低、中、高兼容承诺概率区间分别选择 fallback、defer、commit。
5. 候选与直接 recurrent 对照均为 7,971 个参数，参数量完全相同。
6. recurrent 对照的 8 维模式头全部通过固定稠密投影参与任务模式决策，不存在只用于凑参数但不参与梯度的空闲 head。
7. 候选的部署模式由信息区间上的最坏情况价值计算决定，不是辅助分类损失或事后诊断。

## 实现结构

候选与对照共享相同 GRU 历史编码器和物理动作 head。差异只位于任务模式决策：

- 候选：局部历史 → 兼容承诺概率区间 + 三种模式的两端价值 → 区间内稳健选择；
- 对照：局部历史 → 等容量直接模式 logits → `argmax`。

两者均不通过通信恢复隐藏信息。

## 当前不能宣称的内容

- 区间估计已经校准；
- 候选方法能够由 PPO 稳定学习；
- 候选优于 recurrent MAPPO；
- 该决策核相对最近邻具有足够论文创新性；
- 影子环境中的任务价值可直接代表现实部署代价。

## 下一门

下一步应构造最小可训练接口并在零训练状态下完成：奖励与端点可还原性、常数策略非支配、随机/脚本覆盖、无真值泄漏、固定 tape 和 seed 注册。全部通过后才能讨论 P2 小试验。

## 可追溯文件

- 决策核：`algorithms/epistemic_commitment.py`
- 审计：`scripts/audit_epistemic_commitment_p1d_kernel.py`
- 测试：`tests/test_epistemic_commitment_p1d_kernel.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P1D_KERNEL_AUDIT_RESULT.json`
