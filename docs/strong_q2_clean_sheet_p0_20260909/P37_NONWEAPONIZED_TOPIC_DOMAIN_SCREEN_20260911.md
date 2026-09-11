# P37 非武器化新问题域：宽主题初筛

## 目的

在 P35/P36 停止后，项目转向非武器化的 UAV/多机器人问题域。本审查只决定
哪些**宽主题不能直接作为论文选题**；不评价其中任何单篇工作，也不授权环境或训练。

## 筛选标准

一个宽主题只有同时能给出独立优化对象、不能由固定规则解决的决策缺口、可受控的
方法消融，才可进入候选卡。仅有现实重要性、UAV 场景或“使用 MARL”均不够。

## 检索到的直接近邻与裁决

| 宽主题 | 直接近邻 | 裁决 |
|---|---|---|
| 人机监督下的多 UAV 协同授权 | IJCAI 2015 已研究人机混合主动式多 UAV 任务分配；近期工作还讨论多操作者监督编组 | `STOP_AS_BROAD_TOPIC` |
| 可验证/安全的机器人团队学习 | 安全多机器人学习已覆盖屏蔽、CBF、预测安全过滤器、可验证学习控制与 MARL 安全约束 | `STOP_AS_BROAD_TOPIC` |
| 多模态具身 UAV 闭环 | 受限感知、共享自主、视觉闭环 UAV 控制与多 UAV 动态任务决策均已有直接研究 | `STOP_AS_BROAD_TOPIC` |

## 结论

不能以“人机协同”“可验证安全”或“多模态闭环”本身作为新项目题目；这样会把一个
成熟研究域误写成问题空白。

下一轮候选必须从一个**可枚举的反事实**出发，而不是从应用词汇出发：在同一局部
信息下，至少两种可行动作必须造成不同的未来可行集，并且固定规则、标准记忆策略和
集中式信息上界在训练前就能被设计为可区分对照。若做不到这一点，即使主题热门，也
不进入开发。

## 文献锚点

- Ramchurn et al., human-agent collaboration for multi-UAV dynamic task
  allocation: <https://eprints.soton.ac.uk/377185/>.
- Chen and Ma, multi-operator UAV swarm supervisory control:
  <https://doi.org/10.1016/j.ergon.2026.103981>.
- Panagou et al., learning safe control for multi-robot systems:
  <https://doi.org/10.1016/j.arcontrol.2024.100948>.
- Reddy et al., shared autonomy via deep reinforcement learning:
  <https://roboticsproceedings.org/rss14/p05.pdf>.
