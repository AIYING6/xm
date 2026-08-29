# Stable-v2 D2 readiness report

## 裁决

`D2_READY_FOR_PILOT_AUTHORIZATION`

本裁决只表示 pilot 合同和执行链可复核，不表示云端训练已获授权，更不表示算法有效。

## 已完成

- 3101–3103 provenance audit：`CLEAN`，扫描 3,113 个维护文本文件，无既往科学使用命中；
- 独立 development tape 已冻结；
- `target_kl=0.02`、`epsilon_J=7.874919837916801`、downside/safety/intervention gate 已冻结；
- 单轨迹 runner 严格限制 3 arms × 3 seeds × 0.5M；
- evaluator 固定 9 workers、45 cells、4,500 episodes；
- aggregate 同时检查收益、下尾、离散度、方向、上尾、安全、机制活动和完整性；
- launcher 固定 9 路并发，拒绝已有输出目录并禁止自动续训；
- 合成 gate 测试可接受联合改善证据，并会拒绝“分数稳定但 guard 从未触发”的无效结果。

## 验证

- D1 implementation/regression tests + D2 contract/gate tests：`16 passed`；
- Python compile：PASS；
- shell syntax：PASS；
- D2 preflight：全部 20 项检查 PASS；
- 本地环境创建、训练、checkpoint evaluation：均未执行。

## 授权边界

下一步只有在人工明确授权后，才可把紧凑执行包上传 AutoDL，以 9 路并发运行一次。结束后只返回 0.5M frozen gate，不自动继续。
