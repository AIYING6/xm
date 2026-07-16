# 3DOF 实验写作说明

日期：2026-07-16

## 写作定位

当前 3DOF 结果可以支撑一个较清晰的论文实验主线：

```text
在有限通信、间歇感知和临时通信节点失效条件下，多关系角色图能够提高异构无人机协同杀伤链的故障后恢复能力。
```

这条主线比“普通多机追逃成功率更高”更适合二区论文，因为它强调：

- 任务链条：发现、通信、支援、攻击窗口；
- 平台异构：侦察、通信中继、攻击能力不同；
- 拓扑扰动：中继节点失效、通信 dropout、时延、雷达 dropout；
- 机制解释：任务支援关系和角色对消息门控；
- 场景深度：严格感知模式下不再向策略注入未探测目标真值。

## 可以作为主结论的结果

### 1. Relay failure 恢复能力

这是当前最稳的主结论。

正式节点失效评估中：

```text
single recovery = 92.2%
multi recovery  = 100.0%
delta = +7.8 pp, 95% CI [+2.2, +13.3]

single recovery steps = 21.8
multi recovery steps  = 5.6
delta = -16.2, 95% CI [-28.0, -4.5]
```

建议写法：

```text
在中继节点通信失效场景下，多关系角色图显著提高了杀伤链恢复概率，并缩短了恢复时间。
```

不要写成：

```text
所有节点失效场景下均显著优于单关系图。
```

因为 scout failure 只是正向趋势。

### 2. 任务支援关系消融

这是当前最强的机制证据。

去除 `task_support` 后：

```text
relay failure: success/recovery delta = +11.1 pp, CI [+5.6, +17.8]
recovery steps delta = -23.5, CI [-37.7, -11.6]

scout failure: success/recovery delta = +8.9 pp, CI [+3.3, +15.6]
recovery steps delta = -18.8, CI [-32.9, -7.0]
```

建议写法：

```text
动态任务支援关系不是简单增加图边，而是直接影响侦察、通信中继和攻击平台之间的杀伤链恢复。
```

### 3. 角色对消息门控消融

这是第二层机制证据。

去除 `role_pair_gate` 后：

```text
relay failure: recovery delta = +4.4 pp, CI [+1.1, +8.9]
recovery steps delta = -9.8, CI [-19.2, -2.7]
```

建议写法：

```text
不同角色对之间使用条件化消息传递比共享消息权重更适合 relay failure 恢复。
```

不要把 scout failure 写成显著结果，因为其 CI 穿零。

## 可以作为场景深度增强的结果

### Strict sensing relay failure

严格感知模式下，未探测目标前不再把真实目标位置注入局部观测、共享观测和图目标节点。

10-update strict-sensing fine-tuning pilot 后：

```text
relay failure:
single recovery = 71.1%
multi recovery  = 96.7%
delta = +25.6 pp, CI [+15.6, +36.7]

single recovery steps = 67.5
multi recovery steps  = 13.6
delta = -53.9, CI [-75.3, -32.6]
```

建议写法：

```text
在更严格的间歇感知设置下，中继失效场景的恢复优势仍然存在，说明该方法不是依赖目标真值泄漏获得结果。
```

必须标注：

```text
该结果来自 10-update strict-sensing fine-tuning pilot。
```

不要写成完整正式预算结果，除非后续重新跑更长 strict-sensing fine-tuning。

## 只能作为趋势或边界的结果

以下结果不能作为主结论：

- scout failure：多数结果为正向，但置信区间穿零；
- dropout、delay、radar perturbation：有正向趋势，但不够强；
- range 0.75：混合结果；
- break-turn/weaving target：能区分方法，但绝对成功率太低；
- oracle geometric pursuit：使用模拟器目标真值，只能作为任务可解性和难度参考；
- no_edge_features：当前信号弱；
- no_role_identity：relay 有一定结果，scout 混合，只能辅助。

## 推荐实验章节结构

建议按以下顺序写：

1. 3DOF 异构协同拦截任务与杀伤链指标；
2. 训练协议：BC warm start、PPO fine-tuning、拓扑课程；
3. 主结果：relay failure 恢复；
4. 鲁棒性趋势：dropout、delay、radar、scout failure；
5. 机制消融：no_task_support 和 no_role_pair_gate；
6. 严格感知场景深度实验；
7. relay failure 典型案例回放；
8. 局限性：非 4v2、非 6DOF、非在线导弹、strict sensing 仍是 pilot budget。

## 一句话总结

当前最适合投稿写法不是“我们做了很多实验”，而是：

```text
我们构建了一个 3DOF 异构无人机杀伤链恢复任务，并证明多关系角色图在中继通信失效和严格间歇感知条件下能够显著提升杀伤链恢复能力；消融实验进一步说明任务支援关系和角色对消息门控是主要机制来源。
```
