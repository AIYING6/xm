# P38 内生可行集协同：近邻审查 STOP

## 审查对象

P38 拟考察一个体的行动如何改变其他个体后续可执行的任务集合，并将此称为“内生
可行集协同”。本轮仅进行了文献近邻审查；没有环境、方法或训练。

## 正面命中

- Dynamic Q-value Coordination Graph 已用动态协调图刻画协作 MARL 中随状态变化的
  交互结构；
- Coordination Graphs for Constrained MARL 直接处理耦合约束、联合可行性与去中心化
  协调；
- Dual Collaborative Constraints 以显式协作约束识别动态子任务并协调局部/全局行动。

这些工作不只是共享“约束”词汇，而是已覆盖 P38 试图使用的优化对象：由团队耦合
产生的动态可行行动集合。

## 决策

`P38_STOP_BEFORE_TASK_DESIGN`。

不应把 action availability、feasibility shaping、constraint-aware coordination 或
dynamic feasible-set graph 作为新方法名称重新启动。若未来有候选，它必须提供一个
不等同于“约束图上的协调”的新可识别量，并在开始环境实现前给出对应的反事实与
最强近邻差异。

## 参考锚点

- Siu et al., Dynamic Coordination Graph for Cooperative MARL:
  <https://proceedings.mlr.press/v157/siu21a.html>.
- Amaya-Corredor et al., Coordination Graphs for Constrained MARL:
  <https://arxiv.org/abs/2606.02337>.
- Coordinating MARL via Dual Collaborative Constraints:
  <https://www.sciencedirect.com/science/article/pii/S0893608024007822>.
