"""Read-only action-health audit for frozen R2 checkpoints."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def audit(path: Path) -> dict:
    ckpt = torch.load(path, map_location="cpu")
    method, seed = str(ckpt["method"]), int(ckpt["seed"])
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed + 100, max_steps=60, v16r_mission_mode=True))
    if method == "B2_unified_graph":
        actor = RecipientGraphGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    else:
        actor = ContinuousGuidanceActor(env.obs_dim * 4 if method == "B1_history4" else env.obs_dim, hidden_dim=64, role_specific=True)
    actor.load_state_dict(ckpt["actor"]); actor.eval()
    actions, post_evidence, max_abs = [], [], []
    for _ in range(8):
        obs, _, graph = env.reset(); history = np.repeat(obs[:, None, :], 4, axis=1); seen = False
        for _step in range(60):
            model_obs = history.reshape(env.num_agents, -1) if method == "B1_history4" else obs
            with torch.no_grad():
                ot = torch.as_tensor(model_obs, dtype=torch.float32)
                if method == "B2_unified_graph":
                    act, dist = actor(ot, torch.as_tensor(graph["node"]), torch.as_tensor(graph["relation_adj"]), deterministic=True)
                else:
                    dist = actor.distribution(ot); act = dist.deterministic()
            act_np = act.numpy(); actions.append(act_np)
            if seen: post_evidence.append(act_np)
            max_abs.append(float(np.abs(act_np).max()))
            obs, _, graph, _, done, _ = env.step(act_np)
            history = np.concatenate([history[:, 1:, :], obs[:, None, :]], axis=1)
            seen = seen or bool(np.any(env.base.detected_by > 0.5) or np.any(env.base.target_cache_valid > 0.5))
            if bool(done.all()): break
    a = np.concatenate(actions, axis=0); p = np.concatenate(post_evidence, axis=0) if post_evidence else np.zeros((0, 2))
    return {"method": method, "seed": seed, "action_mean": a.mean(axis=0).tolist(), "action_std": a.std(axis=0).tolist(), "post_evidence_action_std": p.std(axis=0).tolist(), "post_evidence_action_abs_mean": np.abs(p).mean(axis=0).tolist() if len(p) else [0.0, 0.0], "max_abs_action_mean": float(np.mean(max_abs)), "max_abs_action_fraction_gt_0.95": float(np.mean(np.asarray(max_abs) > 0.95)), "log_std": actor.log_std.detach().exp().tolist()}


def main() -> int:
    rows = [audit(p) for p in sorted(Path("results/v1_6r_r2_checkpoints").glob("*.pt"))]
    Path("results/v1_6r_r2_action_health.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
