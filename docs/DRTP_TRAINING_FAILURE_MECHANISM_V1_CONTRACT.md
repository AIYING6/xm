# DRTP Training-Failure Mechanism Experiment V1

状态：`P0–P3 技术通过；P4 云端训练包已冻结；尚未启动大规模训练`。

## 冻结范围

UTR-SG-MAPPO 与 DRTP-SG-MAPPO 的当前算法、SG backbone、PPO、环境、reward、failure semantics、actor information boundary 和全部 DRTP 参数保持不变。所有 telemetry 仅是只读日志接收端，不进入 actor、critic、reward、sampler 或 termination。

探索性 paired seeds 为 `2601/2602/2603`，与所有既有 cohort 分离，不合并到历史结论，不使用 held-out 或 canonical seeds。

## 训练合同

每个 method×seed 从 scratch 严格连续训练 `1,000,192` environment steps（4 env × 64 rollout × 3907 updates），固定保存 `250k/500k/750k/1M` checkpoints 和完整 runtime state；不允许 early stopping、checkpoint promotion、seed replacement 或根据结果修改规则。大规模训练只在云端执行，单卡默认最大安全并发为 6，单进程 CPU 线程设为 1。

## Telemetry 合同

写入 episode summary 与 failure-event window 两级 JSONL。event window 为 `tau=-20…+60`；nominal 使用 matched pseudo-onset `44`。字段定义见 `diagnostics/drtp_mechanism_v1/08_report/telemetry_dictionary.md`。Telemetry 必须持久化到 runtime checkpoint，但仍不得改变训练计算。

## 评价与判定

独立 development-only tape 固定为 `Nominal/F0/T28/D120/C28-120`，每个条件 100 个 episode，manifest/hash 在训练前冻结。任何机制结论必须以 UTR 同 seed 为控制，并同时满足：时间领先、至少 2/3 DRTP 重复、UTR 无同强模式、sampler→exposure→behavior→outcome 至少连续三层证据。否则为 `NO-GO`；不得启动 Stable-DRTP 或新的 10M confirmatory training。

历史 forensic 结论 `NO-GO — existing telemetry does not support a stable actionable mechanism` 保持不变。本合同不回写历史结果。
