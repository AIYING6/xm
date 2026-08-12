"""Independently reconstruct Phase 2IA4 strict-risk cohorts from chain traces.

This audit consumes already-produced DEVELOPMENT_ONLY validation artifacts.  It
does not train, evaluate policies, or alter the frozen endpoint.  Its purpose is
to make the V0 risk-set gate independently auditable from timestep-level data.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "development" / "role_gate_phase2ia4_validation"
ARMS = ("full_gate", "no_role_gate")
SEEDS = (101, 202, 303)
SCENARIOS = (
    "dropout030_delay2_relay_failure_early",
    "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed",
    "dropout030_delay2_relay_failure_late",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Refusing to write an empty audit table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def yes(value: str) -> bool:
    return float(value) > 0.5


def maybe_time(value: str) -> int | None:
    parsed = float(value)
    return None if parsed < 0 else int(round(parsed))


def reconstruct(rows: list[dict[str, str]]) -> dict:
    """Apply the frozen strict endpoint directly to a single episode timeline."""
    rows = sorted(rows, key=lambda row: int(row["timestep"]))
    # A configured failure time is not an observed failure time when an episode
    # terminates first.  The evaluator records the first *active* failure step.
    first_active = next((row for row in rows if yes(row["node_failure_active"])), None)
    failure = int(first_active["timestep"]) if first_active is not None else None
    before = rows if failure is None else [row for row in rows if int(row["timestep"]) < failure]
    after = [] if failure is None else [row for row in rows if int(row["timestep"]) >= failure]
    pre = any(yes(row["chain_valid_t"]) for row in before)
    loss_row = next((row for row in after if not yes(row["chain_valid_t"])), None)
    # `chain_lost_after_failure` is an auxiliary observed field.  Strict-risk
    # membership below additionally requires `pre`, exactly as frozen in V0.
    loss = loss_row is not None
    recovery_row = None
    if loss_row is not None:
        loss_t = int(loss_row["timestep"])
        recovery_row = next(
            (row for row in after if int(row["timestep"]) > loss_t and yes(row["chain_valid_t"])), None
        )
    recovered = pre and loss and recovery_row is not None
    first_post = next((row for row in after if yes(row["chain_valid_t"])), None)
    if pre and loss and recovered:
        cohort = "C"
    elif pre and loss:
        cohort = "D"
    elif pre:
        cohort = "B"
    elif first_post is not None:
        cohort = "E"
    else:
        cohort = "A"
    loss_t = int(loss_row["timestep"]) if loss_row is not None else None
    recovery_t = int(recovery_row["timestep"]) if recovery_row is not None else None
    return {
        "pre_failure_chain_established": int(pre),
        "chain_lost_after_failure": int(loss),
        "post_failure_chain_recovered_after_loss": int(recovered),
        "post_failure_chain_first_established": int(first_post is not None),
        "t_failure": "" if failure is None else failure,
        "t_loss": "" if loss_t is None else loss_t,
        "t_recovery": "" if recovery_t is None else recovery_t,
        # The frozen primary duration is defined only for strict events.
        "delta_t_loss_to_recovery": recovery_t - loss_t if recovered and loss_t is not None and recovery_t is not None else -1,
        "event": int(recovered),
        "censor_time": int(rows[-1]["timestep"]),
        "cohort": cohort,
    }


def same_time(raw: str, rebuilt: str | int) -> bool:
    raw_time = maybe_time(raw)
    rebuilt_time = None if rebuilt == "" or int(rebuilt) < 0 else int(rebuilt)
    return raw_time == rebuilt_time


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    raw_path = args.out_dir / "raw_validation" / "episode_metrics.csv"
    raw = read_csv(raw_path)
    # Episode IDs are deliberately paired across arms; (arm, ID), not ID alone,
    # is the unique validation observation key.
    raw_by_key = {(row["arm"], row["development_episode_id"]): row for row in raw}
    if len(raw_by_key) != len(raw):
        raise RuntimeError("Duplicate (arm, development episode ID) keys in raw validation table")

    rebuilt_rows: list[dict] = []
    mismatches: list[dict] = []
    trace_paths = sorted((args.out_dir / "raw_timestep_chain").glob("*.csv"))
    for trace_path in trace_paths:
        arm = next((candidate for candidate in ARMS if trace_path.name.startswith(candidate + "_")), None)
        if arm is None:
            raise RuntimeError(f"Cannot infer arm from trace filename: {trace_path.name}")
        episodes: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in read_csv(trace_path):
            episodes[row["episode_id"]].append(row)
        for dev_id, timeline in episodes.items():
            if (arm, dev_id) not in raw_by_key:
                raise RuntimeError(f"Trace episode {dev_id} is absent from raw validation")
            source = raw_by_key[(arm, dev_id)]
            rebuilt = reconstruct(timeline)
            row = {
                "development_episode_id": dev_id, "arm": source["arm"], "seed": source["train_seed"],
                "scenario": source["scenario"], "trace_file": trace_path.name, **rebuilt,
            }
            rebuilt_rows.append(row)
            checks = {
                "pre_failure_chain_established": str(rebuilt["pre_failure_chain_established"]) == str(int(float(source["pre_failure_chain_established"]))),
                "chain_lost_after_failure": str(rebuilt["chain_lost_after_failure"]) == str(int(float(source["chain_lost_after_failure"]))),
                "post_failure_chain_recovered_after_loss": str(rebuilt["post_failure_chain_recovered_after_loss"]) == str(int(float(source["post_failure_chain_recovered_after_loss"]))),
                "post_failure_chain_first_established": str(rebuilt["post_failure_chain_first_established"]) == str(int(float(source["post_failure_chain_first_established"]))),
                "t_failure": same_time(source["t_failure"], rebuilt["t_failure"]),
                "t_loss": same_time(source["t_loss"], rebuilt["t_loss"]),
                "t_recovery": same_time(source["t_recovery"], rebuilt["t_recovery"]),
                "delta_t_loss_to_recovery": same_time(source["delta_t_loss_to_recovery"], rebuilt["delta_t_loss_to_recovery"]),
                "event": str(rebuilt["event"]) == str(int(float(source["event"]))),
            }
            for field, passed in checks.items():
                if not passed:
                    mismatches.append({"development_episode_id": dev_id, "arm": source["arm"], "seed": source["train_seed"],
                                       "scenario": source["scenario"], "field": field, "raw_value": source[field],
                                       "trace_reconstructed_value": rebuilt[field]})

    if len(rebuilt_rows) != len(raw):
        raise RuntimeError(f"Trace/raw coverage mismatch: {len(rebuilt_rows)} trace episodes vs {len(raw)} raw episodes")
    write_csv(args.out_dir / "summaries" / "timestep_cohort_classification.csv", sorted(rebuilt_rows, key=lambda r: int(r["development_episode_id"])))
    mismatch_path = args.out_dir / "summaries" / "timestep_evaluator_mismatches.csv"
    if mismatches:
        write_csv(mismatch_path, mismatches)
    elif mismatch_path.exists():
        mismatch_path.unlink()

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rebuilt_rows:
        grouped[(row["arm"], row["seed"], row["scenario"])].append(row)
    per_seed_scenario = []
    for (arm, seed, scenario), rows in sorted(grouped.items()):
        counts = Counter(row["cohort"] for row in rows)
        per_seed_scenario.append({"arm": arm, "seed": seed, "scenario": scenario, "total": len(rows),
                                  **{name: counts[name] for name in "ABCDE"}, "strict_risk_set": counts["C"] + counts["D"],
                                  "strict_recovered": counts["C"], "strict_unrecovered": counts["D"]})
    write_csv(args.out_dir / "summaries" / "timestep_per_seed_scenario.csv", per_seed_scenario)

    arm_summary = []
    v0 = {"rule": "PHASE2IA4_RISKSET_ADEQUACY_RULE_V0", "arms": {}, "overall_pass": False}
    for arm in ARMS:
        rows = [row for row in rebuilt_rows if row["arm"] == arm]
        counts = Counter(row["cohort"] for row in rows)
        seed_risk = {str(seed): sum(row["cohort"] in ("C", "D") for row in rows if row["seed"] == str(seed)) for seed in SEEDS}
        scenario_risk = {scenario: sum(row["cohort"] in ("C", "D") for row in rows if row["scenario"] == scenario) for scenario in SCENARIOS}
        conditions = {
            "nonzero_strict_risk_set": counts["C"] + counts["D"] > 0,
            "at_least_two_seeds_with_risk": sum(value > 0 for value in seed_risk.values()) >= 2,
            "at_least_two_scenarios_with_risk": sum(value > 0 for value in scenario_risk.values()) >= 2,
            "at_least_40_total_risk_episodes": counts["C"] + counts["D"] >= 40,
            "at_least_two_seeds_with_at_least_10_risk_episodes": sum(value >= 10 for value in seed_risk.values()) >= 2,
        }
        arm_pass = all(conditions.values())
        v0["arms"][arm] = {"pass": arm_pass, "conditions": conditions, "seed_risk": seed_risk, "scenario_risk": scenario_risk}
        arm_summary.append({"arm": arm, "total": len(rows), **{name: counts[name] for name in "ABCDE"},
                            "strict_risk_set": counts["C"] + counts["D"], "strict_recovered": counts["C"],
                            "strict_unrecovered": counts["D"], "seed_risk": json.dumps(seed_risk),
                            "scenario_risk": json.dumps(scenario_risk), "v0_pass": arm_pass})
    v0["overall_pass"] = all(value["pass"] for value in v0["arms"].values()) and not mismatches
    v0["trace_coverage"] = {"raw_episode_rows": len(raw), "trace_episode_rows": len(rebuilt_rows), "trace_files": len(trace_paths)}
    v0["evaluator_mismatch_count"] = len(mismatches)
    write_csv(args.out_dir / "summaries" / "timestep_arm_summary.csv", arm_summary)
    (args.out_dir / "summaries" / "V0_RISKSET_ADEQUACY.json").write_text(json.dumps(v0, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(v0, indent=2))


if __name__ == "__main__":
    main()
