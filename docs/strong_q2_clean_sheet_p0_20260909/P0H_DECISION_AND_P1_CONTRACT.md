# P0H 决策与 P1 合同

## 直接结论

本轮没有发现可以立即训练的“低成本强创新”方向。三个候选中，仅**不可靠通信下的认知一致性任务承诺**具有足够清晰的新决策对象和训练前可证伪性，允许进入下一道零训练门：

`P0H_CONDITIONAL_GO_EPISTEMIC_COMMITMENT_TO_P1_ZERO_TRAINING_ONLY`

这不是算法 GO，更不是论文题目冻结。它只授权完成最近邻全文审计、解析反例和环境语义测试。

## 为什么优先候选一

1. 它针对的是团队成员之间的**认知状态不一致**，不是 DRTP 的训练分布问题。
2. 它有真实的新决策对象：在无法确认共同信息时选择 commit、defer 或 fallback。
3. 缺口可在训练前证明；若信息等价类或单边承诺损失不存在，无需消耗 GPU。
4. 可形成严格受控对照：相同 actor 容量和历史信息，仅比较是否显式控制 epistemic consistency risk。
5. 它能复用动力学、训练和审计基础设施，但需要新的任务语义与证据，符合“真正新课题”的约定。

## P1A：最近邻全文差异门

必须全文核验：

- MACKRL；
- arXiv:2512.20778；
- RA-L 2026 communication-value 方法；
- unreliable communication 下 Dec-POMDP/common-information 代表工作。

必须产出逐项矩阵：信息假设、通信是否可控、是否允许可靠 ack、决策对象、保证对象、执行语义、实验环境。候选至少需要一个数学对象和一个执行语义上的实质差异。仅有 UAV 应用差异不通过。

## P1B：最小反例门

构造二智能体、二阶段协调问题，冻结：

- agent 1 的两个合法局部历史不可区分；
- agent 2 是否收到承诺消息不同；
- 双方 commit 获得高收益；
- 单方 commit 产生严格负收益或安全代价；
- fallback 收益较低但有限；
- 通信丢失后不能通过额外可靠消息消除不确定性。

需要解析证明：任何仅依赖 agent 1 合法历史的确定策略都无法在两个状态中同时选择集中式最优动作；同时存在一个风险阈值区间，使 commit/defer/fallback 三者都不是全局支配策略。

失败条件：若普通 recurrent policy 通过现有观测即可区分两个状态，或 always-commit/always-fallback 支配，则关闭。

## P1C：UAV 语义影子环境门

只新增最小 shadow environment，不接训练：

1. 使用 `envs/uav_intercept_3d_env.py` 的动力学和安全计算；
2. 构造需要同步承诺的任务窗口；
3. 消息接收为私有事件，不向 actor 泄漏全局 delivery/ack 真值；
4. 链路丢失后 commit、defer、fallback 均必须有物理后果；
5. 用固定动作脚本证明双边承诺、单边承诺和降级三类轨迹可区分；
6. 验证基线任务可完成且不饱和。

P1C 不允许修改主 `uav_intercept_3d_env.py` 的既有默认语义；应新增独立 adapter 和 smoke test。

## P1D：训练前算法合同

只有 P1A--P1C 全部通过后，才允许定义算法。合同必须满足：

- 算法核心不能被概括为 GRU + auxiliary loss；
- 不把真实消息投递状态或队友 belief 输入 actor；
- 主对照至少包括相同容量 recurrent MAPPO 和 common-knowledge/communication baseline；
- 主要端点同时包括任务回报、成功、单边承诺率、fallback 率、动作一致性风险和安全代价；
- 训练 seed 是统计单位；
- P2 pilot 为 3 seeds、每条不超过 1M steps，总量不超过 15M；
- pilot 前冻结继续/停止标准，不依据结果修阈值。

## 当前禁止事项

- 不建立云端训练包；
- 不命名最终算法；
- 不写“首次解决”或“保证鲁棒”；
- 不把旧 DRTP A/B、OOD、PLR 或消融数字写入新课题；
- 不同时推进候选二、三；
- 不因 P1 失败而立刻修改任务直到反例成立。

## 对质量目标的现实判断

候选一若只实现一个 commitment head，最多仍是普通二区边缘方法；若能同时提供严格信息结构反例、动作一致性/性能界、两个环境、匹配基线和 seed-level 复现，才具有强二区潜力。一区还需要更强理论或真实系统/硬件在环证据。

