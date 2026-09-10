# P8D ACFID 学习型 pilot 形式化

## 关键决定

ACFID 不直接嵌入旧 6-UAV MAPPO 的 centralized state-value critic。原因是该 critic 只估计状态基线；即使把故障交互写入 critic，也不能保证执行期恢复动作具有组合泛化能力。

学习系统冻结为两层：

1. 底层：六架异构 UAV 的角色控制与连续/离散任务执行，所有方法共用且固定；
2. 高层：在故障检测后，根据因果可得任务上下文与 primitive degradation signatures 选择团队恢复选项。

因此论文对象是“异构多 UAV 团队的组合故障恢复策略”，而不是把新的 value head 冒充传统 MAPPO actor 改进。

## 三个方法

### Direct fault-aware policy

把固定故障注册表和任务上下文展平输入 MLP。它允许普通神经网络自行学习组合，但没有显式组合归纳偏置。

### Additive policy

动作 logits 由基础项与所有激活 primitive fault 的共享主效应相加：

\[
z(s,F)=z_0(s)+\sum_{i\in F}z_i(s,f_i).
\]

### ACFID

在 additive 上加入共享 pair interaction：

\[
z(s,F)=z_0(s)+\sum_{i\in F}z_i(s,f_i)
+\sum_{\{i,j\}\subseteq F}z_{ij}(s,f_i,f_j,r_{ij}).
\]

其中 `r_ij` 是预注册、因果可得的任务依赖关系描述；pair head 不使用故障对 ID lookup，因此未见 pair 不对应未训练参数。

## 公平性

冻结宽度下的可训练参数：

| 方法 | hidden | 参数量 |
|---|---:|---:|
| Direct fault-aware | 100 | 15,005 |
| Additive | 81 | 15,157 |
| ACFID | 64 | 15,119 |

最大差距约 1.01%。三者输出相同五类恢复动作，使用相同底层控制器、环境、奖励、优化器、训练组合、步数和评价 tape。

## 已验证静态性质

- ACFID 对 primitive-fault 注册顺序置换不敏感；
- 0 或 1 个激活故障时 interaction head 不生效；
- 三种模型输出完全相同的动作空间形状；
- 三种模型参数容量在冻结容差内。

## 尚未授权训练的原因

当前宏观反事实 P0 还不是具有标准 `reset/step` 时序、底层任务执行和可学习奖励的 pilot 环境。下一门必须确认：

1. 正常与单故障任务可学习但不饱和；
2. 五类恢复动作都在部分状态下具有最优区域；
3. 故障信息只在检测后出现，且没有组合标签或未来泄漏；
4. train/validation/test 组合支持在环境采样器层强制隔离；
5. 固定底层控制器不会使高层动作失去实际效果。

通过后才生成云端训练包。
