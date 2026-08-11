"""Counterfactual one-step action-value audit from frozen checkpoints."""
from __future__ import annotations
import copy, json, math
from pathlib import Path
import numpy as np, torch
from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv

def one(path: Path) -> dict:
    d = torch.load(path, map_location="cpu"); method, seed = str(d["method"]), int(d["seed"])
    base_env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed + 300, max_steps=60, v16r_mission_mode=True))
    actor = RecipientGraphGuidanceActor(base_env.obs_dim, hidden_dim=64, role_specific=True) if method == "B2_unified_graph" else ContinuousGuidanceActor(base_env.obs_dim * 4 if method == "B1_history4" else base_env.obs_dim, hidden_dim=64, role_specific=True)
    actor.load_state_dict(d["actor"]); actor.eval(); learned_rewards=[]; scripted_rewards=[]; learned_geom=[]; scripted_geom=[]
    for _ in range(8):
        obs, _, graph = base_env.reset(); history=np.repeat(obs[:,None,:],4,axis=1)
        for _step in range(60):
            model_obs=history.reshape(base_env.num_agents,-1) if method=="B1_history4" else obs
            with torch.no_grad():
                ot=torch.as_tensor(model_obs,dtype=torch.float32)
                if method=="B2_unified_graph": la,_=actor(ot,torch.as_tensor(graph["node"]),torch.as_tensor(graph["relation_adj"]),deterministic=True)
                else: la,_=actor(ot,deterministic=True)
            learned=la.numpy(); scripted=np.zeros_like(learned); valid=False
            for i,typ in enumerate(base_env.config.blue_types):
                if typ.role != ROLE_ATTACKER: continue
                e=base_env.legal.target_evidence(i)
                if not e.available: continue
                valid=True; rel=e.position-base_env.base.blue_pos[i]; desired=math.atan2(float(rel[1]),float(rel[0]))
                scripted[i,0]=np.clip(angle_diff(desired,float(base_env.base.blue_heading[i]))/max(typ.max_turn_rate,1e-6),-1,1)
                desired_gamma=math.atan2(float(rel[2]),float(np.linalg.norm(rel[:2])+1e-6))
                scripted[i,1]=np.clip((desired_gamma-float(base_env.base.blue_gamma[i]))/max(typ.max_gamma,1e-6),-1,1)
            if valid:
                e1=copy.deepcopy(base_env); e2=copy.deepcopy(base_env)
                before1=e1.base._mean_target_range(); before2=e2.base._mean_target_range()
                _,_,_,r1,_,_=e1.step(learned); _,_,_,r2,_,_=e2.step(scripted)
                learned_rewards.append(float(np.mean(r1))); scripted_rewards.append(float(np.mean(r2)))
                learned_geom.append(float(e1.base._attack_geometry_score())); scripted_geom.append(float(e2.base._attack_geometry_score()))
            obs,_,graph,_,done,_=base_env.step(learned); history=np.concatenate([history[:,1:,:],obs[:,None,:]],axis=1)
            if bool(done.all()): break
    return {"method":method,"seed":seed,"samples":len(learned_rewards),"learned_reward_mean":float(np.mean(learned_rewards)),"scripted_reward_mean":float(np.mean(scripted_rewards)),"reward_gap_learned_minus_scripted":float(np.mean(learned_rewards)-np.mean(scripted_rewards)),"learned_geometry_mean":float(np.mean(learned_geom)),"scripted_geometry_mean":float(np.mean(scripted_geom))}

def main()->int:
    rows=[one(p) for p in sorted(Path("results/v1_6r_r2_checkpoints").glob("*.pt"))]; Path("results/v1_6r_r2_one_step_action_value.json").write_text(json.dumps(rows,indent=2),encoding="utf-8"); print(json.dumps(rows,indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
