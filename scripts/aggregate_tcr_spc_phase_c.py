"""Apply the frozen Phase-C 1M stability decision without training new policies."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from scripts.create_tcr_spc_phase_c_tape import EPISODES, TAPE_START
from scripts.run_tcr_spc_phase_c_single import ARMS, SEEDS


PROTOCOL = "TCR-SPC-PHASE-C-1M-STABILITY-AGGREGATION-V1"
OOD_CONDITIONS = ("timing_28_80", "timing_36_80", "timing_52_80", "timing_60_80", "duration_44_40", "duration_44_60", "duration_44_100", "duration_44_120", "compound_28_120", "compound_60_120")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def cell(summary: list[dict[str, str]], arm: str, seed: int, condition: str) -> dict[str, str]:
    found = [row for row in summary if row["arm"] == arm and int(row["seed"]) == seed and row["condition"] == condition]
    if len(found) != 1:
        raise RuntimeError(f"expected one summary row for {arm}/{seed}/{condition}, found {len(found)}")
    return found[0]


def metric_cell(summary: list[dict[str, str]], arm: str, seed: int) -> dict:
    nominal, f0 = cell(summary, arm, seed, "nominal"), cell(summary, arm, seed, "f0_seen_44_80")
    ood = [cell(summary, arm, seed, condition) for condition in OOD_CONDITIONS]
    failure = [f0, *ood]
    return {
        "arm": arm, "seed": seed, "J_nominal": float(nominal["J"]), "J_F0": float(f0["J"]),
        "J_OOD_mean": mean([float(row["J"]) for row in ood]), "J_OOD_worst": min(float(row["J"]) for row in ood),
        "collision": mean([float(row["collision"]) for row in failure]),
        "timeout": mean([float(row["timeout"]) for row in failure]),
        "constraint_violation": mean([float(row["constraint_violation"]) for row in failure]),
        "failure_exposure": mean([float(row["failure_exposure"]) for row in failure]),
        "episode_length": mean([float(row["episode_length"]) for row in failure]),
        "path_switch_count": mean([float(row["path_switch_count"]) for row in failure]),
        "direct_path_fraction": mean([float(row["direct_path_fraction"]) for row in failure]),
        "task_support_fraction": mean([float(row["task_support_fraction"]) for row in failure]),
    }


def pooled(cells: list[dict]) -> dict:
    numeric = [key for key in cells[0] if key not in {"arm", "seed"}]
    return {key: mean([float(item[key]) for item in cells]) for key in numeric}


def ratios(candidate: dict, reference: dict) -> tuple[float, float]:
    if reference["J_F0"] <= 0.0 or reference["J_OOD_worst"] <= 0.0:
        raise RuntimeError("technical invalid: non-positive paired UTR denominator")
    return candidate["J_F0"] / reference["J_F0"], candidate["J_OOD_worst"] / reference["J_OOD_worst"]


def catastrophic(candidate: dict, reference: dict) -> dict:
    r_f0, r_worst = ratios(candidate, reference)
    performance = (r_f0 < .70 and r_worst < .85) or (r_worst < .70 and r_f0 < .85)
    safety = candidate["timeout"] - reference["timeout"] > .20 and (r_f0 < .85 or r_worst < .85)
    return {"seed": candidate["seed"], "J_F0_ratio": r_f0, "J_OOD_worst_ratio": r_worst,
            "timeout_difference": candidate["timeout"] - reference["timeout"],
            "performance_collapse": performance, "safety_associated_collapse": safety,
            "catastrophic": performance or safety}


def direction(candidate: dict, reference: dict) -> dict:
    return {"seed": candidate["seed"], "J_nominal_difference": candidate["J_nominal"] - reference["J_nominal"],
            "J_F0_difference": candidate["J_F0"] - reference["J_F0"],
            "J_OOD_mean_difference": candidate["J_OOD_mean"] - reference["J_OOD_mean"],
            "J_OOD_worst_difference": candidate["J_OOD_worst"] - reference["J_OOD_worst"],
            "J_OOD_worst_positive": candidate["J_OOD_worst"] > reference["J_OOD_worst"]}


def range_of(values: list[float]) -> float:
    return max(values) - min(values)


def seed_dispersion(cells: list[dict]) -> dict:
    """Descriptive seed-level dispersion; episodes are never treated as repeats."""
    metrics = ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout", "constraint_violation", "failure_exposure")
    return {
        metric: {
            "mean": mean([float(row[metric]) for row in cells]),
            "sample_sd": statistics.stdev([float(row[metric]) for row in cells]),
            "range": range_of([float(row[metric]) for row in cells]),
        }
        for metric in metrics
    }


def report(result: dict) -> str:
    table = "\n".join(
        f"| {row['arm']} | {row['seed']} | {row['J_nominal']:.3f} | {row['J_F0']:.3f} | {row['J_OOD_mean']:.3f} | {row['J_OOD_worst']:.3f} | {row['timeout']:.3f} | {row['failure_exposure']:.3f} |"
        for row in result["per_seed_metrics"]
    )
    catastrophic_rows = "\n".join(
        f"| {row['seed']} | {row['J_F0_ratio']:.3f} | {row['J_OOD_worst_ratio']:.3f} | {row['timeout_difference']:.3f} | {row['catastrophic']} |"
        for row in result["tcr_catastrophic"]
    )
    return f"""# TCR/SPC Phase C — 1M Stability Screen Report

**Final decision: {result['decision']}.** This is a development-only 1M final-checkpoint screen; it is not a superiority, held-out, or canonical result.

## Integrity audit

- 15/15 required trajectories completed: `{result['integrity']['completed_runs']}/15`.
- All runs used the frozen 4×64 rollout, 1,000,192 environment steps, fixed stratified sampler, final checkpoint only, and runtime persistence from update zero: `{result['integrity']['all_contracts_valid']}`.
- Tape: `440000–440099`, SHA256 `{result['tape_hash']}`.
- Canonical and held-out use: false.

## Per-seed final metrics

| Arm | Seed | J nominal | J F0 | J OOD mean | J OOD worst | Timeout | Failure exposure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

## TCR catastrophic-seed audit versus paired UTR

| Seed | F0 ratio | OOD-worst ratio | Timeout difference | Catastrophic |
| ---: | ---: | ---: | ---: | --- |
{catastrophic_rows}

Stress seed `2002` catastrophic: `{result['stress_seed_2002']['catastrophic']}`.

## Pooled descriptive comparison

```json
{json.dumps(result['pooled'], indent=2)}
```

## Seed-level dispersion

```json
{json.dumps(result['seed_dispersion'], indent=2)}
```

## Gradient-conflict diagnostics

```json
{json.dumps(result['gradient_diagnostics'], indent=2)}
```

## Decision basis

```json
{json.dumps(result['decision_audit'], indent=2)}
```

## Stop state

Training stops at 1M. No 3M, held-out, canonical, new tape, method modification, or threshold revision is authorized by this report.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()
    tape = json.loads((args.results_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + EPISODES)) or tape.get("canonical") is not False:
        raise RuntimeError("TECHNICAL INVALID: invalid Phase-C tape")
    eval_root = args.results_root / "evaluations" / "final_1m"
    manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape["tape_hash"] or manifest.get("cells") != 15:
        raise RuntimeError("TECHNICAL INVALID: incomplete unified evaluation")
    summary = rows(eval_root / "per_seed_condition_summary.csv")
    expected_conditions = {"nominal", "f0_seen_44_80", *OOD_CONDITIONS}
    if {row["condition"] for row in summary} != expected_conditions:
        raise RuntimeError("TECHNICAL INVALID: condition set mismatch")
    metrics = [metric_cell(summary, arm, seed) for arm in ARMS for seed in SEEDS]
    by_arm = {arm: [row for row in metrics if row["arm"] == arm] for arm in ARMS}
    tcr_catastrophic = [catastrophic(tcr, next(row for row in by_arm["utr_sg"] if row["seed"] == tcr["seed"])) for tcr in by_arm["tcr_sg"]]
    spc_catastrophic = [catastrophic(spc, next(row for row in by_arm["utr_sg"] if row["seed"] == spc["seed"])) for spc in by_arm["spc_sg"]]
    tcr_directions = [direction(tcr, next(row for row in by_arm["utr_sg"] if row["seed"] == tcr["seed"])) for tcr in by_arm["tcr_sg"]]
    pooled_metrics = {arm: pooled(by_arm[arm]) for arm in ARMS}
    dispersion = {arm: seed_dispersion(by_arm[arm]) for arm in ARMS}
    utr_values = [row["J_OOD_worst"] for row in by_arm["utr_sg"]]
    tcr_values = [row["J_OOD_worst"] for row in by_arm["tcr_sg"]]
    utr_range, tcr_range = range_of(utr_values), range_of(tcr_values)
    utr_sd, tcr_sd = statistics.stdev(utr_values), statistics.stdev(tcr_values)
    tcr_bifurcation = tcr_range > 2.0 * max(utr_range, 1e-12) and tcr_sd > 2.0 * max(utr_sd, 1e-12) and any(row["J_OOD_worst_ratio"] < .85 for row in tcr_catastrophic)
    timeout_diffs = [tcr["timeout"] - next(row for row in by_arm["utr_sg"] if row["seed"] == tcr["seed"])["timeout"] for tcr in by_arm["tcr_sg"]]
    systemic_safety = (pooled_metrics["tcr_sg"]["constraint_violation"] > 0.0 or
                       (pooled_metrics["tcr_sg"]["timeout"] - pooled_metrics["utr_sg"]["timeout"] > .05 and sum(diff > .05 for diff in timeout_diffs) >= 3))
    catastrophic_count = sum(row["catastrophic"] for row in tcr_catastrophic)
    ood_positive = sum(row["J_OOD_worst_positive"] for row in tcr_directions)
    stress = next(row for row in tcr_catastrophic if row["seed"] == 2002)
    tcr_vs_spc = [tcr["J_OOD_worst"] - next(row for row in by_arm["spc_sg"] if row["seed"] == tcr["seed"])["J_OOD_worst"] for tcr in by_arm["tcr_sg"]]
    systematic_spc_inferiority = sum(value < 0.0 for value in tcr_vs_spc) >= 4 and mean(tcr_vs_spc) < 0.0
    valid_exposure = all(
        abs(row["failure_exposure"] - 1.0) <= .01 and row["constraint_violation"] == 0.0
        for arm in ARMS for row in by_arm[arm]
    )
    gradients = rows(eval_root / "gradient_diagnostics_summary.csv")
    gradient_contract_valid = (
        len(gradients) == 15
        and {(row["arm"], int(row["seed"])) for row in gradients} == {(arm, seed) for arm in ARMS for seed in SEEDS}
        and all(row["all_nominal_counts_128"] == "True" and row["all_failure_counts_128"] == "True" for row in gradients)
    )
    integrity = {
        "completed_runs": len(manifest["source_runs"]),
        "all_contracts_valid": manifest.get("final_checkpoint_only") is True and gradient_contract_valid,
        "final_checkpoint_only": manifest.get("final_checkpoint_only") is True,
        "gradient_contract_valid": gradient_contract_valid,
        "canonical_seeds_used": manifest.get("canonical_seeds_used") is False,
        "held_out_used": manifest.get("held_out_used") is False,
    }
    if not integrity["all_contracts_valid"] or not valid_exposure:
        decision = "TECHNICAL INVALID"
    elif catastrophic_count >= 2 or tcr_bifurcation or systemic_safety:
        decision = "PHASE-C EARLY NO-GO"
    elif catastrophic_count >= 1:
        decision = "PHASE-C NO-GO"
    elif (pooled_metrics["tcr_sg"]["J_OOD_mean"] <= pooled_metrics["utr_sg"]["J_OOD_mean"] and
          pooled_metrics["tcr_sg"]["J_OOD_worst"] <= pooled_metrics["utr_sg"]["J_OOD_worst"] and ood_positive < 3):
        decision = "PHASE-C NO-GO"
    elif (valid_exposure and not systemic_safety and
          pooled_metrics["tcr_sg"]["J_OOD_mean"] >= pooled_metrics["utr_sg"]["J_OOD_mean"] and
          pooled_metrics["tcr_sg"]["J_OOD_worst"] >= pooled_metrics["utr_sg"]["J_OOD_worst"] and
          ood_positive >= 3 and not systematic_spc_inferiority and not stress["catastrophic"]):
        decision = "PHASE-C GO"
    else:
        decision = "PHASE-C NO-GO"
    gradient_diagnostics = {f"{row['arm']}_seed{row['seed']}": row for row in gradients}
    result = {
        "protocol": PROTOCOL, "decision": decision, "tape_hash": tape["tape_hash"], "integrity": integrity,
        "per_seed_metrics": metrics, "pooled": pooled_metrics, "seed_dispersion": dispersion,
        "per_condition_summary": str(eval_root / "per_seed_condition_summary.csv"),
        "tcr_catastrophic": tcr_catastrophic,
        "spc_catastrophic": spc_catastrophic, "stress_seed_2002": stress, "gradient_diagnostics": gradient_diagnostics,
        "decision_audit": {"tcr_catastrophic_count": catastrophic_count, "tcr_cross_seed_bifurcation": tcr_bifurcation,
                             "utr_ood_worst_range": utr_range, "tcr_ood_worst_range": tcr_range,
                             "utr_ood_worst_sd": utr_sd, "tcr_ood_worst_sd": tcr_sd,
                             "systemic_safety_deterioration": systemic_safety, "valid_exposure_and_constraints": valid_exposure,
                             "tcr_ood_worst_positive_seeds": ood_positive, "tcr_systematically_inferior_to_spc": systematic_spc_inferiority,
                             "tcr_minus_spc_ood_worst": tcr_vs_spc},
        "training_stopped_at_1m": True, "three_m_started": False, "held_out_started": False, "canonical_started": False,
    }
    with (eval_root / "PHASE_C_DECISION.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2); handle.write("\n")
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    with args.report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report(result))
    print(json.dumps({"decision": decision, "result": str(eval_root / "PHASE_C_DECISION.json"), "report": str(args.report_path)}, indent=2))


if __name__ == "__main__":
    main()
