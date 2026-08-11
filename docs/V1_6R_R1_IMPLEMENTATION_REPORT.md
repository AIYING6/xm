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

## 当前验证

```text
PYTHONPATH=. D:/Anaconda/envs/.conda/envs/cac/python.exe \
  -m scripts.test_v16r_legal_observation_interface

checks=7, failed=0
```

已覆盖：

1. 无合法 evidence 时改变 global target 不改变 actor evidence；
2. local sensing 可更新对应 recipient；
3. valid delivered cache 可更新 recipient，source/path 保留；
4. expired cache 不进入 actor；
5. recipient graph 形状和有限值；
6. graph 不使用全局 target fallback；
7. source/provenance relation 可追溯。

## 尚未通过的门

这不是 R1 完成。仍需补充真实 collector/replay 路径的 hidden-state expiry/reset、现有 actor-boundary 回归、graph provenance 对照、neutralization precedence 和 continuous-action 接口回归。全部通过前禁止 B0/B1/B2 训练。

## 备注

当前旧环境仍保留 legacy discrete action 与旧兼容字段；本次没有修改动力学、reward 或训练器。v1.6R 的 continuous guidance 与最终 actor graph 接口必须在后续 R1 适配层中显式冻结，不能把 legacy 字段自动当作新证据。
