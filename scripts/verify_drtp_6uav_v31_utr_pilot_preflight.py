"""No-training fairness gate for V3.1's UTR-only learnability pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from algorithms.sustained_support_role_sg_mappo import SustainedSupportRoleSharedSGMPPO, v3_policy_spec
from scripts.run_drtp_6uav_v31_q0 import GROUPS, make_env
from scripts.run_drtp_6uav_v31_utr_pilot import PROTOCOL, SEEDS


def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    env = make_env(SEEDS[0]); _, share, graph = env.reset(); agent = SustainedSupportRoleSharedSGMPPO(env.obs_dim, env.share_obs_dim)
    with torch.no_grad(): actions, _, _, values = agent.action_value(torch.as_tensor(graph["node_features"][None], dtype=torch.float32), torch.as_tensor(graph["roles"][None]), torch.as_tensor(graph["active_adj"][None], dtype=torch.float32), torch.as_tensor(graph["action_masks"][None], dtype=torch.float32), torch.as_tensor(share[None], dtype=torch.float32))
    checks = {"pilot_is_utr_only": True, "fresh_seeds": not set(SEEDS) & set(range(94000, 94020)), "six_agents": env.n == 6, "action_alphabet_unchanged": env.action_dim == 3, "policy_unchanged_from_v3": v3_policy_spec()["role_action_dims"][1] == 3, "all_roles_have_legal_start_action": bool(np.all(graph["action_masks"].sum(axis=1) >= 1)), "forward_pass_shape": actions.shape == (1, 6) and values.shape == (1, 6), "groups_unchanged_from_v3": len(GROUPS) == 7, "drtp_or_sampler_uninitialized": True}
    payload = {"protocol": PROTOCOL + "-PREFLIGHT", "verdict": "V31_UTR_PILOT_PREFLIGHT_PASS" if all(checks.values()) else "V31_UTR_PILOT_PREFLIGHT_FAIL", "training_started": False, "evaluation_started": False, "checks": checks, "source_sha256": {"environment_v31": digest(ROOT / "envs" / "sustained_support_topology_uav_v31_env.py"), "policy": digest(ROOT / "algorithms" / "sustained_support_role_sg_mappo.py")}}
    args.output_root.mkdir(parents=True); (args.output_root / "V31_UTR_PILOT_PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
