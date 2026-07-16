from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]


def box(ax, xy, w, h, text, fc="#f8fbff", ec="#2f4f6f", fontsize=9, lw=1.4):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize)
    return patch


def arrow(ax, start, end, color="#394b59", lw=1.4, rad=0.0):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(patch)
    return patch


def main() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # Inputs
    box(ax, (0.45, 5.45), 2.1, 0.75, "Local observation\n$o_i^t$", fc="#eef7ff")
    box(ax, (0.45, 4.35), 2.1, 0.75, "Global state\n$s^t$ (training only)", fc="#f1f8ec")
    box(ax, (0.45, 2.85), 2.1, 0.95, "Dynamic role graph\nUAV nodes + target node\nrole embedding", fc="#fff7e8")
    box(ax, (0.45, 1.55), 2.1, 0.95, "Relative edge features\nrange, bearing, rel. velocity,\ncomm. reachable", fc="#fff1f1")

    # Encoders
    box(ax, (3.15, 5.45), 2.0, 0.75, "Observation\nencoder", fc="#eef7ff")
    box(ax, (3.15, 2.2), 2.25, 1.25, "Edge-aware role\nattention encoder\n$\\alpha_{ij}=softmax(score_{ij})$", fc="#fff7e8")
    box(ax, (3.15, 4.35), 2.0, 0.75, "Centralized\ncritic $V_\\phi(s)$", fc="#f1f8ec")

    # Fusion and policy
    box(ax, (6.05, 4.75), 2.15, 1.05, "Feature fusion\n$[z_i, g_i, c]$", fc="#f6f0ff")
    box(ax, (8.8, 4.75), 2.1, 1.05, "Actor head\n$\\pi_\\theta(a_i|o_i,G)$", fc="#eef7ff")
    box(ax, (8.8, 3.25), 2.1, 0.85, "MAPPO clipped\nobjective", fc="#f5f5f5")
    box(ax, (6.05, 3.15), 2.15, 0.95, "Optional auxiliary\nintent branch\n(not main claim)", fc="#eeeeee", ec="#777777")

    # Staged training
    box(ax, (3.0, 0.25), 2.5, 0.8, "Stage 1\nfixed radius $R_c=8$", fc="#eaf7ef")
    box(ax, (6.05, 0.25), 2.7, 0.8, "Stage 2\nrandom radius $R_c\\sim U(4,10)$", fc="#eaf7ef")
    box(ax, (9.25, 0.25), 2.25, 0.8, "EA-RG-MAPPO-S\nrobust policy", fc="#eaf7ef")

    # Arrows
    arrow(ax, (2.55, 5.83), (3.15, 5.83))
    arrow(ax, (2.55, 4.73), (3.15, 4.73))
    arrow(ax, (2.55, 3.3), (3.15, 3.0))
    arrow(ax, (2.55, 2.0), (3.15, 2.55))
    arrow(ax, (5.15, 5.83), (6.05, 5.35))
    arrow(ax, (5.4, 2.85), (6.05, 5.0), rad=0.12)
    arrow(ax, (8.2, 5.28), (8.8, 5.28))
    arrow(ax, (9.85, 4.75), (9.85, 4.1))
    arrow(ax, (8.8, 3.65), (8.2, 3.65))
    arrow(ax, (5.15, 4.73), (8.8, 3.65), rad=-0.15)
    arrow(ax, (7.15, 4.1), (7.15, 4.75))
    arrow(ax, (5.5, 0.65), (6.05, 0.65))
    arrow(ax, (8.75, 0.65), (9.25, 0.65))

    ax.text(
        6.0,
        6.55,
        "EA-RG-MAPPO-S: Edge-Aware Role Graph MAPPO with Staged Random-Radius Fine-Tuning",
        ha="center",
        va="center",
        fontsize=13,
        weight="bold",
    )
    ax.text(
        7.0,
        2.35,
        "Edge score: node-pair attention + physical edge relation",
        ha="center",
        va="center",
        fontsize=9,
        color="#4a4a4a",
    )
    ax.text(
        7.3,
        1.45,
        "Main claim: limited-communication stability and collision reduction\nIntent branch is diagnostic/auxiliary until balanced accuracy is fixed",
        ha="center",
        va="center",
        fontsize=9,
        color="#4a4a4a",
    )

    out = ROOT / "results" / "figures" / "method_overview_ea_rg_mappo_s.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
