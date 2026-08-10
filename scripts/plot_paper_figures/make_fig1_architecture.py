"""Draw Fig. 1 for the frozen v1.9 PCRF-R2 protocol.

Scientific terms are taken from the v1.9 PCRF-R2 theory/protocol freeze and
the F1 formal-training protocol.  This is a conceptual protocol figure, not a
performance figure: it contains no experimental values or F2 data.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle


COLORS = {
    "scout": "#2166AC",
    "relay": "#3C8D40",
    "attacker": "#C93F3F",
    "target": "#7B4AA8",
    "perception": "#2F6FB3",
    "communication": "#3E8B4A",
    "ink": "#252525",
    "muted": "#707070",
    "panel": "#FAFBFC",
    "border": "#404040",
    "critic": "#F2E7FB",
    "actor": "#EAF3FC",
    "warning": "#FDE9E7",
}

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8,
        "axes.linewidth": 0.7,
    }
)


def box(ax, x, y, w, h, text, *, fc="white", ec="#555555", fs=7.5, lw=0.8, radius=0.025, weight="normal"):
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.010,rounding_size={radius}",
                           facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=COLORS["ink"], weight=weight)
    return patch


def arrow(ax, start, end, *, color=COLORS["ink"], style="-", lw=1.2, mutation=10, alpha=1.0, connection="arc3"):
    patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=mutation, linewidth=lw,
                            linestyle=style, color=color, alpha=alpha, connectionstyle=connection)
    ax.add_patch(patch)
    return patch


def drone(ax, x, y, color, label, *, scale=0.045, failed=False):
    """A compact vector aircraft mark; no external artwork is used."""
    body = Polygon([(x - 1.3 * scale, y), (x - 0.25 * scale, y + 0.30 * scale),
                    (x + 1.45 * scale, y), (x - 0.25 * scale, y - 0.30 * scale)],
                   closed=True, facecolor=color, edgecolor="white", linewidth=0.6, zorder=4)
    wing = Polygon([(x - 0.40 * scale, y), (x - 0.95 * scale, y + 0.85 * scale),
                    (x + 0.40 * scale, y + 0.20 * scale), (x + 0.65 * scale, y)],
                   closed=True, facecolor=color, edgecolor="white", linewidth=0.5, zorder=3)
    wing2 = Polygon([(x - 0.40 * scale, y), (x - 0.95 * scale, y - 0.85 * scale),
                     (x + 0.40 * scale, y - 0.20 * scale), (x + 0.65 * scale, y)],
                    closed=True, facecolor=color, edgecolor="white", linewidth=0.5, zorder=3)
    ax.add_patch(wing); ax.add_patch(wing2); ax.add_patch(body)
    ax.text(x, y - 1.55 * scale, label, ha="center", va="top", fontsize=8, color=color, weight="bold")
    if failed:
        ax.add_patch(Circle((x, y), 1.50 * scale, fill=False, edgecolor="#D62728", linewidth=1.3, linestyle="--", zorder=8))
        ax.plot([x - .6 * scale, x + .6 * scale], [y - .6 * scale, y + .6 * scale], color="#D62728", lw=2.0, zorder=9)
        ax.plot([x - .6 * scale, x + .6 * scale], [y + .6 * scale, y - .6 * scale], color="#D62728", lw=2.0, zorder=9)


def target(ax, x, y, *, scale=0.047, label="Target (T)"):
    ax.add_patch(Circle((x, y), scale, facecolor="#F4EFFA", edgecolor=COLORS["target"], linewidth=1.5, zorder=4))
    ax.add_patch(Circle((x, y), scale * .55, fill=False, edgecolor=COLORS["target"], linewidth=1.0, zorder=5))
    ax.plot([x - scale * 1.25, x + scale * 1.25], [y, y], color=COLORS["target"], lw=0.8)
    ax.plot([x, x], [y - scale * 1.25, y + scale * 1.25], color=COLORS["target"], lw=0.8)
    ax.text(x, y - 1.55 * scale, label, ha="center", va="top", fontsize=8, color=COLORS["target"], weight="bold")


def panel_title(ax, letter, title):
    ax.text(0.015, 0.967, f"({letter})", transform=ax.transAxes, ha="left", va="top", fontsize=13, weight="bold")
    ax.text(0.085, 0.967, title, transform=ax.transAxes, ha="left", va="top", fontsize=10.5, weight="bold")


def init_panel(ax, letter, title):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=COLORS["panel"], edgecolor=COLORS["border"], linewidth=.75))
    panel_title(ax, letter, title)


def draw_a(ax):
    init_panel(ax, "a", "Heterogeneous task scenario")
    drone(ax, .20, .68, COLORS["scout"], "Scout (S)")
    drone(ax, .55, .72, COLORS["relay"], "Relay (R)")
    drone(ax, .28, .28, COLORS["attacker"], "Attacker (A)")
    target(ax, .74, .30)
    arrow(ax, (.23, .68), (.70, .32), color=COLORS["perception"], style=":", lw=1.6)
    box(ax, .36, .48, .105, .075, "P: direct\nperception", fc="#F8FBFF", ec="none", fs=6.5, lw=0, radius=.01)
    arrow(ax, (.25, .66), (.51, .71), color=COLORS["communication"], style="--", lw=1.4)
    arrow(ax, (.55, .66), (.31, .31), color=COLORS["communication"], style="--", lw=1.4)
    ax.text(.50, .43, "C: delivered / cache-valid\ncommunication evidence", color=COLORS["communication"], fontsize=7, ha="center")
    box(ax, .73, .58, .22, .19, "Two legal sources\nP  direct local sensing\nC  delivered + cache-valid", fc="white", ec="#777777", fs=6.5)
    ax.text(.06, .10, "Recipient-specific information only", fontsize=7.1, color=COLORS["muted"], weight="bold")


def mini_chain(ax, x0, y0, w, disrupted=False):
    names = [("S", COLORS["scout"]), ("R", COLORS["relay"]), ("A", COLORS["attacker"]), ("T", COLORS["target"])]
    xs = [x0 + w * value for value in (.10, .37, .64, .90)]
    for index, ((name, color), x) in enumerate(zip(names, xs)):
        if disrupted and name == "R":
            ax.add_patch(Circle((x, y0), .043, fill=False, edgecolor="#AAAAAA", linestyle="--", linewidth=1.1))
        else:
            ax.add_patch(Circle((x, y0), .043, facecolor="#FFFFFF", edgecolor=color, linewidth=1.2))
            ax.text(x, y0, name, color=color, ha="center", va="center", fontsize=7.5, weight="bold")
    for start, end in zip(xs[:-1], xs[1:]):
        color = COLORS["ink"] if not disrupted or start > xs[1] else "#A9A9A9"
        alpha = 1.0 if not disrupted or start > xs[1] else .55
        arrow(ax, (start + .045, y0), (end - .045, y0), color=color, lw=1.0, alpha=alpha)
    if disrupted:
        ax.text((xs[1] + xs[2]) / 2, y0 + .075, "C unavailable", color="#D62728", fontsize=6.5, ha="center")


def draw_b(ax):
    init_panel(ax, "b", "Relay failure disrupts delivered communication")
    ax.text(.23, .86, "Before failure", ha="center", fontsize=8.5, weight="bold")
    ax.text(.76, .86, "After relay failure", ha="center", fontsize=8.5, weight="bold")
    for x in (.04, .54): ax.add_patch(Rectangle((x, .36), .42, .43, facecolor="white", edgecolor="#9A9A9A", linewidth=.65))
    # normal
    drone(ax, .13, .66, COLORS["scout"], "S", scale=.028); drone(ax, .29, .68, COLORS["relay"], "R", scale=.028)
    drone(ax, .14, .47, COLORS["attacker"], "A", scale=.028); target(ax, .38, .47, scale=.028, label="T")
    arrow(ax, (.15, .64), (.28, .67), color=COLORS["communication"], style="--", lw=1.1)
    arrow(ax, (.28, .65), (.15, .49), color=COLORS["communication"], style="--", lw=1.1)
    arrow(ax, (.13, .64), (.37, .49), color=COLORS["perception"], style=":", lw=1.2)
    mini_chain(ax, .05, .22, .40)
    ax.text(.25, .10, "P and C available", ha="center", fontsize=7, color=COLORS["muted"])
    # disrupted
    drone(ax, .63, .66, COLORS["scout"], "S", scale=.028); drone(ax, .79, .68, COLORS["relay"], "R", scale=.028, failed=True)
    drone(ax, .64, .47, COLORS["attacker"], "A", scale=.028); target(ax, .88, .47, scale=.028, label="T")
    arrow(ax, (.65, .64), (.78, .67), color=COLORS["communication"], style="--", lw=1.1, alpha=.27)
    arrow(ax, (.78, .65), (.65, .49), color=COLORS["communication"], style="--", lw=1.1, alpha=.27)
    arrow(ax, (.63, .64), (.87, .49), color=COLORS["perception"], style=":", lw=1.2)
    mini_chain(ax, .55, .22, .40, disrupted=True)
    box(ax, .58, .055, .35, .10, "Failure changes C availability;\nP may remain locally available", fc=COLORS["warning"], ec="#D97D76", fs=6.7)


def node_pair(ax, x, y, p=True, c=True):
    ax.add_patch(Circle((x, y), .025, facecolor="#E8F1FC", edgecolor=COLORS["scout"], lw=1.0))
    ax.add_patch(Circle((x + .12, y), .025, facecolor="#F4EFFA", edgecolor=COLORS["target"], lw=1.0))
    if p: arrow(ax, (x + .028, y + .005), (x + .088, y + .005), color=COLORS["perception"], style=":", lw=1.1, mutation=7)
    if c: arrow(ax, (x + .025, y - .025), (x + .09, y - .025), color=COLORS["communication"], style="--", lw=1.0, mutation=7, connection="arc3,rad=-.35")


def draw_c(ax):
    init_panel(ax, "c", "Overall pipeline: CTDE with recipient-specific execution")
    ax.text(.05, .84, "Execution (decentralized)", fontsize=8.5, weight="bold")
    box(ax, .05, .60, .19, .15, "Recipient i\nself state + local context", fc="white", fs=7.0)
    box(ax, .05, .42, .19, .13, "P: direct local\nperception claim", fc="#F1F6FC", ec=COLORS["perception"], fs=7)
    box(ax, .05, .25, .19, .13, "C: delivered +\ncache-valid packet\nage / confidence", fc="#F1F8F1", ec=COLORS["communication"], fs=6.7)
    arrow(ax, (.24, .68), (.31, .68)); arrow(ax, (.24, .48), (.31, .55)); arrow(ax, (.24, .31), (.31, .43))
    box(ax, .32, .40, .18, .30, "P/C source\nconstruction\n\nlegal masks +\nedge geometry", fc="#FFFFFF", fs=7.3)
    node_pair(ax, .35, .49)
    arrow(ax, (.50, .55), (.58, .55))
    box(ax, .59, .42, .16, .26, "PCRF-R2\nencoder +\nsource-preserving\nfusion", fc=COLORS["actor"], ec="#4E83B9", fs=7.2, weight="bold")
    arrow(ax, (.75, .55), (.81, .55))
    box(ax, .82, .44, .10, .22, "Actor\npolicy\n$\\pi_i$", fc="#EAF3FC", ec="#4E83B9", fs=7.6, weight="bold")
    arrow(ax, (.92, .61), (.95, .74), mutation=7); ax.text(.945, .68, "action", fontsize=5.8, ha="center")
    box(ax, .89, .76, .09, .10, "3DOF\nenvironment", fc="#F7F7F7", ec="#777777", fs=5.8)
    arrow(ax, (.89, .80), (.24, .74), color="#777777", style="--", lw=.7, mutation=6, connection="arc3,rad=.12")
    ax.text(.55, .80, "next recipient-specific P/C", fontsize=5.9, color=COLORS["muted"], ha="center")
    ax.plot([.03, .97], [.18, .18], color="#6C4AA1", lw=1.0, linestyle="--")
    ax.text(.50, .195, "CTDE boundary", fontsize=7.2, color="#6C4AA1", ha="center", va="bottom", weight="bold")
    ax.text(.05, .10, "Training only", fontsize=8, weight="bold", color="#6C4AA1")
    box(ax, .19, .025, .24, .11, "Centralized state\n(shared critic input only)", fc=COLORS["critic"], ec="#9363B8", fs=6.8)
    box(ax, .53, .025, .20, .11, "Centralized critic\n$V_\\phi(s_t)$", fc=COLORS["critic"], ec="#9363B8", fs=7.1, weight="bold")
    arrow(ax, (.43, .08), (.53, .08), color="#6C4AA1")
    ax.text(.80, .08, "critic-only state\nnever enters actor", fontsize=6.5, color="#6C4AA1", va="center")


def draw_d(ax):
    init_panel(ax, "d", "PCRF-R2 encoder and source-preserving fusion")
    box(ax, .04, .64, .20, .19, "P source\ndirect local target claim\navailability + quality", fc="#F1F6FC", ec=COLORS["perception"], fs=7.0)
    box(ax, .04, .37, .20, .19, "C source\ndelivered + cache-valid\npacket, age, confidence", fc="#F1F8F1", ec=COLORS["communication"], fs=6.8)
    arrow(ax, (.24, .735), (.32, .735), color=COLORS["perception"])
    arrow(ax, (.24, .465), (.32, .465), color=COLORS["communication"])
    box(ax, .33, .65, .17, .17, "P encoder\n$F_P(G_i^P)$", fc="#F4F8FC", ec=COLORS["perception"], fs=7.6, weight="bold")
    box(ax, .33, .38, .17, .17, "C encoder\n$F_C(G_i^C)$", fc="#F4F9F3", ec=COLORS["communication"], fs=7.6, weight="bold")
    arrow(ax, (.50, .735), (.58, .67), color=COLORS["perception"])
    arrow(ax, (.50, .465), (.58, .61), color=COLORS["communication"])
    box(ax, .59, .60, .20, .19, "Source-preserving fusion\n$\\beta + \\Delta(c)-\\Delta(0)$\nconflict-conditioned deviation\n$\\Delta(0)=0$", fc="#FFFDF6", ec="#B98732", fs=6.5, weight="bold")
    ax.text(.69, .51, "$c=[a^P-a^C, d_{PC}, age_C, 1-confidence_C]$", fontsize=5.8, ha="center", color="#6B5A32")
    arrow(ax, (.79, .695), (.86, .695), color="#B98732")
    box(ax, .87, .60, .10, .19, "availability-\nmasked\nweighted sum\n$h_i$", fc="#FFFDF6", ec="#B98732", fs=6.3)
    ax.text(.47, .22, "Two-source R2 only • no cross-source residual bypass", fontsize=7.0, color="#8A3434", ha="center", weight="bold")
    ax.text(.47, .12, "One legal source → unit weight; neither legal source → actor uses only local context", fontsize=6.8, color=COLORS["muted"], ha="center")


def draw_legend(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((.01, .12), .98, .76, boxstyle="round,pad=0.008,rounding_size=.018", facecolor="white", edgecolor="#555555", linewidth=.7))
    items = [("Scout", COLORS["scout"]), ("Relay", COLORS["relay"]), ("Attacker", COLORS["attacker"]), ("Target", COLORS["target"])]
    x = .05
    for label, color in items:
        ax.add_patch(FancyBboxPatch((x - .018, .505), .036, .09, boxstyle="round,pad=.002,rounding_size=.025", facecolor=color, edgecolor="white", lw=.5))
        ax.text(x + .028, .55, label, color=color, fontsize=7.3, va="center", weight="bold")
        x += .16
    ax.plot([.62, .68], [.55, .55], color=COLORS["perception"], lw=1.5, linestyle=":")
    ax.text(.69, .55, "P: direct perception", fontsize=7.3, va="center")
    ax.plot([.81, .87], [.55, .55], color=COLORS["communication"], lw=1.5, linestyle="--")
    ax.text(.88, .55, "C: delivered/cache-valid communication", fontsize=7.3, va="center")
    ax.add_patch(Circle((.42, .28), .022, fill=False, edgecolor="#D62728", lw=1.0, linestyle="--"))
    ax.text(.45, .28, "failed relay / unavailable C path", fontsize=7.0, va="center", color="#6B3333")


def make_figure(version: str):
    fig = plt.figure(figsize=(16.4, 10.6), facecolor="white")
    # V2 uses a tighter gap and larger lower panels for readable encoder labels.
    if version == "v1":
        top_y, bottom_y, h_top, h_bottom = .56, .15, .37, .35
    else:
        top_y, bottom_y, h_top, h_bottom = .55, .15, .39, .37
    axes = [
        fig.add_axes((.035, top_y, .47, h_top)), fig.add_axes((.505, top_y, .46, h_top)),
        fig.add_axes((.035, bottom_y, .58, h_bottom)), fig.add_axes((.615, bottom_y, .35, h_bottom)),
        fig.add_axes((.035, .035, .93, .085)),
    ]
    draw_a(axes[0]); draw_b(axes[1]); draw_c(axes[2]); draw_d(axes[3]); draw_legend(axes[4])
    fig.text(.035, .004, "Fig. 1 | PCRF-R2 architecture overview for recipient-specific UAV coordination under relay failure.",
             fontsize=9.5, weight="bold")
    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-prefix", type=Path, default=Path("paper_figures/fig1_architecture"))
    parser.add_argument("--version", choices=("v1", "v2"), default="v2")
    args = parser.parse_args()
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    figure = make_figure(args.version)
    figure.savefig(args.output_prefix.with_suffix(".svg"), bbox_inches="tight")
    figure.savefig(args.output_prefix.with_suffix(".pdf"), bbox_inches="tight")
    figure.savefig(args.output_prefix.with_suffix(".png"), dpi=600, bbox_inches="tight")
    plt.close(figure)
    print(f"FIG1_{args.version.upper()}_WRITTEN: {args.output_prefix}")


if __name__ == "__main__":
    main()
