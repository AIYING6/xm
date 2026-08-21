#!/usr/bin/env python3
"""Read-only T7 test of state-conditioned support-sensitivity calibration."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_t4_support_utilization import GOOD, INTERMEDIATE, SEEDS, WEAK, make_agent, mask_samples, parse_seed, run_actor, tvd

PROTOCOL = "T7-CALIBRATED-SUPPORT-SENSITIVITY-PREMISE-V1"
FAMILIES = ("f0", "timing", "duration")
QUALITY_LOW_MAX = 0.40
QUALITY_HIGH_MIN = 0.60


def family(scenario: str) -> str:
    if scenario.startswith("f0"):
        return "f0"
    if scenario.startswith("timing"):
        return "timing"
    if scenario.startswith("duration"):
        return "duration"
    return "other"


def quality(obs: np.ndarray) -> float:
    """Fixed actor-legal support reliability summary from the T4/T6 contract."""
    return float(np.mean([obs[2, 18], obs[2, 28], 1.0 - obs[2, 29], 1.0 - obs[2, 30], obs[2, 31]]))


def mean(values):
    values = [float(value) for value in values if np.isfinite(value)]
    return None if not values else float(np.mean(values))


def high_low_gap(values):
    low = [row["sensitivity"] for row in values if row["quality"] <= QUALITY_LOW_MAX]
    high = [row["sensitivity"] for row in values if row["quality"] >= QUALITY_HIGH_MIN]
    return {"n_low": len(low), "n_high": len(high), "low": mean(low), "high": mean(high), "high_minus_low": None if not low or not high else float(np.mean(high) - np.mean(low))}


def matched_gap(values):
    """Quality effect inside role/time/topology/action-size/visibility strata."""
    groups = defaultdict(lambda: {"low": [], "high": []})
    for row in values:
        key = (row["seed"], row["family"], row["phase"], row["progress"], row["topology"], row["action_norm_bin"], row["visible"])
        if row["quality"] <= QUALITY_LOW_MAX:
            groups[key]["low"].append(row["sensitivity"])
        elif row["quality"] >= QUALITY_HIGH_MIN:
            groups[key]["high"].append(row["sensitivity"])
    cells = []
    for key, members in groups.items():
        if members["low"] and members["high"]:
            cells.append({"seed": key[0], "family": key[1], "phase": key[2], "gap": float(np.mean(members["high"]) - np.mean(members["low"]))})
    return cells


def group_mean(rows, seeds, field):
    return mean([row[field] for row in rows if row["seed"] in seeds and row[field] is not None])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t1-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")

    rows, checkpoint_audit = [], {}
    for seed in SEEDS:
        raw_path = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}" / "raw_step_telemetry.jsonl"
        samples, sampling = parse_seed(raw_path, seed)
        agent = make_agent(samples[0], args.t1_root / "runs" / "utr_sg" / f"seed{seed}" / "actor_critic_latest.pt", seed)
        base = run_actor(agent.actor, samples)
        masked = run_actor(agent.actor, mask_samples(samples))
        sensitivity = tvd(base["prob"], masked["prob"])
        for index, sample in enumerate(samples):
            obs = sample["obs"]
            expected = base["expected"][index, 2]
            rows.append({
                "seed": seed, "family": sample["family"], "phase": sample["phase"], "progress": sample["progress"],
                "topology": sample["topology"], "visible": int(obs[2, 18] > .5), "quality": quality(obs),
                "action_norm_bin": int(np.digitize(float(np.linalg.norm(expected)), (0.45, 0.90, 1.35))),
                "sensitivity": float(sensitivity[index, 2]),
            })
        checkpoint_audit[str(seed)] = {"parameters": sum(parameter.numel() for parameter in agent.parameters()), "sampling": sampling}
        print(f"processed frozen seed{seed}", flush=True)

    rows = [row for row in rows if row["family"] in FAMILIES]
    raw_by_seed = []
    for seed in SEEDS:
        item = high_low_gap([row for row in rows if row["seed"] == seed])
        item["seed"] = seed
        raw_by_seed.append(item)
    cells = matched_gap(rows)
    matched_by_seed = []
    for seed in SEEDS:
        gaps = [row["gap"] for row in cells if row["seed"] == seed]
        matched_by_seed.append({"seed": seed, "matched_cells": len(gaps), "quality_conditioned_gap": mean(gaps)})
    by_condition = {}
    for condition in FAMILIES:
        scoped = [row for row in cells if row["family"] == condition]
        by_condition[condition] = {
            "matched_cells": len(scoped),
            "good": group_mean(scoped, GOOD, "gap"), "intermediate": group_mean(scoped, INTERMEDIATE, "gap"), "weak": group_mean(scoped, WEAK, "gap"),
            "good_minus_weak": None if group_mean(scoped, GOOD, "gap") is None or group_mean(scoped, WEAK, "gap") is None else group_mean(scoped, GOOD, "gap") - group_mean(scoped, WEAK, "gap"),
        }
    by_phase = {}
    for phase in ("pre", "early", "later"):
        scoped = [row for row in cells if row["phase"] == phase]
        by_phase[phase] = {"matched_cells": len(scoped), "good": group_mean(scoped, GOOD, "gap"), "weak": group_mean(scoped, WEAK, "gap")}

    seed_map = {row["seed"]: row["quality_conditioned_gap"] for row in matched_by_seed}
    good = [seed_map[seed] for seed in GOOD]
    weak = [seed_map[seed] for seed in WEAK]
    intermediate = seed_map[INTERMEDIATE[0]]
    # All five tests and their directional rule are fixed before result interpretation.
    tests = {
        "test1_state_conditioned_structure": all(value is not None and value > 0 for value in good),
        "test2_seed_ordering": all(value is not None for value in good + weak + [intermediate]) and min(good) > max(weak) and intermediate > min(weak),
        "test3_cross_condition": all(info["good_minus_weak"] is not None and info["good_minus_weak"] > 0 for info in by_condition.values()),
        "test4_transition_relevance": by_phase["early"]["good"] is not None and by_phase["pre"]["good"] is not None and by_phase["early"]["good"] >= by_phase["pre"]["good"],
        "test5_matched_control": all(row["matched_cells"] > 0 and row["quality_conditioned_gap"] is not None for row in matched_by_seed),
    }
    premise_pass = all(tests.values())
    result = {
        "protocol": PROTOCOL, "offline_only": True, "no_environment_constructed": True, "no_optimizer_update": True,
        "actor_legal_support_components": ["direct detection", "inbound connectivity", "inverse inbound age", "inverse cache age", "cache confidence"],
        "diagnostic_only": ["GOOD/WEAK/INTERMEDIATE labels", "condition family", "phase", "T2 outcome labels"],
        "thresholds": {"low_max": QUALITY_LOW_MAX, "high_min": QUALITY_HIGH_MIN},
        "checkpoint_audit": checkpoint_audit, "raw_by_seed": raw_by_seed, "matched_by_seed": matched_by_seed,
        "by_condition": by_condition, "by_phase": by_phase, "tests": tests,
        "premise": "PASS" if premise_pass else "FAIL",
        "interpretation": "A PASS supports a state-conditional calibration reference; a FAIL prohibits a calibration method whose target is only legal support quality.",
    }
    args.output_root.mkdir(parents=True)
    (args.output_root / "t7_calibration_premise.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "premise": result["premise"], "tests": tests}, indent=2))


if __name__ == "__main__":
    main()
