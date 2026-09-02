"""Zero-training readiness audit for prospective corrected-learner P2-R."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import ROLE_ACTION_DIMS, RoleSharedSGMPPO
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config

PROTOCOL = "P2_R_CORRECTED_LEARNER_REQUALIFICATION_PREFLIGHT_V1"
P2_HISTORICAL_SEEDS = (6201, 6202, 6203)
P2R_SEEDS = (65011, 65012, 65013, 65014, 65015)
RESERVED_REPLICATION = (65021, 65022, 65023, 65024, 65025)
RESERVED_CONFIRMATORY = (65031, 65032, 65033, 65034, 65035)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2r_preflight")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "formal_training_started": False}))
        return

    out = Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2-R preflight output exists; refusing overwrite")

    role_source = ROOT / "algorithms/redundant_topology_role_sg_mappo.py"
    env_source = ROOT / "envs/redundant_topology_uav_env.py"
    contract = ROOT / "docs/redundant_topology_uav_p2r_20260903/P2_R_REQUALIFICATION_CONTRACT.md"
    role_text = role_source.read_text(encoding="utf-8")
    env = RedundantTopologyUAVEnv(scale_config("main"))
    _, _, graph = env.reset(seed_env=65011)

    all_seed_sets = (set(P2_HISTORICAL_SEEDS), set(P2R_SEEDS), set(RESERVED_REPLICATION), set(RESERVED_CONFIRMATORY))
    distinct_seed_ranges = all(not a & b for i, a in enumerate(all_seed_sets) for b in all_seed_sets[i + 1:])
    source_invariants = {
        "three_role_actor_bodies": all(token in role_text for token in ("self.scout_actor", "self.relay_actor", "self.terminal_actor")),
        "relay_one_action": ROLE_ACTION_DIMS[1] == 1 and "if role == RELAY" in role_text,
        "critic_unchanged_shape": "self.critic = nn.Sequential(nn.Linear(share_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))" in role_text,
        "main_scale_has_eight_paths": env.graph_signature()["total_legal_paths"] == 8,
        "no_direct_scout_terminal_bypass": all(not (i in env.scout_ids and j in env.terminal_ids) for i, j in env.legal_edges()),
        "graph_interface_complete": set(("node_features", "active_adj", "roles", "action_masks")).issubset(graph),
        "contract_present": contract.exists(),
    }
    try:
        _ = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim)
        corrected_learner_importable = True
    except Exception:
        corrected_learner_importable = False

    checks = {
        "five_fresh_matched_training_seeds": len(P2R_SEEDS) == 5 and len(set(P2R_SEEDS)) == 5,
        "historical_p2_seeds_excluded": not set(P2R_SEEDS) & set(P2_HISTORICAL_SEEDS),
        "future_seed_ranges_reserved_and_disjoint": distinct_seed_ranges,
        "corrected_learner_importable": corrected_learner_importable,
        **source_invariants,
        "formal_training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    required_checks = {key: value for key, value in checks.items() if key not in {
        "formal_training_started", "evaluation_started", "automatic_continuation"
    }}
    verdict = "P2_R_PREFLIGHT_PASS" if all(required_checks.values()) else "P2_R_PREFLIGHT_FAIL"
    manifest = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "checks": checks,
        "historical_p2_seeds": P2_HISTORICAL_SEEDS,
        "p2r_training_seeds": P2R_SEEDS,
        "reserved_independent_replication": RESERVED_REPLICATION,
        "reserved_confirmatory": RESERVED_CONFIRMATORY,
        "source_sha256": {"role_learner": digest(role_source), "environment": digest(env_source), "contract": digest(contract)},
        "formal_training_started": False,
        "evaluation_started": False,
        "p3_authorized": False,
        "automatic_continuation": False,
    }
    diag = out / "diagnostics"
    write(diag / "P2_R_SEED_REGISTRY.md", "# P2-R seed registry\n\n"
          "Historical P2: 6201–6203 (excluded)\\n\\n"
          "P2-R prospective matched training: 65011–65015\\n\\n"
          "Reserved independent replication: 65021–65025\\n\\n"
          "Reserved confirmatory: 65031–65035\\n")
    write(diag / "P2_R_PREFLIGHT_REPORT.md", f"# P2-R preflight\n\n**Verdict:** `{verdict}`.\n\n"
          "This audit performs no PPO rollout, update, evaluation or checkpoint selection.\n\n```json\n"
          + json.dumps(manifest, indent=2) + "\n```\n")
    write(diag / "P2_R_PREFLIGHT.json", json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
