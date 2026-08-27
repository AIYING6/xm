# 投稿前科学终稿审稿意见（限于现有证据）

**审查对象：** `main_zh.md` 及由其生成的“投稿前审稿版”PDF；正式主 cohort（2301--2305）、无图 MAPPO 性能参考与独立三方法 cohort（2401--2405）的已冻结源数据。

**审查边界：** 本报告是投稿前的模拟同行评议，不是编辑决定。它不评估尚未选择的目标期刊格式、未托管的匿名仓库链接、作者信息、共同硬件 wall-clock/峰值显存比较，也不虚构 HIL、实飞或额外外部算法实验。

## Review setup

- **稿件类型：** 面向中继节点故障下异构 UAV 协同的算法与受控仿真实证研究。
- **共同主张：** 在冻结的正式 2301--2305 cohort 中，保持 SG actor/critic、116,728 参数、PPO、奖励、训练预算、故障组和正常工况锚点不变时，DRTP 的有界自适应故障组加权相对 UTR 的均匀加权呈现正的 F0、`J_pert,mean` 与 `J_pert,worst` 配对效果；但独立 2401--2405 cohort 完整反向，故不能主张跨 cohort 的稳定优越性或在线自适应的必要性。
- **可见证据：** 参数匹配 5 个训练种子、共同 10M 终点、12,000 条正式主 cohort episode 记录；共同种子和 tape 的 6,000 条无图 MAPPO 性能参考记录；独立 UTR/SNR/DRTP 五种子、10M、18,000 条 episode 记录；安全、风险集触发器、训练遥测和完整性 manifest。
- **读者：** UAV 协同控制、通信受限 MARL、图 MARL 和训练分布设计研究者，尤其是关注平均收益与训练可靠性脱节的工程读者。
- **缺失材料：** 目标期刊模板、作者/基金/利益冲突信息、实际匿名仓库访问链接与外部下载验证、固定非均匀权重在同一正式 cohort 下的对照、4/5 UAV、HIL/实飞证据。

## Reviewer 1

**Emphasis：技术可信度、比较设计与统计单位。**

- **Overall assessment：** 主 cohort 的 UTR--DRTP 比较是本稿最有说服力的部分：参数、训练组、预算、最终检查点和评价 tape 均匹配，且训练种子而不是 episode 被视为独立单位。独立 cohort 的反向结果被完整展示，这显著提高了报告的可信度。
- **Who would be interested, and why：** 对“训练分布控制是否能改善故障拓扑条件下协同任务表现”感兴趣的 UAV/MARL 研究者会受益，尤其是需要将弱种子和安全代价纳入方法报告的读者。
- **Major strengths：** 明确不做 checkpoint promotion 和 seed exclusion；将 pre-trigger collision 与 evaluator trigger validity 分开；不把 2301--2305 与 2401--2405 合成 `n=10`。
- **Assessment against review axes：** 技术 soundness 在正式 cohort 内较强；统计解释有边界意识；更广泛稳定性不能由现有证据建立。

### R1-M1 — 跨 cohort 方向反转限制主结论

- **Axis：** experimental-design / claim-moderation
- **Claim pointer：** 摘要末句、6.9 节、7.1 节、8 节。
- **Evidence pointer：** 正式 2301--2305 cohort 的正向配对端点；独立 2401--2405 cohort 的四个任务端点相对 UTR 均为负向，且存在灾难性种子。
- **Concern：** 正式 cohort 的收益不能被阅读成可跨初始化或跨训练 cohort 重复的总体方法效应。
- **Resolution test：** 当前稿已在摘要、结果、讨论和结论披露反向 cohort；投稿版必须保留这四处的限定，不得将正式 cohort 的平均收益写成普适结论或用任何合并统计淡化反转。这是表述与证据架构门槛，不要求新增训练。

### R1-M2 — 未识别“自适应”相对固定非均匀权重的必要性

- **Axis：** causal-vs-correlative / experimental-design
- **Claim pointer：** 1.2、2.4、4.3、7.4--7.5 节。
- **Evidence pointer：** 主 cohort 只有 UTR（均匀）与 DRTP（自适应）的参数匹配主消融；SNR 位于不同独立 cohort，且并未胜过 UTR。
- **Concern：** 该设计可识别“相对均匀加权的经验差异”，不能排除某个合理的固定非均匀分布在主 cohort 中达到相近结果。
- **Resolution test：** 继续把结论限定为“相对均匀拓扑随机化的有界经验收益”；不得声称 online adaptation 必要、优于任意 static sampler 或具 Group DRO 等价性。若未来追求该机制结论，才需要新的同合同固定非均匀对照。

### R1-m1 — 小样本统计的呈现应保持描述性

- **Axis：** statistical-rigor
- **Claim pointer：** 5.4 节、表2--表6及图3--图5。
- **Evidence pointer：** 每一层 cohort 均为 5 个训练种子；主文报告 mean、median、IQR、MAD、wins/5 与最差配对效果。
- **Concern：** `n=5` 支持受控的种子级描述性比较，不支持把 episode-level 记录误用于扩大显著性。
- **Resolution test：** 终稿图注与结果表持续声明每个点为训练种子、`n=5`、episode 不是独立训练重复；如补充置信区间，只将其明确标为小样本描述性区间。

## Reviewer 2

**Emphasis：原创性、方法解释与工程意义。**

- **Overall assessment：** 论文的可辨识创新不是“发明图 MARL 或 PPO”，而是将中继故障严格定义为合法通信--任务支持路径重构，并将有界训练分布重加权置于冻结的 actor 信息边界中检验。这一定位比泛称“鲁棒 MARL”可信，但仍是任务化、工程性的创新。
- **Who would be interested, and why：** 关注通信故障条件下角色协同以及训练暴露分配的工程研究者会感兴趣；对一般强化学习读者，价值主要在于可靠性披露，而非新理论保证。
- **Major strengths：** 方法只改变训练期六组权重，不改变执行期网络输入；有界 simplex 投影、EMA、难度定义、正常工况锚点和复现边界写得具体；图编码器没有被虚构为本文创新。
- **Assessment against review axes：** 原创性为中等、与任务契合；科学重要性主要是领域内工程价值；适合专业 UAV/MARL 读者而非广泛通用算法突破。

### R2-M1 — 采样器遥测不能单独证明策略层机制

- **Axis：** mechanism-evidence
- **Claim pointer：** 6.7 节和图6；7.4 节。
- **Evidence pointer：** DRTP `q` 轨迹、组暴露、return/EMA 日志、路径与任务支持遥测。
- **Concern：** 权重离开均匀分布说明训练暴露被改变；它并不能区分“哪一组权重变化导致哪一种策略、运动或通信行为变化”。
- **Resolution test：** 保持图6为实现一致性/遥测诊断，而非因果机制证明；使用“相一致”“显示训练分布发生变化”，避免“权重变化导致了特定策略重规划”。当前稿的讨论应继续如此收束。

### R2-M2 — 无图 MAPPO 只能作性能参考

- **Axis：** experimental-design
- **Claim pointer：** 2.4 节、6.3 节、表2b、7.5 节。
- **Evidence pointer：** MAPPO-NoGraph 参数量 35,771，UTR/DRTP 为 116,728；消息输入与网络结构不同；MAPPO-NoGraph 的碰撞、超时更低。
- **Concern：** 把 MAPPO-NoGraph 称为同构 external baseline 或将其差异归因于图结构/DRTP，会超过设计能回答的问题。
- **Resolution test：** 全文统一使用“无图 MAPPO 性能参考”；并列报告其安全优势与任务端点较低事实。当前稿已经这样处理，不能在投稿信或摘要中重新包装为“全面击败 MAPPO”。

### R2-m1 — 正式版需采用目标期刊的数学排版

- **Axis：** readability / reproducibility
- **Claim pointer：** 3--4 节公式及附录B。
- **Evidence pointer：** Markdown 源稿给出完整难度、EMA、平滑和有界单纯形投影公式；PDF 为投稿前科学版本的可读导出。
- **Concern：** 当前 PDF 的行内符号是可读的近似呈现，不应替代期刊 LaTeX/Word 模板中的规范数学排版。
- **Resolution test：** 选刊后按模板重排公式、向量/集合字体、下标和表格；不得修改其数学语义、参数或结果。

## Reviewer 3

**Emphasis：可复现性、安全权衡与读者可读性。**

- **Overall assessment：** 相比常见仿真 MARL 稿件，本稿将终点固定、保留全体种子、保存样本带 hash、区分触发器技术有效性与策略安全性，并将独立反向 cohort 纳入证据层级，复现意识较强。
- **Who would be interested, and why：** 自主系统与安全关键学习的读者会关注：为什么平均任务得分、超时和碰撞不能被压缩成单一“鲁棒性”标签。
- **Major strengths：** 安全报告包含 collision、timeout、constraint、pre-trigger collision、survival-to-onset 与 risk-set validity；主 cohort、外部性能参考和独立重复的角色分工明确。
- **Assessment against review axes：** 复现设计在本地 staging 层面充分，但投稿级可信度尚依赖外部匿名托管；可读性在图1--图2和主结论上较好，仍需期刊化压缩。

### R3-M1 — 实际可访问的匿名复现包是投稿前硬门槛

- **Axis：** reproducibility
- **Claim pointer：** 数据与代码可用性、附录B、文档24和29。
- **Evidence pointer：** 本地匿名 staging package 已包含三层原始记录、manifest、代码、配置和 checksum；但没有真实匿名链接、许可证、永久标识符或外部下载验证。
- **Concern：** “本地已打包”不等于审稿人可获取的复现资产，尤其本稿以 hash、tape、raw records 与不删种子作为可信度基础。
- **Resolution test：** 投稿前托管匿名仓库，在作者环境以外下载、校验 checksum、按 README 重建至少一张主图；明确许可证、checkpoint/runtime-state 可得性和接收后 DOI。此项不需要新训练，但未完成前不宜正式提交。

### R3-M2 — 安全结论必须持续呈现为碰撞--超时权衡

- **Axis：** safety / claim-moderation
- **Claim pointer：** 摘要、6.6 节、表2--表6、7.3 节与结论。
- **Evidence pointer：** 主 cohort 中 DRTP timeout 低于 UTR（0.694 vs 0.874），但 collision 略高（0.008 vs 0.005）；独立 cohort 中 DRTP 的碰撞与超时都更高。
- **Concern：** 单独突出 timeout 下降会给出“更安全”的过强印象。
- **Resolution test：** 所有摘要、结果、结论与投稿材料中同步给出 collision、timeout 和 constraint 的方向；将措辞固定为“任务收益与超时--碰撞权衡”，而非“安全性全面改善”。

### R3-m1 — 工程推广范围有限

- **Axis：** engineering-validity / claim-moderation
- **Claim pointer：** 3.1 节、7.5 节、8 节。
- **Evidence pointer：** 三无人机轻量 3DOF 仿真、预定义故障组；缺少 4/5 UAV、真实通信栈、HIL 和实飞。
- **Concern：** 现有结果支持冻结仿真任务中的经验发现，不能支持部署就绪、规模泛化或真实飞行可靠性。
- **Resolution test：** 保持现有边界表述；题名、摘要和结论中应始终保留“中继节点故障下”“三无人机仿真/冻结条件”的限定。

## Cross-review synthesis

### Consensus strengths

1. 主 cohort 内 UTR--DRTP 的参数匹配、统一 10M final checkpoint、共同样本带、五个独立训练种子和完整安全审计，使“自适应相对均匀加权”的局部经验比较可信。
2. 论文没有隐藏 seed2302、历史不利种子、MAPPO-NoGraph 的安全优势或独立 2401--2405 cohort 的方向反转；这种分层透明性是稿件最突出的可信度优势。
3. 中继故障被定义为合法路径与任务支持重构，而不是凭空的信息恢复；触发器技术有效性与策略失败被正确区分。

### Consensus technical risks

1. **跨 cohort 可靠性：** 正式主 cohort 的正向与独立 cohort 的完整反向并存，任何超出正式 cohort 的稳定性/可重复性声明均不成立。
2. **机制可辨识性：** 缺少同 cohort 固定非均匀权重对照，故只能证明相对均匀权重的经验差异；采样器 telemetry 也不能解释策略层因果机制。
3. **投稿级复现：** 本地包已核验，但匿名外部托管与外部下载复现尚未完成。
4. **安全权衡与工程范围：** 碰撞--超时方向不一致，且三 UAV 3DOF 仿真不等同于部署验证。

### Where emphasis differs

- Reviewer 1 认为统计和 cohort 分层是稿件可信度核心；
- Reviewer 2 更关注方法原创性与“自适应必要性”没有被识别；
- Reviewer 3 将外部可复现资产与安全权衡视为投稿程序和表述的首要风险。

### Broad-interest / significance readout

该稿的价值不在于声称通用鲁棒 MARL 突破，而在于给出一个工程上具体、证据边界清晰的案例：训练期扰动加权可在受控 cohort 中取得明显任务增益，但平均收益不能取代训练可靠性报告。它更适合应用导向 UAV/MARL 中文期刊读者；从现有证据不能推到广泛的通用自主系统结论。

### Submission posture

从科学内容看，稿件可停止新增训练并进入期刊化收口；从投稿程序看，必须先完成匿名仓库托管、作者元数据和目标模板迁移。是否接收由目标期刊编辑与真实审稿过程决定，本报告不作编辑决定。

## Risk / unsupported claims

- 不支持 DRTP 在独立训练 cohort 或随机初始化上稳定优越；
- 不支持 `J_pert,mean` / `J_pert,worst` 是 strict OOD 或一般分布外泛化证据；
- 不支持 DRTP 优于任意固定非均匀 sampler，或 online adaptation 的必要性；
- 不支持权重遥测单独证明具体策略层重规划机制；
- 不支持“DRTP 全面更安全”、4/5 UAV 可扩展、HIL/实飞有效或部署就绪；
- 不可评估目标期刊格式、作者元数据、匿名链接的真实访问性、checkpoint 实体发布，以及共同硬件的资源成本比较。
