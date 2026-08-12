"""Phase 2I-A4 fixed-final-checkpoint DEVELOPMENT_ONLY validation.

Writes a new namespace and preserves timestep-level traces for independent
cohort reconstruction. No canonical seeds/results are accepted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS, evaluate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "development" / "role_gate_phase2ia4"
ARMS = {"full_gate": "relation_conditioned", "no_role_gate": "none"}
SEEDS = (101, 202, 303)
SCENARIOS = (
    ("dropout030_delay2_relay_failure_early", 25),
    ("dropout030_delay2_relay_failure", 40),
    ("dropout030_delay2_relay_failure_delayed", 55),
    ("dropout030_delay2_relay_failure_late", 70),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def episode_id(seed: int, scenario_index: int, episode: int) -> int:
    return 410000 + 10000 * seed + 1000 * scenario_index + episode


def args_for(checkpoint: Path, arm: str, seed: int, scenario_index: int, failure_start: int, episodes: int, device: str, trace: Path) -> SimpleNamespace:
    return SimpleNamespace(checkpoint=checkpoint, method=arm, episodes=episodes, eval_batch_size=1, seed=seed,
        base_seed=episode_id(seed, scenario_index, 0), episode_id_base=episode_id(seed, scenario_index, 0),
        target_policy="straight", communication_range_scale=1.0, communication_dropout_prob=.30,
        message_delay_steps=2, radar_dropout_prob=0.0, strict_target_sensing=True,
        agent_target_info_bottleneck=True, target_prior_position=(10000., 0., 5000.), max_target_message_age_steps=80,
        min_target_confidence=.20, failed_blue_agent=1, node_failure_start_step=failure_start,
        node_failure_duration_steps=80, min_success_step=0, attack_hold_steps=4, stochastic=False,
        allow_random_policy=False, hidden_dim=64, role_dim=8, intent_dim=8, graph_encoder="multi_relation",
        graph_relation_ablation="none", graph_message_ablation="none", graph_input_ablation="none",
        role_gate_mode=ARMS[arm], multi_relation_global_residual_weight=1.0, device=device,
        timestep_trace_path=trace)


def run(args: argparse.Namespace) -> tuple[list[dict], dict]:
    raw = []
    manifest = {"artifact_class": "DEVELOPMENT_ONLY", "checkpoint_rule": "fixed_final_actor_critic_latest",
                "episode_id_formula": "410000 + 10000 * seed + 1000 * scenario_index + episode_index",
                "episodes_per_seed_scenario": args.episodes, "arms": {}, "scenarios": [x[0] for x in SCENARIOS]}
    for arm in args.arms:
        manifest["arms"][arm] = {"role_gate_mode": ARMS[arm], "seeds": {}}
        for seed in args.seeds:
            checkpoint = args.training_root / arm / f"seed{seed}" / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            manifest["arms"][arm]["seeds"][str(seed)] = {"checkpoint": str(checkpoint.relative_to(ROOT)), "sha256": sha256(checkpoint)}
            for scenario_index, (scenario, failure_start) in enumerate(SCENARIOS):
                trace = args.out_dir / "raw_timestep_chain" / f"{arm}_seed{seed}_{scenario}.csv"
                result = evaluate(args_for(checkpoint, arm, seed, scenario_index, failure_start, args.episodes, args.device, trace))
                for row in result:
                    row.update({"artifact_class": "DEVELOPMENT_ONLY", "arm": arm, "train_seed": seed,
                                "scenario": scenario, "scenario_index": scenario_index,
                                "development_episode_id": episode_id(seed, scenario_index, int(row["episode"]))})
                raw.extend(result)
    return raw, manifest


def classify(row: dict) -> str:
    pre = float(row["pre_failure_chain_established"]) > .5
    lost = float(row["chain_lost_after_failure"]) > .5
    rec = float(row["post_failure_chain_recovered_after_loss"]) > .5
    after = float(row["post_failure_chain_first_established"]) > .5
    if pre and lost and rec: return "C"
    if pre and lost: return "D"
    if pre: return "B"
    if after: return "E"
    return "A"


def summarize(raw: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    cohorts = []
    for r in raw:
        cohorts.append({"development_episode_id": r["development_episode_id"], "arm": r["arm"], "seed": r["train_seed"],
                        "scenario": r["scenario"], "cohort": classify(r), "t_failure": r["t_failure"], "t_loss": r["t_loss"],
                        "t_recovery": r["t_recovery"], "delta_t_loss_to_recovery": r["delta_t_loss_to_recovery"],
                        "event": r["event"], "censor_time": r["censor_time"]})
    groups = defaultdict(list)
    for r in cohorts: groups[(r["arm"], r["seed"], r["scenario"])].append(r)
    per_scenario = []
    for key, rows in sorted(groups.items()):
        c = Counter(r["cohort"] for r in rows)
        per_scenario.append({"arm": key[0], "seed": key[1], "scenario": key[2], "total": len(rows), **{x: c[x] for x in "ABCDE"},
                             "strict_risk_set": c["C"] + c["D"], "strict_recovered": c["C"]})
    arms = []
    for arm in ARMS:
        rows = [r for r in cohorts if r["arm"] == arm]
        c = Counter(r["cohort"] for r in rows)
        seed_counts = {s: sum(r["cohort"] in ("C", "D") for r in rows if r["seed"] == str(s)) for s in SEEDS}
        scenario_counts = {s: sum(r["cohort"] in ("C", "D") for r in rows if r["scenario"] == s) for s, _ in SCENARIOS}
        arms.append({"arm": arm, "total": len(rows), **{x: c[x] for x in "ABCDE"}, "strict_risk_set": c["C"] + c["D"],
                     "strict_recovered": c["C"], "risk_seeds": sum(v > 0 for v in seed_counts.values()),
                     "risk_scenarios": sum(v > 0 for v in scenario_counts.values()), "seed_counts": json.dumps(seed_counts),
                     "scenario_counts": json.dumps(scenario_counts)})
    return cohorts, per_scenario, arms


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--training-root", type=Path, default=ROOT / "results" / "development" / "role_gate_phase2ia4" / "runs")
    p.add_argument("--out-dir", type=Path, default=OUT)
    p.add_argument("--episodes", type=int, default=50)
    p.add_argument("--device", default="cuda")
    p.add_argument("--arms", nargs="+", choices=tuple(ARMS), default=list(ARMS))
    p.add_argument("--seeds", nargs="+", type=int, choices=SEEDS, default=list(SEEDS))
    args = p.parse_args()
    raw, manifest = run(args)
    write_csv(args.out_dir / "raw_validation" / "episode_metrics.csv", raw)
    cohorts, per_scenario, arms = summarize(raw)
    write_csv(args.out_dir / "summaries" / "cohort_classification.csv", cohorts)
    write_csv(args.out_dir / "summaries" / "per_seed_scenario.csv", per_scenario)
    write_csv(args.out_dir / "summaries" / "arm_summary.csv", arms)
    manifest["raw_validation_sha256"] = sha256(args.out_dir / "raw_validation" / "episode_metrics.csv")
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(arms, indent=2))


if __name__ == "__main__": main()
