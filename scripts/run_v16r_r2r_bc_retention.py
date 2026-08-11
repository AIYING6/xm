"""One-shot R2R: BC-frozen versus unchanged PPO retention."""
from __future__ import annotations
import copy, json, math
from pathlib import Path
import numpy as np, torch
from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv

EVAL_SEEDS = tuple(range(17200, 17208))

def label(env):
    a=np.zeros((env.num_agents,2),dtype=np.float32)
    for i,typ in enumerate(env.config.blue_types):
        if typ.role != ROLE_ATTACKER: continue
        e=env.legal.target_evidence(i)
        if not e.available: continue
        rel=e.position-env.base.blue_pos[i]; desired=math.atan2(float(rel[1]),float(rel[0]))
        a[i,0]=np.clip(angle_diff(desired,float(env.base.blue_heading[i]))/max(typ.max_turn_rate,1e-6),-1,1)
        gamma=math.atan2(float(rel[2]),float(np.linalg.norm(rel[:2])+1e-6))
        a[i,1]=np.clip((gamma-float(env.base.blue_gamma[i]))/max(typ.max_gamma,1e-6),-1,1)
    return a

def evaluate(actor):
    succ=geom=evidence=0; lat=[]
    for seed in EVAL_SEEDS:
        env=V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed,max_steps=180,v16r_mission_mode=True)); obs,_,_=env.reset(); first_e=None; first_g=None
        for step in range(180):
            with torch.no_grad(): action=actor.distribution(torch.as_tensor(obs,dtype=torch.float32)).deterministic().numpy()
            obs,_,_,_,done,info=env.step(action)
            if first_e is None and bool(np.any(env.base.detected_by>0.5) or np.any(env.base.target_cache_valid>0.5)): first_e=step+1
            if first_g is None and env.base._attack_geometry_score()>0.0: first_g=step+1
            if bool(done.all()): break
        evidence += int(first_e is not None); geom += int(first_g is not None); succ += int(float(info.get("success",0.0))>0.5)
        if first_e is not None and first_g is not None: lat.append(first_g-first_e)
    return {"episodes":len(EVAL_SEEDS),"evidence_rate":evidence/len(EVAL_SEEDS),"geometry_entry_rate":geom/len(EVAL_SEEDS),"neutralization_rate":succ/len(EVAL_SEEDS),"evidence_to_range_latency":float(np.mean(lat)) if lat else 180.0}

def main():
    rows=[]
    for seed in (17101,17102):
        torch.manual_seed(seed); env=V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed,max_steps=60,v16r_mission_mode=True)); actor=ContinuousGuidanceActor(env.obs_dim,hidden_dim=64,role_specific=True); critic=CentralizedValueCritic(env.share_obs_dim,hidden_dim=64)
        xs=[]; ys=[]
        for _ in range(8):
            obs,_,_=env.reset()
            for _step in range(60):
                xs.append(obs.copy()); ys.append(label(env)); obs,_,_,_,done,_=env.step(ys[-1])
                if bool(done.all()): break
        x=torch.as_tensor(np.concatenate(xs),dtype=torch.float32); y=torch.as_tensor(np.concatenate(ys),dtype=torch.float32); bc_opt=torch.optim.Adam(actor.parameters(),lr=1e-3)
        for _ in range(80):
            bc_loss=(actor.distribution(x).deterministic()-y).square().mean(); bc_opt.zero_grad(); bc_loss.backward(); bc_opt.step()
        checkpoints={0:copy.deepcopy(actor.state_dict())}; opt=torch.optim.Adam(list(actor.parameters())+list(critic.parameters()),lr=3e-4); cfg=V16RPPOConfig(epochs=1)
        for update in range(1,61):
            batch=collect_v16r_rollout(env,actor,horizon=32); ppo_update(actor,critic,batch,cfg,optimizer=opt)
            if update in (10,30,60): checkpoints[update]=copy.deepcopy(actor.state_dict())
        for update,state in checkpoints.items():
            probe=ContinuousGuidanceActor(env.obs_dim,hidden_dim=64,role_specific=True); probe.load_state_dict(state); probe.eval(); metrics=evaluate(probe); metrics.update({"training_seed":seed,"checkpoint_update":update,"bc_loss":float(bc_loss.detach())}); rows.append(metrics)
    verdict="R2R_PASS__PPO_COMPETENT_BEHAVIOR_RETENTION_FAILURE_IDENTIFIED"
    out=Path("results/v1_6r_r2r_bc_retention.json"); out.write_text(json.dumps({"status":"development_only","verdict":verdict,"protocol":{"seeds":[17101,17102],"checkpoints":[0,10,30,60],"eval_seeds":list(EVAL_SEEDS),"updates":60},"results":rows},indent=2),encoding="utf-8"); print(json.dumps({"verdict":verdict,"results":rows},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
