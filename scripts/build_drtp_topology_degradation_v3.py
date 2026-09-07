"""Create a visually polished Chinese DRTP manuscript framed around topology degradation.

Quantitative panels only use frozen aggregate results already stated in the source
manuscript.  The topology-statistics panel is explicitly a data-import contract;
it never substitutes a fabricated q trajectory or causal result for archived logs.

Figure export contract (delegated to ``save``): ``.png``, ``.tiff`` at dpi=600,
plus editable-text ``.svg`` and ``.pdf`` exports.
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from build_drtp_submission_ready_v2 import (
    BLUE, GREY, LIGHT, ORANGE, TEAL, arrow, box, fig4, fig5, fig6, insert_after, save, style_tables,
)

plt.rcParams.update({"font.family": ["Arial", "Microsoft YaHei"], "font.size": 9,
                     "axes.unicode_minus": False, "svg.fonttype": "none", "pdf.fonttype": 42})


def _edge(ax, p0, p1, color=BLUE, broken=False):
    if broken:
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        ax.plot([p0[0], mid[0] - .035], [p0[1], mid[1] + .02], color=color, lw=2, ls="--")
        ax.plot([mid[0] + .035, p1[0]], [mid[1] - .02, p1[1]], color=color, lw=2, ls="--")
        ax.text(mid[0], mid[1], "×", color="#D92D20", fontsize=18, ha="center", va="center", weight="bold")
    else:
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=2)


def _node(ax, p, label, color=TEAL):
    ax.add_patch(Circle(p, .045, fc="white", ec=color, lw=2, zorder=3))
    ax.text(p[0], p[1], label, ha="center", va="center", color=color, fontsize=7, weight="bold", zorder=4)


def fig1_problem(path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.7))
    normal = {"侦察": (.18, .52), "中继": (.49, .72), "执行": (.80, .52)}
    degraded = {"侦察": (.18, .52), "中继": (.49, .72), "执行": (.80, .52)}
    for ax, title, pts, fail in ((axes[0], "正常通信拓扑", normal, False), (axes[1], "通信拓扑退化", degraded, True)):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.add_patch(FancyBboxPatch((.03, .37), .94, .51, boxstyle="round,pad=.025,rounding_size=.03",
                                    fc="white", ec=TEAL if not fail else ORANGE, lw=1.7))
        _edge(ax, pts["侦察"], pts["中继"], TEAL if not fail else ORANGE, broken=fail)
        _edge(ax, pts["中继"], pts["执行"], TEAL if not fail else ORANGE, broken=False)
        for label, point in pts.items(): _node(ax, point, label, TEAL if not fail else ORANGE)
        ax.text(.5, .93, title, ha="center", color=TEAL if not fail else ORANGE, weight="bold", fontsize=12)
        message = "可达信息路径\n支持角色协同" if not fail else "局部信息可达性下降\n协同约束随之改变"
        ax.text(.5, .42, message, ha="center", va="center", color="#344054",
                bbox=dict(boxstyle="round,pad=.35", fc=LIGHT, ec="#D0D5DD"))
    chain = [("信息可达性下降", .18), ("协同约束变化", .50), ("需要鲁棒训练", .82)]
    for label, x in chain:
        fig.text(x, .12, label, ha="center", va="center", color=BLUE, weight="bold", fontsize=9,
                 bbox=dict(boxstyle="round,pad=.38", fc="#F2F5F8", ec="#B2CCFF"))
    for x in (.33, .65):
        fig.add_artist(FancyArrowPatch((x,.12),(x+.045,.12),transform=fig.transFigure,arrowstyle="-|>",mutation_scale=12,color=GREY))
    fig.text(.5, .025, "拓扑故障不是普通状态扰动：它改变联合策略可利用的信息结构，因而需要在训练阶段塑造面对结构退化的协同经验。",
             ha="center", color=GREY, fontsize=8.5)
    fig.tight_layout(rect=(0, .09, 1, 1)); save(fig, path)


def fig2_framework(path: Path):
    fig, ax = plt.subplots(figsize=(10.5, 3.4)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    p1 = box(ax, (.02, .44), "冻结拓扑\n故障库", TEAL, .15, .18)
    p2 = box(ax, (.20, .44), "名义组 N\n+ 故障组 F", BLUE, .15, .18)
    p3 = box(ax, (.38, .44), "相对名义的\n困难度估计", ORANGE, .15, .18)
    p4 = box(ax, (.56, .44), "有界单纯形\nq 更新", ORANGE, .15, .18)
    p5 = box(ax, (.74, .44), "reset 条件\n训练暴露", TEAL, .15, .18)
    p6 = box(ax, (.91, .44), "MAPPO\n协同策略", BLUE, .08, .18)
    for a, b in zip((p1, p2, p3, p4, p5), ((.20, .53), (.38, .53), (.56, .53), (.74, .53), (.91, .53))): arrow(ax, a, b)
    ax.text(.50, .88, "DRTP：面向通信拓扑退化的鲁棒性塑造", ha="center", weight="bold", color=BLUE, fontsize=12)
    ax.text(.50, .18, "保持不变：actor · critic · PPO objective · reward · observation · action interface · transition",
            ha="center", va="center", color=GREY, bbox=dict(boxstyle="round,pad=.42", fc=LIGHT, ec="#D0D5DD"))
    ax.text(.50, .08, "唯一变化：环境 reset 阶段在冻结条件组之间分配训练暴露", ha="center", color=TEAL, weight="bold")
    save(fig, path)


def _rows(csv_path: Path):
    with csv_path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fig3_mechanism(path: Path, assets: Path):
    """Plot real A/B sampler telemetry, keeping all associations descriptive."""
    groups = ["F0", "TE", "TL", "DS", "DL", "CP"]
    palette = [BLUE, TEAL, ORANGE, "#7A5AF8", "#12B76A", "#EAAA08"]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.25), gridspec_kw={"height_ratios": [1.05, 1.0]})
    summaries = {}
    for cohort in ("A", "B"):
        q_rows = _rows(assets / f"DRTP_MECHANISM_{cohort}_Q_TRAJECTORY.csv")
        group_rows = _rows(assets / f"DRTP_MECHANISM_{cohort}_GROUP_SUMMARY.csv")
        summaries[cohort] = {row["group"]: row for row in group_rows}
        milestones = sorted({float(row["milestone_fraction"]) for row in q_rows})
        ax = axes[0, 0 if cohort == "A" else 1]
        for group, color in zip(groups, palette):
            means, sds = [], []
            for milestone in milestones:
                values = [float(row[f"q_{group}"]) for row in q_rows if float(row["milestone_fraction"]) == milestone]
                means.append(float(np.mean(values))); sds.append(float(np.std(values, ddof=1)))
            x = np.array(milestones) * 100
            ax.plot(x, means, marker="o", ms=3.5, lw=1.8, color=color, label=group)
            ax.fill_between(x, np.maximum(0, np.array(means)-np.array(sds)), np.minimum(.35, np.array(means)+np.array(sds)), color=color, alpha=.10, linewidth=0)
        ax.axhline(1/6, color="#98A2B3", ls="--", lw=1, label="UTR 均匀值")
        ax.set_title(f"Cohort {cohort}：冻结 sampler q 轨迹（n=5）", loc="left", weight="bold", color=BLUE)
        ax.set_ylim(0, .38); ax.set_xlim(0, 100); ax.grid(alpha=.18); ax.set_xlabel("训练预算（%）"); ax.set_ylabel("非名义组概率 q")
        if cohort == "B": ax.legend(ncol=4, loc="upper left", frameon=False, fontsize=7)

    ax = axes[1, 0]
    for cohort, marker, color in (("A", "o", TEAL), ("B", "s", BLUE)):
        rows = summaries[cohort]
        xs = [float(rows[group]["mean_final_logged_difficulty"]) for group in groups]
        ys = [float(rows[group]["mean_actual_non_nominal_exposure_share"]) for group in groups]
        ax.scatter(xs, ys, s=45, marker=marker, color=color, label=f"Cohort {cohort}")
        for group, x, y in zip(groups, xs, ys): ax.annotate(group, (x, y), xytext=(4, 3), textcoords="offset points", fontsize=7, color=color)
    ax.set_title("组级困难度与实际训练暴露", loc="left", weight="bold", color=BLUE)
    ax.set_xlabel("最终记录困难度（组均值）"); ax.set_ylabel("实际非名义暴露份额"); ax.grid(alpha=.18); ax.legend(frameon=False, fontsize=8)
    ax.text(.98,.04,"描述性关联；非因果估计", transform=ax.transAxes, ha="right", va="bottom", color=GREY, fontsize=7)

    ax = axes[1, 1]
    deltas = [39.64, 23.16]
    bars = ax.bar(["Cohort A", "Cohort B"], deltas, color=[TEAL, BLUE], width=.58)
    ax.axhline(0, color="#344054", lw=.9); ax.set_ylim(0, 50); ax.set_ylabel("DRTP − UTR\n扰动回报均值")
    ax.set_title("冻结终点协同结果", loc="left", weight="bold", color=BLUE); ax.grid(axis="y", alpha=.18)
    for bar, value in zip(bars, deltas): ax.text(bar.get_x()+bar.get_width()/2, value+1.1, f"+{value:.2f}", ha="center", weight="bold")
    fig.text(.5, .012, "真实 q 轨迹、实际暴露与困难度均来自 SHA256 验证的最终训练包；manifest 未归档显式邻接/边列表，故本图不将故障组标签替代为连通性或最短路径统计。",
             ha="center", color=GREY, fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, 1)); save(fig, path)


FIGURES = {
    "图 1 通信拓扑退化问题概览": ("fig1_topology_degradation_problem.png", fig1_problem,
                              "通信拓扑退化问题概览：正常与退化通信图及其对信息可达性和协同约束的影响。"),
    "图 2 DRTP 的拓扑语义化鲁棒性塑造框架": ("fig2_drtp_framework.png", fig2_framework,
                                  "DRTP 框架：仅调整 reset 阶段训练暴露，保持策略学习接口不变。"),
    "图 3 拓扑退化、训练暴露与终点协同结果的机制验证图": ("fig3_mechanism_validation.png", fig3_mechanism,
                                          "A/B 真实 sampler 概率轨迹、组级训练暴露和冻结终点结果；关联只作描述性解释。"),
    "图 4 A/B cohort 的终点汇总与 seed 级配对图位": ("fig4_cohort_summary.png", fig4,
                                            "A/B cohort 的冻结终点汇总：均值、样本标准差与最差训练 seed。"),
    "图 5 冻结 OOD 拓扑泛化结果": ("fig5_ood.png", fig5,
                             "冻结结构与参数 OOD 协议下的 cohort-level 配对回报差。"),
    "图 6 六无人机跨尺度验证": ("fig6_6uav_placeholder.png", fig6,
                        "6-UAV 跨尺度验证占位图，待正式训练与固定终点评估完成后替换。"),
}


def add_alt_text(paragraph, description: str) -> None:
    for drawing in paragraph._p.xpath('.//wp:docPr'):
        drawing.set('descr', description)
        drawing.set('title', description[:80])


def set_table_headers(doc: Document) -> None:
    for table in doc.tables:
        tr_pr = table.rows[0]._tr.get_or_add_trPr()
        header = OxmlElement('w:tblHeader'); header.set(qn('w:val'), 'true'); tr_pr.append(header)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--figure-dir', type=Path, required=True)
    p.add_argument('--mechanism-assets', type=Path, default=Path('docs/drtp_final_paper_closure_20260907/mechanism_assets_final_ab'))
    args = p.parse_args()

    args.figure_dir.mkdir(parents=True, exist_ok=True)
    for _, (filename, creator, _) in FIGURES.items():
        destination = args.figure_dir / Path(filename).stem
        if filename.startswith('fig3_'):
            creator(destination, args.mechanism_assets)
        else:
            creator(destination)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.input, args.output)
    doc = Document(args.output)
    style_tables(doc); set_table_headers(doc)

    for paragraph in list(doc.paragraphs):
        target = next((caption for caption in FIGURES if paragraph.text.startswith(caption)), None)
        if target is None: continue
        filename, _, alt = FIGURES[target]
        paragraph.text = target
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in paragraph.runs:
            run.font.bold = True; run.font.color.rgb = RGBColor(22, 76, 120); run.font.size = Pt(9)
        image_para = insert_after(paragraph); image_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image_para.add_run().add_picture(str(args.figure_dir / filename), width=Cm(15.5))
        add_alt_text(image_para, alt)

    for paragraph in list(doc.paragraphs):
        if paragraph.text.strip().startswith('[图 ') or paragraph.text.strip().startswith('`[图 '):
            paragraph._element.getparent().remove(paragraph._element)
    for section in doc.sections:
        footer = section.footer.paragraphs[0]; footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.text = 'DRTP 中文投稿主稿（通信拓扑退化版）｜数值以冻结聚合产物与 manifest 为准'
        for run in footer.runs:
            run.font.size = Pt(8); run.font.color.rgb = RGBColor(102, 112, 133)
    doc.save(args.output)


if __name__ == '__main__':
    main()
