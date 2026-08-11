"""Stage localization for saved R2 development checkpoints."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def one(path: Path) -> dict[str, float | str | int]:
    data = torch.load(path, map_location="cpu")
    method = str(data["method"])
    seed = int(data["seed"])
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed + 100, max_steps=60, v16r_mission_mode=True))
    if method == "B2_unified_graph":
        actor = RecipientGraphGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    else:
        actor = ContinuousGuidanceActor(env.obs_dim * 4 if method == "B1_history4" else env.obs_dim, hidden_dim=64, role_specific=True)
    actor.load_state_dict(data["actor"])
    actor.eval()
    rows = []
    for _ in range(8):
        obs, _share, graph = env.reset()
        history = np.repeat(obs[:, None, :], 4, axis=1)
        evidence_step = None
        geometry_step = None
        max_geometry = 0.0
        for step in range(env.config.max_steps):
            model_obs = history.reshape(env.num_agents, -1) if method == "B1_history4" else obs
            with torch.no_grad():
                obs_t = torch.as_tensor(model_obs, dtype=torch.float32)
                if method == "B2_unified_graph":
                    action, _ = actor(obs_t, torch.as_tensor(graph["node"]), torch.as_tensor(graph["relation_adj"]), deterministic=True)
                else:
                    action, _ = actor(obs_t, deterministic=True)
            obs, _share, graph, _reward, dones, info = env.step(action.numpy())
            history = np.concatenate([history[:, 1:, :], obs[:, None, :]], axis=1)
            if evidence_step is None and np.any(env.base.detected_by > 0.5) or evidence_step is None and np.any(env.base.target_cache_valid > 0.5):
                evidence_step = step + 1
            geometry = env.base._attack_geometry_score()
            max_geometry = max(max_geometry, geometry)
            if geometry_step is None and geometry > 0.0:
                geometry_step = step + 1
            if bool(dones.all()):
                break
        rows.append({"evidence_step": evidence_step if evidence_step is not None else 60, "geometry_step": geometry_step if geometry_step is not None else 60, "max_geometry": max_geometry, "success": float(info.get("success", 0.0)), "terminal_step": step + 1})
    return {"method": method, "seed": seed, "evidence_rate": float(np.mean([r["evidence_step"] < 60 for r in rows])), "geometry_entry_rate": float(np.mean([r["geometry_step"] < 60 for r in rows])), "success_rate": float(np.mean([r["success"] for r in rows])), "mean_max_geometry": float(np.mean([r["max_geometry"] for r in rows])), "mean_evidence_step": float(np.mean([r["evidence_step"] for r in rows])), "mean_geometry_step": float(np.mean([r["geometry_step"] for r in rows]))}


def main() -> int:
    rows = [one(path) for path in sorted(Path("results/v1_6r_r2_checkpoints").glob("*.pt"))]
    Path("results/v1_6r_r2_failure_stages.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
