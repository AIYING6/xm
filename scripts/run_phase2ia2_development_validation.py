"""Phase 2I-A2 fixed-final-checkpoint development validation executor.

This runner is intentionally isolated from canonical evaluation: it accepts only
development train seeds and writes only under results/development.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS, evaluate

OUT = ROOT / "results" / "development" / "role_gate_phase2ia2"
ARMS = {"full_gate": "relation_conditioned", "no_role_gate": "none"}
SEEDS = (101, 202, 303)
SCENARIOS = (
    ("dropout030_delay2_relay_failure_early", 25),
    ("dropout030_delay2_relay_failure", 40),
    ("dropout030_delay2_relay_failure_delayed", 55),
    ("dropout030_delay2_relay_failure_late", 70),
)


def episode_id(seed: int, scenario_index: int, episode_index: int) -> int:
    return 210000 + 10000 * seed + 1000 * scenario_index + episode_index


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_for(root: Path, arm: str, seed: int) -> Path:
    return root / arm / f"seed{seed}" / "actor_critic_latest.pt"


def eval_args(checkpoint: Path, arm: str, train_seed: int, scenario_index: int, failure_start: int, episodes: int, device: str) -> SimpleNamespace:
    # `base_seed` is the exact frozen episode-ID formula, so matched arms observe
    # identical environment initialization for each train seed/scenario/episode.
    return SimpleNamespace(
        checkpoint=checkpoint, method=arm, episodes=episodes, eval_batch_size=1,
        seed=train_seed, base_seed=episode_id(train_seed, scenario_index, 0),
        target_policy="straight", communication_range_scale=1.0,
        communication_dropout_prob=0.30, message_delay_steps=2, radar_dropout_prob=0.0,
        strict_target_sensing=True, agent_target_info_bottleneck=True,
        target_prior_position=(10000.0, 0.0, 5000.0), max_target_message_age_steps=80,
        min_target_confidence=0.20, failed_blue_agent=1,
        node_failure_start_step=failure_start, node_failure_duration_steps=80,
        min_success_step=0, attack_hold_steps=4, stochastic=False, allow_random_policy=False,
        hidden_dim=64, role_dim=8, intent_dim=8, graph_encoder="multi_relation",
        graph_relation_ablation="none", graph_message_ablation="none",
        role_gate_mode=ARMS[arm], graph_input_ablation="none",
        multi_relation_global_residual_weight=1.0, device=device,
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def mean(rows: Iterable[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if str(row.get(key, "")) != ""]
    return float(np.mean(values)) if values else float("nan")


def conditional_recovery_time(rows: list[dict]) -> float:
    return mean([r for r in rows if float(r["event"]) > 0.5], "delta_t_loss_to_recovery")


def summary_rows(raw: list[dict], training_root: Path) -> tuple[list[dict], list[dict]]:
    groups: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
    for row in raw:
        groups[(row["arm"], int(row["train_seed"]), row["scenario"])].append(row)
    per_seed = []
    for (arm, seed, scenario), rows in sorted(groups.items()):
        risk = [r for r in rows if float(r["pre_failure_chain_established"]) > 0.5 and float(r["chain_lost_after_failure"]) > 0.5]
        recovered = [r for r in risk if float(r["post_failure_chain_recovered_after_loss"]) > 0.5]
        summary = {
            "arm": arm, "train_seed": seed, "scenario": scenario, "total_episodes": len(rows),
            "pre_failure_chain_established": int(sum(float(r["pre_failure_chain_established"]) > 0.5 for r in rows)),
            "chain_lost_after_failure": int(sum(float(r["chain_lost_after_failure"]) > 0.5 for r in rows)),
            "strict_risk_set_size": len(risk), "recovered_count": len(recovered),
            "unrecovered_count": len(risk) - len(recovered),
            "recovery_probability": len(recovered) / len(risk) if risk else float("nan"),
            "conditional_recovery_time": conditional_recovery_time(recovered),
            "mean_t_loss": mean(risk, "t_loss"), "mean_t_recovery": mean(recovered, "t_recovery"),
            "mean_delta_t_loss_to_recovery": conditional_recovery_time(recovered),
            "success_rate": mean(rows, "success"), "collision_rate": mean(rows, "collision"), "timeout_rate": mean(rows, "timeout"),
        }
        summary.update(training_stability(training_root, arm, seed))
        summary.update({f"telemetry_{key}": value for key, value in telemetry_summary(training_root, arm, seed).items()})
        per_seed.append(summary)
    scenario_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in per_seed:
        scenario_groups[(row["arm"], row["scenario"])].append(row)
    per_scenario = []
    for (arm, scenario), rows in sorted(scenario_groups.items()):
        totals = sum(int(r["total_episodes"]) for r in rows)
        risks = sum(int(r["strict_risk_set_size"]) for r in rows)
        recovered = sum(int(r["recovered_count"]) for r in rows)
        per_scenario.append({
            "arm": arm, "scenario": scenario, "seed_count": len(rows), "total_episodes": totals,
            "strict_risk_set_size": risks, "recovered_count": recovered, "unrecovered_count": risks - recovered,
            "recovery_probability": recovered / risks if risks else float("nan"),
            "conditional_recovery_time_mean_across_seeds": mean(rows, "conditional_recovery_time"),
            "success_rate_mean_across_seeds": mean(rows, "success_rate"),
            "collision_rate_mean_across_seeds": mean(rows, "collision_rate"), "timeout_rate_mean_across_seeds": mean(rows, "timeout_rate"),
        })
    return per_seed, per_scenario


def training_stability(training_root: Path, arm: str, seed: int) -> dict:
    path = training_root / arm / f"seed{seed}" / "train_log.csv"
    if not path.exists():
        return {"train_log_present": False}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    keys = ("loss", "approx_kl", "grad_norm", "explained_variance", "role_gate_grad_norm", "role_gate_displacement_l2")
    result = {"train_log_present": True, "updates_logged": len(rows)}
    for key in keys:
        values = [float(r[key]) for r in rows if r.get(key, "") not in ("", None)]
        result[f"{key}_mean"] = float(np.mean(values)) if values else float("nan")
        result[f"{key}_final"] = values[-1] if values else float("nan")
    return result


def telemetry_summary(training_root: Path, arm: str, seed: int) -> dict:
    path = training_root / arm / f"seed{seed}" / "role_gate_telemetry.csv"
    if not path.exists():
        return {"telemetry_present": False}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    alpha = np.asarray([float(r["attention_mean"]) for r in rows])
    gate = np.asarray([float(r["gate_mean"]) for r in rows])
    effective = np.asarray([float(r["effective_payload_mean"]) for r in rows])
    corr = float(np.corrcoef(alpha, gate)[0, 1]) if len(rows) > 1 and np.std(alpha) > 0 and np.std(gate) > 0 else float("nan")
    return {
        "telemetry_present": True, "telemetry_rows": len(rows), "attention_gate_correlation": corr,
        "gate_mean": float(np.mean(gate)), "gate_std": float(np.std(gate)),
        "effective_payload_mean": float(np.mean(effective)), "effective_payload_std": float(np.std(effective)),
    }


def build_arm_comparison(per_seed: list[dict], training_root: Path) -> list[dict]:
    by_key = {(r["train_seed"], r["scenario"], r["arm"]): r for r in per_seed}
    rows = []
    for seed in SEEDS:
        for scenario, _ in SCENARIOS:
            full, no_gate = by_key.get((seed, scenario, "full_gate")), by_key.get((seed, scenario, "no_role_gate"))
            if full is None or no_gate is None:
                continue
            row = {"train_seed": seed, "scenario": scenario}
            for key in ("recovery_probability", "conditional_recovery_time", "success_rate", "collision_rate", "timeout_rate"):
                row[f"full_gate_{key}"] = full[key]
                row[f"no_role_gate_{key}"] = no_gate[key]
                row[f"delta_{key}"] = float(full[key]) - float(no_gate[key]) if np.isfinite(float(full[key])) and np.isfinite(float(no_gate[key])) else float("nan")
            rows.append(row)
    return rows


def write_report(path: Path, per_seed: list[dict], comparisons: list[dict], training_root: Path) -> None:
    complete = len(per_seed) == len(ARMS) * len(SEEDS) * len(SCENARIOS)
    lines = ["# Phase 2I-A2 Role-Gate efficacy report", "", "**Artifact class:** DEVELOPMENT_ONLY", "", "## Status", ""]
    if not complete:
        lines += ["`INCOMPLETE / ARCHITECTURE FREEZE NO-GO`", "", "Not all six fixed-final-checkpoint development validations are present. No retention decision is permitted."]
    else:
        lines += ["`PENDING PREDECLARED RETENTION-RULE REVIEW`", "", "This executor reports diagnostics only. The four retention conditions in `PHASE2IA2_ROLE_GATE_EFFICACY_PROTOCOL.md` must be checked without changing seeds, endpoints, or scenarios."]
    lines += ["", "## Paired development validation", "", f"- Per-seed/scenario rows: {len(per_seed)}", f"- Arm-comparison rows: {len(comparisons)}", "- Episode IDs use `210000 + 10000 × seed + 1000 × scenario_index + episode_index`.", "- Checkpoints are fixed `actor_critic_latest.pt`; no validation checkpoint selection occurs.", "", "## Telemetry", ""]
    for seed in SEEDS:
        telemetry = telemetry_summary(training_root, "full_gate", seed)
        lines.append(f"- seed {seed}: alpha/g correlation = {telemetry.get('attention_gate_correlation', float('nan')):.6g}; gate SD = {telemetry.get('gate_std', float('nan')):.6g}; telemetry present = {telemetry.get('telemetry_present', False)}")
    lines += ["", "## Boundary", "", "No KM/RMST, primary endpoint claim, canonical test result, or manuscript headline is produced here.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    if any(seed not in SEEDS for seed in args.seeds):
        raise ValueError("Phase 2I-A2 accepts only frozen development seeds 101, 202, 303")
    out = args.out_dir
    raw: list[dict] = []
    manifest = {"artifact_class": "DEVELOPMENT_ONLY", "checkpoint_rule": "fixed_final_actor_critic_latest", "episodes_per_seed_scenario": args.episodes, "arms": {}, "scenarios": [name for name, _ in SCENARIOS]}
    for arm in args.arms:
        manifest["arms"][arm] = {"role_gate_mode": ARMS[arm], "seeds": {}}
        for seed in args.seeds:
            checkpoint = checkpoint_for(args.training_root, arm, seed)
            if not checkpoint.exists():
                raise FileNotFoundError(f"Missing fixed final checkpoint: {checkpoint}")
            manifest["arms"][arm]["seeds"][str(seed)] = {"checkpoint": str(checkpoint.relative_to(ROOT)), "sha256": sha256(checkpoint)}
            for scenario_index, (scenario, failure_start) in enumerate(SCENARIOS):
                rows = evaluate(eval_args(checkpoint, arm, seed, scenario_index, failure_start, args.episodes, args.device))
                for row in rows:
                    row.update({"artifact_class": "DEVELOPMENT_ONLY", "arm": arm, "train_seed": seed, "scenario": scenario, "scenario_index": scenario_index, "development_episode_id": episode_id(seed, scenario_index, int(row["episode"]))})
                    raw.append(row)
    raw.sort(key=lambda r: (r["arm"], r["train_seed"], r["scenario_index"], r["episode"]))
    raw_path = out / "raw_validation" / "episode_metrics.csv"
    write_csv(raw_path, raw)
    per_seed, per_scenario = summary_rows(raw, args.training_root)
    comparisons = build_arm_comparison(per_seed, args.training_root)
    write_csv(out / "summaries" / "per_seed.csv", per_seed)
    write_csv(out / "summaries" / "per_scenario.csv", per_scenario)
    write_csv(out / "summaries" / "arm_comparison.csv", comparisons)
    telemetry_dir = out / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    for arm in args.arms:
        for seed in args.seeds:
            source = args.training_root / arm / f"seed{seed}" / "role_gate_telemetry.csv"
            if source.exists():
                shutil.copy2(source, telemetry_dir / f"{arm}_seed{seed}_role_gate_telemetry.csv")
    manifest["raw_validation_sha256"] = sha256(raw_path)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_report(ROOT / "docs" / "PHASE2IA2_ROLE_GATE_EFFICACY_REPORT.md", per_seed, comparisons, args.training_root)
    print(out / "manifest.json")


def self_test(device: str) -> None:
    """Check paired development IDs and deterministic rollout replay without artifacts."""
    assert episode_id(101, 0, 0) == 1_220_000
    assert episode_id(303, 3, 49) == 3_243_049
    checkpoint = ROOT / "results" / "development" / "phase2ia2" / "smoke" / "seed909" / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError("self-test checkpoint is absent; run the engineering smoke setup first")
    _, failure_start = SCENARIOS[0]
    first = evaluate(eval_args(checkpoint, "full_gate", 101, 0, failure_start, 1, device))[0]
    second = evaluate(eval_args(checkpoint, "full_gate", 101, 0, failure_start, 1, device))[0]
    keys = ("success", "collision", "timeout", "event", "t_loss", "t_recovery", "delta_t_loss_to_recovery")
    if any(first[key] != second[key] for key in keys):
        raise AssertionError("development validation replay is not deterministic")
    for required in (
        "pre_failure_chain_established", "chain_lost_after_failure", "post_failure_chain_recovered_after_loss",
        "t_loss", "t_recovery", "delta_t_loss_to_recovery", "event", "censor_time",
    ):
        if required not in first:
            raise AssertionError(f"raw endpoint schema missing {required}")
    print("Phase 2I-A2 executor self-test: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-root", type=Path, default=ROOT / "results" / "development" / "phase2ia2")
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--arms", nargs="+", choices=tuple(ARMS), default=list(ARMS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(SEEDS))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(args.device)
        return
    run(args)


if __name__ == "__main__":
    main()
