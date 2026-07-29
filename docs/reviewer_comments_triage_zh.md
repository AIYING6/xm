# 预审意见处理与项目行动清单

日期：2026-07-29

来源：`D:/File/Downloads/论文审稿意见总结.md`

## 1 总体判断

这份意见总体有道理，而且标准偏高，适合作为一区目标下的内部预审清单。它的核心判断是准确的：

- 当前选题方向有价值；
- 当前论文已经有清晰主线；
- 但现阶段仍是“研究方案 + 初稿骨架 + 部分开发证据”；
- 真正投稿前必须补齐信息边界、形式化定义、公平 baseline、正式统计和可复现细节。

最关键的一点是：该意见没有否定项目方向，而是在指出“如果按现在稿件直接投稿，会被打回来”的问题。项目方向仍然可以继续，但必须按更严格的证据链推进。

## 2 意见优先级判定

| ID | 问题 | 判断 | 优先级 | 当前处理 |
|---|---|---|---|---|
| R1 | 任务支援图可能造成 Actor 信息泄漏 | 合理，必须严查 | P0 | 已修正文档表述，仍需测试和审计表 |
| R2 | 方法公式和参数说明不足 | 合理，必须补 | P0 | 已有公式稿，需继续细化为 LaTeX |
| R3 | 主实验范围过窄 | 部分合理 | P1/P2 | 主实验不宜继续无限扩，需增加 OOD/补充实验 |
| R4 | 任务链恢复定义不严格 | 合理，必须补 | P0 | 需补连续闭合 \(K\) 步和未恢复处理 |
| R5 | 3DOF 动力学描述不足 | 合理，必须补 | P0 | 需从代码抽参数表和方程 |
| R6 | 通信模型描述不足 | 合理，必须补 | P0 | 需写伪代码和参数表 |
| R7 | train/validation/test/OOD 划分不清 | 合理 | P0 | formal protocol 已有基础，需整理成表 |
| R8 | 预算扩展规则不够量化 | 合理 | P1 | 需定义 1M -> 2M 的量化门槛 |
| R9 | 五个训练种子偏少 | 合理但成本高 | P2 | 五种子为最低标准，一区增强可扩 8-10 |
| R10 | baseline 还需加强 | 合理但需分级 | P1/P2 | 参数匹配、Local-only、upper bound 优先 |
| R11 | role-gate prior 是混杂变量 | 合理 | P1 | 不继续调优，但需 prior=0 对照 |
| R12 | BC 初始化影响结论 | 合理 | P1 | 需报告 BC-only 和 PPO gain |
| R13 | 稿件混有内部计划语言 | 合理 | P1 | 当前 docs 可保留，正式 manuscript 需清理 |
| R14 | 摘要是计划型摘要 | 合理 | P2 | 等正式结果后重写 |

## 3 立即修正过的内容

已修正：

- `docs/formal_method_formulas_zh.md`
  - 将任务支援关系从依赖全局 \(z^t\) 改为依赖 actor 合法可见信息 \(b_{ij}^t\)；
  - 明确任务支援边必须满足“角色兼容 + 物理通信投递 + 可见支援证据”；
  - 明确不得使用全局任务链阶段、评估变量或 critic 信息构造 actor 侧边。

- `docs/formal_manuscript_draft_zh_v1.md`
  - 删除容易引发信息泄漏误解的“根据任务链阶段动态构建”表述；
  - 改为“根据角色兼容性和 actor 合法可见的信息状态构建”；
  - 明确任务支援边不得读取全局任务链阶段或评估专用链路闭合变量。

- `tests/test_gate1_communication_feasibility.py`
  - 新增 `test_task_support_relation_does_not_depend_on_hidden_target_state`；
  - 新增 `test_union_graph_does_not_use_potential_task_support_without_delivery`；
  - 新增 `test_relay_failure_blocks_relay_originated_task_support`；
  - 当前通信可行性测试结果：`28 passed`。

- `docs/actor_information_flow_audit_table_zh.md`
  - 新增 Actor 信息流审计表；
  - 明确 task-support relation 的合法数据来源；
  - 记录当前测试覆盖与剩余风险。

## 4 P0 必须完成，否则不能进入最终结论

### P0-1 Actor 信息流审计

目标：证明 actor 没有通过任务支援图获得全局真值。

需要产出：

- `docs/actor_information_flow_audit_table_zh.md`
- 对应测试记录；
- 论文 Methods 中的信息边界表。

当前状态：

```text
基本完成第一轮。已补充 relay-failure 下 task-support edge 的专项断言。
```

必须审计：

| 输入项 | 数据来源 | 是否经通信 | 是否使用真值 | Actor 是否可用 |
|---|---|---:|---:|---:|
| 自身状态 | 本机状态 | 否 | 否 | 是 |
| 邻居状态 | 通信消息或图边 | 是 | 否 | 条件可用 |
| 目标状态 | 直接感知或消息缓存 | 视情况 | 否 | 条件可用 |
| 全局任务链闭合 | 环境评估变量 | 否 | 是 | 否 |
| 任务支援边 | 角色兼容 + 已投递通信 + 可见信息 | 是 | 否 | 是 |
| critic 全局状态 | CTDE 训练 | 否 | 可含真值 | 仅训练可用 |

### P0-2 任务链恢复数学定义

需要定义：

```text
C_t = I_det^t * I_deliver^t * I_fresh^t * I_engage^t
```

恢复时间：

```text
T_rec = inf { tau >= 0 : product_{k=0}^{K-1} C_{t_f+tau+k} = 1 }
```

还需要说明：

- \(K\) 的取值；
- 未恢复 episode 如何处理；
- 右删失或 timeout 截断；
- delayed recovery 和 recovery 的区别。

当前状态：

```text
已在 docs/task_chain_env_formalization_zh.md 中给出第一版定义，并同步更新 docs/formal_method_formulas_zh.md。
```

### P0-3 3DOF 动力学与通信模型可复现化

需要从代码抽取并写入：

- 时间步长；
- 速度更新；
- 航向更新；
- 航迹倾角更新；
- 位置更新；
- 动作空间；
- 安全距离；
- 高度边界；
- 不同角色参数；
- 丢包采样粒度；
- 时延队列；
- TTL；
- 置信度衰减；
- 中继失效影响范围。

当前状态：

```text
已在 docs/task_chain_env_formalization_zh.md 中整理 3DOF 动力学、平台异构参数、感知模型、通信丢包/时延、TTL、置信度、多跳传播、中继失效和攻击窗口定义。
下一步应转为论文 LaTeX Methods 小节，并补充伪代码。
```

### P0-4 方法公式补全

需要补：

- 关系特定参数；
- 角色对参数；
- role gate 计算；
- prior 形式；
- 图融合方式；
- 无邻居处理；
- 图传播层数；
- 参数量统计。

## 5 P1 高收益增强

这些不是立即阻断项，但强烈建议在正式实验前后完成。

1. 增加 `Parameter-Matched Single Graph`。
2. 增加 `Single-Graph + Role ID`。
3. 增加 `Multi-Relation without Role-Pair Gate`。
4. 增加 `Single-Graph + Role-Pair Gate`，如果实现成本可控。
5. 报告 `prior=0` 与 `prior=0.4` 对比。
6. 报告 BC-only、PPO-after-BC 和 PPO gain。
7. 定义 1M 扩 2M 的量化门槛。
8. 增加 Local-only、Perfect-communication upper bound、No-failure upper bound。

## 6 P2 一区增强项

这些用于提升论文上限，不应阻塞 P0 和正式主实验。

1. 通信丢包率 OOD：0.1、0.2、0.4、0.5。
2. 消息时延 OOD：0、1、4。
3. 未见失效时机。
4. 不同初始队形。
5. 轻度机动目标。
6. 不同失效持续时间。
7. 智能体编号或角色编号置换。
8. 小规模 4v2/5v2 rule-red。
9. LAG/JSBSim replay。
10. 若算力允许，将正式训练种子从 5 扩至 8-10。

## 7 哪些意见需要降级处理

### 不建议现在做完整 prior sweep

审稿意见建议 prior=0/0.2/0.4/0.6 全部比较。这个建议科学上合理，但如果全部正式训练，成本较大，而且容易重新打开调参循环。

建议处理方式：

- 正式主线保留 frozen `prior=0.4`；
- 增加 `prior=0` 作为关键对照；
- 0.2/0.6 可作为 development/appendix，不进入主表。

### 不建议所有 OOD 都重新训练

通信丢包、时延、初始队形、失效时机等应优先作为 validation-selected checkpoint 的零样本测试。只有某个 OOD 场景成为第二主场景时，才重新训练。

### 不建议用 8-10 种子阻塞当前流程

五种子是最低正式标准。若五种子结果清晰，再扩 8-10 种子增强；若五种子已经不支持主张，继续扩种子通常不会救论文主线。

## 8 当前下一步执行顺序

按优先级执行：

1. 生成 Actor 信息流审计表。已完成第一轮。
2. 检查/补充 task-support no-leakage 测试。已完成第一轮，28 tests passed。
3. 从代码抽取 3DOF 动力学和通信模型参数。已完成第一版文档。
4. 更新中文方法公式稿和论文 Methods。公式稿已更新，Methods 正文仍需 LaTeX 化。
5. 更新 formal protocol，加入量化 B* 选择规则。
6. 继续正式预算研究。
7. 实验结果出来后，再决定是否扩展 OOD 和 8-10 seeds。

## 9 最终结论

这份审稿意见是“好消息中的坏消息”：

- 坏消息：当前稿件还不能直接投稿，尤其信息边界和形式化定义必须补。
- 好消息：它没有否定研究方向，而是指出了把项目从“有潜力”推进到“可投稿”的关键路径。

当前最重要的不是继续写更多论文正文，而是先把 P0 科学有效性和可复现性补牢。只要任务支援图信息边界被证明干净，方法公式和主实验协议补齐，该项目仍然是朝着更高质量论文方向发展的。
