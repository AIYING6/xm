# 正式结果整合审计

## 结论

`PASS — FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE`。正式五种子结果允许回填中文主稿，但历史开发 NO-GO、留出验证 FAIL 与历史 seed2002 反转必须继续保留。

## 完整性核验

- 归档 SHA256：`cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd`（下载文件已匹配）；
- 训练轨迹：UTR/DRTP × 2301–2305，10/10 completed；
- 共同终点：39,063 updates / 10,000,128 environment steps / 116,728 parameters；
- 评估样本带：490000–490099，hash `84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2`；
- 原始记录：12,000；风险集触发有效性：PASS；
- 中间检查点仅用于曲线，不参与最终选择；无 canonical seed、种子排除、warm restart 或后续自动训练。

## 冻结裁决

- machine verdict: `FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE`；
- catastrophic seeds: 0/5；
- 所有预注册 gate: PASS。

## 论文写作边界

- 可写：在冻结三无人机中继故障任务、共同 10M 预算和预注册五 seed 合同下，DRTP 的 F0、OOD mean 和 OOD worst 的配对均值与中位数为正；
- 不可写：DRTP 对所有随机初始化稳定优越、一般分布鲁棒最优、恢复丢失信息或已完成真实飞行验证；
- 需保留：seed2302 的正常工况反转、历史 seed sensitivity、仅三无人机 3DOF 仿真、内部参数匹配主消融和无外部同合同基线。

## OOD 条件审计

| 条件 | 平均配对ΔJ | 胜出种子数 | 最差配对ΔJ |
|---|---:|---:|---:|
| timing_28_80 | 51.30 | 5/5 | 2.62 |
| timing_36_80 | 52.05 | 5/5 | 8.13 |
| timing_52_80 | 54.00 | 5/5 | 17.46 |
| timing_60_80 | 54.04 | 5/5 | 16.16 |
| duration_44_40 | 49.05 | 4/5 | -1.26 |
| duration_44_60 | 47.33 | 4/5 | -21.30 |
| duration_44_100 | 58.41 | 5/5 | 21.41 |
| duration_44_120 | 62.52 | 5/5 | 27.80 |
| compound_28_120 | 65.38 | 5/5 | 26.44 |
| compound_60_120 | 55.91 | 5/5 | 19.88 |

## 自适应权重遥测

- 末次自适应更新：39040；
- 末次 q 均值：F0=0.102；TE=0.203；TL=0.075；DS=0.110；DL=0.237；CP=0.273。

这些遥测仅表明自适应器实际偏离均匀权重；它们不单独建立策略机制的因果解释。

## 产物

- `formal_results/source_data/`：冻结 decision、manifest、配对与条件级 CSV；
- `formal_results/figures/`：主结果、OOD、可靠性/安全性和自适应权重图；
- `formal_results/formal_result_tables.md`：主文与补充表源。
