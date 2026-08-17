"""Preflight only for Phase C; it creates neither tape nor training run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env  # noqa: E402
from algorithms.ri_gmappo.tcr_topology_sampler import FixedStratifiedTopologySampler  # noqa: E402
from scripts.run_tcr_spc_phase_c_single import ARMS, SEEDS, training_config  # noqa: E402


BASELINE_COMMIT = "b3e13c1"
PACKAGE_PROVENANCE = "TCR_SPC_PHASE_C_CLOUD_PROVENANCE.json"
PACKAGE_PREFLIGHT_EVIDENCE = "TCR_SPC_PHASE_C_PREFLIGHT_EVIDENCE.json"


def parameter_count(arm: str) -> int:
    config = training_config(arm, 2101, ROOT / ".phase_c_preflight")
    # This preflight only instantiates the fixed architecture.  CPU avoids
    # device initialization and guarantees that it cannot consume training GPU.
    config.device = "cpu"
    env = make_env(config, 2101, training=False)
    _, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none", use_intent_context=False,
    )
    return sum(parameter.numel() for parameter in agent.parameters() if parameter.requires_grad)


def historical_seed_trace(seed: int) -> str:
    pattern = f"seed{seed}|\\\"seed\\\": {seed}"
    command = ["git", "log", BASELINE_COMMIT, "-G", pattern, "--format=%H"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
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
    sampler = FixedStratifiedTopologySampler(2101, 4)
    manifest = sampler.manifest()
    trace, unused, history_mode = prior_use_audit()
    counts = {arm: parameter_count(arm) for arm in ARMS}
    result = {
        "protocol": "TCR-SPC-PHASE-C-PREFLIGHT-V1", "phase_c_contract_present": (ROOT / "docs" / "TCR_SPC_PHASE_C_1M_STABILITY_SCREEN_CONTRACT.md").exists(),
        "arms": list(ARMS), "seed_set": list(SEEDS), "canonical_seeds_prohibited": True,
        "stress_seed_2002_declared_development_only": True, "heldout_relabeling_prohibited": True,
        "parameter_counts": counts,
        "all_116728": all(count == 116728 for count in counts.values()),
        "all_same_fixed_exposure": manifest["nominal_mass"] == 0.5 and manifest["conditional_failure_weights"] == {group: 1.0 / 6.0 for group in manifest["failure_groups"]},
        "two_plus_two_stream_contract": manifest["nominal_streams"] == [0, 1] and manifest["failure_streams"] == [2, 3],
        "drtp_adaptation_absent": manifest["return_adaptive_state"] is False,
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
