from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Patch
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "results" / "figures"
DEFAULT_REPORT = ROOT / "docs" / "intercept_3d_manuscript_figures.md"
DEFAULT_MAIN_TABLE = ROOT / "results" / "intercept_3d_paper_main_table.csv"
DEFAULT_TASK_SUPPORT = ROOT / "results" / "intercept_3d_task_support_ablation_formal_summary.csv"
DEFAULT_ROLE_PAIR_GATE = ROOT / "results" / "intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.csv"
DEFAULT_STRICT = (
    ROOT
    / "results"
    / "intercept_3d_strict_sensing_curriculum_seed0_pilot"
    / "formal_recovery_summary.csv"
)


COLORS = {
    "single": "#4C78A8",
    "multi": "#2F9C67",
    "task": "#F58518",
    "gate": "#B279A2",
    "strict": "#E45756",
    "gray": "#59656F",
    "light_gray": "#E6E8EB",
    "target": "#D95F02",
    "scout": "#1B9E77",
    "relay": "#386CB0",
    "attacker": "#E7298A",
}


@dataclass(frozen=True)
class DeltaCI:
    mean: float
    low: float
    high: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-ready figures for the 3DOF UAV study.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--main-table", type=Path, default=DEFAULT_MAIN_TABLE)
    parser.add_argument("--task-support", type=Path, default=DEFAULT_TASK_SUPPORT)
    parser.add_argument("--role-pair-gate", type=Path, default=DEFAULT_ROLE_PAIR_GATE)
    parser.add_argument("--strict-sensing", type=Path, default=DEFAULT_STRICT)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def by_scenario(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["scenario"]: row for row in rows}


def as_float(row: dict[str, str], key: str) -> float:
    value = row[key]
    if value == "NA" or value == "":
        return float("nan")
    return float(value)


def parse_delta_ci(text: str) -> DeltaCI:
    match = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s+\[([+-]?\d+(?:\.\d+)?),\s*([+-]?\d+(?:\.\d+)?)\]\s*", text)
    if not match:
        raise ValueError(f"Cannot parse delta CI: {text!r}")
    return DeltaCI(*(float(x) for x in match.groups()))


def save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def style_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D8DDE3", linewidth=0.8, alpha=0.8)


def plot_task_scene(out_path: Path) -> None:
    fig = plt.figure(figsize=(8.2, 5.2))
    ax = fig.add_subplot(111, projection="3d")

    blue = {
        "Scout": np.array([-9.5, -2.0, 4.8]),
        "Relay": np.array([-6.3, 1.5, 5.3]),
        "Attacker": np.array([-3.4, -1.3, 4.6]),
    }
    target = np.array([2.8, 0.2, 5.0])

    role_colors = {"Scout": COLORS["scout"], "Relay": COLORS["relay"], "Attacker": COLORS["attacker"]}
    for label, pos in blue.items():
        ax.scatter(pos[0], pos[1], pos[2], s=110, color=role_colors[label], edgecolor="white", linewidth=1.0)
        ax.text(pos[0], pos[1], pos[2] + 0.25, label, ha="center", va="bottom", fontsize=9)

    ax.scatter(target[0], target[1], target[2], s=130, marker="^", color=COLORS["target"], edgecolor="white", linewidth=1.0)
    ax.text(target[0], target[1], target[2] + 0.3, "Target", ha="center", va="bottom", fontsize=9)

    # Communication and support paths.
    pairs = [("Scout", "Relay"), ("Relay", "Attacker"), ("Scout", "Attacker")]
    for a, b in pairs:
        pa, pb = blue[a], blue[b]
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], [pa[2], pb[2]], color=COLORS["relay"], linewidth=1.6, alpha=0.75)

    for label in ("Scout", "Attacker"):
        p = blue[label]
        ax.plot([p[0], target[0]], [p[1], target[1]], [p[2], target[2]], color=COLORS["task"], linestyle="--", linewidth=1.7)

    theta = np.linspace(0, 2 * math.pi, 160)
    for center, radius, color in ((blue["Scout"], 4.0, COLORS["scout"]), (blue["Relay"], 5.2, COLORS["relay"])):
        ax.plot(center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta), np.full_like(theta, center[2] - 0.15), color=color, alpha=0.25, linewidth=1.1)

    ax.set_title("3DOF heterogeneous UAV kill-chain recovery task", pad=14, fontsize=12)
    ax.set_xlabel("x / km")
    ax.set_ylabel("y / km")
    ax.set_zlabel("altitude / km")
    ax.view_init(elev=23, azim=-58)
    ax.set_box_aspect((1.7, 1.0, 0.55))
    ax.set_xlim(-11.0, 4.0)
    ax.set_ylim(-4.0, 4.0)
    ax.set_zlim(3.8, 6.2)

    legend = [
        Patch(facecolor=COLORS["scout"], label="Perception-capable scout"),
        Patch(facecolor=COLORS["relay"], label="Communication relay"),
        Patch(facecolor=COLORS["attacker"], label="Attack-window former"),
        Patch(facecolor=COLORS["task"], label="Sensing / task support"),
    ]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.02, 0.98), frameon=True, fontsize=8)
    save_fig(fig, out_path)


def curved_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str, label: str | None = None, rad: float = 0.0, lw: float = 2.0, linestyle: str = "-") -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=lw,
        linestyle=linestyle,
        color=color,
        alpha=0.9,
    )
    ax.add_patch(arrow)
    if label:
        mid = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
        ax.text(mid[0], mid[1] + 0.04, label, color=color, fontsize=8, ha="center", va="center")


def plot_multi_relation_graph(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    ax.set_title("Task-graph multi-relation representation (perception / communication / task support)", fontsize=12, pad=12)
    ax.set_xlim(0, 1.15)
    ax.set_ylim(0, 1)
    ax.axis("off")

    pos = {
        "Scout": (0.18, 0.66),
        "Relay": (0.45, 0.45),
        "Attacker": (0.72, 0.66),
        "Target": (0.45, 0.16),
    }
    node_colors = {
        "Scout": COLORS["scout"],
        "Relay": COLORS["relay"],
        "Attacker": COLORS["attacker"],
        "Target": COLORS["target"],
    }
    curved_arrow(ax, pos["Scout"], pos["Target"], COLORS["scout"], None, rad=-0.16)
    curved_arrow(ax, pos["Target"], pos["Scout"], COLORS["scout"], None, rad=-0.10, lw=1.2, linestyle="--")
    curved_arrow(ax, pos["Scout"], pos["Relay"], COLORS["relay"], None, rad=0.08)
    curved_arrow(ax, pos["Relay"], pos["Attacker"], COLORS["relay"], None, rad=0.08)
    curved_arrow(ax, pos["Scout"], pos["Attacker"], COLORS["task"], None, rad=-0.20)
    curved_arrow(ax, pos["Relay"], pos["Attacker"], COLORS["task"], None, rad=-0.15, lw=1.7, linestyle="--")
    curved_arrow(ax, pos["Attacker"], pos["Target"], COLORS["attacker"], None, rad=0.08)

    for name, (x, y) in pos.items():
        circle = plt.Circle((x, y), 0.075, color=node_colors[name], ec="white", lw=1.8, zorder=4)
        ax.add_patch(circle)
        ax.text(x, y + 0.002, name, ha="center", va="center", fontsize=9, color="white", weight="bold", zorder=5)

    box_text = "Static role-pair modulation (auxiliary)\nmultiplies sender messages by a learned embedding\nnot conditioned on failure state; no message pruning"
    ax.text(
        0.45,
        0.93,
        box_text,
        ha="center",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#F7F8FA", "edgecolor": "#C9D1D9"},
    )

    legend_handles = [
        Patch(facecolor=COLORS["scout"], label="Perception relation"),
        Patch(facecolor=COLORS["relay"], label="Communication relation"),
        Patch(facecolor=COLORS["task"], label="Task-support relation"),
        Patch(facecolor=COLORS["attacker"], label="Attack-window relation"),
    ]
    ax.text(0.93, 0.74, "Node roles", fontsize=9, weight="bold", ha="left", va="center")
    ax.text(0.93, 0.68, "Scout: wide radar", fontsize=8, ha="left", va="center")
    ax.text(0.93, 0.62, "Relay: long communication", fontsize=8, ha="left", va="center")
    ax.text(0.93, 0.56, "Attacker: engagement geometry", fontsize=8, ha="left", va="center")
    ax.text(0.93, 0.50, "Target: intermittently sensed", fontsize=8, ha="left", va="center")
    ax.legend(handles=legend_handles, loc="lower right", bbox_to_anchor=(1.0, 0.08), ncol=1, frameon=False, fontsize=8)
    save_fig(fig, out_path)


def plot_recovery_evidence(main_rows: list[dict[str, str]], task_rows: list[dict[str, str]], gate_rows: list[dict[str, str]], out_path: Path) -> None:
    main = by_scenario(main_rows)
    relay = main["relay_failure"]
    scout = main["scout_failure"]

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.0), gridspec_kw={"width_ratios": [1.0, 1.0, 1.2]})
    fig.suptitle("Main relay-failure recovery evidence and mechanism ablations", fontsize=12, y=1.03)

    labels = ["Relay failure", "Scout failure"]
    x = np.arange(len(labels))
    width = 0.34
    single_success = [as_float(relay, "single_recovery_percent"), as_float(scout, "single_recovery_percent")]
    multi_success = [as_float(relay, "multi_recovery_percent"), as_float(scout, "multi_recovery_percent")]
    axes[0].bar(x - width / 2, single_success, width, color=COLORS["single"], label="Single graph")
    axes[0].bar(x + width / 2, multi_success, width, color=COLORS["multi"], label="EA-RG-MAPPO-S")
    axes[0].set_ylabel("Post-failure recovery / %")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0, 110)
    style_axes(axes[0])
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    for i, row in enumerate((relay, scout)):
        axes[0].text(i, max(single_success[i], multi_success[i]) + 4, row["recovery_delta_pp_ci95"], ha="center", fontsize=8)

    single_steps = [as_float(relay, "single_recovery_steps"), as_float(scout, "single_recovery_steps")]
    multi_steps = [as_float(relay, "multi_recovery_steps"), as_float(scout, "multi_recovery_steps")]
    axes[1].bar(x - width / 2, single_steps, width, color=COLORS["single"], label="Single graph")
    axes[1].bar(x + width / 2, multi_steps, width, color=COLORS["multi"], label="EA-RG-MAPPO-S")
    axes[1].set_ylabel("Recovery steps")
    axes[1].set_xticks(x, labels)
    axes[1].set_ylim(0, max(single_steps) * 1.35)
    style_axes(axes[1])
    for i, row in enumerate((relay, scout)):
        axes[1].text(i, max(single_steps[i], multi_steps[i]) + 2.5, row["recovery_steps_delta_ci95"], ha="center", fontsize=8)

    ablation_labels = ["No task support", "No role-pair gate"]
    task = by_scenario(task_rows)["relay_failure"]
    gate = by_scenario(gate_rows)["relay_failure"]
    success_deltas = [
        100.0 * as_float(task, "delta_post_failure_chain_recovered_mean"),
        100.0 * as_float(gate, "delta_post_failure_chain_recovered_mean"),
    ]
    success_err_low = [
        success_deltas[0] - 100.0 * as_float(task, "delta_post_failure_chain_recovered_ci_low"),
        success_deltas[1] - 100.0 * as_float(gate, "delta_post_failure_chain_recovered_ci_low"),
    ]
    success_err_high = [
        100.0 * as_float(task, "delta_post_failure_chain_recovered_ci_high") - success_deltas[0],
        100.0 * as_float(gate, "delta_post_failure_chain_recovered_ci_high") - success_deltas[1],
    ]
    ax2 = axes[2]
    ax2.axhline(0, color="#30363D", linewidth=0.9)
    ax2.bar(np.arange(2), success_deltas, color=[COLORS["task"], COLORS["gate"]], width=0.55)
    ax2.errorbar(np.arange(2), success_deltas, yerr=[success_err_low, success_err_high], fmt="none", ecolor="#30363D", capsize=4, lw=1.2)
    ax2.set_ylabel("Full model recovery gain / pp")
    ax2.set_xticks(np.arange(2), ablation_labels)
    max_success_hi = max(
        100.0 * as_float(task, "delta_post_failure_chain_recovered_ci_high"),
        100.0 * as_float(gate, "delta_post_failure_chain_recovered_ci_high"),
    )
    ax2.set_ylim(0, max_success_hi * 1.20)
    style_axes(ax2)
    for i, value in enumerate(success_deltas):
        ax2.text(i, value + 1.2, f"+{value:.1f} pp", ha="center", fontsize=8)

    fig.tight_layout()
    save_fig(fig, out_path)


def plot_strict_sensing(strict_rows: list[dict[str, str]], out_path: Path) -> None:
    rows = by_scenario(strict_rows)
    relay = rows["relay_failure"]
    scout = rows["scout_failure"]
    labels = ["Relay failure", "Scout failure"]
    x = np.arange(len(labels))
    width = 0.34

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))
    fig.suptitle("Strict intermittent sensing pilot: no true target-state fallback", fontsize=12, y=1.03)

    single_recovery = [
        100.0 * as_float(relay, "single_post_failure_chain_recovered_mean"),
        100.0 * as_float(scout, "single_post_failure_chain_recovered_mean"),
    ]
    multi_recovery = [
        100.0 * as_float(relay, "multi_post_failure_chain_recovered_mean"),
        100.0 * as_float(scout, "multi_post_failure_chain_recovered_mean"),
    ]
    axes[0].bar(x - width / 2, single_recovery, width, color=COLORS["single"], label="Single graph")
    axes[0].bar(x + width / 2, multi_recovery, width, color=COLORS["multi"], label="EA-RG-MAPPO-S")
    axes[0].set_ylabel("Recovery / %")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0, 110)
    style_axes(axes[0])
    axes[0].legend(frameon=False, fontsize=8)

    for i, row in enumerate((relay, scout)):
        delta = 100.0 * as_float(row, "delta_post_failure_chain_recovered_mean")
        lo = 100.0 * as_float(row, "delta_post_failure_chain_recovered_ci_low")
        hi = 100.0 * as_float(row, "delta_post_failure_chain_recovered_ci_high")
        axes[0].text(i, max(single_recovery[i], multi_recovery[i]) + 4, f"{delta:+.1f} [{lo:+.1f}, {hi:+.1f}]", ha="center", fontsize=8)

    single_steps = [
        as_float(relay, "single_post_failure_chain_recovery_steps_mean"),
        as_float(scout, "single_post_failure_chain_recovery_steps_mean"),
    ]
    multi_steps = [
        as_float(relay, "multi_post_failure_chain_recovery_steps_mean"),
        as_float(scout, "multi_post_failure_chain_recovery_steps_mean"),
    ]
    axes[1].bar(x - width / 2, single_steps, width, color=COLORS["single"], label="Single graph")
    axes[1].bar(x + width / 2, multi_steps, width, color=COLORS["multi"], label="EA-RG-MAPPO-S")
    axes[1].set_ylabel("Recovery steps")
    axes[1].set_xticks(x, labels)
    axes[1].set_ylim(0, max(single_steps) * 1.30)
    style_axes(axes[1])
    for i, row in enumerate((relay, scout)):
        delta = as_float(row, "delta_post_failure_chain_recovery_steps_mean")
        lo = as_float(row, "delta_post_failure_chain_recovery_steps_ci_low")
        hi = as_float(row, "delta_post_failure_chain_recovery_steps_ci_high")
        axes[1].text(i, max(single_steps[i], multi_steps[i]) + 4, f"{delta:+.1f} [{lo:+.1f}, {hi:+.1f}]", ha="center", fontsize=8)

    fig.text(0.5, -0.03, "Budget-labeled scenario-depth result: 10 PPO fine-tuning updates, 30 episodes per seed.", ha="center", fontsize=8)
    fig.tight_layout()
    save_fig(fig, out_path)


def write_report(path: Path, figures: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Manuscript Figure Assets",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "These figures are generated from existing 3DOF result files and schematic task definitions. They do not retrain or re-evaluate policies.",
        "",
        "| Figure | File | Manuscript use |",
        "| --- | --- | --- |",
    ]
    for name, rel_path, use in figures:
        lines.append(f"| {name} | `{rel_path}` | {use} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Use relay-failure recovery as the main statistical figure.",
            "- Use task-support and role-pair-gate ablation deltas as mechanism evidence.",
            "- Label strict sensing as a 10-update scenario-depth pilot, not as a full-budget universal claim.",
            "- Keep the existing relay-failure replay figure as the qualitative timeline/case figure.",
            "",
            "Existing qualitative figure:",
            "",
            "- `results/figures/intercept_3d_relay_failure_case_replay.png`",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    main_rows = read_csv(args.main_table)
    task_rows = read_csv(args.task_support)
    gate_rows = read_csv(args.role_pair_gate)
    strict_rows = read_csv(args.strict_sensing)

    figures = [
        (
            "Task scene",
            "results/figures/intercept_3d_task_scene.png",
            "Introduce the 3DOF scout-relay-attacker kill-chain task.",
        ),
        (
            "Multi-relation graph",
            "results/figures/intercept_3d_multi_relation_graph.png",
            "Explain perception, communication, task-support, and role-pair-conditioned messages.",
        ),
        (
            "Main recovery evidence",
            "results/figures/intercept_3d_recovery_evidence_summary.png",
            "Show relay/scout recovery and relay-failure mechanism ablations.",
        ),
        (
            "Strict sensing pilot",
            "results/figures/intercept_3d_strict_sensing_summary.png",
            "Show the no-target-fallback scenario-depth result with an honest budget label.",
        ),
    ]

    plot_task_scene(ROOT / figures[0][1])
    plot_multi_relation_graph(ROOT / figures[1][1])
    plot_recovery_evidence(main_rows, task_rows, gate_rows, ROOT / figures[2][1])
    plot_strict_sensing(strict_rows, ROOT / figures[3][1])
    write_report(args.report, figures)

    for _name, rel_path, _use in figures:
        print(rel_path)
    print(args.report.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
