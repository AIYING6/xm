"""Role-specific continuous MAPPO control for LER pilot (development only)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, torch
from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv

def evaluate(env, actor, episodes=8):
    success = 0; entries = 0
    for _ in range(episodes):
        obs, _, _ = env.reset()
        for step in range(env.config.max_steps):
            with torch.no_grad():
                action, _ = actor(torch.as_tensor(obs, dtype=torch.float32), deterministic=True)
            obs, _, _, _, dones, info = env.step(action.numpy())
            entries += int(float(info.get("attack_window_rate", 0.0)) > 0.0)
            if bool(dones.all()):
                success += int(float(info.get("success", 0.0)) > 0.5); break
    return {"neutralization_rate": success / episodes, "entry_episode_count": entries}

def run(seed, updates, horizon, target_policy):
    torch.manual_seed(seed)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=180, target_policy=target_policy, strict_target_sensing=True, agent_target_info_bottleneck=True, v16r_mission_mode=True))
    actor = ContinuousGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=64)
    opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4)
    cfg = V16RPPOConfig(epochs=1)
    last = None
    for _ in range(updates):
        batch = collect_v16r_rollout(env, actor, horizon=horizon)
        last = ppo_update(actor, critic, batch, cfg, optimizer=opt)
    return {"seed": seed, "updates": updates, "horizon": horizon, "evaluation": evaluate(env, actor), "last_metrics": last}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--updates',type=int,default=60); ap.add_argument('--horizon',type=int,default=180); ap.add_argument('--seeds',type=int,nargs='+',default=[51001,51002]); ap.add_argument('--target-policy',default='evasive'); ap.add_argument('--output',default='results/ler_b1_control_rmnt180.json'); a=ap.parse_args()
    out={"status":"development_only","method":"B1_role_specific","target_policy":a.target_policy,"results":[run(s,a.updates,a.horizon,a.target_policy) for s in a.seeds]}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
