"""One-shot R3 pilot: vanilla PPO versus evidence-masked behavior retention."""
from __future__ import annotations
import copy, json, math
from pathlib import Path
import numpy as np, torch
from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv

EVAL_SEEDS=tuple(range(17400,17408)); CHECKPOINTS=(0,10,30,60)

def label(env):
    a=np.zeros((env.num_agents,2),np.float32)
    for i,typ in enumerate(env.config.blue_types):
        if typ.role!=ROLE_ATTACKER: continue
        e=env.legal.target_evidence(i)
        if not e.available: continue
        rel=e.position-env.base.blue_pos[i]; a[i,0]=np.clip(angle_diff(math.atan2(float(rel[1]),float(rel[0])),float(env.base.blue_heading[i]))/max(typ.max_turn_rate,1e-6),-1,1)
        a[i,1]=np.clip((math.atan2(float(rel[2]),float(np.linalg.norm(rel[:2])+1e-6))-float(env.base.blue_gamma[i]))/max(typ.max_gamma,1e-6),-1,1)
    return a

def evaluate(actor):
    ev=ge=su=0; lat=[]
    for seed in EVAL_SEEDS:
        env=V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed,max_steps=180,v16r_mission_mode=True)); obs,_,_=env.reset(); e0=g0=None
        for step in range(180):
            with torch.no_grad(): act=actor.distribution(torch.as_tensor(obs,dtype=torch.float32)).deterministic().numpy()
            obs,_,_,_,done,info=env.step(act)
            if e0 is None and bool(np.any(env.base.detected_by>0.5) or np.any(env.base.target_cache_valid>0.5)): e0=step+1
            if g0 is None and env.base._attack_geometry_score()>0: g0=step+1
            if bool(done.all()): break
        ev+=int(e0 is not None); ge+=int(g0 is not None); su+=int(float(info.get("success",0))>0.5)
        if e0 is not None and g0 is not None: lat.append(g0-e0)
    return {"evidence_rate":ev/len(EVAL_SEEDS),"geometry_entry_rate":ge/len(EVAL_SEEDS),"neutralization_rate":su/len(EVAL_SEEDS),"evidence_to_range_latency":float(np.mean(lat)) if lat else 180.0,"episodes":len(EVAL_SEEDS)}

def main():
    rows=[]; cfgppo=V16RPPOConfig(epochs=1)
    for seed in (17301,17302):
        torch.manual_seed(seed); env=V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed,max_steps=60,v16r_mission_mode=True)); bc=ContinuousGuidanceActor(env.obs_dim,hidden_dim=64,role_specific=True); critic0=CentralizedValueCritic(env.share_obs_dim,64); critic1=CentralizedValueCritic(env.share_obs_dim,64)
        xs=[]; ys=[]
        for _ in range(8):
            obs,_,_=env.reset()
            for _step in range(60):
                xs.append(obs.copy()); ys.append(label(env)); obs,_,_,_,done,_=env.step(ys[-1])
                if bool(done.all()): break
        x=torch.as_tensor(np.concatenate(xs),dtype=torch.float32); y=torch.as_tensor(np.concatenate(ys),dtype=torch.float32); bco=torch.optim.Adam(bc.parameters(),lr=1e-3)
        for _ in range(80):
            bcl=(bc.distribution(x).deterministic()-y).square().mean(); bco.zero_grad(); bcl.backward(); bco.step()
        ref=copy.deepcopy(bc); vanilla=copy.deepcopy(bc); retain=copy.deepcopy(bc); opt0=torch.optim.Adam(list(vanilla.parameters())+list(critic0.parameters()),lr=3e-4); opt1=torch.optim.Adam(list(retain.parameters())+list(critic1.parameters()),lr=3e-4)
        for method,actor,critic,opt in (("vanilla_ppo",vanilla,critic0,opt0),("retention_ppo",retain,critic1,opt1)):
            rows.append(dict(evaluate(actor),training_seed=seed,method=method,checkpoint_update=0,bc_loss=float(bcl.detach())))
            for update in range(1,61):
                batch=collect_v16r_rollout(env,actor,32)
                if method=="retention_ppo": ppo_update(actor,critic,batch,cfgppo,optimizer=opt,reference_actor=ref,retention_coef=1.0)
                else: ppo_update(actor,critic,batch,cfgppo,optimizer=opt)
                if update in (10,30,60): rows.append(dict(evaluate(actor),training_seed=seed,method=method,checkpoint_update=update,bc_loss=float(bcl.detach())))
    out=Path("results/v1_6r_r3_behavior_retention_pilot.json"); out.write_text(json.dumps({"status":"development_only","protocol":{"seeds":[17301,17302],"eval_seeds":list(EVAL_SEEDS),"checkpoints":list(CHECKPOINTS),"retention_coef":1.0},"results":rows},indent=2),encoding="utf-8"); print(json.dumps(rows,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
