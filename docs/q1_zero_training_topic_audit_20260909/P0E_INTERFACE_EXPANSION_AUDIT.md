# P0E：接口扩展候选审查

**裁决：** `P0E_NO_GO_FOR_THREE_INTUITIVE_EXTENSIONS`

## 1. 在线角色重分配

### 科学吸引力

故障后重新分配侦察、中继和终端任务，比被动执行固定角色更接近“恢复协同能力”的问题。

### 仓库与语义约束

- `envs/uav_intercept_3d_env.py` 中角色同时决定传感、通信、攻击能力和 role-specific reward；直接交换角色会改变飞行器能力模型和奖励，而不只是增加一个决策变量。
- `configs/b_line_p1_formal_problem_novelty_freeze.json` 已明确记录 relay control 缺失，并禁止把 relay reassignment 误写为原生变量。
- 多 UAV task allocation、角色分配和轨迹联合优化已有密集工作。仅增加 assignment head 不足以形成强二区创新。

### 决策

`NO_GO_SEMANTIC_REWRITE_AND_CROWDED`。

## 2. 任务—通信联合决策

### 科学吸引力

让通信对象、relay selection 或发送时机成为预算约束动作，可以把拓扑故障从外生扰动变成可控恢复问题。

### 仓库与历史约束

- 当前 `ACTION3D_TABLE` 只承载飞行/任务动作，消息由环境根据可达性自动传递。
- B-line/C-line 已对 sensing-routing-service reconfiguration 做过形式化、反例和 23 篇近邻审查。
- `docs/q1_zero_training_topic_audit_20260908/c0r/C0R_RESULT.json` 的结论为 `C0R_NO_GO`：近邻覆盖强、无非通用理论靶点、当前接口没有 transition-effective routing/relay/capacity action。

### 决策

`NO_GO_PREVIOUSLY_FALSIFIED`。

## 3. 隐故障信念与信息获取

### 科学吸引力

不直接暴露故障身份时，策略需要从合法观测历史推断通信状态，并在任务行为与信息获取之间权衡。

### 仓库与最近邻约束

- 当前 `graph_obs` 直接包含实时 `comm`、`active_support` 与 `relation_adj`；建立隐故障问题必须更改 observation contract。
- TATG 已以“当前快照不足、合法历史是否携带拓扑转变信息”为核心，完成 P1 信息缺口、公式、实现、序列 PPO 与 pilot 基础设施。belief encoder 或 history state 会与这条路线直接重合。
- 部分可观测 MARL 已有 Bayesian belief、attention recurrence、state modelling 和 information-seeking reward 等成熟邻域。

### 决策

`NO_GO_TATG_OVERLAP_AND_OBSERVATION_REWRITE`。

## 综合判断

三个直觉上的接口扩展都不能同时满足：

1. 与仓库历史不重合；
2. 只需小幅改动；
3. 存在清晰、可识别的新决策对象；
4. 文献中没有近乎直接的成熟邻域；
5. 可在有限训练预算下完成强证据。

因此 P0E 不授权环境实现、算法编码或训练。

