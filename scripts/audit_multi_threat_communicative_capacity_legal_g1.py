"""G1 audit using only explicit delivered track messages."""
from __future__ import annotations
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig
from envs.multi_threat_communicative_capacity_defense_env import MultiThreatCommunicativeCapacityDefenseEnv
from scripts.run_multi_threat_capacity_graph_mappo import PARAMETERS

def act(env,i,goal):
 d=goal-env.base.blue_pos[i];h=math.atan2(float(d[1]),float(d[0]));e=math.atan2(math.sin(h-float(env.base.blue_heading[i])),math.cos(h-float(env.base.blue_heading[i])));return int(((int(np.sign(e)) if abs(e)>.035 else 0)+1)*9+((int(np.sign(float(d[2]))) if abs(float(d[2]))>250 else 0)+1)*3+2)
def track(env,agent,threat,fallback):return env.track_pos[agent,threat] if env.track_valid[agent,threat] else fallback
def actions(env,parallel):
 p=track(env,env.attacker,0,np.asarray((7000.,-env.config.red_initial_lateral,5000.),np.float32));s=track(env,env.scout,1,np.asarray((7000.,env.config.red_initial_lateral,5000.),np.float32));sg=s if parallel else p;rg=.5*(env.base.blue_pos[env.scout]+env.base.blue_pos[env.attacker]);return np.asarray([act(env,env.scout,sg),act(env,env.relay,rg),act(env,env.attacker,p)],np.int64)
def run(seed,parallel):
 env=MultiThreatCommunicativeCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed,**PARAMETERS));env.reset();info={}
 while not env.base.done:_,_,_,_,_,info=env.step(actions(env,parallel))
 return {"seed":seed,"controller":"parallel" if parallel else "concentrated","defense_success":int(info.get("defense_success",0.)>.5),"asset_breach":int(info.get("asset_breach",0.)>.5),"delivered_tracks":int(info.get("track_messages_valid",0.))}
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--seed-start",type=int,default=108001);p.add_argument("--seeds",type=int,default=24);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("pass --execute")
 if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
 a.output_root.mkdir(parents=True);rows=[run(a.seed_start+i,q) for i in range(a.seeds) for q in (False,True)]
 with (a.output_root/"COMMUNICATIVE_CAPACITY_LEGAL_G1_ROWS.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 win={name:sum(r["defense_success"] for r in rows if r["controller"]==name) for name in ("parallel","concentrated")};report={"protocol":"MULTI-THREAT-COMMUNICATIVE-CAPACITY-LEGAL-G1-V1","verdict":"COMMUNICATIVE_LEGAL_G1_PASS" if win["parallel"]>win["concentrated"] else "COMMUNICATIVE_LEGAL_G1_FAIL","diagnostic_only":True,"training_started":False,"defense_success_by_controller":win,"parallel_minus_concentrated":win["parallel"]-win["concentrated"],"interpretation":"Controller targets are derived only from explicit delivered track payloads or public fixed patrol geometry."};(a.output_root/"COMMUNICATIVE_CAPACITY_LEGAL_G1_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
if __name__=="__main__":main()
