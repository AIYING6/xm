# P2：Latent Agent-Scoped Uncertainty 现象审计协议

状态：`P2_PHENOMENON_AUDIT_PROTOCOL_FROZEN__NO_ALGORITHM__NO_UAV_MODIFICATION`

## 目的

在实现任何新算法前，使用标准 cooperative MARL 基准验证：执行期不可直接观测、且随时间变化的受影响 agent scope，是否会造成可重复的协同退化，并且不能被静态鲁棒策略或单一全局 mask 等价消除。

## 基准范围

只允许使用两个标准风格的连续协作任务：

1. 三智能体粒子协作导航（MPE/Particle 风格）；
2. 三智能体连续协作覆盖或编队任务（与导航不同的动力学/奖励结构）。

不加入 UAV 专有的 sensing、Relay、neutralization 或自定义通信语义。若第二个任务无法在现有依赖中以透明方式实现，则 P2 直接判定为 `NO_GO`，不得用 UAV 任务替代。

## 预注册场景

- `nominal`：所有 agent 正常；
- `single_scope`：固定时段只影响一个 agent 的 observation 或 actuation；
- `switching_scope`：在冻结时刻将受影响 agent 从一个 agent 切换到另一个 agent；
- `correlated_scope`：同时影响具有协作依赖的 agent 子集。

scope、modality、severity、切换时刻和随机种子在审计前冻结。actor 只能使用自身 observation/action history；scope truth 只能用于 oracle、审计标注或训练期诊断，不能进入执行策略。

## 只读对照

- `scope_oracle`：允许读取真实 scope，仅作为可达性上界；
- `static_robust`：不读取 scope，使用单一固定鲁棒策略；
- `local_history`：只使用合法局部历史；
- `scope_mask_control`：只提供一个静态 capability/uncertainty mask，检验简单 mask 是否已经足够；
- paired counterfactual：保持物理状态、动作和随机数一致，只切换隐藏 scope。

本阶段不训练新算法；如果必须运行已有 baseline，只允许使用预先冻结的透明实现，不得调参追求退化或恢复。

## 主要证据

必须同时报告：

- scope 改变前后最优协同行为是否改变；
- local history 与 scope oracle 的性能差距；
- switching-scope 相对 nominal/static-robust 的任务退化；
- scope-mask 是否可以规则级等价解决；
- 不同 benchmark、不同 scope 轨迹下现象是否重复；
- scope inference delay 与任务失败阶段的关系。

## 裁决

### PASS

两个标准任务均满足：隐藏 scope 真实改变最优协同行为；局部历史有不完整但可测证据；scope oracle 可达而 static/local-history 明显退化；静态 mask 不能等价恢复；paired counterfactual 可重复。状态更新为：

`P2_PHENOMENON_AUDIT_PASS__READY_FOR_MINIMAL_ALGORITHM_DESIGN`

### PARTIAL

现象只在一个任务成立、或 scope-mask 已能大部分等价解决、或局部证据与 oracle 差异不稳定。状态更新为：

`P2_PARTIAL__PHENOMENON_NOT_GENERAL_OR_MECHANISM_SPACE_UNCLEAR`

不得直接设计算法；仅允许一次问题定义复核。

### NO-GO

若 scope 只改变难度而不改变最优协同行为，或现象可由普通 domain randomization/adversarial training/static mask 解释，或无法在两个标准任务复现，则：

`P2_NO_GO__LATENT_SCOPE_PROBLEM_NOT_IDENTIFIABLE`

关闭该候选，不回到旧 UAV 平台继续制造现象。
