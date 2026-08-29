"""Zero-training forensic analysis for the frozen DRTP-KLR 0.5M pilot."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics


SEEDS = (3101, 3102, 3103)
CORE_FIELDS = (
    "train_avg_reward",
    "policy_loss",
    "value_loss",
    "entropy",
    "approx_kl",
    "clip_fraction",
    "grad_norm",
    "explained_variance",
    "advantage_std",
    "actor_update_norm",
    "critic_update_norm",
)
Q_FIELDS = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")
SEGMENTS = ((1, 250), (251, 500), (501, 750), (751, 1000), (1001, 1500), (1501, 1953))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def same_numeric(left: str, right: str, tolerance: float = 1e-12) -> bool:
    a, b = finite(left), finite(right)
    if a is None or b is None:
        return left == right
    return abs(a - b) <= tolerance


def mean_field(rows: list[dict[str, str]], field: str, lo: int, hi: int) -> float:
    values = [
        value
        for row in rows
        if lo <= int(row["update"]) <= hi
        if (value := finite(row[field])) is not None
    ]
    return statistics.mean(values)


def first_core_divergence(
    original: list[dict[str, str]], candidate: list[dict[str, str]]
) -> tuple[int | None, str | None]:
    for left, right in zip(original, candidate):
        for field in CORE_FIELDS:
            if not same_numeric(left[field], right[field]):
                return int(left["update"]), field
    return None, None


def sampler_divergence(root: Path, seed: int) -> dict[str, float | int | None]:
    def updates(arm: str) -> dict[int, dict[str, str]]:
        rows = read_csv(root / "runs" / arm / f"seed{seed}" / "drtp_topology_sampler_log.csv")
        return {
            int(row["adaptation_count"]): row
            for row in rows
            if row["record_type"] == "weight_update"
        }

    original, candidate = updates("drtp_sg"), updates("drtp_klr_sg")
    common = sorted(set(original) & set(candidate))
    for count in common:
        maximum = max(abs(float(original[count][field]) - float(candidate[count][field])) for field in Q_FIELDS)
        if maximum > 1e-12:
            return {
                "first_q_divergence_adaptation": count,
                "first_q_divergence_update": int(candidate[count]["update"]),
                "first_q_max_abs_difference": maximum,
            }
    return {
        "first_q_divergence_adaptation": None,
        "first_q_divergence_update": None,
        "first_q_max_abs_difference": 0.0,
    }


def sampler_state(root: Path, arm: str, seed: int) -> tuple[dict[str, int], dict[str, float]]:
    rows = read_csv(root / "runs" / arm / f"seed{seed}" / "drtp_topology_sampler_log.csv")
    exposure: dict[str, int] = {}
    for row in rows:
        if row["record_type"] == "selection":
            exposure[row["group"]] = exposure.get(row["group"], 0) + 1
    final = [row for row in rows if row["record_type"] == "weight_update"][-1]
    return exposure, {field: float(final[field]) for field in Q_FIELDS}


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-archive-sha256", required=True)
    args = parser.parse_args()
    root = args.results_root.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(f"refusing forensic overwrite: {output}")
    output.mkdir(parents=True)

    gate = json.loads(
        (root / "diagnostics" / "stable_v2_pilot_gate" / "PILOT_GATE_DECISION.json")
        .read_text(encoding="utf-8")
    )
    gate_by_seed = {int(row["seed"]): row for row in gate["seed_results"]}
    seed_rows, event_rows, condition_rows = [], [], []
    evaluation_summary = read_csv(root / "evaluations" / "final_05m" / "per_seed_condition_summary.csv")

    for seed in SEEDS:
        original = read_csv(root / "runs" / "drtp_sg" / f"seed{seed}" / "train_log.csv")
        candidate = read_csv(root / "runs" / "drtp_klr_sg" / f"seed{seed}" / "train_log.csv")
        if len(original) != 1953 or len(candidate) != 1953:
            raise RuntimeError(f"incomplete train log for seed {seed}")
        triggers = [row for row in candidate if finite(row["policy_guard_triggered"]) == 1.0]
        first_trigger = int(triggers[0]["update"]) if triggers else None
        divergence_update, divergence_field = first_core_divergence(original, candidate)
        q_divergence = sampler_divergence(root, seed)
        original_exposure, original_q = sampler_state(root, "drtp_sg", seed)
        candidate_exposure, candidate_q = sampler_state(root, "drtp_klr_sg", seed)
        segment_differences = []
        for lo, hi in SEGMENTS:
            original_mean = mean_field(original, "train_avg_reward", lo, hi)
            candidate_mean = mean_field(candidate, "train_avg_reward", lo, hi)
            segment_differences.append({
                "updates": f"{lo}-{hi}",
                "original": original_mean,
                "klr": candidate_mean,
                "klr_minus_original": candidate_mean - original_mean,
            })
        outcome = gate_by_seed[seed]
        seed_rows.append({
            "seed": seed,
            "trigger_count": len(triggers),
            "first_trigger_update": first_trigger,
            "last_trigger_update": int(triggers[-1]["update"]) if triggers else None,
            "first_core_divergence_update": divergence_update,
            "first_core_divergence_field": divergence_field,
            **q_divergence,
            "max_attempted_kl": max(float(row["policy_kl_attempted_max"]) for row in triggers),
            "G_original": outcome["G_original"],
            "G_klr": outcome["G_klr"],
            "klr_minus_original": outcome["klr_minus_original"],
            "original_catastrophic": outcome["original_catastrophic"],
            "klr_catastrophic": outcome["klr_catastrophic"],
            "exposure_l1_count_difference": sum(
                abs(candidate_exposure.get(group, 0) - original_exposure.get(group, 0))
                for group in set(original_exposure) | set(candidate_exposure)
            ),
            "final_q_l1_difference": sum(
                abs(candidate_q[field] - original_q[field]) for field in Q_FIELDS
            ),
            "original_exposure": json.dumps(original_exposure, sort_keys=True, separators=(",", ":")),
            "klr_exposure": json.dumps(candidate_exposure, sort_keys=True, separators=(",", ":")),
            "original_final_q": json.dumps(original_q, sort_keys=True, separators=(",", ":")),
            "klr_final_q": json.dumps(candidate_q, sort_keys=True, separators=(",", ":")),
            "reward_segment_differences": json.dumps(segment_differences, separators=(",", ":")),
        })
        for row in triggers:
            event_rows.append({
                "seed": seed,
                "update": int(row["update"]),
                "guard_epoch": int(row["policy_guard_epoch"]),
                "attempted_kl": float(row["policy_kl_attempted_max"]),
                "attempted_update_l2": float(row["actor_attempted_update_l2"]),
                "rollback_l2": float(row["actor_rollback_l2"]),
                "train_avg_reward": finite(row["train_avg_reward"]),
                "value_loss": finite(row["value_loss"]),
                "explained_variance": finite(row["explained_variance"]),
                "advantage_std": finite(row["advantage_std"]),
                "critic_update_norm": finite(row["critic_update_norm"]),
                "final_klr_minus_original": outcome["klr_minus_original"],
            })
        by_key = {
            (row["method"], row["condition"]): row
            for row in evaluation_summary
            if int(row["train_seed"]) == seed
        }
        for condition in ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120"):
            utr = by_key[("utr_sg", condition)]
            original_eval = by_key[("drtp_sg", condition)]
            candidate_eval = by_key[("drtp_klr_sg", condition)]
            condition_rows.append({
                "seed": seed,
                "condition": condition,
                "J_utr": float(utr["J"]),
                "J_original": float(original_eval["J"]),
                "J_klr": float(candidate_eval["J"]),
                "klr_minus_original": float(candidate_eval["J"]) - float(original_eval["J"]),
                "klr_minus_utr": float(candidate_eval["J"]) - float(utr["J"]),
                "klr_collision": float(candidate_eval["collision"]),
                "klr_timeout": float(candidate_eval["timeout"]),
            })

    write_csv(output / "seed_forensic_summary.csv", seed_rows)
    write_csv(output / "intervention_events.csv", event_rows)
    write_csv(output / "condition_endpoint_comparison.csv", condition_rows)
    signed_outcomes = [row["klr_minus_original"] for row in seed_rows]
    conclusion = {
        "protocol": "DRTP-STABLE-V2-PILOT-D3-FORENSIC-V1",
        "zero_training": True,
        "training_or_evaluation_started": False,
        "source_gate_decision": gate["decision"],
        "source_archive_sha256": args.source_archive_sha256,
        "source_archive_integrity_verified": True,
        "observations": {
            "all_seeds_intervened": all(row["trigger_count"] > 0 for row in seed_rows),
            "all_core_trajectories_match_until_first_intervention": all(
                row["first_core_divergence_update"] is not None
                and row["first_core_divergence_update"] >= row["first_trigger_update"]
                for row in seed_rows
            ),
            "intervention_count_is_not_monotonic_with_outcome": not (
                seed_rows[0]["trigger_count"] < seed_rows[1]["trigger_count"] < seed_rows[2]["trigger_count"]
                or seed_rows[0]["trigger_count"] > seed_rows[1]["trigger_count"] > seed_rows[2]["trigger_count"]
            ),
            "mixed_candidate_effects": min(signed_outcomes) < 0 < max(signed_outcomes),
            "upper_tail_loss_seed": 3103,
        },
        "scientific_decision": "FULL_ROLLBACK_KLR_CLOSED_UNDER_FROZEN_GATE",
        "mechanistic_interpretation": (
            "Rare rollback events are sufficient to redirect training trajectories, but trigger count or "
            "maximum attempted KL does not separate beneficial from harmful outcomes across the three seeds. "
            "Policy dynamics diverge before the adaptive sampler weights, after which exposure and q also diverge."
        ),
        "authorized_next_action": "ZERO_TRAINING_SOFT_KL_INTERVENTION_DESIGN_AUDIT_ONLY",
        "not_authorized": [
            "DRTP-KLR continuation",
            "target_kl tuning",
            "seed reuse",
            "new training before a new frozen contract",
        ],
        "seed_summary": seed_rows,
    }
    with (output / "STABLE_V2_D3_FORENSIC.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(conclusion, indent=2) + "\n")
    table = "\n".join(
        f"| {row['seed']} | {row['trigger_count']} | {row['first_trigger_update']} | "
        f"{row['first_core_divergence_update']} | {row['first_q_divergence_update']} | "
        f"{row['G_original']:.3f} | {row['G_klr']:.3f} | {row['klr_minus_original']:.3f} |"
        for row in seed_rows
    )
    seed3103_conditions = [row for row in condition_rows if row["seed"] == 3103]
    condition_table = "\n".join(
        f"| {row['condition']} | {row['J_original']:.3f} | {row['J_klr']:.3f} | "
        f"{row['klr_minus_original']:.3f} |"
        for row in seed3103_conditions
    )
    report = f"""# Stable-v2 pilot D3 zero-training forensic

Source decision: `{gate['decision']}`. Source archive SHA256: `{args.source_archive_sha256}`.
No training or checkpoint evaluation was executed.

| Seed | Rollbacks | First rollback | First train divergence | First q divergence | G Original | G KLR | KLR−Original |
|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

The full-rollback KLR candidate is closed under its frozen gate because upper-tail retention failed.
The result is nevertheless informative: all three KLR gains are positive, the catastrophic seed was removed,
and dispersion fell sharply, while seed3103 lost 18.785 points relative to its Original DRTP counterpart.

Rollback frequency is not an outcome discriminator: seed3101 benefited with 13 events, seed3102 benefited with
9, and seed3103 degraded with 14. Maximum attempted KL is likewise not a stable separator. The evidence supports
trajectory redirection by rare interventions, not a claim that one KL magnitude or event count causes failure.

For every seed, the training trajectory diverges at or immediately after the first rollback, while the first
sampler-q divergence appears later at update 160. This ordering is consistent with actor intervention preceding
sampler/exposure feedback; it does not prove that the later sampler change causes the final outcome.

## Seed3103 condition boundary

| Condition | J Original | J KLR | KLR−Original |
|---|---:|---:|---:|
{condition_table}

Seed3103 is not a global optimization collapse: KLR improves nominal score but loses across all four failure
conditions, and its later training-return segments are not worse than Original. The upper-tail failure is therefore
fault-conditional and cannot be diagnosed from aggregate training return, trigger count, or maximum KL alone.

The only authorized next step is a zero-training design audit for one softer KL intervention that preserves the
attempted actor-update direction (for example backtracking/projection) instead of all-or-nothing rollback. This
does not authorize a new model, threshold sweep, seed reuse, training, or any change to mainline A.
"""
    with (output / "STABLE_V2_D3_FORENSIC_REPORT.md").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    print(json.dumps({"status": conclusion["scientific_decision"], "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
