# DRTP 实验驱动写作：证据登记册

> 本登记册只记录本次初稿实际采用的代码、配置、原始结果归档与审计材料。`paper/`、`paper_latex*/`、`paper_submission*/` 均未作为事实来源。

## 证据层级

| 层级 | 证据 | 用途与可信度边界 |
|---|---|---|
| E1：主要受控证据 | `tmp/cross_tape_reliability_20260827/assets/results/formal/drtp_utr_q2_paired_5seed_cloud_10way/formal_preflight.json`；同目录 `formal_tape_manifest.json`、`evaluations/final_10m/evaluation_manifest.json`、`evaluations/final_10m/DRTP_UTR_Q2_FORMAL_DECISION.json`、`evaluations/final_10m/per_seed_condition_summary.csv`、`evaluations/final_10m/paired_seed_results.csv` | 唯一用于“在该冻结合同下，DRTP 相对 UTR 的受控端点差异”的主要证据。五个训练种子是独立单位；100 个 episode/条件仅用于估计每个训练种子的端点。 |
| E1：设计与实现核验 | `scripts/create_drtp_utr_q2_formal_tape.py`；`scripts/run_drtp_utr_q2_formal_single.py`；`tests/test_drtp_utr_q2_formal.py`；`algorithms/ri_gmappo/drtp_topology_sampler.py` | 核验共同种子、共同 10M 预算、最终检查点、名义质量、故障组、以及 UTR/DRTP 的唯一变化项。 |
| E2：独立队列的相关比较 | `D:/File/Downloads/drtp_stabilization_A_complete_results.tar.gz`；`D:/File/Downloads/drtp_stabilization_B_complete_results.tar.gz` 内的 `.../reaggregation_repair_v1/diagnostics/*/CONFIRMATION_REPORT.json`；`configs/drtp_stabilization_final_freeze.json`；`configs/drtp_stabilization_independent_replication_freeze.json`；`scripts/run_drtp_stabilization_confirmatory_single.py` | 两个新五种子队列保留 UTR 与原始 DRTP 臂，但同时服务于后续稳定化候选筛选；与 E1 协议和研究目的不完全相同。因此分队列描述，不同 E1 合并，也不作为 E1 的样本扩增。 |
| E2：匹配的外部优先级参考 | `configs/drtp_plr_external_formal_freeze_20260906.json`；`D:/File/Downloads/drtp_plr_matched_ab_results.tar.gz` 内 `diagnostics/plr_matched_ab_final/*.csv` 与 `PLR_MATCHED_AB_FINAL_REPORT.md` | 配置声明同环境、奖励、actor/critic、PPO、容量、预算与终点评估带。它用于定位 DRTP 与一种 PLR-style 优先级信号的相对表现；但不替代 UTR–DRTP 的单变量主要因果对照，也不能单独证明“拓扑语义导致”任何差异。 |
| E3：后验结构保留端点评估 | `configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json`；`D:/File/Downloads/drtp_final_evidence_heldout_ood_results.tar.gz` 内 `diagnostics/final_heldout_ood/*.csv` | 训练时不可访问的结构/参数条件端点。它在既有端点训练完成后执行，故仅可作为冻结后验的保留测试；不扩写为前瞻性确认性泛化。结构条件中只有超出训练支持的节点/边修改可称为“支持外结构条件”，而训练组内的时序和时长条件不得称为严格 OOD。 |
| E3：训练分布遥测 | E1 与 A/B 归档内 `runs/drtp_sg/seed*/drtp_topology_sampler_log.csv`；`algorithms/ri_gmappo/drtp_topology_sampler.py` | 可以确认 `q`、实际选择和暴露记录偏离均匀分布；不能据此识别策略内部信息恢复、因果行为机制或普适泛化机制。 |
| E4：负向与机制边界 | `docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md`；`diagnostics/drtp_cohort_reversal_20260828/05_report/cohort_reversal_forensic_report.md`；`docs/drtp_b5_final_review_20260830/B5_FINAL_MECHANISM_REVIEW.md`；`docs/drtp_b5_final_review_20260830/B5_FINAL_DECISION.json` | 历史独立三种子端点含一个严重反向 seed；训练期遥测不足以确认一个可行动的失稳前兆；B5 未支持“失败组信用分配”机制。它们限制、而非否定 E1 的条件性结果。 |
| 排除 | `D:/File/Downloads/drtp_6uav_cross_scale_fresh_restart_v1_results.tar.gz`；以及任何 `paper/`、`paper_latex*/`、`paper_submission*/` 文本 | 已知旧 6-UAV 运行的故障在 episode 结束后才注入，非名义条件的有效故障触发为零；不能作为跨规模性能证据。旧稿件只可能帮助发现术语，未参与事实判定。 |

## 任务与接口事实来源

| 主题 | 文件 | 已核验事实 |
|---|---|---|
| 环境 | `envs/uav_intercept_3d_env.py` | 三架蓝方异构 UAV 与一架目标；轻量 3DOF 离散转向、爬升、速度动作；默认最大 260 步。 |
| 合法信息边界 | `envs/uav_intercept_3d_env.py`：`_is_comm_failed`、`_radar_visible`、`_has_fresh_target_cache`、`_attacker_cache_path_is_legal` | 继电节点故障在预设窗口内令其通信失效；继电依赖任务中，攻击者远离终端感知包络时必须依赖合法送达的目标缓存；故障后可用直接 Scout→Attacker 路径仅是受时序约束的恢复路径。 |
| 任务端点 | `envs/uav_intercept_3d_env.py`：`step`、`_info`；`scripts/run_drtp_stabilization_confirmatory_evaluation.py` | 端点评价分开记录回报 `J`、成功、超时、碰撞、约束违规与控制量；任务得分不得替代安全结论。 |
| 主要干预 | `algorithms/ri_gmappo/drtp_topology_sampler.py` | 仅在 reset 时选择已冻结的条件；不向观测、奖励或 PPO 损失添加变量。UTR 对故障组条件均匀分配；DRTP 用完成 episode 回报的组 EMA 相对于名义组构造难度并对 `q` 作有界更新。 |

## 对本初稿有效的结论边界

1. E1 支持的主张只限于：在该三 UAV、继电节点故障、固定 10M 训练与固定终点评估合同下，DRTP 与 UTR 的端点比较。
2. E1 的 11 个非名义条件均来自训练时冻结的故障组成员，故本文将它们称为“跨条件故障端点”，**不称为严格 OOD**。
3. 后验结构保留测试含支持外节点/边结构，但并非在原始 E1 训练前形成的确认性泛化试验；只能作补充、分队列报告。
4. 任何队列均不以 episode、条件或 rollout 作为独立训练重复；不报告由此产生的伪独立显著性检验。
5. 6-UAV、运行开销与语义消融的合格终点材料目前未在本地核验到，统一标记 `TODO（需补证）`。
