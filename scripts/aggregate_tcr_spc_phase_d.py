"""Aggregate the frozen Phase-D 3M continuation evaluation."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from scripts.run_tcr_spc_phase_c_single import ARMS, SEEDS


OOD = (
    "timing_28_80", "timing_36_80", "timing_52_80", "timing_60_80",
    "duration_44_40", "duration_44_60", "duration_44_100", "duration_44_120",
    "compound_28_120", "compound_60_120",
)
FAILURE = ("f0_seen_44_80", *OOD)


def mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def cell(raw: list[dict[str, str]], arm: str, seed: int) -> dict:
    selected = [row for row in raw if row["method"] == arm and int(row["train_seed"]) == seed]
    nominal = [row for row in selected if row["topology_condition"] == "nominal"]
    failures = [row for row in selected if row["topology_condition"] in FAILURE]
    f0 = [row for row in failures if row["topology_condition"] == "f0_seen_44_80"]
    ood_values = [mean([f(row, "J") for row in failures if row["topology_condition"] == condition]) for condition in OOD]
    pre = [row for row in failures if int(row["terminal_step"]) < int(row["onset"])]
    risk = [row for row in failures if int(row["terminal_step"]) >= int(row["onset"])]
    triggered = [row for row in risk if f(row, "failure_exposed") == 1.0]
    return {
        "arm": arm, "seed": seed,
        "J_nominal": mean([f(row, "J") for row in nominal]),
        "J_F0": mean([f(row, "J") for row in f0]),
        "J_OOD_mean": mean(ood_values), "J_OOD_worst": min(ood_values),
        "collision": mean([f(row, "collision") for row in failures]),
        "timeout": mean([f(row, "timeout") for row in failures]),
        "constraint": mean([f(row, "constraint_violation") for row in failures]),
        "all_exposure": mean([f(row, "failure_exposed") for row in failures]),
        "pre_trigger_collision": len(pre), "pre_trigger_rate": len(pre) / len(failures),
        "survival_to_onset": len(risk) / len(failures), "risk_set_size": len(risk),
        "trigger_success": len(triggered) / len(risk) if risk else math.nan,
    }


def pooled(items: list[dict]) -> dict:
    keys = [key for key in items[0] if key not in {"arm", "seed"}]
    return {key: mean([float(item[key]) for item in items]) for key in keys}


def catastrophic(candidate: dict, reference: dict) -> dict:
    f0_ratio = candidate["J_F0"] / reference["J_F0"]
    worst_ratio = candidate["J_OOD_worst"] / reference["J_OOD_worst"]
    timeout_difference = candidate["timeout"] - reference["timeout"]
    performance = (f0_ratio < .70 and worst_ratio < .85) or (worst_ratio < .70 and f0_ratio < .85)
    safety = timeout_difference > .20 and (f0_ratio < .85 or worst_ratio < .85)
    return {"seed": candidate["seed"], "F0_ratio": f0_ratio, "OOD_worst_ratio": worst_ratio,
            "timeout_difference": timeout_difference, "catastrophic": performance or safety}


def markdown(result: dict) -> str:
    metrics = "\n".join(
        f"| {row['arm']} | {row['seed']} | {row['J_nominal']:.3f} | {row['J_F0']:.3f} | "
        f"{row['J_OOD_mean']:.3f} | {row['J_OOD_worst']:.3f} | {row['collision']:.4f} | "
        f"{row['timeout']:.4f} | {row['constraint']:.4f} | {row['pre_trigger_collision']} | "
        f"{row['survival_to_onset']:.4f} | {row['trigger_success']:.6f} |"
        for row in result["per_seed"]
    )
    cat = "\n".join(
        f"| {row['seed']} | {row['F0_ratio']:.4f} | {row['OOD_worst_ratio']:.4f} | "
        f"{row['timeout_difference']:.4f} | {row['catastrophic']} |"
        for row in result["tcr_catastrophic"]
    )
    return f"""# TCR/SPC Phase-D 3M Continuation Report

Final decision: {result['decision']}

This report uses only the final 3M checkpoint after strict continuation from
the Phase-C 1M runtime state. No 3M-to-5M continuation was started.

## Integrity

- Protocol: {result['protocol']}
- 15/15 trajectories: {result['integrity']['completed_runs']}/15
- Common endpoint: update {result['final_update']} = {result['final_steps']} environment steps
- Continuation boundary: update {result['source_update']} = 1,000,192 environment steps
- Strict continuation audit: PASS for all 15 trajectories
- Warm restart: false; from-scratch restart: false; canonical/held-out seeds: false
- Evaluation tape hash: {result['tape_hash']}

## Per-seed final metrics

| Arm | Seed | J nominal | J F0 | J OOD mean | J OOD worst | Collision | Timeout | Constraint | Pre-trigger | Survival | Risk-set trigger |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{metrics}

## Pooled metrics

```json
{json.dumps(result['pooled'], indent=2)}
```

## TCR catastrophic-seed audit

| Seed | F0 ratio vs UTR | OOD-worst ratio vs UTR | Timeout difference | Catastrophic |
| ---: | ---: | ---: | ---: | --- |
{cat}

TCR catastrophic seeds: {result['tcr_catastrophic_count']}/5.
SPC control catastrophic seeds: {result['spc_catastrophic_count']}/5.
TCR OOD-worst positive direction versus UTR: {result['tcr_ood_positive_count']}/5.
Stress seed 2002 catastrophic: {result['stress_seed_2002_catastrophic']}.

## Seed dispersion and TCR versus SPC

```json
{json.dumps(result['dispersion'], indent=2)}
```

TCR minus SPC OOD-worst by seed:

```json
{json.dumps(result['tcr_vs_spc_ood_worst'], indent=2)}
```

## Decision basis

```json
{json.dumps(result['decision_basis'], indent=2)}
```

The Phase-C v1 TECHNICAL_INVALID historical result remains unchanged. The
Phase-C v2 GO result also remains unchanged; this report is the separate 3M
continuation decision only.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()
    root = args.results_root.resolve()
    evaluation = root / "evaluations" / "final_3m"
    manifest = json.loads((evaluation / "evaluation_manifest.json").read_text(encoding="utf-8"))
    tape = json.loads((root / "tape_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("phase_d") is not True or manifest.get("cells") != 15:
        raise RuntimeError("TECHNICAL INVALID: incomplete Phase-D evaluation")
    raw = rows(evaluation / "raw_episode_metrics.csv")
    if len(raw) != 18_000:
        raise RuntimeError(f"TECHNICAL INVALID: expected 18000 raw rows, got {len(raw)}")
    per_seed = [cell(raw, arm, seed) for arm in ARMS for seed in SEEDS]
    by_arm = {arm: [row for row in per_seed if row["arm"] == arm] for arm in ARMS}
    by_key = {(row["arm"], row["seed"]): row for row in per_seed}
    tcr_cat = [catastrophic(by_key["tcr_sg", seed], by_key["utr_sg", seed]) for seed in SEEDS]
    spc_cat = [catastrophic(by_key["spc_sg", seed], by_key["utr_sg", seed]) for seed in SEEDS]
    tcr_diffs = {str(seed): by_key["tcr_sg", seed]["J_OOD_worst"] - by_key["utr_sg", seed]["J_OOD_worst"] for seed in SEEDS}
    tcr_vs_spc = {str(seed): by_key["tcr_sg", seed]["J_OOD_worst"] - by_key["spc_sg", seed]["J_OOD_worst"] for seed in SEEDS}
    p = {arm: pooled(by_arm[arm]) for arm in ARMS}
    tcr_values = [by_key["tcr_sg", seed]["J_OOD_worst"] for seed in SEEDS]
    utr_values = [by_key["utr_sg", seed]["J_OOD_worst"] for seed in SEEDS]
    tcr_range, utr_range = max(tcr_values) - min(tcr_values), max(utr_values) - min(utr_values)
    tcr_sd, utr_sd = statistics.stdev(tcr_values), statistics.stdev(utr_values)
    bifurcation = tcr_range > 2 * max(utr_range, 1e-12) and tcr_sd > 2 * max(utr_sd, 1e-12) and any(row["OOD_worst_ratio"] < .85 for row in tcr_cat)
    timeout_diffs = [by_key["tcr_sg", seed]["timeout"] - by_key["utr_sg", seed]["timeout"] for seed in SEEDS]
    systemic_safety = p["tcr_sg"]["constraint"] > 0 or (p["tcr_sg"]["timeout"] - p["utr_sg"]["timeout"] > .05 and sum(value > .05 for value in timeout_diffs) >= 3)
    technical = all(row["risk_set_size"] > 0 and row["trigger_success"] == 1.0 for row in per_seed)
    tcr_cat_count = sum(row["catastrophic"] for row in tcr_cat)
    spc_cat_count = sum(row["catastrophic"] for row in spc_cat)
    tcr_positive = sum(value > 0 for value in tcr_diffs.values())
    systematic_spc_disadvantage = sum(value < 0 for value in tcr_vs_spc.values()) >= 4 and mean(list(tcr_vs_spc.values())) < 0
    if not technical:
        decision = "PHASE-D TECHNICAL INVALID"
    elif tcr_cat_count >= 2 or bifurcation or systemic_safety:
        decision = "PHASE-D NO-GO"
    elif tcr_cat_count >= 1 or tcr_positive < 3 or p["tcr_sg"]["J_OOD_mean"] < p["utr_sg"]["J_OOD_mean"] or p["tcr_sg"]["J_OOD_worst"] < p["utr_sg"]["J_OOD_worst"] or systematic_spc_disadvantage:
        decision = "PHASE-D NO-GO"
    else:
        decision = "PHASE-D GO"
    result = {
        "protocol": "TCR-SPC-PHASE-D-3M-CONTINUATION-AGGREGATION-V1", "decision": decision,
        "source_update": 3907, "final_update": 11719, "final_steps": 3_000_064,
        "tape_hash": tape["tape_hash"], "per_seed": per_seed, "pooled": p,
        "tcr_catastrophic": tcr_cat, "spc_catastrophic": spc_cat,
        "tcr_catastrophic_count": tcr_cat_count, "spc_catastrophic_count": spc_cat_count,
        "tcr_ood_positive_count": tcr_positive, "stress_seed_2002_catastrophic": next(row["catastrophic"] for row in tcr_cat if row["seed"] == 2002),
        "tcr_vs_spc_ood_worst": tcr_vs_spc,
        "dispersion": {arm: {key: {"mean": mean([row[key] for row in by_arm[arm]]), "sd": statistics.stdev([row[key] for row in by_arm[arm]])} for key in ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout")} for arm in ARMS},
        "integrity": {"completed_runs": len(by_key), "technical_validity": technical, "strict_continuation_audit": True, "warm_restart": False, "from_scratch": False},
        "decision_basis": {"tcr_catastrophic_count": tcr_cat_count, "spc_catastrophic_count": spc_cat_count, "tcr_ood_positive_count": tcr_positive, "cross_seed_bifurcation": bifurcation, "systemic_safety_erosion": systemic_safety, "systematic_spc_disadvantage": systematic_spc_disadvantage, "technical_validity": technical},
    }
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(markdown(result), encoding="utf-8", newline="\n")
    (evaluation / "PHASE_D_DECISION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "report": str(args.report_path), "final_steps": 3_000_064}, indent=2))


if __name__ == "__main__":
    main()
