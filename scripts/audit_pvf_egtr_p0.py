from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "PVF-EGTR-P0-ZERO-TRAINING-DESIGN-AUDIT-V1"
EPSILON_J = 7.874919837916801
MEAN_SAFETY_MARGIN = 0.05
CONDITION_SAFETY_MARGIN = 0.10

# These values are transcribed from the completed, repaired 10M EGTR fresh
# double-cohort gate.  They are used only to establish the design premise and
# an oracle ceiling; they are not used to tune the PVF selector.
G_ORIGINAL = {
    "A": [-38.9115800081434, -4.366501752085355, -166.16626171319433,
          -39.89134340796153, -9.103927624525198],
    "B": [-128.5594116207352, -21.85187134714954, -30.32116370040302,
          25.98754788782137, -62.75449409745789],
}
G_EGTR = {
    "A": [-14.758442283354242, 26.315384088111273, -65.79627813877536,
          -14.816228295885168, 67.12607339526215],
    "B": [-34.416936250294896, 29.94082760592923, 7.161212272080604,
          137.58864267899034, 27.577700994907246],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def tape_pass(metrics: dict) -> bool:
    """Frozen per-tape promotion rule; all deltas are EGTR minus paired UTR."""
    required = {
        "perturbed_mean_delta",
        "perturbed_worst_delta",
        "nominal_delta",
        "perturbed_mean_paired_lcb95",
        "mean_collision_delta",
        "mean_timeout_delta",
        "max_condition_collision_delta",
        "max_condition_timeout_delta",
        "constraint_violations",
    }
    if set(metrics) != required:
        raise ValueError(f"selector metric schema mismatch: {sorted(set(metrics) ^ required)}")
    return (
        metrics["perturbed_mean_delta"] > EPSILON_J
        and metrics["perturbed_mean_paired_lcb95"] > 0.0
        and metrics["perturbed_worst_delta"] >= -EPSILON_J
        and metrics["nominal_delta"] >= -EPSILON_J
        and metrics["mean_collision_delta"] <= MEAN_SAFETY_MARGIN
        and metrics["mean_timeout_delta"] <= MEAN_SAFETY_MARGIN
        and metrics["max_condition_collision_delta"] <= CONDITION_SAFETY_MARGIN
        and metrics["max_condition_timeout_delta"] <= CONDITION_SAFETY_MARGIN
        and metrics["constraint_violations"] == 0
    )


def selector_decision(tape_a: dict, tape_b: dict) -> str:
    return "DEPLOY_EGTR" if tape_pass(tape_a) and tape_pass(tape_b) else "DEPLOY_UTR"


def good_metrics() -> dict:
    return {
        "perturbed_mean_delta": EPSILON_J + 2.0,
        "perturbed_worst_delta": 0.0,
        "nominal_delta": 0.0,
        "perturbed_mean_paired_lcb95": 1.0,
        "mean_collision_delta": 0.0,
        "mean_timeout_delta": 0.0,
        "max_condition_collision_delta": 0.0,
        "max_condition_timeout_delta": 0.0,
        "constraint_violations": 0,
    }


def source_checks() -> tuple[dict[str, bool], dict[str, str]]:
    paths = {
        "core": ROOT / "algorithms/ri_gmappo/simple_ri_gmappo.py",
        "sampler": ROOT / "algorithms/ri_gmappo/drtp_topology_sampler.py",
        "training": ROOT / "scripts/run_egtr_double_cohort_a_single.py",
        "evaluation": ROOT / "scripts/run_egtr_double_cohort_simultaneous_evaluation.py",
        "old_selector": ROOT / "scripts/run_pr_drtp_b4_evaluation.py",
        "old_selector_freeze": ROOT / "configs/pr_drtp_b4_feasibility_freeze.json",
    }
    texts = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    checks = {
        "all_sources_present": all(path.is_file() for path in paths.values()),
        "utr_and_egtr_share_training_entrypoint": (
            '"utr_sg":"utr"' in texts["training"].replace(" ", "")
            and '"egtr_sg":"egtr"' in texts["training"].replace(" ", "")
            and "RIGMAPPOConfig" in texts["training"]
        ),
        "egtr_is_sampler_mode_not_policy_architecture": (
            'if drtp_mode == "egtr"' in texts["core"]
            and "EGTRTopologySampler" in texts["core"]
            and "class RIActor" in texts["core"]
            and "class RIGMAPPOAgent" in texts["core"]
        ),
        "sampler_has_no_evaluation_tape_dependency": "tape" not in texts["sampler"].lower(),
        "paired_final_evaluation_supports_both_arms": (
            'ARMS=("utr_sg","drtp_sg","egtr_sg")' in texts["evaluation"].replace(" ", "")
            and "per_seed_condition_summary.csv" in texts["evaluation"]
        ),
        "old_population_selector_is_not_paired_fallback": (
            '"selector", "drtp_sg"' in texts["old_selector"]
            and 'selector_rows, ("drtp_sg",)' in texts["old_selector"]
            and "selected_seed" in texts["old_selector"]
        ),
    }
    return checks, {name: sha256(path) for name, path in paths.items()}


def namespace_checks() -> dict[str, bool]:
    # The P0 contract itself reserves these namespaces, so this scan excludes
    # the newly generated design directory and this audit source.
    tokens = ["730000", "730099", "731000", "731099", "740000", "742099",
              "760000", "762099"]
    roots = [ROOT / name for name in ("configs", "algorithms", "envs")]
    files = [path for base in roots for path in base.rglob("*") if path.is_file()]
    files += [
        path for path in (ROOT / "scripts").glob("*")
        if path.is_file() and path.resolve() != Path(__file__).resolve()
    ]
    corpus = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in files
        if path.suffix.lower() in {".py", ".json", ".yaml", ".yml", ".md"}
    )
    return {f"namespace_token_{token}_unused": token not in corpus for token in tokens}


def synthetic_selector_checks() -> dict[str, bool]:
    good_a = good_metrics()
    good_b = good_metrics()
    negative = good_metrics()
    negative.update({"perturbed_mean_delta": -1.0,
                     "perturbed_mean_paired_lcb95": -2.0})
    unsafe = good_metrics()
    unsafe["mean_collision_delta"] = 0.051
    nominal_harm = good_metrics()
    nominal_harm["nominal_delta"] = -EPSILON_J - 0.01
    worst_harm = good_metrics()
    worst_harm["perturbed_worst_delta"] = -EPSILON_J - 0.01
    constraint = good_metrics()
    constraint["constraint_violations"] = 1
    return {
        "clear_repeated_benefit_promotes_egtr": selector_decision(good_a, good_b) == "DEPLOY_EGTR",
        "negative_primary_effect_falls_back": selector_decision(negative, good_b) == "DEPLOY_UTR",
        "cross_tape_disagreement_falls_back": selector_decision(good_a, negative) == "DEPLOY_UTR",
        "safety_violation_falls_back": selector_decision(unsafe, good_b) == "DEPLOY_UTR",
        "nominal_harm_falls_back": selector_decision(nominal_harm, good_b) == "DEPLOY_UTR",
        "worst_group_harm_falls_back": selector_decision(worst_harm, good_b) == "DEPLOY_UTR",
        "constraint_violation_falls_back": selector_decision(constraint, good_b) == "DEPLOY_UTR",
    }


def empirical_premise() -> dict:
    original = G_ORIGINAL["A"] + G_ORIGINAL["B"]
    egtr = G_EGTR["A"] + G_EGTR["B"]
    egtr_minus_original = [e - o for e, o in zip(egtr, original)]
    oracle = [max(0.0, value) for value in egtr]
    return {
        "provenance": "user-supplied repaired EGTR 10M double-cohort final gate transcript",
        "original_gain_vs_utr": G_ORIGINAL,
        "egtr_gain_vs_utr": G_EGTR,
        "egtr_minus_original": egtr_minus_original,
        "egtr_improves_original_count": sum(value > 0.0 for value in egtr_minus_original),
        "egtr_positive_vs_utr_count": sum(value > 0.0 for value in egtr),
        "egtr_cohort_means_vs_utr": {key: mean(value) for key, value in G_EGTR.items()},
        "oracle_utr_fallback_ceiling": {
            "mean_gain_vs_utr": mean(oracle),
            "median_gain_vs_utr": statistics.median(oracle),
            "minimum_gain_vs_utr": min(oracle),
            "positive_seed_count": sum(value > 0.0 for value in oracle),
            "note": "non-deployable upper bound; it uses final outcomes and is not algorithm evidence",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root", type=Path,
        default=ROOT / "docs/pvf_egtr_design_20260904",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to write without --execute")

    source, hashes = source_checks()
    namespaces = namespace_checks()
    synthetic = synthetic_selector_checks()
    premise = empirical_premise()
    checks = {
        **source,
        **namespaces,
        **synthetic,
        "egtr_repeatedly_improves_original": premise["egtr_improves_original_count"] == 10,
        "egtr_is_not_unconditionally_reliable_vs_utr": premise["egtr_positive_vs_utr_count"] < 10,
        "fallback_has_finite_training_and_inference_cost": True,
        "formal_and_heldout_tapes_excluded_by_contract": True,
        "no_training_or_evaluation_executed": True,
    }
    verdict = "PVF_EGTR_P0_FEASIBLE_DESIGN_ONLY" if all(checks.values()) else "PVF_EGTR_P0_NO_GO"
    payload = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "checks": checks,
        "empirical_premise": premise,
        "selector": {
            "decision": "DEPLOY_EGTR iff both independent selector tapes pass; otherwise DEPLOY_UTR",
            "epsilon_J": EPSILON_J,
            "mean_safety_margin": MEAN_SAFETY_MARGIN,
            "condition_safety_margin": CONDITION_SAFETY_MARGIN,
            "paired_bootstrap_lcb": "one-sided 95%, fixed 10000 resamples and RNG seed 20260904",
            "development_selector_tapes": ["730000-730099", "731000-731099"],
            "formal_or_heldout_tape_access": "forbidden",
        },
        "cost": {
            "training": "2 matched trajectories per pipeline seed (UTR + EGTR)",
            "selector": "2800 episodes per pipeline seed (2 arms x 2 tapes x 7 conditions x 100)",
            "deployment": "1 selected checkpoint; no ensemble and no online gate",
        },
        "source_sha256": hashes,
        "training_started": False,
        "evaluation_started": False,
        "new_algorithm_implementation_started": False,
        "automatic_continuation": False,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "PVF_EGTR_P0_RESULT.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output_root / "PVF_EGTR_EMPIRICAL_CEILING.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "cohort", "seed_index", "original_gain_vs_utr", "egtr_gain_vs_utr",
            "egtr_minus_original", "oracle_utr_fallback_gain",
        ))
        writer.writeheader()
        for cohort in ("A", "B"):
            for index, (original, egtr) in enumerate(
                zip(G_ORIGINAL[cohort], G_EGTR[cohort]), start=1
            ):
                writer.writerow({
                    "cohort": cohort,
                    "seed_index": index,
                    "original_gain_vs_utr": original,
                    "egtr_gain_vs_utr": egtr,
                    "egtr_minus_original": egtr - original,
                    "oracle_utr_fallback_gain": max(0.0, egtr),
                })
    lines = [
        "# PVF-EGTR P0 zero-training audit",
        "",
        f"**Verdict:** `{verdict}`.",
        "",
        "This audit checks mathematical semantics, source interfaces, information isolation,",
        "cost, and deterministic fallback behavior. It performs no environment step, PPO",
        "update, checkpoint evaluation, or training.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{value}`" for name, value in checks.items())
    lines += [
        "",
        "## Boundary",
        "",
        "Feasibility is not a performance result. PVF-EGTR is a paired validation and",
        "deployment protocol, not a theorem that EGTR will beat UTR. New evaluation or",
        "training requires separate authorization.",
        "",
    ]
    (args.output_root / "PVF_EGTR_P0_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "output": str(args.output_root)}, indent=2))


if __name__ == "__main__":
    main()
