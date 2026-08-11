"""Two-seed LER-MAPPO development pilot; not formal paper evidence."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import torch
from algorithms.mappo.legal_evidence_role_actor import LegalEvidenceRoleActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def evaluate(env, actor, episodes=8):
    successes = 0; entries = 0; geometry = []; terms = []
    for _ in range(episodes):
        obs, _, _ = env.reset()
        for step in range(env.config.max_steps):
            role = torch.as_tensor([int(env.base.config.blue_types[i].role) for i in range(env.num_agents)], dtype=torch.long)
            mask = torch.as_tensor([float(env.legal.target_evidence(i).available) for i in range(env.num_agents)], dtype=torch.float32)
            with torch.no_grad():
                action, _ = actor(torch.as_tensor(obs, dtype=torch.float32), role, mask, deterministic=True)
            obs, _, _, _, dones, info = env.step(action.numpy())
            if float(info.get("attack_window_rate", 0.0)) > 0.0: entries += 1
            geometry.append(float(info.get("attack_geometry_score", 0.0)))
            if bool(dones.all()):
                successes += int(float(info.get("success", 0.0)) > 0.5); terms.append(step + 1); break
    return {"neutralization_rate": successes / episodes, "entry_rate": entries / episodes,
            "mean_attack_geometry_score": float(np.mean(geometry)) if geometry else 0.0,
            "mean_terminal_step": float(np.mean(terms)) if terms else float(env.config.max_steps)}


def run(seed, updates, horizon):
    torch.manual_seed(seed)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=180, strict_target_sensing=True, agent_target_info_bottleneck=True, v16r_mission_mode=True))
    actor = LegalEvidenceRoleActor(env.obs_dim, hidden_dim=64)
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=64)
    opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4)
    cfg = V16RPPOConfig(epochs=1)
    history = []
    for _ in range(updates):
        batch = collect_v16r_rollout(env, actor, horizon=horizon, legal_evidence_actor=True)
        history.append(ppo_update(actor, critic, batch, cfg, optimizer=opt, legal_evidence_actor=True))
    return {"seed": seed, "updates": updates, "horizon": horizon, "evaluation": evaluate(env, actor), "last_metrics": history[-1]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--updates", type=int, default=12); ap.add_argument("--horizon", type=int, default=32); ap.add_argument("--output", default="results/ler_mappo_pilot.json"); args = ap.parse_args()
    out = {"status": "development_only", "method": "LER-MAPPO", "results": [run(s, args.updates, args.horizon) for s in (51001, 51002)]}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True); Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8"); print(json.dumps(out, indent=2))


if __name__ == "__main__": main()
