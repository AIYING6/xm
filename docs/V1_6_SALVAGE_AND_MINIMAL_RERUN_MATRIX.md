# v1.6 论文抢救与最小重跑矩阵

状态：`V1_6_SCIENTIFIC_RECOVERY_AUTHORIZED__MINIMAL_RETRAINING__PAPER_FIRST`

日期：2026-08-11

目标：停止所有新算法/新 benchmark 挖掘，把 v1.6 重新收束成一篇可投稿的 EA-RG 异构 UAV 受限通信 MARL 论文。

## 1. 资产分类

| 资产/结论 | 当前处理 | 是否重跑 |
|---|---|---:|
| 3DOF/异构 UAV 环境与动力学 | 直接保留；不改旧证据链 | 否 |
| Scout/Relay/Attacker 角色与通信 range/loss/delay | 作为任务基础设施保留；论文中只写实际验证过的语义 | 否，先做语义清点 |
| packet/cache/age/provenance 工具 | 直接保留，并作为 actor 合约实现基础 | 否，做回归 |
| MAPPO/HAPPO 训练框架与 checkpoint 管线 | 直接保留 | 否 |
| EA-RG relation-specific encoder / graph 代码 | 算法主体保留，重新核对输入图构造 | 否，先做接口回归 |
| 原 977-update checkpoints | 仅开发/探索证据；不能作为严格公平主结果 | 否 |
| 旧 global-ish actor graph 或未满足 recipient-specific 合约的结果 | 从正式证据中删除 | 不适用 |
| 旧 recovery headline | 删除或改写；不能继续声称“故障前已建立链条后的恢复” | 不一定重训 |
| robustness/多半 ablation/可视化 | 主结果稳定后择要复用 | 暂不重跑 |

## 2. 论文语义修正

### 必须删除

没有证明 failure 前任务链已经成立时，不使用：

> recovery after disruption / recovery of an established task chain

### 可审慎保留的候选表述

根据重跑结果二选一：

1. `failure-exposed heterogeneous coordination under constrained communication`；
2. `task-chain establishment and physical mission completion under constrained communication`。

“recovery”只能在新的 protocol 明确记录 pre-failure established chain、failure-induced break 和 post-failure restoration 后使用；本矩阵不授权重新制造该终点。

## 3. actor 合约修复门

在任何正式重训前，必须通过：

1. actor 只能使用当前合法 local sensing 或 delivered/cache-valid packet；
2. global `last_detected_target` 等旁路不能改变 actor observation；
3. dropped、pending、expired payload 不能进入 actor；
4. critic privileged state 不得流入 actor；
5. EA-RG、strong single-graph 和 MAPPO 的 actor 输入边界逐方法一致；
6. 原 actor-boundary/continuous-action/role-head 回归全部通过。

这一步是必须修复的科学缺陷，不是可由文字解释消除的限制。

## 4. 最小重跑方案（只做资格判断，不立即启动）

### 4.1 Development qualification

固定一个 primary scenario、同一 evaluation population、同一 reward/episode horizon，比较四个方法：

1. EA-RG（proposed）；
2. vanilla MAPPO；
3. HAPPO；
4. strong single-graph comparator。

每个方法 2 个新训练 seeds、缩短但预先冻结的 development budget：共 **8 个训练 runs**。该阶段只回答：严格 actor 合约修复后，EA-RG 是否仍相对强 baseline 保留方向一致的信号。

### 4.2 Formal minimum if qualification passes

若 8-run qualification 中 EA-RG 在两个 seed 都保持方向一致优势，才授权 primary formal：同四个方法、同一协议、每方法 5 个新 seeds，共 **20 个 formal runs**。先不扩展多场景 robustness，不做大规模 ablation。

### 4.3 Qualification NO-GO

若 EA-RG 在两个 seed 都不优于 strong graph/MAPPO，或优势依赖不合法信息，则停止 EA-RG 论文主线，不再通过加模块或追加 seed 救结果。

## 5. 最小正式比较与机制指标

正式主结果至少报告：

* physical mission success / task-chain establishment；
* completion time 或 restricted completion time；
* collision/constraint failure；
* communication range/loss/delay 下的性能；
* EA-RG 相对 single-graph 的 relation ablation；
* actor information contract 与参数/训练预算公平性。

机制分析只保留能回答 EA-RG 作用的问题，例如 relation-specific message removal、single unified graph、no-graph 和合法信息 provenance 变化；不把旧 recovery proxy 重新包装成主终点。

## 6. 当前禁止事项

* 禁止 V2/R1/R2、Robust MARL、multi-rate、dynamic capability 等新方向；
* 禁止在没有完成 8-run qualification 前租正式大规模训练资源；
* 禁止把旧 checkpoint 当作严格公平主证据；
* 禁止为了恢复旧 headline 修改 endpoint、population 或 actor contract；
* 禁止把所有旧实验全部重跑。

