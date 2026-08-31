# S5 探索性稳定化压力测试与负结果边界

## 目的与证据层级

本补充材料汇总正式 DRTP 主比较完成后开展的 B 线探索。其目的不是从多个候选中追溯性选择一个“更好算法”，而是检验若干直观局部稳定器是否已经足以消除 Original DRTP 的训练 seed/cohort 风险。所有表项均为独立的开发或验证合同；不同 seed 集、预算、evaluation tape 与候选语义不允许合并为一个 `n`，也不重写本文正式 2301--2305 主 cohort 的 UTR--DRTP 结论。

训练 seed 是唯一独立单位。episode、update、sampler window 和 shadow event 仅是技术重复或时间对齐信息。所有失败 seed、checkpoint、manifest 和冻结 gate 均保留；不存在基于最终性能的 seed 替换、重跑、checkpoint promotion 或参数 sweep。

## 压力测试总表

| 路线 | 局部设计目标 | 最有利的已完成信号 | 独立或后续检验 | 最终状态 |
| --- | --- | --- | --- | --- |
| TR | 限制单次 sampler 权重移动 | 保留部分高收益 seed | 0.5M gate 未保护最差 seed，且离散度未降低 | 关闭 |
| Uniform anchor | 保留固定均匀采样底座 | 早期 cohort 中移除冻结 catastrophic 标签 | R1 五 seed 检验反转并扩大离散度 | 关闭 |
| KLR/KLB | 大 KL actor 更新的回滚/保护 | KLR 三 seed pilot 的平均和最差 paired gain 曾为正 | 两个独立 KLR cohort 均出现新的 catastrophic seed 且 gain dispersion 增大；KLB 未恢复收益 | 关闭 |
| Paired probe (PP) | 以训练期配对 probe 调整暴露 | P3 cohort 中下尾短期改善 | P4 独立 cohort 出现 catastrophic 候选并扩大离散度 | 关闭 |
| Population/priority selector | 从训练信号选择保守干预 | 个别开发 seed 有局部收益 | 未跨 cohort 稳定保住相对 UTR 优势 | 关闭 |
| Selective-KLR shadow audit | 判断一次 rollback 是否真的有益 | 88 个 KL alarm 中观察到少数有益和有害事件 | 84 个事件为 near-zero，未形成可推广的 seed-level selector 信号 | 不训练 selector |
| CV-DRTP | 用反事实 critic 降低 agent credit 方差 | 无可推广的早期成功信号 | 两个新鲜五 seed cohort 均系统性失去相对 UTR 收益并新增 catastrophic seed | 永久关闭 |

## 解释边界

这些结果支持一个有限结论：在当前冻结的环境、PPO 和 DRTP 实现中，简单限制 sampler、基于 KL 的固定 actor 干预、训练期 probe、候选选择或额外反事实 critic 均未显示出跨 cohort 同时满足“保留收益、保护下尾、缩小离散度”的可靠效果。该结论不等价于证明任何稳定化都不可能成功，也不建立 Original DRTP seed sensitivity 的单一因果机制。

因此，本文不把上述候选写成主方法、附加 baseline 排行榜或机制证明。它们的贡献是提高解释的透明度：独立 cohort 的反向结果不能被表述为一个已经可由简单局部修补解决的技术细节。未来若研究训练可靠性，需要先由新的、可重复且时间领先的机制证据授权最小干预设计，并在两个新鲜 cohort 中同步验证。
