"""Read-only diagnostics for the short R2 baseline runs."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def one(method: str, seed: int) -> dict[str, float]:
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=60, v16r_mission_mode=True))
    actor = RecipientGraphGuidanceActor(env.obs_dim, hidden_dim=64) if method == "B2_unified_graph" else ContinuousGuidanceActor(env.obs_dim, hidden_dim=64)
    obs, _share, graph = env.reset()
    rewards, geometries, ranges, evidences, turns, climbs = [], [], [], [], [], []
    for _ in range(env.config.max_steps):
        with torch.no_grad():
            obs_t = torch.as_tensor(obs, dtype=torch.float32)
            if method == "B2_unified_graph":
                action, _ = actor(obs_t, torch.as_tensor(graph["node"], dtype=torch.float32), torch.as_tensor(graph["relation_adj"], dtype=torch.float32), deterministic=True)
            else:
                action, _ = actor(obs_t, deterministic=True)
        turns.extend(action[:, 0].numpy().tolist())
        climbs.extend(action[:, 1].numpy().tolist())
        obs, _share, graph, reward, dones, _info = env.step(action.numpy())
        rewards.extend(reward.reshape(-1).tolist())
        geometries.append(env.base._attack_geometry_score())
        ranges.append(env.base._mean_target_range())
        evidences.append(float(np.mean(env.base.detected_by)))
        if bool(dones.all()):
            break
    return {
        "method": method, "seed": seed, "mean_reward": float(np.mean(rewards)),
        "positive_reward_fraction": float(np.mean(np.asarray(rewards) > 0.0)),
        "geometry_initial": float(geometries[0]), "geometry_max": float(np.max(geometries)),
        "range_initial": float(ranges[0]), "range_final": float(ranges[-1]),
        "evidence_fraction": float(np.mean(np.asarray(evidences) > 0.0)),
        "turn_abs_mean": float(np.mean(np.abs(turns))), "climb_abs_mean": float(np.mean(np.abs(climbs))),
        "turn_saturation_fraction": float(np.mean(np.abs(turns) > 0.95)),
        "climb_saturation_fraction": float(np.mean(np.abs(climbs) > 0.95)),
    }


def main() -> int:
    rows = [one(method, seed) for method in ("B0_flat", "B2_unified_graph") for seed in (17101, 17102)]
    path = Path("results/v1_6r_r2_learning_signal_diagnostic.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
