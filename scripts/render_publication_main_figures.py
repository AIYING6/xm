"""Render redesigned publication figures without changing locked scientific evidence.

Fig. 1 is a code-traceable schematic based only on MF01--MF10. Fig. 2 reads
the frozen held-out inputs used by the locked survival analysis and visualizes
only the four methods authorised by the existing Fig. 2 contract.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper_chinese" / "figures" / "publication"
FACT_MANIFEST = ROOT / "docs" / "figure_contracts" / "FACT_MANIFEST_METHOD_FIGURE.md"
RAW_BASE = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_held_out_v1_5_10800_20260807/held_out_v1.5")
PRIMARY_SCENARIOS = {"dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure"}

COL = {
    "ink": "#20252B",
    "muted": "#68727D",
    "rule": "#C9D0D7",
    "panel": "#F8FAFC",
    "blue": "#0F4D92",          # EA-RG / perception
    "blue_light": "#7FA5CA",
    "brick": "#B65D54",         # MAPPO
    "happo": "#677C91",         # HAPPO
    "violet": "#8B7AA8",        # wider single graph
    "gold": "#C7952D",          # environment-delivered communication
    "green": "#4E8B68",         # task-support
    "target": "#BA7185",
    "failure": "#A85B5A",
}

METHODS = {
    "full_ea_rg": ("EA-RG", COL["blue"], "-", 2.6),
    "mappo": ("MAPPO", COL["brick"], "-", 1.55),
    "happo": ("HAPPO", COL["happo"], "-.", 1.35),
    "param_matched_single": ("宽单图", COL["violet"], "--", 1.25),
}


def apply_style() -> None:
    chinese = Path(r"C:\Windows\Fonts\msyh.ttc")
    if chinese.exists():
        fm.fontManager.addfont(str(chinese))
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "Arial", "DejaVu Sans", "Liberation Sans"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 7.3,
            "axes.linewidth": 0.8,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "legend.frameon": False,
            "axes.unicode_minus": False,
        }
    )


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.02, 1.025, label, transform=ax.transAxes, ha="left", va="bottom", fontsize=9.2, weight="bold", color=COL["ink"])


def rounded(ax: plt.Axes, xy: tuple[float, float], width: float, height: float, text: str, *, face="#F8FAFC", edge="#C9D0D7", fontsize: float = 6.7, weight: str = "normal") -> None:
    ax.add_patch(FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.012,rounding_size=0.028", facecolor=face, edgecolor=edge, linewidth=0.8))
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=fontsize, color=COL["ink"], weight=weight, linespacing=1.22)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], *, color: str, style: str = "-", width: float = 1.2, rad: float = 0.0, shrink: float = 13) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", connectionstyle=f"arc3,rad={rad}", mutation_scale=8.5, linewidth=width, linestyle=style, color=color, shrinkA=shrink, shrinkB=shrink, zorder=2))


def node(ax: plt.Axes, xy: tuple[float, float], abbr: str, label: str, color: str, *, subtitle: str | None = None) -> None:
    ax.add_patch(Circle(xy, radius=0.058, facecolor=color, edgecolor="white", linewidth=1.0, zorder=4))
    ax.text(*xy, abbr, ha="center", va="center", color="white", fontsize=6.7, weight="bold", zorder=5)
    ax.text(xy[0], xy[1] - 0.086, label, ha="center", va="top", fontsize=6.3, color=COL["ink"])
    if subtitle:
        ax.text(xy[0], xy[1] - 0.118, subtitle, ha="center", va="top", fontsize=5.8, color=COL["muted"])


def draw_method_figure() -> list[Path]:
    fig = plt.figure(figsize=(7.205, 4.65), facecolor="white", constrained_layout=False)
    gs = gridspec.GridSpec(2, 12, figure=fig, height_ratios=[1.04, 0.96], hspace=0.34, wspace=0.50)
    ax_a = fig.add_subplot(gs[0, :4])
    ax_b = fig.add_subplot(gs[0, 4:])
    ax_c = fig.add_subplot(gs[1, :])
    for ax in (ax_a, ax_b, ax_c):
        ax.set_axis_off()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    # (a) compact task/failure setting.
    panel_label(ax_a, "a")
    ax_a.text(0.02, 0.95, "故障后的任务链", fontsize=7.5, weight="bold", color=COL["ink"], va="top")
    pos = {"Scout": (0.14, 0.50), "Relay": (0.42, 0.50), "Attack": (0.70, 0.50), "Target": (0.84, 0.20)}
    node(ax_a, pos["Scout"], "S", "Scout", COL["blue"])
    node(ax_a, pos["Relay"], "R", "Relay", COL["blue"])
    node(ax_a, pos["Attack"], "A", "Attack", COL["blue"])
    node(ax_a, pos["Target"], "T", "Target", COL["target"])
    arrow(ax_a, pos["Scout"], pos["Relay"], color=COL["gold"], width=1.35)
    arrow(ax_a, pos["Relay"], pos["Attack"], color=COL["gold"], width=1.35)
    arrow(ax_a, pos["Scout"], pos["Target"], color=COL["blue"], style="--", width=1.1, rad=-0.18)
    arrow(ax_a, pos["Attack"], pos["Target"], color=COL["green"], width=1.1, rad=0.10)
    ax_a.add_patch(Circle((0.42, 0.61), radius=0.018, facecolor=COL["failure"], edgecolor="white", linewidth=0.5, zorder=6))
    ax_a.text(0.42, 0.72, "中继失效", ha="center", va="bottom", fontsize=5.8, color=COL["failure"])
    ax_a.text(0.02, 0.035, "失效打断信息链；恢复由稳定任务链窗口定义", fontsize=5.8, color=COL["muted"])

    # (b) enlarged task graph / relation representation.
    panel_label(ax_b, "b")
    ax_b.text(0.02, 0.95, "三关系任务图", fontsize=7.5, weight="bold", color=COL["ink"], va="top")
    p = {"Scout": (0.20, 0.53), "Relay": (0.47, 0.70), "Attack": (0.73, 0.53), "Target": (0.47, 0.26)}
    node(ax_b, p["Scout"], "S", "Scout", COL["blue"])
    node(ax_b, p["Relay"], "R", "Relay", COL["blue"])
    node(ax_b, p["Attack"], "A", "Attack", COL["blue"])
    node(ax_b, p["Target"], "T", "Target", COL["target"])
    arrow(ax_b, p["Scout"], p["Target"], color=COL["blue"], style="--", width=1.55, rad=-0.08)
    arrow(ax_b, p["Relay"], p["Target"], color=COL["blue"], style="--", width=1.2, rad=0.07)
    arrow(ax_b, p["Scout"], p["Relay"], color=COL["gold"], width=1.55, rad=0.03)
    arrow(ax_b, p["Relay"], p["Attack"], color=COL["gold"], width=1.55, rad=0.03)
    arrow(ax_b, p["Scout"], p["Attack"], color=COL["green"], width=1.35, rad=-0.23)
    arrow(ax_b, p["Relay"], p["Attack"], color=COL["green"], width=1.15, style="--", rad=-0.07)
    relation_key = [
        ("感知", COL["blue"], "--"),
        ("环境递送通信", COL["gold"], "-"),
        ("任务支撑", COL["green"], "-"),
    ]
    for idx, (label, color, style) in enumerate(relation_key):
        x = 0.08 + idx * 0.30
        ax_b.plot([x, x + 0.055], [0.08, 0.08], color=color, linewidth=1.65, linestyle=style, solid_capstyle="round")
        ax_b.text(x + 0.07, 0.08, label, va="center", fontsize=5.8, color=COL["muted"])
    ax_b.text(0.98, 0.94, "三类关系", ha="right", va="top", fontsize=5.7, color=COL["muted"])

    # (c) selective coordination module: relation-specific encoder is hero.
    panel_label(ax_c, "c")
    ax_c.text(0.02, 0.95, "EA-RG 协同编码", fontsize=7.5, weight="bold", color=COL["ink"], va="top")
    rounded(ax_c, (0.04, 0.36), 0.14, 0.25, "局部观测\n+可用图", face="#F8FAFC", fontsize=6.6)
    rounded(ax_c, (0.29, 0.29), 0.26, 0.40, "关系专属编码\n+边特征注意力", face="#EAF1F8", edge=COL["blue"], fontsize=7.2, weight="bold")
    rounded(ax_c, (0.62, 0.36), 0.15, 0.25, "联合图\n+残差融合", face="#F8FAFC", fontsize=6.6)
    rounded(ax_c, (0.84, 0.36), 0.12, 0.25, "分散\n+actor", face="#F8FAFC", fontsize=6.6)
    rounded(ax_c, (0.32, 0.77), 0.20, 0.12, "Gate Prior · 静态 Role-Pair", face="#FBF7ED", edge="#D5B56C", fontsize=5.9)
    arrow(ax_c, (0.18, 0.485), (0.29, 0.485), color=COL["muted"], width=1.05, shrink=4)
    arrow(ax_c, (0.55, 0.485), (0.62, 0.485), color=COL["blue"], width=1.3, shrink=4)
    arrow(ax_c, (0.77, 0.485), (0.84, 0.485), color=COL["muted"], width=1.05, shrink=4)
    arrow(ax_c, (0.42, 0.77), (0.42, 0.69), color="#C7952D", width=0.95, shrink=2)
    ax_c.text(0.42, 0.17, "关系邻接是图聚合掩码；不是策略学习的物理通信开关", ha="center", fontsize=5.9, color=COL["muted"])
    ax_c.text(0.97, 0.05, "17 维边特征", ha="right", fontsize=5.8, color=COL["muted"])

    fig.subplots_adjust(left=0.055, right=0.985, top=0.94, bottom=0.09)
    return export(fig, "fig1_method_overview_publication")


def role_icon(ax: plt.Axes, role: str, xy: tuple[float, float], scale: float = 1.0, alpha: float = 1.0) -> None:
    """Minimal vector pictograms; the icon does not encode unimplemented physics."""
    x, y = xy
    color = {"scout": "#175A96", "relay": "#3C7C47", "attacker": "#BB3C36", "target": "#7650A5"}[role]
    if role in {"scout", "relay"}:
        ax.add_patch(Circle((x, y), 0.026 * scale, facecolor=color, edgecolor="white", linewidth=0.5, alpha=alpha, zorder=5))
        for dx, dy in ((-0.05, 0.028), (0.05, 0.028), (-0.05, -0.028), (0.05, -0.028)):
            ax.plot([x, x + dx], [y, y + dy], color=color, linewidth=1.0 * scale, alpha=alpha, zorder=4)
            ax.add_patch(Circle((x + dx, y + dy), 0.014 * scale, fill=False, edgecolor=color, linewidth=1.0 * scale, alpha=alpha, zorder=4))
        if role == "relay":
            for r in (0.040, 0.058):
                ax.add_patch(Arc((x, y + 0.035 * scale), r * 2, r * 1.25, theta1=28, theta2=152, color=color, linewidth=0.8 * scale, alpha=alpha))
    elif role == "attacker":
        ax.add_patch(Polygon([(x - 0.07 * scale, y), (x + 0.06 * scale, y + 0.03 * scale), (x + 0.075 * scale, y), (x + 0.06 * scale, y - 0.03 * scale)], closed=True, facecolor=color, edgecolor="white", linewidth=0.5, alpha=alpha, zorder=5))
        ax.plot([x - 0.02 * scale, x + 0.02 * scale], [y, y], color="white", linewidth=0.7 * scale, alpha=alpha, zorder=6)
    else:
        ax.add_patch(Circle((x, y), 0.024 * scale, facecolor="white", edgecolor=color, linewidth=1.2 * scale, alpha=alpha, zorder=5))
        for r in (0.045, 0.066):
            ax.add_patch(Arc((x, y), r * 2, r * 2, theta1=24, theta2=156, color=color, linewidth=0.9 * scale, alpha=alpha))


def relation_line(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], kind: str, *, alpha: float = 1.0, broken: bool = False) -> None:
    color, linestyle = {"perception": ("#1D5EAA", ":"), "communication": ("#3B7D47", "--"), "support": ("#E5812E", "-.")} [kind]
    if broken:
        mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        for a, b in ((start, (mid[0] - 0.025, mid[1])), ((mid[0] + 0.025, mid[1]), end)):
            arrow(ax, a, b, color="#AAB1B9", style="--", width=1.0, shrink=6)
        ax.text(mid[0], mid[1], "×", ha="center", va="center", fontsize=10, color="#B64342", weight="bold", zorder=7)
    else:
        arrow(ax, start, end, color=color, style=linestyle, width=1.25, shrink=6)


def framed(ax: plt.Axes) -> None:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False, edgecolor="#A9B0B8", linewidth=0.75, clip_on=False))


def draw_method_figure_v2() -> list[Path]:
    """Journal-page-style method overview with the same authorised Fig. 1 facts."""
    fig = plt.figure(figsize=(7.205, 5.05), facecolor="white")
    gs = gridspec.GridSpec(2, 10, figure=fig, height_ratios=[0.98, 1.17], hspace=0.0, wspace=0.0)
    ax_a = fig.add_subplot(gs[0, :5]); ax_b = fig.add_subplot(gs[0, 5:]); ax_c = fig.add_subplot(gs[1, :])
    for ax in (ax_a, ax_b, ax_c): framed(ax)
    # a: heterogeneous task scenario with only three relations.
    panel_label(ax_a, "a"); ax_a.text(0.07, 0.95, "异构任务场景", va="top", fontsize=7.6, weight="bold")
    loc = {"scout": (0.22, 0.66), "relay": (0.65, 0.69), "attacker": (0.28, 0.32), "target": (0.75, 0.28)}
    for role, text in (("scout", "Scout\n(S)"), ("relay", "Relay\n(R)"), ("attacker", "Attacker\n(A)"), ("target", "Target\n(T)")):
        role_icon(ax_a, role, loc[role], 1.0)
        ax_a.text(loc[role][0], loc[role][1] - 0.095, text, ha="center", va="top", fontsize=5.9, color={"scout":"#175A96","relay":"#3C7C47","attacker":"#BB3C36","target":"#7650A5"}[role])
    relation_line(ax_a, loc["scout"], loc["target"], "perception")
    relation_line(ax_a, loc["scout"], loc["relay"], "perception")
    relation_line(ax_a, loc["relay"], loc["target"], "communication")
    relation_line(ax_a, loc["attacker"], loc["target"], "support")
    relation_line(ax_a, loc["relay"], loc["attacker"], "communication")
    ax_a.text(0.06, 0.08, "任务链恢复以稳定窗口为事件", fontsize=5.7, color=COL["muted"])
    # b: before/after failure and the task graph, without claiming learned recovery.
    panel_label(ax_b, "b"); ax_b.text(0.07, 0.95, "中继失效扰动协调：三关系任务图", va="top", fontsize=7.2, weight="bold")
    for x0, title, faulty in ((0.05, "失效前", False), (0.54, "中继失效后", True)):
        ax_b.add_patch(Rectangle((x0, 0.28), 0.40, 0.52, fill=False, edgecolor="#C7CDD4", linewidth=0.65))
        ax_b.text(x0 + 0.20, 0.84, title, ha="center", fontsize=6.1, weight="bold")
        pts = {"scout": (x0 + 0.09, 0.62), "relay": (x0 + 0.28, 0.67), "attacker": (x0 + 0.10, 0.40), "target": (x0 + 0.30, 0.40)}
        for role in pts: role_icon(ax_b, role, pts[role], 0.60, 0.30 if faulty and role == "relay" else 1.0)
        relation_line(ax_b, pts["scout"], pts["target"], "perception", alpha=0.7)
        relation_line(ax_b, pts["relay"], pts["target"], "communication", broken=faulty)
        relation_line(ax_b, pts["attacker"], pts["target"], "support", broken=faulty)
        if faulty:
            ax_b.add_patch(Circle(pts["relay"], 0.055, fill=False, edgecolor="#D14841", linewidth=1.0, linestyle=(0, (2, 2))))
            ax_b.text(*pts["relay"], "×", ha="center", va="center", fontsize=12, color="#C83232", weight="bold")
        ax_b.add_patch(FancyBboxPatch((x0 + 0.06, 0.07), 0.28, 0.12, boxstyle="round,pad=0.01,rounding_size=0.02", facecolor="#FAFBFC", edgecolor="#BBC3CC", linewidth=0.6))
        task = "S  →  R  →  A  →  T" if not faulty else "S  →  ○  →  A  →  T"
        ax_b.text(x0 + 0.20, 0.13, task, ha="center", va="center", fontsize=6.2, color=COL["ink"])
    # c: pipeline, with relation-specific encoder clearly dominant.
    panel_label(ax_c, "c"); ax_c.text(0.035, 0.94, "EA-RG 协同编码", va="top", fontsize=7.6, weight="bold")
    rounded(ax_c, (0.05, 0.43), 0.15, 0.25, "局部观测\n+可用图", fontsize=6.5)
    # small graph glyph rather than an equal-weight software block.
    rounded(ax_c, (0.26, 0.34), 0.18, 0.43, "多关系图", fontsize=6.5)
    gpts = [(0.30,0.58),(0.39,0.60),(0.32,0.43),(0.40,0.45)]
    for (x,y),c in zip(gpts,["#5E96C5","#85AE58","#D96745","#9C73B5"]): ax_c.add_patch(Circle((x,y),0.012,facecolor=c,edgecolor="white",linewidth=.3,zorder=5))
    ax_c.plot([gpts[0][0],gpts[1][0]],[gpts[0][1],gpts[1][1]],color="#1D5EAA",linestyle=":",lw=1)
    ax_c.plot([gpts[1][0],gpts[3][0]],[gpts[1][1],gpts[3][1]],color="#3B7D47",linestyle="--",lw=1)
    ax_c.plot([gpts[2][0],gpts[3][0]],[gpts[2][1],gpts[3][1]],color="#E5812E",linestyle="-.",lw=1)
    rounded(ax_c, (0.51, 0.32), 0.24, 0.47, "关系专属编码\n+边特征注意力", face="#EAF1F8", edge="#1D5EAA", fontsize=7.2, weight="bold")
    rounded(ax_c, (0.55, 0.83), 0.16, 0.09, "Gate Prior · 静态 Role-Pair", face="#FBF7ED", edge="#D5B56C", fontsize=5.6)
    rounded(ax_c, (0.79, 0.43), 0.12, 0.25, "联合图\n+残差融合", fontsize=6.2)
    rounded(ax_c, (0.93, 0.43), 0.055, 0.25, "分散\n+actor", fontsize=5.4)
    for s,e,col in [((0.20,.555),(.26,.555),COL["muted"]),((.44,.555),(.51,.555),"#1D5EAA"),((.75,.555),(.79,.555),"#1D5EAA"),((.91,.555),(.93,.555),COL["muted"]),((.63,.83),(.63,.79),"#C7952D")]: arrow(ax_c,s,e,color=col,width=1.0,shrink=2)
    ax_c.text(0.51, 0.19, "关系邻接为图聚合掩码，不是策略控制的物理通信", fontsize=5.6, color=COL["muted"])
    # shared legend strip, compact and print-safe with line style redundancy.
    ax_c.add_patch(FancyBboxPatch((0.05,0.035),0.90,0.09,boxstyle="round,pad=0.01,rounding_size=0.015",facecolor="white",edgecolor="#BCC3CB",linewidth=.6))
    legend = [("感知", "#1D5EAA", ":"), ("环境递送通信", "#3B7D47", "--"), ("任务支撑", "#E5812E", "-.")]
    for i,(label,color,style) in enumerate(legend):
        x=.28+i*.21; ax_c.plot([x,x+.035],[.08,.08],color=color,linestyle=style,lw=1.3); ax_c.text(x+.045,.08,label,va="center",fontsize=5.4)
    ax_c.text(.085,.08,"关系类型",va="center",fontsize=5.5,weight="bold")
    fig.subplots_adjust(left=.035,right=.99,top=.985,bottom=.035)
    return export(fig, "fig1_method_overview_publication")


def load_survival(method: str, seed: str) -> tuple[np.ndarray, np.ndarray, Path]:
    path = RAW_BASE / method / f"seed{seed}" / "test_episode_metrics.csv"
    times: list[float] = []
    events: list[int] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["scenario"] not in PRIMARY_SCENARIOS:
                continue
            failure_start = int(float(row["node_failure_start_step"]))
            steps = int(float(row["steps"]))
            if steps < failure_start:
                continue
            recovered = float(row["post_failure_chain_recovered"]) > 0.5
            times.append(float(row["post_failure_chain_recovery_steps"]) if recovered else float(steps - failure_start))
            events.append(int(recovered))
    return np.asarray(times), np.asarray(events), path


def km_step(times: np.ndarray, events: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(times)
    times, events = times[order], events[order]
    unique = np.unique(times)
    at_risk = len(times)
    survival = 1.0
    output = []
    for time in unique:
        at_time = times == time
        observed = int(events[at_time].sum())
        censored = int(at_time.sum()) - observed
        survival *= 1.0 - observed / at_risk
        output.append(survival)
        at_risk -= observed + censored
    return unique, np.asarray(output)


def draw_recovery_figure() -> tuple[list[Path], list[Path]]:
    curves: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    input_paths: list[Path] = []
    for method in METHODS:
        per_seed = [load_survival(method, seed) for seed in ("0", "1", "2")]
        assert all(len(times) == 200 for times, _events, _path in per_seed), f"Unexpected exposure count for {method}"
        curves[method] = (np.concatenate([times for times, _events, _path in per_seed]), np.concatenate([events for _times, events, _path in per_seed]))
        input_paths.extend(path for _times, _events, path in per_seed)

    fig = plt.figure(figsize=(7.205, 4.05), facecolor="white", constrained_layout=False)
    gs = gridspec.GridSpec(2, 10, figure=fig, width_ratios=[1, 1, 1, 1, 1, 1, 0.88, 0.88, 0.88, 0.88], height_ratios=[1, 1], hspace=0.48, wspace=0.72)
    ax_a = fig.add_subplot(gs[:, :6])
    ax_b = fig.add_subplot(gs[0, 6:])
    ax_c = fig.add_subplot(gs[1, 6:])

    for method, (label, color, linestyle, linewidth) in METHODS.items():
        times, events = curves[method]
        x, y = km_step(times, events)
        ax_a.step(np.r_[0, x], np.r_[1.0, y], where="post", color=color, linestyle=linestyle, linewidth=linewidth, label=label, zorder=3 if method == "full_ea_rg" else 2)
        ax_b.step(np.r_[0, x], np.r_[1.0, y], where="post", color=color, linestyle=linestyle, linewidth=linewidth, zorder=3 if method == "full_ea_rg" else 2)

    # (a) full process.
    panel_label(ax_a, "a")
    ax_a.set_title("故障后恢复全过程", loc="left", x=0.08, fontsize=7.7, weight="bold", pad=4)
    ax_a.axvline(80, color=COL["rule"], linewidth=0.9, linestyle=(0, (2, 2)), zorder=0)
    ax_a.text(80, 0.985, "τ = 80", ha="center", va="top", fontsize=5.9, color=COL["muted"])
    ax_a.set(xlim=(0, 220), ylim=(0, 1.03), xlabel="故障开始后的步数", ylabel="未恢复概率  $S(t)$")
    ax_a.set_xticks([0, 40, 80, 120, 160, 220])
    ax_a.set_yticks([0, 0.25, 0.50, 0.75, 1.00])
    ax_a.tick_params(length=2.5, width=0.7, pad=2)
    ax_a.legend(loc="upper right", fontsize=6.2, handlelength=2.0, labelspacing=0.45, borderpad=0.2)

    # (b) data-motivated early detail, selected as 0--35 because separation occurs during the initial event accumulation.
    panel_label(ax_b, "b")
    ax_b.set_title("早期细节", loc="left", x=0.11, fontsize=7.4, weight="bold", pad=4)
    ax_b.set(xlim=(0, 35), ylim=(0, 1.03), ylabel="$S(t)$")
    ax_b.set_xticks([0, 15, 30])
    ax_b.set_yticks([0, 0.5, 1.0])
    ax_b.tick_params(length=2.2, width=0.7, pad=1.5)
    ax_b.text(0.97, 0.07, "0–35 步", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.8, color=COL["muted"])

    # (c) effect magnitude: seed dots + pooled hierarchical bootstrap interval.
    panel_label(ax_c, "c")
    ax_c.set_title("RMST80 差异", loc="left", x=0.11, fontsize=7.4, weight="bold", pad=4)
    seed_delta = np.array([-2.64, -7.27, -1.21])
    pooled = float(seed_delta.mean())
    ci_low, ci_high = -7.16, -1.05
    y = np.array([3, 2, 1, 0])
    ax_c.axvline(0, color=COL["rule"], linewidth=0.9, linestyle=(0, (2, 2)), zorder=0)
    ax_c.scatter(seed_delta, y[:3], s=20, color=COL["blue_light"], edgecolor="white", linewidth=0.45, zorder=3)
    ax_c.plot([ci_low, ci_high], [y[3], y[3]], color=COL["blue"], linewidth=1.8, solid_capstyle="round", zorder=2)
    ax_c.scatter([pooled], [y[3]], s=28, color=COL["blue"], edgecolor="white", linewidth=0.5, zorder=3)
    ax_c.set(xlim=(-8.2, 1.1), ylim=(-0.6, 3.6), xlabel="EA-RG − MAPPO（步；负值=更早）")
    ax_c.set_xticks([-8, -4, 0])
    ax_c.set_yticks(y, ["seed 0", "seed 1", "seed 2", "合并"])
    ax_c.tick_params(length=2.2, width=0.7, pad=1.5)
    ax_c.text(pooled, 0.33, "−3.71  [−7.16, −1.05]", ha="center", va="bottom", fontsize=5.6, color=COL["blue"])
    ax_c.text(0.02, -0.44, "分层配对 bootstrap", transform=ax_c.transAxes, fontsize=5.6, color=COL["muted"])

    for ax in (ax_a, ax_b, ax_c):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(COL["muted"])
        ax.spines["bottom"].set_color(COL["muted"])

    fig.text(0.055, 0.012, "曲线汇总 3 个独立训练 seed、每方法 600 个 failure-exposed episodes；未恢复 episode 右删失。", ha="left", va="bottom", fontsize=5.8, color=COL["muted"])
    fig.subplots_adjust(left=0.085, right=0.985, top=0.94, bottom=0.16)
    return export(fig, "fig2_primary_recovery_publication"), input_paths


def export(fig: plt.Figure, name: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    base = OUT / name
    # SVG is intentionally first and has editable text through svg.fonttype='none'.
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    fig.savefig(base.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(
        base.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        facecolor="white",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    return [base.with_suffix(ext) for ext in (".svg", ".pdf", ".png", ".tiff")]


def draw_contact_sheet() -> list[Path]:
    fig, axes = plt.subplots(2, 1, figsize=(7.205, 8.25), facecolor="white", constrained_layout=True)
    assets = [
        ("Fig. 1 · 方法概览", OUT / "fig1_method_overview_publication.png"),
        ("Fig. 2 · 主要恢复证据", OUT / "fig2_primary_recovery_publication.png"),
    ]
    for ax, (title, path) in zip(axes, assets):
        ax.imshow(plt.imread(path))
        ax.set_title(title, loc="left", fontsize=9.4, weight="bold", pad=5)
        ax.axis("off")
    return export(fig, "publication_figure_contact_sheet")


def write_provenance(fig1: list[Path], fig2: list[Path], contact: list[Path], inputs: list[Path]) -> None:
    digest = hashlib.sha256()
    for path in sorted(inputs):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    text = (
        "Publication figure redesign bundle\n"
        "Fig. 1 fact source: MF01--MF10 only; no experimental numeric inputs.\n"
        "Fig. 2 source: frozen held-out inputs, Early + Nominal, 4 contract methods, 3 seeds, 200 matched exposures/method/seed.\n"
        "RMST80 forest values: seed deltas -2.64/-7.27/-1.21; pooled mean -3.71; hierarchical paired-bootstrap CI [-7.16, -1.05].\n"
        "Output width: 7.205 in (183 mm); SVG first, PDF and 600-dpi PNG fallback.\n"
        f"Raw input SHA256(path+content, 12 inputs): {digest.hexdigest()}\n"
        f"Files: {', '.join(path.name for path in fig1 + fig2 + contact)}\n"
    )
    with (OUT / "publication_figure_provenance.txt").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> None:
    apply_style()
    fig1 = draw_method_figure_v2()
    fig2, inputs = draw_recovery_figure()
    contact = draw_contact_sheet()
    write_provenance(fig1, fig2, contact, inputs)


if __name__ == "__main__":
    main()
