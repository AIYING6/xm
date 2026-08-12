"""Independent Phase 2IA5 E0 trace/reconstruction and adequacy audit."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "development" / "role_gate_phase2ia5_e0"
ARMS = ("full_gate", "no_role_gate")
SEEDS = (101, 202, 303)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"Refusing to write empty audit table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def yes(value: str) -> bool:
    return float(value) > 0.5


def time_or_none(value: str) -> int | None:
    value = float(value)
    return None if value < 0 else int(round(value))


def same_time(raw: str, rebuilt: int | None) -> bool:
    return time_or_none(raw) == rebuilt


def reconstructed(timeline: list[dict[str, str]]) -> dict:
    timeline = sorted(timeline, key=lambda row: int(row["timestep"]))
    active = next((row for row in timeline if yes(row["node_failure_active"])), None)
    failure = int(active["timestep"]) if active is not None else None
    before = timeline if failure is None else [row for row in timeline if int(row["timestep"]) < failure]
    after = [] if failure is None else [row for row in timeline if int(row["timestep"]) >= failure]
    pre = any(yes(row["chain_valid_t"]) for row in before)
    loss_row = next((row for row in after if not yes(row["chain_valid_t"])), None)
    loss = loss_row is not None
    loss_time = int(loss_row["timestep"]) if loss_row is not None else None
    recovery_row = next((row for row in after if loss_time is not None and int(row["timestep"]) > loss_time and yes(row["chain_valid_t"])), None)
    recovery_time = int(recovery_row["timestep"]) if recovery_row is not None else None
    recovered = pre and loss and recovery_time is not None
    return {
        "t_failure": failure, "pre_failure_chain_established": int(pre),
        "chain_lost_after_failure": int(loss),
        "t_loss": loss_time, "t_recovery": recovery_time,
        "post_failure_chain_recovered_after_loss": int(recovered),
        "event": int(recovered), "delta_t_loss_to_recovery": recovery_time - loss_time if recovered else None,
        "censor_time": int(timeline[-1]["timestep"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    raw = read_csv(args.out_dir / "raw_validation" / "episode_metrics.csv")
    expected_rows = len(ARMS) * len(SEEDS) * 100
    if len(raw) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} raw rows, found {len(raw)}")
    raw_by_key = {(row["arm"], row["development_episode_id"]): row for row in raw}
    if len(raw_by_key) != len(raw):
        raise RuntimeError("Duplicate (arm, episode ID) rows")

    reconstructed_rows, mismatches = [], []
    trace_files = sorted((args.out_dir / "raw_timestep_chain").glob("*.csv"))
    for trace_path in trace_files:
        arm = next((candidate for candidate in ARMS if trace_path.name.startswith(candidate + "_")), None)
        if arm is None:
            raise RuntimeError(f"Cannot infer arm: {trace_path.name}")
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in read_csv(trace_path):
            grouped[row["episode_id"]].append(row)
        for dev_id, timeline in grouped.items():
            source = raw_by_key.get((arm, dev_id))
            if source is None:
                raise RuntimeError(f"Trace-only observation: {arm}/{dev_id}")
            rebuild = reconstructed(timeline)
            trigger = time_or_none(source["eligibility_trigger_step"])
            actual_start = time_or_none(source["actual_failure_start_step"])
            eligible = yes(source["eligible_before_cap"])
            checks = {
                "eligibility_flag_vs_trigger": eligible == (trigger is not None and trigger <= 220),
                "trigger_hold_cap": trigger is None or 4 <= trigger <= 220,
                "failure_start_vs_trigger": (actual_start == trigger + 1) if trigger is not None and trigger <= 220 else actual_start is None,
                "trace_failure_start": same_time(source["t_failure"], rebuild["t_failure"]),
                # Without an injected failure the legacy endpoint API writes
                # -1 (not applicable), whereas trace reconstruction retains
                # an observational false.  This is an applicability sentinel,
                # not an endpoint mismatch.
                "trace_pre": (float(source["pre_failure_chain_established"]) < 0 and rebuild["t_failure"] is None)
                or int(float(source["pre_failure_chain_established"])) == rebuild["pre_failure_chain_established"],
                "trace_loss": int(float(source["chain_lost_after_failure"])) == rebuild["chain_lost_after_failure"],
                "trace_recovery": (float(source["post_failure_chain_recovered_after_loss"]) < 0 and rebuild["t_failure"] is None)
                or int(float(source["post_failure_chain_recovered_after_loss"])) == rebuild["post_failure_chain_recovered_after_loss"],
                "trace_t_loss": same_time(source["t_loss"], rebuild["t_loss"]),
                "trace_t_recovery": same_time(source["t_recovery"], rebuild["t_recovery"]),
                "trace_event": int(float(source["event"])) == rebuild["event"],
            }
            for field, passed in checks.items():
                if not passed:
                    mismatches.append({"development_episode_id": dev_id, "arm": arm, "seed": source["train_seed"], "field": field,
                                       "raw": source.get(field, "endpoint field"), "reconstructed": json.dumps(rebuild)})
            reconstructed_rows.append({"development_episode_id": dev_id, "arm": arm, "seed": source["train_seed"],
                                       "eligible_before_cap": int(eligible), "eligibility_trigger_step": trigger if trigger is not None else "",
                                       "actual_failure_start_step": actual_start if actual_start is not None else "", **rebuild})
    if len(reconstructed_rows) != len(raw):
        raise RuntimeError(f"Trace coverage mismatch: {len(reconstructed_rows)} traces vs {len(raw)} raw rows")
    summary_rows = []
    e0 = {"protocol": "PHASE2IA5-ETF-V1", "arms": {}, "overall_pass": False,
          "raw_episode_rows": len(raw), "trace_episode_rows": len(reconstructed_rows), "trace_files": len(trace_files),
          "mismatch_count": len(mismatches)}
    for arm in ARMS:
        rows = [row for row in reconstructed_rows if row["arm"] == arm]
        eligible_by_seed = {str(seed): sum(row["eligible_before_cap"] for row in rows if row["seed"] == str(seed)) for seed in SEEDS}
        loss = sum(row["eligible_before_cap"] and row["chain_lost_after_failure"] for row in rows)
        conditions = {
            "at_least_40_eligible": sum(eligible_by_seed.values()) >= 40,
            "eligibility_in_at_least_two_seeds": sum(value > 0 for value in eligible_by_seed.values()) >= 2,
            "two_seeds_each_at_least_10_eligible": sum(value >= 10 for value in eligible_by_seed.values()) >= 2,
            "at_least_one_eligible_observed_loss": loss >= 1,
            "trace_and_endpoint_consistency": not mismatches,
        }
        arm_pass = all(conditions.values())
        e0["arms"][arm] = {"pass": arm_pass, "eligible_by_seed": eligible_by_seed, "eligible_total": sum(eligible_by_seed.values()),
                            "eligible_with_observed_loss": loss, "conditions": conditions}
        summary_rows.append({"arm": arm, "episodes": len(rows), "eligible_total": sum(eligible_by_seed.values()),
                             "eligible_seed101": eligible_by_seed["101"], "eligible_seed202": eligible_by_seed["202"],
                             "eligible_seed303": eligible_by_seed["303"], "eligible_with_observed_loss": loss, "E0_pass": arm_pass})
    e0["overall_pass"] = all(e0["arms"][arm]["pass"] for arm in ARMS)
    write_csv(args.out_dir / "summaries" / "E0_trace_reconstruction.csv", reconstructed_rows)
    write_csv(args.out_dir / "summaries" / "E0_arm_summary.csv", summary_rows)
    if mismatches:
        write_csv(args.out_dir / "summaries" / "E0_mismatches.csv", mismatches)
    (args.out_dir / "summaries" / "E0_ADEQUACY.json").write_text(json.dumps(e0, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(e0, indent=2))


if __name__ == "__main__":
    main()
