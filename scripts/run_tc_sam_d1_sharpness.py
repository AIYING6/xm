"""Frozen offline actor sharpness probe for completed TC-SAM versus T1 UTR."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np, torch
from scripts.run_m0_offline_feasibility import SEEDS,SAMPLES_PER_SEED,collect_f0_states,logits,mean_kl,relay_deletion,actor_tensors,parameter_perturbation,restore_parameters
from scripts.telemetry_native_t1 import build_matched_sg_agent
def main():
 p=argparse.ArgumentParser();p.add_argument('--tc-root',type=Path,required=True);p.add_argument('--t1-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(); report={'protocol':'TC-SAM-D1-OFFLINE-SHARPNESS-V1','zero_training':True,'zero_rollout':True,'parameter_radius':.01,'per_seed':{}}
 for seed in SEEDS:
  row={}
  for label,root,arm in [('utr',a.t1_root,'utr_sg'),('tc_sam',a.tc_root,'tc_sam_utr')]:
   ck=root/'runs'/arm/f'seed{seed}'/'actor_critic_latest.pt'; raw=root/'evaluations'/'final_1m'/arm/f'seed{seed}'/'raw_step_telemetry.jsonl'; agent=build_matched_sg_agent(ck,construction_seed=seed,device='cpu'); states=collect_f0_states(raw,SAMPLES_PER_SEED); local=[]; pert=[]
   for i,state in enumerate(states):
    base=logits(agent,state); local.append(mean_kl(base,logits(agent,state,relay_deletion(actor_tensors(state,torch.device('cpu'))[4])))); g=torch.Generator(device='cpu').manual_seed(seed*10000+i); noises=parameter_perturbation(agent,.01,g)
    try: pert.append(mean_kl(base,logits(agent,state)))
    finally: restore_parameters(agent,noises)
   row[label]={'local_relay_deletion_kl':float(np.mean(local)),'parameter_perturbation_kl':float(np.mean(pert))}
  report['per_seed'][str(seed)]=row
 report['interpretation']='Offline actor sensitivity only; not a performance gate or proof of causality.';a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
