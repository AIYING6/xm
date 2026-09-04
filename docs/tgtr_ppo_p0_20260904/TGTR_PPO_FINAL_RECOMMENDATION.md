# TGTR-PPO P0 最终建议

## 结论

`TGTR_P0_FEASIBLE_FOR_C1`

这是“允许实现并做同批 rollout 机制审计”的结论，不是算法有效结论，也不是训练授权。

## 推荐主线

主线从 sampler adaptation 改为：

> 固定同步拓扑曝光 + ordinary PPO 高收益锚点 + 逐拓扑组最小修正 + 独立 training-stream certificate + 逐组完整策略 KL。

这个候选保留了现有经验中最有价值的两点：

- UTR 的固定曝光避免 q-feedback；
- ordinary PPO 是默认方向，避免 worst-group 方法把整个训练永久变保守。

同时直接补上历史方法都没有解决的缺口：

- TCR 只约束瞬时聚合梯度；
- group weighting 只改变 loss 贡献；
- KLR 只看全局 sampled-action KL；
- EGTR 仍通过 sampler 改变未来数据分布。

TGTR 检查并约束的是候选 actor step 对每个 topology group 实际造成的局部 policy change。

## 为什么不是立刻跑 3 seed

现有 4-stream rollout 在一次 update 中没有六个 failure group，直接训练会使核心算法定义失真。必须先完成 default-off 24-stream Sync-UTR/TGTR 实现，并用 C1 证明：

- 七组真的同时存在；
- correction 真的作用；
- certificate 不是形式检查；
- 算法不会频繁 zero-step；
- 计算成本可承受。

## P0 后唯一允许的动作

单独授权后，可进行 **TGTR C1 implementation + same-rollout mechanism audit**。不得同时启动 0.5M、1M 或 10M 训练；不得生成 formal evaluation tape；不得回头修改 EGTR、DRTP、TCR 的历史结论。

## 失败即停止的条件

如果 C1 表明：ordinary update 很少产生可复现的逐组伤害、TGTR 需要频繁零步、certificate 与 design 方向不一致、或成本超过 4×，则关闭该候选。届时不应再把同一方案改名为 TGTR-v2。
