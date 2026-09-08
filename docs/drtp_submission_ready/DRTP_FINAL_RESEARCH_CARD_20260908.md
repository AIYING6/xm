# DRTP 最终研究卡（证据驱动版）

## 研究对象

- **暂定题目**：面向中继拓扑退化的异构无人机协同训练暴露重分配
- **任务**：轻量 3DOF 三无人机协同任务；中继故障会改变合法通信、感知与任务支撑路径。
- **问题**：在固定名义工况与冻结故障支持下，均匀训练暴露能否充分塑造策略对不同故障组的适应？
- **唯一主要干预**：UTR 与 Original DRTP 共享 actor、critic、PPO、奖励、观察、动作、环境转移、预算与故障支持；仅 reset 时的六个故障组质量分配不同。
- **独立单位**：训练 seed；条件、episode 和时间步只构成同一训练 seed 的 endpoint 测量。

## 可检验论文论题

在两个独立、训练前冻结的 10M cohort 中，相对于条件均匀的 UTR，在相同故障支持上的有界自适应故障组暴露分配与更高的 cohort 平均扰动任务回报相伴出现；该关联需要与下尾、成功、超时和碰撞端点共同解释。

## 问题—方法—证据—结论闭环

| 环节 | 可核验内容 | 证据与边界 |
|---|---|---|
| 问题 | relay 故障改变合法路径，因而改变协同所能利用的信息结构 | 环境/故障实现与执行期信息边界；不称为隐藏信息恢复 |
| 方法 | DRTP 用名义相对困难信号，在有界单纯形内更新训练故障组质量 | sampler 源码与训练日志；日志仅证明暴露分布改变 |
| 主证据 | A：`+39.64`、3/5；B：`+23.15`、4/5 的 DRTP−UTR perturbed-return cohort 均值差 | A/B 分开；不做 pooled n=10 推断；不写逐 seed 保证 |
| 可靠性 | 两批 success/timeout 方向有利；A collision 增加、B 相同 | 不将任务回报直接转换为全面安全结论 |
| 训练排除结构条件 | A/B structural aggregate 的 mean / worst return 差均为正 | 仅适用于预先冻结的四个 structural 条件带；B timeout 不利 |
| 外部定位 | A：DRTP 回报、下尾与 timeout 优于 PLR-style；B：PLR-style 回报更高、DRTP success/timeout 更好 | 竞争性定位，不等价于主因果对照，更非全面胜出 |

## 最多三项可检验贡献

1. **受控干预贡献**：构造仅改变训练期故障组暴露分配的 UTR—DRTP 对照，隔离容量、输入、奖励和学习器之外的分布塑形变量。
2. **算法干预贡献**：设计名义锚定、相对难度驱动且有界的 DRTP 训练暴露更新，保持执行期信息边界不变。
3. **经验发现贡献**：在两批独立冻结 10M cohort 中观察到 DRTP 相对 UTR 的重复 cohort 平均增益，并以训练排除结构条件带与 PLR-style 比较限定适用范围。

## 不可支持的结论

- 任何训练 seed 均会改善；
- DRTP 对所有优先级式训练或所有拓扑退化全面优越；
- 回报提升等价于无条件安全改善；
- 结构条件带结果等价于任意未知拓扑上的普适泛化；
- actor 在执行时恢复未被允许的信息，或本研究已实现实飞验证。

## 当前结果叙事顺序

1. 先报告 A/B 中 UTR—DRTP 的受控端点（主结果）。
2. 紧接报告 success、timeout、collision 与下尾，防止单一均值替代可靠性分析。
3. 报告训练排除 structural 条件带，明确条件集合与可靠性方向边界。
4. 报告 PLR-style 外部定位，强调 A/B 的不同排序和不可替代性。
5. 仅在故障注入审计通过后加入 6-UAV v2；仅在全因子汇总通过后加入语义/自适应消融；运行开销必须实测。

## 关键来源

- `configs/drtp_stabilization_final_method_selection_20260906.json`
- `configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json`
- `D:/File/Downloads/drtp_stabilization_A_complete_results.tar.gz`
- `D:/File/Downloads/drtp_stabilization_B_complete_results.tar.gz`
- `D:/File/Downloads/drtp_final_evidence_heldout_ood_results.tar.gz`
- `D:/File/Downloads/drtp_plr_matched_ab_results.tar.gz`
- `DRTP_FINAL_EVIDENCE_REGISTER_20260908.md`

## TODO（需补证）

- 只纳入故障真实注入已审计的 6-UAV v2；旧 `fault-step=9` 不可恢复。
- 审计 2×2 完成包后再决定消融是否能识别 topology semantic 与 adaptive update 的分量贡献。
- 在相同硬件、并发和预算下实测训练时长、sampler 更新时间与峰值显存。
