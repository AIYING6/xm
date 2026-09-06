"""Validate final DRTP A/B assets and a fresh held-out/OOD environment contract.

This verifier never opens a policy checkpoint, evaluation tape, optimizer, or
training routine.  It is deliberately restricted to archive integrity and
environment-interface semantics before a separately authorized endpoint test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


FREEZE = ROOT / "configs" / "drtp_final_evidence_p0_heldout_ood_freeze_20260906.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_freeze() -> dict:
    return json.loads(FREEZE.read_text(encoding="utf-8"))


def required_members(spec: dict, archive_root: str) -> set[str]:
    expected: set[str] = set()
    for arm in spec["checkpoint_contract"]["arms"]:
        for seed in spec["source_archives"][archive_root]["seeds"]:
            run = f"{spec['source_archives'][archive_root]['archive_root']}/runs/{arm}/seed{seed}"
            expected.update({f"{run}/run_manifest.json", f"{run}/actor_critic_latest.pt"})
    return expected


def check_archive(label: str, path: Path, spec: dict) -> dict:
    asset = spec["source_archives"][label]
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_hash = sha256(path)
    if actual_hash != asset["sha256"]:
        raise RuntimeError(f"{label} archive SHA256 mismatch")
    required = required_members(spec, label)
    with tarfile.open(path, "r:gz") as archive:
        members = {member.name.lstrip("./") for member in archive.getmembers() if member.isfile()}
        missing = sorted(required - members)
        if missing:
            raise RuntimeError(f"{label} archive missing required inputs: {missing}")
        manifests: list[dict] = []
        for member in sorted(name for name in required if name.endswith("run_manifest.json")):
            handle = archive.extractfile(member)
            if handle is None:
                raise RuntimeError(f"cannot read {member}")
            manifests.append(json.loads(handle.read().decode("utf-8")))
    expected_steps = spec["checkpoint_contract"]["environment_steps"]
    expected_updates = spec["checkpoint_contract"]["updates"]
    for manifest in manifests:
        if manifest.get("status") != "completed":
            raise RuntimeError(f"{label} source run is not completed")
        if manifest.get("environment_steps") != expected_steps or manifest.get("updates") != expected_updates:
            raise RuntimeError(f"{label} source run is not at the frozen 10M endpoint")
        if manifest.get("checkpoint_promotion") is not False or manifest.get("seed_replacement") is not False:
            raise RuntimeError(f"{label} source run violates endpoint-selection contract")
    return {"file": path.name, "sha256": actual_hash, "validated_runs": len(manifests)}


def make_env(seed: int, condition: dict) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=int(condition["failed_blue_agent"]),
        node_failure_start_step=int(condition["start_step"]),
        node_failure_duration_steps=int(condition["duration_steps"]),
        comm_topology_mode=str(condition["comm_topology_mode"]),
    ))


def check_environment(spec: dict) -> dict:
    conditions = spec["fresh_heldout_ood_tape"]["conditions"]
    expected_names = {
        "nominal_reference", "parameter_early_relay", "parameter_long_relay",
        "structural_scout_node", "structural_symmetric_longest_edge",
        "structural_directed_longest_edge", "structural_scout_node_plus_edge",
    }
    if {item["name"] for item in conditions} != expected_names:
        raise RuntimeError("held-out/OOD condition registry changed")
    signatures = []
    edge_modes: dict[str, int] = {}
    for condition in conditions:
        env = make_env(782000, condition)
        obs, share_obs, graph = env.reset()
        signatures.append((obs.shape, share_obs.shape, graph["node_feat"].shape, graph["edge_feat"].shape, graph["adj"].shape))
        edge_modes[condition["name"]] = len(env._ood_prune_links)
    if len(set(signatures)) != 1:
        raise RuntimeError("OOD condition changed actor/critic/graph interface shape")
    if edge_modes["structural_symmetric_longest_edge"] != 2 or edge_modes["structural_directed_longest_edge"] != 1:
        raise RuntimeError("static edge deletion semantics are inactive")
    if edge_modes["structural_scout_node_plus_edge"] != 2:
        raise RuntimeError("combined node-edge structural condition is inactive")
    return {
        "conditions": [item["name"] for item in conditions],
        "shared_interface_signature": [list(part) for part in signatures[0]],
        "pruned_directed_links_at_reset": edge_modes,
        "condition_descriptor_direct_actor_input": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-a", type=Path, required=True)
    parser.add_argument("--archive-b", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    spec = load_freeze()
    archive_a = check_archive("A", args.archive_a, spec)
    archive_b = check_archive("B", args.archive_b, spec)
    environment = check_environment(spec)
    args.output_root.mkdir(parents=True)
    result = {
        "protocol": spec["protocol"], "verdict": "DRTP_FINAL_EVIDENCE_P0_PREFLIGHT_PASS",
        "archive_validation": {"A": archive_a, "B": archive_b}, "environment": environment,
        "training_started": False, "evaluation_started": False, "checkpoint_selection": False,
        "automatic_algorithm_revision": False, "automatic_external_comparator": False, "automatic_6uav": False,
    }
    (args.output_root / "DRTP_FINAL_EVIDENCE_P0_PREFLIGHT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "DRTP_FINAL_EVIDENCE_P0_PREFLIGHT.md").write_text(
        "# DRTP final evidence P0 preflight\n\n"
        "**Verdict:** `DRTP_FINAL_EVIDENCE_P0_PREFLIGHT_PASS`.\n\n"
        "Both downloaded A/B result archives match their frozen hashes and contain all ten UTR/DRTP final checkpoints and completed manifests. "
        "The fresh held-out/OOD conditions preserve the existing actor/critic/graph interface and activate the declared static edge-deletion semantics. "
        "No checkpoint was opened, no policy was evaluated, and no training was started.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
