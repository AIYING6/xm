"""Build reproducible, evidence-bounded figures for the DRTP Chinese manuscript.

This script deliberately reads only the final A/B archives, the held-out
structural archive and the PLR-style archive enumerated in the manuscript
evidence register.  It never reads historical development cohorts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOWNLOADS = Path(r"D:\File\Downloads")
FIG_DIR = ROOT / "paper" / "q2_final_zh" / "final_figures"
SOURCE_DIR = ROOT / "docs" / "drtp_submission_ready" / "figure_source_data"

UTR = "#7B879B"
DRTP = "#147C80"
PLR = "#D98928"
GROUP_COLORS = ["#147C80", "#4D8CC9", "#D98928", "#8B6BAE", "#C75D6C", "#5E9C76"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_from_tar(archive: Path, predicate) -> pd.DataFrame:
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
        matches = [name for name in names if predicate(name)]
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one CSV in {archive.name}; got {matches}")
        content = tar.extractfile(matches[0]).read().decode("utf-8-sig")
    return pd.read_csv(io.StringIO(content))


def final_endpoint(archive: Path) -> pd.DataFrame:
    data = csv_from_tar(
        archive,
        lambda name: name.endswith("CONFIRMATION_PER_SEED_ENDPOINTS.csv")
        and "reaggregation_repair_v1" in name,
    )
    return data[data["method"].isin(["utr_sg", "drtp_sg"])].copy()


def q_log_rows(archive: Path, cohort: str) -> pd.DataFrame:
    """Read actual reset-selection rows nearest the frozen training milestones."""
    records = []
    found = 0
    milestones = (0, 3907, 11719, 39063)
    # Streaming mode avoids repeated seeks through the large gzip archive.
    with tarfile.open(archive, "r|gz") as tar:
        for member in tar:
            name = member.name
            if not ("/runs/drtp_sg/seed" in name and name.endswith("drtp_topology_sampler_log.csv")):
                continue
            found += 1
            seed = int(name.split("/seed", 1)[1].split("/", 1)[0])
            # Stream wrappers in tarfile's ``r|gz`` mode are not seekable; decoding the
            # current member preserves one-pass archive traversal while keeping parsing portable.
            reader = csv.DictReader(io.StringIO(tar.extractfile(member).read().decode("utf-8-sig")))
            selected: dict[int, dict] = {}
            for row in reader:
                if row["record_type"] != "selection" or row["env_index"] != "0":
                    continue
                update = int(row["update"])
                if not any(update <= milestone for milestone in milestones):
                    continue
                values = {f"q_{group}": row[f"q_{group}"] for group in ("F0", "TE", "TL", "DS", "DL", "CP")}
                if any(value in ("", None) for value in values.values()):
                    continue
                for milestone in milestones:
                    old = selected.get(milestone)
                    if update <= milestone and (old is None or update >= old["selected_at_update"]):
                        selected[milestone] = {"selected_at_update": update, **values}
            for milestone, values in selected.items():
                records.append(
                    {
                        "cohort": cohort,
                        "train_seed": seed,
                        "update": milestone,
                        **{key: float(value) for key, value in values.items()},
                    }
                )
    if found != 5:
        raise RuntimeError(f"Expected five DRTP sampler logs in {archive.name}, got {found}")
    return pd.DataFrame(records)


def configure() -> None:
    mpl.rcParams.update(
        {
            "font.family": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 9,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def export(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG_DIR / f"{stem}.tiff", dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.12, 1.05, label, transform=ax.transAxes, fontweight="bold", fontsize=9, va="top")


def plot_paired(ax: plt.Axes, data: pd.DataFrame, metric: str, title: str) -> None:
    piv = data.pivot(index="train_seed", columns="method", values=metric).sort_index()
    for _, row in piv.iterrows():
        ax.plot([0, 1], [row["utr_sg"], row["drtp_sg"]], color="#B8C0CC", lw=0.8, zorder=1)
    for x, method, color, label in [(0, "utr_sg", UTR, "UTR"), (1, "drtp_sg", DRTP, "DRTP")]:
        # Fixed offsets separate seed points visually; they do not alter values.
        jitter = np.linspace(-0.035, 0.035, len(piv))
        ax.scatter(np.full(len(piv), x) + jitter, piv[method], color=color, edgecolor="white", linewidth=0.5, s=29, zorder=3)
        ax.hlines(piv[method].mean(), x - 0.18, x + 0.18, color=color, lw=2.1, zorder=4)
        ax.text(x, piv[method].mean() + 7, f"{piv[method].mean():.1f}", ha="center", color=color, fontsize=7)
    ax.set_xticks([0, 1], ["UTR", "DRTP"])
    ax.set_xlim(-0.42, 1.42)
    ax.set_title(title)
    ax.set_ylabel("扰动条件回报 J")
    ax.grid(axis="y", color="#E5E7EB", lw=0.6)


def figure_main(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True, constrained_layout=True)
    for ax, cohort, panel in zip(axes, ("A", "B"), ("a", "b")):
        plot_paired(ax, data[data["cohort"] == cohort], "J_perturbed", f"Cohort {cohort}")
        add_panel_label(ax, panel)
    fig.suptitle("最终冻结 10M endpoint：UTR 与 DRTP 的同种子配对比较", y=1.02, fontweight="bold")
    export(fig, "Fig4_final_ab_paired_endpoint")


def figure_structural(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.1), sharey="row", constrained_layout=True)
    metrics = [("structural_J_mean", "结构条件平均回报"), ("structural_J_worst", "结构条件最差回报")]
    for row_index, (metric, label) in enumerate(metrics):
        for col_index, cohort in enumerate(("A", "B")):
            ax = axes[row_index, col_index]
            plot_paired(ax, data[data["cohort"] == cohort], metric, f"Cohort {cohort}" if row_index == 0 else "")
            ax.set_ylabel(label)
            if row_index == 0:
                ax.set_xlabel("")
            add_panel_label(ax, chr(ord("a") + row_index * 2 + col_index))
    fig.suptitle("训练未读取的 structural 条件带：固定 endpoint 配对结果", y=1.02, fontweight="bold")
    export(fig, "Fig5_heldout_structural_endpoint")


def figure_plr(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True, constrained_layout=True)
    methods = [("utr_sg", "UTR", UTR), ("drtp_sg", "DRTP", DRTP), ("plr_style_sg", "PLR-style", PLR)]
    for ax, cohort, panel in zip(axes, ("A", "B"), ("a", "b")):
        subset = data[data["cohort"] == cohort]
        for x, (method, label, color) in enumerate(methods):
            values = subset[subset["method"] == method]["J_perturbed"].to_numpy()
            # Fixed offsets separate points visually; no synthetic observations are added.
            ax.scatter(x + np.linspace(-0.04, 0.04, len(values)), values, color=color, edgecolor="white", linewidth=0.5, s=28, zorder=3)
            ax.hlines(values.mean(), x - 0.20, x + 0.20, color=color, lw=2.2, zorder=4)
            ax.text(x, values.mean() + 7, f"{values.mean():.1f}", ha="center", color=color, fontsize=7)
        ax.set_xticks(range(3), [item[1] for item in methods])
        ax.set_title(f"Cohort {cohort}")
        ax.set_ylabel("扰动条件回报 J")
        ax.grid(axis="y", color="#E5E7EB", lw=0.6)
        add_panel_label(ax, panel)
    fig.suptitle("PLR-style 外部定位：A/B 分层的 endpoint 回报", y=1.02, fontweight="bold")
    export(fig, "Fig6_plr_style_positioning")


def q_milestones(q_data: pd.DataFrame) -> pd.DataFrame:
    if q_data.empty:
        raise RuntimeError("No reset-selection records found in final DRTP sampler logs")
    expected = 2 * 5 * 4
    if len(q_data) != expected:
        raise RuntimeError(f"Expected {expected} sampler milestone records, got {len(q_data)}")
    return q_data.copy()


def figure_q(q_data: pd.DataFrame) -> None:
    sampled = q_milestones(q_data)
    sampled.to_csv(SOURCE_DIR / "Fig3_q_evolution_milestones.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True, constrained_layout=True)
    groups = ("F0", "TE", "TL", "DS", "DL", "CP")
    labels = ("F0", "TE", "TL", "DS", "DL", "CP")
    for ax, cohort, panel in zip(axes, ("A", "B"), ("a", "b")):
        subset = sampled[sampled["cohort"] == cohort]
        for group, label, color in zip(groups, labels, GROUP_COLORS):
            field = f"q_{group}"
            stats = subset.groupby("update")[field].agg(["mean", "min", "max"]).reindex([0, 3907, 11719, 39063])
            x = stats.index.to_numpy() / 39063.0
            ax.plot(x, stats["mean"], marker="o", ms=3, lw=1.5, color=color, label=label)
            ax.fill_between(x, stats["min"], stats["max"], color=color, alpha=0.10, linewidth=0)
        ax.axhline(1 / 6, color="#9CA3AF", lw=1, ls="--", label="UTR 均匀质量" if cohort == "A" else None)
        ax.set_title(f"Cohort {cohort}")
        ax.set_xlabel("训练进度（占 10M budget 的比例）")
        ax.set_ylabel("故障组质量 q")
        ax.set_ylim(0.0, 0.42)
        ax.grid(axis="y", color="#E5E7EB", lw=0.6)
        add_panel_label(ax, panel)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.13), frameon=False)
    fig.suptitle("DRTP 训练日志：故障组暴露质量的实际演化", y=1.02, fontweight="bold")
    export(fig, "Fig3_drtp_q_evolution")


def write_metadata(archives: dict[str, Path]) -> None:
    metadata = {
        "backend": "Python/matplotlib",
        "independent_unit": "training_seed",
        "figures": {
            "Fig3": "DRTP sampler q telemetry; implementation evidence only",
            "Fig4": "final A/B UTR--DRTP primary paired comparison",
            "Fig5": "predeclared held-out structural condition band",
            "Fig6": "PLR-style external positioning; not the primary causal comparison",
        },
        "archives": {key: {"path": str(path), "sha256": sha256(path)} for key, path in archives.items()},
    }
    (SOURCE_DIR / "figure_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads-dir", type=Path, default=DEFAULT_DOWNLOADS)
    args = parser.parse_args()
    downloads = args.downloads_dir
    archives = {
        "A": downloads / "drtp_stabilization_A_complete_results.tar.gz",
        "B": downloads / "drtp_stabilization_B_complete_results.tar.gz",
        "heldout": downloads / "drtp_final_evidence_heldout_ood_results.tar.gz",
        "plr": downloads / "drtp_plr_matched_ab_results.tar.gz",
    }
    missing = [str(path) for path in archives.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required final-evidence archives: " + ", ".join(missing))

    configure()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    primary = pd.concat(
        [final_endpoint(archives["A"]).assign(cohort="A"), final_endpoint(archives["B"]).assign(cohort="B")],
        ignore_index=True,
    )
    primary.to_csv(SOURCE_DIR / "Fig4_final_ab_paired_endpoint.csv", index=False)

    heldout = csv_from_tar(archives["heldout"], lambda name: name.endswith("DRTP_FINAL_EVIDENCE_PER_SEED_ENDPOINTS.csv"))
    heldout = heldout[heldout["method"].isin(["utr_sg", "drtp_sg"])].copy()
    heldout.to_csv(SOURCE_DIR / "Fig5_heldout_structural_endpoint.csv", index=False)

    plr = csv_from_tar(archives["plr"], lambda name: name.endswith("PLR_MATCHED_AB_PER_SEED_ENDPOINTS.csv"))
    plr = plr[plr["method"].isin(["utr_sg", "drtp_sg", "plr_style_sg"])].copy()
    plr.to_csv(SOURCE_DIR / "Fig6_plr_style_positioning.csv", index=False)

    q = pd.concat([q_log_rows(archives["A"], "A"), q_log_rows(archives["B"], "B")], ignore_index=True)

    figure_q(q)
    figure_main(primary)
    figure_structural(heldout)
    figure_plr(plr)
    write_metadata(archives)


if __name__ == "__main__":
    main()
