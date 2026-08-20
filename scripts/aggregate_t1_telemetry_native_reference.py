"""Aggregate T1 reference outcomes only from telemetry-native episode aggregates."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_t1_telemetry_native_single import SEEDS  # noqa: E402
from scripts.telemetry_native_t0 import read_jsonl, sha256  # noqa: E402


PROTOCOL = "T1-TELEMETRY-NATIVE-REFERENCE-AGGREGATE-V1"


def mean(rows: list[dict], field: str) -> float:
    values = [float(row[field]) for row in rows if row.get(field) is not None and math.isfinite(float(row[field]))]
    return float(np.mean(values)) if values else math.nan


def cell_summary(rows: list[dict]) -> dict:
    by_condition: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_condition[str(row["scenario"])].append(row)
    condition_j = {name: mean(items, "J") for name, items in sorted(by_condition.items())}
    ood = [value for name, value in condition_j.items() if name not in {"nominal", "f0_seen_44_80"}]
    failure_rows = [row for row in rows if int(row["scheduled_failure_onset"]) > 0]
    risk_set = [row for row in failure_rows if int(row["terminal_step"]) >= int(row["scheduled_failure_onset"])]
    pre_trigger_collision = [row for row in failure_rows if int(row["collision"]) == 1 and int(row["terminal_step"]) < int(row["scheduled_failure_onset"])]
    return {
        "J_nominal": condition_j["nominal"], "J_F0": condition_j["f0_seen_44_80"],
        "J_OOD_mean": float(np.mean(ood)), "J_OOD_worst": float(np.min(ood)),
        "condition_J": condition_j, "collision": mean(rows, "collision"), "timeout": mean(rows, "timeout"),
        "constraint_violation": mean(rows, "constraint_violation"), "episode_length": mean(rows, "terminal_step"),
        "risk_set_size": len(risk_set), "scheduled_failure_episodes": len(failure_rows),
        "survival_to_onset_fraction": len(risk_set) / len(failure_rows),
        "failure_trigger_success_among_risk_set": mean(risk_set, "failure_exposed"),
        "pre_trigger_collision_count": len(pre_trigger_collision),
        "pre_trigger_collision_rate": len(pre_trigger_collision) / len(failure_rows),
        "path_switch_count": mean(failure_rows, "path_switch_count"),
        "direct_path_fraction": mean(failure_rows, "direct_path_fraction_during_failure"),
        "relay_path_fraction": mean(failure_rows, "relay_path_fraction_during_failure"),
        "task_support_fraction": mean(failure_rows, "task_support_fraction_during_failure"),
        "legal_information_fraction": mean(failure_rows, "legal_information_fraction_during_failure"),
        "mean_cache_age": mean(failure_rows, "mean_cache_age_during_failure"),
        "traveled_distance": mean(failure_rows, "traveled_distance"), "control_effort": mean(failure_rows, "control_effort"),
    }


def markdown(per_seed: dict[int, dict], pooled: dict) -> str:
    table = "\n".join(
        f"| {seed} | {row['J_nominal']:.3f} | {row['J_F0']:.3f} | {row['J_OOD_mean']:.3f} | {row['J_OOD_worst']:.3f} | {row['collision']:.3f} | {row['timeout']:.3f} |"
        for seed, row in per_seed.items()
    )
    return f"""# T1 Telemetry-Native UTR-SG Reference Report

**Status:** `DESCRIPTIVE DEVELOPMENT REFERENCE ONLY`
**Protocol:** `{PROTOCOL}`

This report is derived only from the new T1 per-seed
`raw_step_telemetry.jsonl -> episode_aggregates.jsonl` chain.  It does not
reuse a historical aggregate, promote a checkpoint, establish algorithmic
superiority, or serve as held-out/canonical evidence.

| Training seed | J nominal | J F0 | J OOD mean | J OOD worst | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{table}
| Pooled seed mean | {pooled['J_nominal']:.3f} | {pooled['J_F0']:.3f} | {pooled['J_OOD_mean']:.3f} | {pooled['J_OOD_worst']:.3f} | {pooled['collision']:.3f} | {pooled['timeout']:.3f} |

## Technical validity and safety diagnostics

- pooled survival to onset: `{pooled['survival_to_onset_fraction']:.4f}`;
- pooled trigger success in the alive-at-onset risk set: `{pooled['failure_trigger_success_among_risk_set']:.4f}`;
- pooled pre-trigger collision rate: `{pooled['pre_trigger_collision_rate']:.4f}`;
- all pre-trigger terminations remain in unconditional return and safety metrics.

## Boundary

T1 is a new telemetry-native reference line.  It does not authorize a new
algorithm, a training extension, held-out or canonical evaluation, or a paper
superiority claim.  Any next comparison requires a separately frozen contract.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    root = args.output_root / "evaluations" / "final_1m" / "utr_sg"
    per_seed = {}
    for seed in SEEDS:
        seed_root = root / f"seed{seed}"
        manifest = json.loads((seed_root / "manifest.json").read_text(encoding="utf-8"))
        raw_path, aggregate_path = seed_root / "raw_step_telemetry.jsonl", seed_root / "episode_aggregates.jsonl"
        if not manifest.get("source_closure_pass") or manifest.get("historical_aggregate_reuse") is not False:
            raise RuntimeError(f"invalid source-closure manifest: {seed_root}")
        if sha256(raw_path) != manifest["raw_step_telemetry_sha256"] or sha256(aggregate_path) != manifest["episode_aggregates_sha256"]:
            raise RuntimeError(f"telemetry hash mismatch: {seed_root}")
        per_seed[seed] = cell_summary(read_jsonl(aggregate_path))
    keys = ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout", "constraint_violation", "episode_length", "survival_to_onset_fraction", "failure_trigger_success_among_risk_set", "pre_trigger_collision_rate", "path_switch_count", "direct_path_fraction", "relay_path_fraction", "task_support_fraction", "legal_information_fraction", "mean_cache_age", "traveled_distance", "control_effort")
    pooled = {key: float(np.mean([row[key] for row in per_seed.values()])) for key in keys}
    result = {"protocol": PROTOCOL, "status": "completed", "training_seed_unit": "seed", "per_seed": per_seed, "pooled_seed_mean": pooled}
    output = args.output_root / "evaluations" / "final_1m" / "T1_REFERENCE_RESULT.json"
    if output.exists() or args.report_path.exists():
        raise FileExistsError("refusing to overwrite T1 aggregate/report")
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    with args.report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown(per_seed, pooled))
    print(json.dumps({"status": "completed", "result": str(output), "report": str(args.report_path)}, indent=2))


if __name__ == "__main__":
    main()
