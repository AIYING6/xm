# DRTP 匹配运行开销测量协议

## 目的

测量 UTR 与 DRTP 的训练期 wall-clock、sampler/update 开销和峰值 GPU memory；该实验不评估策略性能、不保存可用于论文性能比较的新 checkpoint，也不改变算法。

## 前置门

必须先运行 `scripts/verify_drtp_runtime_profiler_preflight.py`。只有 verdict 为 `RUNTIME_PROFILER_READY` 才能启动 profiler。其依据是 A/B 正式冻结 manifest 的 sampler、learner 与环境 SHA256；任一源码不一致时，禁止将测得时间写入 Table 5。

## 匹配条件

- 同一 GPU、同一驱动/CUDA/PyTorch、同一 CPU thread 与相同并发策略；
- 固定并记录一个随机 seed；
- UTR/DRTP 使用同一环境数、rollout、PPO epochs、minibatch、hidden dimension 和更新数；
- 固定短窗口覆盖完整 sampler 选择与至少一个 adapt interval；建议每方法三个独立重复；
- 不执行 endpoint evaluation，不访问 frozen tape，不依据结果调整超参数。

## 记录字段

| 字段 | 记录方法 |
|---|---|
| wall-clock | 进程启动至固定 update 完成的 elapsed time；同时报告每 update 与每 env step。 |
| sampler overhead | sampler selection + difficulty/projection update 的累计耗时与占 wall-clock 比例。 |
| GPU memory | `torch.cuda.max_memory_allocated()`，并记录设备名称。 |
| 配置与来源 | 代码 SHA、硬件、并发、线程、seed、update 数与软件版本。 |

## Table 5 解释边界

报告测量均值、范围或中位数；不因为网络参数数量未变化而写“zero overhead”。若增量小，可在指定硬件与配置下写“measured overhead was small”；若增量可见，则如实归因于 sampler logging/更新，而不修改方法。
