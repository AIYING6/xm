# -*- coding: utf-8 -*-
"""Revise the original long-form Chinese manuscript without replacing its body.

The project has several historical experiment lines.  This builder intentionally
uses the maintained long-form manuscript as the parent: it retains its reviewed
background, problem model, method derivation and reference list, while replacing
only the outdated experiment/result/appendix blocks with the final frozen A/B
evidence.  It prevents a compact evidence note from accidentally becoming the
new manuscript master.
"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "paper" / "q2_final_zh" / "main_zh.md"
EVIDENCE = ROOT / "paper" / "q2_final_zh" / "main_zh_final_ab.md"
OUT = ROOT / "paper" / "q2_final_zh" / "main_zh_original_master_evidence_integrated.md"


def span(text: str, begin: str, end: str) -> str:
    return text[text.index(begin): text.index(end)]


PROTOCOL = r'''## 5 最终冻结实验设计与证据分层

### 5.1 受控比较及唯一干预

本文的主要比较是 UTR-SG-MAPPO 与 DRTP-SG-MAPPO。在两种训练臂之间，单图 actor/critic、PPO 目标与超参数、奖励、局部观测、动作接口、执行期信息边界、环境转移、训练预算、名义工况质量和六类故障组支持集合均保持不变；唯一改变的是 reset 阶段六个冻结故障组之间的训练暴露质量。UTR 对六组采用均匀质量，DRTP 以训练期的名义相对困难代理周期性更新有界质量。因而该比较识别的是“有界自适应故障组暴露相对于均匀故障组暴露”的合同内增量，不是不同网络容量、不同输入信息或不同奖励塑形的比较。

每条轨迹从零开始训练至预先指定的 10M endpoint。最终 checkpoint 是唯一允许进入正式评估的检查点；训练过程的里程碑仅服务于恢复和训练日志，不参与性能驱动的 checkpoint 晋升、种子排除、提前停止或追加重跑。每个 cohort 内 UTR 与 DRTP 使用同一训练 seed 形成配对，但训练种子是唯一独立统计单位，不能把同一策略的多个条件或 episode 计为额外训练重复。

**表1｜本文证据层级与可回答问题。**

| 层级 | 证据对象 | 证据角色 | 允许的结论上限 |
|---|---|---|---|
| 最终冻结主比较 | A（78011--78015）和 B（78021--78025）的 UTR--DRTP 配对 endpoint | 主要受控比较 | 两个独立 cohort 中的 cohort 级结果与可靠性权衡 |
| 训练未读取 structural 条件带 | 固定 A/B checkpoint 的预先冻结 held-out tape | 分层泛化支撑 | 对该明确条件带的 endpoint 表现，非一般 OOD 保证 |
| PLR-style 比较 | 匹配预算的外部优先级式训练臂 | 外部定位 | 相同任务下的性能位置与回报--可靠性权衡，非主因果对照 |
| sampler 日志 | 10 条最终 DRTP 训练轨迹 | 实施与机制描述 | 训练暴露确已偏离均匀分配，非内部策略机制的因果证明 |
| 历史开发和早期队列 | 其他种子、其他协议或其他候选方法 | 来源追溯背景 | 不参与本文样本量、主表或主结论 |

### 5.2 双 cohort、固定 endpoint 与评估带

最终 A cohort 使用训练种子 78011--78015，B cohort 使用 78021--78025。两批训练种子、训练过程与 endpoint tape 相互独立；A/B 分层报告，任何 n=10 汇总仅可作描述性展示，不可替代两批分别成立的证据。评价在训练前冻结的名义与故障条件带上执行，记录原始 episode 指标并汇总为每个训练 seed 的 endpoint。当前主文将训练支持内的扰动条件称为“扰动条件”，而不把它们误称为 OOD。

为避免将后续资产与主比较混淆，训练完成后另对固定 A/B endpoint 执行训练未读取的 held-out tape。其 primary structural 条件带包含 Scout 节点故障、对称最长边删除、有向最长边删除以及 Scout 节点故障与边删除的复合；仅改变 relay 故障时机或时长的 parameter 条件只作诊断，不承担结构泛化结论。该 held-out 评价不重新训练、不选择 checkpoint，也不产生新的训练重复。

**表2｜冻结任务、策略接口与训练设置。**

| 类别 | 固定设置 |
|---|---|
| 任务实体 | 三架异构蓝方 UAV（Scout、Relay、Attacker）与一个目标 |
| 动力学与时域 | 轻量 3DOF；1 s 时间步；最大 260 步 |
| 执行期输入 | 本地状态、合法目标信息、合法图关系、缓存时效与任务支持状态；不输入故障标签或未来链路 |
| 动作空间 | 每架 UAV 从 27 个离散转向、爬升和加减速组合中选择动作 |
| 学习器 | 相同单图 MAPPO、CTDE、PPO 目标、网络参数量、奖励与训练预算 |
| 唯一方法差异 | reset 阶段六个冻结故障组的暴露质量：UTR 固定均匀；DRTP 有界自适应 |

**表3｜UTR 与 DRTP 的受控变量关系。**

| 项目 | UTR | DRTP | 是否构成方法差异 |
|---|---|---|---|
| actor/critic、PPO、奖励、观测、动作 | 相同 | 相同 | 否 |
| 名义工况质量 | 0.50 | 0.50 | 否 |
| 故障组支持集合与成员 | 相同 | 相同 | 否 |
| 故障组内成员采样 | 相同冻结规则 | 相同冻结规则 | 否 |
| 故障组间质量 | 六组均匀 | 基于名义相对困难的有界更新 | 是 |
| 执行期故障标签/隐藏信息 | 不输入 | 不输入 | 否 |

**表4｜训练条件组和报告端点的语义。**

| 对象 | 定义或角色 | 本文中允许的解释 |
|---|---|---|
| Nominal | 无 relay 故障的锚点工况 | 名义能力保持与困难代理的参考 |
| F0 | 典型 relay 故障（冻结 onset/duration） | 典型故障端点 |
| TE/TL | 较早/较晚 onset 的故障成员 | 训练支持内的时机扰动 |
| DS/DL | 较短/较长 duration 的故障成员 | 训练支持内的持续时间扰动 |
| CP | onset 和 duration 的复合故障成员 | 训练支持内的复合扰动 |
| \(J_{\mathrm{perturbed}}\) | 六个故障组端点的聚合任务回报 | 主要任务端点，不自动等同安全 |
| success/timeout/collision | 终局行为端点 | 与回报并列解释，不可互相替代 |

### 5.3 端点、统计单位与可靠性解释

主任务端点为每个训练 seed 的扰动条件平均任务回报 \(J_{\mathrm{perturbed}}\)。同时报告中位数、观测最差训练 seed、样本标准差及同 seed 的 DRTP--UTR 差，以区分中心趋势、离散度和下尾行为。成功率、超时率和碰撞率是独立的终局指标：较高回报不自动代表更安全，较低碰撞也不自动代表任务更优。本文不以 episode 数量构造训练重复的 p 值，也不将训练种子较少的描述性结果包装为逐 seed 保证。

正式解释遵循以下顺序：先看 A/B 分层的 UTR--DRTP 主比较，再看配对方向、下尾与成功/超时/碰撞的权衡；随后将 structural 条件带与 PLR-style 作为边界清楚的支撑性证据。旧 6-UAV v1 因故障注入发生在大量 episode 终止后而永久排除；fault-step=3 的 v2、全因子消融和统一硬件的运行开销在各自结果、原始记录和合同审计完成前不进入本文结论。

### 5.4 可复现性、检查点与排除规则

所有正式结果均由保存的最终 checkpoint、评价 manifest、逐 episode 原始指标、逐 seed 汇总和诊断报告组成可追溯链。训练与评估之间不允许依据回报替换 checkpoint；同一 cohort 内方法间使用共同的冻结 endpoint 规则。若某个历史试验的环境、故障时机、种子队列、算法臂或评价协议与最终 A/B 合同不一致，则它只能保留在归档中，不能通过改名、拼接或合并而成为本文的正式证据。

'''


APPENDICES = r'''## 附录A 最终证据与图表的可追溯性

主比较使用 A cohort（78011--78015）和 B cohort（78021--78025）的最终固定 10M endpoint。每个 cohort 的训练 seed、checkpoint、运行时状态、sampler manifest、评价 tape、逐 episode 指标和逐 seed 汇总均保留于相应归档。本文的图3--图6由这些归档中的原始 CSV 和训练日志重新生成；图源数据、归档 SHA256 和生成脚本由 `DRTP_FINAL_EVIDENCE_REGISTER_20260908.md`、`figure_source_data/` 及 `build_drtp_final_evidence_figures.py` 共同记录。

论文图表中的连线始终表示同一训练 seed 的方法配对，点表示一个训练 seed，横线表示 cohort 内均值。图中不以 episode 点替代训练重复，也不对 A/B 的分层结果进行确认性合并。由此，读者可以区分“环境运行次数多”与“独立训练初始化数量有限”这两个不同层面的不确定性来源。

## 附录B 证据排除与后续补充规则

本项目经历过多轮环境、训练分布和候选方法开发。为避免演变过程污染本文的最终叙事，任何早期 2301--2305、2401--2405 或其他不属于最终 A/B 冻结合同的结果均不进入摘要、主结果表、正式样本量或结论性语言。它们最多用于源代码演变、风险背景或补充材料中的来源说明。

跨规模证据仅接受故障注入时机已通过 Q0 审计的 6-UAV v2；旧 v1 不得以“训练已完成”为由进入结果。Fixed-DRTP/Random-DRTP 的析因消融只有在独立训练、固定 endpoint 与完整汇总完成后，才可检验组件必要性；在此之前，本文将采样器遥测写为实施事实，而非语义和自适应机制的因果拆分。运行开销同样只接受统一硬件、并发和预算下的实测 wall-clock、采样更新时间与峰值显存。

**表11｜结果进入主文的资格规则。**

| 资产 | 当前处理 | 原因 |
|---|---|---|
| 最终 A/B UTR--DRTP | 纳入主结果 | 同一最终冻结合同下的两批独立 cohort |
| structural held-out tape | 纳入分层结果 | 训练未读取、条件带预先冻结、固定 endpoint |
| PLR-style | 纳入外部定位 | 匹配预算的外部参考，但不替代主因果对照 |
| 早期历史队列 | 不进入主表或结论 | 协议、种子队列或研究目的不同 |
| 旧 6-UAV v1 | 永久排除 | 故障注入晚于大量 episode 终止 |
| 6-UAV v2、析因消融、运行开销 | TODO（需补证） | 尚未完成结果与来源审计 |

## 数据与代码可用性

用于生成本文主表与图3--图6的结构化汇总、图源数据和再生成脚本已在项目维护仓库中归档。训练 checkpoint 与原始 episode 记录以带 SHA256 的压缩归档管理；受存储与运行环境限制的部分可在合理请求下按相同 manifest 提供。论文中的每一项正式数值均应能回溯至相应 cohort 的评价汇总，而不能仅从正文转录。

## 作者贡献、利益冲突与资助

TODO（需补证）：按实际作者、单位、贡献角色、利益冲突及资助信息填写；此处不作虚构声明。
'''


def build() -> Path:
    parent = PARENT.read_text(encoding="utf-8")
    evidence = EVIDENCE.read_text(encoding="utf-8")
    intro = span(evidence, "# ", "## 2 相关工作")
    technical = span(parent, "## 2 相关工作", "## 5 实验协议")
    result_to_conclusion = span(evidence, "## 6 双 cohort 受控结果", "## 附录A")
    # Tables 2--4 are restored above from the original long-form protocol;
    # shift evidence tables without changing their values or narrative scope.
    result_to_conclusion = (
        result_to_conclusion.replace("表5", "表9")
        .replace("表4", "表8")
        .replace("表3", "表6")
        .replace("表2", "表5")
    )
    reliability_table = r'''
**表7｜主比较的任务端点与终局行为应分层阅读。** 均值在 cohort 内按五个训练 seed 汇总。

| Cohort | 方法 | 成功率 | 超时率 | 碰撞率 | 对任务回报的正确解释 |
|---|---|---:|---:|---:|---|
| A | UTR | 0.267 | 0.730 | 0.003 | 主比较基线 |
| A | DRTP | 0.394 | 0.597 | 0.009 | 成功/超时有利，但碰撞不完全同向 |
| B | UTR | 0.289 | 0.711 | 0.000 | 独立 cohort 基线 |
| B | DRTP | 0.398 | 0.602 | 0.000 | 成功/超时有利，碰撞持平 |

'''
    result_to_conclusion = result_to_conclusion.replace(
        "### 6.4 训练排除的结构条件带提供了有限的泛化支撑",
        reliability_table + "### 6.4 训练排除的结构条件带提供了有限的泛化支撑",
    )
    telemetry_table = r'''
**表10｜采样器遥测的可验证事实与解释边界。**

| 日志对象 | 可由日志直接验证 | 不能由日志单独验证 |
|---|---|---|
| 组质量 \(q\) | 各故障组的实际训练暴露偏离 UTR 的均匀质量 | 某一组质量必然导致某种策略表示或行为 |
| 名义相对困难代理 | 更新时使用的训练期统计量与组间差异 | 困难代理是唯一或充分的真实环境难度定义 |
| 组选择和计数 | 所有冻结组持续被覆盖且训练分布被重分配 | 训练分布变化已构成普适泛化机制证明 |

'''
    result_to_conclusion = result_to_conclusion.replace(
        "## 7 讨论",
        telemetry_table + "## 7 讨论",
    )
    references = span(parent, "## 参考文献", "## 附录A")
    OUT.write_text(
        intro + "\n" + technical + "\n" + PROTOCOL + "\n" + result_to_conclusion + "\n" + references + "\n" + APPENDICES,
        encoding="utf-8",
    )
    return OUT


if __name__ == "__main__":
    print(build())
