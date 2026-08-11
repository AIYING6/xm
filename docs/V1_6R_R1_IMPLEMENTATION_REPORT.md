# v1.6R R1 实现报告

状态：`R1_PARTIAL__LEGAL_INTERFACE_INITIAL_PASS__FULL_REGRESSION_PENDING`

日期：2026-08-11

## 已完成

- 新增 `envs/v16r_legal_interface.py`；
- 新增 `LegalObservationInterface`；
- 新增 `LegalTargetEvidence`，统一表达 local sensing / delivered cache / none；
- 新增 recipient-specific graph builder；
- 禁止 interface 读取 `last_detected_target_*` 和 `_estimated_target_state()`；
- graph 仅使用当前 recipient 合法 evidence，并携带 source/path/age/confidence；
- 新增 `scripts/test_v16r_legal_observation_interface.py`。
- 新增 legacy-safe 的 `step_guidance()` continuous turn/climb 接口；旧 `step(int_actions)` 保持不变；
- 新增 `scripts/test_v16r_continuous_guidance.py`。
- 新增 `envs/v16r_env_adapter.py`，将 continuous guidance 与 recipient-specific graph 接入标准 reset/step 外观；
- 新增 `scripts/test_v16r_env_adapter.py`。

## 当前验证

```text
PYTHONPATH=. D:/Anaconda/envs/.conda/envs/cac/python.exe \
  -m scripts.test_v16r_legal_observation_interface

 checks=11, failed=0
```

Continuous guidance 回归：

```text
checks=5, failed=0
```

Adapter 端到端回归：

```text
checks=5, failed=0
```

已覆盖：

1. 无合法 evidence 时改变 global target 不改变 actor evidence；
2. local sensing 可更新对应 recipient；
3. valid delivered cache 可更新 recipient，source/path 保留；
4. expired cache 不进入 actor；
5. recipient graph 形状和有限值；
6. graph 不使用全局 target fallback；
7. source/provenance relation 可追溯。
8. recipient-0 cache 不泄漏到 recipient-1；
9. recipient-0 local sensing 不泄漏到 recipient-1。
10. recipient graph stack 显式保留 recipient 维度；
11. relation 维度与 graph schema 一致。

## 尚未通过的门

这不是 R1 完成。静态检查现有 MAPPO collector 后确认：当前 rollout 是前馈的，没有 recurrent hidden state；因此现阶段没有 hidden-state 绕过 expiry 的实际路径，但未来接入 GRU/recurrent actor 时必须显式加入 reset mask。

同时发现两个明确的 R1 集成阻塞：

1. legacy collector 仍接收环境返回的共享 graph，而不是 `[recipient, node, node, feature]` 的 recipient-specific graph；
2. legacy 3DOF 环境默认仍使用离散 27-action；已通过 `V16RIntercept3DEnv` 提供独立 continuous guidance 路径，但 MAPPO collector 尚未接入该路径。

这两个差异不能通过字段别名掩盖，必须在 R1 适配层中显式解决。仍需补充 graph provenance 对照、neutralization precedence 和 continuous-action 接口回归。全部通过前禁止 B0/B1/B2 训练。

## 备注

当前旧环境仍保留 legacy discrete action 与旧兼容字段；本次没有修改动力学、reward 或训练器。v1.6R 的 continuous guidance 与最终 actor graph 接口必须在后续 R1 适配层中显式冻结，不能把 legacy 字段自动当作新证据。
