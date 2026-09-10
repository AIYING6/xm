# P8 ACFID P0 结果

## 决策

`ACFID_P0_STOP`

不启动 9M pilot。该决定来自预先冻结的 G1–G6 门，而不是训练结果不理想后的事后调整。

## 结果

| Gate | 结果 | 核心量 |
|---|---|---|
| G1 基础可学习性 | PASS | 单故障最优价值均值 1.330 |
| G2 非加性 | PASS | 15 个 pair 超过冻结交互阈值 |
| G3 决策相关性 | PASS | 14 个 pair 改变动作排序 |
| G4 加性模型不足 | FAIL | 二阶模型 MAE 0.430，高于加性模型 0.378 |
| G5 低阶零样本泛化 | FAIL | 二阶 regret 0.158，高于加性模型 0.142 |
| G6 结构对齐 | PASS | 同分支交互 1.062，跨分支交互 0.583 |

## 科学解释

P0 支持“组合故障会产生动作相关的非加性效应”，但不支持“只学习 nominal、single 和部分 pair 后，普通二阶交互展开可以改善未见组合恢复决策”。

失败暴露的是方法地基缺口：为每个故障对设置独立二阶项时，训练中未出现的 pair 没有可估计参数。二阶展开描述了交互，却没有提供从已见交互迁移到未见交互的归纳机制。高阶组合上的额外误差也使二阶模型的动作排序劣于加性模型。

因此当前证据不能授权：

- 强化学习 pilot；
- “低阶交互支持零样本组合恢复”的论文主张；
- 通过修改门槛、重新选择 pair 或删除高阶测试来挽救结论。

## 保留价值

该审计仍确认了三个有价值的事实：任务中存在非加性交互；交互会改变恢复动作；同任务分支的交互更强。这些事实可作为未来研究输入，但不足以使当前 ACFID 方法进入训练。

## 后续状态

该停止结论对“每个故障对使用独立二阶参数”的 P8 方法保持有效。后续 P8B 没有降低本门阈值或重选测试组合，而是提出了新的跨故障类型、任务分支和上下文共享参数化，并通过独立的新增方法门。P8 与 P8B 结果必须同时保留：前者是必要负对照，后者是方法修正证据。

## 资产

- 环境：`envs/acfid_compound_fault_env.py`
- 冻结门：`configs/p8_acfid_p0_interaction_gate_20260910.json`
- 审计程序：`scripts/p8_acfid_p0_interaction_gate.py`
- 机器结果：`artifacts/diagnostics/p8_acfid_p0_interaction_gate_20260910/ACFID_P0_REPORT.json`
- pair 明细：`artifacts/diagnostics/p8_acfid_p0_interaction_gate_20260910/ACFID_P0_PAIR_INTERACTIONS.csv`
