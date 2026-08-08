"""Render the Chinese manuscript's code-traceable three-relation schematic.

This is a schematic only: it reads no experiment results and must stay aligned with
docs/figure_contracts/FACT_MANIFEST_METHOD_FIGURE.md (MF01--MF10).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "paper_chinese" / "figures"
FACT_MANIFEST = ROOT / "docs" / "figure_contracts" / "FACT_MANIFEST_METHOD_FIGURE.md"

COLORS = {
    "perception": "#2C7FB8",
    "communication": "#F28E2B",
    "support": "#59A14F",
    "actor": "#4E79A7",
    "target": "#D37295",
    "failure": "#C44E52",
    "module": "#EFF3F8",
    "ink": "#1F2933",
}


def configure_font() -> None:
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        fm.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = "Microsoft YaHei"
    plt.rcParams.update({"axes.unicode_minus": False, "pdf.fonttype": 42, "ps.fonttype": 42})


def arrow(ax, start, end, color, label=None, curve=0.0, style="-"):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        connectionstyle=f"arc3,rad={curve}",
        mutation_scale=13,
        linewidth=2.1,
        linestyle=style,
        color=color,
        shrinkA=20,
        shrinkB=20,
        zorder=2,
    )
    ax.add_patch(patch)
    if label:
        x = (start[0] + end[0]) / 2
        y = (start[1] + end[1]) / 2 + 0.07 + curve * 0.4
        ax.text(x, y, label, ha="center", va="center", fontsize=9, color=color, weight="bold")


def node(ax, xy, title, subtitle, facecolor):
    ax.add_patch(Circle(xy, radius=0.095, facecolor=facecolor, edgecolor="white", linewidth=1.7, zorder=3))
    ax.text(xy[0], xy[1], title, ha="center", va="center", color="white", fontsize=10, weight="bold", zorder=4)
    ax.text(xy[0], xy[1] - 0.15, subtitle, ha="center", va="top", fontsize=9, color=COLORS["ink"])


def module(ax, x, y, w, h, text, subtext=None):
    ax.add_patch(
        FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.025", facecolor=COLORS["module"], edgecolor="#6B7C93", linewidth=1.1)
    )
    ax.text(x + w / 2, y + h * (0.60 if subtext else 0.5), text, ha="center", va="center", fontsize=10, color=COLORS["ink"], weight="bold", wrap=True)
    if subtext:
        ax.text(x + w / 2, y + h * 0.28, subtext, ha="center", va="center", fontsize=8.5, color="#52606D", wrap=True)


def draw_task_panel(ax):
    ax.set_title("a  任务链与故障窗口", loc="left", fontsize=12, weight="bold", color=COLORS["ink"])
    positions = {"scout": (0.17, 0.65), "relay": (0.48, 0.65), "attacker": (0.79, 0.65), "target": (0.79, 0.25)}
    node(ax, positions["scout"], "Scout", "侦察", COLORS["actor"])
    node(ax, positions["relay"], "Relay", "中继", COLORS["actor"])
    node(ax, positions["attacker"], "Attack", "攻击", COLORS["actor"])
    node(ax, positions["target"], "Target", "目标（非 actor）", COLORS["target"])
    arrow(ax, positions["scout"], positions["relay"], COLORS["communication"], "环境递送通信")
    arrow(ax, positions["relay"], positions["attacker"], COLORS["communication"], None)
    arrow(ax, positions["scout"], positions["target"], COLORS["perception"], "有效感知", curve=-0.20, style="--")
    arrow(ax, positions["attacker"], positions["target"], COLORS["support"], "任务支撑", curve=0.12)
    ax.add_patch(FancyBboxPatch((0.33, 0.86), 0.30, 0.075, boxstyle="round,pad=0.02", facecolor="#FCE8E6", edgecolor=COLORS["failure"], linewidth=1.1))
    ax.text(0.48, 0.898, "Relay 失效窗口：节点状态", ha="center", va="center", fontsize=9, color=COLORS["failure"], weight="bold")
    ax.annotate("通信可达性由距离、丢包、时延和故障决定", xy=(0.48, 0.48), xytext=(0.48, 0.08), ha="center", fontsize=8.5, color="#52606D", arrowprops={"arrowstyle": "-", "color": "#8A9AA9"})
    ax.text(0.02, 0.98, "攻击窗口是局部状态/Task-Support 条件，不是第四类关系", transform=ax.transAxes, fontsize=8.5, color="#52606D", va="top")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_encoder_panel(ax):
    ax.set_title("b  三关系编码与策略聚合", loc="left", fontsize=12, weight="bold", color=COLORS["ink"])
    module(ax, 0.03, 0.62, 0.20, 0.20, "局部观测\n+与可用图", "3 个 actor + 目标")
    module(ax, 0.31, 0.62, 0.23, 0.20, "三关系邻接", "感知｜通信｜任务支撑")
    module(ax, 0.62, 0.62, 0.27, 0.20, "两层关系专属\n+边特征注意力", "17 维边特征进入 attention")
    module(ax, 0.62, 0.27, 0.27, 0.17, "联合图 GAT 残差", "union-graph residual")
    module(ax, 0.31, 0.27, 0.23, 0.17, "静态 Role-Pair 调制", "仅 relation × role pair")
    module(ax, 0.03, 0.27, 0.20, 0.17, "Gate Prior", "选定 logit 初值 0.4")
    module(ax, 0.37, 0.05, 0.35, 0.12, "分散 actor 输出", "集中训练 critic 使用共享状态")
    for start, end in [((0.23, 0.72), (0.31, 0.72)), ((0.54, 0.72), (0.62, 0.72)), ((0.755, 0.62), (0.755, 0.44)), ((0.54, 0.355), (0.62, 0.355)), ((0.23, 0.355), (0.31, 0.355)), ((0.16, 0.27), (0.48, 0.17)), ((0.425, 0.27), (0.52, 0.17)), ((0.755, 0.27), (0.62, 0.17))]:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, linewidth=1.4, color="#6B7C93"))
    ax.text(0.48, 0.92, "关系邻接是图聚合硬掩码；不等同于可学习的物理通信载荷", ha="center", fontsize=8.5, color="#52606D")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def main() -> None:
    configure_font()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.1), constrained_layout=True)
    draw_task_panel(axes[0])
    draw_encoder_panel(axes[1])
    fig.text(0.5, 0.012, "EA-RG-MAPPO-S：故障后任务链恢复的三关系任务图表示", ha="center", fontsize=12, weight="bold", color=COLORS["ink"])
    for suffix, dpi in (("png", 300), ("pdf", None)):
        fig.savefig(OUT_DIR / f"fig1_three_relation_task_graph.{suffix}", dpi=dpi, bbox_inches="tight")
    manifest_hash = hashlib.sha256(FACT_MANIFEST.read_bytes()).hexdigest()
    provenance = (
        "Schematic fact source: docs/figure_contracts/FACT_MANIFEST_METHOD_FIGURE.md\n"
        f"SHA256: {manifest_hash}\n"
        "Script: scripts/render_zh_three_relation_method_figure.py\n"
        "Relations shown: perception, communication, task-support only.\n"
    )
    with (OUT_DIR / "fig1_three_relation_task_graph.provenance.txt").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(provenance)


if __name__ == "__main__":
    main()
