from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "results" / "intercept_3d_node_failure_curriculum_formal_node_failure_eval" / "episode_metrics.csv"
DEFAULT_OUT_CSV = ROOT / "results" / "intercept_3d_relay_failure_case_candidates.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "intercept_3d_relay_failure_case_candidates.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find matched relay-failure episodes suitable for trajectory/timeline case studies.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def build_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    pairs: dict[tuple[int, int], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        if row["scenario"] != "relay_failure":
            continue
        pairs[(int(row["train_seed"]), int(row["episode"]))][row["graph_encoder"]] = row

    candidates: list[dict[str, str]] = []
    for (train_seed, episode), graphs in pairs.items():
        if "single" not in graphs or "multi_relation" not in graphs:
            continue
        single = graphs["single"]
        multi = graphs["multi_relation"]
        single_recovered = as_float(single, "post_failure_chain_recovered")
        multi_recovered = as_float(multi, "post_failure_chain_recovered")
        single_recovery_steps = as_float(single, "post_failure_chain_recovery_steps")
        multi_recovery_steps = as_float(multi, "post_failure_chain_recovery_steps")
        if multi_recovered <= 0.0:
            continue
        recovery_step_gain = single_recovery_steps - multi_recovery_steps
        recovery_prob_gain = multi_recovered - single_recovered
        if recovery_prob_gain <= 0.0 and recovery_step_gain <= 0.0:
            continue
        candidates.append(
            {
                "train_seed": str(train_seed),
                "episode": str(episode),
                "single_eval_seed": single["seed"],
                "multi_eval_seed": multi["seed"],
                "single_checkpoint": single["checkpoint"],
                "multi_checkpoint": multi["checkpoint"],
                "single_recovered": f"{single_recovered:.0f}",
                "multi_recovered": f"{multi_recovered:.0f}",
                "single_recovery_steps": f"{single_recovery_steps:.1f}",
                "multi_recovery_steps": f"{multi_recovery_steps:.1f}",
                "recovery_step_gain": f"{recovery_step_gain:.1f}",
                "single_success": f"{as_float(single, 'success'):.0f}",
                "multi_success": f"{as_float(multi, 'success'):.0f}",
                "single_tracking_during_failure": f"{as_float(single, 'tracking_during_failure_rate'):.3f}",
                "multi_tracking_during_failure": f"{as_float(multi, 'tracking_during_failure_rate'):.3f}",
                "single_connectivity_during_failure": f"{as_float(single, 'connectivity_during_failure'):.3f}",
                "multi_connectivity_during_failure": f"{as_float(multi, 'connectivity_during_failure'):.3f}",
                "case_score": f"{100.0 * recovery_prob_gain + max(0.0, recovery_step_gain):.1f}",
            }
        )
    candidates.sort(key=lambda row: float(row["case_score"]), reverse=True)
    return candidates


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No relay-failure case candidates found")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]], limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Relay-Failure Case Candidates",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "These matched episodes are candidates for later trajectory and timeline plots. They are not new experiments; they are selected from the formal relay-failure evaluation CSV.",
        "",
        "| Rank | Train seed | Episode | Single recovered | Multi recovered | Recovery steps single/multi | Step gain | Tracking during failure single/multi | Connectivity during failure single/multi |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for idx, row in enumerate(rows[:limit], start=1):
        lines.append(
            f"| {idx} | {row['train_seed']} | {row['episode']} | {row['single_recovered']} | {row['multi_recovered']} | "
            f"{row['single_recovery_steps']} / {row['multi_recovery_steps']} | {row['recovery_step_gain']} | "
            f"{row['single_tracking_during_failure']} / {row['multi_tracking_during_failure']} | "
            f"{row['single_connectivity_during_failure']} / {row['multi_connectivity_during_failure']} |"
        )
    lines.extend(
        [
            "",
            "## Next Use",
            "",
            "Use the top candidates to replay both checkpoints with per-step logging, then draw a timeline of node failure, tracking loss/recovery, communication connectivity, and kill-chain closure.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = build_candidates(read_rows(args.input))
    rows = rows[: args.limit]
    write_csv(args.out_csv, rows)
    write_md(args.out_md, rows, args.limit)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
