# DRTP B 线 H3 假设空间压缩报告

最终 Gate：`NO_ACTIONABLE_H3`。

## 已排除的内容

H1 已关闭：没有跨 seed 重复的直接 sampler/exposure/support/outcome 链。
H2 已关闭：5 个新的 paired seed 在冻结 0.5M 判据下产生 0/5 完整
optimization → q → behavior/support signature。大 q 偏离、单点 PPO 异常、或单个
bad seed 均不能被重新命名为 H3。

## 对剩余空间的筛选

1. **Policy basin / initialization** 与 **behavior-mode bifurcation** 在概念上仍可能，
   但当前仅有 2702 的局部行为差异；它后来恢复，且没有第二个 adverse seed 重复。
   2300/2400 没有步级行为/几何/动作遥测，不能把 cohort reversal 归因于模式分叉。
2. **Group-conditioned credit assignment** 缺少 group-conditioned critic error、advantage
   credit 或反事实价值记录，故当前不可观测。
3. **Distribution drift sensitivity** 是唯一能用旧 sampler 数据直接检查的方向，但不
   支持升级：独立负向 cohort 的平均 L1 q change 更低（0.000546 vs 0.000605），
   虽最大变化和平均 q 距离更高；KL 基本相同。动态指标没有形成唯一、可重复、与
   支持/结果相连的方向。
4. **Generic PPO/MARL sensitivity** 仍可作为 null explanation，但不是 DRTP-specific
   的可证伪病因，也没有单一最小 intervention。

## 为什么不选择 H3

没有候选同时满足现有描述性支持、时间顺序、paired UTR 特异性、短预算证伪性与
单一最小修复方向。此时强行选 policy basin、credit assignment 或 distribution drift
只会把 H1/H2 的未证实叙事换名重启，违背本合同。

## 冻结动作

- 不生成 `H3_MINIMAL_CONFIRMATION_PROPOSAL.md`；
- 不启动新训练、评价、1M/3M/10M continuation 或算法修改；
- DRTP B 线机制稳定化探索在当前证据边界下停止。

这不改变 A 线论文：DRTP 仍可被如实表述为具有显著 formal-cohort 平均收益、但有
跨 cohort/seed sensitivity 的经验方法；B 线新增结果只加强“目前没有科学授权的
稳定化干预”的边界。
