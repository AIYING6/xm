# P8B ACFID 共享结构交互门结果

## 决策

`ACFID_SHARED_INTERACTION_GATE_PASS`

P8 的负结果证明普通独立 pair 二阶项不能产生零样本泛化。P8B 没有修改环境、故障集合、恢复动作、训练/测试组合或原 P0 阈值；唯一方法修正是把独立 pair 参数替换为跨故障类型、任务分支和任务上下文共享的交互预测器。

## 受控比较

| 模型 | 未见 pair MAE | 未见 pair regret | triple regret | quadruple regret |
|---|---:|---:|---:|---:|
| Additive | 0.3670 | 0.0878 | 0.2803 | 0.2699 |
| Type-only shared interaction | 0.2335 | 0.0663 | 0.1407 | 0.0678 |
| Task-structured shared interaction | **0.1422** | **0.0368** | **0.1076** | 0.0683 |

相对增益：

- 未见 pair MAE 相对 additive 降低 61.25%；
- 未见 pair regret 相对 additive 降低 58.09%；
- 未见 pair regret 相对 type-only 降低 44.54%；
- triple/quadruple 平均 regret 为 additive 的 31.98%。

四项冻结检查全部通过：pair MAE、pair regret、任务结构增量价值及高阶组合非劣性。

## 允许的解释

该结果支持以下方法假设：故障类型、任务分支关系和当前任务上下文可以为未见故障对提供共享的交互归纳偏置；普通二阶展开失败不等于动作条件交互问题失败。

## 不能推出的结论

这仍是人为可控宏观任务上的零训练可识别性结果，不能证明神经策略能够学会该表示，也不能证明真实 UAV 故障服从二阶结构。单一冻结 pair 划分也可能偶然有利，因此尚不授权 9M pilot。

## 下一门

P0C 必须在多个平衡训练 pair 划分、多个上下文随机种子和保持不变的阈值下复核：

1. structured 对 additive 的 pair regret 增益方向是否稳定；
2. structured 是否稳定优于 type-only；
3. triple/quadruple 是否保持非劣；
4. 是否存在由单一故障类型或单一任务分支驱动的脆弱划分。

P0C 通过后才允许构建 3×3×1M 的学习 pilot。
