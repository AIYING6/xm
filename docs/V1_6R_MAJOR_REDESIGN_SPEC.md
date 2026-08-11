# v1.6R：严格信息边界下的证据融合与物理中和

状态：`V1_6R_MAJOR_SCIENTIFIC_AND_ALGORITHMIC_REDESIGN_PROPOSED`

日期：2026-08-11

## 1. 决策

v1.6R 不是旧 v1.6 的小修复，也不继承旧 checkpoint、旧 recovery 终点或旧 headline。它是一次科学问题、信息边界、任务终点和算法接口同时重构的新版本。旧实现作为工程资产和失败案例归档；所有 v1.6R 正式数字从新的冻结协议重新产生。

当前停止：旧版 salvage qualification、旧 recovery 线、task-chain 主终点、全局 actor graph。当前不进入正式训练，先完成 R0 规格冻结。

## 2. 研究问题

在严格 recipient-specific 信息约束下，同一目标的当前本地感知、已送达通信和带年龄的合法缓存可能具有不同新鲜度、可信度和传播来源。核心问题是：

> 保留这些合法证据的来源、时效和关系身份，是否比过早压缩为单一目标状态，更能支持异构 UAV 将证据转化为物理攻击范围获取和最终中和？

这不是“通信越多越好”或“图网络必然优于统一网络”的预设；统一图基线可能胜出，结果必须由配对实验决定。

## 3. 可复用资产与永久删除项

### 直接复用

- 3DOF UAV/目标动力学、Scout/Relay/Attacker 角色和任务分布；
- 通信范围、丢包、延迟、packet/cache/age/confidence 基础设施；
- strict actor-contract 检查、recipient-specific observation、信息来源审计；
- continuous guidance action、role-specific action heads、MAPPO/HAPPO 训练框架；
- neutralization evaluator、RMTN、attack-range acquisition 和失败阶段诊断；
- checkpoint、配置 hash、paired evaluation、bootstrap/seed-aware 统计工具。

### 继承思想但必须重验/重实现

- relation-specific encoder、edge-aware message passing、角色异质性建模；
- graph adapter 与通信 provenance 字段；
- 旧测试脚本只能作为回归工具，不能自动成为 v1.6R 证据。

### v1.6R 永久删除

- recovery/chain-closed 作为主成功终点；
- `engage_commit` 作为成功按钮；
- 9-action 离散 guidance；
- global-ish actor graph、全局 `last_detected_target`、共享全局目标变量；
- Task-Support relation（若不能证明独立信息来源）；
- 旧 v1.6 checkpoint、旧 recovery headline 和未通过严格 actor contract 的数字。

## 4. 任务与终点冻结草案

保留 Scout/Relay/Attacker 与机动目标。任务成功只定义为：真实运动状态满足攻击几何并连续保持 4 个环境 transition 后自动发生 `NEUTRALIZED`。不再由通信图、chain、engagement-ready 或按钮直接判成功。

主终点：

- Mission Success@H = `NEUTRALIZED` 比例；
- RMTN_H = neutralization 时间，未中和为 H；
- `P(attack-range acquisition | legal target evidence)`；
- evidence-to-range latency；
- `NO_ATTACK_RANGE_ACQUISITION`、collision、constraint failure、escape、timeout 的互斥分类。

同一步发生 neutralization 与 collision/constraint failure 时，failure precedence 保持优先。H、4-step hold、终止优先级和 evaluator 在训练前冻结。

## 5. 严格 actor information contract

对 recipient (i)，执行期目标信息只能来自：

1. 当前合法 local sensing；
2. 实际 delivered 且仍在有效年龄内的 packet/cache。

禁止 actor 使用 global truth、`last_detected_target`、pending/dropped/expired payload、evaluator geometry、其他 agent 状态、全局 adjacency 或 privileged critic state。critic 可在训练期使用明确声明的 share-observation，但任何字段不得回流 actor。

缓存过期必须同时清除显式 target evidence 和相关 temporal hidden state；collector、replay buffer、episode reset 都必须通过同一语义。任何绕过 expiry 的隐式记忆均判为 NO-GO。

架构边界固定为：

```text
Environment → LegalObservationInterface
            → RecipientSpecificGraphBuilder
            → Actor / Centralized Critic
```

GraphBuilder 只接收 LegalObservationInterface 输出，不能直接访问环境状态。

## 6. 候选主方法（未完成新颖性裁决）

工作名：**TEAR-MAPPO**（Temporal Evidence Alignment and Relational MAPPO）。这里的“候选”不是已证明创新，必须通过 R0 机制和近邻审查。

### 6.1 Recipient-specific relational graph

每个 actor 独立构图。节点/边只代表该 recipient 合法看到的 local sensing 或 delivered/cache-valid communication evidence。节点/边附带 role/capability、age、confidence、sender/provenance。不存在由环境预先提供的全局图。

### 6.2 Temporal Evidence Alignment

将带 generation time 的 packet evidence 映射到当前决策时刻的 latent 表征，显式输入 age/validity；不创造缺失信息，也不把过期包重新激活。

### 6.3 Conflict-aware relation fusion

感知证据与通信证据先分开编码，再根据合法的 disagreement、age、confidence、role/provenance 进行融合。融合权重必须可记录，用于机制审计；不能只报告最终成功率。

role-specific heads 仅作为异构动作语义的透明工程配置，不单独宣称算法创新。

## 7. 公平基线与消融

所有方法获得完全相同的合法原始证据、历史窗口、动作空间、reward、critic、训练预算和评估 seeds。

- B0：flat legal-info MAPPO；
- B1：同历史窗口的 GRU-MAPPO；
- B2：统一实体/统一图编码 MAPPO（保留 age/provenance 字段）；
- B3：relation encoder，无 temporal alignment；
- Full：TEAR-MAPPO；
- 可选 HAPPO 作为训练范式对照，不作为主创新。

必须报告参数量、FLOPs/rollout 开销和输入字段清单。关键消融：去掉 temporal alignment、去掉 conflict fusion、统一 relation、去掉 age/provenance。任何 Full 额外获得的字段都判比较无效。

## 8. 场景与协议

- S0：可靠通信，验证基础可学习性；
- S1：受限范围 + 丢包，验证合法间歇证据；
- S2：真实 Scout→Relay→Attacker 路径 + stale evidence，验证 relay provenance；
- OOD：更高 delay 与未见过的目标机动，仅用于泛化，不用于挑选方法。

开发阶段只用 2 个预冻结 seeds；通过后正式使用 6–8 个训练 seeds、固定 untouched evaluation population、seed 作为最高层 resampling 单位，并报告 bootstrap CI。不同 difficulty level 的均值差不能直接写成因果效应。

## 9. R0→正式实验门

### R0：规格冻结

冻结 mission physics、actor contract、graph schema、证据 provenance、age 语义、终点、baseline、消融和统计协议。输出字段级 schema 与配置 hash。

### R1：实现与确定性回归

必须通过：actor-boundary、packet/cache expiry、recipient graph legality、continuous-action、neutralization precedence、graph provenance、collector hidden-state reset。新增环境或适配器必须先有 smoke test。

### R2：透明 baseline learnability

只跑 B0/B1/B2 的小规模 development。若严格合法 baseline 连 S0 都不可学，先修 benchmark，不进入方法训练。

### M0：TEAR 最小实现与 pilot

只实现上述两项机制，不添加 attention、world model、auxiliary loss、new reward 或通信协议。Full 与最强匹配基线的唯一实质差异必须可审计。

### Formal：正式多 seed

只有 pilot 同时满足 acquisition 机制指标方向一致、无信息泄漏、无明显 action collapse，才授权正式 6–8 seed。若 pilot 为 partial/no-go，只能分析已有轨迹或关闭该机制，不得靠加 seed/加 updates 救结果。

## 10. Kill conditions 与证据政策

以下任一项出现即停止 TEAR 主线：

- 多证据共存在关键 acquisition 窗口近乎不存在；
- unified/set encoder 可无损等价表示 Full 的全部决策相关信息；
- Full/Baseline 输入或容量不匹配；
- hidden state 绕过 packet/cache expiry；
- Full 只提高最终 reward，不改善预注册 acquisition 机制指标；
- 结果仅由单 seed 或 post-hoc endpoint 选择支持。

旧 v1.6 和之前实验保留为 legacy audit/engineering history，不并入 v1.6R 的正式性能表。论文只引用从严格 v1.6R freeze 之后产生、带配置 hash、来源和回归记录的结果。

## 11. 当前下一步

1. 先提交 R0 文档与字段/schema 清单；
2. 停止旧 salvage/旧训练启动；
3. 实现 R1 的 LegalObservationInterface 与 RecipientSpecificGraphBuilder；
4. 通过回归后再做 B0/B1/B2 小规模 learnability；
5. 未完成 R1/R2 前不实现 TEAR、不租正式训练资源、不写正式论文结论。

这条路线的原则是：复用工程，重建证据；复用失败经验，删除旧叙事；只允许一次结构性修复，不再进行无限 v1.6.x 试错。
