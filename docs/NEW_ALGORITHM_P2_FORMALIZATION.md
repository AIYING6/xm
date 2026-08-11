# P2：Latent Agent-Scoped Uncertainty 形式化

状态：`P2_FORMALIZATION_AUTHORIZED__NO_CODE__NO_TRAINING`

## 研究问题

在 cooperative partially observable Markov game 中，部署期存在一个随时间变化的隐变量：当前哪一组 agent、哪一种信息/动力学通道受到不确定性影响。每个 agent 只能根据自身合法历史推断与自身相关的局部证据，团队仍需完成共同任务。

## 数学对象

基础状态为 `s_t`，联合动作为 `a_t`，局部历史为：

```text
h_i^t = (o_i^0, a_i^0, ..., o_i^t)
```

每一步存在 scope variable：

```text
z_t = (U_t, m_t, ξ_t)
```

其中：

- `U_t ⊆ {1,...,N}` 是受影响 agent 子集；
- `m_t` 是 uncertainty modality，例如 sensing、actuation 或 communication；
- `ξ_t` 是该 modality 的 severity/realization。

观测与转移写为：

```text
o_i^{t+1} ~ O_i(· | s_{t+1}, z_t, i)
s_{t+1} ~ T(· | s_t, a_t, z_t)
```

执行期 actor 只能使用 `h_i^t`，不能直接读取 `z_t`、其他 agent 的受影响状态或全局 uncertainty truth。训练 critic 若读取 `z_t`，必须明确标记为 training-only privileged input，且不得回流 actor。

## 与近邻的区分

### 不是固定 agent-specific uncertainty set

固定 uncertainty set 允许每个 agent 有不同不确定性范围，但不要求 episode 内 `U_t` 变化，也不要求 actor 在线识别当前 scope。

### 不是普通 adversarial targeting

若 adversary 直接知道并选择攻击 agent，且 agent policy 只需对预先给定 adversary distribution 鲁棒，则不构成 P2。P2 要求 scope realization 对执行期 actor 是隐变量，并且局部证据对不同 agent 不完整。

### 不是普通 POMDP belief reconstruction

若方法只学习完整 latent state/belief，再将其输入策略，P2 可能退化为已有 belief-MARL。P2 只有在“scope 的 agent-subset 结构改变联合责任/协同策略，且局部 posterior 之间存在不一致”时才保留。

## 标准 benchmark 现象审计

不写新算法，先构造最小 3-agent cooperative benchmark（基于标准 particle/MPE 风格连续协作任务），只加入一个明确的 scope variable：

1. nominal：所有 agent 正常；
2. single-scope：随机只影响一个 agent 的 sensing 或 actuation；
3. switching-scope：episode 内 `U_t` 在预冻结时刻切换；
4. correlated-scope：影响具有协同依赖的 agent 子集。

只做规则/反事实审计：

- scope oracle controller；
- static robust controller；
- local-history controller；
- same physical state with different hidden scope；
- scope removal counterfactual。

## PASS 条件

只有同时满足以下条件，P2 才进入算法设计：

1. hidden scope 在不改变 nominal task 的前提下真实改变最优协同行为；
2. local history 对 scope 存在不完整但可测的证据；
3. scope oracle 能完成任务，固定/static robust policy 在 switching-scope 下明显退化；
4. 只给一个 capability mask 或全局 scope flag 就能解决的情况不算 PASS；
5. phenomenon 在至少两个标准 cooperative benchmark/任务变体中重复；
6. 现象不依赖 UAV 特有的 sensing、Relay 或 neutralization 语义。

## 硬 NO-GO

- scope 只改变 reward/难度，不改变最优协同行为；
- scope 可以由一个静态 mask 唯一推导；
- local-history policy 与 scope-oracle policy 无明显差异；
- phenomenon 只是普通 domain randomization 或 adversarial training；
- 只在自定义 UAV 环境中出现；
- 无法在标准 benchmark 中建立稳定反事实差异。

通过后才进入：

```text
P2_PHENOMENON_AUDIT_PASS__READY_FOR_MINIMAL_ALGORITHM_DESIGN
```
