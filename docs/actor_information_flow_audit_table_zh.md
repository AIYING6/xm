# Actor 信息流审计表

日期：2026-07-29

目的：回应“任务支援关系图可能造成 Actor 信息泄漏”的预审意见，明确 3DOF 任务链恢复实验中 decentralized actor、centralized critic、evaluation metrics 的信息边界。

## 1 审计结论

当前论文写作必须采用以下表述：

```text
EA-RG-MAPPO 使用通信可行 masked actor graph，而不是允许 Actor 访问全局任务链真值的动态图。
```

任务支援边必须同时满足：

```text
role_compatible(src, dst)
and delivered_communication(dst, src)
and visible_support_evidence(src)
```

因此，任务支援关系不能写成“由全局任务链阶段动态切换”。如果论文需要描述其动态性，应写成：

```text
任务支援边由角色兼容性、已投递通信和 actor 可见的信息新鲜度/本地状态共同决定。
```

## 2 Actor 输入审计表

| 信息项 | 数据来源 | 是否经通信 | 是否使用环境真值 | Actor 是否可用 | 当前处理 |
|---|---|---:|---:|---:|---|
| 自身位置、速度、航向、航迹倾角 | 本机状态 | 否 | 否 | 是 | `obs[i]` |
| 自身能量/平台能力 | 本机状态/配置 | 否 | 否 | 是 | `obs[i]` |
| 自身角色标识 | 平台配置 | 否 | 否 | 是 | role features / embedding |
| 自身直接探测标志 | 本机传感器模型 | 否 | 否 | 是 | detection flag |
| 自身本地攻击窗口标志 | 本地目标估计 + 本机几何条件 | 否 | 否 | 是 | `local_attack_window` |
| 目标相对状态 | 直接感知或缓存估计 | 视情况 | 否 | 条件可用 | strict sensing + target cache |
| 未感知目标真实位置 | 环境全局状态 | 否 | 是 | 否 | 使用 target prior 或无效缓存 |
| 共享 graph 目标节点 | 公共先验 | 否 | 否 | 是 | strict bottleneck 下固定 prior + zero velocity |
| 邻居平台状态 | 通信图/消息 | 是 | 否 | 条件可用 | 受通信 mask 约束 |
| 未通信邻居隐藏状态 | 环境全局状态 | 否 | 是 | 否 | 不应影响 actor logits |
| 消息年龄 | 已接收消息缓存 | 是 | 否 | 是 | actor-visible cache metadata |
| 消息置信度 | 已接收消息缓存 | 是 | 否 | 是 | actor-visible cache metadata |
| 通信丢包/时延配置 | 场景配置 | 否 | 否 | 是 | 可作为环境条件标量 |
| 物理通信边 | 通信半径、丢包、时延、节点功能 | 是 | 否 | 是 | `relation_adj[communication]` |
| 感知边 | 直接目标探测 | 否 | 否 | 条件可用 | `relation_adj[perception]` |
| 任务支援边 | 角色兼容 + 已投递通信 + 可见支援证据 | 是 | 否 | 是 | `relation_adj[task_support]` |
| 真实攻击窗口 `attack_window` | 环境真实目标状态 | 否 | 是 | 否 | 仅 reward/critic/termination/evaluation |
| 全局任务链闭合 \(C_t\) | evaluation metrics | 否 | 是 | 否 | 仅评价/统计 |
| 全局攻击链进度 | evaluation/critic feature | 否 | 是 | 否 | 不得进入 actor graph |
| centralized critic 全局状态 | CTDE training | 否 | 可含真值 | 仅训练 | `share_obs` |

## 3 任务支援边审计

当前代码位置：

```text
envs/uav_intercept_3d_env.py
```

相关函数：

```text
_support_edge(src, dst)
_has_target_information(agent_id)
_active_support_edge(src, dst)
```

当前逻辑摘要：

1. `_support_edge(src, dst)` 只定义角色兼容性，例如 Scout -> Attacker、Relay -> Attacker、Attacker -> Relay。
2. `_active_support_edge(src, dst)` 首先要求 `_support_edge(src, dst)` 为真。
3. `_active_support_edge(src, dst)` 要求 `self.comm_adj[dst, src] > 0.5`，即接收方确实能够从发送方获得通信。
4. Scout/Relay 的支援激活依赖 `_has_target_information(src)`，其中 Relay 只能使用自身直接探测或已经写入本地缓存的目标信息。
5. Attacker/Interceptor 的支援激活依赖发送方自身 `local_attack_window`，该标志由 actor 可见目标估计计算，而不是由真实目标状态直接计算。

## 4 仍需重点核查的问题

### 4.1 `_has_target_information` 是否只使用合法信息

需要确认：

- `detected_by[agent_id]` 是否来自本机传感器模型；
- `_has_fresh_target_cache(agent_id)` 是否只由已投递消息写入；
- `comm_adj[agent_id, source]` 是否表示当前已投递或当前物理可通信；
- 不应通过 `detected_by[source] + comm_adj[agent_id, source]` 让接收方即时知道“source 探测到了目标”，除非该信息已经经过通信语义允许。

如果 `comm_adj` 只是物理邻接，而不是已投递消息，则 `_has_target_information` 可能仍然偏乐观。需要用测试确认 dropout 和 delay 不会被绕过。

### 4.2 Attacker local attack-window flag 是否可通信

Attacker -> Relay 的任务支援边可由 `local_attack_window[src]` 激活。当前处理：

- `attack_window` 使用真实目标状态，只用于 reward、critic、termination 和 evaluation；
- `local_attack_window` 使用 attacker 的本地目标估计和本机几何状态；
- 在 strict sensing + target-info bottleneck 下，若 attacker 没有直接探测或有效目标缓存，则 `local_attack_window=0`；
- relay 看到 attacker 支援边仍需 `comm_adj[relay, attacker] > 0.5`，因此 dropout、delay 和 relay failure 会阻断该边。

该风险已由 `test_local_attack_window_requires_actor_visible_target_information` 覆盖。

### 4.3 `adj` 中的 attack 边语义

图构建中存在：

```text
adj[i, j] = max(adj[i, j], sensing, comm, active_support, attack)
```

其中 `attack` 表示本地攻击窗口辅助边。当前定义为：

```text
attack(i, target) = 1 iff local_attack_window[i] = 1
```

该边界已明确：

- `attack` 不是第四类 relation，不进入 `relation_adj`；
- `attack` 只进入 union adjacency，用于本机本地攻击窗口下的辅助连接；
- `attack` 由 `local_attack_window` 生成，不读取 evaluation-only `attack_window`；
- strict bottleneck 下共享 graph 目标节点固定为公共 prior + zero velocity，因此该边不会把真实目标节点泄漏给其他 actor；
- 对任务支援关系的消融不能把该辅助边写成主创新。

## 5 必须补充的测试

已有测试文件：

```text
tests/test_gate1_communication_feasibility.py
```

最新验证结果：

```text
2026-07-29: 33 passed
```

现有文档声称已覆盖：

- receiver-sender graph direction；
- task-support no-bypass；
- disconnected attacker action-logit invariance to hidden target changes；
- delayed-message delivery timing；
- packet-dropout prevention；
- communication-subsystem failure delivery blocking；
- one-hop-per-delay-cycle propagation。

建议新增或确认以下测试：

1. **Task-support no global-stage leakage**
   - 改变 evaluation-only chain state；
   - 保持 actor 可见信息不变；
   - actor logits 和 task-support adjacency 不变。
   - 当前新增近似覆盖：`test_task_support_relation_does_not_depend_on_hidden_target_state`。

2. **Task-support requires delivered communication**
   - source 有目标信息；
   - receiver 与 source 物理邻近但消息被 dropout 或 delay 未到达；
   - task-support edge 不应提前激活。
   - 当前已有覆盖：`test_task_support_relation_requires_delivered_communication`。

3. **Relay failure blocks support propagation**
   - relay 有旧目标信息；
   - relay communication subsystem failed；
   - relay-originated task-support edge 不应产生新消息。
   - 当前已有通信层覆盖：`test_comm_failure_drops_queued_delivery`；
   - 当前新增 task-support 专项覆盖：`test_relay_failure_blocks_relay_originated_task_support`。

4. **Hidden target state invariance**
   - 无直接感知、无有效缓存、无有效通信；
   - 修改真实目标状态；
   - actor logits 不变。
   - 当前已有覆盖：`test_disconnected_attacker_logits_do_not_change_with_hidden_target` 和 `test_strict_bottleneck_graph_hides_stale_global_target_state`。
   - 当前强化覆盖：即便某一平台直接探测目标，strict bottleneck 下共享 graph 的 target node 仍保持公共 prior/zero velocity；真实目标信息只进入检测者自己的 local observation。

5. **Union graph residual no bypass**
   - communication relation 和 task-support relation 都关闭；
   - union adjacency 不应仍然连接非法信息通道。
   - 当前新增覆盖：`test_union_graph_does_not_use_potential_task_support_without_delivery`。

6. **Local attack-window no hidden target leakage**
   - attacker 在真实几何上处于攻击窗口；
   - attacker 无直接探测、无有效缓存、无有效通信；
   - actor observation 中 `local_attack_window` 必须为 0，task-support edge 不得激活；
   - 写入合法目标缓存后 `local_attack_window` 才允许变为 1。
   - 当前新增覆盖：`test_local_attack_window_requires_actor_visible_target_information`。

7. **Relay support no teammate-private-state shortcut**
   - Scout 当前具备目标信息；
   - Relay 与 Scout 通信邻接存在，但目标消息尚未写入 Relay 本地缓存；
   - Relay-originated task-support edge 不得读取 Scout 当前私有 `F_m`；
   - 写入合法 Relay 缓存后该支援边才允许激活。
   - 当前新增覆盖：`test_relay_task_support_uses_relay_cache_not_teammate_private_state`。

8. **Recovery metric uses stable closure-window start**
   - `chain_closed` 表示连续 `attack_hold_steps` 步稳定闭合后的评价变量；
   - post-failure recovery delay 按稳定闭合窗口的起始步计算；
   - 当前新增覆盖：`test_post_failure_recovery_steps_use_stable_closure_window_start`。

9. **Fresh-information recovery vs stale-cache recovery**
   - 失效后重新闭合任务链时，区分攻击平台依赖失效前旧缓存维持闭合、故障后投递的故障前旧消息闭合，还是获得了故障后生成的新鲜目标信息；
   - 主协议选点使用连续 `attack_hold_steps` 步、after-loss、generation-based 的 `post_failure_fresh_info_recovered`；旧缓存恢复和故障后投递旧消息仅作为辅助诊断；
   - 当前新增覆盖：`test_post_failure_fresh_info_recovery_separates_stale_cache`。

## 6 论文 Methods 推荐写法

可直接写入论文：

```text
为避免任务支援关系成为隐藏的全局状态通道，本文将 actor 侧任务支援边定义为通信可行的 masked relation。任务支援边仅在三类条件同时满足时激活：发送方和接收方角色兼容，接收方能够通过物理通信约束获得发送方消息，且发送方具备 actor 可见的支援证据，例如直接感知、有效目标缓存或本地攻击窗口状态。全局任务链闭合变量、评估专用恢复指标和 centralized critic 状态不参与 actor 侧任务支援图构建。
```

## 7 当前风险状态

风险等级：低到中等，后续重点转向方法公式、动力学和通信模型可复现化。

理由：

- 文档和代码中已有“task-support edges require delivered physical communication”的设计；
- `_active_support_edge` 确实检查 `comm_adj[dst, src]`；
- 新增测试已经确认 task-support adjacency 不依赖隐藏目标状态，union graph 不使用未投递的潜在支援边，Relay 不读取队友当前私有目标信息，actor 侧本地攻击窗口不读取隐藏目标真值，恢复指标与连续闭合窗口一致，且新鲜信息恢复与旧缓存维持恢复被区分统计；
- relay failure 下的 task-support 专项行为已由 `test_relay_failure_blocks_relay_originated_task_support` 覆盖；
- 论文初稿原表述容易被审稿人理解为全局阶段泄漏，已经修正。

尽管信息边界风险已明显降低，正式论文仍不应仅凭结构描述把任务支援关系写成强机制结论；该结论还需要正式消融实验支持。
