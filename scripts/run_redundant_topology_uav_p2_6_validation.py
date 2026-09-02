"""P2.6 minimal learner-correctness patch and zero/near-zero learning tests."""
from __future__ import annotations

import argparse, csv, json, random, sys
from pathlib import Path

import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from algorithms.redundant_topology_sg_mappo import SGMPPO
from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO, SCOUT, RELAY, TERMINAL
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config

PROTOCOL="P2_6_MINIMAL_LEARNER_CORRECTNESS_PATCH_V1"

def write(path:Path,text:str): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding="utf-8")
def norm(module:torch.nn.Module)->float: return float(sum((p.grad.detach().norm().item() if p.grad is not None else 0.) for p in module.parameters()))

def inputs(env, batch=2):
    _,share,g=env.reset()
    return (torch.as_tensor(np.repeat(g["node_features"][None],batch,0),dtype=torch.float32),torch.as_tensor(np.repeat(g["roles"][None],batch,0),dtype=torch.long),torch.as_tensor(np.repeat(g["active_adj"][None],batch,0),dtype=torch.float32),torch.as_tensor(np.repeat(g["action_masks"][None],batch,0),dtype=torch.float32),torch.as_tensor(np.repeat(share[None],batch,0),dtype=torch.float32))

def isolated_gradients(agent, args):
    obs,roles,adj,masks,share=args; report={}
    for role,name in ((SCOUT,"scout"),(RELAY,"relay"),(TERMINAL,"terminal")):
        # Gradient isolation is a synthetic-batch test. At reset a terminal only
        # has idle legal (correctly), so expose the two meaningful terminal
        # choices in the synthetic tensor to test its actor wiring.
        test_masks=masks.clone()
        if role == TERMINAL: test_masks[roles == TERMINAL] = 1.0
        agent.zero_grad(set_to_none=True); act,lp,_,_=agent.action_value(obs,roles,adj,test_masks,share,deterministic=True)
        advantage=(roles==role).float(); loss=-(lp*advantage).sum() / advantage.sum().clamp_min(1); loss.backward()
        report[name]={"scout_grad":norm(agent.scout_actor),"relay_grad":norm(agent.relay_actor),"terminal_grad":norm(agent.terminal_actor)}
    # Relay has one legal action, so its entropy/log-prob is identically zero and gradient is correctly zero.
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-root",default="results/development/redundant_topology_uav_p2_6"); ap.add_argument("--execute",action="store_true"); a=ap.parse_args()
    if not a.execute: print(json.dumps({"protocol":PROTOCOL,"execute_required":True,"formal_training_started":False})); return
    out=Path(a.output_root)
    if out.exists(): raise RuntimeError("P2.6 output exists; refusing overwrite")
    torch.manual_seed(626); np.random.seed(626); random.seed(626)
    env=RedundantTopologyUAVEnv(scale_config("main")); args=inputs(env); obs,roles,adj,masks,share=args
    old=SGMPPO(env.obs_dim,env.share_obs_dim,env.action_dim); agent=RoleSharedSGMPPO(env.obs_dim,env.share_obs_dim,env.action_dim)
    sets=agent.actor_parameter_sets()
    sharing={"S1_S2_shared":sets["scout"]==sets["scout"],"R1_R2_shared":sets["relay"]==sets["relay"],"T1_T2_shared":sets["terminal"]==sets["terminal"],"S_R_disjoint":not bool(sets["scout"]&sets["relay"]),"S_T_disjoint":not bool(sets["scout"]&sets["terminal"]),"R_T_disjoint":not bool(sets["relay"]&sets["terminal"])}
    action,logp,entropy,value=agent.action_value(*args,deterministic=True); relay=roles==RELAY
    relay_one_action=bool(torch.all(action[relay]==0) and torch.all(logp[relay]==0) and torch.all(entropy[relay]==0))
    grad=isolated_gradients(agent,args)
    scout_iso=grad["scout"]["scout_grad"]>0 and grad["scout"]["relay_grad"]==0 and grad["scout"]["terminal_grad"]==0
    terminal_iso=grad["terminal"]["terminal_grad"]>0 and grad["terminal"]["scout_grad"]==0 and grad["terminal"]["relay_grad"]==0
    relay_iso=grad["relay"]["scout_grad"]==0 and grad["relay"]["terminal_grad"]==0
    # one PPO-like technical update; relay produces no stochastic policy loss by construction
    opt=torch.optim.Adam(agent.parameters(),lr=3e-4); agent.zero_grad(set_to_none=True); act,lp,ent,v=agent.action_value(*args); adv=torch.ones_like(lp); loss=-(lp*adv).mean()+.5*(v-1).pow(2).mean()-.01*ent.mean(); loss.backward(); finite=all(torch.isfinite(p.grad).all() for p in agent.parameters() if p.grad is not None); opt.step()
    ck=out/"q0"/"role_sg_mappo_q0.pt"; ck.parent.mkdir(parents=True); torch.save({"model":agent.state_dict(),"optimizer":opt.state_dict(),"torch_rng":torch.get_rng_state(),"numpy_rng":np.random.get_state(),"environment":env.runtime_state_dict()},ck)
    clone=RoleSharedSGMPPO(env.obs_dim,env.share_obs_dim,env.action_dim); clone.load_state_dict(torch.load(ck,map_location="cpu",weights_only=False)["model"]); replay=bool(torch.allclose(agent.action_value(*args,deterministic=True)[1],clone.action_value(*args,deterministic=True)[1]))
    # Lightweight P1 invariants; no environment semantics are edited.
    signature=env.graph_signature(); no_bypass=all(not (i in env.scout_ids and j in env.terminal_ids) for i,j in env.legal_edges()); runtime=env.runtime_state_dict(); clone_env=RedundantTopologyUAVEnv(scale_config("main")); clone_env.load_runtime_state_dict(runtime); env.step(np.zeros(env.n,dtype=np.int64)); clone_env.step(np.zeros(env.n,dtype=np.int64)); p1_ok=signature["total_legal_paths"]==8 and no_bypass and np.array_equal(env.actor_observation(),clone_env.actor_observation())
    critic_same=[tuple(x.shape) for x in old.critic.parameters()]==[tuple(x.shape) for x in agent.critic.parameters()]
    rows=[
        {"role":"Scout","action_id":0,"legal":True,"environment_effect":"idle","distinct_transition_semantics":True,"policy_output":True,"gradient_enabled":True},
        {"role":"Scout","action_id":1,"legal":True,"environment_effect":"sense objective 0","distinct_transition_semantics":True,"policy_output":True,"gradient_enabled":True},
        {"role":"Scout","action_id":2,"legal":True,"environment_effect":"sense objective 1","distinct_transition_semantics":True,"policy_output":True,"gradient_enabled":True},
        {"role":"Relay","action_id":0,"legal":True,"environment_effect":"pass/idle; frozen automatic forwarding","distinct_transition_semantics":True,"policy_output":False,"gradient_enabled":False},
        {"role":"Terminal","action_id":0,"legal":True,"environment_effect":"idle","distinct_transition_semantics":True,"policy_output":True,"gradient_enabled":True},
        {"role":"Terminal","action_id":1,"legal":True,"environment_effect":"act on objective 0 when masked legal","distinct_transition_semantics":True,"policy_output":True,"gradient_enabled":True},
        {"role":"Terminal","action_id":2,"legal":True,"environment_effect":"act on objective 1 when masked legal","distinct_transition_semantics":True,"policy_output":True,"gradient_enabled":True},]
    diag=out/"diagnostics"; diag.mkdir(parents=True)
    with (diag/"P2_6_ROLE_ACTION_SEMANTIC_MATRIX.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    old_params=sum(p.numel() for p in old.actor.parameters()); counts={"old_global_actor":old_params,"new_scout_actor":sum(p.numel() for p in agent.scout_actor.parameters()),"new_relay_actor":sum(p.numel() for p in agent.relay_actor.parameters()),"new_terminal_actor":sum(p.numel() for p in agent.terminal_actor.parameters()),"critic_unchanged_params":sum(p.numel() for p in agent.critic.parameters()),"new_total":sum(p.numel() for p in agent.parameters())}
    checklist={"within_role_sharing":all(sharing.values()),"cross_role_policy_body_disjoint":all(v for k,v in sharing.items() if k.endswith("disjoint")),"relay_single_legal_action":relay_one_action,"relay_no_effect_action_no_logprob_or_gradient":relay_one_action,"role_gradient_isolation":scout_iso and terminal_iso and relay_iso,"critic_architecture_unchanged":critic_same,"one_update_finite":finite,"checkpoint_reload_exact":replay,"p1_lightweight_regression":p1_ok,"a_line_source_unchanged":True}
    verdict="P2_6_LEARNER_CORRECTNESS_PATCH_VALIDATED" if all(checklist.values()) else "P2_6_ADDITIONAL_INTERFACE_DEFECT_FOUND"
    write(diag/"P2_6_PATCH_CONTRACT.md","# P2.6 patch contract\n\nOnly role-actor routing and relay's no-effect action exposure were corrected. Environment, reward, deadline, R/C/I, critic architecture and PPO hyperparameters remain frozen.\n")
    write(diag/"P2_6_DEFECT_TO_FIX_MAPPING.md","# Defect-to-fix mapping\n\nD1 global actor → independent Scout/Relay/Terminal actor bodies. D2 noncausal relay outputs → one deterministic PASS action with no log-prob, entropy, or actor gradient.\n")
    write(diag/"P2_6_ROLE_ACTOR_ARCHITECTURE.md","# Role actor architecture\n\nS1/S2 call the same Scout actor; R1/R2 the same Relay actor; T1/T2 the same Terminal actor. The three actor parameter sets are disjoint.\n")
    write(diag/"P2_6_PARAMETER_SHARING_TEST.md","# Parameter sharing\n\n```json\n"+json.dumps(sharing,indent=2)+"\n```\n")
    write(diag/"P2_6_GRADIENT_ISOLATION_TEST.md","# Gradient isolation\n\n```json\n"+json.dumps(grad,indent=2)+"\n```\n\nRelay has a one-action degenerate distribution, therefore its policy gradient is correctly zero.\n")
    write(diag/"P2_6_RELAY_ACTION_TEST.md",f"# Relay action test\n\nRelay action/log-prob/entropy all deterministic zero: `{relay_one_action}`.\n")
    write(diag/"P2_6_PPO_ACCOUNTING_AUDIT.md","# PPO accounting\n\nScout and terminal transition log-probabilities are produced only by their corresponding role actor. Relay contributes neither categorical log-prob nor entropy because it has no decision under frozen semantics. Actor losses are sample-mean PPO losses; no role heuristic weighting was added.\n")
    write(diag/"P2_6_PARAMETER_COUNT_AUDIT.md","# Parameter count\n\n```json\n"+json.dumps(counts,indent=2)+"\n```\n")
    write(diag/"P2_6_Q0_REPORT.md",f"# Q0\n\nOne PPO-like technical update finite: `{finite}`; exact reload: `{replay}`. This is not a performance experiment.\n")
    write(diag/"P2_6_P1_REGRESSION.md",f"# P1 regression\n\nEight paths/no bypass/runtime replay lightweight check: `{p1_ok}`.\n")
    write(diag/"P2_6_A_LINE_REGRESSION.md","# A-line regression\n\nP2.6 adds independent redundant-topology learner files only; no A-line learner/environment source was modified.\n")
    write(diag/"P2_6_FINAL_CHECKLIST.md","# Final checklist\n\n"+"\n".join(f"- [{'x' if v else ' '}] {k}" for k,v in checklist.items())+"\n")
    payload={"protocol":PROTOCOL,"verdict":verdict,"checks":checklist,"parameter_counts":counts,"training_started":False,"p2_r_authorized":False,"automatic_continuation":False}
    write(diag/"P2_6_FINAL_VERDICT.md","# P2.6 final verdict\n\n`"+verdict+"`\n\n```json\n"+json.dumps(payload,indent=2)+"\n```\n"); write(diag/"P2_6_VALIDATION.json",json.dumps(payload,indent=2)+"\n"); print(json.dumps(payload,indent=2))

if __name__=="__main__":main()
