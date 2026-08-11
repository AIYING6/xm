"""Final one-shot EG-BR-MAPPO pilot using the frozen R3 protocol."""
from __future__ import annotations
import copy, json
from pathlib import Path
import numpy as np, torch
from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv
from scripts.run_v16r_r3_behavior_retention_pilot import label, evaluate

def main():
    rows=[]; cfgppo=V16RPPOConfig(epochs=1)
    for seed in (17501,17502):
        torch.manual_seed(seed); env=V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed,max_steps=60,v16r_mission_mode=True)); bc=ContinuousGuidanceActor(env.obs_dim,64,role_specific=True); c0=CentralizedValueCritic(env.share_obs_dim,64); c1=CentralizedValueCritic(env.share_obs_dim,64)
        xs=[]; ys=[]
        for _ in range(8):
            obs,_,_=env.reset()
            for _step in range(60):
                xs.append(obs.copy()); ys.append(label(env)); obs,_,_,_,done,_=env.step(ys[-1])
                if bool(done.all()): break
        x=torch.as_tensor(np.concatenate(xs),dtype=torch.float32); y=torch.as_tensor(np.concatenate(ys),dtype=torch.float32); bo=torch.optim.Adam(bc.parameters(),lr=1e-3)
        for _ in range(80):
            bcl=(bc.distribution(x).deterministic()-y).square().mean(); bo.zero_grad(); bcl.backward(); bo.step()
        ref=copy.deepcopy(bc); vanilla=copy.deepcopy(bc); egbr=copy.deepcopy(bc); o0=torch.optim.Adam(list(vanilla.parameters())+list(c0.parameters()),lr=3e-4); o1=torch.optim.Adam(list(egbr.parameters())+list(c1.parameters()),lr=3e-4)
        for method,actor,critic,opt in (("vanilla_ppo",vanilla,c0,o0),("egbr_ppo",egbr,c1,o1)):
            for update in range(61):
                if update in (0,10,30,60): rows.append(dict(evaluate(actor),training_seed=seed,method=method,checkpoint_update=update,bc_loss=float(bcl.detach())))
                if update==60: break
                batch=collect_v16r_rollout(env,actor,32)
                if method=="egbr_ppo": ppo_update(actor,critic,batch,cfgppo,optimizer=opt,reference_actor=ref,retention_coef=1.0,adaptive_retention=True,retention_beta=1.0)
                else: ppo_update(actor,critic,batch,cfgppo,optimizer=opt)
    out=Path("results/v1_6r_egbr_pilot.json"); out.write_text(json.dumps({"status":"development_only","protocol":{"seeds":[17501,17502],"retention_coef":1.0,"retention_beta":1.0,"adaptive_retention":True},"results":rows},indent=2),encoding="utf-8"); print(json.dumps(rows,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
