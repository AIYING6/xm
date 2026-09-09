# P6 最终选题冻结：开放集对手团队响应效用适应

日期：2026-09-10  
状态：`TOPIC_SELECTED / TRAINING_NOT_AUTHORIZED`

## 最终决定

停止继续横向寻找题目。强二区新主线冻结为：

> **开放集对手团队下的响应效用推断与无梯度策略适应：面向 3v3 多无人机对抗博弈**

暂定英文题目：

> **Response-Utility Inference for Gradient-Free Adaptation to Open-Set Opponent Teams in Multi-UAV Adversarial Games**

这是真正的新课题，不是 DRTP 的延伸，也不把通信故障、采样重加权或旧论文资产设为前提。

## 一句话论题

当对手团队策略在测试时未见或发生切换时，智能体不必先把对手归入已知类别；它可以从交互历史直接估计一组冻结响应策略的条件效用及不确定性，在不更新网络参数的情况下选择低遗憾响应。

## 为什么选择它

1. **问题真实且高于单纯性能改进。** 多无人机对抗中的测试时对手变化构成策略分布偏移，固定策略或仅针对训练对手优化的策略可能失配。
2. **创新对象清晰。** 方法输出不是 opponent ID、动作预测或隐变量标签，而是响应库上的效用向量 `Q(B_k | history)` 及其置信信息。
3. **可形成闭环机制。** 行为历史 → 响应效用估计 → 不确定性控制的响应选择 → 对手切换检测 → 无梯度再适应。
4. **可证伪。** 若响应之间没有专门化、未见对手没有 oracle 余量，方法在训练前就应停止；不会再出现长实验结束后才发现题目不成立。
5. **资产基础可用但不绑架选题。** 现有 OSTA 包已有环境、冻结协议、评估 tape、测试和门控设计，可减少工程启动成本；正式结论仍需新实验产生。

## 与最近邻工作的边界

该方向并非无人区。已有工作覆盖了未见对手泛化、显式 opponent-type inference、模型式 opponent modeling、策略库复用和基于层次响应的策略选择。因此不能声称“首次研究未见对手适应”。

本文拟隔离的差异是：

| 方向 | 典型输出/机制 | 本课题的严格区别 |
|---|---|---|
| opponent classification/modeling | 对手类型、动作或策略模型 | 直接估计每个候选响应的条件效用，不要求正确识别类别 |
| hierarchical response learning | 联合学习高层选择器与低层响应 | 响应库冻结，重点考察测试时选择误差与 response regret |
| Bayesian policy reuse | 对已知或部分已知策略库维护信念并复用响应 | 正式测试含语义未见团队策略，并报告不确定性校准与开放集回退 |
| robust/self-play policy | 学得单一混合或均衡策略 | 从有限响应库中按交互历史动态选择；以 oracle 响应为上界 |
| open-set opponent identification | 显式辨识训练外对手 | 不以身份辨识为必要中间目标，评价效用排序与决策后果 |

最近邻审查意味着：**“行为编码器 + 策略选择”本身不构成创新。** 可发表贡献必须落在“开放集团队对手的响应效用推断、校准选择和切换适应”这一完整问题—方法—评价闭环上。

## 研究问题

- **RQ1（存在性）**：不同冻结响应是否对不同对手团队形成可重复的专门化，而非存在一个普遍最优响应？
- **RQ2（开放集缺口）**：面向未见对手时，群体训练基线与 oracle 响应之间是否存在可利用效用余量？
- **RQ3（方法效果）**：效用推断选择器能否降低相对 oracle 的 response regret，并优于单策略、均匀/静态混合、最近行为检索和 opponent-ID/latent baselines？
- **RQ4（不确定性）**：校准不确定性能否在证据不足或开放集偏移时改善最差情形，而不只提高平均胜率？
- **RQ5（非平稳性）**：对手策略在回合内切换时，变化检测与无梯度重选能否缩短适应延迟？

## 最多三项贡献

1. 定义开放集对手团队下的**响应效用推断**问题，以 response regret 而非 opponent-ID accuracy 作为核心决策指标。
2. 设计基于团队行为历史的效用—不确定性估计与保守响应选择机制，并扩展到对手策略切换下的无梯度再适应。
3. 建立包含已见、手工未见、独立学习未见和动态切换对手的受控 3v3 UAV 评测协议，分离识别质量、响应选择质量、任务收益与安全代价。

## 训练前四道硬门

任何方法训练前必须依次通过：

1. **G2 基线可学习性**：至少两个独立种子达到冻结的可学习阈值，且任务不饱和。
2. **G3 响应专门化**：4×4 cross-play 中至少 3/4 响应满足 `CSA_i = W_ii - max_{k!=i} W_ki > 0.10`，且不存在通用最优响应。
3. **G4 开放集缺口**：`W_seen - W_unseen >= 0.10`；低于 0.05 直接停止。
4. **G5 oracle 余量**：至少两个 held-out 对手的 `Oracle_j - W(P_POP,R_j) > 0.10`，且最好至少一个大于 0.20。

只有四门通过，才允许开发效用推断模型。任一存在性门失败，停止课题或重构任务，不通过调模型掩盖问题。

## 冻结实验结构

### 对手集合

- 已见：R1 Nearest、R2 Focus Fire、R3 Assignment、R4 Flanking。
- 未见：R5 Dynamic Roles、R6 Bait-and-Flank、R8 Independently Learned Opponent。
- 动态：R7 Strategy Switching。

R8 必须保留，以避免全部开放集证据都来自人为脚本差异。

### 主要对照

- population-trained single policy；
- static/uniform response mixture；
- oracle response selector（只作上界）；
- history encoder without utility supervision；
- opponent identity/latent prediction baseline；
- proposed response-utility selector；
- proposed selector without uncertainty；
- proposed selector without change detector（仅 R7）。

### 核心指标

- 团队胜率、任务回报与安全损失分别报告；
- response regret（相对冻结 oracle）；
- top-1 response selection accuracy 与效用排序相关性；
- 不确定性校准误差、选择性风险/覆盖率；
- 策略切换后的检测延迟、恢复时间和累计遗憾；
- 训练种子为独立统计单位，episode 不冒充独立重复。

## 当前证据状态

采用资产：`D:\File\MyFile\Temp\backup\OSTA_UAV_Project_Code_and_Scheme_2026-08-23.zip`  
SHA256：`715B204079548813933608081F0B327D51D8DC1289C2BFE4685BB9D91F9D7F4E`

已核验包内材料：

- `PROJECT_SCHEME_CURRENT.md`：课题逻辑和 R1–R8 对手定义；
- `research/P0_SCIENTIFIC_CONTRACT_V1.md`：科学问题与停止规则；
- `research/P1_EXPERIMENT_FREEZE_V2.md`：环境、指标、种子与协议冻结；
- `research/P3_SEEN_BEHAVIOR_PRECHECK_V1.md`：已见行为预检设计；
- `README_CURRENT_STATUS.md`：工程与实验状态。

目前只能确认一个种子的 1M 基线结果，且表现仍较弱；第二种子的最终资产尚未在当前归档中核验。因此状态是：

> **选题已冻结，但 G2 尚未通过，禁止直接进入正式方法训练。**

## 唯一下一步

停止继续找题。先同步并核验最新 seed-2 基线结果；若仍不足，按照已冻结 G2 合同补足最小可学习性验证。G2 通过后立即执行 B1–B4 专家交叉博弈以判定 G3。直到 G3–G5 全部通过，不实现复杂模型、不跑正式大规模实验。

## 预期论文定位

若 G2–G5 和后续方法验证全部通过，该课题具备强二区竞争力，因为它同时包含新的决策对象、开放集与非平稳评测、受控消融和明确的决策指标。若关键存在性门失败，则不能靠写作或扩大算力达到强二区；应尽早停止。

