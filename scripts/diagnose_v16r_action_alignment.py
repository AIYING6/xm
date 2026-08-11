"""Compare learned guidance to legal scripted pursuit after evidence arrives."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def one(path: Path) -> dict[str, float | str | int]:
    data = torch.load(path, map_location="cpu")
    method, seed = str(data["method"]), int(data["seed"])
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed + 200, max_steps=60, v16r_mission_mode=True))
    actor = RecipientGraphGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True) if method == "B2_unified_graph" else ContinuousGuidanceActor(env.obs_dim * 4 if method == "B1_history4" else env.obs_dim, hidden_dim=64, role_specific=True)
    actor.load_state_dict(data["actor"])
    actor.eval()
    errors, range_deltas, evidence_steps = [], [], []
    for _ in range(8):
        obs, _share, graph = env.reset()
        history = np.repeat(obs[:, None, :], 4, axis=1)
        prev_range = env.base._mean_target_range()
        seen = False
        for step in range(env.config.max_steps):
            model_obs = history.reshape(env.num_agents, -1) if method == "B1_history4" else obs
            with torch.no_grad():
                obs_t = torch.as_tensor(model_obs, dtype=torch.float32)
                if method == "B2_unified_graph":
                    action, _ = actor(obs_t, torch.as_tensor(graph["node"]), torch.as_tensor(graph["relation_adj"]), deterministic=True)
                else:
                    action, _ = actor(obs_t, deterministic=True)
            learned = action.numpy()
            legal = np.zeros_like(learned)
            for i, typ in enumerate(env.config.blue_types):
                if typ.role != ROLE_ATTACKER:
                    continue
                evidence = env.legal.target_evidence(i)
                if not evidence.available:
                    continue
                seen = True
                rel = evidence.position - env.base.blue_pos[i]
                desired = math.atan2(float(rel[1]), float(rel[0]))
                legal[i, 0] = np.clip(angle_diff(desired, float(env.base.blue_heading[i])) / max(typ.max_turn_rate, 1e-6), -1.0, 1.0)
                desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
                legal[i, 1] = np.clip((desired_gamma - float(env.base.blue_gamma[i])) / max(typ.max_gamma, 1e-6), -1.0, 1.0)
                errors.append(float(np.linalg.norm(learned[i] - legal[i])))
            obs, _share, graph, _reward, dones, _info = env.step(learned)
            history = np.concatenate([history[:, 1:, :], obs[:, None, :]], axis=1)
            cur_range = env.base._mean_target_range()
            if seen:
                range_deltas.append(prev_range - cur_range)
            prev_range = cur_range
            if bool(dones.all()):
                break
        if seen:
            evidence_steps.append(step + 1)
    return {"method": method, "seed": seed, "mean_action_error_after_evidence": float(np.mean(errors)) if errors else float("nan"), "mean_range_delta_after_evidence": float(np.mean(range_deltas)) if range_deltas else float("nan"), "evidence_episodes": len(evidence_steps)}


def main() -> int:
    rows = [one(path) for path in sorted(Path("results/v1_6r_r2_checkpoints").glob("*.pt"))]
    Path("results/v1_6r_r2_action_alignment.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
