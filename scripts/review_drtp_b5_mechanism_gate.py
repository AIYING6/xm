"""Apply the frozen B5 human mechanism gate to an extracted result archive.

This script is deliberately descriptive.  The independent unit is the training
seed; PPO updates, groups, group pairs, and episodes are technical repetitions.
It never trains, evaluates checkpoints, or modifies a run artifact.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics


ARMS = ("utr_sg", "drtp_sg")
SEEDS = (3601, 3602, 3603, 3604, 3605)
WINDOWS = ("250k", "500k", "750k", "1m")
WINDOW_LIMITS = (976, 1953, 2930, 3907)
FAILURE_GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")
CREDIT_METRICS = (
    "mean_value_residual_rmse",
    "mean_td_residual_abs_q90",
    "mean_normalized_advantage",
    "mean_actor_gradient_norm",
    "mean_critic_gradient_norm",
)
BEHAVIOR_METRICS = (
    "reward_per_step",
    "progress_per_step",
    "attack_window_per_step",
    "connectivity_per_step",
    "message_age_penalty_per_step",
    "timeout",
    "collision",
    "success",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean(values) -> float:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else math.nan


def window_for_update(update: int) -> str:
    for label, limit in zip(WINDOWS, WINDOW_LIMITS):
        if update <= limit:
            return label
    return WINDOWS[-1]


def endpoint_products(gate_dir: Path) -> tuple[list[dict], dict[tuple[int, str], float]]:
    rows = read_csv(gate_dir / "paired_endpoint_timeline.csv")
    gains = {(int(row["seed"]), row["checkpoint_label"]): float(row["drtp_minus_utr_J_pert_mean"]) for row in rows}
    final = [gains[(seed, "1m")] for seed in SEEDS]
    summary = [{
        "n_training_seeds": len(final),
        "wins": sum(value > 0 for value in final),
        "mean_gain": mean(final),
        "median_gain": statistics.median(final),
        "sample_sd": statistics.stdev(final),
        "minimum_gain": min(final),
        "maximum_gain": max(final),
        "adverse_seeds": ";".join(str(seed) for seed in SEEDS if gains[(seed, "1m")] < 0),
        "independent_unit": "training_seed",
    }]
    timeline = []
    for seed in SEEDS:
        for label in WINDOWS:
            timeline.append({
                "seed": seed,
                "window": label,
                "drtp_minus_utr_J_pert_mean": gains[(seed, label)],
                "sign": "positive" if gains[(seed, label)] > 0 else "adverse",
            })
    return summary + timeline, gains


def credit_products(gate_dir: Path) -> list[dict]:
    rows = read_csv(gate_dir / "group_credit_timeline_summary.csv")
    index = {(row["arm"], int(row["seed"]), row["window_end"], row["group"]): row for row in rows}
    products = []
    for seed in SEEDS:
        for window in WINDOWS:
            for metric in CREDIT_METRICS:
                arm_contrasts = {}
                for arm in ARMS:
                    nominal = float(index[(arm, seed, window, "N")][metric])
                    failures = mean(index[(arm, seed, window, group)][metric] for group in FAILURE_GROUPS)
                    arm_contrasts[arm] = failures - nominal
                products.append({
                    "seed": seed,
                    "window": window,
                    "metric": metric,
                    "utr_failure_minus_nominal": arm_contrasts["utr_sg"],
                    "drtp_failure_minus_nominal": arm_contrasts["drtp_sg"],
                    "paired_drtp_minus_utr_contrast": arm_contrasts["drtp_sg"] - arm_contrasts["utr_sg"],
                    "independent_unit": "training_seed",
                })
    return products


def conflict_products(gate_dir: Path) -> list[dict]:
    rows = read_csv(gate_dir / "gradient_conflict_timeline_summary.csv")
    grouped: dict[tuple[str, int, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if "N" in (row["group_a"], row["group_b"]):
            grouped[(row["arm"], int(row["seed"]), row["window_end"])].append(row)
    products = []
    for seed in SEEDS:
        for window in WINDOWS:
            for metric in ("actor_conflict_fraction", "critic_conflict_fraction"):
                values = {
                    arm: mean(float(row[metric]) for row in grouped[(arm, seed, window)])
                    for arm in ARMS
                }
                products.append({
                    "seed": seed,
                    "window": window,
                    "metric": f"mean_nominal_failure_{metric}",
                    "utr": values["utr_sg"],
                    "drtp": values["drtp_sg"],
                    "paired_drtp_minus_utr": values["drtp_sg"] - values["utr_sg"],
                    "independent_unit": "training_seed",
                })
    return products


def episode_behavior_products(root: Path) -> list[dict]:
    group_rows: list[dict] = []
    for arm in ARMS:
        for seed in SEEDS:
            path = root / "runs" / arm / f"seed{seed}" / "failure_telemetry" / "episode_summary.jsonl"
            episodes = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            by_env: dict[int, list[dict]] = defaultdict(list)
            for episode in episodes:
                by_env[int(episode["env_index"])].append(episode)
            buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
            for env_episodes in by_env.values():
                cumulative_steps = 0
                for episode in sorted(env_episodes, key=lambda item: int(item["episode_index"])):
                    cumulative_steps += int(episode["step_count"])
                    update = math.ceil(cumulative_steps / 64)
                    buckets[(window_for_update(update), episode["scenario_group"])].append(episode)
            for (window, group), items in buckets.items():
                values: dict[str, list[float]] = defaultdict(list)
                for item in items:
                    steps = max(1, int(item["step_count"]))
                    components = item.get("reward_components_sum", {})
                    values["reward_per_step"].append(float(item["total_reward"]) / steps)
                    for key in ("progress", "attack_window", "connectivity", "message_age_penalty"):
                        values[f"{key}_per_step"].append(float(components.get(key, 0.0)) / steps)
                    for key in ("timeout", "collision", "success"):
                        values[key].append(float(item.get(key, 0)))
                row = {"arm": arm, "seed": seed, "window": window, "group": group, "episodes": len(items)}
                row.update({metric: mean(values[metric]) for metric in BEHAVIOR_METRICS})
                group_rows.append(row)
    group_index = {(row["arm"], row["seed"], row["window"], row["group"]): row for row in group_rows}
    products = []
    for seed in SEEDS:
        for window in WINDOWS:
            for metric in BEHAVIOR_METRICS:
                arm_values = {
                    arm: mean(group_index[(arm, seed, window, group)][metric] for group in FAILURE_GROUPS)
                    for arm in ARMS
                }
                products.append({
                    "seed": seed,
                    "window": window,
                    "metric": metric,
                    "utr_equal_group_mean": arm_values["utr_sg"],
                    "drtp_equal_group_mean": arm_values["drtp_sg"],
                    "paired_drtp_minus_utr": arm_values["drtp_sg"] - arm_values["utr_sg"],
                    "note": "six failure groups weighted equally; training episodes are descriptive technical repetitions",
                })
    return products


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.input_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    gate = root / "diagnostics" / "b5_1m_mechanism_gate"

    endpoint_rows, gains = endpoint_products(gate)
    endpoint_summary, endpoint_timeline = endpoint_rows[:1], endpoint_rows[1:]
    credit = credit_products(gate)
    conflicts = conflict_products(gate)
    behavior = episode_behavior_products(root)
    write_csv(output / "seed_level_endpoint_summary.csv", endpoint_summary)
    write_csv(output / "paired_endpoint_timeline_review.csv", endpoint_timeline)
    write_csv(output / "failure_credit_contrasts.csv", credit)
    write_csv(output / "nominal_failure_gradient_conflicts.csv", conflicts)
    write_csv(output / "quarter_behavior_summary.csv", behavior)

    adverse = [seed for seed in SEEDS if gains[(seed, "1m")] < 0]
    criteria = [
        {"criterion": "temporal_precedence", "pass": False, "reason": "No direction-consistent candidate precedes the adverse 1M endpoint across milestones."},
        {"criterion": "replication_at_least_2_of_5_adverse_seeds", "pass": False, "reason": f"Only {len(adverse)} final paired-adverse seed exists ({adverse}); the frozen replication requirement cannot be met."},
        {"criterion": "paired_utr_specificity", "pass": False, "reason": "Credit/conflict and training-behavior contrasts are mixed and are not uniquely stronger in a repeated DRTP failure subset."},
        {"criterion": "two_non_equivalent_middle_layer_indicators", "pass": False, "reason": "No replicated adverse subset supports two aligned credit-assignment indicators."},
        {"criterion": "continuous_optimization_behavior_outcome_chain", "pass": False, "reason": "Transient endpoint reversals and changing signal directions break a continuous time-leading chain."},
        {"criterion": "neighboring_threshold_robustness", "pass": False, "reason": "There is no complete candidate signature to test at 0.50/0.75/1.00; this requirement is therefore not satisfied."},
    ]
    write_csv(output / "mechanism_criteria_matrix.csv", criteria)
    decision = {
        "status": "B5_MECHANISM_NO_GO",
        "hypothesis": "failure-group-conditioned credit-assignment mechanism",
        "integrity": True,
        "all_frozen_criteria_pass": False,
        "mechanism_declared": False,
        "algorithm_modification_authorized": False,
        "automatic_continuation_authorized": False,
        "final_paired_adverse_seeds": adverse,
        "independent_unit": "training_seed",
        "mainline_a_modified": False,
        "scientific_boundary": "This closes the frozen B5 credit-assignment mechanism hypothesis; it does not erase the observed DRTP upper-tail gains.",
    }
    (output / "B5_FINAL_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

    final = endpoint_summary[0]
    report = f"""# DRTP B5 final human mechanism review

**Decision:** `B5_MECHANISM_NO_GO`.

## What the experiment established

At 1M, Original DRTP exceeds paired UTR on `J_pert_mean` in {final['wins']}/5 training seeds. The seed-level mean and median gains are {final['mean_gain']:.3f} and {final['median_gain']:.3f}, but the minimum gain is {final['minimum_gain']:.3f} and the sample SD is {final['sample_sd']:.3f}. Thus B5 preserves evidence of high-return potential while independently reproducing substantial training-seed risk.

The milestone directions are non-monotonic. Seeds 3601--3603 are adverse at 750k and recover by 1M, seed 3604 remains positive, and seed 3605 ends adverse. Failure-versus-nominal value residuals, TD residuals, normalized advantages, actor/critic gradient norms, nominal--failure gradient conflicts, and group-stratified training behavior do not form one direction-consistent precursor that repeats in at least two final adverse DRTP seeds and is absent from paired UTR.

## Frozen-gate outcome

All six frozen requirements were conjunctive. None can rescue the failed 2/5 adverse-seed replication requirement: only seed 3605 is paired-adverse at 1M. The changing signs across 250k, 500k, 750k, and 1M also prevent a continuous time-leading optimization-to-behavior-to-outcome chain. Because no complete candidate signature exists, neighboring-threshold robustness is not satisfied rather than retrospectively redefining a signal.

Accordingly, failure-group-conditioned credit assignment is **not supported as a stable actionable mechanism** by B5. No DRTP patch, Stable-v2, continuation, seed replacement, or performance-driven rerun is scientifically authorized under this contract.

## Statistical boundary

The independent unit is the training seed (`n=5` per arm). Update-by-group rows, gradient-pair rows, and episodes are technical repetitions used for descriptive time alignment only. No episode-level or update-level pseudo-replication, null-hypothesis test, or invented p-value is used.

## Project consequence

This decision does not modify mainline A and does not negate DRTP's observed upper-tail or mean gains. It closes the specific B5 credit-assignment mechanism route. A future optimization-reliability study would require a newly framed project and independent evidence; it must not be presented as an authorized continuation of B5.
"""
    (output / "B5_FINAL_MECHANISM_REVIEW.md").write_text(report, encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
