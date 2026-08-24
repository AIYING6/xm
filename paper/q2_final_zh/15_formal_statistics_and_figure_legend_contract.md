# 正式五种子统计与图表报告合同

## 1. 适用范围

本文件仅约束 `DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1` 的最终 10M 检查点结果：UTR/DRTP 各五个训练种子（2301–2305）、共同评估样本带 490000–490099、12,000 条原始评估记录。正式归档 SHA256 为 `cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd`。

## 2. 独立统计单位与禁止事项

- 独立统计单位为 **training seed**，配对单位为相同 seed 下的 UTR 与 DRTP；\(n=5\)。
- 100 个 evaluation episode 用于估计一个训练种子在指定条件下的表现，不能作为 100 个独立训练重复，也不能据此虚构显著性检验。
- 主文报告配对差值的均值、中位数、样本标准差、IQR、MAD、正向种子数和最差差值；不报告把 episode 误作独立样本所得的 p 值或置信区间。
- 所有五个训练种子必须保留。历史 seed2002、正式 seed2302 和 seed2304 的不利边界不得删除或以“异常值”名义排除。

## 3. 主端点与受限解释

主端点为 \(J_{F0}\)、\(J_{pert,mean}\) 与 \(J_{pert,worst}\)，正常工况 \(J_{nominal}\) 是能力保持端点。其中后两个指标分别映射到冻结机器字段 `J_OOD_mean` 和 `J_OOD_worst`，但不被解释为严格未见分布外测试。正式结果中，上述三个鲁棒性端点均为 5/5 正向配对差值；这支持冻结任务中的正向中心趋势，但不支持“对所有随机初始化稳定优越”或一般分布鲁棒最优性。

安全性与技术有效性单独报告：碰撞、超时、约束违规保留所有 episode；触发器有效性只在故障起始时刻仍存活的风险集中计算。起始时刻前的碰撞既不删除，也不重标记为已暴露。

## 4. 可复查数据源

| 论文内容 | 冻结源文件 |
|---|---|
| 裁决与 pooled 指标 | `formal_results/source_data/DRTP_UTR_Q2_FORMAL_DECISION.json` |
| 每种子、每条件的绝对指标 | `formal_results/source_data/per_seed_condition_summary.csv` |
| 配对效应与灾难性判定 | `formal_results/source_data/paired_seed_results.csv` |
| 评估完整性与风险集信息 | `formal_results/source_data/evaluation_manifest.json` |
| 样本带定义与哈希 | `formal_results/source_data/formal_tape_manifest.json` |
| 采样器末次权重与实际选择次数 | `formal_results/source_data/sampler_telemetry_summary.json` |

## 5. 图注复用文本

**图3：** 正式五种子最终检查点的主要任务端点。灰线连接同一训练种子的 UTR 与 DRTP，菱形为五种子总体均值；训练种子而非 episode 是独立统计单位。

**图4：** 十个冻结跨扰动条件（故障时机、持续时间和复合条件）下的平均配对任务得分差值，柱顶为正向训练种子数。其具体 onset--duration 成员曾被训练 sampler 使用，因而不作为严格 OOD 证据。

**图5：** 全部保留的逐种子鲁棒性效应与故障条件安全性。起始时刻前碰撞仍计入总体安全指标；风险集仅用于触发器技术有效性。

**图6：** DRTP 在正式五种子中的平均拓扑组权重轨迹。该遥测证明采样暴露被改变，不单独证明从权重到策略行为的因果链。

## 6. 终稿必保留限制

1. 仅覆盖三无人机轻量 3DOF 仿真和冻结的中继故障家族；
2. 主比较为参数匹配的内部 UTR 主消融，而非外部算法排名；
3. 历史开发与留出阶段出现过训练种子敏感性；
4. 正式裁决是 `FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE`，不是 `STABLE_PASS`；
5. 尚无 4/5 UAV、HIL 或实飞验证，也无公共硬件上的严格 wall-clock/峰值显存对照。
