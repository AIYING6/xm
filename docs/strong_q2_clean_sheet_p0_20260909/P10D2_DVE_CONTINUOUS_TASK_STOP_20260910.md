# P10-D2 连续拦截任务可识别性审计

**判定：** `P10D2_CONTINUOUS_TASK_STOP_FALLBACK_ORACLE`  
**训练：** 未启动。  
**题目状态：** 不关闭 DVE，但当前连续任务定义不得进入学习实验。

## 1. 冻结运行结果

在 600 个连续二维双 UAV 拦截条件上，旧机动由推理起点快照生成；推理期间 UAV 与目标持续运动；完成后分别滚动旧机动和 fallback。

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| stale action 有效比例 | 80.00% | 20%–80% | PASS（边界） |
| 同时延有效性分叉对 | 30.63% | ≥20% | PASS |
| 个体安全、联合不兼容 | 17.00% | ≥5% | PASS |
| stale 执行安全失败 | 17.00% | ≤80% | PASS |
| oracle 相对最佳常数策略增益 | 0.059 | ≥0.100 | **FAIL** |

平均轨迹价值：always-accept 为 -3.922，always-fallback 为 -2.591，逐样本 oracle 为 -2.532。

## 2. 停止原因

当前 fallback 在完成时直接读取当前目标位置，并立即生成精确追踪速度，没有任何重规划计算时间、控制切换时间或任务机会损失。这等价于给 fallback 一个零成本 completion-time replanning oracle。

因此 always-fallback 已逼近逐样本 oracle，DVE 决策只剩极小可提升空间。若在这个接口上训练，可能出现两种不可发表结果：

- 所有方法都学会 fallback，DVE 没有增益；
- 通过人为增加 accept 奖励制造增益，但科学问题不成立。

该失败不是通过修改门槛、增加时延或调大碰撞惩罚来修复。

## 3. 唯一允许的结构修订

P10-D2R 只修订 fallback 的真实时间语义：

1. accept：立即执行已经完成的旧机动；
2. fallback-hold：立即执行有界安全保持动作；
3. replan：从完成时状态启动一次新的慢推理，在其计算完成前持续 fallback-hold；
4. 新动作只能在第二次推理完成后执行；
5. accept 与 replan 使用同一慢策略计算时延分布；
6. 所有方法共享相同 fallback controller，不允许 DVE 独占更优低层控制。

这不是给 DVE 添加奖励，而是移除当前对 fallback 的零成本 oracle 假设，使“立即采用旧决策”和“安全等待新决策”形成真实实时控制权衡。

## 4. P10-D2R 预设门

- stale action 有效比例 25%–75%；
- 同时延有效性分叉对 ≥20%；
- 联合不兼容比例 ≥10%；
- always-accept 和 always-replan 均比 oracle 低至少10%；
- oracle 选择 accept 与 replan 的比例均在20%–80%；
- zero-latency replan 只作为上界，不能作为公平 baseline；
- 不增加显式 validity 分类奖励；
- 若引入真实 fallback 时序后 oracle 间隙仍不足，关闭 DVE 任务线。

## 5. 证据边界

本结果证明连续运动学中存在同延迟异有效性和联合不兼容状态，但当前 fallback 接口使决策价值不足。它不支持任何方法性能结论，也不授权修改 DVE 算法。

## 6. 资产

- 环境：`envs/dve_continuous_intercept.py`
- 配置：`configs/p10d2_dve_continuous_task_audit_20260910.json`
- 审计：`scripts/p10d2_dve_continuous_task_audit.py`
- 结果：`docs/strong_q2_clean_sheet_p0_20260909/P10D2_DVE_CONTINUOUS_TASK_RESULT.json`
