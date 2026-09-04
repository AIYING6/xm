# TGTR-PPO P0：证据与失败模式分析

**状态：** 零训练设计审计完成
**结论：** 现有证据支持更换“更新机制”，不支持宣称已经识别 DRTP/EGTR 反转的统一根因。

## 1. 目标没有改变

目标是训练得到一个单模型、单最终策略：不依赖模型 selector、fallback 或评估期选择；在新训练 seed、故障条件和 OOD 条件下保留高收益，并降低 catastrophic downside 与跨 seed 波动。

PVF 仅保留为工程备选，不作为主研究贡献。

## 2. 现有结果排除了哪些简单答案

| 历史路线 | 已建立的事实 | 对新设计的约束 |
| --- | --- | --- |
| Original DRTP / EGTR | 改变训练分布可以产生很高收益；EGTR 相对 Original DRTP 在两批新 cohort 中整体改善明显，但相对 UTR 仍发生 cohort 差异，且两批未同时通过安全/离散度合同 | 不能否认 adaptive exposure 的收益潜力，但不能把 sampler 微调当成稳定性解法 |
| S2 / anchor / TR | 限制 sampler 的局部方案可在某些 seed 改善，也可伤害原本较好的轨迹 | 不再做 DRTP-v3/EGTR-v2 式 q 修补 |
| KLR / KLB | 全局 post-step KL rollback 的 pilot 有正向迹象，但双 cohort 复制产生新 catastrophic seed 并扩大离散度 | “大 KL 就回滚”不是充分规则；全局平均 KL 不是拓扑组保护 |
| Selective-KLR / SR-DRTP | matched-shadow 没有得到时间领先、跨 cohort 可重复的干预效用信号 | 不再训练 gate 去猜“什么时候救” |
| Group-weighted PPO | 同批 rollout 的局部 surrogate 在 5/5 seed 上改善，但完整训练两批均失败并产生更差下尾 | 标量加权和局部 surrogate 胜利不足以证明长期稳定 |
| TCR / SPC | TCR 已经实现 nominal/failure 梯度投影；1M 表现强，但 2M 的 TCR seed2101 出现真实崩塌，且冲突率、投影量、KL、梯度范数均没有唯一异常 | 不能把 PCGrad/CAGrad/MGDA 换名后当作新方法；瞬时梯度几何不等于实际策略漂移控制 |
| TC-SAM | 参数邻域平滑没有形成稳定性能优势 | 单纯 flatness 正则不是当前首选 |
| M3 rich telemetry | collapse/recovery 窗口没有重复、领先、可操作的统一 precursor | 新方法是预防性结构约束，不是“已证实根因的修复” |

## 3. 仍然成立的正证据

1. 高收益事实是真实的：多条 DRTP/EGTR/TCR 轨迹在冻结评估协议上显著高于其 paired UTR；问题是该收益不能稳定复制到多数新 seed。
2. 固定 50% nominal / 50% failure exposure 的 UTR/TCR 系统能正常学习，说明无需 adaptive q 才能训练任务。
3. rollout 已保存 training-only `condition_group`，并能计算逐组 advantage、surrogate 与 actor gradient；这些信息不进入 actor observation，也不读取 evaluation tape。
4. 现有 actor 更新事务已能保存/恢复参数与 Adam state，并能在更新后计算经验 KL；实现新的候选检查不需要模型 selector。

## 4. 新设计要解决的精确缺口

PPO clipping 并不等同于严格 trust region。历史 KLR 又只检查全 batch 的 sampled-action approximate KL。两者都不能阻止某个样本较少的 topology group 在一次更新中发生过大的真实策略移动。

TGTR-PPO 因此不预测“哪条 seed 会坏”，也不以梯度冲突作为病因。它只执行一个更窄、可直接验证的原则：

> 普通 PPO 仍是高收益默认方向；只有当同一 training batch 显示某个 topology group 的 held-stream mean surrogate 被该候选更新降低，或发生过大策略漂移时，才对该 actor step 做最小修正，并用未参与修正求解的同批独立 stream 做训练内证书。

## 5. 关键接口发现

当前 `FixedStratifiedTopologySampler` 强制 `num_envs == 4`：两路 nominal、两路 failure。failure group 在 episode reset 时才轮换。由于 rollout 为 64 step、episode 可长至 260 step，一次 PPO update 通常只含两个 failure group，而非六组。

所以，现有 4-stream batch **不能**支撑“每次更新对六个 failure group 分别约束”。P0 不允许忽略这个事实。TGTR-PPO 的开发必须先建立 default-off 的同步固定分层采集：

- 24 streams；
- 12 nominal streams；
- 每个 failure group 固定 2 streams；
- 每次 64-step rollout 共 1536 graphs；
- nominal 768 graphs；每个 failure group 128 graphs；
- 每组两条 stream 分别作为 design/certificate，不能按时间点伪装成独立样本；
- 总环境步预算保持不变，因此更新次数相应减少；
- matched baseline 必须是同样 24-stream batch 的 ordinary UTR PPO（Sync-UTR）。

这个改变不是 adaptive sampler：组质量、组概率和 stream 映射在训练前固定，且永远不读取 return。

## 6. 科学边界

- 不能声称 gradient conflict 是历史反转根因。
- 不能声称每步局部证书保证最终 return 单调。
- 不能把 C1 的 same-rollout 结果写成算法性能证据。
- 如果同步批次成本不可承受、修正后频繁零步，或同批 certificate 不能排除组伤害，则该机制在进入 fresh-seed 训练前关闭。
