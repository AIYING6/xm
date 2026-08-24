# DRTP 静态非均匀拓扑扰动对照：训练前冻结合同

**协议：** `DRTP-SNR-Q2-MECHANISM-COMPARATOR-V1`  
**状态：** `PRETRAINING_CONTRACT_FROZEN — NO TRAINING STARTED`

## 1. 问题与定位

该后续实验只检验一个替代解释：DRTP 相对 UTR 的收益是否仅来自非均匀故障暴露，而非训练期间依据已完成 episode 回报更新的动态重加权。它是独立的、前瞻性的机制对照，不改写历史 development、held-out 或正式 UTR--DRTP 五种子结论。

三种方法必须同场出现：

| 方法 | 正常工况质量 | 六个故障组条件分布 | 训练期反馈 |
|---|---:|---|---|
| UTR-SG-MAPPO | 0.50 | 均匀 \(1/6\) | 无 |
| SNR-SG-MAPPO | 0.50 | 下表冻结的静态非均匀分布 | 无 |
| DRTP-SG-MAPPO | 0.50 | 有界动态分布 \(q_u\) | 已完成 episode return→EMA→difficulty |

三者都使用同一 116,728 参数单图 actor/critic、PPO、S2 环境、奖励、故障语义、actor 信息边界、七个训练组和运行时状态持久化。SNR 不是新网络、辅助损失、奖励或课程；它只是在 reset 时读取固定的六维概率。

## 2. SNR 静态权重：独立构造原则与冻结数值

令每个组的结构严重度仅由训练前已知的故障起始时刻与持续时间定义：F0 为参照 0；较早起始 TE 为 +1；较晚起始 TL 为 −1；短持续 DS 为 −1；长持续 DL 为 +1；同时具有最早起始和最长持续的复合组 CP 为 +2。该规则不读取 UTR/DRTP 的训练日志、权重、回报、checkpoint 或正式评估结果。

为避免额外调节连续温度或事后搜索，按上述严重度的秩次直接冻结如下条件分布：

| 故障组 | F0 | TE | TL | DS | DL | CP | 合计 |
|---|---:|---:|---:|---:|---:|---:|---:|
| \(q_k^{\mathrm{SNR}}\) | 0.15 | 0.20 | 0.10 | 0.10 | 0.20 | 0.25 | 1.00 |

因此，训练中每组的无条件质量为 \(p_k^{\mathrm{SNR}}=0.5q_k^{\mathrm{SNR}}\)。SNR 权重不得变动、平滑、EMA 更新、难度计算或由 checkpoint 恢复后的状态更新。该分布与任何已有 DRTP 最终 \(q\) 轨迹的相似或差异均不能作为其构造依据。

## 3. 前瞻性运行设计

训练种子、评价样本带命名空间和预算必须在任何 SNR/UTR/DRTP 训练或新评价前一次性冻结。建议使用未曾用于训练、调参、诊断或决策的连续新 seeds `2401–2405`，并在启动前执行 Git 历史、工作区、归档和 manifest 的 seed-provenance 审计；任何已使用的 seed 必须使预检查失败，而不是换一个“看起来更好”的 seed。

每一方法×种子轨迹从零开始、严格连续训练至共同的 39,063 updates（10,000,128 环境步），保存相同里程碑，但只以共同 10M final checkpoint 作最终判断。禁止 warm restart、checkpoint promotion、早停、种子排除、canonical seeds 0–4、使用历史 2301–2305 checkpoint 或根据任一中期结果调整预算。

新评价样本带应使用未占用 namespace（建议 `500000–500099`）、12 个与正式合同相同的条件及每条件 100 episode。它只能作为该机制对照的前瞻性证据，不能与历史样本带混合。

## 4. 预检查与技术验收

在长训练前必须 PASS：

- 三种方法均为 116,728 参数，且除 sampler mode/static q 外配置哈希相同；
- SNR 的每次 reset 仅从冻结 q 采样，组内成员保持均匀；
- SNR 不实例化或写入 q 更新、EMA、difficulty、completed-return feedback；
- UTR、SNR、DRTP 的 normal anchor、组宇宙、PPO、奖励、环境和 actor 信息边界逐项一致；
- 三种 sampler 的 deterministic replay、save→reload→next-update exact continuation、graph legality 与一更新有限值 smoke 均通过；
- 新种子与新样本带 provenance 为 PASS。

## 5. 解释规则

最终以配对训练种子为独立单位，完整报告每个种子的 \(J_{\mathrm{nominal}}\)、\(J_{F0}\)、\(J_{\mathrm{pert,mean}}\)、\(J_{\mathrm{pert,worst}}\)、碰撞、超时、约束违规和风险集触发有效性。

- `DRTP > SNR > UTR`：支持动态反馈在静态非均匀暴露之上具有附加经验价值；
- `DRTP ≈ SNR > UTR`：支持非均匀暴露分配的价值，但不支持将动态反馈作为主要机制贡献；
- `SNR > DRTP`：DRTP 的动态机制主张不成立，应将 SNR 作为更简单的经验方案；
- 三者无清晰差异：仅保留已有 UTR--DRTP 的有限描述，不扩大动态归因。

这些是解释边界，不是根据当前结果倒推的 superiority threshold。安全、暴露和灾难性种子规则必须在真正训练前以独立运行合同固定，不得在结果后修改。

## 6. 禁止项与停止点

本合同本身不授权训练、样本带生成或 checkpoint 评价。未经作者针对该 15 条、共同 10M 轨迹的单独运行授权，不得执行任何长训练命令。不得复制正式 DRTP 2301–2305 的终局 q、终局回报或历史最好 seed 以设定 SNR；不得因 SNR 结果再搜索第二个静态分布。
