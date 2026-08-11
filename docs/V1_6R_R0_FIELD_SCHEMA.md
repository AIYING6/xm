# v1.6R R0 字段与来源冻结清单

状态：`R0_SCHEMA_DRAFT__NO_TRAINING`

本清单把 v1.6R 的合法信息边界落到字段级。任何 actor 输入必须能追溯到下表中的来源；未列字段不得直接进入 actor。

## Actor 可用字段

| 类别 | 字段 | 合法来源 | 失效规则 |
|---|---|---|---|
| self | 自身位置、速度、航向、爬升角、role/capability | 当前 agent 自身状态 | episode reset 清零/重置 |
| local_target | 相对位置、相对速度、LOS/几何误差 | 当前合法 local sensing | radar 不可见立即无效 |
| packet_target | 目标状态、sender、path、generation/delivery step | 实际 delivered packet | 丢弃、pending、未送达不得进入 |
| cache_target | 最近合法 packet 的状态 | valid cache | age 超限或 confidence 不足立即失效 |
| provenance | source role、hop/path、direct/relayed、age、confidence | packet/cache 元数据 | 随对应 evidence 一起失效 |
| interaction | 其他 agent 的合法消息/可见状态 | 当前 local sensing 或 delivered packet | 不得读取全局 agent state |

## Actor 禁止字段

`last_detected_target`、真实 target state、evaluator geometry、全局 adjacency、其他 agent 私有 sensing、pending/dropped/expired payload、critic share-observation、终点标签、未来状态。

## 时间语义

- generation step：证据产生时刻；
- delivery step：recipient 实际收到时刻；
- age：当前 step − generation step；
- valid：delivery 已发生、age 未超限、confidence 达标；
- expiry：显式证据、provenance 和相关 hidden state 同时清除；
- reset：episode reset 必须清除所有 target-related hidden state 和 cache。

## GraphBuilder 契约

`RecipientSpecificGraphBuilder` 的输入只能是 `LegalObservationInterface` 输出。每个 recipient 独立构图；graph 中只允许当前合法 evidence 对应的节点/边。Task-Support 或由环境预构造的全局关系不进入 v1.6R 主图。

## R1 必须通过的确定性测试

1. 无 sensing、无 delivered packet、无 valid cache 时，改变 global target truth 不改变 actor 输入；
2. 合法 local sensing 能更新对应 actor 输入；
3. 合法 packet 能更新 recipient 输入且 sender/path 正确；
4. expired cache 不进入 actor；
5. expiry 同步清除 temporal hidden state；
6. recipient A 的私有证据不出现在 recipient B；
7. graph relation 与 provenance 一一对应；
8. neutralization/failure precedence 不变；
9. continuous action 与现有 PPO log-prob 接口一致；
10. reset 后 cache、graph、hidden state 完全复位。

通过前不启动 baseline 或 TEAR 训练。
