#!/usr/bin/env python3
"""T6 four-family GOOD-vs-WEAK decision-structure audit (read-only).

The script reads frozen T1 telemetry/checkpoints only.  It never constructs an
environment, calls reset/step, updates an optimizer, or writes model assets.
"""

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

from scripts.analyze_t4_support_utilization import (
    ACTION3D_TABLE, GOOD, INTERMEDIATE, SEEDS, WEAK, make_agent, mask_samples,
    parse_seed, run_actor, spearman, tvd,
)

PROTOCOL = "T6-GOOD-WEAK-SUPPORT-DECISION-STRUCTURE-V1"
FAMILIES = ("f0", "timing", "duration")
ROLES = ("scout", "relay", "attacker")
ACTION_NORM_BINS = (0.45, 0.90, 1.35)
SUPPORT_THRESHOLD = 0.50
TRANSITION_WINDOW = 12
SETTLE_WINDOW = 3


def finite_mean(values):
    values = [float(value) for value in values if value is not None and np.isfinite(value)]
    return None if not values else float(np.mean(values))


def family(scenario: str) -> str:
    return "nominal" if scenario == "nominal" else "f0" if scenario.startswith("f0") else "timing" if scenario.startswith("timing") else "duration" if scenario.startswith("duration") else "compound"


def support_quality(obs: np.ndarray) -> float:
    return float(np.mean([obs[2, 18], obs[2, 28], 1.0 - obs[2, 29], 1.0 - obs[2, 30], obs[2, 31]]))


def group_result(seed_rows, field, group):
    return finite_mean([row[field] for row in seed_rows if row["seed"] in group])


def direction(seed_rows, field, higher_is_better=True):
    good = [row[field] for row in seed_rows if row["seed"] in GOOD]
    weak = [row[field] for row in seed_rows if row["seed"] in WEAK]
    if not good or not weak or any(value is None for value in good + weak):
        return False
    return all(value > max(weak) for value in good) if higher_is_better else all(value < min(weak) for value in good)


def matched_gap(rows, value, key_fields):
    """Good-minus-weak standardization within fixed recorded-state strata."""
    bins = defaultdict(lambda: defaultdict(list))
    for row in rows:
        bins[tuple(row[name] for name in key_fields)][row["seed"]].append(row[value])
    gaps = []
    for members in bins.values():
        good = [item for seed in GOOD for item in members.get(seed, [])]
        weak = [item for seed in WEAK for item in members.get(seed, [])]
        if good and weak:
            gaps.append(float(np.mean(good) - np.mean(weak)))
    return {"matched_cells": len(gaps), "good_minus_weak": finite_mean(gaps)}


def transition_scan(path: Path, seed: int):
    """Use recorded actor inputs/actions to derive an objective transition proxy."""
    completed, current_key, episode = [], None, []

    def flush():
        nonlocal episode
        if len(episode) < SETTLE_WINDOW + 2 or episode[0]["family"] not in FAMILIES:
            episode = []
            return
        for start in range(1, len(episode)):
            if episode[start]["support_bin"] == episode[start - 1]["support_bin"]:
                continue
            # First changed realized attacker decision in a pre-fixed 12-step window.
            pre_action = episode[start - 1]["attacker_action"]
            horizon = episode[start:min(len(episode), start + TRANSITION_WINDOW)]
            changed = next((offset for offset, item in enumerate(horizon, 1) if item["attacker_action"] != pre_action), None)
            if changed is None:
                continue
            change_index = start + changed - 1
            tail = episode[change_index:min(len(episode), change_index + SETTLE_WINDOW)]
            settled = int(len(tail) == SETTLE_WINDOW and len({item["attacker_action"] for item in tail}) == 1)
            completed.append({
                "seed": seed, "family": episode[start]["family"], "phase": episode[start]["phase"],
                "t_adapt": changed, "settled": settled,
                "support_direction": episode[start]["support_bin"] - episode[start - 1]["support_bin"],
            })
            break  # One objectively defined first transition per episode.
        episode = []

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            raw = json.loads(line)
            key = (raw["scenario"], int(raw["episode_id"]))
            if current_key is not None and key != current_key:
                flush()
            current_key = key
            actor = raw["actor"]
            obs = np.asarray(actor["obs"], dtype=np.float32)
            onset, step = int(raw["scheduled_failure_onset"]), int(raw["post_step"])
            phase = "pre" if step < onset else "early" if step - onset < 20 else "later" if step - onset < 80 else "post_late"
            action_index = raw["action_index"]
            episode.append({
                "family": family(raw["scenario"]), "phase": phase,
                "support_bin": int(support_quality(obs) >= SUPPORT_THRESHOLD),
                "attacker_action": int(action_index[2]),
            })
    if episode:
        flush()
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--t2-analysis", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")

    rows, transitions, checkpoint_audit = [], [], {}
    for seed in SEEDS:
        raw_path = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}" / "raw_step_telemetry.jsonl"
        samples, sampling = parse_seed(raw_path, seed)
        agent = make_agent(samples[0], args.t1_root / "runs" / "utr_sg" / f"seed{seed}" / "actor_critic_latest.pt", seed)
        base, masked = run_actor(agent.actor, samples), run_actor(agent.actor, mask_samples(samples))
        sensitivity = tvd(base["prob"], masked["prob"])
        for index, sample in enumerate(samples):
            obs = sample["obs"]
            for role in range(3):
                expected = base["expected"][index, role]
                rows.append({
                    "seed": seed, "role": ROLES[role], "family": sample["family"], "phase": sample["phase"],
                    "progress": sample["progress"], "topology": sample["topology"], "future": sample["y"],
                    "chain": sample["chain"], "legal": sample["legal"], "visible": int(obs[role, 18] > .5),
                    "support_bin": int(support_quality(obs) >= SUPPORT_THRESHOLD),
                    "action_norm_bin": int(np.digitize(float(np.linalg.norm(expected)), ACTION_NORM_BINS)),
                    "sensitivity": float(sensitivity[index, role]), "prob": base["prob"][index, role].tolist(),
                    "expected": expected.tolist(),
                })
        transitions.extend(transition_scan(raw_path, seed))
        checkpoint_audit[str(seed)] = {"parameter_count": sum(parameter.numel() for parameter in agent.parameters()), "sampling": sampling}
        print(f"T6 processed frozen seed{seed}: {len(samples)} samples, {len([x for x in transitions if x['seed']==seed])} transitions", flush=True)

    # Family A: mask sensitivity, condition/role/magnitude/visibility standardized.
    a_rows = [row for row in rows if row["family"] in FAMILIES]
    a_match = matched_gap(a_rows, "sensitivity", ("role", "family", "phase", "progress", "topology", "support_bin", "action_norm_bin", "visible"))
    a_seed = [{"seed": seed, "value": finite_mean([row["sensitivity"] for row in a_rows if row["seed"] == seed])} for seed in SEEDS]
    a_condition = {condition: matched_gap([row for row in a_rows if row["family"] == condition], "sensitivity", ("role", "phase", "progress", "topology", "support_bin", "action_norm_bin", "visible")) for condition in FAMILIES}
    a_pass = a_match["good_minus_weak"] is not None and a_match["good_minus_weak"] > .01 and all((a_condition[name]["good_minus_weak"] or -1) > 0 for name in FAMILIES)

    # Family B/C: matched high-versus-low support action-distribution separation.
    separation_cells = []
    cell_groups = defaultdict(lambda: {0: [], 1: []})
    for row in a_rows:
        key = (row["seed"], row["role"], row["family"], row["phase"], row["progress"], row["topology"], row["action_norm_bin"], row["visible"])
        cell_groups[key][row["support_bin"]].append(row)
    for key, members in cell_groups.items():
        if not members[0] or not members[1]:
            continue
        low, high = np.mean([member["prob"] for member in members[0]], axis=0), np.mean([member["prob"] for member in members[1]], axis=0)
        separation_cells.append({"seed": key[0], "role": key[1], "family": key[2], "phase": key[3], "tvd": float(.5 * np.abs(low-high).sum())})
    c_seed = [{"seed": seed, "value": finite_mean([row["tvd"] for row in separation_cells if row["seed"] == seed])} for seed in SEEDS]
    c_condition = {condition: matched_gap([row for row in separation_cells if row["family"] == condition], "tvd", ("role", "phase")) for condition in FAMILIES}
    c_pass = len(separation_cells) >= 30 and all((c_condition[name]["good_minus_weak"] or -1) > 0 for name in FAMILIES)
    role_summary = {role: {"good": finite_mean([row["tvd"] for row in separation_cells if row["role"] == role and row["seed"] in GOOD]), "weak": finite_mean([row["tvd"] for row in separation_cells if row["role"] == role and row["seed"] in WEAK])} for role in ROLES}
    b_pass = c_pass and len({round((data["good"] or 0) - (data["weak"] or 0), 4) for data in role_summary.values()}) > 1 and all((data["good"] or 0) > (data["weak"] or np.inf) for data in role_summary.values())

    # Family D: first support-bin transition; lower latency and higher settling are good.
    d_seed = []
    for seed in SEEDS:
        values = [row for row in transitions if row["seed"] == seed]
        d_seed.append({"seed": seed, "t_adapt": finite_mean([row["t_adapt"] for row in values]), "settled": finite_mean([row["settled"] for row in values]), "n": len(values)})
    d_good_t, d_weak_t = group_result(d_seed, "t_adapt", GOOD), group_result(d_seed, "t_adapt", WEAK)
    d_good_s, d_weak_s = group_result(d_seed, "settled", GOOD), group_result(d_seed, "settled", WEAK)
    d_pass = d_good_t is not None and d_weak_t is not None and d_good_s is not None and d_weak_s is not None and d_good_t < d_weak_t and d_good_s > d_weak_s

    performance = {int(row["seed"]): row for row in json.loads(args.t2_analysis.read_text(encoding="utf-8"))["seed_summaries"]}
    a_values = {row["seed"]: row["value"] for row in a_seed}
    association = {metric: spearman([a_values[seed] for seed in SEEDS], [float(performance[seed][metric]) for seed in SEEDS]) for metric in ("J_F0", "J_OOD_mean", "J_OOD_worst", "timeout")}
    a_direction = all(value > 0 for value in [a_condition[name]["good_minus_weak"] for name in FAMILIES])
    # Candidate priority is decided before looking at text output: A only if its matched
    # and all-family tests pass and it has >=2 descriptive performance associations.
    association_count = sum(abs(value or 0.0) >= .7 for value in association.values())
    if a_pass and a_direction and association_count >= 2:
        decision, target = "D2 — MODERATE_DECISION_STRUCTURE_SIGNAL", "calibrated actor-legal support sensitivity"
    else:
        decision, target = "D3 — NO_ACTIONABLE_DECISION_STRUCTURE", None
    family_results = {
        "A": {"result": "PASS" if a_pass else "FAIL", "matched": a_match, "by_condition": a_condition, "per_seed": a_seed},
        "B": {"result": "PASS" if b_pass else "FAIL", "role_summary": role_summary, "cells": len(separation_cells)},
        "C": {"result": "PASS" if c_pass else "FAIL", "by_condition": c_condition, "per_seed": c_seed, "cells": len(separation_cells)},
        "D": {"result": "PASS" if d_pass else "FAIL", "per_seed": d_seed, "good": {"t_adapt": d_good_t, "settled": d_good_s}, "weak": {"t_adapt": d_weak_t, "settled": d_weak_s}},
    }
    result = {
        "protocol": PROTOCOL, "offline_only": True, "no_environment_constructed": True, "no_optimizer_update": True,
        "frozen_seeds": {"good": list(GOOD), "weak": list(WEAK), "intermediate": list(INTERMEDIATE)},
        "thresholds": {"support_quality": SUPPORT_THRESHOLD, "transition_window": TRANSITION_WINDOW, "settle_window": SETTLE_WINDOW, "sensitivity_gap": .01, "association_abs_spearman": .7},
        "actor_legal": ["obs direct/communication/age/confidence", "existing graph tensors", "role"],
        "diagnostic_only": ["seed rank", "condition family", "phase", "future continuity", "T2 outcomes"],
        "forbidden": ["share_obs", "failure truth actor input", "global topology/path", "future state"],
        "checkpoint_audit": checkpoint_audit, "families": family_results, "seed_association_family_A": association,
        "counterexamples": {"A": [row for row in a_seed if row["seed"] in GOOD and row["value"] is not None and row["value"] < finite_mean([item["value"] for item in a_seed if item["seed"] in WEAK])], "D": [row for row in d_seed if row["n"] == 0]},
        "decision": decision, "primary_algorithmic_target": target,
        "boundary": "D2 identifies a development-only decision-use target, not a causal mechanism or method authorization.",
    }
    args.output_root.mkdir(parents=True)
    (args.output_root / "t6_decision_structure_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "decision": decision, "family_results": {name: result["result"] for name, result in family_results.items()}}, indent=2))


if __name__ == "__main__":
    main()
