# DRTP B线 B3：1M 机制门报告

状态：`MECHANISM_HYPOTHESIS_NO_GO`

## 结论

六条冻结的 B3 trajectory 均完整完成，技术有效；但 B3 所检验的单一
机制链没有达到预注册的重复性门槛。因此，**关闭当前
`sampler/q → exposure → behavior/support → outcome` 机制假设**。不续训至
3M，不提出稳定化修改，也不授权任何 10M 训练。

这不是“DRTP 已经稳定”的结论。相反，B3 在 1M 又观测到种子依赖的最终
策略结果；只是该结果没有在至少两个 DRTP seed 上以同方向的退化形式重复，
因此不能被用于支持一个可操作的 sampler-level 失败机制。

## 完整性与 provenance

| 项目 | 结果 |
|---|---|
| 冻结代码提交 | `69117b628fe85026e0638abb73dcfbfb04e4a64c` |
| 方法 × seed | UTR / original DRTP × 2701, 2702, 2703 |
| 每条训练预算 | 1,000,192 environment steps（全部完成） |
| 里程碑 | 0.25M / 0.50M / 0.75M / 1M 均保存 |
| read-only telemetry | 六条均存在；每条 episode summary 与 event window 均非空 |
| 固定诊断 tape | hash `e01c905b04257fd6b373dbbe3ca25cf5f0dece0864e89b6713bd7647107ce9ed` |
| 评估 | 30 cells、3,000 raw episode records、全部保留 |

云端 launcher 的 `fatal: not a git repository` 仅来自归档交付环境中尝试读取
Git HEAD 的 stderr；六个 manifest 均已写入相同的冻结 source commit，训练、
checkpoint、telemetry 和 evaluation 均正常完成，故该信息不构成技术无效。

## Seed-level 结果方向（DRTP − UTR）

| seed | nominal ΔJ | F0 ΔJ | T28 ΔJ | D120 ΔJ | C28-120 ΔJ | 解释 |
|---:|---:|---:|---:|---:|---:|---|
| 2701 | +100.09 | +80.76 | +95.51 | +75.84 | +77.44 | 全部有利，timeout 均下降 |
| 2702 | −108.54 | −89.85 | −89.59 | −85.84 | −88.23 | 全部不利，timeout 上升 |
| 2703 | +56.63 | +58.34 | +2.61 | −1.00 | +2.00 | 总体有利/近似持平，timeout 均下降 |

因此，2702 是一个清晰的同 seed UTR-controlled 反转实例；然而 2701 与 2703
并没有出现同方向的最终退化。B3 的 `Replication` 条件要求至少 2/3 DRTP seeds
出现同方向、相似结构的候选链，现有 outcome 层本身即不满足该必要条件。

## 为什么不从单个坏 seed 推出机制

B3 的 `MECHANISM_CANDIDATE` 需要同时满足：异常时间领先、至少 2/3 DRTP
seeds 重复、paired UTR 中无同强模式，以及
`sampler/exposure → behavior/support → outcome` 的三层证据。虽然所有 six runs
均保存了完整 event-window telemetry，单个 seed2702 的相关模式不能替代
跨-seed 重复性。因此不得把它归因为 q、specific sampler group、几何、信息路径
或 PPO 的原因，也不得据此引入 trust region、confidence gate、warm-up 或任何
Stable-DRTP 模块。

## 冻结的后续动作

- 不启动 B3 3M strict continuation；
- 不生成算法 intervention；
- 不重跑、替换或删除 seed2702；
- B 线该机制链永久关闭；
- A 线论文仍独立按“高平均收益、训练 cohort/seed 敏感性”为边界收口。

原始归档：`drtp_b3_1m_results.tar.gz`，SHA256
`297bbe7753b6273882e8d010c8ac35d55766af417bda8074ed4017eadcf1e6ac`。
