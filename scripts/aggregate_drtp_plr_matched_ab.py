from __future__ import annotations
import argparse,csv,json,statistics
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.drtp_plr_matched_ab_contracts import SEEDS
PERT=('F0','TE','TL','DS','DL','CP')
def read(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def write(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def locate(root,cohort):
 files=list(root.glob('**/per_seed_condition_summary.csv'))
 matches=[]
 for p in files:
  rows=read(p)
  if rows and any(r.get('method')=='utr_sg' and int(r.get('train_seed',-1)) in SEEDS[cohort] for r in rows):matches.append(p)
 if len(matches)!=1:raise RuntimeError(f'expected one extracted {cohort} baseline summary, found {len(matches)}')
 return matches[0]
def endpoint(rows,method,seeds):
 out=[]
 for s in seeds:
  d={r['condition']:r for r in rows if r['method']==method and int(r['train_seed'])==s}
  if set(d)!={'nominal',*PERT}:raise RuntimeError(f'incomplete {method}/seed{s}')
  x=[d[c] for c in PERT];out.append({'method':method,'train_seed':s,'J_nominal':float(d['nominal']['J']),'J_perturbed':statistics.mean(float(r['J']) for r in x),'J_perturbed_worst_condition':min(float(r['J']) for r in x),'success_perturbed':statistics.mean(float(r['success']) for r in x),'collision_perturbed':statistics.mean(float(r['collision']) for r in x),'timeout_perturbed':statistics.mean(float(r['timeout']) for r in x)})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--baseline-a-root',type=Path,required=True);p.add_argument('--baseline-b-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:raise SystemExit('explicit --execute is required')
 out=a.output_root/'diagnostics'/'plr_matched_ab_final'
 if out.exists():raise FileExistsError(f'refusing to overwrite {out}')
 all_end=[];paired=[];summaries=[]
 for c,broot in (('A',a.baseline_a_root),('B',a.baseline_b_root)):
  baseline=read(locate(broot,c));plr=read(a.output_root/'cohorts'/c/'evaluations'/'final_10m'/'per_seed_condition_summary.csv');rows=baseline+plr;ends=sum((endpoint(rows,m,SEEDS[c]) for m in ('utr_sg','drtp_sg','plr_style_sg')),[]);all_end += [{**r,'cohort':c} for r in ends];look={(r['method'],r['train_seed']):r for r in ends}
  for base in ('utr_sg','drtp_sg'):
   for s in SEEDS[c]:paired.append({'cohort':c,'candidate':'plr_style_sg','baseline':base,'train_seed':s,**{f'delta_{k}':look[('plr_style_sg',s)][k]-look[(base,s)][k] for k in ('J_nominal','J_perturbed','J_perturbed_worst_condition','success_perturbed','collision_perturbed','timeout_perturbed')}})
  for m in ('utr_sg','drtp_sg','plr_style_sg'):
   z=[r for r in ends if r['method']==m];summaries.append({'cohort':c,'method':m,'n_training_seeds':len(z),'mean_J_perturbed':statistics.mean(r['J_perturbed'] for r in z),'median_J_perturbed':statistics.median(r['J_perturbed'] for r in z),'min_J_perturbed':min(r['J_perturbed'] for r in z),'sample_sd_J_perturbed':statistics.stdev(r['J_perturbed'] for r in z),'mean_collision_perturbed':statistics.mean(r['collision_perturbed'] for r in z),'mean_timeout_perturbed':statistics.mean(r['timeout_perturbed'] for r in z)})
 out.mkdir(parents=True);write(out/'PLR_MATCHED_AB_PER_SEED_ENDPOINTS.csv',all_end);write(out/'PLR_MATCHED_AB_PAIRED_DELTAS.csv',paired);write(out/'PLR_MATCHED_AB_COHORT_SUMMARY.csv',summaries);report={'protocol':'DRTP-PLR-EXTERNAL-MATCHED-AB-REPORT-V2','verdict':'PLR_EXTERNAL_MATCHED_AB_REPORTED','A_B_primary_reporting_separate':True,'pooled_n10_descriptive_only':True,'baseline_retraining':False,'drtp_modified':False,'automatic_algorithm_revision':False};(out/'PLR_MATCHED_AB_FINAL_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');(out/'PLR_MATCHED_AB_FINAL_REPORT.md').write_text('# Matched A/B PLR external comparison\n\n`PLR_EXTERNAL_MATCHED_AB_REPORTED`\n\nUTR and Original DRTP are reused frozen endpoints. Cohorts A and B are reported separately; any pooled n=10 display is descriptive only.\n',encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
