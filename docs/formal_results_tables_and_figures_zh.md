# 中文结果表格与图表模板

日期：2026-07-29

用途：约束正式实验结果的写法、表格结构和图表逻辑。本文档不填虚构数字，只定义正式 held-out test 完成后应该如何组织证据。

## 1 结果章节总逻辑

结果章节应回答四个问题：

1. 在冻结四场景 suite 下，EA-RG-MAPPO 是否优于无图和单图 baseline？
2. 如果优于 baseline，优势主要体现在恢复概率、恢复时间、安全性还是通信效率？
3. 多关系图和角色对消息传播是否是优势来源，而不是 BC、奖励或训练预算造成的？
4. 方法在哪些场景、种子或指标下失效？

结果章节不要按实验执行时间写。建议按证据链写：

```text
Overall comparison
-> Relay-failure recovery process
-> Mechanism diagnostics
-> Ablations
-> Scenario-depth supplements
-> Failure modes
```

## 2 主结果表模板

表题建议：

```text
表 1 有限通信与中继失效条件下四种方法的正式 held-out test 结果
```

列结构：

| 方法 | Recovery ↑ | Delayed recovery ↑ | RMRT ↓ | Success ↑ | Timeout ↓ | Collision ↓ | 95% CI |
|---|---:|---:|---:|---:|---:|---:|---|
| MAPPO/no-graph | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Single-Graph MAPPO | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| HAPPO | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Parameter-Matched Single | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| EA-RG-MAPPO | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

表下注释必须说明：

- 所有方法使用相同 \(B^*\) 训练预算；
- checkpoint 由 validation 选择；
- test split 只运行一次；
- CI 来自 seed-aware hierarchical bootstrap；
- episode 不作为完全独立训练样本处理。

正文写法模板：

```text
在冻结四场景 suite 上，EA-RG-MAPPO 在 [主指标] 上达到 [数值]，相较于 [baseline] 的 [数值] 提高 [差值]，bootstrap 95% CI 为 [区间]。同时，其 collision rate 为 [数值]，说明恢复性能提升没有以安全性显著下降为代价。若某 baseline 在某指标上更优，需在同一段如实说明。
```

## 3 场景分解表模板

表题建议：

```text
表 2 不同中继失效时机下的任务链恢复率
```

| 方法 | Early | Standard | Delayed | Late | Mean | Worst |
|---|---:|---:|---:|---:|---:|---:|
| MAPPO/no-graph | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Single-Graph MAPPO | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| HAPPO | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| EA-RG-MAPPO | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

正文写法模板：

```text
场景分解结果显示，[场景名] 是最困难场景，所有方法恢复率均下降。EA-RG-MAPPO 的优势主要出现在 [场景]，而在 [场景] 与 [baseline] 接近。这说明方法优势集中在 [通信恢复/早期信息不足/后期链路保持] 条件下，而不是所有条件下无差别提升。
```

## 4 消融表模板

表题建议：

```text
表 3 多关系角色图关键组件消融
```

| 方法 | Recovery ↑ | Delayed recovery ↑ | RMRT ↓ | Collision ↓ | 结论 |
|---|---:|---:|---:|---:|---|
| Full EA-RG-MAPPO | [ ] | [ ] | [ ] | [ ] | 完整方法 |
| w/o Role-Pair Gate | [ ] | [ ] | [ ] | [ ] | 检验角色对消息传播 |
| w/o Task-Support Relation | [ ] | [ ] | [ ] | [ ] | 检验任务支援关系 |
| w/o Explicit Role Identity | [ ] | [ ] | [ ] | [ ] | 检验角色信息 |
| Parameter-Matched Single | [ ] | [ ] | [ ] | [ ] | 检验参数量解释 |

正文写法模板：

```text
移除 [模块] 后，[指标] 从 [数值] 下降到 [数值]，说明该模块对 [恢复概率/恢复速度/安全性] 有贡献。若下降很小或结果不稳定，则只能说明该模块在当前协议下贡献有限，不能作为强机制结论。
```

## 5 图 1：方法框架图

图题建议：

```text
图 1 EA-RG-MAPPO 的多关系角色图结构
```

必须包含：

- Scout、Relay、Attacker、Target；
- 感知关系；
- 通信关系；
- 任务支援关系；
- role-pair-conditioned message passing；
- centralized critic 与 decentralized actors 的信息边界。

图注模板：

```text
EA-RG-MAPPO 将异构无人机协同任务表示为多关系角色图。Actor 侧只使用局部观测和通过有效感知/通信获得的信息，critic 在训练阶段使用全局状态。感知关系、通信关系和任务支援关系分别编码目标信息来源、实际消息传递和任务链阶段依赖。
```

## 6 图 2：失效对齐恢复曲线

图题建议：

```text
图 2 中继失效后的任务链恢复过程
```

子图建议：

- A：Recovery probability after relay failure；
- B：Target tracking rate；
- C：Communication connectivity；
- D：Mean message age；
- E：Chain-closed probability。

正文写法模板：

```text
以中继失效时刻为 \(t=0\) 对齐后，EA-RG-MAPPO 在失效后 [时间范围] 内保持更高的 [tracking/connectivity/chain-closed]，并在 [时间范围] 内降低平均消息年龄。这表明其恢复优势不仅体现在 episode 终值，也体现在失效后的动态恢复过程。
```

## 7 图 3：逐 seed 散点和置信区间

图题建议：

```text
图 3 五个训练种子下的恢复率分布
```

要求：

- 每个 seed 一个点；
- 显示均值；
- 显示 95% CI；
- 使用 paired difference 子图更好。

正文写法模板：

```text
逐 seed 结果显示，EA-RG-MAPPO 在 [x/5] 个训练种子上优于 [baseline]。均值差为 [数值]，95% CI 为 [区间]。该结果说明 [稳定优势/优势主要来自部分 seed/seed 方差仍较大]。
```

## 8 图 4：代表性案例

图题建议：

```text
图 4 预定义代表性 episode 中的任务链恢复过程
```

选择规则：

不要挑差距最大案例。建议选：

```text
方法差值接近总体中位数、初始条件相同、能够体现典型恢复过程的 matched episode。
```

图中应包含：

- 三维轨迹；
- 中继失效时刻；
- 目标跟踪状态；
- 通信链是否可达；
- 攻击窗口是否形成；
- 消息年龄时间轴。

## 9 图 5：机制或消融图

可选方案：

- relation attention before/after failure；
- role-pair gate 分布；
- w/o task-support 后恢复率变化；
- parameter-matched single 与 full EA 对比。

图注必须避免过度解释。可以写：

```text
该图显示 full EA-RG-MAPPO 在失效后更频繁激活 [关系]，与其更高的恢复率一致。
```

不要写：

```text
该图证明模型理解了杀伤链机制。
```

## 10 结果章节禁止写法

不要写：

```text
本文方法全面优于所有 baseline。
本文方法证明了完整空战任务链闭合能力。
所有场景下均表现最优。
attention 可视化证明模型具有可解释智能。
```

建议写：

```text
在冻结的有限通信与中继失效 suite 中，EA-RG-MAPPO 在 [指标] 上相较于 [baseline] 表现更好；该优势主要体现在 [场景/阶段]，并受到 [限制] 约束。
```

## 11 数据填充顺序

正式结果出来后，按以下顺序填：

1. 先填主结果表；
2. 再填场景分解表；
3. 再填 seed-aware CI；
4. 再生成故障对齐曲线；
5. 再选代表性案例；
6. 最后写 Discussion 和 Conclusion。

不要先写结论再倒推结果解释。
