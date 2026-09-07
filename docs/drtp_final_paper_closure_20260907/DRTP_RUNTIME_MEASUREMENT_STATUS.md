# DRTP Table 5 运行开销测量状态

**状态：** `RUNTIME_PROFILER_BLOCKED_SOURCE_MISMATCH`（2026-09-07）。

## 已完成的只读预检

`scripts/verify_drtp_runtime_profiler_preflight.py` 从 SHA256 已验证的
`drtp_stabilization_A_complete_results.tar.gz` 读取最终冻结 manifest，并把其中的
sampler、learner 和环境源码哈希与当前工作树逐项对照。

| 组件 | 结果 |
|---|---|
| `drtp_topology_sampler.py` | 精确匹配 |
| `uav_intercept_3d_env.py` | 精确匹配 |
| `simple_ri_gmappo.py` | 不匹配 |

冻结 learner 哈希为
`b2ae085ed60e20007ee188a044a2dc53d7061d8f7451c562f15244aeeef33873`，
当前工作树对应文件哈希为
`895eb0da3b4d1d803f386ed0229a0c8a4a20b87c75d84402c23040fe57a57a6b`。

## 结论与论文处理

当前**不得**用本机或任意非冻结源码进行 UTR/DRTP timing、sampler overhead 或 GPU memory
对比，也不得在 Table 5 填入估算值或“零开销”。这不是算法性能失败，而是可追溯性门未满足。

Table 5 在投稿稿中保留为 `TBD: exact frozen-source profiler pending`。主文仅可写：DRTP 在
reset-side 分配训练暴露，不改变 actor、critic、PPO、奖励或环境转移；这一定义不等价于已测得的
运行成本结论。

## 唯一允许的下一步

恢复最终确认实验所用的完整源代码包，或恢复哈希与上述 learner 完全一致的
`algorithms/ri_gmappo/simple_ri_gmappo.py`，再重新运行预检。仅当 verdict 为
`RUNTIME_PROFILER_READY` 时，才可在单一匹配 GPU 上启动固定短窗口、三次重复的 UTR/DRTP
profiler；该 profiler 不执行终点评估、不用于策略选择，也不修改算法。
