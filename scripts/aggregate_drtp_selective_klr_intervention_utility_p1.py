"""Aggregate P1 shadow records without declaring a Selective-KLR mechanism."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "drtp_selective_klr_intervention_utility_p1_freeze.json"


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("--execute required")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8")); out = args.output_root
    report = out / "diagnostics" / "intervention_utility_p1_gate"
    report.mkdir(parents=True, exist_ok=False)
    margin = float(freeze["analysis"]["practical_utility_margin"])
    seed_rows, all_events = [], []
    integrity = True
    for seed in freeze["cohorts"]["A"] + freeze["cohorts"]["B"]:
        run = out / "runs" / "drtp_sg" / f"seed{seed}"
        manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
        util_manifest = json.loads((run / "intervention_utility" / "manifest.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader((run / "intervention_utility" / "trigger_probe_events.csv").open(encoding="utf-8")))
        if manifest.get("status") != "completed" or util_manifest.get("status") != "COMPLETED": integrity = False
        by_event: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for row in rows: by_event[row["event_id"]][row["branch"]].append(row)
        event_summaries = []
        for event_id, branches in sorted(by_event.items(), key=lambda item: int(item[0])):
            accept, rollback = branches.get("accept", []), branches.get("rollback", [])
            key = lambda r: (r["base_id"], r["group"], r["condition"], r["initial_state_hash"])
            if len(accept) != len(rollback) or [key(x) for x in accept] != [key(x) for x in rollback]:
                integrity = False; continue
            failure_a = [float(row["episode_return"]) for row in accept if row["group"] != "N"]
            failure_b = [float(row["episode_return"]) for row in rollback if row["group"] != "N"]
            delta = mean(failure_b) - mean(failure_a)
            label = "beneficial_rollback" if delta >= margin else "harmful_rollback" if delta <= -margin else "near_zero"
            event_summaries.append({"seed": seed, "cohort": manifest["cohort"], "event_id": int(event_id), "update": int(accept[0]["update"]), "alarm_kl": float(accept[0]["alarm_kl"]), "accept_failure_mean": mean(failure_a), "rollback_failure_mean": mean(failure_b), "rollback_minus_accept": delta, "utility_class": label, "paired_rows": len(accept)})
        positive = sum(event["utility_class"] == "beneficial_rollback" for event in event_summaries)
        negative = sum(event["utility_class"] == "harmful_rollback" for event in event_summaries)
        seed_rows.append({"seed": seed, "cohort": manifest["cohort"], "alarms": len(event_summaries), "beneficial": positive, "harmful": negative, "near_zero": len(event_summaries)-positive-negative, "extra_probe_episodes": util_manifest.get("extra_probe_episodes", 0), "extra_probe_env_steps": util_manifest.get("extra_probe_env_steps", 0)})
        all_events.extend(event_summaries)
    cohorts = {name: [row for row in seed_rows if row["cohort"] == name] for name in ("A", "B")}
    sufficient_alarm_coverage = all(sum(row["alarms"] > 0 for row in rows) >= 2 for rows in cohorts.values())
    both_directions_observed = any(event["utility_class"] == "beneficial_rollback" for event in all_events) and any(event["utility_class"] == "harmful_rollback" for event in all_events)
    status = "INTERVENTION_UTILITY_P1_READY_FOR_REVIEW" if integrity and sufficient_alarm_coverage else "INTERVENTION_UTILITY_NO_GO"
    with (report / "p1_seed_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0])); writer.writeheader(); writer.writerows(seed_rows)
    fields = ["seed", "cohort", "event_id", "update", "alarm_kl", "accept_failure_mean", "rollback_failure_mean", "rollback_minus_accept", "utility_class", "paired_rows"]
    with (report / "p1_event_utility.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(all_events)
    decision = {"status": status, "integrity": integrity, "sufficient_alarm_coverage": sufficient_alarm_coverage, "both_directions_observed": both_directions_observed, "trigger_events": len(all_events), "independent_unit": "training_seed", "mechanism_declared": False, "selective_klr_training_authorized": False, "automatic_continuation_authorized": False}
    (report / "P1_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    text = f"# Intervention Utility P1 report\n\n**Status:** `{status}`.\n\n- Trigger events: `{len(all_events)}`\n- Integrity: `{integrity}`\n- At least two alarm-bearing seeds in each cohort: `{sufficient_alarm_coverage}`\n- Both practically beneficial and harmful rollback events observed: `{both_directions_observed}`\n- Frozen practical utility margin: `{margin}`\n\nThis is an observational shadow audit. Trigger events are not independent samples, no mechanism is declared, and no Selective-KLR training or automatic continuation is authorized.\n"
    (report / "P1_REPORT.md").write_text(text, encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report / "P1_REPORT.md")}, indent=2))


if __name__ == "__main__": main()
