"""Render the P1 Chinese manuscript KM panel from the frozen held-out inputs.

The raw held-out data are intentionally read-only and remain in the sibling frozen
worktree referenced by _operator_scripts/run_survival_v1_1.py.  This renderer only
selects the four methods authorised by the Fig. 2 contract.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RAW_BASE = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_held_out_v1_5_10800_20260807/held_out_v1.5")
OUT_DIR = ROOT / "paper_chinese" / "figures"
METHODS = {
    "full_ea_rg": ("EA-RG", "#1F77B4", 2.8),
    "mappo": ("MAPPO", "#D62728", 2.1),
    "happo": ("HAPPO", "#2CA02C", 2.1),
    "param_matched_single": ("宽单图", "#9467BD", 2.1),
}
PRIMARY_SCENARIOS = {"dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure"}


def configure_font() -> None:
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        fm.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = "Microsoft YaHei"
    plt.rcParams.update({"axes.unicode_minus": False, "pdf.fonttype": 42, "ps.fonttype": 42})


def load(method: str, seed: str) -> tuple[np.ndarray, np.ndarray, Path]:
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
    curve = []
    for time in unique:
        at_time = times == time
        observed = int(events[at_time].sum())
        censored = int(at_time.sum()) - observed
        if at_risk > 0:
            survival *= 1.0 - observed / at_risk
        curve.append(survival)
        at_risk -= observed + censored
    return unique, np.asarray(curve)


def main() -> None:
    configure_font()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    input_paths: list[Path] = []
    fig, ax = plt.subplots(figsize=(7.4, 5.1), constrained_layout=True)
    for method, (label, color, width) in METHODS.items():
        all_times, all_events = [], []
        for seed in ("0", "1", "2"):
            times, events, path = load(method, seed)
            assert len(times) == 200, f"{method}/seed{seed} expected 200 matched exposures, got {len(times)}"
            all_times.append(times)
            all_events.append(events)
            input_paths.append(path)
        time, survival = km_step(np.concatenate(all_times), np.concatenate(all_events))
        ax.step(np.r_[0, time], np.r_[1.0, survival], where="post", label=label, color=color, linewidth=width)
    ax.axvspan(0, 80, color="#EAF2F8", zorder=0)
    ax.axvline(80, color="#5D6D7E", linewidth=1.1, linestyle="--")
    ax.text(40, 0.06, "预设故障持续窗口\n$\\tau=80$", ha="center", va="bottom", fontsize=9, color="#34495E")
    ax.annotate("RMST80：EA-RG 11.81 步\nMAPPO 15.51 步", xy=(80, 0.47), xytext=(116, 0.30), fontsize=9.2, color="#1F2933", arrowprops={"arrowstyle": "-", "color": "#5D6D7E"})
    ax.set(xlim=(0, 220), ylim=(0, 1.03), xlabel="故障开始后的步数", ylabel="未恢复概率  $S(t)=P(T>t)$")
    ax.set_title("匹配失效暴露下的故障后恢复（Early + Nominal）", loc="left", fontsize=12, weight="bold")
    ax.grid(axis="y", color="#D8DDE3", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(title="方法", frameon=False, loc="upper right")
    ax.text(0.00, -0.19, "每条曲线汇总 3 个训练 seed、600 个 failure-exposed episodes；右删失。曲线仅作分布展示，主要比较为预设的 EA-RG–MAPPO RMST80。", transform=ax.transAxes, fontsize=8.3, color="#52606D")
    for suffix, dpi in (("png", 300), ("pdf", None)):
        fig.savefig(OUT_DIR / f"fig2_early_recovery_km.{suffix}", dpi=dpi, bbox_inches="tight")
    digest = hashlib.sha256()
    for path in sorted(input_paths):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    provenance = (
        "Claim: EA-RG is earlier than MAPPO within pre-specified RMST80; pooled KM is descriptive.\n"
        "Raw source: sibling frozen held-out v1.5 worktree, read-only.\n"
        "Selection: Early + Nominal; 4 Fig. 2 contract methods; 3 seeds; 200 exposures/method/seed.\n"
        "Script: scripts/render_zh_early_recovery_figure.py\n"
        f"SHA256(path+content, 12 inputs): {digest.hexdigest()}\n"
    )
    with (OUT_DIR / "fig2_early_recovery_km.provenance.txt").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(provenance)


if __name__ == "__main__":
    main()
