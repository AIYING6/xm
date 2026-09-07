"""Create a submission-oriented, descriptive Figure 3 from final DRTP telemetry."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


GROUPS = ["F0", "TE", "TL", "DS", "DL", "CP"]
COLORS = {
    "F0": "#0072B2", "TE": "#D55E00", "TL": "#009E73",
    "DS": "#CC79A7", "DL": "#E69F00", "CP": "#56B4E9",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "font.family": ["Microsoft YaHei", "DejaVu Sans"],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "legend.fontsize": 7,
        "svg.fonttype": "none",
    })
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.65), gridspec_kw={"width_ratios": [1.05, 1.05, 1.15]})

    for axis, cohort in zip(axes[:2], ("A", "B")):
        frame = pd.read_csv(args.input_dir / f"DRTP_MECHANISM_{cohort}_Q_TRAJECTORY.csv")
        for group in GROUPS:
            summary = frame.groupby("milestone_fraction")[f"q_{group}"].agg(["mean", "min", "max"]).reset_index()
            x = summary["milestone_fraction"].to_numpy()
            axis.plot(x, summary["mean"], color=COLORS[group], lw=1.5, label=group)
            axis.fill_between(x, summary["min"], summary["max"], color=COLORS[group], alpha=0.10, linewidth=0)
        axis.axhline(1 / 6, color="#4D4D4D", lw=0.8, ls="--", label="uniform 1/6")
        axis.set_title(f"({cohort}) Cohort {cohort}: 非名义组采样概率 $q$")
        axis.set_xlabel("训练进度（归一化 update）")
        axis.set_ylabel("组条件概率")
        axis.set_xlim(0, 1)
        axis.set_ylim(0.05, 0.40)
        axis.set_xticks([0, .25, .5, .75, 1.0], ["0", "25%", "50%", "75%", "100%"])
        axis.grid(axis="y", color="#D9D9D9", lw=.5)
        for spine in ("top", "right"):
            axis.spines[spine].set_visible(False)

    axes[0].legend(loc="upper left", ncol=2, frameon=False, handlelength=1.6)
    combined = []
    for cohort, marker in (("A", "o"), ("B", "s")):
        frame = pd.read_csv(args.input_dir / f"DRTP_MECHANISM_{cohort}_GROUP_ENDPOINTS.csv")
        for seed, seed_frame in frame.groupby("train_seed"):
            axes[2].scatter(
                seed_frame["final_logged_difficulty"], seed_frame["actual_non_nominal_exposure_share"],
                c=[COLORS[group] for group in seed_frame["group"]], marker=marker, s=19,
                edgecolors="white", linewidths=.35, alpha=.9, zorder=2,
            )
        combined.append(frame)
    axes[2].set_title("(C) 记录难度与实际故障组暴露")
    axes[2].set_xlabel("最终记录的名义相对困难度")
    axes[2].set_ylabel("实际非名义组暴露占比")
    axes[2].grid(color="#D9D9D9", lw=.5)
    for spine in ("top", "right"):
        axes[2].spines[spine].set_visible(False)
    axes[2].scatter([], [], c="#4D4D4D", marker="o", s=19, label="A seed")
    axes[2].scatter([], [], c="#4D4D4D", marker="s", s=19, label="B seed")
    axes[2].legend(loc="upper left", frameon=False)

    fig.text(
        .5, -.03,
        "阴影为同一 cohort 内五个训练 seed 的范围。图展示冻结训练 telemetry 的描述性过程；不构成策略内部因果证明。",
        ha="center", va="top", fontsize=7, color="#404040",
    )
    fig.subplots_adjust(left=.075, right=.99, top=.88, bottom=.24, wspace=.40)
    stem = args.output_dir / "Fig3_DRTP_topology_exposure_evolution"
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"}, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=250, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
