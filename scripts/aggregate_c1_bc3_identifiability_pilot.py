"""Aggregate the frozen C1 BC3 short pilot without extending its claims."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


PROTOCOL = "C1-BC3-IDENTIFIABILITY-PILOT-V1"
ARMS = ("ff_mappo", "recurrent_mappo", "bc3_mappo", "shuffled_bc3_mappo")
SEEDS = (91111, 91112, 91113)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def action_signature(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {"post_failure_events": 0.0, "post_failure_load_response_rate": 0.0, "mean_posterior_shift": 0.0}
    responses = [float(row["response_is_joint_load"]) > 0.5 for row in rows]
    shifts = [float(row["posterior_after"]) - float(row["posterior_before"]) for row in rows]
    return {
        "post_failure_events": float(len(rows)),
        "post_failure_load_response_rate": float(mean(responses)),
        "mean_posterior_shift": float(mean(shifts)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to aggregate without --execute")
    diagnostics = args.output_root / "diagnostics"
    if diagnostics.exists():
        raise FileExistsError(f"refusing to overwrite {diagnostics}")
    summaries: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            endpoint = args.output_root / "runs" / arm / f"seed{seed}" / "evaluation"
            summary = read_json(endpoint / "summary.json")
            if summary.get("protocol") != PROTOCOL or summary.get("arm") != arm:
                raise ValueError(f"unexpected endpoint metadata for {arm}/seed{seed}")
            signatures = action_signature(endpoint / "post_failure_action_trace.csv")
            summaries.append({"arm": arm, "seed": seed, **summary, **signatures})
    diagnostics.mkdir(parents=True)
    fields = list(summaries[0])
    with (diagnostics / "C1_BC3_PILOT_PER_SEED.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(summaries)
    grouped = {
        arm: [row for row in summaries if row["arm"] == arm]
        for arm in ARMS
    }
    group_summary = {
        arm: {
            "mean_completed_foods": mean(float(row["mean_completed_foods"]) for row in rows),
            "mean_timeout_rate": mean(float(row["timeout_rate"]) for row in rows),
            "mean_post_failure_events": mean(float(row["post_failure_events"]) for row in rows),
            "mean_post_failure_load_response_rate": mean(float(row["post_failure_load_response_rate"]) for row in rows),
            "mean_posterior_shift": mean(float(row["mean_posterior_shift"]) for row in rows),
        }
        for arm, rows in grouped.items()
    }
    decision = {
        "protocol": "C1-BC3-IDENTIFIABILITY-PILOT-AGGREGATE-V1",
        "verdict": "C1_BC3_PILOT_REPORTED_NO_AUTOMATIC_EXTENSION",
        "group_summary": group_summary,
        "interpretation_boundary": (
            "This short pilot reports prespecified behavior traces and endpoint summaries only. "
            "It cannot establish a formal performance advantage or authorize a budget extension. "
            "Human review must apply the frozen three-part identifiability gate."
        ),
        "training_started": False,
        "automatic_continuation": False,
    }
    (diagnostics / "C1_BC3_PILOT_DECISION.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
