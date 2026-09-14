# PSCR 主线下一步：团队服务链交接信用方法规格（2026-09-14）

## 本文目的与当前决定

本文把 PSCR 的下一步从“再找一个模块”收敛成可实现、可比较的算法假设。它是**方法设计规格，不是冻结协议、实验结果或强二区保证**。本文只沿用 PSCR 的非攻击性持续服务/请求重配置任务；不把 DRTP、P10、P30、P32 或 V8 的结果并入 PSCR 样本。

暂定算法名：**最小可行交接联盟 MAPPO**（Minimal Feasible Handoff Coalition MAPPO, **MFHC-MAPPO**）。其唯一候选机制是：在服务链切换需要多个异构无人机联合改变意图时，以当前任务合同导出的“最小可行切换联盟”为单位计算 PPO 反事实优势，避免单机边际反事实把必要的联合切换误判成零贡献。

算法新颖性目前是**有明确区分假设、尚未完成系统文献优先权审查**。COMA、Shapley 信用和协同任务分配均已有成熟工作；不能把“反事实信用”“联盟信用”或“多 UAV 动态重分配”本身称为创新。正式锁题前必须确认下文的任务条件化最小可行联盟是否与已发表的可行联合动作信用方法实质不同。

## 一、项目内证据基线

| 已核实事实 | 证据与解释边界 |
|---|---|
| PSCR 使用三架异构 UAV、3DOF 动力学、感知—中继—执行服务链；未来请求在公开到达前不向 actor 泄露真实位置/紧急度。 | `envs/pscr_adversarial_service_env.py`。这是任务接口事实，不是算法贡献。 |
| 高层服务意图接口为每架 UAV 提供本地服务意图动作，并由共同的透明控制器转为 3DOF 动作。 | `envs/pscr_service_reconfiguration_env.py`。这允许各机分别作出实际动作，但尚未证明学到了协调切换。 |
| 5 个 seed 的 G1 固定终点评估覆盖 `bounded_mixture`、`routine_aligned`、`urgent_opposite`，每 seed 每情形 24 回合。 | `configs/pscr_service_interface_g1_plain_baseline_freeze_20260912.json` 与 `results/development/pscr_service_interface_g1_plain_baseline_20260912/diagnostics/g1_endpoint/PSCR_G1_ENDPOINT_MANIFEST.json`。这些只属于开发基线。 |
| G1 结果存在显著 seed 差异；例如 seed 99001 完成主服务，而 seed 99002/99003 在多个情形下未完成主服务。所有记录的 `reconfiguration_events` 为 0。 | `results/development/pscr_service_interface_g1_plain_baseline_20260912/diagnostics/g1_endpoint/PSCR_G1_PER_SEED_ENDPOINTS.csv`。因此不能写成“已学会团队重构”，也不应把这一基线当作已稳定的强基准。 |
| V8 的 relation-value 头、容量匹配 MLP 和语义打乱臂在 3 个 seed 上行为与端点完全相同。 | `results/development/commitment_handoff_v8_relation_value_g3_pilot_20260914/g3_audit/v8_g3_pilot_report.json`。这否定该 V8 头的候选识别，不否定 PSCR，也不构成 PSCR 算法证据。 |

## 二、论文问题与可检验缺口

在动态服务需求下，一条服务链由感知、通信中继和执行等互补角色共同成立。请求切换不是独立 UAV 的普通目标选择：如果只有部分节点切换，原链可能中断而新链仍不成立；只有某个角色组合联合调整，新的可行服务链才会形成。共享团队回报把该结果延迟到服务完成后，逐 agent 的单步边际优势可能低估需要联合改变的成员。

可检验问题：**在相同任务、策略骨干、PPO 目标、奖励、观测、动作、控制器和训练预算下，按服务链约束识别最小可行切换联盟，并对其联合动作计算反事实优势，能否改善多机策略的服务链交接与多请求完成？**

这不是声称普通 MAPPO 无法学到协同，也不是声称 COMA 必然失败；它提出一个特定失配假设：在“只有一组或少数组合能令角色链从旧请求转到新请求”的决策状态，逐 agent 的边际反事实可能把必要的互补行动当作无效行动。

## 三、算法定义

### 3.1 固定项与唯一变化项

所有实验臂固定：PSCR 环境转移、3DOF 物理、actor 输入/动作、共享奖励、PPO clip 与 GAE、网络骨干（容量匹配）、训练课程、训练预算、seed、训练请求生成 tape 和终点评估 tape。MFHC-MAPPO 不获得隐藏未来请求真值，不改奖励、不改执行期动作筛选、不改飞控控制器。

唯一变化项：**在存在服务链交接选择的状态，策略梯度优势从逐 agent 反事实，改为基于物理/任务合同可行集的最小交接联盟反事实优势。**辅助评论器若必须新增，其参数量计入并在容量匹配对照中抵消；优先复用集中式 critic，避免靠额外网络容量获益。

### 3.2 服务链与可行联合行动

令时刻 (t) 的执行期合法状态为 (s_t)，团队高层意图为 (\mathbf a_t=(a_t^1,\ldots,a_t^N))，当前服务请求为 (r_t)。由固定环境规则得到请求 (r) 的链可行谓词：

\[
\mathcal F_r(s,\mathbf a)=1
\]

当且仅当意图执行后，必要异构角色在物理范围、通信可达性、能量/安全约束和请求时限下能形成该请求的服务链。审计使用环境真实转移与公开任务合同重放；执行期 actor 不读取 oracle 可行标签。

### 3.3 最小可行交接联盟

令公开任务状态给出的可切换请求集合为 \(\mathcal R_{alt}(s_t)\)。环境审计器针对这些请求枚举完整联合宏动作，并验证目的服务链。为保证反事实 baseline 不依赖采样到的联盟动作，联盟必须仅由状态与公开任务合同确定，不能先看本次 actor 采样的目标请求再挑选。定义：

\[
\mathcal C_t(s_t)=\left\{C\subseteq\{1,\ldots,N\}:\exists r'\in\mathcal R_{alt}(s_t),\exists\mathbf a'_C,\quad
\mathcal F_{r'}(s_t,(\mathbf a'_C,\mathbf a_{-C,t}))=1\right\}.
\]

最小联盟为其基数最小成员：

\[
\mathcal C_t^*=\arg\min_{C\in\mathcal C_t}|C|.
\]

若不存在可行联盟，该状态不施加交接联盟优势项，仍按原 MAPPO 更新。若存在多个同样小的联盟，训练期按固定随机种子在这些联盟间均匀抽样，并记录抽样概率；不得事后选对方法最有利的联盟。联盟搜索只在小规模团队（本任务 (N=3)）枚举，计算成本有限。固定“其他 agent 动作”时可行备选集允许随其动作变化，但联盟集合本身不得由被选联盟当前采样动作或目标请求标签决定。

### 3.4 联盟反事实优势

令 (Q_\psi(s,\mathbf a)) 为集中 critic 对共享团队回报的估计。对被选中的最小联盟 (C_t^*\)，定义可行反事实基线：

\[
b_{C_t^*}(s_t,\mathbf a_{-C_t^*})=
\mathbb E_{\tilde{\mathbf a}_{C}\sim\pi(\cdot|\mathbf o_C)}
\left[Q_\psi(s_t,(\tilde{\mathbf a}_{C},\mathbf a_{-C_t^*}))\mid
(\tilde{\mathbf a}_{C},\mathbf a_{-C_t^*})\in\mathcal F_{r'}(s_t)\right],
\]

\[
A_{C_t^*}(s_t,\mathbf a_t)=Q_\psi(s_t,\mathbf a_t)-b_{C_t^*}(s_t,\mathbf a_{-C_t^*}).
\]

交接状态的联盟策略梯度项为：

\[
g_{C_t^*}=A_{C_t^*}\nabla_\theta\sum_{i\in C_t^*}\log\pi_\theta(a_t^i|o_t^i).
\]

非交接状态沿用标准 MAPPO 优势。为避免重复计数，同一时刻只采一个预注册联盟；联盟优势只在请求切换被允许且存在至少两个任务方案的状态计算。实现前需以单元测试验证该基线对联盟当前采样动作条件独立，且 mask/可行集没有把未来真值引入 actor。

### 3.5 相对已有方法的可检验差异

| 方法 | 反事实变化对象 | 任务可行语义 | 在本研究中的作用 |
|---|---|---|---|
| MAPPO | 不显式枚举局部反事实 | 无 | 主容量匹配基线 |
| COMA-style individual counterfactual | 单个 agent 动作，其他 agent 固定 | 对照实现是否按可行集约束需明示 | 检验逐 agent 边际是否足够 |
| 全团队 joint-advantage MAPPO | 全体动作共同变化 | 不分配最小联盟 | 检验仅增加团队级优势是否已足够 |
| MFHC-MAPPO | 任务状态相关的最小可行交接联盟 | 由服务链约束导出 | 候选方法 |
| shuffled-coalition control | 保持联盟大小分布，打乱“状态—所需联盟”映射 | 破坏任务语义映射 | 识别收益是否依赖正确的交接结构 |

**新颖性边界：** COMA 已有单 agent 反事实；Shapley MARL 已有联盟贡献归因；ROMA 等已研究学习角色。MFHC-MAPPO 只有在“按服务链可行性确定状态条件最小干预联盟”这一点经过全面文献核查，且相对可行集 COMA/全团队 PPO 产生可复现差异时，才可能构成有意义的方法贡献。目前不可写“首次联盟信用分配”。

## 四、实验计划：一次聚焦的算法识别，不再重开题目列表

### RQ1：团队交接是否真需要联盟级优势？

训练臂：容量匹配 MAPPO、COMA-style individual counterfactual、全团队 joint-advantage MAPPO、MFHC-MAPPO。先用现有五个 PSCR 开发 seed 分布确定基线难度；新方法 pilot 使用全新冻结 seed，不与开发队列合并。若需正式结果，所有臂共享新 seed 与相同预算。

### RQ2：改善是否来自正确的交接联盟结构？

唯一主要消融：MFHC-MAPPO 对 shuffled-coalition control，保持联盟大小、参数、训练更新数、输入、数据 tape 完全相同，只置换状态到联盟的映射。若打乱臂不退化，则不支持语义机制 claim。

### RQ3：收益是否以可靠性代价换来？

分别报告：加权服务价值、主/次请求完成率、未服务/超时、服务链连续性、重配置次数与延迟、能量、碰撞、约束违规。episode 是同一训练策略下的测量回合；统计独立单位是 training seed。不能用总 reward 替代服务安全性。

### RQ4：是否适应需求不确定性？

使用训练 tape 未包含的到达率/紧急度/扇区组合做 held-out 评估，明确称为训练排除条件评估而非天然 OOD。至少报告每 seed 的条件分层结果及 seed 层汇总。

## 五、执行顺序与成本控制

1. **立即完成方法代码规格化**：接口复用现有 `PSCRServiceReconfigurationEnv`，新增联盟枚举/反事实基线单元，不动现有环境奖励和物理规则。
2. **先做纯单元测试与离线重放测试**：检查最小联盟在三机 8 个子集上可重算、可行性标签只由公开动作后果生成、联合梯度有限且数值稳定。这是算法正确性测试，不作为研究资格门。
3. **直接进入有限 pilot**：三臂（MAPPO、individual-CF、MFHC）× 3 个新 seed，训练预算先用统一开发预算；同时记录服务链交接事件和联盟命中率。已有 G1 已提供任务基线，不再重复一轮 plain-MAPPO 门禁。
4. **只有 pilot 显示“交接行为有变化且任务/可靠性有可解释差异”时，扩为冻结正式队列**；如果算法行为与对照相同，就据结果修改算法本身一次（而不是换题、扫超参或继续扩大算力）。
5. **正式训练前完成外部新颖性核查与比较实现**，重点排查可行集约束下的 COMA、coalition credit、temporally extended credit 和多 UAV 动态任务重分配。检索摘要已确认相邻方向拥挤，正式核查不能省略。

## 六、目前结论和可声称范围

- 项目已有一个可学习但 seed 敏感的 PSCR 基线；它尚未显示实际服务链重构行为。
- V8 relation-value 机制没有识别信号，故不沿用该具体模块。
- 下一算法假设已具体到输入、联盟定义、反事实基线、策略梯度、对照和消融，不再停留在“以后再想创新”。
- MFHC-MAPPO 目前是**可证伪的方法候选**，不是已验证有效的方法，不预先承诺强二区；创新上限取决于与 constrained COMA/Shapley/role-MARL 的实质差异和 seed-level 结果。
- 若正确联盟语义相对 individual-CF、joint advantage 与打乱臂都无法产生行为/端点差异，则该机制缺乏经验价值；届时保留 PSCR 任务资产，调整算法而不重开宽泛选题搜寻。

## 参考起点（需正式书目核验）

- Foerster et al., *Counterfactual Multi-Agent Policy Gradients*, AAAI 2018: <https://ojs.aaai.org/index.php/AAAI/article/view/11794>
- Wang et al., *Shapley Counterfactual Credits for Multi-Agent Reinforcement Learning*, KDD 2021: <https://doi.org/10.1145/3447548.3467420>
- Agorio et al., *Multi-agent assignment via state augmented reinforcement learning*, L4DC 2024: <https://proceedings.mlr.press/v242/agorio24a.html>
- Zhao et al., *A Method of Multi-UAV Cooperative Task Assignment Based on Reinforcement Learning*, 2022: <https://onlinelibrary.wiley.com/doi/10.1155/2022/1147819>
- Liu et al., *Digital-Twin-Assisted Task Assignment in Multi-UAV Systems: A Deep Reinforcement Learning Approach*, IEEE IoT Journal 2023: <https://doi.org/10.1109/JIOT.2023.3263574>
