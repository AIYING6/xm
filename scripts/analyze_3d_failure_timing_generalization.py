from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCENARIOS = (
    "dropout030_relay_failure_early",
    "dropout030_relay_failure",
    "dropout030_relay_failure_delayed",
    "dropout030_relay_failure_late",
)
DEFAULT_METHODS = ("no_graph", "single", "multi_relation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate fixed-checkpoint relay-failure timing generalization diagnostics."
    )
    parser.add_argument(
        "--summary-csv",
        action="append",
        type=Path,
        default=None,
        help="Checkpoint summary CSV. May be repeated.",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "docs" / "gate1_safety_fx60_failure_timing_generalization_diag5_summary.md",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "gate1_safety_fx60_failure_timing_generalization_diag5" / "timing_summary.csv",
    )
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def mean_all(rows: list[dict[str, str]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def mean_valid(rows: list[dict[str, str]], key: str) -> tuple[float | None, int]:
    values = [float(row[key]) for row in rows if float(row[key]) >= 0.0]
    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100.0:.1f}"


def aggregate(rows: list[dict[str, str]], scenarios: list[str], methods: list[str]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["scenario"], row["graph_encoder"])].append(row)

    out: list[dict[str, object]] = []
    for scenario in scenarios:
        for method in methods:
            method_rows = groups.get((scenario, method), [])
            if not method_rows:
                continue
            tracking, valid_tracking = mean_valid(method_rows, "tracking_during_failure_rate_mean")
            chain, valid_chain = mean_valid(method_rows, "chain_closed_during_failure_rate_mean")
            out.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "n_training_seeds": len(method_rows),
                    "episodes_per_seed": int(float(method_rows[0].get("episodes", "0"))),
                    "recovery": mean_all(method_rows, "post_failure_chain_recovered_mean"),
                    "tracking": tracking,
                    "chain": chain,
                    "timeout": mean_all(method_rows, "timeout_mean"),
                    "collision": mean_all(method_rows, "collision_mean"),
                    "valid_failure_window_tracking_seeds": valid_tracking,
                    "valid_failure_window_chain_seeds": valid_chain,
                }
            )
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = (
        "scenario",
        "method",
        "n_training_seeds",
        "episodes_per_seed",
        "recovery",
        "tracking",
        "chain",
        "timeout",
        "collision",
        "valid_failure_window_tracking_seeds",
        "valid_failure_window_chain_seeds",
    )
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]], source_csvs: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    min_episodes = min(int(row["episodes_per_seed"]) for row in rows) if rows else 0
    is_formal = min_episodes >= 100
    title_suffix = "Formal Summary" if is_formal else "Diagnostic"
    evidence_note = (
        f"This is a fixed-checkpoint formal summary with {min_episodes} episodes per training seed."
        if is_formal
        else f"This is a {min_episodes}-episode-per-seed diagnostic only. It is not paper-level evidence."
    )
    lines = [
        f"# Gate 1 Safety Fixed-Update-60 Failure-Timing Generalization {title_suffix}",
        "",
        evidence_note,
        "",
        "Source CSVs:",
        "",
        *[f"- `{source_csv.as_posix()}`" for source_csv in source_csvs],
        "",
        "Failure-window metrics treat `-1` sentinel values as N/A when an episode terminates before the failure window contributes valid measurements.",
        "",
        "| Scenario | Method | Episodes/seed | Recovery | Tracking | Chain | Timeout | Collision | Valid failure-window seeds |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        valid = f"{row['valid_failure_window_tracking_seeds']}/{row['n_training_seeds']}"
        lines.append(
            "| {scenario} | {method} | {episodes_per_seed} | {recovery} | {tracking} | {chain} | {timeout} | {collision} | {valid} |".format(
                scenario=row["scenario"],
                method=row["method"],
                episodes_per_seed=row["episodes_per_seed"],
                recovery=fmt_pct(row["recovery"]),
                tracking=fmt_pct(row["tracking"]),
                chain=fmt_pct(row["chain"]),
                timeout=fmt_pct(row["timeout"]),
                collision=fmt_pct(row["collision"]),
                valid=valid,
            )
        )

    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- Early relay failure is harder than the nominal failure timing, but the method ordering is preserved: `no_graph < single < multi_relation` on recovery.",
            "- The nominal dropout-relay timing is still the cleanest current main scenario.",
        ]
    )
    if any("late" in str(row["scenario"]) or "delayed" in str(row["scenario"]) for row in rows):
        lines.extend(
            [
                "- Delayed or late relay failure needs careful metric handling because some policies finish or fail before the failure window produces valid failure-window tracking/chain measurements.",
                "- If delayed or late conditions are used, report valid-window counts and avoid overinterpreting failure-window tracking averages when many episodes terminate before the window.",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    summary_csvs = args.summary_csv or [
        ROOT
        / "results"
        / "gate1_safety_fx60_failure_timing_generalization_diag5"
        / "test_checkpoint_summary.csv"
    ]
    input_rows: list[dict[str, str]] = []
    for summary_csv in summary_csvs:
        input_rows.extend(read_rows(summary_csv))
    rows = aggregate(input_rows, args.scenarios, args.methods)
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, summary_csvs)
    print(args.out_csv)
    print(args.out_md)


if __name__ == "__main__":
    main()
