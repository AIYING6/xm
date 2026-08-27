# 27 投稿前审稿模拟（限于现有材料）

## Review setup

- **Input scope：** `main_zh.md`、正式主 cohort 源数据/图表、无图 MAPPO 性能参考、独立三方法重复 S4、证据 manifest、复现包计划和引用账本。
- **Assessment boundary：** 本报告只评价现有仿真与归档证据，未检查目标中文期刊模板、匿名仓库的实际可访问性、checkpoint 实体下载、作者元数据或任何未提供的 HIL/实飞结果。
- **Shared manuscript claim summary：** DRTP 在冻结的 2301--2305 正式 cohort 中相对参数匹配的 UTR 显示较高 F0 与跨扰动汇总表现，但独立 2401--2405 三方法 cohort 的方向反转，故结论被限定为 cohort-dependent empirical gain，而非 seed-stable 或一般化的鲁棒性结论。
- **Visible evidence base：** 主 cohort 为 5 个配对训练种子、共同 10M final checkpoint、12 个条件和 12,000 条记录；无图 MAPPO 性能参考采用相同正式种子/tape；独立 SNR 三方法 cohort 为 5 个新种子、10M 和 18,000 条记录，完整保留。
- **Missing materials affecting confidence：** 目标期刊格式、实际匿名仓库链接/DOI/许可证、作者与资助元数据、共同硬件下的 wall-clock/peak-memory，以及物理或 HIL 验证均未提供。

## Reviewer 1

**Emphasis：实验设计、证据分层与统计。**

- **Overall assessment：** 该稿最强之处是将训练 seed 视为独立单位、预先固定 10M final checkpoint，并将安全与 trigger-validity 分开。完整披露独立反向 cohort 明显优于只展示正式正向 cohort 的常见写法。
- **Who would be interested in the results, and why：** UAV 协同、图 MARL 与鲁棒训练研究者会关注：训练分布重加权在同一任务内的收益与跨 cohort 可靠性为何会分离。
- **Major strengths：** 参数匹配 UTR--DRTP 主消融清晰；12 条件协议与风险集定义明确；无图 MAPPO 被恰当降级为性能参考；独立 cohort 未被池化或选择性删减。
- **Assessment against Nature-style criteria：** 原创性来自受控任务化训练分布，而非通用算法；科学重要性对 UAV/MARL 社群有意义，但跨学科广泛性有限；技术完整性在正式 cohort 内较强；对非专业读者的可读性依赖图1和图2是否在最终版清楚说明。
- **Recommendation posture：** 支持性评价，但应先关闭透明度与因果边界问题。

### Major concerns

**R1-M1 — [experimental-design] 同 cohort 的 static nonuniform 对照缺失。**
**Claim pointer：** 本文将可辨识问题限定为 adaptive weighting 相对 uniform weighting 的效果。
**Evidence pointer：** 主文1.2、2.4、7节；独立 cohort 6.9 与S4。
**Concern：** 独立 SNR cohort 的存在并不能识别“online adaptation 是否优于合理 static nonuniform distribution”，因为训练种子、tape 与 DRTP--UTR 方向均已改变。
**Resolution test：** 不新增训练的可接受解决方式是继续在摘要、贡献、讨论、结论和图注中将结论限定为“relative to uniform”；不得以 SNR 或文字暗示 adaptive necessity。

**R1-M2 — [statistical-rigor] 跨 cohort 异质性需要成为可见的核心结果，而非附带 limitation。**
**Claim pointer：** 正式 cohort 观察到五种子正向，而独立 cohort 四个任务端点相对 UTR 均负向。
**Evidence pointer：** 主文6.9、表6、S4、证据 manifest。
**Concern：** 仅在 Discussion 中轻描淡写会造成读者把正式 cohort 的数值误读为可复现的总体效应。
**Resolution test：** 保留摘要中的反向事实；主文6.9放在结果而非仅补充；不合并 `n=10`，同时在主图/图注或结果导读显式提示“formal positive / independent adverse”。

### Minor concerns

**R1-m1 — [figures-and-tables] 统计可读性。**
**Claim pointer：** 配对 seed 图与条件分解图承担主要数值论证。
**Evidence pointer：** 图3--图5及表2--表5。
**Concern：** 最终图注需自足写明每个点代表训练 seed、菱形/柱/线的含义、`n=5`、是否显示均值或中位数，以及 source data 文件。
**Resolution test：** 终稿图注及补充材料 S1 清楚给出这些定义，且不把 episode 误作重复。

## Reviewer 2

**Emphasis：方法新颖性、因果解释与工程边界。**

- **Overall assessment：** 方法实现边界描述充分：DRTP 不改变 actor/critic、PPO 或执行期输入，只控制六个故障组的训练期权重；这使正式 UTR--DRTP 的局部因果解释清楚。最主要的风险来自把局部经验增益延伸为更广的 topology robustness 主张。
- **Who would be interested in the results, and why：** 关注通信失效下协同控制、训练分布设计与 MARL 可靠性的工程研究者会感兴趣，特别是合法路径重构而非“信息恢复”的问题设定。
- **Major strengths：** 故障语义、actor 信息边界、normal anchor 与有界 simplex projection 写得可复核；图编码器不是被包装成新颖性；没有把 M3DDPG/TAPE 等不可比方法伪装为公平基线。
- **Assessment against Nature-style criteria：** 技术路线具有工程意义，原创性为中等且受任务约束；对工程社群的兴趣明确，广泛跨学科影响未由证据建立；方法细节总体可复现，前提是复现包实际发布。
- **Recommendation posture：** 若持续保持受限 claim，并完成可复现性托管，可作为应用导向无人机/MARL 期刊稿件评估。

### Major concerns

**R2-M1 — [claim-moderation] “拓扑鲁棒性”必须被操作条件限定。**
**Claim pointer：** 题名和摘要使用“拓扑鲁棒协同”。
**Evidence pointer：** 主文题名、摘要、3.3--3.5、7.5。
**Concern：** 实验是固定三机、预定义六类故障组、训练支持集内条件和仿真环境；它不能证明任意节点故障、未知拓扑规模或实飞环境下的通用 robustness。
**Resolution test：** 在题名/摘要/结论附近保留“中继节点故障下”“冻结条件/仿真任务”的锚定词；避免 strict OOD、general topology generalization、deployment-ready 等语句。

**R2-M2 — [causal-vs-correlative] 采样器遥测不构成策略机制证据。**
**Claim pointer：** DRTP 权重轨迹与最终性能关系。
**Evidence pointer：** 主文6.7、图6、S2--S3。
**Concern：** 权重确实离开均匀分布只证明训练暴露改变；现有数据不能识别哪一组加权导致何种运动/通信策略变化。
**Resolution test：** 将图6定位为 implementation/telemetry consistency；讨论中只使用“相一致”而不写“导致/证明机制”。

### Minor concerns

**R2-m1 — [writing-clarity] 术语统一。**
**Claim pointer：** 归档字段与论文指标。
**Evidence pointer：** 主文3.5、附录B、S1、S3。
**Concern：** 机器字段 `J_OOD_*` 很容易被读者理解为未见 OOD。
**Resolution test：** 只在两个 archive-mapping 位置出现原字段；正文、图表和标题统一为 `J_pert,mean`/`J_pert,worst`。

## Reviewer 3

**Emphasis：可复现性、安全报告与投稿可读性。**

- **Overall assessment：** 本稿在 seed 保留、终点固定、风险集定义和独立 cohort 透明性上高于一般的仿真型 MARL 稿件。安全性没有被简化为单一 success score，这一点值得保留。
- **Who would be interested in the results, and why：** 需要审查故障安全、训练可靠性和实验可复核性的自主系统读者会受益；对一般机器学习读者，价值在于对“平均收益掩盖 cohort 风险”的直接展示。
- **Major strengths：** 任务得分、collision、timeout、constraint、pre-trigger collision、survival-to-onset 与 trigger-validity 被区分；MAPPO-NoGraph 的较低碰撞/超时没有被省略；主/独立 cohort 不混合。
- **Assessment against Nature-style criteria：** 技术可靠性报告较强；原创性和跨学科重要性中等；对非专门读者而言，数据/代码与证据层级说明需要在最终 PDF 中保持简洁而可操作。
- **Recommendation posture：** 目前的主要 submission risk 是复现资产尚未实际托管，而非必须继续增加训练。

### Major concerns

**R3-M1 — [reproducibility] 数据与代码声明尚是计划，不是已实现的访问路线。**
**Claim pointer：** 主文“数据与代码可用性”承诺匿名或公开仓库。
**Evidence pointer：** 主文末尾；文档24；manifest 25。
**Concern：** 论文强调 hash、tape、raw records 和 no-seed-exclusion，若匿名仓库没有实际可访问链接、README、许可证和 checkpoint policy，这个证据链会在送审时断裂。
**Resolution test：** 在投稿前建立匿名审稿链接，上传三层 cohort 的完整数据和脚本，验证外部下载及 checksum；接收后替换为永久标识符。若 checkpoint 体积受限，明确公开 schema、hash 和获取路径。

**R3-M2 — [experimental-design] 安全主张需要固定为 trade-off，而非“更安全”。**
**Claim pointer：** DRTP 的 timeout 较低。
**Evidence pointer：** 主文6.6、图5、S1、无图 MAPPO 性能参考摘要。
**Concern：** DRTP 的 collision 略高，且独立 cohort 也显示不利安全方向；只突出 timeout 会造成不平衡的安全叙事。
**Resolution test：** 每次提及 timeout 改善时同步给出 collision/constraint 边界；将“安全改善”改为“超时--碰撞权衡”。

### Minor concerns

**R3-m1 — [writing-clarity] 管理性语句应进一步压缩。**
**Claim pointer：** 合同、机器裁决与证据层级的说明。
**Evidence pointer：** 方法、附录B和数据可用性段。
**Concern：** 部分训练治理语言对于投稿读者过长，会遮蔽科学问题。
**Resolution test：** 主文仅保留可复现所需的终点、seed、tape、hash 与禁止选择性报告事实；流程性细节转入补充材料/匿名仓库 README。

## Cross-review synthesis

### Consensus strengths

- 正式 UTR--DRTP cohort 的参数匹配、10M final checkpoint、共同 tape 与五个 training seed 为局部因果比较提供了可信基础。
- 完整保留独立三方法 cohort 的反向结果、无图 MAPPO 的安全优势和历史不利 strata，使证据链比仅报正向平均值更可信。
- 安全、pre-trigger termination 与 evaluator trigger validity 被正确分开；不使用 episode 伪重复。

### Consensus technical risks

1. **`static-control-identifiability`：** 没有同 cohort 固定非均匀控制，故不能宣称 online adaptation 必要；R1、R2 均将其视为核心边界。
2. **`cross-cohort-reliability`：** 独立 cohort 的完全反向必须作为结果层的中心限制，而不是仅作为 discussion 脚注；R1、R3 均指出这直接限制可重复性叙事。
3. **`reproducibility-hosting`：** 复现包需实际托管；R1、R3 认为这是投稿前的程序性硬门槛。
4. **`claim-moderation`：** topology robustness、safety 和机制解释均须保持受限；R2、R3 在不同维度提出同一风险。

### Where emphasis differs across reviewers

- Reviewer 1 最关注比较设计、独立单位和跨 cohort 统计解释；
- Reviewer 2 最关注方法新颖性、静态对照和从 telemetry 到策略机制的因果跳跃；
- Reviewer 3 最关注可复现资产的实际交付和 collision--timeout 的平衡表述。

### Broad-interest / significance readout

本文的广泛性主要来自“训练可靠性应成为拓扑鲁棒 MARL 结果的一部分”这一方法论信息，而非一个已被证明能泛化至所有 UAV 拓扑的通用算法。它适合应用导向 UAV/MARL 读者；尚不足以据此声称更宽泛的通用自主系统突破。

### Most important issues to resolve before a strong case is established

1. 实际发布匿名复现包并验证外部可访问性；
2. 在终稿摘要、结果、讨论和图注持续显著地保留独立 cohort 反向事实；
3. 消除任何“adaptive 必要”“严格 OOD”“统一安全改善”或“跨 cohort 稳定优越”的剩余措辞；
4. 由目标中文期刊模板完成作者元数据、篇幅、参考文献和图表格式。

## Risk / unsupported claims

- 不支持：DRTP 对任意 static nonuniform sampler 必然更好；
- 不支持：DRTP 在随机初始化或独立 cohort 上稳定优越；
- 不支持：`J_pert` 是 strict OOD，或 DRTP 具有一般 DRO 理论保证；
- 不支持：三机仿真直接证明 4/5 UAV、HIL 或实飞可部署性；
- 不支持：采样权重轨迹单独证明了某一策略层的因果机制；
- 不可评估：作者元数据、目标期刊格式、匿名仓库的真实访问性、checkpoint 实体分发和共同硬件 wall-clock/显存比较。
