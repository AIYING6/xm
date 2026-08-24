"""Build no-training evidence enhancements for the Chinese DRTP manuscript.

The script consumes only frozen final-10M logs and the completed formal paired
evaluation archive. It never evaluates a checkpoint, selects a milestone, or
changes an experimental record. Its purpose is to make terminal outcomes and
training diagnostics traceable in the manuscript.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "formal" / "drtp_utr_q2_paired_5seed_cloud_10way"
PAPER = ROOT / "paper" / "q2_final_zh"
FIGURES = PAPER / "formal_results" / "figures"
SOURCE_DATA = PAPER / "formal_results" / "source_data"
SEEDS = (2301, 2302, 2303, 2304, 2305)
ARMS = ("utr_sg", "drtp_sg")
COLORS = {"utr_sg": "#484878", "drtp_sg": "#E53935"}
DISPLAY = {"utr_sg": "UTR-SG-MAPPO", "drtp_sg": "DRTP-SG-MAPPO"}
FAMILIES = {
    "正常工况": ("nominal",),
    "F0": ("f0_seen_44_80",),
    "时机 OOD": ("timing_28_80", "timing_36_80", "timing_52_80", "timing_60_80"),
    "持续时间 OOD": ("duration_44_40", "duration_44_60", "duration_44_100", "duration_44_120"),
    "复合 OOD": ("compound_28_120", "compound_60_120"),
}
METRICS = (
    ("success_at_horizon", "任务完成率", (0.0, 0.4)),
    ("timeout", "超时率", (0.0, 1.0)),
    ("collision", "碰撞率", (0.0, 0.045)),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def configure_style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Noto Sans CJK SC", "SimHei", "Arial", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.unicode_minus": False,
        "legend.frameon": False,
    })


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    base = FIGURES / stem
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    svg = base.with_suffix(".svg")
    svg.write_text(re.sub(r"[ \t]+(?=\r?\n)", "", svg.read_text(encoding="utf-8")), encoding="utf-8")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(base.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def formal_terminal_outcomes() -> list[dict[str, object]]:
    path = RESULTS / "evaluations" / "final_10m" / "raw_episode_metrics.csv"
    rows = read_csv(path)
    require(len(rows) == 12000, f"expected 12,000 formal rows, got {len(rows)}")
    require({row["method"] for row in rows} == set(ARMS), "method set mismatch")
    require({int(row["train_seed"]) for row in rows} == set(SEEDS), "formal seed set mismatch")
    require({row["topology_condition"] for row in rows} == {condition for values in FAMILIES.values() for condition in values},
            "formal condition set mismatch")
    by_cell: dict[tuple[str, int, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_cell[(row["method"], int(row["train_seed"]), row["topology_condition"])].append(row)
    output: list[dict[str, object]] = []
    for family, conditions in FAMILIES.items():
        for arm in ARMS:
            for seed in SEEDS:
                cell_rows = [record for condition in conditions for record in by_cell[(arm, seed, condition)]]
                require(cell_rows, f"empty formal outcome cell: {arm}/{seed}/{family}")
                output.append({
                    "method": arm,
                    "train_seed": seed,
                    "family": family,
                    "episodes": len(cell_rows),
                    **{metric: sum(float(record[metric]) for record in cell_rows) / len(cell_rows)
                       for metric, _, _ in METRICS},
                    "constraint_violation": sum(float(record["constraint_violation"]) for record in cell_rows) / len(cell_rows),
                    "terminal_step": sum(float(record["terminal_step"]) for record in cell_rows) / len(cell_rows),
                })
    return output


def write_terminal_source(rows: list[dict[str, object]]) -> None:
    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    path = SOURCE_DATA / "formal_terminal_outcomes_by_seed_family.csv"
    fields = ["method", "train_seed", "family", "episodes", "success_at_horizon", "timeout", "collision", "constraint_violation", "terminal_step"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot_terminal_outcomes(rows: list[dict[str, object]]) -> None:
    by_cell = {(row["method"], int(row["train_seed"]), row["family"]): row for row in rows}
    families = list(FAMILIES)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.35))
    offsets = {"utr_sg": -0.16, "drtp_sg": 0.16}
    for panel, (metric, title, ylim) in enumerate(METRICS):
        axis = axes[panel]
        x = np.arange(len(families))
        for family_index, family in enumerate(families):
            for seed in SEEDS:
                left = float(by_cell[("utr_sg", seed, family)][metric])
                right = float(by_cell[("drtp_sg", seed, family)][metric])
                axis.plot([family_index + offsets["utr_sg"], family_index + offsets["drtp_sg"]], [left, right],
                          color="#A8A8A8", linewidth=0.7, alpha=0.75, zorder=1)
                axis.scatter(family_index + offsets["utr_sg"], left, s=10, color=COLORS["utr_sg"], zorder=2)
                axis.scatter(family_index + offsets["drtp_sg"], right, s=10, color=COLORS["drtp_sg"], zorder=2)
            for arm in ARMS:
                values = [float(by_cell[(arm, seed, family)][metric]) for seed in SEEDS]
                axis.scatter(family_index + offsets[arm], np.mean(values), s=28, marker="D", color=COLORS[arm], zorder=3)
        axis.set_title(title, fontweight="bold")
        axis.set_xticks(x, families, rotation=28, ha="right")
        axis.set_ylim(*ylim)
        axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7)
        if panel == 0:
            axis.set_ylabel("样本比例")
            axis.scatter([], [], s=22, marker="D", color=COLORS["utr_sg"], label="UTR 均值（n=5）")
            axis.scatter([], [], s=22, marker="D", color=COLORS["drtp_sg"], label="DRTP 均值（n=5）")
            axis.legend(loc="upper left", fontsize=6.2)
        axis.text(-0.13, 1.04, chr(ord("a") + panel), transform=axis.transAxes, fontweight="bold", fontsize=10)
    fig.suptitle("正式五种子终止结局：成功、超时与碰撞", y=1.04, fontweight="bold", fontsize=10)
    fig.tight_layout()
    save_figure(fig, "fig7_formal_terminal_outcomes")


def binned_training_monitor() -> list[dict[str, object]]:
    bin_width = 500
    output: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            path = RESULTS / "runs" / arm / f"seed{seed}" / "train_log.csv"
            rows = read_csv(path)
            require(len(rows) == 39063, f"unexpected update count in {path}")
            buckets: dict[int, list[dict[str, str]]] = defaultdict(list)
            for row in rows:
                buckets[(int(row["update"]) - 1) // bin_width].append(row)
            for bucket, values in sorted(buckets.items()):
                output.append({
                    "method": arm,
                    "train_seed": seed,
                    "update_start": bucket * bin_width + 1,
                    "update_end": int(values[-1]["update"]),
                    "environment_steps_million": (bucket * bin_width + 1) * 256 / 1_000_000,
                    "train_avg_reward": float(np.mean([float(row["train_avg_reward"]) for row in values])),
                    "approx_kl": float(np.mean([float(row["approx_kl"]) for row in values])),
                    "clip_fraction": float(np.mean([float(row["clip_fraction"]) for row in values])),
                })
    return output


def write_monitor_source(rows: list[dict[str, object]]) -> None:
    path = SOURCE_DATA / "formal_training_monitor_binned.csv"
    fields = ["method", "train_seed", "update_start", "update_end", "environment_steps_million", "train_avg_reward", "approx_kl", "clip_fraction"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot_training_monitor(rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.3))
    grouped: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["method"]), int(row["train_seed"]))].append(row)
    for axis, metric, ylabel, label in (
        (axes[0], "train_avg_reward", "训练批次平均回报", "训练批次平均回报"),
        (axes[1], "approx_kl", "近似 KL", "PPO 近似 KL"),
    ):
        for arm in ARMS:
            all_values = []
            for seed in SEEDS:
                sequence = grouped[(arm, seed)]
                x = np.array([float(row["environment_steps_million"]) for row in sequence])
                y = np.array([float(row[metric]) for row in sequence])
                all_values.append(y)
                axis.plot(x, y, color=COLORS[arm], alpha=0.14, linewidth=0.55)
            values = np.vstack(all_values)
            axis.plot(x, values.mean(axis=0), color=COLORS[arm], linewidth=1.4, label=DISPLAY[arm])
            axis.fill_between(x, values.min(axis=0), values.max(axis=0), color=COLORS[arm], alpha=0.10)
        axis.set_title(label, fontweight="bold")
        axis.set_xlabel("训练环境步（百万）")
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7)
    axes[1].set_ylim(bottom=0)
    axes[0].legend(loc="lower right")
    axes[0].text(-0.11, 1.04, "a", transform=axes[0].transAxes, fontweight="bold", fontsize=10)
    axes[1].text(-0.11, 1.04, "b", transform=axes[1].transAxes, fontweight="bold", fontsize=10)
    fig.suptitle("训练期诊断（非最终性能比较，不用于检查点选择）", y=1.04, fontweight="bold", fontsize=10)
    fig.tight_layout()
    save_figure(fig, "figS1_training_diagnostics")


def write_report(terminal_rows: list[dict[str, object]], monitor_rows: list[dict[str, object]]) -> None:
    by = {(row["method"], row["family"]): [] for row in terminal_rows}
    for row in terminal_rows:
        by[(row["method"], row["family"])].append(row)
    lines = [
        "# 正式结果无训练证据补强审计", "",
        "## 执行边界", "",
        "本审计只读取正式五种子共同 10M 最终检查点的既有日志和 12,000 条原始评估记录；未启动训练、未重新运行评估、未选择中间 checkpoint，也未修改历史裁决。", "",
        "## 图表合同", "",
        "- 图7核心结论：DRTP 的任务得分改善能对应到更高的任务完成率和更低的超时率；碰撞率的小幅升高必须同步展示。",
        "- 图S1核心结论：十条轨迹完整训练至相同 10M 终点，训练期监控数据可用于透明展示优化过程；其回报因两方法采样分布不同，不作为最终方法优劣证据。",
        "- 统计单位：训练种子（n=5）；每个菱形是五个种子均值，细线连接同一配对种子。",
        "- 终止记录：所有 episode 均保留；没有删除故障前碰撞或提前终止记录。", "",
        "## 图7源数据摘要", "",
        "| 条件族 | 指标 | UTR均值 | DRTP均值 | DRTP−UTR |", "|---|---|---:|---:|---:|",
    ]
    for family in FAMILIES:
        for metric, label, _ in METRICS:
            left = np.mean([float(row[metric]) for row in by[("utr_sg", family)]])
            right = np.mean([float(row[metric]) for row in by[("drtp_sg", family)]])
            lines.append(f"| {family} | {label} | {left:.3f} | {right:.3f} | {right-left:+.3f} |")
    lines += ["", "## 数据与产物", "",
              "- `formal_results/source_data/formal_terminal_outcomes_by_seed_family.csv`：图7的逐种子、逐条件族源数据；",
              "- `formal_results/source_data/formal_training_monitor_binned.csv`：图S1的 500-update 分箱源数据；",
              "- `formal_results/figures/fig7_formal_terminal_outcomes.*`：主文图；",
              "- `formal_results/figures/figS1_training_diagnostics.*`：补充性训练诊断图。", "",
              "## 解释边界", "",
              "图7支持“正式任务得分改善伴随完成率提高与超时降低”，但不证明特定策略因果机制。图S1只证明训练日志完整可审计；由于 DRTP 与 UTR 的训练场景权重不同，不能将训练期 rollout 回报直接解释为相同分布上的性能 superiority。", ""]
    (PAPER / "16_no_training_evidence_enhancement_audit.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    configure_style()
    terminal_rows = formal_terminal_outcomes()
    write_terminal_source(terminal_rows)
    plot_terminal_outcomes(terminal_rows)
    monitor_rows = binned_training_monitor()
    write_monitor_source(monitor_rows)
    plot_training_monitor(monitor_rows)
    write_report(terminal_rows, monitor_rows)
    print("PASS: generated terminal-outcome and training-diagnostic evidence without training or re-evaluation")


if __name__ == "__main__":
    main()
