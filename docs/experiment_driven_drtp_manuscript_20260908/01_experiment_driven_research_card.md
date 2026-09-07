# 实验驱动研究卡：DRTP 三 UAV 拓扑故障训练研究

## 1. 任务

在轻量 3DOF 异构三 UAV 协作拦截环境中，蓝方由侦察、继电和攻击角色构成。继电节点故障会在有限时段内删除该节点相关通信，使攻击角色在超出本地终端感知包络时不能继续使用依赖失效继电路径的缓存信息；环境仅允许满足既定时序与路径规则的替代信息路径。研究对象是这种**合法信息边界下的协同任务完成**，而不是恢复被掩蔽的全局状态或处理完全断联。

**来源：** `envs/uav_intercept_3d_env.py:93–161, 735–755, 987–1036, 1045–1162`。

## 2. 可检验缺口

训练时，名义情形与六个冻结故障组共同构成可采样条件空间。均匀随机化为每个故障组分配相同的条件质量；它并不区分训练过程中不同组的完成回报相对于名义条件的差异。可检验问题不是“均匀随机化是否错误”，而是：**在其余训练和执行条件不变时，受限的、完成回报驱动的训练暴露重分配是否改变最终故障端点与其可靠性代价？**

**来源：** `algorithms/ri_gmappo/drtp_topology_sampler.py:14–43, 188–325`；`tests/test_drtp_utr_q2_formal.py`。

## 3. 唯一主要方法差异

| 项目 | UTR | DRTP | 该项是否隔离 |
|---|---|---|---|
| actor、critic、图编码器、参数量 | 相同 | 相同 | 是；E1 前置检查记录两臂均为 116,728 参数。 |
| PPO、奖励、观测、动作、环境转移、执行期信息边界 | 相同 | 相同 | 是；代码测试在排除 sampler mode/seed/output 后要求配置字典相等。 |
| 名义条件质量 | 0.50 | 0.50 | 是。 |
| 故障组支持集合与组内条件抽取 | 相同 | 相同 | 是。 |
| 故障组条件质量 | 条件均匀 | 按有界自适应 `q` 更新 | **唯一主要干预**。 |

**来源：** `algorithms/ri_gmappo/drtp_topology_sampler.py:14–43, 176–325`；`tests/test_drtp_utr_q2_formal.py:test_formal_config_diff_is_sampler_only`；`tmp/cross_tape_reliability_20260827/assets/results/formal/drtp_utr_q2_paired_5seed_cloud_10way/formal_preflight.json`。

## 4. 主要因果对照

**受控比较：** 共同的五个前瞻性训练种子（2301–2305）下，UTR 与 DRTP 各自从头训练 10,000,128 环境步；只使用最终 10M checkpoint；在同一确定性 episode ID 带、同一 12 条条件、每条件 100 个 episode 上评价。

故此，对“仅改变训练暴露分配是否会改变所定义端点”的最强内部效度来自 E1 的 UTR–DRTP 配对比较。它**不**证明任何单个 `q` 变化、组难度或信息路径是收益的中介原因。

**来源：** `scripts/create_drtp_utr_q2_formal_tape.py`；`scripts/run_drtp_utr_q2_formal_single.py`；`tmp/cross_tape_reliability_20260827/assets/results/formal/drtp_utr_q2_paired_5seed_cloud_10way/formal_preflight.json`；同目录 `evaluations/final_10m/evaluation_manifest.json`。

## 5. 研究问题、端点与统计单位

| RQ | 可回答问题 | 主要端点 | 独立单位 | 证据层级 |
|---|---|---|---|---|
| RQ1 | 有界自适应重加权是否改变典型中期继电故障与跨条件故障端点？ | `J_F0`、11 个非名义条件的平均/最差 `J`、名义 `J` | 训练 seed（配对 n=5） | E1 |
| RQ2 | 这种差异伴随何种超时、碰撞、约束违规及故障触发有效性权衡？ | timeout、collision、constraint、failure exposure/trigger | 训练 seed；episode 仅为 seed 内估计 | E1；E3 补充 |
| RQ3 | 采样器是否确实改变训练暴露？ | `q`、`q` 对均匀分布的 L1 距离、组选择/暴露日志 | 训练 seed | E3 |
| RQ4 | 新队列与训练排除条件如何限定主结论？ | A/B 分队列端点；保留结构/参数条件 | 各队列训练 seed | E2/E3/E4 |
| RQ5 | 哪些替代解释被控制，哪些仍不可识别？ | 配置相等性、同带评价、触发有效性、PLR-style 匹配比较、机制审计 | 设计与审计单元 | E1–E4 |

## 6. 已证实结论

1. E1 中，DRTP 相对 UTR 的配对 `J_F0`、跨条件平均 `J` 和跨条件最差 `J` 的均值与中位数均为正，三项各有 5/5 训练种子正向；名义 `J` 的中位数差为正、4/5 种子正向。详见 E1 决策 JSON 和配对 CSV。
2. E1 中，故障超时率平均降低，碰撞率平均略升，但约束违规均为 0；故而可写“所定义任务端点及超时表现改善，碰撞并未同步单调改善”，不能写“更安全”。
3. DRTP 采样器在 reset 层面以完成 episode 回报的 EMA 形成组间相对难度，经过平滑和有界单纯形投影更新 `q`；其日志记录这一改变。它证实训练暴露改变，未证实策略内在机制。

## 7. 不能支持的结论

- DRTP 对所有训练 seed、所有故障模型或所有规模始终更优。
- 训练支持内的 timing/duration 条件是严格 OOD。
- `q` 偏离均匀分布导致了信息恢复、角色重分工或某种特定泛化机制。
- 任务回报提高等同于碰撞、约束或真实飞行安全的全面改善。
- PLR-style 在一队列落后即可证明其一般劣于 DRTP；反之亦然。
- 旧 6-UAV 结果可支持跨规模结论。

## 8. 风险与 TODO

1. `TODO（需补证）`：获得并审计修复后 6-UAV v2 的有效故障触发、最终 checkpoint、同带端点评估和下载归档；旧 6-UAV 不可使用。
2. `TODO（需补证）`：用冻结且匹配的源码、硬件和并发设置测量 UTR/DRTP wall-clock、采样更新开销与峰值显存。
3. `TODO（需补证）`：若语义/固定权重消融完成，应独立验证其训练带、种子、同一支持集合和终点评估；在此之前不能据 PLR 或遥测把收益归因于“拓扑语义”。
4. 历史 n=3 held-out 队列出现严重不利实现，且机制诊断没有找到稳定、可行动的训练期前兆；这限制稳健性与机制主张的外推。

**负向证据来源：** `docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md`；`diagnostics/drtp_cohort_reversal_20260828/05_report/cohort_reversal_forensic_report.md`；`docs/drtp_b5_final_review_20260830/B5_FINAL_MECHANISM_REVIEW.md`。
