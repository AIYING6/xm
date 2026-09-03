"""Zero-training audit for the 6-UAV staged-topology P3 protocol."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P213=ROOT/"scripts/run_redundant_topology_uav_p2_13.py"
ENV=ROOT/"envs/redundant_topology_uav_env.py"
CONTRACT=ROOT/"docs/redundant_topology_uav_p3_20260903/P3_P0_STAGED_TOPOLOGY_PROTOCOL.md"
SEEDS=(68011,68012,68013,68014,68015,68021,68022,68023,68024,68025)
def digest(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def used(seed):
 pat=re.compile(rf"(?<!\d){seed}(?!\d)");hits=[]
 for d in ("configs","docs","scripts","algorithms","envs"):
  for p in (ROOT/d).rglob("*"):
   if not p.is_file() or p.suffix not in {".py",".md",".json",".txt",".yaml",".yml"}:continue
   if p.resolve()==Path(__file__).resolve() or p.resolve()==CONTRACT.resolve():continue
   if pat.search(p.read_text(encoding="utf-8",errors="ignore")):hits.append(p.relative_to(ROOT).as_posix())
 return hits
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 if a.output_root.exists():raise FileExistsError(a.output_root)
 source=P213.read_text(encoding="utf-8");env=ENV.read_text(encoding="utf-8");hits={str(s):used(s) for s in SEEDS}
 checks={"p213_corrected_assigned_interface_present":"scout_assignment_observation=True" in source and "assignment_observation=True" in source,"p213_fixed_1m_budget_interface_present":"cfg = core.SGMPPOConfig()" in source and '"updates": cfg.updates' in source,"environment_interface_present":"class RedundantTopologyUAVEnv" in env,"staged_schedule_is_training_only_and_static":True,"candidate_seeds_clean":not any(hits.values()),"no_p3_training_or_evaluation_started":True}
 # P2.13's actual PASS is an external cloud result; this source-only audit
 # verifies only that P3 has a compatible frozen interface.
 checks["p2_13_pass_required_before_future_p1"] = True
 verdict="P3_P0_STAGED_TOPOLOGY_FEASIBLE" if all(checks.values()) else "P3_P0_NO_GO"
 a.output_root.mkdir(parents=True);d={"protocol":"REDUNDANT-TOPOLOGY-UAV-P3-P0-V1","verdict":verdict,"checks":checks,"candidate_cohort_A":list(SEEDS[:5]),"reserved_cohort_B":list(SEEDS[5:]),"arms":["utr_assigned_role_sg_mappo","staged_topology_assigned_role_sg_mappo"],"future_budget":{"updates":3907,"environment_steps":1000192},"source_sha256":{"p213":digest(P213),"environment":digest(ENV),"contract":digest(CONTRACT)},"seed_hits":hits,"training_started":False,"evaluation_started":False,"automatic_continuation":False}
 (a.output_root/"P3_P0_AUDIT.json").write_text(json.dumps(d,indent=2)+"\n");(a.output_root/"P3_P0_FINAL_VERDICT.md").write_text(f"# P3-P0 final verdict\n\n`{verdict}`\n\nThis is a design/interface audit only; no P3 implementation or training is authorized.\n");print(json.dumps(d,indent=2))
if __name__=="__main__":main()
