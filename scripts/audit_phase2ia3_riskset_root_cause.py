"""Phase 2I-A3 strict-risk-set root-cause audit.

This audit never trains and never changes the frozen strict endpoint.  It uses
the existing Phase 2I-A2 episode artifacts, plus explicitly labelled small
diagnostic replays from the six fixed final checkpoints.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np

from evaluate_ri_gmappo_3d import evaluate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = ROOT / "results" / "development" / "role_gate_phase2ia2"
OUT = ROOT / "results" / "development" / "phase2ia3_riskset_audit"
ARMS = ("full_gate", "no_role_gate")
SEEDS = (101, 202, 303)
SCENARIOS = (
    "dropout030_delay2_relay_failure_early",
    "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed",
    "dropout030_delay2_relay_failure_late",
)


def f(row: dict, key: str, default=float("nan")) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def truth(row: dict, key: str) -> bool:
    return f(row, key, 0.0) > 0.5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def cohort(row: dict) -> str:
    pre = truth(row, "pre_failure_chain_established")
    lost = truth(row, "chain_lost_after_failure")
    event = truth(row, "post_failure_chain_recovered_after_loss")
    first_after = truth(row, "post_failure_chain_first_established")
    if pre and lost and event:
        return "C"
    if pre and lost and not event:
        return "D"
    if pre and not lost:
        return "B"
    if not pre and first_after:
        return "E"
    return "A"


def cohort_reconstruction(raw: list[dict]) -> list[dict]:
    out = []
    for row in raw:
        c = cohort(row)
        out.append({
            "development_episode_id": row["development_episode_id"],
            "arm": row["arm"], "seed": row["train_seed"], "scenario": row["scenario"],
            "cohort": c,
            "pre_failure_chain_established": row["pre_failure_chain_established"],
            "chain_lost_after_failure": row["chain_lost_after_failure"],
            "post_failure_chain_recovered_after_loss": row["post_failure_chain_recovered_after_loss"],
            "t_failure": row["t_failure"], "t_loss": row["t_loss"],
            "t_recovery": row["t_recovery"], "delta_t_loss_to_recovery": row["delta_t_loss_to_recovery"],
            "censor_time": row["censor_time"],
            "first_chain_establishment_time_available": "False",
            "timeline_source_limitation": "Phase2IA2 raw CSV stores endpoint summaries, not timestep chain states",
        })
    return out


def aggregate_cohorts(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[(row["arm"], row["seed"], row["scenario"])].append(row)
    result = []
    for (arm, seed, scenario), items in sorted(groups.items()):
        counts = Counter(x["cohort"] for x in items)
        result.append({"arm": arm, "seed": seed, "scenario": scenario, "total": len(items),
                       "A": counts["A"], "B": counts["B"], "C": counts["C"], "D": counts["D"], "E": counts["E"],
                       "residual_invalid": 0, "strict_risk_set_C_plus_D": counts["C"] + counts["D"],
                       "strict_recovered_C": counts["C"],
                       "identity_total_equals_sum": len(items) == sum(counts[x] for x in "ABCDE")})
    return result


def endpoint_audit(raw: list[dict]) -> list[dict]:
    rows = []
    for r in raw:
        pre = truth(r, "pre_failure_chain_established")
        lost = truth(r, "chain_lost_after_failure")
        recovered = truth(r, "post_failure_chain_recovered_after_loss")
        event = truth(r, "event")
        strict_expected = pre and lost and recovered
        mismatch = []
        operational = []
        if event != strict_expected:
            mismatch.append("event_vs_strict_definition")
        if truth(r, "chain_lost_after_failure") != (f(r, "t_loss", -1) >= 0):
            mismatch.append("loss_vs_t_loss")
        # `t_recovery` can be populated by the legacy operational recovery
        # detector even when strict pre-failure eligibility is false.  Record
        # that semantic discrepancy separately; it is not a strict endpoint
        # mismatch and must not be promoted to an R1 evaluator bug.
        if (f(r, "t_recovery", -1) >= 0) != (truth(r, "post_failure_chain_recovered_after_loss") and lost and pre):
            operational.append("legacy_operational_recovery_vs_strict_recovery")
        rows.append({"development_episode_id": r["development_episode_id"], "arm": r["arm"], "seed": r["train_seed"],
                     "scenario": r["scenario"], "mismatch_fields": ";".join(mismatch),
                     "mismatch": bool(mismatch), "operational_semantic_discrepancy": ";".join(operational),
                     "classification": "strict fields consistent; legacy operational recovery field is separately recorded" if operational and not mismatch else "strict schema reconstruction; timestep independence unavailable"})
    return rows


def timing_rows(raw: list[dict]) -> list[dict]:
    rows = []
    for r in raw:
        first = f(r, "post_failure_first_chain_step", -1)
        failure = f(r, "t_failure", -1)
        relation = "before_failure" if first >= 0 and failure >= 0 and first < failure else "after_failure" if first >= 0 and failure >= 0 else "never_or_unavailable"
        rows.append({"development_episode_id": r["development_episode_id"], "arm": r["arm"], "seed": r["train_seed"],
                     "scenario": r["scenario"], "first_chain_establishment_proxy": first,
                     "t_failure": failure, "timing_relation": relation,
                     "exact_first_establishment_available": False})
    return rows


def failure_rows(raw: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for r in raw:
        groups[(r["arm"], r["train_seed"], r["scenario"])].append(r)
    out = []
    for (arm, seed, scenario), items in sorted(groups.items()):
        pre = [r for r in items if truth(r, "pre_failure_chain_established")]
        out.append({"arm": arm, "seed": seed, "scenario": scenario, "pre_established": len(pre),
                    "maintained_after_failure": sum(not truth(r, "chain_lost_after_failure") for r in pre),
                    "lost_after_failure": sum(truth(r, "chain_lost_after_failure") for r in pre),
                    "strict_recovered": sum(truth(r, "event") for r in pre),
                    "loss_time_mean": np.mean([f(r, "t_loss") for r in pre if f(r, "t_loss") >= 0]) if any(f(r, "t_loss") >= 0 for r in pre) else float("nan"),
                    "alternate_path_fields_available": False,
                    "interpretation": "summary CSV has connectivity fields but no per-edge alternate-path timeline"})
    return out


def telemetry_rows() -> list[dict]:
    output = []
    for arm in ARMS:
        for seed in SEEDS:
            path = BASE / "telemetry" / f"{arm}_seed{seed}_role_gate_telemetry.csv"
            if not path.exists():
                continue
            raw = read_csv(path)
            groups = defaultdict(list)
            for r in raw:
                groups[(r.get("relation", "unknown"), r.get("receiver_role", "unknown"), r.get("sender_role", "unknown"))].append(r)
            for (relation, receiver, sender), items in sorted(groups.items()):
                gates = [f(r, "gate_mean") for r in items]
                alpha = [f(r, "attention_mean") for r in items]
                effective = [f(r, "effective_payload_mean") for r in items]
                corr = np.corrcoef(alpha, gates)[0, 1] if len(items) > 1 and np.std(alpha) > 0 and np.std(gates) > 0 else float("nan")
                output.append({"arm": arm, "seed": seed, "relation": relation, "receiver_role": receiver, "sender_role": sender,
                               "n": len(items), "gate_mean": np.mean(gates), "gate_std": np.std(gates),
                               "attention_mean": np.mean(alpha), "attention_std": np.std(alpha),
                               "effective_payload_mean": np.mean(effective), "effective_payload_std": np.std(effective),
                               "alpha_gate_correlation": corr, "saturation_fraction_threshold_0.05_0.95": sum(x <= .05 or x >= .95 for x in gates) / len(gates),
                               "telemetry_note": "telemetry is aggregate per update/relation/role pair; no edge-level timestep trace"})
    return output


def diagnostic_args(checkpoint: Path, arm: str, seed: int, failure_start: int, no_failure: bool, episodes: int, device: str) -> SimpleNamespace:
    return SimpleNamespace(checkpoint=checkpoint, method=arm, episodes=episodes, eval_batch_size=1, seed=seed,
        base_seed=310000 + 10000 * seed + (0 if no_failure else 1000), target_policy="straight",
        communication_range_scale=1.0, communication_dropout_prob=.30, message_delay_steps=2, radar_dropout_prob=0.0,
        strict_target_sensing=True, agent_target_info_bottleneck=True, target_prior_position=(10000., 0., 5000.),
        max_target_message_age_steps=80, min_target_confidence=.20, failed_blue_agent=-1 if no_failure else 1,
        node_failure_start_step=0 if no_failure else failure_start, node_failure_duration_steps=0 if no_failure else 80,
        min_success_step=0, attack_hold_steps=4, stochastic=False, allow_random_policy=False, hidden_dim=64, role_dim=8,
        intent_dim=8, graph_encoder="multi_relation", graph_relation_ablation="none", graph_message_ablation="none",
        graph_input_ablation="none", role_gate_mode="relation_conditioned" if arm == "full_gate" else "none",
        multi_relation_global_residual_weight=1.0, device=device)


def run_replay(training_root: Path, episodes: int, device: str) -> tuple[list[dict], dict]:
    rows = []
    manifest = {"artifact_class": "DIAGNOSTIC_FEASIBILITY_ONLY", "episodes_per_arm_seed_condition": episodes,
                "conditions": ["F0_no_failure", "F1_delayed_failure_start_120"], "arms": {}, "seeds": list(SEEDS)}
    for arm in ARMS:
        for seed in SEEDS:
            checkpoint = training_root / arm / f"seed{seed}" / "actor_critic_latest.pt"
            manifest.setdefault("checkpoints", {})[f"{arm}_seed{seed}"] = {"path": str(checkpoint), "sha256": sha256(checkpoint)}
            for condition, no_failure, start in (("F0_no_failure", True, 0), ("F1_delayed_failure_start_120", False, 120)):
                print(f"replay {arm} seed={seed} condition={condition}", flush=True)
                result = evaluate(diagnostic_args(checkpoint, arm, seed, start, no_failure, episodes, device))
                for r in result:
                    r.update({"artifact_class": "DIAGNOSTIC_FEASIBILITY_ONLY", "diagnostic_condition": condition,
                              "arm": arm, "train_seed": seed, "diagnostic_episode_id": 310000 + 10000 * seed + (0 if no_failure else 1000) + int(r["episode"])})
                rows.extend(result)
    return rows, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-root", type=Path, default=BASE / "runs")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--device", default="cuda" if __import__("torch").cuda.is_available() else "cpu")
    parser.add_argument("--skip-replay", action="store_true")
    args = parser.parse_args()
    raw = read_csv(BASE / "raw_validation" / "episode_metrics.csv")
    reconstructed = cohort_reconstruction(raw)
    aggregates = aggregate_cohorts(reconstructed)
    mismatches = endpoint_audit(raw)
    timing = timing_rows(raw)
    failures = failure_rows(raw)
    telemetry = telemetry_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "episode_cohort_classification.csv", reconstructed)
    write_csv(OUT / "cohort_counts.csv", aggregates)
    write_csv(OUT / "evaluator_mismatch.csv", mismatches)
    write_csv(OUT / "first_establishment_timing.csv", timing)
    write_csv(OUT / "failure_effectiveness_summary.csv", failures)
    write_csv(OUT / "stratified_telemetry.csv", telemetry)
    replay_manifest = {"artifact_class": "DIAGNOSTIC_FEASIBILITY_ONLY", "skipped": args.skip_replay}
    if not args.skip_replay:
        replay, replay_manifest = run_replay(args.training_root, args.episodes, args.device)
        write_csv(OUT / "diagnostic_replay_episode_metrics.csv", replay)
    elif (OUT / "diagnostic_replay_manifest.json").exists():
        replay_manifest = json.loads((OUT / "diagnostic_replay_manifest.json").read_text(encoding="utf-8"))
    (OUT / "diagnostic_replay_manifest.json").write_text(json.dumps(replay_manifest, indent=2, default=str) + "\n", encoding="utf-8")
    summary = {"raw_episodes": len(raw), "cohort_rows": len(reconstructed), "mismatch_count": sum(bool(r["mismatch"]) for r in mismatches),
               "cohort_totals": dict(Counter(r["cohort"] for r in reconstructed)), "strict_risk_set": sum(r["strict_risk_set_C_plus_D"] for r in aggregates),
               "timeline_limitation": "raw Phase2IA2 artifact does not contain timestep-level chain state", "replay_artifact_class": "DIAGNOSTIC_FEASIBILITY_ONLY"}
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
