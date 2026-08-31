# DRTP B 线组合决策（2026-08-31）

**状态：** `B_LINE_NO_PROMOTABLE_RELIABLE_DRTP_CANDIDATE`  
**主线 A：** `UNCHANGED`  
**自动训练或算法续代：** `NOT AUTHORIZED`

## 目标不变

B 线的目标仍是一个同时满足下列条件的 Reliable-DRTP：保留 Original
DRTP 的故障鲁棒收益、改善最差训练 seed、降低跨 seed 离散度，且不以压低原有
高收益 seed 或牺牲安全性为代价。它不修改、替代或追溯性改写主线 A 的证据。

## 已完成证据的组合判断

| 路线 | 最终可用结论 | 组合决策 |
| --- | --- | --- |
| TR / uniform anchor / conservative sampler | 不能同时保留收益、下尾与离散度 | 关闭，不作参数 sweep |
| 固定 KLR / KLB | 早期 KLR 曾有正向迹象，但双 cohort 最终复现中两个 cohort 均出现新的 catastrophic seed，且离散度增加 | 关闭，不调 KL 阈值 |
| paired probe / population selector | 早期方向不能跨独立 cohort 保持 | 关闭，不做 v2 |
| B1 短分支 update sensitivity | 坏 DRTP seed 未出现一致、时间领先、且超过 UTR 的更新分叉信号 | 该机制关闭 |
| B5 failure-credit telemetry | 未形成重复的 optimization → behavior → outcome 连续链 | 该机制关闭 |
| Selective-KLR P1 shadow audit | 88 个报警中仅少数有实际干预效用；绝大多数 near-zero，且有益/有害事件不能形成 seed 级可推广判别器 | 不训练 selector |
| CV-DRTP counterfactual critic | 两个新鲜 5-seed cohort 均失败；CV 在 A 中新增 4 个 catastrophic seed，在 B 中新增 5 个，且均未保留 Original 收益 | 永久关闭 CV 路线，不做 CV-v2 |

CV-DRTP 的 0.5M 双 cohort 结果特别具有决定性。Cohort A 的 CV 相对 UTR
五个 paired gain 均为负，并新增 4 个 catastrophic seed；Cohort B 同样五个 gain
均为负，并新增 5 个 catastrophic seed。Cohort B 的 range/SD 略小不能解释为
稳定化成功，因为这是在系统性损失收益和下尾后的表面收缩。故该路线不能继续到
1M，也不能通过更改 Q-loss 权重、baseline 形式或其它未预注册补丁来挽救。

## 科学结论与边界

当前证据不支持“Original DRTP 的不稳定性由某一个局部 sampler、KL 报警、
credit proxy 或 actor–critic 形式的单一可操作故障机制所致”。这**不等于**算法
研究无路可走；它只排除了继续以局部补丁和结果驱动调参为主要策略。

高收益仍是 Original DRTP 的真实观察事实，但它与严重的训练 seed/cohort 风险
并存。任何未来 Reliable-DRTP 必须以新的、独立支持的机制为起点，而非从过去
某一个局部 pilot 中挑选最好的数值。

## 下一阶段：机制发现，不造新算法

下一步只允许零训练的跨档案证据综合。目标不是再次筛选赢家，而是检验是否存在
可被未来干预的共同前兆。分析应以训练 seed 为独立单位，保留 cohort 分层，并
覆盖已存在的 Original DRTP、UTR、KLR、P1 shadow、B1 和 B5 证据。

只有同时满足以下条件，才可提出一个新的最小算法设计合同：

1. 至少两个不利 DRTP seed 出现同方向的候选信号；
2. 信号在性能/任务退化之前出现，并在相邻合理阈值下不消失；
3. matched UTR 和高收益 DRTP seed 中该信号明显更弱或不存在；
4. 信号连接至少三层连续证据：训练状态或更新 → 行为/价值/策略中间层 → 任务结果；
5. 候选干预能够精确对应该信号，且不需要同时修改 PPO、sampler、reward、网络等多个模块。

任一条件不成立时，输出 `MECHANISM_DISCOVERY_NO_GO`，停止 B 线新增算法训练，
将资源转回主线 A 的投稿收敛。即使未来形成机制合同，第一轮验证也必须在两个
新鲜 cohort 中同时启动，并分别报告，不得用合并的 n=10 掩盖 cohort reversal。

## 禁止项

- 不做 TR-v2、anchor sweep、KLR-v2、KLB-v2、PP-v2、PR-v2、Selective-KLR 或 CV-v2；
- 不因某个好 seed 重跑、替换 seed、升格 checkpoint 或延长预算；
- 不将 B 线探索结果混入主线 A 的正式因果主结论；
- 不以 episode、update 或 trigger row 代替训练 seed 进行统计推断。
