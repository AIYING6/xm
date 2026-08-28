"""Preregistered B3 1M integrity and mechanism-gate data product."""
from __future__ import annotations
import argparse, csv, json, math
from collections import defaultdict
from pathlib import Path

ARMS, SEEDS = ("utr_sg", "drtp_sg"), (2701, 2702, 2703)
ROOT=Path(__file__).resolve().parents[1]

def avg(rows,key):
 vals=[]
 for row in rows:
  try:
   value=float(row[key]);
   if math.isfinite(value): vals.append(value)
  except (KeyError,TypeError,ValueError): pass
 return sum(vals)/len(vals) if vals else math.nan

def read_csv(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def main():
 p=argparse.ArgumentParser(); p.add_argument("--output-root",type=Path,required=True); p.add_argument("--execute",action="store_true"); a=p.parse_args()
 if not a.execute: raise SystemExit("--execute required")
 output=a.output_root; report=output / "diagnostics" / "b3_1m_mechanism_gate"; report.mkdir(parents=True,exist_ok=False)
 manifests=[]; integrity=True
 for arm in ARMS:
  for seed in SEEDS:
   m=json.loads((output/"runs"/arm/f"seed{seed}"/"run_manifest.json").read_text(encoding="utf-8")); manifests.append(m); integrity &= m.get("status")=="completed" and m.get("environment_steps")==1000192
 eval_manifest=json.loads((output/"evaluations"/"final_1m"/"evaluation_manifest.json").read_text(encoding="utf-8")); integrity &= eval_manifest.get("raw_rows")==3000
 rows=read_csv(output/"evaluations"/"final_1m"/"raw_episode_metrics.csv")
 grouped=defaultdict(list)
 for row in rows: grouped[(row["method"],int(row["train_seed"]),row["topology_condition"])].append(row)
 summary=[]
 for arm in ARMS:
  for seed in SEEDS:
   for cond in ("nominal","F0_44_80","T28_28_80","D120_44_120","C28_120"):
    part=grouped[(arm,seed,cond)]; summary.append({"method":arm,"seed":seed,"condition":cond,"J":avg(part,"J"),"timeout":avg(part,"timeout"),"collision":avg(part,"collision"),"constraint_violation":avg(part,"constraint_violation"),"failure_exposed":avg(part,"failure_exposed")})
 with (report/"seed_level_summary.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(summary[0])); w.writeheader();w.writerows(summary)
 # This is intentionally a gate *data product*. A mechanistic candidate is
 # not inferred from returns or a single correlation; telemetry requires the
 # frozen time-leading, UTR-controlled three-layer review.
 matrix=[{"layer":"sampler/exposure","artifact":"drtp_topology_sampler_log.csv + episode_summary.jsonl","status":"available"},{"layer":"behavior/support","artifact":"failure_event_window.jsonl (-20..60)","status":"available"},{"layer":"outcome","artifact":"final_1m raw episode metrics","status":"available"}]
 with (report/"mechanism_evidence_matrix.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(matrix[0]));w.writeheader();w.writerows(matrix)
 status="MECHANISM_1M_GATE_READY_FOR_REVIEW" if integrity else "TECHNICAL_INVALID"
 (report/"go_no_go.md").write_text(f"# B3 1M mechanism gate\n\nStatus: `{status}`.\n\nAll automatic checks retain every seed and episode. The frozen mechanism gate may only classify `MECHANISM_CANDIDATE` or `MECHANISM_HYPOTHESIS_NO_GO` after a time-leading, 2/3 DRTP-repeated, UTR-controlled three-layer telemetry review; it does not authorize an algorithm modification.\n",encoding="utf-8")
 (report/"mechanism_1m_gate_report.md").write_text(f"# DRTP B3 1M mechanism-gate report\n\nIntegrity: `{integrity}`; evaluation rows: `{len(rows)}`.\n\nThis report contains the preregistered 1M gate data products. No stabilization modification, 3M extension, or 10M run is started automatically.\n",encoding="utf-8")

if __name__=="__main__":main()
