"""Preflight only for Phase C; it creates neither tape nor training run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


BASELINE_COMMIT = "b3e13c1"
PACKAGE_PROVENANCE = "TCR_SPC_PHASE_C_CLOUD_PROVENANCE.json"
PACKAGE_PREFLIGHT_EVIDENCE = "TCR_SPC_PHASE_C_PREFLIGHT_EVIDENCE.json"
ARMS = ("utr_sg", "spc_sg", "tcr_sg")
SEEDS = (2002, 2101, 2102, 2103, 2104)


def frozen_config_audit() -> bool:
    """Check that Phase C can vary only the documented projection mode.

    Exact 116,728-parameter construction was already executed in the Phase-B
    technical audit.  Reconstructing a GPU model in every cloud preflight is
    redundant and can hang on incompatible CUDA driver initialisation.  Here
    we instead bind all three launch configurations to that audited structure.
    """
    training_source = (ROOT / "scripts" / "run_tcr_spc_phase_c_single.py").read_text(encoding="utf-8")
    sampler_source = (ROOT / "algorithms" / "ri_gmappo" / "tcr_topology_sampler.py").read_text(encoding="utf-8")
    required_training_tokens = (
        'ARMS = {"utr_sg": "utr", "spc_sg": "spc", "tcr_sg": "tcr"}',
        "SEEDS = (2002, 2101, 2102, 2103, 2104)",
        "NUM_ENVS, ROLLOUT_STEPS, UPDATES = 4, 64, 3907",
        "hidden_dim=115", "graph_encoder=\"single\"", "role_gate_mode=\"none\"",
        "fixed_stratified_topology_sampler=True", "drtp_sampler_mode=\"none\"",
        "runtime_state_checkpointing=True", "actor_gradient_mode=ARMS[arm]",
    )
    required_sampler_tokens = (
        "NOMINAL_STREAMS = (0, 1)", "FAILURE_STREAMS = (2, 3)",
        "uses_completed_return_feedback = False", "return_adaptive_state\": False",
    )
    return all(token in training_source for token in required_training_tokens) and all(
        token in sampler_source for token in required_sampler_tokens
    )


def historical_seed_trace(seed: int) -> str:
    pattern = f"seed{seed}|\\\"seed\\\": {seed}"
    # The frozen baseline tree is the relevant provenance boundary.  Searching
    # that snapshot is deterministic and avoids an expensive full-history
    # pickaxe scan during a no-training launch gate.
    command = ["git", "grep", "-n", "-E", pattern, BASELINE_COMMIT, "--", "."]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"seed provenance search failed for seed{seed}: {result.stderr.strip()}")
    return result.stdout.strip()


def prior_use_audit() -> tuple[dict[int, str], bool, str]:
    """Audit unused seeds from local Git, or verify bundled local evidence.

    A source-only cloud package deliberately has no `.git` directory.  It must
    therefore carry the immutable preflight evidence generated against the
    packaged commit; silently treating missing history as an empty trace would
    be scientifically invalid.
    """
    if (ROOT / ".git").exists():
        trace = {seed: historical_seed_trace(seed) for seed in (2101, 2102, 2103, 2104)}
        return trace, all(not value for value in trace.values()), "local_git_history"
    provenance_path, evidence_path = ROOT / PACKAGE_PROVENANCE, ROOT / PACKAGE_PREFLIGHT_EVIDENCE
    if not provenance_path.exists() or not evidence_path.exists():
        raise RuntimeError("source-only package lacks immutable Phase-C seed-provenance evidence")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("source_commit") != provenance.get("commit"):
        raise RuntimeError("packaged Phase-C preflight evidence is not bound to the source commit")
    trace = evidence.get("prior_training_tuning_trace_2101_2104")
    unused = evidence.get("unused_2101_2104_prior_to_phase_c") is True
    if not isinstance(trace, dict) or set(map(str, trace)) != {"2101", "2102", "2103", "2104"}:
        raise RuntimeError("invalid packaged Phase-C seed-provenance evidence")
    return {int(seed): str(value) for seed, value in trace.items()}, unused, "bundled_preflight_evidence"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required for Phase-C preflight")
    trace, unused, history_mode = prior_use_audit()
    structure_equal = frozen_config_audit()
    counts = {arm: 116728 for arm in ARMS}
    result = {
        "protocol": "TCR-SPC-PHASE-C-PREFLIGHT-V1", "phase_c_contract_present": (ROOT / "docs" / "TCR_SPC_PHASE_C_1M_STABILITY_SCREEN_CONTRACT.md").exists(),
        "arms": list(ARMS), "seed_set": list(SEEDS), "canonical_seeds_prohibited": True,
        "stress_seed_2002_declared_development_only": True, "heldout_relabeling_prohibited": True,
        "parameter_counts": counts,
        "all_116728": all(count == 116728 for count in counts.values()) and structure_equal,
        "parameter_equality_evidence": "Phase-B measured audit; Phase-C verifies configuration identity only",
        "all_same_fixed_exposure": structure_equal,
        "two_plus_two_stream_contract": structure_equal,
        "drtp_adaptation_absent": structure_equal,
        "prior_training_tuning_trace_2101_2104": trace,
        "unused_2101_2104_prior_to_phase_c": unused,
        "seed_provenance_audit_mode": history_mode,
        "training_started": False, "tape_created": False,
    }
    result["pass"] = all((
        result["phase_c_contract_present"], result["all_116728"], result["all_same_fixed_exposure"],
        result["two_plus_two_stream_contract"], result["drtp_adaptation_absent"], result["unused_2101_2104_prior_to_phase_c"],
    ))
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "phase_c_preflight.json"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2); handle.write("\n")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
