# 无人机协同决策课题当前实施进度与下一步计划

日期：2026-07-13

## 0. 最新状态修正

截至 2026-07-13，当前主线已经从早期 RI-GMAPPO 调整为：

```text
EA-RG-MAPPO-S = Edge-Aware Role Graph MAPPO
              + Staged random-radius fine-tuning
```

原因是目标意图辅助分支的诊断结果显示 balanced accuracy 不足，暂不能作为论文主创新点。当前可以稳定支撑论文的主张是：

```text
边特征增强角色图能够在有限通信下提升协同追逃稳定性；
分阶段随机通信半径微调能够改善跨通信半径鲁棒性；
EA-RG-MAPPO-S 相比 MAPPO/GAT-MAPPO 显著降低碰撞率并降低种子间波动。
```

后续所有实验、论文草稿和图表应以 EA-RG-MAPPO-S 为主线。意图预测只保留为探索性诊断，不写成主贡献。

## 0.1 最新推进：LAG 图接口适配

已新增一层面向 LAG-like 6DOF 状态的 role graph 适配接口：

```text
envs/lag_role_graph_adapter.py
envs/lag_role_graph_wrapper.py
scripts/test_lag_role_graph_adapter.py
scripts/test_lag_role_graph_wrapper.py
docs/lag_role_graph_adapter_test.md
docs/lag_role_graph_wrapper_test.md
results/lag_role_graph_adapter_test.csv
results/lag_role_graph_wrapper_test.csv
```

当前测试结论：

```text
python scripts/test_lag_role_graph_adapter.py
checks=26, failed=0
node_feat=(4, 15), edge_feat=(4, 4, 13), adj=(4, 4)

python scripts/test_lag_role_graph_wrapper.py
checks=11, failed=0
reset/step passthrough and graph refresh OK
```

现实含义：

```text
1. 当前 EA-RG-MAPPO-S 的图表示已经能对接 LAG-like aircraft state；
2. wrapper 已提供 `reset/step -> graph` 的最小调用链，方便后续接真实 LAG runner；
3. 这一步只验证接口、张量形状和图不变量，不声称真实 JSBSim 训练已经完成；
4. 后续补齐 LAG JSBSim data/submodule 后，可以优先把真实 reset/step 接到该适配层，而不需要重写算法主干。
```

## 0.2 最新推进：跨条件综合鲁棒性摘要

已新增综合鲁棒性摘要，用于压缩展示最终跨半径评估和通信 dropout 诊断的整体趋势：

```text
scripts/analyze_aggregate_robustness.py
results/aggregate_robustness_summary.csv
results/aggregate_robustness_summary.md
results/latex_aggregate_robustness_table.tex
```

当前关键结果：

```text
Final cross-radius:
EA-RG-MAPPO-S mean_success=0.903, mean_collision=0.072, conservative_margin=0.793.

Dropout diagnostic:
EA-RG-MAPPO-S mean_success=0.892, mean_collision=0.070, conservative_margin=0.747.
```

现实含义：

```text
1. 该摘要能帮助论文和答辩快速说明“跨半径/通信退化下整体更稳”；
2. 它不是新的训练目标，也不是标准 benchmark 指标；
3. 论文具体结论仍应以逐半径主表、dropout 表和 seed-paired 统计为主。
```

## 0.3 最新推进：通信半径插值诊断

已新增未见通信半径 $5,7,9$ 的轻量评估，用于检查主表半径 $4,6,8,10$ 之间的插值稳定性：

```text
scripts/evaluate_radius_interpolation.py
results/radius_interpolation_eval.csv
results/radius_interpolation_summary.csv
results/radius_interpolation_notes.md
results/latex_radius_interpolation_table.tex
results/figures/radius_interpolation_success_rate.png
results/figures/radius_interpolation_collision_rate.png
```

当前关键结果：

```text
radius=5: EA collision=0.067, MAPPO=0.227, GAT=0.113
radius=7: EA collision=0.100, MAPPO=0.200, GAT=0.140
radius=9: EA collision=0.067, MAPPO=0.153, GAT=0.173
```

现实含义：

```text
1. 该诊断增强“跨通信半径稳定性不是只在主表四个半径上成立”的可信度；
2. 它是 50 episodes per seed 的附录级评估，不替代 300-episode 主表；
3. 论文中应写成未见半径诊断或插值证据，不写成全半径完备验证。
```

## 0.4 最新推进：图表资产质量审计

已新增图表资产审计，用于检查投稿图是否存在、尺寸是否合理、是否近似空白：

```text
scripts/audit_figure_assets.py
docs/figure_asset_audit.md
results/figure_asset_audit.csv
```

当前结果：

```text
figures_checked = 22
warnings = 0
```

现实含义：

```text
1. 当前论文用 PNG 图像均能被读取，尺寸和像素变化正常；
2. 该审计能防止后续构建时出现空白图、损坏图或漏图；
3. 它是技术资产检查，不替代人工排版和图表审美检查。
```

## 0.5 最新推进：实验预算一致性审计

已新增实验预算一致性审计，用于防止不同 episode budget 的结果被混用：

```text
scripts/audit_evaluation_budget_consistency.py
docs/evaluation_budget_audit.md
results/evaluation_budget_audit.csv
```

当前结果：

```text
budget_groups_checked = 6
failures = 0
```

覆盖范围：

```text
final_main = 300 episodes per seed
ablation = 100 episodes per seed
speed_robustness = 100 episodes per seed
comm_dropout = 50 episodes per seed
radius_interpolation = 50 episodes per seed
edge_feature_masking = 30 episodes per seed
```

现实含义：

```text
1. 主表和附录诊断的预算边界更清楚；
2. 后续修改 caption 或 CSV 时会自动暴露预算不一致；
3. 论文仍应在正文中明确区分主结果和附录级诊断。
```

## 0.6 最新推进：方法命名一致性审计

已新增方法命名一致性审计，用于区分论文最终方法名和历史代码目录名：

```text
scripts/audit_method_naming_consistency.py
docs/method_naming_audit.md
results/method_naming_audit.csv
```

当前结果：

```text
publishable_files_checked = 27
mapping_checks = 1
failures = 0
```

命名规则：

```text
论文方法名：EA-RG-MAPPO-S
允许的代码/结果目录映射：ri_gmappo_edge_stage2_rand_seed*_20
RI-GMAPPO / RI edge 等旧路线名称只保留在内部历史日志中，不进入投稿正文。
```

## 0.7 最新推进：结果溯源审计

已新增结果溯源审计，用于把投稿资产和生成链路绑定起来：

```text
scripts/audit_result_provenance.py
docs/result_provenance_audit.md
results/result_provenance_audit.csv
```

当前结果：

```text
artifacts_checked = 54
tables = 11
figures = 22
reports = 11
audits = 10
failures = 0
```

覆盖范围：

```text
1. 主表、统计表、附录诊断表；
2. 22 张当前 PNG 图表；
3. 图表资产、实验预算、方法命名、英文稿准备度等审计报告；
4. LAG/JSBSim 迁移探针和 role graph adapter/wrapper 测试报告。
```

现实含义：

```text
后续改图、改表、打包补充材料时，可以直接追踪每个资产来自哪个 CSV 或脚本，降低写论文和投稿返修阶段的断链风险。
```

## 0.8 最新推进：补充数据说明 README

已新增补充数据说明文档，用于给审稿补充材料中的 CSV 做用途和预算边界说明：

```text
scripts/write_supplemental_data_readme.py
docs/supplemental_data_readme.md
```

该 README 覆盖主结果、dropout、半径插值、速度鲁棒性、edge feature 诊断、审计 CSV 和 LAG 迁移接口诊断数据。核心边界是：

```text
主结论只以 final_comm_300_summary.csv 为主要定量依据；
100/50/30 episode 文件作为附录或机制诊断；
LAG/JSBSim 文件只作为迁移准备证据，不作为真实 6DOF 验证。
```

## 0.9 最新推进：补充 CSV schema 审计

已新增补充 CSV schema 审计，用于固定结果数据文件的结构和关键取值域：

```text
scripts/audit_supplemental_csv_schema.py
docs/supplemental_csv_schema_audit.md
results/supplemental_csv_schema_audit.csv
```

当前结果：

```text
csv_files_checked = 31
failures = 0
```

检查内容：

```text
1. 每个 CSV 的必需列和行数；
2. 主结果/诊断结果的方法名、seed、通信半径、episode budget、target speed；
3. 审计 CSV 的 status 字段；
4. success/collision/timeout 等 rate 列是否保持在 [0, 1]。
```

现实含义：

```text
后续如果重跑实验、改图表脚本或整理补充材料，字段名、行数或关键取值一变，构建门禁会立即报错。
```

## 0.10 最新推进：主张-证据矩阵

已新增主张-证据矩阵，用于约束论文写作时每条主张的证据来源和措辞边界：

```text
scripts/write_claim_evidence_matrix.py
docs/claim_evidence_matrix.md
results/claim_evidence_matrix.csv
```

当前结果：

```text
claims_checked = 9
failures = 0
```

覆盖主张：

```text
1. 300-episode 主结果有限通信稳定性；
2. seed-paired 描述性统计；
3. 通信 dropout 诊断；
4. 跨条件综合鲁棒性；
5. 通信半径插值泛化；
6. 目标速度鲁棒性；
7. edge feature masking 机制诊断；
8. LAG/JSBSim 扩展边界；
9. intent branch 不能作为主贡献的负向边界。
```

现实含义：

```text
论文写作时可以直接按该矩阵取证据和措辞，避免把附录诊断写成主结果，或把 LAG 接口准备误写成完整 6DOF 验证。
```

## 0.11 最新推进：稿件证据引用审计

已新增稿件证据引用审计，用于检查中英文 LaTeX 是否实际引用主张矩阵要求的证据：

```text
scripts/audit_manuscript_evidence_references.py
docs/manuscript_evidence_reference_audit.md
results/manuscript_evidence_reference_audit.csv
```

当前结果：

```text
references_checked = 51
failures = 0
```

本轮同时补强了中文稿边界措辞：

```text
1. 明确 intent 分支 balanced accuracy = 0.200，不能作为强主张；
2. 明确当前结果不能被写成完整 6DOF 空战验证；
3. 明确 intent 分支不作为本文主贡献。
```

现实含义：

```text
证据矩阵不再只是工程文档；中英文稿件必须实际包含对应表、图、数值和限制性表述，否则构建门禁会失败。
```

## 0.12 最新推进：双语数值一致性审计

已新增双语数值一致性审计，用于从结果 CSV 派生关键数值，并检查这些数值是否同时出现在中英文 LaTeX 稿件中：

```text
scripts/audit_bilingual_numeric_consistency.py
docs/bilingual_numeric_consistency_audit.md
results/bilingual_numeric_consistency_audit.csv
```

当前结果：

```text
numeric_markers_checked = 47
failures = 0
```

本轮同时补强了中英文主结果段：

```text
1. 英文主结果补充 radius=6 和 radius=8 的 success/collision 数值；
2. 中文主结果补充 radius=6 和 radius=8 的 success/collision 数值；
3. edge masking 仍以表格承载具体数值，正文只保留机制趋势描述。
```

现实含义：

```text
如果后续手工改中文或英文稿件导致关键数字与 CSV 不一致，构建门禁会直接失败。
```

## 0.13 最新推进：LaTeX 标签引用完整性审计

已新增中英文 LaTeX 标签引用完整性审计：

```text
scripts/audit_latex_reference_integrity.py
docs/latex_reference_integrity_audit.md
results/latex_reference_integrity_audit.csv
```

当前结果：

```text
reference_checks = 86
failures = 0
```

检查内容：

```text
1. 中英文稿件关键表格和图像 label 是否存在；
2. 主表、附录表和核心图是否被正文引用；
3. 是否存在重复 label；
4. 是否存在 ref 指向不存在 label 的情况。
```

现实含义：

```text
后续调整 LaTeX 图表、重命名 label 或移动附录时，引用断裂会在构建阶段暴露，而不是等到最终编译或投稿检查时才发现。
```

## 0.14 最新推进：双语稿件完整性审计

已新增中英文 LaTeX 稿件完整性审计：

```text
scripts/audit_bilingual_manuscript_completeness.py
docs/bilingual_manuscript_completeness_audit.md
results/bilingual_manuscript_completeness_audit.csv
```

当前结果：

```text
checks = 36
failures = 0
action_items = 8
```

检查内容：

```text
1. 中英文 main.tex 和 8 个章节文件是否存在；
2. title、author、abstract、keywords、bibliography、result table input、figure、citation 是否完整；
3. 主体文字规模是否达到继续投稿化改写的最低要求；
4. intent/6DOF 等关键边界标记是否保留；
5. 作者、数据可用性、基金/利益声明、期刊 BibTeX 样式等投稿前行动项。
```

现实含义：

```text
当前稿件没有结构性硬错误，可以继续进入期刊模板迁移；尚未确定的作者和期刊声明类事项被保留为 action item，不阻断实验与证据链构建。
```

## 0.15 最新推进：投稿行动项清单

已新增投稿行动项清单，用于把分散在准备度报告和稿件完整性审计中的剩余事项集中管理：

```text
scripts/write_submission_action_register.py
docs/submission_action_register.md
results/submission_action_register.csv
```

当前结果：

```text
items = 10
blocked = 2
deferred = 1
open = 7
```

其中 blocked 项：

```text
1. 当前运行环境缺少 LaTeX 工具链，无法验证 PDF 排版；
2. LAG/JSBSim 真实 reset/step 仍受缺失 data 子模块和导入问题阻塞。
```

现实含义：

```text
当前证据链和稿件源文件可继续推进；真正投稿前还需要选择期刊模板、补作者与声明、在完整 LaTeX 环境编译 PDF，并决定是否补 5-seed 或真实 LAG 小实验。
```

## 0.16 最新推进：实验扩展决策计划

已新增实验扩展决策计划，用于决定后续是否补新实验，以及哪些路线应推迟到第二篇：

```text
scripts/write_experiment_extension_decision_plan.py
docs/experiment_extension_decision_plan.md
results/experiment_extension_decision_plan.csv
```

当前结果：

```text
options = 7
ready = 3
deferred = 3
blocked = 1
```

核心结论：

```text
1. 若目标是 practical Q2 投稿，应优先做期刊模板/PDF 迁移，而不是贸然开启完整 6DOF；
2. 若导师或审稿人要求更强证据，再考虑 5-seed 主结果扩展或真实 LAG reset/step 探针；
3. 完整 6DOF 训练、导弹/雷达/有人机协同应作为后续系统级课题，不应挤进当前论文主张；
4. 规则/mask 只能作为工程约束或辅助设计，不写成主创新点。
```

## 0.17 最新推进：稳定 artifact checksum 清单

已新增稳定复现包 checksum 清单：

```text
scripts/write_reproducibility_checksum_manifest.py
docs/reproducibility_checksum_manifest.md
results/reproducibility_checksum_manifest.csv
scripts/verify_reproducibility_checksum_manifest.py
docs/reproducibility_checksum_verification.md
results/reproducibility_checksum_verification.csv
```

当前结果：

```text
artifacts_hashed = 169
artifacts_verified = 169
failures = 0
```

设计边界：

```text
1. 记录稳定复现包文件的 size 和 SHA256；
2. 排除 paper_asset_build_report、supplemental_data_readme、schema/provenance 自身、checksum 自身和 verification 输出等动态文件；
3. verifier 逐项复算 size 和 SHA256，适合在移动项目、打包补充材料或发给导师前验证文件未损坏或被替换。
```

## 0.18 最新推进：checksum manifest 反向验证

已新增 checksum manifest 的反向验证器：

```text
scripts/verify_reproducibility_checksum_manifest.py
docs/reproducibility_checksum_verification.md
results/reproducibility_checksum_verification.csv
```

当前设计：

```text
1. 先由 write_reproducibility_checksum_manifest.py 生成稳定 artifact 的 size/SHA256；
2. 再由 verify_reproducibility_checksum_manifest.py 读取 manifest 并复算每个文件；
3. 任一文件缺失、size 不一致或 SHA256 不一致都会使脚本失败；
4. verification 输出本身不进入 checksum manifest，避免自引用导致每次运行都改变哈希。
```

## 0.19 最新推进：3DOF 异构协同拦截环境第一版

为把课题从 2D toy pursuit 升级到具备二区潜力的航空任务实验，已新增 3DOF 3v1 异构协同拦截环境：

```text
envs/uav_intercept_3d_env.py
scripts/smoke_test_intercept_3d_env.py
docs/intercept_3d_smoke_test.md
results/intercept_3d_smoke_test.csv
```

当前环境包含：

```text
1. 蓝方 3 架异构 UAV：侦察、通信中继、攻击；
2. 红方 1 个高价值目标，采用规则逃逸机动；
3. 三维位置、速度、航向、航迹倾角；
4. 高度、速度、转弯率、爬升角和边界约束；
5. 雷达探测范围、水平/垂直视场和 radar dropout；
6. 通信半径、communication dropout、消息年龄和通信连通率；
7. 攻击窗口判定、攻击窗口保持和杀伤链闭合指标；
8. 与当前训练框架兼容的 reset/step/graph_obs 接口。
```

smoke test 当前结果：

```text
episodes = 15
obs shape = (3, 34)
share_obs shape = (3, 47)
node_feat shape = (4, 20)
edge_feat shape = (4, 4, 18)

geometric success = 0.800
geometric attack_window_rate = 0.266
geometric_dropout success = 0.800
random success = 0.000
```

现实含义：

```text
1. 3DOF 主实验环境的最小接口已跑通；
2. 几何启发式策略明显强于随机策略，说明环境不是纯随机噪声；
3. 当前结果只证明环境可执行和指标可记录，不证明 EA-RG-MAPPO-S 已在 3DOF 上训练成功；
4. 下一步应让 train_ri_gmappo.py 支持 2d_pursuit / 3d_intercept 环境切换，并先跑 3DOF 小规模训练。
```

## 1. 当前研究定位

当前课题已经从泛泛的“无人机强化学习”收敛到一个可执行方向：

> 面向异构无人机协同追逃/拦截任务，研究有限通信条件下的角色感知图多智能体强化学习方法，并进一步引入目标意图预测，提高混合机动目标下的协同决策鲁棒性。

更新后的准确表述应改为：

> 面向异构无人机协同追逃/拦截任务，研究有限通信条件下的边特征增强角色图多智能体强化学习方法，通过显式建模相对距离、方位、速度差和通信可达性，并结合分阶段随机通信半径微调，提高混合机动目标下的协同决策稳定性和安全性。

现阶段不是直接做 6DOF 空战、导弹、雷达和有人机协同完整系统，而是先在低维可控环境中把算法创新点验证出来。这样做的现实原因是：

1. 实验成本低，训练和调参能快速迭代。
2. 变量可控，容易判断改进来自算法而不是仿真复杂度。
3. 成功后可以自然迁移到 LAG/JSBSim 这类 6DOF 框架，不需要完全另起炉灶。
4. 更符合研究生阶段“先做出可发表结果，再逐步扩展系统复杂度”的实际路径。

早期拟定的主线方法为：

```text
RI-GMAPPO = MAPPO
          + role-aware graph representation
          + target intent prediction
          + communication-limited attention
```

该路线已被修正。当前主线方法为：

```text
EA-RG-MAPPO-S = MAPPO
              + role-aware graph representation
              + edge-aware graph attention
              + communication-radius masking
              + staged random-radius fine-tuning
```

其中，规则策略只作为环境验证和实验辅助，不能作为论文主创新点。

## 2. 已完成工作

### 2.1 文献与方向梳理

已完成对本地论文资料和近期相关方向的初步梳理，形成的判断是：

- 纯规则空战/追逃策略不适合作为主创新点。
- 单纯套用 MAPPO、MADDPG、PPO 等算法也不够。
- 图网络、多智能体协同、有限通信、目标意图预测、课程学习和可解释性更适合作为论文创新来源。
- 直接上 6DOF 空战系统风险较高，应作为第二阶段或第三阶段扩展。

阶段判断：

```text
低维可控环境验证算法创新 -> 迁移到 LAG/JSBSim -> 扩展导弹/雷达/有人机协同
```

### 2.2 LAG 项目调研

已检查 `work/LAG`，结论如下：

- LAG 是可借鉴的 6DOF/JSBSim 空战强化学习框架。
- 它包含 PPO/MAPPO、自博弈、SingleCombat、MultipleCombat、Missile、TacView 等模块。
- 它适合作为后续 6DOF 迁移平台。
- 它不适合作为第一阶段直接改造基础，因为图表示、意图预测、有限通信注意力等模块缺失，直接在 LAG 上改会增加调试成本。

当前决策：

```text
第一阶段：自建轻量 2D/简化环境验证 RI-GMAPPO
第二阶段：把有效模块迁移到 LAG/JSBSim
```

### 2.3 已搭建项目

当前项目路径：

```text
C:/Users/96251/Documents/Codex/2026-07-12/ni/work/ri_gmappo_uav
```

核心结构：

```text
envs/uav_pursuit_env.py                  # 2D 异构无人机追逃环境
baselines/rule_policy.py                 # 规则策略，仅用于验证
algorithms/mappo/simple_mappo.py         # MAPPO 基线
algorithms/gat_mappo/simple_gat_mappo.py # hybrid GAT-MAPPO
scripts/train_mappo.py                   # MAPPO 训练
scripts/train_gat_mappo.py               # GAT-MAPPO 训练
scripts/evaluate_model.py                # MAPPO 评估
scripts/evaluate_gat_model.py            # GAT-MAPPO 评估
results/                                 # 实验结果和记录
```

Python 环境：

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe
torch 2.4.1+cu124
CUDA available: True
```

### 2.4 环境验证

已实现的环境能力：

- 3 架异构追击无人机 + 1 个目标。
- 离散 9 动作机动控制。
- 支持局部观测、集中 critic 状态、图观测。
- 支持目标策略：
  - `straight`
  - `random`
  - `nearest_escape`
  - `mixed`
- 支持目标速度参数 `--target-speed`。
- 奖励包含：
  - 团队接近目标进度；
  - 个体接近目标进度；
  - 距离势函数；
  - 朝向目标奖励；
  - 近距离碰撞惩罚；
  - 成功/碰撞终止奖励。

环境验证结果说明：

- 随机策略成功率低，超时多。
- 规则策略成功率高但仍有碰撞。
- 说明任务不是完全随机可解，也不是过难不可学，适合作为强化学习验证环境。

## 3. 当前实验结果

### 3.1 MAPPO 课程学习结果

训练设置：

```text
target-policy = straight
target-speed  = 0.45
updates       = 150
num-envs      = 16
rollout-steps = 128
lr            = 0.001
```

最终结果：

| 场景 | 成功率 | 碰撞率 | 说明 |
|---|---:|---:|---|
| straight, speed 0.45 | 1.00 | 0.00 | 已稳定学会 |
| straight, speed 0.75 | 0.80 | 0.20 | 有一定迁移 |
| random, speed 0.75 | 0.97 | 0.03 | 表现较好 |
| mixed, speed 0.75 | 0.87 | 0.12 | 当前最稳基线 |

判断：

MAPPO 基线已经可用，后续所有创新方法都必须与它公平比较。

### 3.2 GAT-MAPPO 结果

第一版纯 GAT 失败：

```text
success_rate = 0.30
timeout_rate = 0.70
```

原因判断：

纯图特征替代局部观测后，模型丢失了重要的 ego-relative 信息。

因此改为 hybrid GAT：

```text
policy_input = concat(local_obs_embedding, graph_agent_embedding)
```

hybrid GAT 可以学会课程任务，但迁移结果仍弱于 MAPPO。

100 回合 mixed/0.75 评估：

| 方法 | 成功率 | 碰撞率 | 超时率 | 平均步数 |
|---|---:|---:|---:|---:|
| MAPPO 课程 checkpoint | 0.87 | 0.12 | 0.01 | 51.99 |
| Hybrid GAT-MAPPO 课程 checkpoint | 0.82 | 0.14 | 0.05 | 54.94 |

判断：

单纯加入图注意力不能作为主创新点。它最多作为 RI-GMAPPO 的一个组成部分或消融对照。

### 3.3 mixed 目标微调实验

已比较两种微调方式：

1. 直接微调：`lr=5e-4`
2. 保守微调：`lr=1e-4`，并保存 best checkpoint

100 回合独立评估：

| 方法 | Checkpoint | 成功率 | 碰撞率 | 超时率 | 平均步数 |
|---|---|---:|---:|---:|---:|
| MAPPO | pre fine-tune | 0.87 | 0.12 | 0.01 | 51.99 |
| Hybrid GAT-MAPPO | pre fine-tune | 0.82 | 0.14 | 0.05 | 54.94 |
| MAPPO | direct FT, lr=5e-4, latest | 0.76 | 0.24 | 0.00 | 65.07 |
| Hybrid GAT-MAPPO | direct FT, lr=5e-4, latest | 0.70 | 0.21 | 0.09 | 69.53 |
| MAPPO | conservative FT, lr=1e-4, best | 0.86 | 0.10 | 0.04 | 56.17 |
| Hybrid GAT-MAPPO | conservative FT, lr=1e-4, best | 0.83 | 0.11 | 0.06 | 54.06 |

实验结论：

- 直接 mixed 微调会破坏已有策略，不应作为默认训练方案。
- 保守微调更稳，但没有显著超过原课程 checkpoint。
- 当前真正需要做的是引入新的有效信息，而不是继续堆普通 GAT 或盲目加长训练。

## 4. 当前代码改动状态

已完成：

1. `UAVPursuitEnv` 环境构建。
2. 规则策略 baseline。
3. MAPPO 基线训练、评估、checkpoint 保存。
4. hybrid GAT-MAPPO 训练、评估。
5. MAPPO/GAT-MAPPO 的 best checkpoint 保存逻辑。
6. mixed fine-tune 对照实验记录。

近期新增/更新的关键文件：

```text
algorithms/mappo/simple_mappo.py
algorithms/gat_mappo/simple_gat_mappo.py
scripts/evaluate_model.py
scripts/evaluate_gat_model.py
results/mappo_baseline_notes.md
results/gat_mappo_notes.md
results/mixed_finetune_comparison.md
```

当前已有结果说明：

```text
MAPPO 可作为强基线。
GAT-MAPPO 可作为消融基线。
EA-RG-MAPPO-S 已完成实现、训练、消融和 300-episode 多半径复评。
目标意图分支已有诊断结果，但 balanced accuracy 不足，不作为论文主创新点。
当前主结果应围绕有限通信鲁棒性、碰撞率下降和跨半径稳定性展开。
```

## 5. 当前风险判断

### 5.1 不能夸大的结论

目前不能写：

```text
当前方法实现了可靠目标意图识别。
当前实验已经验证完整 6DOF 空战、导弹、雷达、有人机协同系统。
EA-RG-MAPPO-S 在所有可能场景和所有指标上都全面最优。
```

目前可以写：

```text
在二维异构无人机协同追逃环境中，EA-RG-MAPPO-S 在有限通信半径下表现出更高成功率、更低碰撞率和更低种子间波动；
相对边特征和分阶段随机通信半径微调是当前实验中最稳定的有效成分。
```

### 5.2 最大技术风险

当前最大风险已经从“创新模块能否有效”转为：

```text
论文证据链是否足够完整，以及方法能否在更高保真环境中保持趋势。
```

因此后续不应再频繁改主方法，而应围绕现有主线补强：

1. 更正式的文献支撑；
2. 更清晰的消融和可视化解释；
3. 复现实验脚本和 artifact 完整性；
4. LAG/JSBSim 小规模迁移可行性验证。

### 5.3 论文风险

要支撑较好期刊投稿，仍需注意：

1. 近期 UAV arXiv 文献不能承担核心理论依据，需要继续补正式期刊/会议文献。
2. 意图预测诊断结果不能作为正贡献，只能作为负结果或探索性说明。
3. 2D 环境结果必须写成“算法机制验证”，不能冒充完整空战系统验证。
4. 如果时间允许，应补一个 LAG/JSBSim 轻量迁移实验，哪怕只验证接口和趋势。

## 6. 下一步计划

### 阶段 A：论文证据链加固

目标：把现有实验结果整理成可投稿叙事。

需要完成：

1. 继续补充 UAV 有限通信、协同追逃、安全约束相关正式文献；
2. 将 `docs/reference_quality_audit.md` 的审计结果同步到 Related Work；
3. 在中文初稿和 LaTeX 中统一主张边界；
4. 确保所有表格、图片、脚本、checkpoint 都能追溯到实验命令。

### 阶段 B：补充低成本实验

优先级从高到低：

1. 通信半径随机训练/固定训练的对比曲线；
2. edge-aware attention 去除不同边特征分量的轻量消融；
3. 目标速度或目标机动强度的小型泛化测试；
4. 失败案例轨迹可视化，用来解释碰撞下降原因。

这些实验应尽量复用现有训练结果和评估脚本，避免重新开启大规模训练。

### 阶段 C：LAG/JSBSim 小迁移

迁移顺序：

1. 只接入 LAG 的 NoWeapon 或最简多机任务；
2. 保留 LAG 飞行动力学和环境接口；
3. 先移植 observation-to-graph 构建逻辑，而不是完整重训论文主模型；
4. 验证角色图、边特征、通信 mask 在 LAG 状态空间中能否构造；
5. 再决定是否训练 EA-RG-MAPPO-S 的 6DOF 版本。

判断：

这不是另起炉灶。当前 2D 阶段的网络结构、实验指标、消融逻辑和论文主张都能迁移；需要重做的是环境适配和训练调参。

## 7. 近期三步执行清单

### Step 1：完成文献与引用质量加固

已完成第一轮：补入 PPO、MADDPG、COMA、VDN、QMIX、GAT、MAPPO 等基础引用，并新增 `docs/reference_quality_audit.md`。

下一步继续查找 UAV 有限通信和追逃方向的正式期刊/会议文献，替换或补强当前 UAV arXiv 近例。

### Step 2：做轻量消融与图表补强

优先生成不需要重新训练或只需短评估的材料：

```text
edge feature ablation summary
random-radius vs fixed-radius summary
failure/success trajectory comparison
attention behavior explanation
```

当前已新增 edge feature 评估时消融：

```text
scripts/evaluate_edge_feature_ablation.py
results/edge_feature_ablation_eval.csv
results/edge_feature_ablation_summary.csv
results/edge_feature_ablation_notes.md
results/figures/edge_feature_ablation_delta.png
```

结论边界：该实验只说明评估时边特征屏蔽呈弱敏感性，不能替代训练期消融；其中 `comm_reachable` 和 `target_node_flag` 被屏蔽时退化最一致。

当前已新增目标速度泛化评估：

```text
scripts/evaluate_speed_robustness.py
scripts/plot_speed_robustness.py
results/speed_robustness_eval.csv
results/speed_robustness_summary.csv
results/speed_robustness_notes.md
results/figures/speed_robustness_success_r4.png
results/figures/speed_robustness_collision_r4.png
results/figures/speed_robustness_success_r8.png
results/figures/speed_robustness_collision_r8.png
```

结论边界：该实验是 100-episode 附录级泛化评估，支撑“低碰撞优势不只来自单一 target_speed 设置”，但不替代 300-episode 主表。

### Step 3：准备 LAG 迁移检查清单

输出一个独立文档，明确：

```text
LAG 中可用状态量；
如何构造 node_feat/edge_feat/adj；
哪些模块能直接复用；
哪些模块必须重写；
第一轮 smoke test 的最低标准。
```

当前已新增：

```text
docs/lag_migration_checklist.md
scripts/lag_graph_smoke_test.py
results/lag_graph_smoke_stats.csv
```

synthetic 模式已通过，说明状态到角色图的构造逻辑可运行。真实 LAG 模式目前卡在 `work/LAG/envs/JSBSim/data` 缺失，需补完整 JSBSim data/submodule 后再继续。

## 8. 2026-07-13 更新：RI-GMAPPO v1 已实现

本轮已完成 RI-GMAPPO v1 的第一版实现和快速对照实验。

新增文件：

```text
algorithms/ri_gmappo/__init__.py
algorithms/ri_gmappo/simple_ri_gmappo.py
scripts/train_ri_gmappo.py
scripts/evaluate_ri_gmappo.py
results/ri_gmappo_v1_notes.md
```

环境更新：

```text
graph_obs 增加 intent_label
```

RI-GMAPPO v1 结构：

```text
policy_input = concat(local_obs_embedding, graph_agent_embedding, predicted_intent_embedding)
```

快速实验结论：

| 方法 | mixed/0.75 100 回合成功率 | 碰撞率 | 超时率 | 意图准确率 |
|---|---:|---:|---:|---:|
| MAPPO 课程 checkpoint | 0.87 | 0.12 | 0.01 | n/a |
| Hybrid GAT-MAPPO 课程 checkpoint | 0.82 | 0.14 | 0.05 | n/a |
| RI-GMAPPO v1, intent_coef=0.1 | 0.86 | 0.11 | 0.03 | 0.58 |
| RI-GMAPPO ablation, intent_coef=0.0 | 0.88 | 0.10 | 0.02 | 0.08 |

当前判断：

```text
RI-GMAPPO v1 已经可训练，且 intent head 能学到一定意图信息；
但 intent_coef=0.1 还没有带来明确性能提升，不能声称“意图预测显著提升性能”。
```

更现实的下一步：

```text
先做 intent_coef 扫描和 oracle-intent 诊断，
确认“目标意图”对控制是否真的有价值，
再决定是否继续扩展边特征和通信 mask。
```

### 8.1 意图诊断实验更新

已完成 `detach_intent` 和 `oracle_intent` 两个诊断开关，并完成 30-update 快速实验。

100 回合独立评估结果：

| 方法 | mixed/0.75 成功率 | 碰撞率 | 超时率 | 平均步数 | 意图准确率 |
|---|---:|---:|---:|---:|---:|
| RI-GMAPPO, intent_coef=0.03 | 0.83 | 0.13 | 0.04 | 59.75 | 0.59 |
| RI-GMAPPO, detach_intent, intent_coef=0.05 | 0.90 | 0.07 | 0.04 | 51.18 | 0.58 |
| RI-GMAPPO, oracle_intent | 0.89 | 0.09 | 0.03 | 49.05 | 0.06 |

关键判断：

```text
detach_intent + intent_coef=0.05 是目前最有希望的 RI-GMAPPO 版本。
它首次在成功率和碰撞率上同时超过 MAPPO 课程 checkpoint。
```

但该结论还只是单 seed 快速实验，不能直接写成论文结论。下一步必须做多 seed 和通信受限评估。

### 8.2 3-seed 重复实验更新

已完成 `detach_intent + intent_coef=0.05` 的 seed 0/1/2 重复实验。

100 回合 mixed/0.75 独立评估：

| Seed | 成功率 | 碰撞率 | 超时率 | 平均步数 | 意图准确率 |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.90 | 0.07 | 0.04 | 51.18 | 0.58 |
| 1 | 0.94 | 0.05 | 0.01 | 56.16 | 0.59 |
| 2 | 0.84 | 0.11 | 0.05 | 55.81 | 0.38 |

均值和标准差：

```text
success_rate    = 0.893 ± 0.050
collision_rate  = 0.077 ± 0.031
timeout_rate    = 0.033 ± 0.021
avg_steps       = 54.38 ± 2.78
intent_accuracy = 0.516 ± 0.115
```

更新判断：

```text
RI-GMAPPO detach-intent 的均值优于 MAPPO 课程 checkpoint，
但 seed=2 不够强，说明方法仍有稳定性风险。
```

因此下一步不应立刻迁移 LAG，也不应直接写论文主结论。应该先做通信半径压力测试，并考虑加入相对边特征提高稳定性。

### 8.3 通信半径压力测试更新

已加入 `--communication-radius` 参数，并让局部队友观测受通信半径约束：

```text
如果队友超出通信半径，其局部观测槽位清零。
```

这使通信压力测试比之前更严格，也更符合有限通信设定。

代表性 checkpoint 的 100 回合 mixed/0.75 评估如下：

| 方法 | 半径 | 成功率 | 碰撞率 | 超时率 | 平均步数 |
|---|---:|---:|---:|---:|---:|
| MAPPO | 4 | 0.39 | 0.43 | 0.19 | 124.50 |
| GAT-MAPPO | 4 | 0.85 | 0.14 | 0.01 | 82.88 |
| RI-GMAPPO | 4 | 0.94 | 0.05 | 0.02 | 65.50 |
| MAPPO | 6 | 0.56 | 0.41 | 0.04 | 107.44 |
| GAT-MAPPO | 6 | 0.82 | 0.14 | 0.04 | 87.79 |
| RI-GMAPPO | 6 | 0.95 | 0.04 | 0.01 | 62.84 |
| MAPPO | 8 | 0.57 | 0.39 | 0.05 | 92.96 |
| GAT-MAPPO | 8 | 0.74 | 0.24 | 0.02 | 85.35 |
| RI-GMAPPO | 8 | 0.95 | 0.04 | 0.01 | 62.87 |
| MAPPO | 10 | 0.79 | 0.19 | 0.02 | 79.38 |
| GAT-MAPPO | 10 | 0.76 | 0.21 | 0.03 | 80.18 |
| RI-GMAPPO | 10 | 0.92 | 0.05 | 0.03 | 71.07 |

当前判断：

```text
通信压力测试是目前最强的正结果。
RI-GMAPPO 在有限通信下明显比 MAPPO 和普通 GAT-MAPPO 更稳。
```

但这仍然是代表性 checkpoint 评估。下一步应补 RI-GMAPPO seed 1/2 的通信压力评估，确认这个优势不是 seed 0 偶然结果。

### 8.4 RI-GMAPPO 通信压力 3-seed 更新

已完成 RI-GMAPPO detach-intent 的 seed 0/1/2 通信压力评估。

均值和标准差如下：

| 半径 | 成功率 | 碰撞率 | 超时率 | 平均步数 | 意图准确率 |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.907 ± 0.042 | 0.080 ± 0.044 | 0.017 ± 0.006 | 73.20 ± 7.60 | 0.537 ± 0.089 |
| 6 | 0.917 ± 0.076 | 0.063 ± 0.059 | 0.023 ± 0.023 | 72.77 ± 11.41 | 0.550 ± 0.064 |
| 8 | 0.887 ± 0.146 | 0.097 ± 0.125 | 0.017 ± 0.021 | 72.00 ± 13.45 | 0.538 ± 0.089 |
| 10 | 0.907 ± 0.071 | 0.073 ± 0.059 | 0.020 ± 0.017 | 72.04 ± 10.18 | 0.532 ± 0.094 |

当前判断：

```text
有限通信方向仍然是目前最强、最像论文主线的结果。
RI-GMAPPO 在均值上保持了较高成功率和较低碰撞率。
```

但风险也很明确：

```text
seed=2 在半径 8 时下降到 success=0.72, collision=0.24。
这说明方法有潜力，但训练稳定性还不够。
```

下一步应优先增强稳定性，而不是直接迁移 LAG。建议方向：

1. 加入相对边特征，让图注意力看到距离、方位、相对速度。
2. 做更严格的 checkpoint selection，避免训练内 20 回合 best 选择偶然偏差。
3. 补一张通信压力折线图，作为后续论文主图雏形。

### 8.5 相对边特征实验更新

已实现 edge-aware RI-GMAPPO。

边特征包含：

```text
相对位置、距离、相对方位、相对速度、通信可达标记、目标节点标记
```

核心结果：

```text
seed=2, radius=8 的弱点从
success=0.72, collision=0.24
提升到
success=0.86-0.90, collision=0.09-0.10
```

3-seed edge-aware 通信压力均值：

| 半径 | 成功率 | 碰撞率 | 超时率 | 平均步数 |
|---:|---:|---:|---:|---:|
| 4 | 0.927 ± 0.021 | 0.037 ± 0.015 | 0.037 ± 0.006 | 65.85 ± 2.78 |
| 6 | 0.887 ± 0.015 | 0.073 ± 0.032 | 0.040 ± 0.036 | 63.41 ± 2.20 |
| 8 | 0.900 ± 0.036 | 0.083 ± 0.012 | 0.020 ± 0.026 | 63.78 ± 4.58 |
| 10 | 0.837 ± 0.032 | 0.113 ± 0.015 | 0.050 ± 0.017 | 73.36 ± 4.12 |

判断：

```text
边特征能修复 radius=8 的不稳定，并显著降低 radius=4 的碰撞；
但固定在 radius=8 训练会损害 radius=10 泛化。
```

因此下一步不是直接定稿 edge-aware 方法，而是加入通信半径随机化训练：

```text
训练时每个 episode 从 [4, 10] 随机采样 communication_radius。
```

如果随机半径训练能同时保持 radius=4/8 的优势并恢复 radius=10 表现，那么 RI-GMAPPO + edge-aware attention 就更适合作为最终主方法。

随机半径训练已做第一轮 seed=2 快速测试：

| Checkpoint | 半径 | 成功率 | 碰撞率 | 超时率 |
|---|---:|---:|---:|---:|
| best | 4 | 0.81 | 0.12 | 0.07 |
| best | 6 | 0.90 | 0.09 | 0.01 |
| best | 8 | 0.90 | 0.06 | 0.04 |
| best | 10 | 0.85 | 0.10 | 0.05 |
| latest | 4 | 0.75 | 0.19 | 0.07 |
| latest | 6 | 0.87 | 0.08 | 0.06 |
| latest | 8 | 0.87 | 0.09 | 0.04 |
| latest | 10 | 0.80 | 0.12 | 0.09 |

判断：

```text
朴素随机半径训练暂时没有带来预期收益。
它削弱了 radius=4 表现，也没有充分恢复 radius=10。
```

下一步更现实的是先改进 checkpoint selection：

```text
训练时 20 回合 best 选择波动太大；
需要用 100 回合验证脚本统一选择 checkpoint。
```

这一步会让后续结果更可信，也能降低“偶然选到好/坏 checkpoint”的干扰。

已新增统一评估脚本：

```text
scripts/evaluate_ri_run.py
```

功能：

```text
给定一个 RI-GMAPPO run 目录，
自动评估 actor_critic_best.pt 和 actor_critic_latest.pt，
在多个通信半径下输出 CSV。
```

后续所有 RI 变体都应先用这个脚本做统一评估，再决定是否进入多 seed 或画图阶段。

### 8.6 分阶段随机半径微调更新

已完成 seed=2 的 staged random-radius fine-tuning。

方案：

```text
stage 1: edge-aware radius=8 训练
stage 2: 从 stage-1 best checkpoint 出发，用 lr=3e-5 做短程随机半径微调
```

结果：

| Variant | R4 成功/碰撞 | R8 成功/碰撞 | R10 成功/碰撞 |
|---|---:|---:|---:|
| edge fixed-r8 best | 0.95 / 0.02 | 0.86 / 0.09 | 0.85 / 0.11 |
| naive random-radius best | 0.81 / 0.12 | 0.90 / 0.06 | 0.85 / 0.10 |
| staged random-radius best | 0.93 / 0.03 | 0.86 / 0.12 | 0.91 / 0.06 |

判断：

```text
分阶段微调比朴素随机半径训练更合理。
它恢复了 radius=10 泛化，同时基本保住 radius=4。
但 radius=8 没有提升，甚至碰撞略高。
```

下一步：

```text
补跑 seed0/seed1 的 staged random-radius fine-tune。
如果三 seed 均值更均衡，再把 staged edge-aware RI-GMAPPO 作为主方法候选。
```

seed0/seed1 已补跑，并完成三 seed 汇总。

staged random-radius latest checkpoint 均值：

| 半径 | 成功率 | 碰撞率 | 超时率 |
|---:|---:|---:|---:|
| 4 | 0.907 ± 0.012 | 0.067 ± 0.012 | 0.027 ± 0.012 |
| 6 | 0.907 ± 0.015 | 0.073 ± 0.021 | 0.020 ± 0.010 |
| 8 | 0.883 ± 0.051 | 0.083 ± 0.031 | 0.033 ± 0.032 |
| 10 | 0.880 ± 0.020 | 0.090 ± 0.026 | 0.033 ± 0.021 |

当前主方法候选：

```text
RI-GMAPPO + edge-aware attention + detach intent + staged random-radius fine-tuning
```

这个版本不是每个半径都最强，但整体最均衡，尤其恢复了 radius=10 泛化。

下一步应从“继续盲目训练”转向“整理论文式结果”：

1. 生成通信半径-成功率折线图。
2. 生成通信半径-碰撞率折线图。
3. 汇总 MAPPO/GAT/RI/no-edge/edge/staged 的方法对比表。
4. 检查是否还需要补某个关键 baseline 的多 seed。

已生成论文式结果材料：

```text
results/paper_result_tables.md
results/paper_comm_results.csv
results/figures/comm_success_rate.png
results/figures/comm_collision_rate.png
scripts/plot_comm_results.py
```

当前最关键缺口：

```text
MAPPO/GAT-MAPPO/RI 的通信压力主表均已有 3-seed 均值。
下一步缺口从“补基线”转为“可解释分析和主方法定稿”。
```

### 8.7 GAT-MAPPO 多 seed 基线补强

已完成 GAT-MAPPO seed1/seed2 的两阶段训练，并完成 seed0/seed1/seed2 的通信半径压力测试。

训练配置与 seed0 保持一致：

```text
stage 1: straight, speed=0.45, updates=60, lr=1e-3
stage 2: resume stage-1 latest, updates=90, lr=5e-4
```

新增脚本：

```text
scripts/evaluate_gat_runs.py
```

生成结果：

```text
results/gat_comm_multi_seed_eval.csv
results/gat_comm_multi_seed_summary.csv
```

GAT-MAPPO 3-seed 通信压力均值：

| 半径 | 成功率 | 碰撞率 | 超时率 | 平均步数 |
|---:|---:|---:|---:|---:|
| 4 | 0.840 ± 0.037 | 0.127 ± 0.012 | 0.040 ± 0.042 | 70.21 ± 14.32 |
| 6 | 0.873 ± 0.045 | 0.097 ± 0.031 | 0.030 ± 0.022 | 64.53 ± 17.87 |
| 8 | 0.777 ± 0.052 | 0.183 ± 0.040 | 0.043 ± 0.048 | 67.52 ± 15.51 |
| 10 | 0.797 ± 0.029 | 0.170 ± 0.033 | 0.033 ± 0.029 | 69.51 ± 11.50 |

对当前主方法的影响：

```text
GAT-MAPPO 多 seed 后仍在 radius=8/10 明显弱于 RI edge staged。
这增强了“意图感知 + 边特征 + 分阶段随机半径微调”主方法的可信度。
```

但也说明：

```text
GAT-MAPPO 在 radius=4/6 并不弱，因此论文中不能简单写“GAT 全面失败”。
更合理的表述是：普通图注意力能缓解有限通信问题，但在更复杂通信半径下稳定性不足；
引入目标意图和相对边特征后，碰撞率和跨半径稳定性进一步改善。
```

### 8.8 MAPPO 多 seed 基线补强

已完成 MAPPO seed1/seed2 的课程训练，并完成 seed0/seed1/seed2 的通信压力测试。

训练配置：

```text
straight, speed=0.45, updates=150, num_envs=16, rollout_steps=128, lr=1e-3
```

新增脚本：

```text
scripts/evaluate_mappo_runs.py
```

生成结果：

```text
results/mappo_comm_multi_seed_eval.csv
results/mappo_comm_multi_seed_summary.csv
```

MAPPO 3-seed 通信压力均值：

| 半径 | 成功率 | 碰撞率 | 超时率 | 平均步数 |
|---:|---:|---:|---:|---:|
| 4 | 0.690 ± 0.212 | 0.240 ± 0.135 | 0.073 ± 0.083 | 85.40 ± 30.28 |
| 6 | 0.777 ± 0.158 | 0.217 ± 0.141 | 0.013 ± 0.019 | 68.69 ± 29.24 |
| 8 | 0.800 ± 0.167 | 0.180 ± 0.151 | 0.023 ± 0.021 | 62.21 ± 24.59 |
| 10 | 0.850 ± 0.054 | 0.143 ± 0.046 | 0.007 ± 0.009 | 58.90 ± 17.53 |

关键修正：

```text
原 MAPPO seed0 代表性结果偏弱，不能作为唯一基线。
多 seed 后，MAPPO 在部分 seed 下很强，但方差很大，尤其 radius=4/6/8。
```

对论文主张的影响：

```text
不能写 RI-GMAPPO “大幅全面超过 MAPPO”。
更稳妥、更真实的主张是：
RI-GMAPPO 在有限通信下提升了跨半径稳定性，并显著降低碰撞率；
相比 MAPPO，它的均值更稳、方差更小；相比 GAT-MAPPO，它在 radius=8/10 更有优势。
```

## 9. 当前总体进度判断

按完整课题推进估计：

```text
方向确定：已完成
文献和方案：已完成初版
环境搭建：已完成
MAPPO 基线：已完成
MAPPO 多 seed 通信基线：已完成
GAT-MAPPO 消融：已完成初版
GAT-MAPPO 多 seed 通信基线：已完成
mixed 微调对照：已完成
RI-GMAPPO 主方法：已完成 v1 初版
完整消融实验：已完成部分核心项，仍缺可解释分析和最终方法选择
可视化分析：未开始
LAG/6DOF 迁移：未开始
论文撰写：未开始
```

当前进度大约处于：

```text
第一阶段算法验证的 72%-78%
```

下一步最重要的是开始做可视化分析，并决定最终主方法采用 `RI edge fixed-r8` 还是 `RI edge staged`。

建议执行顺序：

1. 生成 MAPPO/GAT/RI 在 radius=4 和 radius=10 下的成功/失败轨迹图。
2. 生成 RI intent head 的混淆矩阵，确认意图预测不是摆设。
3. 对比 `RI edge fixed-r8` 与 `RI edge staged`，确定论文主方法和消融命名。
4. 更新论文式方法表和图表说明。

## 10. 可视化与意图诊断更新

已生成首批轨迹案例图：

```text
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
```

轨迹案例结论：

```text
radius=4: MAPPO 碰撞，GAT 和 RI 成功。
radius=10: GAT 碰撞，MAPPO 和 RI 成功。
```

这些图适合作为论文中的 qualitative case study，但不能替代多 seed 表格。

同时完成 RI intent head 混淆矩阵诊断：

```text
results/figures/intent_confusion_ri_staged_r8.png
results/intent_confusion_ri_staged_r8.csv
```

关键发现：

```text
plain accuracy = 0.587
balanced accuracy = 0.200
```

这说明当前 intent head 基本塌缩为预测 `escape_nearest`，plain accuracy 主要来自类别不平衡。

已尝试 class-balanced intent loss 诊断微调：

```text
results/ri_gmappo_edge_balanced_intent_seed1_20
results/figures/intent_confusion_ri_balanced_seed1_r8.png
results/intent_confusion_ri_balanced_seed1_r8.csv
```

结果：

```text
plain accuracy = 0.348
balanced accuracy = 0.203
```

判断：

```text
仅靠类别加权不能修复 intent head。
当前单帧 mixed-policy intent 标签可观测性不足，不能把“准确意图识别”作为强论文结论。
```

下一步方向需要调整：

1. 如果继续保留意图作为主创新，应加入短时历史或目标转弯率等可观测运动特征，并用 balanced accuracy 汇报。
2. 如果优先保证论文能投出，应把主创新收敛到 `edge-aware role graph coordination under limited communication`，把 intent branch 降级为辅助模块或消融项。

## 11. Per-Seed 附录材料更新

已生成 per-seed 通信压力附录表：

```text
results/per_seed_comm_appendix.csv
results/per_seed_comm_appendix.md
```

已生成 per-seed 散点图：

```text
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
```

作用：

```text
这些材料能展示不同随机种子下的分布，而不只是均值。
当前图表会更清楚地显示 MAPPO 的 seed 方差较大，而 EA-RG-MAPPO-S 的跨半径表现更集中。
```

下一步建议：

```text
开始写论文实验部分的初稿，包括环境、基线、评价指标、训练协议和通信压力设置。
```

## 12. 方法章节和投稿检查清单更新

已新增方法章节初稿：

```text
docs/paper_method_section_draft.md
```

已新增方法框图：

```text
scripts/plot_method_overview.py
results/figures/method_overview_ea_rg_mappo_s.png
```

已新增投稿前检查清单：

```text
docs/submission_readiness_checklist.md
```

当前推荐下一步：

```text
整合完整论文草稿骨架，而不是继续无目标地增加实验。
```

已新增完整论文骨架和材料索引：

```text
docs/paper_full_draft_outline.md
docs/paper_asset_index.md
```

已新增 Related Work 文献综述和 BibTeX 初版：

```text
docs/related_work_literature_review.md
docs/references_seed.bib
```

已生成 LaTeX 主结果表：

```text
scripts/make_latex_tables.py
results/latex_main_comm_table.tex
```

已完成最终 300-episode 通信压力复评：

```text
scripts/evaluate_final_comm_300.py
results/final_comm_300_eval.csv
results/final_comm_300_summary.csv
results/latex_final_comm_300_table.tex
results/final_300_eval_notes.md
```

关键结果：

```text
EA-RG-MAPPO-S radius=4 success=0.926 ± 0.004, collision=0.054 ± 0.007
EA-RG-MAPPO-S radius=6 success=0.919 ± 0.012, collision=0.064 ± 0.006
EA-RG-MAPPO-S radius=8 success=0.890 ± 0.021, collision=0.083 ± 0.012
EA-RG-MAPPO-S radius=10 success=0.879 ± 0.017, collision=0.086 ± 0.020
```

判断：

```text
300-episode 复评进一步增强了有限通信稳定性和低碰撞率主张。
这张表应作为论文最终主表；100-episode 全消融表作为消融/附录表。
```

已生成 300-episode 最终主图：

```text
scripts/plot_final_300_results.py
results/figures/final_300_success_rate.png
results/figures/final_300_collision_rate.png
```

已生成连续中文论文初稿 v1：

```text
docs/paper_manuscript_zh_v1.md
```

当前下一步：

```text
1. 将中文初稿中的公式改为正式 LaTeX；
2. 统一图表编号和引用；
3. 补充中文/英文文献引用；
4. 可选：做 LAG/JSBSim 小规模迁移验证。
```

已新增 LaTeX 论文工程：

```text
paper_latex/main.tex
paper_latex/sections/
paper_latex/references.bib
paper_latex/README.md
```

静态检查已确认章节、图片、最终表格和 bib 文件存在；当前运行环境未找到 `xelatex`，因此 PDF 编译尚未验证。

已新增 LaTeX 静态检查脚本：

```text
scripts/check_latex_project.py
```

当前检查结果：

```text
checked tex files: 28
bib keys: 9
OK
```

已新增并接入 LaTeX 消融表：

```text
results/latex_ablation_comm_table.tex
paper_latex/sections/05_experiments.tex
paper_latex/sections/06_discussion.tex
paper_latex/sections/07_conclusion.tex
```

当前表格策略：

```text
最终主表：results/latex_final_comm_300_table.tex
消融表：results/latex_ablation_comm_table.tex
```

已新增复现清单和项目级 artifact 检查：

```text
docs/reproducibility_manifest.md
scripts/check_reproducibility_artifacts.py
```

当前检查结果：

```text
required files checked: 68
required scripts checked: 18
OK
```

## 13. 最新质量门槛更新

已新增并接入论文定量主张一致性检查：

```text
scripts/check_paper_claim_consistency.py
```

检查范围：

```text
1. 最终主表中 EA-RG-MAPPO-S 的低碰撞主张；
2. target_speed=0.90 速度泛化附录中的低碰撞主张；
3. edge feature 评估时屏蔽诊断中的弱敏感性和 comm/target 标记退化主张。
```

已新增并接入论文文本风险审计：

```text
scripts/check_paper_text_risk.py
```

检查范围：

```text
1. 发布稿中不能出现旧路线残留；
2. 不能正向声称已验证完整 6DOF 空战、导弹、雷达、有人机协同系统；
3. 不能正向声称当前方法实现高精度目标意图识别；
4. 不能正向声称所有指标全面最优。
```

当前最新检查结果：

```text
python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

## 32. 最新状态索引

当前最新新增实验证据：

```text
通信 dropout 退化鲁棒性诊断，见本文件第 31 节。
核心文件：
scripts/evaluate_comm_dropout_robustness.py
results/comm_dropout_robustness_eval.csv
results/comm_dropout_robustness_summary.csv
results/comm_dropout_robustness_notes.md
results/latex_comm_dropout_robustness_table.tex
results/comm_dropout_paired_statistics.csv
results/comm_dropout_paired_statistics.md
results/latex_comm_dropout_paired_ci_table.tex
```

当前最新质量门禁：

```text
python scripts/build_paper_assets.py: OK
python scripts/check_latex_project.py: checked tex files: 32; bib keys: 14, 14; OK
python scripts/check_paper_claim_consistency.py: final_main, speed_robustness, edge_masking, paired_ci, comm_dropout; OK
python scripts/check_english_latex_consistency.py: english latex files checked: 9; required markers checked: 17; OK
python scripts/check_paper_text_risk.py: text risk files checked: 30; OK
python scripts/check_reproducibility_artifacts.py: required files checked: 79; required scripts checked: 22; OK
```

当前最建议的下一步：

```text
1. 若继续实验增强：优先 LAG/JSBSim 最小迁移，而不是继续扩大轻量 dropout 诊断；
2. 若推进投稿：让导师确定 Drones / Aerospace / JIRS 首投目标，然后执行 docs/journal_template_migration_plan.md；
3. 论文主张保持为有限通信下的边特征角色图协同鲁棒性，不扩展成完整空战系统已验证。
```

## 31. 通信 dropout 退化鲁棒性诊断

本轮围绕“有限通信下稳定性”新增通信链路随机丢失诊断。

代码改动：

```text
envs/uav_pursuit_env.py
scripts/evaluate_comm_dropout_robustness.py
```

环境改动：

```text
1. UAVPursuitConfig 新增 communication_dropout_prob，默认 0.0；
2. 默认值不改变已有训练和评估行为；
3. 评估时可对 pursuer-pursuer 通信边进行随机 dropout；
4. dropout 同步作用于 teammate local-observation 槽、graph adjacency 和 edge reachability；
5. target observation node 仍保留，该诊断只模拟无人机之间的通信链路退化；
6. dropout 使用独立 RNG，避免改变 mixed target policy 的随机轨迹序列。
```

新增结果：

```text
results/comm_dropout_robustness_eval.csv
results/comm_dropout_robustness_summary.csv
results/comm_dropout_robustness_notes.md
results/latex_comm_dropout_robustness_table.tex
```

实验设置：

```text
methods = MAPPO, GAT-MAPPO, EA-RG-MAPPO-S
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 8
communication_dropout_prob = 0.00, 0.25, 0.50
episodes = 50 per seed
seeds = 0, 1, 2
mode = evaluation-time communication dropout, no retraining
```

关键结果：

```text
dropout=0.50, radius=4:
EA-RG-MAPPO-S collision = 0.047
MAPPO collision = 0.300
GAT-MAPPO collision = 0.167

dropout=0.50, radius=8:
EA-RG-MAPPO-S collision = 0.053
MAPPO collision = 0.293
GAT-MAPPO collision = 0.173
```

论文使用边界：

```text
可以写：通信链路随机丢失诊断进一步支持 EA-RG-MAPPO-S 的低碰撞鲁棒性。
不能写：该 50-episode 诊断替代 300-episode 主表，或证明真实无线链路/复杂网络干扰已被完整验证。
```

已接入：

```text
paper_latex/sections/08_appendix_experiments.tex
paper_latex_en/sections/08_appendix_experiments.tex
scripts/check_paper_claim_consistency.py
scripts/analyze_comm_dropout_statistics.py
scripts/check_english_latex_consistency.py
scripts/check_reproducibility_artifacts.py
scripts/write_submission_package_manifest.py
docs/evidence_chain_status.md
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
```

最新验证：

```text
python scripts/build_paper_assets.py
Runtime environment report: OK
Checkpoint inventory: OK
Submission readiness report: OK
Submission package manifest: OK
English manuscript readiness audit: OK
Final 300 paired statistics: OK
LaTeX tables: OK
Final 300 figures: OK
Communication ablation figures: OK
Per-seed appendix: OK
Edge feature ablation figure: OK
Speed robustness figures: OK
LAG graph synthetic smoke: OK
LaTeX static check: OK
Quantitative claim consistency: OK
English LaTeX consistency: OK
Paper text risk audit: OK
Reproducibility artifact gate: OK

python scripts/check_latex_project.py
checked tex files: 32
bib keys: 14, 14
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking, paired_ci, comm_dropout
OK

python scripts/check_english_latex_consistency.py
english latex files checked: 9
required markers checked: 17
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 79
required scripts checked: 22
OK
```

下一步建议：

```text
1. 不建议继续扩大 dropout 诊断为主实验，除非导师明确要求；
2. 若要增强工程真实性，下一步优先做 LAG/JSBSim 最小迁移或目标期刊模板迁移；
3. 论文主线仍保持为 edge-aware role graph coordination under limited communication。
```

## 26. 投稿包清单与最终材料入口补全

本轮新增并接入投稿包清单：

```text
docs/submission_package_manifest.md
scripts/write_submission_package_manifest.py
```

清单作用：

```text
1. 区分中文 LaTeX 投稿包、英文 LaTeX 投稿包、共享图表和表格；
2. 标出可作为 supplementary evidence 的 CSV、报告和 checkpoint 映射；
3. 明确哪些内容属于内部过程材料，不应直接放入期刊投稿；
4. 明确当前运行环境尚未准备好的项目：PDF 编译、目标期刊模板、真实 LAG/JSBSim 验证。
```

已接入：

```text
scripts/build_paper_assets.py
scripts/check_reproducibility_artifacts.py
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
```

本轮完整验证：

```text
python scripts/build_paper_assets.py
Runtime environment report: OK
Checkpoint inventory: OK
Submission readiness report: OK
Submission package manifest: OK
LaTeX tables: OK
Final 300 figures: OK
Communication ablation figures: OK
Per-seed appendix: OK
Edge feature ablation figure: OK
Speed robustness figures: OK
LAG graph synthetic smoke: OK
LaTeX static check: OK
Quantitative claim consistency: OK
English LaTeX consistency: OK
Paper text risk audit: OK
Reproducibility artifact gate: OK

python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14, 14
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking
OK

python scripts/check_english_latex_consistency.py
english latex files checked: 9
required markers checked: 16
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 69
required scripts checked: 19
OK
```

当前结论：

```text
研究证据链、论文材料索引、中英文 LaTeX 工程、自动构建脚本和可复现 artifact gate 已经闭环。
仍未闭环的是 PDF 实际编译与目标期刊模板适配，因为当前 cac 环境缺少 xelatex/latexmk/bibtex。
```

下一步建议：

```text
1. 先做英文 LaTeX 语言压缩和期刊化表达；
2. 再选择一个二区候选期刊，按其模板迁移 paper_latex_en/；
3. 若要继续增强实验，可优先补一个轻量 statistical significance / confidence interval 附录，而不是重训主模型。
```

## 27. 最终主结果 seed 配对统计附录

本轮新增最终 300-episode 主实验的 seed 配对描述性统计：

```text
scripts/analyze_final_300_statistics.py
results/final_300_paired_statistics.csv
results/final_300_paired_statistics.md
results/latex_final_300_paired_ci_table.tex
```

统计方式：

```text
1. 按 method / seed / communication radius 对齐；
2. 对 EA-RG-MAPPO-S 相对 MAPPO 和 GAT-MAPPO 分别计算配对差值；
3. success_gain = EA success - baseline success；
4. collision_reduction = baseline collision - EA collision；
5. n=3 seeds，使用 df=2 的 95% t 区间，只作为描述性证据，不作为强显著性主张。
```

主要发现：

```text
EA-RG-MAPPO-S 相对 MAPPO 和 GAT-MAPPO 在所有通信半径上的平均 success_gain 与 collision_reduction 均为正。
相对 GAT-MAPPO，radius=4 的 collision_reduction 95% 描述性区间为 [0.039, 0.123]。
相对 GAT-MAPPO，radius=8 的 success_gain 和 collision_reduction 区间分别为 [0.005, 0.206] 与 [0.005, 0.186]。
相对 MAPPO 的区间较宽，原因是 MAPPO seed 间方差较大；正文中不能写成所有半径均强显著。
```

已接入：

```text
scripts/build_paper_assets.py
scripts/check_reproducibility_artifacts.py
scripts/check_paper_claim_consistency.py
scripts/check_english_latex_consistency.py
scripts/write_submission_package_manifest.py
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
paper_latex/sections/08_appendix_experiments.tex
paper_latex_en/sections/08_appendix_experiments.tex
```

本轮完整验证：

```text
python scripts/build_paper_assets.py
Runtime environment report: OK
Checkpoint inventory: OK
Submission readiness report: OK
Submission package manifest: OK
Final 300 paired statistics: OK
LaTeX tables: OK
Final 300 figures: OK
Communication ablation figures: OK
Per-seed appendix: OK
Edge feature ablation figure: OK
Speed robustness figures: OK
LAG graph synthetic smoke: OK
LaTeX static check: OK
Quantitative claim consistency: OK
English LaTeX consistency: OK
Paper text risk audit: OK
Reproducibility artifact gate: OK

python scripts/check_latex_project.py
checked tex files: 30
bib keys: 14, 14
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking, paired_ci
OK

python scripts/check_english_latex_consistency.py
english latex files checked: 9
required markers checked: 16
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 72
required scripts checked: 20
OK
```

下一步建议：

```text
1. 对英文 LaTeX 正文做期刊风格压缩，重点减少方法和实验章节的重复解释；
2. 增加一个 journal target shortlist 文档，按二区、主题匹配、实验门槛和版式成本筛选投稿目标；
3. 安装或切换到有 xelatex/latexmk/bibtex 的环境后，优先编译 paper_latex_en/main.tex 并修版面问题。
```

## 28. 投稿期刊目标 shortlist

本轮新增投稿目标筛选文档：

```text
docs/journal_target_shortlist.md
```

筛选原则：

```text
1. 以当前已完成证据链为前提，不假设已经完成 6DOF/LAG/导弹/雷达系统；
2. 优先选择 UAV / aerospace / robotic systems 方向匹配的期刊；
3. 将审稿门槛、APC/出版模式、速度、当前证据充分性分开判断；
4. 不承诺 JCR/CAS 分区，投稿前必须通过学校数据库核验最新版。
```

当前建议顺序：

```text
1. Drones：最贴合 UAV/无人机主题，适合作为第一目标，前提是可接受 OA/APC 和 MDPI 风险；
2. Aerospace：航空航天工程方向匹配，适合有限通信 UAV 决策主线；
3. Journal of Intelligent & Robotic Systems：机器人/无人系统方向匹配，适合作为 Springer 路线；
4. IEEE Access：速度和范围友好，但主题不如前三个精准；
5. Robotics and Autonomous Systems：冲刺目标，建议补 LAG/6DOF 后再考虑；
6. Engineering Applications of Artificial Intelligence：高门槛冲刺目标，当前版本不建议首投。
```

已接入：

```text
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
scripts/check_reproducibility_artifacts.py
```

本轮验证：

```text
python scripts/check_reproducibility_artifacts.py
required files checked: 73
required scripts checked: 20
OK

python scripts/build_paper_assets.py
Submission package manifest: OK
Final 300 paired statistics: OK
Reproducibility artifact gate: OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK
```

下一步建议：

```text
1. 若优先实用投稿，选择 Drones 或 Aerospace，开始模板迁移；
2. 若导师更在意出版社/声誉，选择 Journal of Intelligent & Robotic Systems，按机器人/无人系统语言重写摘要和 introduction；
3. 若要冲击更强期刊，先补 LAG/JSBSim 或 6DOF 小实验，否则当前证据不足以支撑 RAS/EAAI。
```

## 29. 英文稿投稿化审计

本轮新增英文 LaTeX 投稿化审计脚本与报告：

```text
scripts/audit_english_manuscript_readiness.py
docs/english_manuscript_readiness_audit.md
```

审计覆盖：

```text
1. paper_latex_en/main.tex 和 8 个 section 的行数、词数、表格输入、图和 cite 命令数量；
2. title、abstract、keywords 是否存在；
3. 英文主文长度是否接近可投稿范围；
4. 2D/6DOF 边界、intent 辅助分支边界和统计证据标记是否存在；
5. 作者占位、Data/Code Availability、Funding/Conflict 声明、期刊模板 bibliography style 等投稿前动作项。
```

当前审计结果：

```text
Title words: 13
Abstract words: 200
Main-text words, excluding appendix: 3175
Total words, including appendix: 3831
LaTeX files checked: 9
Hard errors: 0
Action items: 4
```

当前 action items：

```text
1. 替换 paper_latex_en/main.tex 中的 author placeholder；
2. 选择目标期刊后添加 Data/Code Availability statement；
3. 按目标期刊要求添加 Funding、Conflict of Interest、Author Contributions 等声明；
4. 将 generic plain bibliography style 替换为目标期刊模板样式。
```

已接入：

```text
scripts/build_paper_assets.py
scripts/check_reproducibility_artifacts.py
scripts/write_submission_package_manifest.py
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
```

本轮验证：

```text
python scripts/build_paper_assets.py
English manuscript readiness audit: OK
Reproducibility artifact gate: OK

python scripts/check_reproducibility_artifacts.py
required files checked: 74
required scripts checked: 21
OK

python scripts/check_latex_project.py
checked tex files: 30
bib keys: 14, 14
OK

python scripts/check_english_latex_consistency.py
english latex files checked: 9
required markers checked: 16
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK
```

下一步建议：

```text
1. 先确定 Drones / Aerospace / JIRS 三者之一；
2. 根据目标期刊模板处理 author、声明和 bibliography style；
3. 继续把 air-combat/radar/missile/human-UAV 相关表述限制在 future work，不进入当前实验主张。
```

## 30. 三条首投路线的模板迁移计划

本轮新增目标期刊模板迁移计划：

```text
docs/journal_template_migration_plan.md
```

该文档给出三条首投路线：

```text
Route A: Drones
Route B: Aerospace
Route C: Journal of Intelligent & Robotic Systems
```

迁移策略：

```text
1. 当前 paper_latex_en/ 保持为通用英文源工程；
2. 选定目标期刊后，再新建 target-specific 文件夹，例如 paper_latex_en_drones/；
3. 先迁移模板、作者、声明、bibliography style 和图表格式；
4. 不提前把当前通用工程绑死到某一个期刊模板；
5. 保持主张边界：当前证据只验证 2D 有限通信 UAV 追逃，不验证完整 6DOF/导弹/雷达/有人机协同。
```

三个路线的实用判断：

```text
Drones：主题最贴合，适合实用首投，但需要和导师确认 OA/APC 与 MDPI 风险。
Aerospace：航空航天方向匹配，需强调这是决策层/协同层验证，不是完整飞控或武器交战验证。
JIRS：机器人/无人系统路线，需减少 air-combat 词汇，增加 multi-robot coordination 表述。
```

已接入：

```text
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
scripts/check_reproducibility_artifacts.py
scripts/write_submission_package_manifest.py
```

本轮验证：

```text
python scripts/check_reproducibility_artifacts.py
required files checked: 75
required scripts checked: 21
OK

python scripts/build_paper_assets.py
Submission package manifest: OK
English manuscript readiness audit: OK
Reproducibility artifact gate: OK
```

下一步建议：

```text
1. 让导师在 Drones / Aerospace / JIRS 三者中确定首投目标；
2. 目标确定后，复制 paper_latex_en/ 到对应 target-specific 文件夹；
3. 按 docs/journal_template_migration_plan.md 执行模板和声明迁移；
4. 在有 LaTeX 工具链的环境中编译 PDF 并修版面。
```

## 26. 投稿准备度报告补全

本轮新增投稿准备度报告脚本：

```text
scripts/write_submission_readiness_report.py
```

生成报告：

```text
docs/submission_readiness_report.md
```

报告结论：

```text
Research manuscript package is internally consistent and evidence-backed.
Not final submission-ready in this runtime because PDF rendering cannot be verified without a LaTeX toolchain.
Current strongest claim: EA-RG-MAPPO-S improves limited-communication stability and reduces collision in simplified 2D heterogeneous UAV pursuit.
Boundary: full 6DOF air combat, missile/radar modeling, and human-UAV teaming have not been experimentally validated yet.
```

报告自动检查：

```text
1. 中英文稿件材料是否存在；
2. 主结果表和关键图表是否存在；
3. 复现门禁脚本和报告是否存在；
4. EA-RG-MAPPO-S 最终 300-episode 主结果是否满足当前成功率/碰撞率阈值；
5. 当前运行环境是否具备 PDF 编译工具链。
```

当前主要剩余限制：

```text
1. xelatex/latexmk/bibtex 当前不可用，因此 PDF 版面尚未验证；
2. 尚未套目标期刊模板；
3. 真实 LAG/JSBSim smoke test 仍受缺失 JSBSim data/submodule 限制。
```

当前检查结果：

```text
python scripts/build_paper_assets.py
Submission readiness report: OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

## 14. 论文材料一键构建更新

已新增轻量级论文材料构建脚本：

```text
scripts/build_paper_assets.py
```

该脚本只基于已有结果重建表格、图片和附录材料，并运行质量门禁；不重新训练策略，也不重新跑长评估。已生成构建报告：

```text
docs/paper_asset_build_report.md
```

当前一键构建结果：

```text
python scripts/build_paper_assets.py
LaTeX tables: OK
Final 300 figures: OK
Communication ablation figures: OK
Per-seed appendix: OK
Edge feature ablation figure: OK
Speed robustness figures: OK
LAG graph synthetic smoke: OK
LaTeX static check: OK
Quantitative claim consistency: OK
Paper text risk audit: OK
Reproducibility artifact gate: OK
```

本轮已完成：

```text
1. 已把一键构建脚本纳入最终 artifact gate；
2. 已复跑所有质量门禁，确认新增报告也被检查；
3. 下一步进入论文正文精修：摘要、引言贡献表述、实验段落和图表引用统一。
```

## 15. LaTeX 正文精修进度

本轮已对 LaTeX 正文进行第一轮质量精修：

```text
paper_latex/sections/01_introduction.tex
paper_latex/sections/02_related_work.tex
paper_latex/sections/03_problem.tex
paper_latex/sections/04_method.tex
paper_latex/sections/05_experiments.tex
```

已完成的调整：

```text
1. 引言中强化“物理边语义 + 有限通信半径变化”的问题缺口；
2. 贡献点中加入 300 回合每种子复评的低碰撞范围，增强数据支撑；
3. 方法章节补充 edge feature 向量公式，明确相对位置、距离、方位、速度差和通信可达标记；
4. 实验章节将“显著降低”改为更稳妥的数值对比表述；
5. 明确 100-episode 消融表和 300-episode 主表的用途边界。
6. 相关工作补充“本文定位”段，将 MAPPO、GNN/MARL 和有限通信 UAV 工作自然收束到本文缺口；
7. 问题建模补充状态、集中训练分散执行、有限通信图、奖励和评价指标定义。
8. 讨论章节拆分为稳定性来源、向 LAG/6DOF 扩展的边界和局限性；
9. 结论章节明确当前证据来自二维异构追逃，6DOF/雷达/导弹/有人机协同属于未来迁移验证。
```

精修后检查结果：

```text
python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

下一步建议继续推进：

```text
1. 当前环境缺少 xelatex/latexmk/bibtex，PDF 编译需在安装 LaTeX 发行版后完成；
2. 继续补训练时长和 checkpoint 命名说明；
3. 视时间补充 5-seed 或 LAG 小规模迁移验证。
```

## 16. 实验设置与超参数表补全

本轮新增训练与评估设置 LaTeX 表：

```text
results/latex_training_settings_table.tex
```

生成入口：

```text
scripts/make_latex_tables.py
```

已接入论文实验章节：

```text
paper_latex/sections/05_experiments.tex
```

表中记录的核心设置包括：

```text
num_envs=8
rollout_steps=128
hidden_dim=128
lr=3e-4
gamma=0.99
gae_lambda=0.95
clip_coef=0.2
entropy_coef=0.01
value_coef=0.5
max_grad_norm=0.5
ppo_epochs=4
MAPPO minibatch_size=512
GAT/EA-RG graph minibatch=256
fixed training radius=8
staged fine-tuning radius=U(4,10)
final evaluation=300 episodes per seed, 3 seeds
```

当前检查结果：

```text
python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

下一步建议继续推进：

```text
1. 当前环境已确认缺少 xelatex/latexmk/bibtex，PDF 编译需转到装有 LaTeX 的环境；
2. 继续补训练时长和 checkpoint 命名说明；
3. 之后再考虑 5-seed 扩展或 LAG 小规模迁移验证。
```

## 17. 运行环境报告补全

本轮新增运行环境报告脚本：

```text
scripts/write_runtime_environment_report.py
```

生成报告：

```text
docs/runtime_environment_report.md
```

当前环境记录：

```text
python: D:/Anaconda/envs/.conda/envs/cac/python.exe
Python version: 3.8.20
platform: Windows-10-10.0.22631-SP0
torch: 2.4.1+cu124
CUDA available: True
CUDA version: 12.4
GPU: NVIDIA GeForce GTX 1650 Ti
xelatex/latexmk/bibtex: not found
```

当前检查结果：

```text
python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

## 18. Checkpoint 清单补全

本轮新增 checkpoint 清单脚本：

```text
scripts/write_checkpoint_inventory.py
```

生成报告：

```text
docs/checkpoint_inventory.md
```

该报告将论文方法、随机种子、结果目录和最终 checkpoint 对齐，覆盖：

```text
MAPPO: seed 0/1/2
GAT-MAPPO: seed 0/1/2
EA-RG-MAPPO-S: seed 0/1/2
```

注意：

```text
checkpoint 清单中的训练日志最后评估行只作为 run sanity check；
论文最终主结果仍以 results/final_comm_300_summary.csv 的 300-episode 复评为准。
```

当前检查结果：

```text
python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

## 19. LaTeX README 与投稿清单更新

本轮同步更新：

```text
paper_latex/README.md
docs/submission_readiness_checklist.md
```

更新内容：

```text
1. README 中加入一键构建命令 scripts/build_paper_assets.py；
2. README 中说明训练设置表、运行环境报告和 checkpoint 清单位置；
3. 投稿清单更新为当前 LaTeX 工程已具备、主表采用 300-episode 复评；
4. 投稿清单补充 runtime report、checkpoint inventory、速度鲁棒性和 edge feature 诊断材料；
5. 投稿清单中的 artifact gate 更新为 required files checked: 68, required scripts checked: 18。
```

当前剩余最现实工作：

```text
1. 在装有 xelatex 的环境中编译 PDF 并做版面检查；
2. 继续语言润色和英文转写；
3. 视投稿目标决定是否补 5-seed 或 LAG/JSBSim 小迁移。
```

## 20. 英文摘要与贡献点补全

本轮已在 LaTeX 主稿中加入英文题名、英文摘要和英文关键词：

```text
paper_latex/main.tex
```

同时新增英文摘要与贡献点独立文档：

```text
docs/english_abstract_and_contributions.md
```

用途：

```text
1. 可作为中文期刊双语摘要的英文部分；
2. 可作为后续英文全文转写的摘要和贡献点基础；
3. 可用于投稿系统中的 Abstract / Keywords / Contributions 字段。
```

已同步更新：

```text
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
scripts/check_reproducibility_artifacts.py
scripts/check_paper_text_risk.py
```

文本风险审计已扩展到英文摘要文档，并新增英文过度主张短语检查，例如：

```text
verified full 6DOF
high-accuracy target intent recognition
outperforms all baselines on all metrics
```

当前检查结果：

```text
python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

## 21. 英文 Introduction 初稿补全

本轮新增英文引言初稿：

```text
docs/english_introduction_draft.md
```

该文档基于当前 LaTeX 中文引言和已验证实验结果转写，包含：

```text
1. UAV swarm cooperative pursuit 背景；
2. MAPPO 在有限通信关系建模上的不足；
3. 普通 GAT 对物理边语义利用不足的问题；
4. 本文选择二维异构追逃作为现实可实现阶段的理由；
5. EA-RG-MAPPO-S 三项贡献；
6. 目标意图分支不能作为主贡献的边界说明。
```

已接入：

```text
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
scripts/check_reproducibility_artifacts.py
scripts/check_paper_text_risk.py
```

当前检查结果：

```text
python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

下一步英文转写顺序建议：

```text
1. Related Work 英文初稿；
2. Problem Formulation 英文初稿；
3. Method 英文初稿；
4. Experiments 英文初稿。
```

## 22. 英文 Related Work 与 Problem/Method 初稿补全

本轮新增：

```text
docs/english_related_work_draft.md
docs/english_problem_method_draft.md
```

英文 Related Work 覆盖：

```text
1. Multi-Agent Reinforcement Learning；
2. Graph Neural Networks for Multi-Agent Coordination；
3. Limited-Communication UAV Cooperation；
4. Position of This Work。
```

英文 Problem/Method 覆盖：

```text
1. cooperative pursuit problem formulation；
2. centralized training and decentralized execution；
3. limited-communication graph definition；
4. reward and evaluation metrics；
5. EA-RG-MAPPO-S overview；
6. role graph construction；
7. relative edge-feature enhanced attention；
8. MAPPO optimization；
9. staged random-radius fine-tuning。
```

已接入：

```text
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
scripts/check_reproducibility_artifacts.py
scripts/check_paper_text_risk.py
```

当前检查结果：

```text
python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

下一步英文转写建议：

```text
1. Experiments 英文初稿；
2. Discussion/Conclusion 英文初稿；
3. 整合为 docs/english_manuscript_draft.md。
```

## 23. 英文 Experiments、Discussion/Conclusion 与完整英文稿补全

本轮新增：

```text
docs/english_experiments_draft.md
docs/english_discussion_conclusion_draft.md
docs/english_manuscript_draft.md
```

英文 Experiments 覆盖：

```text
1. environment settings；
2. compared methods；
3. 300-episode main results；
4. ablation analysis；
5. visualization analysis；
6. target-intent branch diagnostic；
7. target-speed robustness；
8. evaluation-time edge-feature masking diagnostic。
```

英文 Discussion/Conclusion 覆盖：

```text
1. source of stability under limited communication；
2. boundary of extension to LAG/6DOF systems；
3. limitations；
4. conclusion and future work。
```

完整英文初稿：

```text
docs/english_manuscript_draft.md
```

该文件由以下英文分节稿合并而来：

```text
docs/english_abstract_and_contributions.md
docs/english_introduction_draft.md
docs/english_related_work_draft.md
docs/english_problem_method_draft.md
docs/english_experiments_draft.md
docs/english_discussion_conclusion_draft.md
```

当前检查结果：

```text
python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14
OK

python scripts/check_paper_claim_consistency.py
claim groups checked: final_main, speed_robustness, edge_masking
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

下一步建议：

```text
1. 对 docs/english_manuscript_draft.md 做语言统一和冗余清理；
2. 已将英文稿转换为 paper_latex_en/ 独立英文 LaTeX 工程；
3. 继续保持当前证据边界，不将 LAG/6DOF 写成已验证结果。
```

## 24. 英文 LaTeX 工程补全

本轮新增独立英文 LaTeX 工程：

```text
paper_latex_en/main.tex
paper_latex_en/sections/01_introduction.tex
paper_latex_en/sections/02_related_work.tex
paper_latex_en/sections/03_problem.tex
paper_latex_en/sections/04_method.tex
paper_latex_en/sections/05_experiments.tex
paper_latex_en/sections/06_discussion.tex
paper_latex_en/sections/07_conclusion.tex
paper_latex_en/sections/08_appendix_experiments.tex
paper_latex_en/README.md
```

工程设计：

```text
1. 英文工程复用 paper_latex/references.bib；
2. 英文工程复用 results/figures/ 和 results/latex_*.tex 表格；
3. scripts/check_latex_project.py 已扩展为同时检查 paper_latex/ 和 paper_latex_en/；
4. scripts/check_paper_text_risk.py 已覆盖英文 LaTeX 全部章节。
```

当前检查结果：

```text
python scripts/check_latex_project.py
checked tex files: 28
bib keys: 14, 14
OK

python scripts/check_paper_text_risk.py
text risk files checked: 30
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

当前限制：

```text
本机运行环境仍缺少 xelatex/latexmk/bibtex，因此英文 PDF 版面尚未编译验证。
```

下一步建议：

```text
1. 对 paper_latex_en/ 做语言和公式细节润色；
2. 在安装 LaTeX 的环境中编译中英文 PDF；
3. 若英文投稿优先，则将 paper_latex_en/ 改造成目标期刊模板格式。
```

## 25. 英文 LaTeX 一致性检查补全

本轮新增英文 LaTeX 专项一致性检查脚本：

```text
scripts/check_english_latex_consistency.py
```

检查范围：

```text
1. paper_latex_en/main.tex 和 8 个英文 section 是否存在且非空；
2. 英文稿是否包含 EA-RG-MAPPO-S、Edge-Aware Role Graph、staged random-radius fine-tuning 等核心方法标记；
3. 英文稿是否包含 300-episode 主结果关键数值；
4. 英文稿是否包含训练设置表、最终主表、消融表、速度鲁棒性表和 edge-feature 诊断表；
5. 英文稿是否包含核心图像；
6. 英文稿是否保留 2D/6DOF 证据边界。
```

已接入：

```text
scripts/build_paper_assets.py
scripts/check_reproducibility_artifacts.py
docs/paper_asset_index.md
docs/reproducibility_manifest.md
paper_latex_en/README.md
```

当前检查结果：

```text
python scripts/check_english_latex_consistency.py
english latex files checked: 9
required markers checked: 16
OK

python scripts/check_reproducibility_artifacts.py
required files checked: 68
required scripts checked: 18
OK
```

## 33. 文件尾部最新状态索引

当前最新新增实验证据：

```text
通信 dropout 退化鲁棒性诊断，详见第 31 节；本轮新增对应趋势图。
核心文件：
scripts/evaluate_comm_dropout_robustness.py
scripts/plot_comm_dropout_robustness.py
results/comm_dropout_robustness_eval.csv
results/comm_dropout_robustness_summary.csv
results/comm_dropout_robustness_notes.md
results/latex_comm_dropout_robustness_table.tex
results/figures/comm_dropout_success_rate.png
results/figures/comm_dropout_collision_rate.png
```

当前最新质量门禁：

```text
python scripts/build_paper_assets.py: OK, including Communication dropout figures
python scripts/check_latex_project.py: checked tex files: 32; bib keys: 14, 14; OK
python scripts/check_paper_claim_consistency.py: final_main, speed_robustness, edge_masking, paired_ci, comm_dropout; OK
python scripts/check_english_latex_consistency.py: english latex files checked: 9; required markers checked: 17; OK
python scripts/check_paper_text_risk.py: text risk files checked: 30; OK
python scripts/check_reproducibility_artifacts.py: required files checked: 81; required scripts checked: 23; OK
```

## 34. 通信 dropout 诊断趋势图补全

本轮将通信 dropout 诊断从“表格证据”补全为“表格 + 曲线图”：

```text
scripts/plot_comm_dropout_robustness.py
results/figures/comm_dropout_success_rate.png
results/figures/comm_dropout_collision_rate.png
```

图像设计：

```text
1. 横轴为 communication dropout probability；
2. 纵轴分别为 success rate 和 collision rate；
3. 颜色区分 MAPPO、GAT-MAPPO、EA-RG-MAPPO-S；
4. 线型区分 radius=4 和 radius=8；
5. error bar 表示 3 个 seed 的标准差。
```

已接入：

```text
paper_latex/sections/08_appendix_experiments.tex
paper_latex_en/sections/08_appendix_experiments.tex
scripts/build_paper_assets.py
scripts/check_reproducibility_artifacts.py
scripts/check_english_latex_consistency.py
scripts/write_submission_package_manifest.py
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
```

最新验证：

```text
python scripts/build_paper_assets.py
Communication dropout figures: OK
Reproducibility artifact gate: OK

python scripts/check_reproducibility_artifacts.py
required files checked: 81
required scripts checked: 23
OK
```

## 35. LAG/JSBSim 最小迁移探针

本轮新增 LAG/JSBSim 迁移准备探针：

```text
scripts/probe_lag_jsbsim_migration.py
docs/lag_jsbsim_migration_probe.md
results/lag_jsbsim_migration_probe.csv
```

探针目标：

```text
1. 检查本地 LAG 目录是否具备 MultipleCombat 相关 env/task/base env/simulator wrapper；
2. 静态读取 LAG 的动作空间、观测长度、共享观测长度、reward/termination 组件；
3. 检查 LAG Python 模块是否可导入；
4. 检查 JSBSim data 子模块是否存在；
5. 明确当前只能说“迁移准备”，不能说“真实 6DOF 验证完成”。
```

当前探针结果：

```text
Missing required paths: 1
Failed imports: 1
Synthetic graph smoke rows: 400
Real JSBSim status: blocked: envs/JSBSim/data submodule missing
Failed import: envs.JSBSim.envs.multiplecombat_env -> ModuleNotFoundError: No module named 'envs.JSBSim.human_task'
```

可复用接口：

```text
1. MultipleCombatTask 存在；
2. action_space = MultiDiscrete([41, 41, 41, 30])；
3. obs_length = 9 + (num_agents - 1) * 6；
4. share_observation_space = num_agents * obs_length；
5. simulator wrapper 暴露 get_position / get_velocity / get_rpy，可用于 6DOF role graph。
```

已接入：

```text
scripts/build_paper_assets.py
scripts/check_reproducibility_artifacts.py
scripts/write_submission_package_manifest.py
docs/lag_migration_checklist.md
docs/evidence_chain_status.md
docs/paper_asset_index.md
docs/submission_readiness_checklist.md
docs/reproducibility_manifest.md
```

最新验证：

```text
python scripts/build_paper_assets.py
LAG JSBSim migration probe: OK
Reproducibility artifact gate: OK

python scripts/check_reproducibility_artifacts.py
required files checked: 83
required scripts checked: 24
OK
```

下一步建议：

```text
1. 补齐 LAG/envs/JSBSim/data 子模块；
2. 处理 envs.JSBSim.human_task 导入缺口；
3. 再做 real MultipleCombatEnv reset/one-step probe；
4. reset/one-step 成功后，再考虑 EA-RG-MAPPO-S 的 6DOF actor/action-head 适配。
```

当前最建议的下一步：

```text
1. 若继续实验增强：优先 LAG/JSBSim 最小迁移，而不是继续扩大轻量 dropout 诊断；
2. 若推进投稿：让导师确定 Drones / Aerospace / JIRS 首投目标，然后执行 docs/journal_template_migration_plan.md；
3. 论文主张保持为有限通信下的边特征角色图协同鲁棒性，不扩展成完整空战系统已验证。
```
