# P10-C2 DVE 分层任务分布冻结结果

**判定：** `P10C2_DISTRIBUTION_PASS`  
**候选方法训练：** 未授权。  
**下一步：** 只允许基线学习性和接口审计。

## 1. 分布构造原则

本轮不修改 DVE 决策规则或奖励，只将原先失衡的全因子均匀网格替换为方法无关的四类任务状态分层：

| 状态层 | 数量 | 物理/任务含义 |
|---|---:|---|
| valid tracking | 20 | 状态变化有限，旧机动仍安全且能推进任务 |
| task obsolescence | 8 | 旧机动仍安全，但目标关系变化后不再推进任务 |
| team contention | 6 | 旧机动对个体仍有价值，但与先完成队友的共享资源预约冲突 |
| dynamic divergence | 6 | 推理期间状态漂移使旧机动越出有效域 |

每个层内的状态漂移由冻结区间上的等距点生成，计算时延按 20、40、80、120 ms 循环分配；40 个状态元组全部唯一。分层规则不读取任何学习方法输出或训练结果。

## 2. 可识别性结果

- 应接受旧动作比例：50%；
- 同时延状态对：180；
- 需要相反 accept/fallback 决策的状态对：100；
- 有效性分叉对比例：55.56%；
- DVE oracle stale-action acceptance：0。

| 规则策略 | 平均团队价值 | 相对 DVE oracle 差距 | accept rate | stale accept rate |
|---|---:|---:|---:|---:|
| Naive accept | 2.500 | 57.63% | 100% | 50.00% |
| Always fallback | 3.400 | 42.37% | 0 | 0 |
| Fixed TTL | 2.700 | 54.24% | 50.00% | 25.00% |
| Current-state safety shield | 4.675 | 20.76% | 77.50% | 27.50% |
| DVE oracle | 5.900 | — | 50.00% | 0 |

## 3. 门控结果

以下预设条件全部通过：

- 有效动作占比在 35%–65%；
- always-accept 和 always-fallback 均比 oracle 低至少 15%；
- 分叉对比例不低于 20%；
- naive async 平均价值为正，不是全面失败；
- DVE 严格优于 fixed TTL；
- DVE 严格优于 safety shield；
- DVE 不接受已失效动作。

这解决了 P10-C 中 always-fallback 接近最优的问题。现在任务同时惩罚盲目接受和过度回退，必须根据完成时状态、任务相关性和团队预约区分动作。

## 4. 仍未证明的内容

该结果来自规则 oracle 的零训练枚举，只证明冻结分布具有非平凡决策结构。它不证明：

- recurrent MAPPO 能学会该任务；
- DVE head 可以校准有效域；
- DVE 优于 delay-aware 神经基线；
- 分层比例等同于真实机载负载分布；
- 当前最小环境足以构成论文主实验。

## 5. 下一阶段冻结要求

P10-D0 先实现容量匹配的 baseline-only 学习合同，禁止实现 DVE head。训练、验证和测试必须分离：

- 训练：层内连续取样，但不使用冻结验证/测试点；
- 验证：用于固定 checkpoint 选择，不调节任务分布；
- 测试：封存，P10-D0 不触碰；
- 基线：delay-aware recurrent policy，输入仅为合法局部状态、旧动作元数据、时延和预约摘要；
- 资格：3 seeds 中至少 2 个明显优于两个常数策略，且不退化为近乎 always-fallback 或 always-accept。

基线不可学习则停止或重审环境接口，不据此评价 DVE。基线通过后，才允许实现容量匹配的 DVE 候选与消融。

## 6. 可复核资产

- 配置：`configs/p10c2_dve_stratified_distribution_20260910.json`
- 审计脚本：`scripts/p10c2_dve_distribution_audit.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P10C2_DVE_DISTRIBUTION_RESULT.json`

