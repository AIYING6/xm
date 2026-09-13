"""Strictly legal-information transparent-controller audit.

Unlike prior geometry-oracle controllers, each role here obtains a threat
position only from its own sighting or from a node reachable in the current
communication graph.  Fixed patrol fallbacks use public mission geometry, not
hidden routes or red state.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig
from envs.multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv
from scripts.run_multi_threat_capacity_graph_mappo import PARAMETERS

POLICIES=("legal_parallel","legal_concentrated")


def action(env,agent,goal):
    delta=goal-env.base.blue_pos[agent];desired=math.atan2(float(delta[1]),float(delta[0]));error=math.atan2(math.sin(desired-float(env.base.blue_heading[agent])),math.cos(desired-float(env.base.blue_heading[agent])));turn=int(np.sign(error)) if abs(error)>.035 else 0;climb=int(np.sign(float(delta[2]))) if abs(float(delta[2]))>250 else 0
    return int((turn+1)*9+(climb+1)*3+2)


def known_threat(env,recipient,threat):
    reach=env.base._transitive_comm();sources=[source for source in range(env.num_agents) if reach[recipient,source]>0.5 and env._visible(source,threat)]
    if not sources:return None
    source=min(sources,key=lambda i:float(np.linalg.norm(env.red_pos[threat]-env.base.blue_pos[i])))
    return env.red_pos[threat].copy()


def legal_actions(env,policy):
    primary=known_threat(env,env.attacker,0);secondary=known_threat(env,env.scout,1)
    # These patrol points encode only the publicly fixed approach corridor;
    # they do not reveal the later asset assignment.
    fallback_primary=np.asarray((7000.,-env.config.red_initial_lateral,5000.),dtype=np.float32)
    fallback_secondary=np.asarray((7000.,env.config.red_initial_lateral,5000.),dtype=np.float32)
    if policy=="legal_parallel":
        scout_goal=secondary if secondary is not None else fallback_secondary
        attacker_goal=primary if primary is not None else fallback_primary
    elif policy=="legal_concentrated":
        scout_goal=primary if primary is not None else fallback_primary
        attacker_goal=primary if primary is not None else fallback_primary
    else:raise ValueError(policy)
    relay_goal=.5*(env.base.blue_pos[env.scout]+env.base.blue_pos[env.attacker])
    return np.asarray([action(env,env.scout,scout_goal),action(env,env.relay,relay_goal),action(env,env.attacker,attacker_goal)],dtype=np.int64)


def run(seed,policy):
    env=MultiThreatCapacityShapedDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed,**PARAMETERS));env.reset();info={};total=0.
    while not env.base.done:
        _,_,_,reward,_,info=env.step(legal_actions(env,policy));total+=float(reward.mean())
    return {"seed":seed,"policy":policy,"return":total,"defense_success":int(info.get("defense_success",0)>0.5),"asset_breach":int(info.get("asset_breach",0)>0.5),"timeout":int(info.get("timeout",0)>0.5)}


def main():
    p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--seed-start",type=int,default=107001);p.add_argument("--seeds",type=int,default=24);p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);rows=[run(a.seed_start+i,p) for i in range(a.seeds) for p in POLICIES]
    with (a.output_root/"MULTI_THREAT_CAPACITY_LEGAL_G1_ROWS.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    success={p:sum(int(r["defense_success"]) for r in rows if r["policy"]==p) for p in POLICIES};report={"protocol":"MULTI-THREAT-CAPACITY-LEGAL-G1-V1","verdict":"LEGAL_CONTROLLER_SIGNAL" if success["legal_parallel"]>success["legal_concentrated"] else "LEGAL_CONTROLLER_SIGNAL_NOT_ESTABLISHED","diagnostic_only":True,"training_started":False,"defense_success_by_controller":success,"parallel_minus_concentrated":success["legal_parallel"]-success["legal_concentrated"],"interpretation":"This is the first task-feasibility result that obeys the actor information boundary. It replaces neither previous physical-oracle diagnostics nor learned-policy tests."}
    (a.output_root/"MULTI_THREAT_CAPACITY_LEGAL_G1_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
if __name__=="__main__":main()
