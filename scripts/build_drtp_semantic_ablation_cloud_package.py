"""Build the 10-trajectory non-paired DRTP semantic-ablation cloud package."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "drtp_semantic_ablation_freeze_20260907.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one patch anchor, found {text.count(old)}")
    return text.replace(old, new)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, default=ROOT / "output" / "DRTP_STABILIZATION_FINAL_CONFIRMATION_10M.zip")
    parser.add_argument("--output-package", type=Path, default=ROOT / "output" / "DRTP_SEMANTIC_ABLATION_NONPAIRED_10M_V1.zip")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_package.exists() or args.output_package.with_suffix(args.output_package.suffix + ".sha256").exists():
        raise FileExistsError("refusing to overwrite an existing cloud package")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["fresh_seed_registry"] != [80011, 80012, 80013, 80014, 80015]:
        raise RuntimeError("fresh non-paired seed registry differs from the frozen protocol")
    with tempfile.TemporaryDirectory(prefix="drtp-semantic-ablation-") as temporary:
        temporary_root = Path(temporary)
        with ZipFile(args.source_archive) as archive:
            prefix = next(name.split("/", 1)[0] for name in archive.namelist() if "/" in name)
            for relative, expected in freeze["source_members_sha256"].items():
                if hashlib.sha256(archive.read(f"{prefix}/{relative}")).hexdigest() != expected:
                    raise RuntimeError(f"source hash mismatch: {relative}")
            archive.extractall(temporary_root)
        extracted = temporary_root / prefix
        package = temporary_root / "DRTP_SEMANTIC_ABLATION_NONPAIRED_10M"
        extracted.rename(package)
        shutil.copy2(ROOT / "algorithms" / "ri_gmappo" / "drtp_semantic_ablation_sampler.py", package / "algorithms" / "ri_gmappo")
        shutil.copy2(FREEZE, package / "configs" / FREEZE.name)

        learner = (package / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8")
        learner = replace_once(learner,
            "from algorithms.ri_gmappo.drtp_topology_sampler import AnchoredEGTRTopologySampler, EGTRTopologySampler\n",
            "from algorithms.ri_gmappo.drtp_topology_sampler import AnchoredEGTRTopologySampler, EGTRTopologySampler\nfrom algorithms.ri_gmappo.drtp_semantic_ablation_sampler import SemanticAblationTopologySampler\n")
        learner = replace_once(learner,
            '{"none", "utr", "snr", "drtp", "pp_drtp", "r_drtp", "egtr", "anchored_egtr", "drtp_tr", "conservative_drtp"}',
            '{"none", "utr", "snr", "drtp", "pp_drtp", "r_drtp", "egtr", "anchored_egtr", "drtp_tr", "conservative_drtp", "random_drtp", "fixed_drtp"}')
        learner = replace_once(learner, "    if drtp_mode == \"egtr\":\n",
            "    if drtp_mode in {\"random_drtp\", \"fixed_drtp\"}:\n        drtp_sampler = SemanticAblationTopologySampler(drtp_mode, sampler_seed, sampler_updates)\n    elif drtp_mode == \"egtr\":\n")
        write(package / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py", learner)

        runner = (package / "scripts" / "run_drtp_stabilization_confirmatory_single.py").read_text(encoding="utf-8")
        runner = replace_once(runner, 'PROTOCOL = "DRTP-STABILIZATION-FINAL-CONFIRMATION-10M-V1"', 'PROTOCOL = "DRTP-SEMANTIC-ABLATION-NONPAIRED-10M-V1"')
        runner = replace_once(runner, 'SEEDS = (78011, 78012, 78013, 78014, 78015)', 'SEEDS = (80011, 80012, 80013, 80014, 80015)')
        runner = replace_once(runner, 'ARMS = {\n    "utr_sg": ("utr", None), "drtp_sg": ("drtp", None), "egtr_sg": ("egtr", None),\n    "global_anchored_egtr_a075_sg": ("anchored_egtr", 0.75),\n}', 'ARMS = {"fixed_drtp_sg": ("fixed_drtp", None), "random_drtp_sg": ("random_drtp", None)}')
        runner = replace_once(runner, 'TAPE_PROTOCOL = "DRTP-STABILIZATION-CONFIRMATORY-TAPE-V1"', 'TAPE_PROTOCOL = "DRTP-SEMANTIC-ABLATION-NONPAIRED-TAPE-V1"')
        runner = replace_once(runner, 'list(range(780000, 780100))', 'list(range(800000, 800100))')
        write(package / "scripts" / "run_drtp_semantic_ablation_single.py", runner)

        tape = (package / "scripts" / "create_drtp_stabilization_confirmatory_tape.py").read_text(encoding="utf-8")
        tape = tape.replace('DRTP-STABILIZATION-CONFIRMATORY-TAPE-V1', 'DRTP-SEMANTIC-ABLATION-NONPAIRED-TAPE-V1').replace('list(range(780000, 780100))', 'list(range(800000, 800100))')
        write(package / "scripts" / "create_drtp_semantic_ablation_tape.py", tape)

        evaluator = (package / "scripts" / "run_drtp_stabilization_confirmatory_evaluation.py").read_text(encoding="utf-8")
        evaluator = evaluator.replace('DRTP-STABILIZATION-FINAL-CONFIRMATION-10M-EVALUATION-V1', 'DRTP-SEMANTIC-ABLATION-NONPAIRED-10M-EVALUATION-V1').replace('DRTP-STABILIZATION-CONFIRMATORY-TAPE-V1', 'DRTP-SEMANTIC-ABLATION-NONPAIRED-TAPE-V1').replace('list(range(780000, 780100))', 'list(range(800000, 800100))').replace('from run_drtp_stabilization_confirmatory_single import ARMS, SEEDS, STEPS, UPDATES', 'from run_drtp_semantic_ablation_single import ARMS, SEEDS, STEPS, UPDATES')
        write(package / "scripts" / "run_drtp_semantic_ablation_evaluation.py", evaluator)

        aggregate = '''"""Aggregate the new, intentionally non-paired semantic-ablation cohort."""\nimport argparse, csv, json, statistics\nfrom collections import defaultdict\nfrom pathlib import Path\n\nARMS=("fixed_drtp_sg","random_drtp_sg")\nSEEDS=(80011,80012,80013,80014,80015)\nPERTURBED=("F0","TE","TL","DS","DL","CP")\ndef mean(x): return statistics.fmean(x)\ndef write(path, rows):\n    with path.open("w",newline="",encoding="utf-8") as h:\n        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)\ndef main():\n p=argparse.ArgumentParser();p.add_argument("--evaluation-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()\n if not a.execute: raise SystemExit("explicit --execute is required")\n out=a.output_root/"diagnostics"/"semantic_ablation_final"\n if out.exists(): raise FileExistsError(out)\n rows=list(csv.DictReader((a.evaluation_root/"per_seed_condition_summary.csv").open(encoding="utf-8")))\n by=defaultdict(dict)\n for r in rows: by[(r["method"],int(r["train_seed"]))][r["condition"]]=r\n endpoints=[]\n for arm in ARMS:\n  for seed in SEEDS:\n   cell=by[(arm,seed)]\n   if set(cell)!={"nominal",*PERTURBED}: raise RuntimeError(f"incomplete endpoint {arm}/{seed}")\n   p=[cell[g] for g in PERTURBED]\n   endpoints.append({"method":arm,"train_seed":seed,"J_nominal":float(cell["nominal"]["J"]),"J_perturbed":mean([float(x["J"]) for x in p]),"J_perturbed_worst_condition":min(float(x["J"]) for x in p),"success_perturbed":mean([float(x["success"]) for x in p]),"timeout_perturbed":mean([float(x["timeout"]) for x in p]),"collision_perturbed":mean([float(x["collision"]) for x in p])})\n summary=[]\n for arm in ARMS:\n  chosen=[r for r in endpoints if r["method"]==arm]; record={"method":arm,"n_training_seeds":len(chosen)}\n  for metric in ("J_perturbed","J_perturbed_worst_condition","success_perturbed","timeout_perturbed","collision_perturbed"):\n   values=[r[metric] for r in chosen];record.update({f"mean_{metric}":mean(values),f"median_{metric}":statistics.median(values),f"worst_seed_{metric}":max(values) if metric in {"timeout_perturbed","collision_perturbed"} else min(values),f"sample_sd_{metric}":statistics.stdev(values)})\n  summary.append(record)\n out.mkdir(parents=True);write(out/"SEMANTIC_ABLATION_PER_SEED_ENDPOINTS.csv",endpoints);write(out/"SEMANTIC_ABLATION_COHORT_SUMMARY.csv",summary)\n report={"protocol":"DRTP-SEMANTIC-ABLATION-NONPAIRED-10M-V1","verdict":"SEMANTIC_ABLATION_NONPAIRED_REPORTED","primary_unit":"training_seed","new_methods":list(ARMS),"reused_main_references":["utr_sg","drtp_sg"],"paired_delta_with_reused_reference_forbidden":True,"automatic_algorithm_revision":False}\n (out/"SEMANTIC_ABLATION_FINAL_REPORT.json").write_text(json.dumps(report,indent=2)+"\\n",encoding="utf-8");print(json.dumps(report,indent=2))\nif __name__=="__main__":main()\n'''
        write(package / "scripts" / "aggregate_drtp_semantic_ablation.py", aggregate)
        launcher = '''#!/usr/bin/env bash\nset -euo pipefail\nPYTHON_BIN="${PYTHON_BIN:-python}"\nOUTPUT_ROOT="${OUTPUT_ROOT:-results/ablation/drtp_semantic_ablation_nonpaired}"\nMAX_PARALLEL="${MAX_PARALLEL:-10}"\n[[ "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 10 ]] || { echo "MAX_PARALLEL must be 1..10" >&2; exit 2; }\nexport OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"\n[[ ! -e "$OUTPUT_ROOT/runs" ]] || { echo "ablation runs already exist" >&2; exit 2; }\nmkdir -p "$OUTPUT_ROOT"\n"$PYTHON_BIN" scripts/verify_drtp_semantic_ablation_cloud_preflight.py --output-root "$OUTPUT_ROOT/preflight" --execute\n"$PYTHON_BIN" scripts/create_drtp_semantic_ablation_tape.py --output-root "$OUTPUT_ROOT/tape"\nrunning=0\nfor arm in fixed_drtp_sg random_drtp_sg; do for seed in 80011 80012 80013 80014 80015; do\n "$PYTHON_BIN" scripts/run_drtp_semantic_ablation_single.py --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &\n running=$((running+1)); if [[ "$running" -ge "$MAX_PARALLEL" ]]; then wait -n; running=$((running-1)); fi\ndone; done\nwait\nprintf '%s\\n' '{"status":"DRTP_SEMANTIC_ABLATION_TRAINING_COMPLETE","trajectories":10,"evaluation_started":false}' > "$OUTPUT_ROOT/SEMANTIC_ABLATION_TRAINING_COMPLETE.json"\n"$PYTHON_BIN" scripts/run_drtp_semantic_ablation_evaluation.py --trained-root "$OUTPUT_ROOT" --output-root "$OUTPUT_ROOT/evaluations/final_10m" --workers "$MAX_PARALLEL" --execute\n"$PYTHON_BIN" scripts/aggregate_drtp_semantic_ablation.py --evaluation-root "$OUTPUT_ROOT/evaluations/final_10m" --output-root "$OUTPUT_ROOT" --execute\nprintf '%s\\n' '{"status":"DRTP_SEMANTIC_ABLATION_COMPLETE","trajectories":10,"endpoint_evaluation_completed":true,"automatic_algorithm_revision":false}' > "$OUTPUT_ROOT/SEMANTIC_ABLATION_COMPLETE.json"\n'''
        write(package / "scripts" / "launch_drtp_semantic_ablation_autodl.sh", launcher)
        preflight = '''import argparse,json,hashlib\nfrom pathlib import Path\nfrom scripts.run_drtp_semantic_ablation_single import ARMS,SEEDS,STEPS,UPDATES,training_config\nROOT=Path(__file__).resolve().parents[1]\ndef d(p): return hashlib.sha256(p.read_bytes()).hexdigest()\ndef main():\n p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()\n if not a.execute: raise SystemExit("explicit --execute is required")\n if a.output_root.exists(): raise FileExistsError(a.output_root)\n f=json.loads((ROOT/"configs/drtp_semantic_ablation_freeze_20260907.json").read_text()); cfg=training_config("fixed_drtp_sg",SEEDS[0],Path("x")); checks={"new_arms_exact":set(ARMS)=={"fixed_drtp_sg","random_drtp_sg"},"fresh_seeds_exact":SEEDS==(80011,80012,80013,80014,80015),"mature_budget_exact":UPDATES==39063 and STEPS==10000128,"only_reset_sampler_varies":cfg.graph_encoder=="single" and cfg.evaluation_enabled is False,"no_utr_or_drtp_retraining":not ({"utr_sg","drtp_sg"}&set(ARMS))}\n if not all(checks.values()): raise RuntimeError(checks)\n a.output_root.mkdir(parents=True);r={"protocol":f["protocol"],"verdict":"SEMANTIC_ABLATION_CLOUD_PREFLIGHT_PASS","checks":checks,"source_sha256":{"learner":d(ROOT/"algorithms/ri_gmappo/simple_ri_gmappo.py"),"base_sampler":d(ROOT/"algorithms/ri_gmappo/drtp_topology_sampler.py"),"ablation_sampler":d(ROOT/"algorithms/ri_gmappo/drtp_semantic_ablation_sampler.py"),"environment":d(ROOT/"envs/uav_intercept_3d_env.py")},"training_started":False,"evaluation_started":False};\n for n in ("SEMANTIC_ABLATION_PREFLIGHT.json","SEMANTIC_ABLATION_PREFLIGHT.md"): (a.output_root/n).write_text(json.dumps(r,indent=2)+"\\n")\n print(json.dumps(r,indent=2))\nif __name__=="__main__": main()\n'''
        write(package / "scripts" / "verify_drtp_semantic_ablation_cloud_preflight.py", preflight)
        preflight_path = package / "scripts" / "verify_drtp_semantic_ablation_cloud_preflight.py"
        write(preflight_path, replace_once(
            preflight_path.read_text(encoding="utf-8"),
            "from pathlib import Path\n",
            "from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n",
        ))
        (package / "README_ABLATION.md").write_text("# Non-paired DRTP mechanism ablation\n\nThis package trains only Fixed-DRTP and Random-DRTP for five fresh seeds each. UTR and DRTP are deliberately not retrained. Reused main endpoints must be reported as an independent reference, never as paired deltas.\n", encoding="utf-8")
        with ZipFile(args.output_package, "w", ZIP_DEFLATED) as archive:
            for path in package.rglob("*"):
                if path.is_file(): archive.write(path, path.relative_to(temporary_root).as_posix())
    sha = digest(args.output_package)
    args.output_package.with_suffix(args.output_package.suffix + ".sha256").write_text(f"{sha}  {args.output_package.name}\n", encoding="ascii")
    print(json.dumps({"package": str(args.output_package), "sha256": sha, "trajectories": 10, "environment_steps": 100001280}, indent=2))


if __name__ == "__main__":
    main()
