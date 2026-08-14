"""Aggregate the frozen TP-1 Schedule-C development result."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "PHASE-TP-1-SCHEDULE-C-V1"
SEEDS = (1601, 1602)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def validate_run(run: Path, seed: int) -> tuple[dict, list[dict[str, str]]]:
    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed", manifest
    assert manifest["arm"] == "ctp_c", manifest
    assert manifest["seed"] == seed, manifest
    assert manifest["schedule"] == "C", manifest
    assert manifest["environment_steps"] == 300032, manifest
    assert manifest["updates"] == 1172, manifest
    assert manifest["num_envs"] == 4 and manifest["rollout_steps"] == 64, manifest
    assert manifest["checkpoint_selection"] == "fixed_final_update_only", manifest
    assert manifest["resume"] is False and manifest["early_stopping"] is False, manifest
    assert manifest["checkpoint_promotion"] is False, manifest
    assert manifest["tuning_tape_start"] == 350000, manifest
    paired = read_csv(run / "paired_metrics.csv")
    raw = read_csv(run / "raw_episode_metrics.csv")
    assert len(paired) == 50, len(paired)
    assert len(raw) == 100, len(raw)
    assert all(row["arm"] == "ctp_c" for row in paired), paired[:1]
    assert all(row["failure_exposed"] in {"0", "1"} for row in paired), paired[:1]
    return manifest, paired


def summarize(seed: int, paired: list[dict[str, str]]) -> dict:
    return {
        "seed": seed,
        "J_nominal": mean(paired, "J_nominal"),
        "J_failure": mean(paired, "J_failure"),
        "Delta_J": mean(paired, "delta_J"),
        "collision_failure": mean(paired, "collision_failure"),
        "timeout_failure": mean(paired, "timeout_failure"),
        "constraint_failure": mean(paired, "constraint_failure"),
        "failure_exposure": mean(paired, "failure_exposed"),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("results/phase_tp1_schedule_c"))
    args = parser.parse_args()
    rows = []
    manifests = []
    for seed in SEEDS:
        manifest, paired = validate_run(args.results_root / "runs" / "ctp_c" / f"seed{seed}", seed)
        manifests.append(manifest)
        rows.append(summarize(seed, paired))
    out_csv = args.results_root / "schedule_c_per_seed_summary.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    pooled = {key: sum(row[key] for row in rows) / len(rows) for key in fields if key != "seed"}
    result = {
        "protocol": PROTOCOL,
        "round_a_complete": True,
        "schedule_c_complete": True,
        "per_seed": rows,
        "pooled_mean": pooled,
        "schedule_b_started": False,
        "schedule_d_started": False,
        "tp2_started": False,
        "canonical_seeds_used": False,
        "resume_used": False,
        "early_stopping_used": False,
        "checkpoint_promotion_used": False,
        "fixed_tuning_tape": "350000-350049",
        "manifest_count": len(manifests),
        "selection_verdict": "SCHEDULE_C_COMPLETED_PENDING_SCHEDULE_A_COMPARISON",
    }
    (args.results_root / "SCHEDULE_C_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
