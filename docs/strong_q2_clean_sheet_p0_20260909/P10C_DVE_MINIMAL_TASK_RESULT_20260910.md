# P10-C DVE 最小异步任务可识别性结果

**判定：** `TASK_IDENTIFIABLE_DISTRIBUTION_NOT_FROZEN`  
**训练授权：** 否。

## 1. 已完成内容

新增独立的两 UAV 单决策环境 `DVEAsyncUAVEnv`，接口保持：

- `reset() -> obs, share_obs, graph_obs`
- `step(actions) -> obs, share_obs, graph_obs, rewards, dones, infos`

环境显式包含推理时延、完成时状态漂移、任务相关性和共享走廊预约四个变量。该环境不复用 DRTP 采样器、不包含学习方法，也不产生论文性能证据。

## 2. 穷举结果

32 个冻结条件由 2 个时延、4 个状态漂移、2 个任务相关性和 2 个预约状态的笛卡尔积组成。同一时延内共有 240 个无序状态对，其中 56 对需要不同的 accept/fallback 决策，有效性分叉比例为 23.33%，超过预设 20% 门槛。

| 规则策略 | 平均团队价值 | stale accept rate | joint conflict rate |
|---|---:|---:|---:|
| Naive accept | -4.000 | 87.50% | 50.00% |
| Always fallback | 4.000 | 0 | 0 |
| Fixed TTL | 0.000 | 43.75% | 25.00% |
| Current-state safety shield | 3.500 | 25.00% | 0 |
| DVE oracle | 4.625 | 0 | 0 |

DVE oracle 严格优于 fixed TTL 和 safety shield，并消除 stale accept。标准环境接口的两个 smoke test 均通过。

## 3. 为什么现在仍不能训练

当前全因子均匀网格中，`task_relevant=true`、`corridor_reserved=false` 且 `state_drift<=2` 的旧动作有效条件只占 4/32，即 12.5%。因此：

- Naive accept 被大量无效状态压低，过于容易击败；
- Always fallback 达到 4.000，与 DVE oracle 的 4.625 只差 0.625；
- 学习器可能通过近乎总是回退取得高分，无需学习动作特定有效域；
- 直接训练将无法区分“学会 DVE”与“学会保守拒绝”。

这不是 DVE 科学对象失败，而是候选训练分布尚未形成公平、非平凡的 accept/fallback 权衡。必须在训练前修复，不能跑完后再解释。

## 4. 下一道零训练门：P10-C2 分布与奖励可识别性

不修改 DVE 方法，仅调整并冻结任务实例分布。要求：

1. 应接受旧动作的条件占 35%–65%；
2. always-accept 与 always-fallback 均至少比 oracle 低 15%；
3. fixed TTL 与 safety shield 均严格低于 oracle；
4. 中等时延条件下 naive async 有明显退化但平均价值不得为负；
5. 有效性分叉对比例仍不低于 20%；
6. accept/fallback 的价值来自任务动力学，不以额外分类奖励塑造；
7. 冻结训练、验证和测试分布后才允许做基线可学习性 pilot。

P10-C2 应使用分层采样或一个有物理含义的状态生成过程，而不是为达到比例随意复制样本。所有比例与阈值必须在方法训练前登记。

## 5. 证据边界

当前只支持：DVE 的目标决策在最小环境中存在，且不能由固定 TTL 或纯安全过滤完全替代。

当前不支持：MAPPO 能学习该决策、DVE 优于神经基线、任务分布具有真实 UAV 代表性、方法具备安全保证或论文创新已经成立。

## 6. 可复核资产

- 环境：`envs/dve_async_uav_env.py`
- 配置：`configs/p10c_dve_minimal_async_identifiability_20260910.json`
- 审计：`scripts/p10c_dve_minimal_async_identifiability.py`
- 测试：`tests/test_dve_async_uav_env.py`
- 结果：`docs/strong_q2_clean_sheet_p0_20260909/P10C_DVE_IDENTIFIABILITY_RESULT.json`

