"""Render Chinese concept figures for the frozen DRTP manuscript.

The script only visualizes already-frozen task and method contracts. It never
reads rewards, changes experiment data, or runs training.
"""
from __future__ import annotations

from pathlib import Path
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "q2_final_zh" / "formal_results" / "figures"
BLUE = "#2563eb"
GREY = "#6b7280"
RED = "#dc2626"
GREEN = "#16a34a"
PURPLE = "#7c3aed"


def setup() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Noto Sans CJK SC", "SimHei", "Arial", "DejaVu Sans", "sans-serif"],
        "font.size": 8,
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / f"{stem}.svg"
    fig.savefig(svg_path, bbox_inches="tight")
    svg_path.write_text(re.sub(r"[ \t]+(?=\r?\n)", "", svg_path.read_text(encoding="utf-8")),
                        encoding="utf-8")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def node(ax, xy: tuple[float, float], label: str, color: str) -> None:
    ax.add_patch(Circle(xy, 0.075, facecolor=color, edgecolor="white", linewidth=1.5, zorder=3))
    ax.text(*xy, label, ha="center", va="center", color="white", fontsize=7, fontweight="bold", zorder=4)


def arrow(ax, left, right, color, text="", linestyle="-") -> None:
    ax.add_patch(FancyArrowPatch(left, right, arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.6, color=color, linestyle=linestyle, zorder=2))
    if text:
        ax.text((left[0] + right[0]) / 2, (left[1] + right[1]) / 2 + .075, text,
                ha="center", va="bottom", color=color, fontsize=7)


def box(ax, xywh, text: str, color: str = "#f3f4f6", fontsize: float = 7) -> None:
    x, y, w, h = xywh
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.025",
                                facecolor=color, edgecolor="#9ca3af", linewidth=.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)


def fig1() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.25))
    titles = ["(a) 异构角色与合法关系", "(b) 故障前：中继路径", "(c) 故障中：路径重构", "(d) 故障合同与信息边界"]
    for ax, title in zip(axes, titles):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.set_title(title, fontweight="bold", fontsize=8)

    ax = axes[0]
    node(ax, (.18, .57), "0", BLUE); node(ax, (.50, .57), "1", PURPLE); node(ax, (.82, .57), "2", RED)
    node(ax, (.50, .18), "T", GREEN)
    ax.text(.18, .41, "侦察机", ha="center", fontsize=6.5)
    ax.text(.50, .41, "中继机", ha="center", fontsize=6.5)
    ax.text(.82, .41, "攻击机", ha="center", fontsize=6.5)
    ax.text(.50, .06, "目标", ha="center", fontsize=6.5)
    arrow(ax, (.25, .57), (.43, .57), BLUE)
    arrow(ax, (.57, .57), (.75, .57), PURPLE)
    arrow(ax, (.22, .52), (.45, .23), GREEN, "感知")
    ax.text(.5, .87, "策略仅使用当前合法观测、边特征与消息状态", ha="center", fontsize=6.8)

    ax = axes[1]
    node(ax, (.16, .50), "0", BLUE); node(ax, (.50, .50), "1", PURPLE); node(ax, (.84, .50), "2", RED)
    arrow(ax, (.24, .50), (.42, .50), PURPLE)
    arrow(ax, (.58, .50), (.76, .50), PURPLE)
    ax.text(.5, .22, "缓存信息路径：0 → 1 → 2", ha="center", fontsize=7)
    ax.text(.5, .82, "正常 / 故障前", ha="center", color=GREY, fontsize=7)

    ax = axes[2]
    node(ax, (.16, .50), "0", BLUE); node(ax, (.50, .50), "1", "#d1d5db"); node(ax, (.84, .50), "2", RED)
    arrow(ax, (.24, .50), (.42, .50), RED, linestyle="--")
    arrow(ax, (.58, .50), (.76, .50), RED, linestyle="--")
    ax.text(.50, .65, "中继相关边失效", ha="center", color=RED, fontsize=6.6)
    arrow(ax, (.24, .40), (.76, .40), GREEN)
    ax.text(.50, .31, "若物理规则满足：合法替代路径 0 → 2", ha="center", color=GREEN, fontsize=6.1)
    ax.text(.5, .16, "路径与任务支持重构", ha="center", fontsize=7)
    ax.text(.5, .82, "故障窗口内", ha="center", color=RED, fontsize=7)

    ax = axes[3]
    box(ax, (.10, .62, .80, .16), "典型 F0：起始 44；持续 80 步", "#fee2e2", fontsize=6.5)
    box(ax, (.10, .38, .80, .16), "训练组：N + F0 / TE / TL\n/ DS / DL / CP", "#eff6ff", fontsize=6.2)
    box(ax, (.10, .14, .80, .16), "禁止：故障标签、最短路\n未来链路、仿真器真值", "#f3f4f6", fontsize=6.2)
    fig.suptitle("中继节点故障引起合法通信—任务路径重构的问题定义", y=1.03, fontsize=10, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig1_relay_failure_topology_reconfiguration")


def fig2() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.25))
    titles = ["(a) 共同策略与训练组", "(b) UTR：均匀故障暴露", "(c) DRTP：有界自适应加权", "(d) 公平比较的隔离变量"]
    for ax, title in zip(axes, titles):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.set_title(title, fontweight="bold", fontsize=8)

    ax = axes[0]
    box(ax, (.13, .65, .74, .16), "同一单图 SG actor + CTDE critic\n116,728 参数；同一 PPO", "#eff6ff")
    box(ax, (.13, .40, .74, .16), "50% 正常工况锚点 N", "#ecfdf5")
    box(ax, (.13, .15, .74, .16), "50% 故障：F0、TE、TL、DS、DL、CP", "#fff7ed")

    ax = axes[1]
    box(ax, (.15, .69, .70, .15), "N：固定 0.50", "#ecfdf5")
    box(ax, (.15, .45, .70, .15), "故障质量：0.50", "#fff7ed")
    box(ax, (.15, .18, .70, .17), "六组均匀：q=1/6\n每组总概率=1/12", "#eff6ff")

    ax = axes[2]
    box(ax, (.12, .74, .76, .13), "N：固定 0.50", "#ecfdf5")
    box(ax, (.12, .53, .76, .13), "组回报 → EMA → 相对难度", "#f5f3ff")
    box(ax, (.12, .31, .76, .13), "指数更新 + 平滑 + 有界单纯形投影", "#f5f3ff")
    box(ax, (.12, .09, .76, .13), "q(k) ∈ [0.05, 0.35]；仅训练期使用", "#fff7ed")
    arrow(ax, (.50, .52), (.50, .45), PURPLE)
    arrow(ax, (.50, .30), (.50, .23), PURPLE)

    ax = axes[3]
    box(ax, (.10, .69, .80, .15), "相同：网络、PPO、奖励、环境\n训练组、正常锚点、预算、样本带", "#f3f4f6", fontsize=6.4)
    box(ax, (.10, .43, .80, .15), "唯一差异：UTR 固定均匀 q\nDRTP 更新有界 q", "#dbeafe", fontsize=6.8)
    box(ax, (.10, .17, .80, .15), "执行期相同：无新增参数、输入\n和自适应采样器", "#fefce8", fontsize=6.5)
    fig.suptitle("UTR 与 DRTP 的训练分布差异及公平比较合同", y=1.03, fontsize=10, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig2_utr_drtp_training_distribution")


def main() -> None:
    setup(); fig1(); fig2()
    print(f"PASS: concept figures written to {OUT}")


if __name__ == "__main__":
    main()
