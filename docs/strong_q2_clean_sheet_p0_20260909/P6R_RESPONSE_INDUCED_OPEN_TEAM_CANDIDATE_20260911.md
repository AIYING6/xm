# P6R：响应诱导的开放团队对手适应——候选与零训练门

## 状态

`P6R_N0_STRUCTURAL_STOP`。本文件不授权环境实现、训练、云端计算或论文题目冻结。

## 为什么重审 P6，而不复活旧 P6

旧 P6 的当前实例化已经停止：其四个蓝方候选响应面对所有已测红方策略时，R3 都是最佳响应。因此它没有可选择的 response specialization，不能训练对手适应方法（`P6_CIRU_Z1_Z2_AUDIT_RESULT_20260910.md`）。

P6R 既不把这一失败解释成“多 UAV 对抗不值得研究”，也不调整旧任务的阈值、奖励或响应库。它将研究对象改为一个明确可证伪的问题：**候选响应本身会改变对手之后的可观测轨迹时，不能先把对手当作一个被动、固定的类别再选择响应。**

## 不可作为创新的已有内容

以下对象已经存在，不能换名重做：

- 从历史识别对手策略并从策略库复用最佳响应；
- 对未知/切换对手进行 opponent modelling；
- 基于 latent opponent type 选择策略；
- 仅在策略库中维持 Bayesian belief；
- 用单策略自博弈或 population training 获得鲁棒性。

近邻证据包括：多策略对手下的策略检测与知识复用、有限信息对手建模，以及近年的 open-set opponent modelling。它们已覆盖“识别对手、选择或复用响应、对手可能切换”这一宽泛命题。

## 唯一可能的研究缺口

设 (h_t) 是我方合法观测历史、(r\in\mathcal R) 是冻结候选团队响应、(o) 是对手团队。传统 policy-reuse 形式倾向于估计 (p(o\mid h_t))，再选择与该身份对应的响应。

P6R 的对象不同且更窄：定义**响应诱导效用**

\[
V_r(h_t)=\mathbb E\big[J\mid h_t,\;\text{我方从 }t\text{ 起执行 }r\big],
\]

并问：在两个对手团队对被动历史 (h_t) 难以区分、但对不同 (r) 产生不同后续互动与效用排序的情况下，能否学习直接排序 (V_r(h_t))，而不把正确的 opponent-ID 视为必要中间目标？

这里“响应诱导”必须是环境博弈结构的自然后果：对手会根据我方的护航、区域控制或资源争夺行动改变后续队形/目标选择；不能由脚本在检测到 arm 标签后人为切换。

## 最小任务语义（非武器化）

使用三对三的连续 UAV **区域护送—拦截竞赛**：两队争取把各自的移动服务单元安全护送穿过共享空间；一方的区域封控、分散护送或集中护送会改变另一方是否包夹、牵制或转向另一路径。该任务只记录得分、越界、碰撞、护送完成和时间，不涉及现实攻击、目标伤害或武器控制。

候选响应须是任务层可解释的团队策略，而非网络随机初始化：例如 `split-cover`、`concentrated-escort`、`decoy-route`、`perimeter-hold`。它们在执行接口、参数预算和总训练暴露上必须匹配。

## N0：训练前四个必要事实

| 门 | 必须证明的事实 | 失败处理 |
|---|---|---|
| N0.1 非传递响应结构 | 冻结的响应—对手交叉收益矩阵中不存在通用最优响应；至少三个对手的唯一最优响应不同，且排序余量预先定义并报告 | 停止：重演旧 P6 的 R3 支配 |
| N0.2 被动历史混叠 | 至少一对对手在相同被动前缀统计下难以区分，但其最佳响应不同 | 停止：普通 opponent-ID/GRU 已足以解释问题 |
| N0.3 响应诱导差异 | 在相同初始状态下，改变我方候选响应会对同一对手产生材料性的后续队形/目标选择差异；机制不能读取我方 arm 标签 | 停止：对手只是外生轨迹源 |
| N0.4 可学习但不饱和 | 容量匹配的单策略 MAPPO 在公共训练对手上高于随机基线，但不接近所有对手的 oracle 响应 | 停止：近零任务或无适应余量 |

这些门不是以任意成功率作筛选；它们对应 P6R 的逻辑前提。N0.1--N0.3 均可由固定脚本/交叉执行完成，零 PPO 更新。

## 只有 N0 通过后才允许的算法合同

如果 N0 全部通过，算法不能只是“history encoder + policy selector”。唯一可检验干预应为：

1. 使用冻结 cross-play 数据训练**响应条件效用排序器**，输入仅为合法历史和候选响应标识；
2. 对每个候选响应输出效用均值与不确定性，并以预注册的保守选择规则进行测试时切换；
3. 通过 `response-label shuffle`、`identity-supervised selector` 和 `history-only selector` 分离“直接效用排序”“对手身份识别”和任意额外容量的作用；
4. 不提供对手真实策略 ID、未来轨迹、测试时环境克隆或在线梯度更新。

主要指标为 response regret、任务完成、碰撞/越界、效用排序相关性、校准误差、选择性风险和切换后累积遗憾。训练 seed 是唯一独立统计单位。

## 一票否决的近邻边界

若近邻全文核对发现已有方法同时具备“团队级、被动历史混叠、响应会诱导对手后续变化、直接 response-conditional utility 排序、开放集评测”五项，P6R 必须停止。若只是用 UAV 应用、更多对手脚本或更大网络区分，也必须停止。

## N0 实测结论（2026-09-11）

已按 `configs/p6r_response_induced_open_team_n0_v1.json` 完成零训练结构审计，结果文件为 `artifacts/diagnostics/p6r_n0_response_induced_open_team_20260911/P6R_N0_REPORT.json`。审计没有 PPO 更新，也未创建训练轨迹。

审计确认：三条规则具有相同的中性被动前缀；改变友方可观测的通道承诺会改变对手后续资源分配；不存在跨全部规则的单一响应支配。这些都是必要但不充分的条件。

但是 N0.1 失败：`mirror_pressure` 下 `left_commit` 与 `right_commit` 并列最优（间隔为 0），`commitment_exploiter` 的最佳—次优间隔仅为 0.02，低于冻结的 0.08。因此，该构造尚未形成可稳定识别的唯一响应专门化，不能把“直接响应条件效用排序”与普通策略复用清楚地区分。

**处理：停止 P6R，不调阈值、不调整成本系数使其通过、不启动 N0.4 或 MAPPO。** 该停止是训练前的预期保护性结果，而非程序故障。

## 近邻线索（供 N0 逐篇全文核验）

- *Accurate policy detection and efficient knowledge reuse against multi-strategic opponents*：https://www.sciencedirect.com/science/article/abs/pii/S0950705122001605
- *Limited Information Opponent Modeling*：https://openreview.net/pdf?id=35onDMLBjz
- *Open Set Opponent Modeling*：https://openreview.net/pdf?id=KHnSYIJmPc
- *Bayes-ToMoP*：https://arxiv.org/abs/1808.08061

## 可追溯来源

- `docs/strong_q2_clean_sheet_p0_20260909/P6_FINAL_TOPIC_SELECTION_OSTA_20260910.md`
- `docs/strong_q2_clean_sheet_p0_20260909/P6_CIRU_Z1_Z2_AUDIT_RESULT_20260910.md`
- `docs/strong_q2_clean_sheet_p0_20260909/P0H_CANDIDATE_CARDS.md`
- `docs/strong_q2_clean_sheet_p0_20260909/P40_TOPOLOGY_TRANSFER_VALUE_NOVELTY_GATE_20260911.md`
