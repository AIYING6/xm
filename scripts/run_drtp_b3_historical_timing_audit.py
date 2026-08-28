"""Bounded historical timing audit used only to size the B3 observation window.

It does not infer a mechanism or reuse a historical outcome as a B3 result.
It asks whether a simple, pre-declared *training-return proxy* separation
between paired DRTP and UTR is sustained in the archived 10M cohorts.  The
answer determines whether a 1M B3 observation can be a no-go gate or is only
an inconclusive horizon check.
"""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "diagnostics" / "drtp_cohort_reversal_20260828" / "01_reconstructed" / "training_dynamics_long.csv"
DEFAULT_OUT = ROOT / "diagnostics" / "drtp_b_line" / "03_historical_timing_audit"
COHORTS = ("formal_2301_2305", "independent_2401_2405")
BIN_UPDATES = 500
PERSISTENT_BINS = 2
STEPS_PER_UPDATE = 256
AVAILABLE_DIAGNOSTICS = (
    "train_avg_reward", "entropy", "approx_kl", "policy_loss", "value_loss", "grad_norm",
)
UNAVAILABLE_REQUIRED_HISTORY = ("q_distance_from_uniform", "q_ranking", "nominal_ema", "group_ema", "difficulty")


def median(values: list[float]) -> float:
    return float(statistics.median(values)) if values else float("nan")


def read_paired_bins() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    values: dict[tuple[str, str, int, int], list[float]] = defaultdict(list)
    diagnostics: dict[tuple[str, str, int, int, str], list[float]] = defaultdict(list)
    with INPUT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["method"] not in {"utr_sg", "drtp_sg"}:
                continue
            update = int(row["update"])
            key = (row["cohort"], row["method"], int(row["seed"]), (update - 1) // BIN_UPDATES)
            for metric in AVAILABLE_DIAGNOSTICS:
                value = row.get(metric)
                if value not in {None, ""}:
                    diagnostics[(*key, metric)].append(float(value))
            value = row.get("train_avg_reward")
            if value not in {None, ""}:
                values[key].append(float(value))
    bins: list[dict[str, object]] = []
    by_seed: list[dict[str, object]] = []
    for cohort in COHORTS:
        seed_ids = sorted({key[2] for key in values if key[0] == cohort and key[1] == "utr_sg"})
        for bin_id in sorted({key[3] for key in values if key[0] == cohort}):
            differences = []
            for seed in seed_ids:
                utr = values.get((cohort, "utr_sg", seed, bin_id), [])
                drtp = values.get((cohort, "drtp_sg", seed, bin_id), [])
                if utr and drtp:
                    delta = statistics.fmean(drtp) - statistics.fmean(utr)
                    differences.append(delta)
                    by_seed.append({
                        "cohort": cohort, "seed": seed, "bin_id": bin_id,
                        "update_start": bin_id * BIN_UPDATES + 1,
                        "update_end": (bin_id + 1) * BIN_UPDATES,
                        "environment_steps_million_end": (bin_id + 1) * BIN_UPDATES * STEPS_PER_UPDATE / 1_000_000,
                        "utr_mean_train_reward": statistics.fmean(utr),
                        "drtp_mean_train_reward": statistics.fmean(drtp),
                        "drtp_minus_utr_train_reward": delta,
                    })
            if len(differences) != len(seed_ids):
                continue
            bins.append({
                "cohort": cohort, "bin_id": bin_id,
                "update_start": bin_id * BIN_UPDATES + 1,
                "update_end": (bin_id + 1) * BIN_UPDATES,
                "environment_steps_million_end": (bin_id + 1) * BIN_UPDATES * STEPS_PER_UPDATE / 1_000_000,
                "seed_count": len(differences), "mean_delta_train_reward": statistics.fmean(differences),
                "median_delta_train_reward": median(differences),
                "positive_seeds": sum(item > 0.0 for item in differences),
                "negative_seeds": sum(item < 0.0 for item in differences),
                "paired_deltas": ";".join(f"{item:.8f}" for item in differences),
            })
    metric_rows: list[dict[str, object]] = []
    for (cohort, method, seed, bin_id, metric), metric_values in diagnostics.items():
        metric_rows.append({
            "cohort": cohort, "method": method, "seed": seed, "bin_id": bin_id,
            "update_start": bin_id * BIN_UPDATES + 1,
            "update_end": (bin_id + 1) * BIN_UPDATES,
            "environment_steps_million_end": (bin_id + 1) * BIN_UPDATES * STEPS_PER_UPDATE / 1_000_000,
            "metric": metric, "mean_value": statistics.fmean(metric_values),
        })
    return bins, by_seed, metric_rows


def directional_separation(formal: dict[str, object], independent: dict[str, object]) -> str | None:
    # Deliberately sign-only: this is a horizon proxy, not an effect-size or
    # mechanism threshold.  At least three of five paired seeds must point in
    # each opposing cohort direction.
    if int(formal["positive_seeds"]) >= 3 and int(independent["negative_seeds"]) >= 3:
        return "formal_positive_independent_negative"
    if int(formal["negative_seeds"]) >= 3 and int(independent["positive_seeds"]) >= 3:
        return "formal_negative_independent_positive"
    return None


def first_persistent_separation(rows: list[dict[str, object]]) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    by_cohort = {cohort: {int(row["bin_id"]): row for row in rows if row["cohort"] == cohort} for cohort in COHORTS}
    events: list[dict[str, object]] = []
    common = sorted(set(by_cohort[COHORTS[0]]) & set(by_cohort[COHORTS[1]]))
    for index, bin_id in enumerate(common):
        direction = directional_separation(by_cohort[COHORTS[0]][bin_id], by_cohort[COHORTS[1]][bin_id])
        events.append({"bin_id": bin_id, "direction": direction or "none"})
        if index + PERSISTENT_BINS > len(common) or direction is None:
            continue
        following = common[index:index + PERSISTENT_BINS]
        if all(directional_separation(by_cohort[COHORTS[0]][candidate], by_cohort[COHORTS[1]][candidate]) == direction for candidate in following):
            return by_cohort[COHORTS[0]][bin_id], events
    return None, events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {output}")
    output.mkdir(parents=True, exist_ok=False)
    rows, by_seed, metric_rows = read_paired_bins()
    first, events = first_persistent_separation(rows)
    first_million = None if first is None else float(first["environment_steps_million_end"])
    one_million_has_proxy = first_million is not None and first_million <= 1.0
    recommendation = "ONE_MILLION_CAN_BE_A_MECHANISM_NO_GO_HORIZON" if one_million_has_proxy else "ONE_MILLION_IS_INCONCLUSIVE_TIME_HORIZON_EXTEND_HEALTHY_RUNS_TO_3M"
    with (output / "paired_train_reward_proxy_by_500_updates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output / "divergence_timing_by_seed.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(by_seed[0]))
        writer.writeheader()
        writer.writerows(by_seed)
    with (output / "historical_available_diagnostics_by_500_updates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metric_rows[0]))
        writer.writeheader()
        writer.writerows(metric_rows)
    with (output / "historical_metric_availability.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "available", "role"])
        writer.writeheader()
        writer.writerows(
            [{"metric": metric, "available": "yes", "role": "descriptive archived PPO/train diagnostic"} for metric in AVAILABLE_DIAGNOSTICS]
            + [{"metric": metric, "available": "no", "role": "not reconstructable from archived long table"} for metric in UNAVAILABLE_REQUIRED_HISTORY]
        )
    with (output / "timing_rule.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["bin_id", "direction"])
        writer.writeheader()
        writer.writerows(events)
    first_description = "none in archived horizon" if first is None else (
        f"bin {first['bin_id']}, ending at {first_million:.3f}M steps"
    )
    lines = [
        "# B3 historical divergence timing audit", "",
        "This is a zero-training, retrospective *horizon* audit.  It does not establish a behavior mechanism or a final-performance onset.", "",
        "## Frozen proxy rule", "",
        "At 500-update bins, calculate paired DRTP minus UTR mean training reward for every seed. A cohort-direction proxy exists only if at least 3/5 formal pairs and at least 3/5 independent pairs have opposite signs. It is persistent only when the same direction occurs in two consecutive bins (1,000 updates = 0.256M environment steps).", "",
        "## Result", "",
        f"- first persistent proxy separation: {first_description}",
        f"- 1M gate recommendation: `{recommendation}`", "",
        "## Diagnostic availability", "",
        "The archived long table contains training reward, entropy, approximate KL, policy loss, value loss, and gradient norm; their binned descriptive values are exported. It does not contain q distance/ranking, nominal/group EMA, or difficulty. Those unavailable sampler fields are explicitly recorded as unavailable rather than inferred.", "",
        "This result only sizes the prospective B3 observation horizon. The proxy is not a mechanism variable and cannot support sampler causality without behavior telemetry.",
    ]
    (output / "historical_timing_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(recommendation)


if __name__ == "__main__":
    main()
