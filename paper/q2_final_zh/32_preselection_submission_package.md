# DRTP 中文稿：选刊前投稿材料包

**状态：** `READY_WITH_AUTHOR_CHECKS`
**范围：** 本材料包服务于 `DRTP-SG-MAPPO` 中文科学终稿的首次投稿；尚未选择目标期刊，故不伪造期刊格式、作者身份、基金、审稿人、匿名链接或许可信息。

## 1. 投稿就绪度

**一条主论证。** 在异构三无人机的合法通信—任务图中，中继节点故障会引起路径组成与任务支持来源重构；在正式、冻结的五种子 cohort 中，有界自适应拓扑扰动重加权相对于均匀拓扑随机化表现出正向的任务端点收益，但独立三方法 cohort 的完整反向结果说明该收益不具有已证实的跨 cohort 稳定性。

**读者与价值。** 航空智能控制、无人机集群协同、通信受限多智能体决策和训练可靠性研究者，可据此评估一个将网络、PPO、奖励和正常工况暴露锚点固定后的训练分布比较，以及其可复现边界。

**投稿状态。** `READY_WITH_AUTHOR_CHECKS`：科学终稿、补充材料、证据 manifest、本地匿名复现包和预审稿已完成；目标期刊、作者元数据、实际匿名仓库和模板迁移尚未完成。

## 2. Deliverable matrix

| 材料 | 状态 | 现有来源 | 作者仍需完成 |
|---|---|---|---|
| 匿名主稿 | 已完成 | `paper/q2_final_zh/output/DRTP_SG_MAPPO_中文论文终稿_投稿前审稿版.pdf` | 按目标刊模板迁移并人工核验 |
| 补充材料 | 已完成 | `paper/q2_final_zh/supplementary/` | 确认目标刊的附件命名/文件大小要求 |
| 证据与复现包 | 本地 staging 已完成 | `output/drtp_relay_failure_anonymous_reproducibility_v1/` | 外部匿名托管、独立下载与 checksum 验证 |
| 题名页 | 已有模板 | 本文第 4 节 | 填真实作者、单位、通讯方式、基金 |
| 投稿信 | 已有模板 | 本文第 5 节 | 填期刊、编辑称谓、通讯作者与原创性事实 |
| Highlights/编辑摘要 | 已有模板 | 本文第 6 节 | 核对目标刊是否要求、字符上限与语言 |
| 声明 | 已有模板 | 本文第 7 节 | 填 CRediT、冲突、基金、许可、仓库链接 |
| 建议/回避审稿人 | 不预填 | — | 由作者核实身份与利益冲突后另行提供 |
| 图文摘要 | 未创建 | — | 仅在目标刊要求时另行制作；不应由 AI 视觉草图替代科学示意图 |

## 3. 跨文件一致性硬约束

以下文字必须在主稿、摘要、投稿信、亮点、补充材料、数据声明与投稿系统中一致：

1. 正式主比较为 UTR-SG-MAPPO vs DRTP-SG-MAPPO，五个训练前冻结种子 2301--2305、共同 10M 最终 checkpoint；
2. MAPPO-NoGraph 是架构/输入不同的性能参考，而非 DRTP 因果机制的主消融；
3. 独立 UTR/SNR/DRTP cohort（2401--2405）完整保留且出现反向结果；不与主 cohort 合并为 `n=10`；
4. `J_pert,mean` 和 `J_pert,worst` 是训练 support 内的跨扰动端点，不能写为 strict OOD；
5. 不主张信息恢复、一般 DRO、普适拓扑泛化、seed-stable superiority，或在线自适应相对于任意固定非均匀权重的必要性；
6. 主 cohort 的 task-score 改善与 timeout 降低必须同时配对报告 collision 从 0.005 升至 0.008 的事实；
7. 未经目标刊要求或作者的单独新授权，不新增训练、种子、checkpoint promotion 或后续算法作为本文结果。

## 4. 题名页模板（identified version）

> 匿名送审稿不得包含本节的作者识别字段；双盲要求以目标刊最新官方指南为准。

```text
题目：中继节点故障下异构多无人机拓扑鲁棒协同：有界自适应拓扑扰动重加权与种子敏感性

短题名：【AUTHOR_INPUT_NEEDED：不超过目标刊限制】
文章类型：【AUTHOR_INPUT_NEEDED：研究论文/学术论文等】
目标期刊：【AUTHOR_INPUT_NEEDED】

作者：
【AUTHOR_INPUT_NEEDED：姓名 1】1，
【AUTHOR_INPUT_NEEDED：姓名 2】2，……

1.【AUTHOR_INPUT_NEEDED：单位、城市、邮编】
2.【AUTHOR_INPUT_NEEDED：单位、城市、邮编】

通讯作者：【AUTHOR_INPUT_NEEDED：姓名、邮箱、通信地址】
ORCID：【AUTHOR_INPUT_NEEDED：仅在作者确认后填写】
基金项目：【AUTHOR_INPUT_NEEDED：规范名称与编号】
图数/表数：【AUTHOR_INPUT_NEEDED：按模板核算】
字数：【AUTHOR_INPUT_NEEDED：按目标刊统计规则核算】
```

## 5. 初次投稿信模板

```text
尊敬的【编辑/编辑部】：

谨提交题为《中继节点故障下异构多无人机拓扑鲁棒协同：有界自适应拓扑扰动重加权与种子敏感性》的稿件，申请作为【文章类型】在《【目标期刊】》审阅。

本文研究异构三无人机协同中中继节点故障导致的通信—任务路径重构。在不改变单图 MAPPO 策略网络、PPO 目标、奖励、环境和执行期信息边界的条件下，本文将训练期方法差异限定为：均匀拓扑扰动随机化与有界自适应拓扑扰动重加权。正式五个配对训练种子的共同 10M 最终检查点结果显示，DRTP 相对匹配的均匀基线在 F0、跨扰动平均和跨扰动最差端点上均呈正向配对差值，同时平均超时率降低。

本文的贡献不在于宣称一般化的鲁棒性保证，而在于提供一个中继故障语义、合法信息边界、训练分布对照和种子级记录均可核验的受控实证研究。为保持结论边界，稿件还完整披露一个独立三方法 10M cohort 的反向结果；该 cohort 不与正式主 cohort 合并统计，并表明 DRTP 的跨训练 cohort 可靠性有限。无图 MAPPO 仅作为架构/输入不同的性能参考，不被用于 DRTP 因果归因。

我们认为本文与《【目标期刊】》读者对【AUTHOR_INPUT_NEEDED：根据官方范围填写的航空控制/无人机协同/系统可靠性/多智能体决策入口】的关注相契合。投稿时将按期刊要求提供匿名主稿、补充材料、合同与数据/代码可用性说明。复现包包含冻结配置、评价 tape manifest、原始 episode 指标、种子级汇总、作图与核验脚本；其匿名访问链接与 checkpoint 获取策略将在作者完成实际托管后填入。

【AUTHOR_INPUT_NEEDED：声明本文未一稿多投/未公开发表；所有作者已审阅并同意投稿；预印本、会议版本、相关稿件与利益冲突情况。不得在未核实前保留本段为肯定表述。】

感谢审阅。

此致
敬礼！

【通讯作者姓名】
【单位】
【邮箱】
【日期】
```

## 6. Highlights 与编辑摘要模板

### 6.1 Highlights（投稿前按字符限制压缩）

- 将中继节点故障建模为合法通信—任务路径重构，而非默认的完全信息中断。
- 在网络、PPO、奖励和正常工况锚点匹配的条件下，比较有界自适应加权与均匀拓扑随机化。
- 正式五种子 10M cohort 中，DRTP 在 F0 与跨扰动任务端点上均呈正向配对收益，并降低平均超时率。
- 透明报告碰撞—超时权衡与独立 cohort 反向结果，将训练可靠性作为结论边界而非删除不利证据。

### 6.2 编辑摘要/意义声明

中继节点故障改变的未必是“有没有信息”，而可能是可合法利用的信息路径与任务支持来源。本文以受控的异构三无人机环境，将这一变化与训练分布设计联系起来。结果表明，有界自适应拓扑扰动加权在一个冻结的五种子正式 cohort 中可改善多类扰动端点，但独立 cohort 的反向结果也表明该策略不能被表述为跨初始化稳定优越。该证据结构为通信受限无人机 MARL 的性能报告、训练种子处理与可靠性边界提供了可审计范例。

## 7. 声明模板

### 数据与代码可用性

```text
支撑本文正式 UTR--DRTP cohort、MAPPO-NoGraph 性能参考和完整独立三方法重复 cohort 的匿名复现包，将在审稿阶段通过【AUTHOR_INPUT_NEEDED：真实匿名访问链接】向审稿人提供。该包包括冻结合同、配置、评价 tape manifest、episode 级原始指标、种子级汇总、图表源数据、统计与核验脚本以及 SHA256 manifest。checkpoint 与 runtime-state 文件【AUTHOR_INPUT_NEEDED：公开存放地址/受限获取条件】；其 hash 与 schema 已包含在复现包中。文章发表后，材料将以【AUTHOR_INPUT_NEEDED：许可证】在【AUTHOR_INPUT_NEEDED：正式仓库 DOI 或永久标识】公开。
```

### CRediT 作者贡献

```text
概念化：【AUTHOR_INPUT_NEEDED】；方法学：【AUTHOR_INPUT_NEEDED】；软件：【AUTHOR_INPUT_NEEDED】；验证：【AUTHOR_INPUT_NEEDED】；形式分析：【AUTHOR_INPUT_NEEDED】；调查：【AUTHOR_INPUT_NEEDED】；资源：【AUTHOR_INPUT_NEEDED】；数据整理：【AUTHOR_INPUT_NEEDED】；初稿写作：【AUTHOR_INPUT_NEEDED】；写作—审阅与编辑：【AUTHOR_INPUT_NEEDED】；可视化：【AUTHOR_INPUT_NEEDED】；监督：【AUTHOR_INPUT_NEEDED】；项目管理：【AUTHOR_INPUT_NEEDED】；经费获取：【AUTHOR_INPUT_NEEDED】。
```

### 利益冲突、基金、伦理与原创性

```text
利益冲突：【AUTHOR_INPUT_NEEDED：无/具体说明】。
基金项目：【AUTHOR_INPUT_NEEDED：规范名称与编号】。
伦理与知情同意：本研究为计算机仿真研究，不涉及人类受试者、人体样本或动物实验；【AUTHOR_INPUT_NEEDED：仍需按目标期刊栏目要求确认是否保留】。
原创性与作者同意：【AUTHOR_INPUT_NEEDED：作者核实后填写未一稿多投、未公开发表、全体作者同意投稿及相关版本披露】。
```

## 8. AUTHOR_INPUT_NEEDED

1. 目标期刊、文章类型及该刊最新投稿指南；
2. 全部作者姓名、顺序、单位、通讯作者邮箱与 ORCID；
3. 基金、利益冲突、CRediT、预印本/会议版本/相关稿件和原创性事实；
4. 实际匿名仓库 URL、许可证、公开永久标识符、checkpoint/runtime-state 的访问策略；
5. 该期刊是否要求图文摘要、Highlights、审稿人建议、保密审查、双盲文件或其他报告清单；
6. 在非作者日常开发环境下完成的下载、SHA256 和关键图表重建证据。

## 9. 提交前最后核对顺序

1. 选择期刊后，依据其最新官方说明逐项标记 Deliverable matrix；
2. 外部托管匿名复现包，并以独立环境测试下载与核验；
3. 填写私有 `submission_release_metadata.json`，不得纳入匿名/公开源码；
4. 按目标刊模板生成匿名稿与 identified title page；
5. 人工核对主稿、补充、投稿信和数据声明满足第 3 节的七项硬约束；
6. 运行 `scripts/check_drtp_submission_release_gate.py --release-metadata ... --require-author-completion`；
7. 仅在输出 `SUBMISSION_RELEASE_READY` 后提交。
