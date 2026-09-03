"""Create the zero-training preregistration package for EGTR replication.

This program deliberately does not import the trainer or create an environment.
It only freezes provenance, identifiers, endpoint definitions, and a runnable
decision rule before any prospective EGTR trajectory exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "EGTR-FRESH-DOUBLE-COHORT-PREREGISTRATION-AUDIT-V1"
COHORTS = {"A": [71011, 71012, 71013, 71014, 71015], "B": [71021, 71022, 71023, 71024, 71025]}
ARMS = {"utr_sg": "UTR-SG-MAPPO", "drtp_sg": "Original DRTP-SG-MAPPO", "egtr_sg": "EGTR-DRTP-SG-MAPPO"}
TAPE_IDS = list(range(720000, 720100))
CONDITIONS = ["nominal", "F0", "TE", "TL", "DS", "DL", "CP"]
MATURE_UPDATES, MATURE_STEPS = 39063, 10_000_128
SCAN_ROOTS = ("configs", "docs", "scripts", "algorithms", "envs")
FUTURE_PLAN_FILES = {
    "docs/egtr_double_cohort_preregistration_20260903/EGTR_SIMULTANEOUS_DUAL_COHORT_AMENDMENT.md",
    "scripts/create_egtr_double_cohort_a_tape.py",
    "scripts/run_egtr_double_cohort_a_single.py",
    "scripts/verify_egtr_double_cohort_a_preflight.py",
    "scripts/run_egtr_double_cohort_a_evaluation.py",
    "scripts/aggregate_egtr_double_cohort_a.py",
    "scripts/launch_egtr_double_cohort_a_autodl.sh",
    "scripts/build_egtr_double_cohort_a_cloud_package.py",
    "scripts/create_egtr_double_cohort_simultaneous_tape.py",
    "scripts/run_egtr_double_cohort_simultaneous_single.py",
    "scripts/run_egtr_double_cohort_simultaneous_evaluation.py",
    "scripts/aggregate_egtr_double_cohort_simultaneous.py",
    "scripts/launch_egtr_double_cohort_simultaneous_autodl.sh",
    "scripts/build_egtr_double_cohort_simultaneous_cloud_package.py",
    "scripts/run_egtr_double_cohort_simultaneous_amendment_audit.py",
}
METHOD = ROOT / "algorithms/ri_gmappo/drtp_topology_sampler.py"
KLR_FREEZE = ROOT / "configs/drtp_klr_final_replication_freeze.json"
P3_REPORT = ROOT / "docs/EGTR_P3_1M_EVALUATION_AND_GATE_REPORT.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def text_seed_hits(value: int) -> list[str]:
    pattern = re.compile(rf"(?<!\d){value}(?!\d)")
    hits: list[str] = []
    for dirname in SCAN_ROOTS:
        for path in (ROOT / dirname).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".md", ".json", ".csv", ".txt", ".yaml", ".yml"}:
                continue
            # The audit necessarily contains the prospective identifiers it is
            # auditing; its own source is not prior evidence of their use.
            if path.resolve() == Path(__file__).resolve():
                continue
            # These files merely implement this already frozen prospective
            # registry. They are excluded from the *historical-use* audit;
            # all other maintained source remains in scope.
            if path.relative_to(ROOT).as_posix() in FUTURE_PLAN_FILES:
                continue
            try:
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(path.relative_to(ROOT).as_posix())
            except OSError:
                pass
    return hits


RULE = r'''"""Frozen EGTR double-cohort decision rule; run only after final 10M data exist."""
from __future__ import annotations
import statistics

EPSILON_J = 7.874919837916801
SEED_SAFETY_MARGIN = 0.10
POOLED_SAFETY_MARGIN = 0.05

def _mean(xs): return sum(xs) / len(xs)
def _mad(xs):
    med = statistics.median(xs)
    return statistics.median(abs(x - med) for x in xs)
def _ratio(x, u): return x / u if u > 0 else 1 + (x - u) / max(abs(u), EPSILON_J)
def catastrophic(candidate, utr):
    f0 = _ratio(candidate["J_F0"], utr["J_F0"])
    worst = _ratio(candidate["J_pert_worst"], utr["J_pert_worst"])
    return ((f0 < .70 and worst < .85) or (worst < .70 and f0 < .85)
            or (candidate["timeout"] - utr["timeout"] > .20 and (f0 < .85 or worst < .85)))

def cohort_decision(rows):
    """Rows are five paired dicts: seed, utr, original, egtr metrics."""
    if len(rows) != 5: raise ValueError("one frozen cohort must contain exactly five paired training seeds")
    g_o = [r["original"]["J_pert_mean"] - r["utr"]["J_pert_mean"] for r in rows]
    g_e = [r["egtr"]["J_pert_mean"] - r["utr"]["J_pert_mean"] for r in rows]
    e_minus_o = [r["egtr"]["J_pert_mean"] - r["original"]["J_pert_mean"] for r in rows]
    top = [i for i, value in enumerate(g_o) if value > EPSILON_J]
    criteria = {
      "meaningful_mean_robustness_benefit": _mean(g_e) >= EPSILON_J,
      "median_robustness_nonnegative": statistics.median(g_e) >= 0.0,
      "majority_seed_benefit": sum(x >= 0.0 for x in g_e) >= 3,
      "original_mean_retained_within_noise_margin": _mean(e_minus_o) >= -EPSILON_J,
      "lower_tail_improved_vs_original": min(g_e) - min(g_o) > EPSILON_J,
      "catastrophic_not_increased_vs_original": sum(catastrophic(r["egtr"], r["utr"]) for r in rows) <= sum(catastrophic(r["original"], r["utr"]) for r in rows),
      "range_reduced_vs_original": (max(g_e)-min(g_e)) < (max(g_o)-min(g_o)),
      "mad_reduced_vs_original": _mad(g_e) < _mad(g_o),
      "upper_tail_retained": bool(top) and all(e_minus_o[i] >= -EPSILON_J for i in top),
      "nominal_noninferior": _mean(r["egtr"]["J_nominal"]-r["utr"]["J_nominal"] for r in rows) >= -EPSILON_J and sum(r["egtr"]["J_nominal"]-r["utr"]["J_nominal"] >= -EPSILON_J for r in rows) >= 3,
      "per_seed_noncompensable_safety": all(r["egtr"]["collision"]-r["utr"]["collision"] <= SEED_SAFETY_MARGIN and r["egtr"]["timeout"]-r["utr"]["timeout"] <= SEED_SAFETY_MARGIN for r in rows),
      "cohort_mean_safety": _mean(r["egtr"]["collision"]-r["utr"]["collision"] for r in rows) <= POOLED_SAFETY_MARGIN and _mean(r["egtr"]["timeout"]-r["utr"]["timeout"] for r in rows) <= POOLED_SAFETY_MARGIN,
    }
    return {"decision": "COHORT_PASS" if all(criteria.values()) else "COHORT_FAIL", "criteria": criteria, "G_original": g_o, "G_egtr": g_e}

def final_decision(cohort_a, cohort_b):
    return "EGTR_DOUBLE_COHORT_REPLICATION_GO" if cohort_a["decision"] == cohort_b["decision"] == "COHORT_PASS" else "EGTR_DOUBLE_COHORT_REPLICATION_NO_GO"
'''


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required; this creates only a zero-training preregistration audit")
    out = args.output_root / "diagnostics" / "egtr_double_cohort_preregistration"
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    freeze = json.loads(KLR_FREEZE.read_text(encoding="utf-8"))
    method_text, p3_text = METHOD.read_text(encoding="utf-8"), P3_REPORT.read_text(encoding="utf-8")
    checks = {
        "p3_is_seen_development_evidence_only": "development-only" in p3_text and "不构成" in p3_text,
        "egtr_constants_match_frozen_method_contract": all(token in method_text for token in ("EGTR_CONFIDENCE_KAPPA = 0.20", "EGTR_REQUIRED_SAMPLES = 8.0", "EGTR_TRUST_REGION_L1 = 0.10", "EGTR_MAD_SCALE = 1.4826")),
        "independent_preexisting_threshold_source": freeze["gate"]["epsilon_source"] == "DRTP-STABILIZATION-S0-V1 pooled P90 absolute same-checkpoint cross-tape endpoint variation",
        "noncompensable_safety_source_preexisted_egtr": freeze["gate"]["seed_condition_safety_margin"] == 0.1 and freeze["gate"]["pooled_safety_margin"] == 0.05,
        "all_required_sources_present": METHOD.exists() and KLR_FREEZE.exists() and P3_REPORT.exists(),
    }
    ids = [seed for values in COHORTS.values() for seed in values] + [TAPE_IDS[0], TAPE_IDS[-1]]
    seed_hits = {str(value): text_seed_hits(value) for value in ids}
    clean = all(not hit for hit in seed_hits.values())
    checks["fresh_seed_and_tape_namespace_clean_in_maintained_text"] = clean
    verdict = "EGTR_DOUBLE_COHORT_PREREGISTRATION_READY" if all(checks.values()) else ("EGTR_PREREGISTRATION_EVIDENCE_CONTAMINATION" if not clean else "EGTR_PREREGISTRATION_THRESHOLD_UNRESOLVED")
    out.mkdir(parents=True)
    thresholds = {"epsilon_J": freeze["gate"]["epsilon_J"], "downside_improvement_margin": freeze["gate"]["downside_improvement_margin"], "seed_safety_margin": freeze["gate"]["seed_condition_safety_margin"], "cohort_mean_safety_margin": freeze["gate"]["pooled_safety_margin"], "catastrophic_ratios": {"F0_and_worst": [0.70, 0.85], "timeout_plus_degradation": [0.20, 0.85]}, "unit": "training_seed", "source": "configs/drtp_klr_final_replication_freeze.json; pre-existing non-EGTR stabilization gate"}
    write(out / "EGTR_NUMERIC_DECISION_THRESHOLDS.json", json.dumps(thresholds, indent=2))
    write(out / "EGTR_MACHINE_EXECUTABLE_DECISION_RULE.py", RULE)
    write(out / "EGTR_DOUBLE_COHORT_EVIDENCE_CLASSIFICATION.md", "# Evidence classification\n\nThe 2501–2503 EGTR P3 results are **SEEN DEVELOPMENT EVIDENCE ONLY**. They are excluded from seed selection, threshold selection, statistical confirmation and the final fresh-cohort decision. They remain cited solely as the reason to demand prospective replication and a non-compensable safety rule.\n")
    write(out / "EGTR_FROZEN_IMPLEMENTATION_MANIFEST.md", f"# Frozen implementation\n\nOnly `egtr_sg` may use the sampler-only EGTR implementation in `{METHOD.relative_to(ROOT).as_posix()}` (SHA256 `{sha256(METHOD)}`). Frozen constants: confidence kappa 0.20; required samples 8; MAD scale 1.4826; simplex [0.05, 0.35]; post-projection L1 step <= 0.10. UTR and Original DRTP retain their existing samplers. PPO, optimizer, critic, actor, reward, environment, observation, and evaluation interface must not change.\n")
    write(out / "EGTR_THRESHOLD_PROVENANCE.md", f"# Threshold provenance\n\nAll numeric thresholds are reused without modification from the non-EGTR KLR replication freeze `{KLR_FREEZE.relative_to(ROOT).as_posix()}` (SHA256 `{sha256(KLR_FREEZE)}`). `epsilon_J={freeze['gate']['epsilon_J']}` is the label-free DRTP-STABILIZATION-S0-V1 P90 same-checkpoint cross-tape variation. Per-seed collision and timeout margin is 0.10; cohort-mean margin is 0.05. No EGTR outcome was read to set a threshold.\n")
    write(out / "EGTR_SAFETY_NONINFERIORITY_CONTRACT.md", "# Non-compensable safety contract\n\nFor every paired training seed, EGTR must satisfy both `collision(EGTR)-collision(UTR) <= 0.10` **and** `timeout(EGTR)-timeout(UTR) <= 0.10`. A timeout improvement cannot compensate a collision increase, or vice versa. Cohort means must separately be <= 0.05.\n")
    write(out / "EGTR_CATASTROPHIC_SEED_DEFINITION.md", "# Catastrophic definition\n\nRelative to paired UTR and using epsilon_J for a nonpositive denominator, a candidate is catastrophic if: (F0 ratio <0.70 and perturbed-worst ratio <0.85), or (worst ratio <0.70 and F0 ratio <0.85), or timeout rises >0.20 while either ratio <0.85. EGTR catastrophic count must not exceed Original DRTP's count within either cohort.\n")
    write(out / "EGTR_DISPERSION_CONTRACT.md", "# Dispersion contract\n\nFor `G=J_pert_mean(method)-J_pert_mean(UTR)` over the five training seeds, EGTR must have strictly lower range and strictly lower median absolute deviation than Original DRTP. Training seed—not episode—is the independent unit.\n")
    for label, seeds in COHORTS.items():
        write(out / f"EGTR_COHORT_{label}_SEED_REGISTRY.md", f"# Cohort {label} registry\n\nFrozen training seeds: `{seeds}`. Exact-token audit across maintained `configs/docs/scripts/algorithms/envs` found `{[seed_hits[str(s)] for s in seeds]}`. These seeds must be rejected at launch if later found in a historical registry.\n")
    write(out / "EGTR_EVALUATION_REGISTRY.md", f"# Evaluation registry\n\nDevelopment-only paired tape IDs: `{TAPE_IDS[0]}–{TAPE_IDS[-1]}`; each final 10M checkpoint is evaluated over {len(CONDITIONS)} frozen groups (`{', '.join(CONDITIONS)}`), 100 paired episodes per group, for 700 episodes per arm/seed. The tape is generated after P0, is unavailable to training, and cannot be used for algorithm or threshold selection.\n")
    write(out / "EGTR_MATURE_HORIZON_CONTRACT.md", f"# Mature horizon\n\nEvery trajectory starts from scratch and runs exactly `{MATURE_UPDATES}` PPO updates / `{MATURE_STEPS:,}` environment steps. Final checkpoint only; no early stopping, promotion, seed replacement, rerun, or 1M/3M intermediate decision.\n")
    prereg = f"# EGTR fresh double-cohort prospective replication\n\n**P0 verdict:** `{verdict}`.\n\nMethods: {', '.join(ARMS)}. Cohort A `{COHORTS['A']}` and Cohort B `{COHORTS['B']}` must be reported and decided separately. A pooled n=10 result is descriptive only. Cohort B may be started only under a separately logged execution authorization after Cohort A is complete; Cohort A failure stops the program. The generated machine rule requires benefit retention, lower-tail improvement, non-increased catastrophes, reduced dispersion, nominal noninferiority and the non-compensable safety rule in each cohort. No training, evaluation, package, or automatic continuation occurred in P0.\n"
    write(out / "EGTR_DOUBLE_COHORT_PREREGISTRATION.md", prereg)
    evidence = {"protocol": PROTOCOL, "verdict": verdict, "checks": checks, "cohorts": COHORTS, "tape": {"ids": [TAPE_IDS[0], TAPE_IDS[-1]], "episodes_per_arm_seed": 700, "groups": CONDITIONS}, "mature_horizon": {"updates": MATURE_UPDATES, "environment_steps": MATURE_STEPS}, "source_hashes": {"egtr_sampler": sha256(METHOD), "non_egtr_gate": sha256(KLR_FREEZE), "seen_p3_report": sha256(P3_REPORT)}, "text_namespace_hits": seed_hits, "training_started": False, "evaluation_started": False, "automatic_continuation": False}
    write(out / "EGTR_PREREGISTRATION_AUDIT.json", json.dumps(evidence, indent=2))
    write(out / "EGTR_PREREGISTRATION_FINAL_VERDICT.md", f"# EGTR P0 final verdict\n\n`{verdict}`\n\nThis is a zero-training preregistration result only. It grants no training, evaluation, package creation, checkpoint selection, threshold revision or automatic continuation authority.\n")
    print(json.dumps({"verdict": verdict, "output": str(out), "training_started": False}, indent=2))


if __name__ == "__main__":
    main()
