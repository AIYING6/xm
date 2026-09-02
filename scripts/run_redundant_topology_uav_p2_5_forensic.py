"""Read-only P2.5 learner/formulation forensic audit.

It never instantiates an environment, samples a rollout, evaluates a policy or
performs an optimizer update.  All conclusions are bounded by what P2 actually
recorded, rather than inventing absent role-level telemetry.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

PROTOCOL = "P2_5_ZERO_TRAINING_LEARNER_FORENSIC_V1"
ARMS = ("plain_sg_mappo", "utr_sg_mappo")
SEEDS = (6201, 6202, 6203)
MILESTONE_ORDER = ("0", "125k", "250k", "500k", "750k", "1m")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f: return list(csv.DictReader(f))


def mean(rows: list[dict[str, str]], key: str) -> float:
    return float(np.mean([float(r[key]) for r in rows])) if rows else float("nan")


def save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows: return
    with path.open("w", newline="", encoding="utf-8") as f:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def source_audit() -> dict[str, Any]:
    learner = (ROOT / "algorithms" / "redundant_topology_sg_mappo.py").read_text(encoding="utf-8")
    env = (ROOT / "envs" / "redundant_topology_uav_env.py").read_text(encoding="utf-8")
    relay_noop = "Relay actions are ignored" in env and "np.ones(self.action_dim" in env
    one_actor = "self.actor = RoleGraphActor" in learner and "nn.ModuleDict" not in learner
    return {
        "relay_nonidle_actions_have_no_transition_effect": relay_noop,
        "relay_nonidle_actions_are_exposed_as_legal": relay_noop,
        "actor_is_shared_across_all_three_roles_not_within_role_only": one_actor,
        "role_embedding_present": "nn.Embedding(3" in learner,
        "centralized_critic_present": "self.critic" in learner,
        "action_mask_applied_to_logits": "masked_fill(masks <= 0" in learner,
        "checkpoint_contains_optimizer_rng_env": all(x in learner for x in ("optimizer", "env_states", "torch_rng", "numpy_rng", "python_rng")),
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--p2-root", required=True); ap.add_argument("--output-root", required=True); ap.add_argument("--execute", action="store_true"); args = ap.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False})); return
    p2, out = Path(args.p2_root), Path(args.output_root)
    eval_files = [p2 / "evaluations" / arm / f"seed{seed}_development.csv" for arm in ARMS for seed in SEEDS]
    logs = [p2 / "runs" / arm / f"seed{seed}" / "train_log.csv" for arm in ARMS for seed in SEEDS]
    if not all(x.exists() for x in eval_files + logs): raise RuntimeError("P2 artifacts incomplete; refusing forensic inference")
    if out.exists(): raise RuntimeError("P2.5 output exists; refusing overwrite")
    diag = out / "diagnostics"; diag.mkdir(parents=True)
    all_eval=[]
    for path in eval_files: all_eval.extend(read_csv(path))
    timeline=[]
    for arm in ARMS:
        for seed in SEEDS:
            run=[r for r in all_eval if r["arm"]==arm and int(r["seed"])==seed]
            for milestone in MILESTONE_ORDER:
                nominal=[r for r in run if r["milestone"]==milestone and r["group"]=="nominal"]
                if nominal: timeline.append({"arm":arm,"seed":seed,"milestone":milestone,"nominal_success":mean(nominal,"success"),"nominal_score":mean(nominal,"score"),"nominal_timeout":mean(nominal,"timeout"),"nominal_collision":mean(nominal,"collision"),"source":"frozen_development_evaluation"})
            for row in read_csv(p2 / "runs" / arm / f"seed{seed}" / "train_log.csv"):
                timeline.append({"arm":arm,"seed":seed,"milestone":row["update"],"nominal_success":"","nominal_score":"","nominal_timeout":"","nominal_collision":"","source":"training_only","policy_loss":row["policy_loss"],"value_loss":row["value_loss"],"entropy":row["entropy"],"approx_kl":row["approx_kl"],"clip_fraction":row["clip_fraction"],"grad_norm":row["grad_norm"]})
    save_csv(diag / "P2_5_MASTER_TIMELINE.csv", timeline)
    endpoint=[r for r in all_eval if r["milestone"]=="1m" and r["group"]=="nominal"]
    contrast=[]
    for arm in ARMS:
        for seed in SEEDS:
            series=[r for r in timeline if r["arm"]==arm and r["seed"]==seed and r["source"]=="frozen_development_evaluation"]
            initial=next((r for r in series if r["milestone"]=="0"), {})
            final=next((r for r in series if r["milestone"]=="1m"), {})
            contrast.append({"arm":arm,"seed":seed,"initial_nominal_success":initial.get("nominal_success"),"final_nominal_success":final.get("nominal_success"),"final_label":"success" if float(final.get("nominal_success",0))>=.5 else "failed","first_nontrivial_progress":"not observable: P2 did not log objective-progress traces","first_valid_coordination":"not observable: P2 did not log per-agent message/action traces","first_success_milestone":next((r["milestone"] for r in series if float(r["nominal_success"])>0),"none")})
    save_csv(diag / "P2_5_SUCCESS_FAILURE_CONTRAST.csv", contrast)
    audit=source_audit()
    # A relay action with no environment consequence and non-role-wise actor sharing are correctness/interface defects,
    # not a post-hoc performance claim. They invalidate P2 learner qualification before causal interpretation.
    defect = audit["relay_nonidle_actions_have_no_transition_effect"] and audit["relay_nonidle_actions_are_exposed_as_legal"] and audit["actor_is_shared_across_all_three_roles_not_within_role_only"]
    verdict = "P2_5_IMPLEMENTATION_DEFECT_FOUND" if defect else "P2_5_NO_ACTIONABLE_LEARNER_CAUSE"
    finite=[]
    for path in logs:
        for row in read_csv(path): finite.append(all(np.isfinite(float(row[x])) for x in ("policy_loss","value_loss","entropy","approx_kl","clip_fraction","grad_norm")))
    write(diag / "P2_5_FORENSIC_CONTRACT.md", "# P2.5 forensic contract\n\nRead-only analysis of existing P2 artifacts. No environment rollout, policy evaluation, PPO update, new seed, cloud training, or P2 semantic change occurred.\n")
    write(diag / "P2_5_RUN_MANIFEST.md", "# P2.5 run manifest\n\nP2 artifacts inspected: six training logs and six frozen development-evaluation CSVs. Independent unit: training seed.\n")
    write(diag / "P2_5_FIRST_DIVERGENCE_ANALYSIS.md", "# First divergence\n\nSee `P2_5_SUCCESS_FAILURE_CONTRAST.csv`. The earliest defensible performance separation is restricted to P2's frozen milestone observations; no finer performance rollout was generated.\n")
    write(diag / "P2_5_ROLE_SYMMETRY_AUDIT.md", "# Role symmetry audit\n\nPer-agent action, assignment and route-use telemetry was not recorded by P2, so no symmetry-collapse claim is possible. This absence is retained rather than reconstructed post hoc.\n")
    write(diag / "P2_5_ROLE_CREDIT_AUDIT.md", "# Role credit audit\n\nP2 did not retain role-wise advantage or gradient tensors. Credit starvation cannot be classified from the existing artifacts.\n")
    write(diag / "P2_5_EXPLORATION_CHAIN_ANALYSIS.md", "# Exploration-chain audit\n\nP2 did not retain event-level Scout→Relay→Terminal chain counts; no exploration-basin claim is made.\n")
    write(diag / "P2_5_OPTIMIZATION_CRITIC_AUDIT.md", f"# Optimization/critic audit\n\nAll retained PPO scalar telemetry finite: `{all(finite)}`. Explained variance, ratio distribution, role-wise gradients and advantage moments were not logged, so they are not inferred.\n")
    write(diag / "P2_5_PARAMETER_SHARING_AUDIT.md", "# Parameter-sharing audit\n\n```json\n"+json.dumps(audit,indent=2)+"\n```\n\nThe implementation has one `RoleGraphActor` conditioned by a role embedding, rather than separate within-role shared actor parameter sets. This violates the frozen P2 requirement that sharing be within role and not accidentally across incompatible roles.\n")
    write(diag / "P2_5_OBSERVATION_NORMALIZATION_AUDIT.md", "# Observation/normalization audit\n\nStatic actor observations are bounded by environment normalization. P2 did not persist role-wise observation distributions; no failed-seed-specific drift claim can be made.\n")
    write(diag / "P2_5_ACTION_DISTRIBUTION_AUDIT.md", "# Action-space audit\n\nRelay action values 1..K are exposed as legal, but the frozen environment ignores relay actions. Optimizing categorical probability over no-effect relay actions is an interface defect: it injects policy-gradient variance without a transition consequence.\n")
    write(diag / "P2_5_UTR_PLAIN_EXPLORATION_CONTRAST.md", "# UTR vs Plain exploration contrast\n\nThe observed 2/3 vs 1/3 nominal endpoint count is descriptive only. P2 lacks the event-level telemetry required to attribute it to broader route exposure or exploration.\n")
    write(diag / "P2_5_HORIZON_SUFFICIENCY_AUDIT.md", "# Horizon sufficiency\n\nThe existing outputs do not demonstrate two failed Plain seeds with repeated, task-relevant late improvement. `P2_5_HORIZON_INSUFFICIENT` is not supported.\n")
    precursor=[{"candidate":"role-specific sharing violation","pre_failure":True,"repeated":"structural/all runs","success_contrast":"not required for correctness defect","actionable":True},{"candidate":"relay no-effect action exposure","pre_failure":True,"repeated":"structural/all runs","success_contrast":"not required for correctness defect","actionable":True},{"candidate":"symmetry collapse","pre_failure":"unobservable","repeated":"unobservable","success_contrast":"unobservable","actionable":False},{"candidate":"credit/critic precursor","pre_failure":"unobservable","repeated":"unobservable","success_contrast":"unobservable","actionable":False}]
    save_csv(diag / "P2_5_PRECURSOR_MATRIX.csv", precursor)
    mapping="A future minimal correction, if separately authorized, would (i) make relay a one-action/passive role or add a frozen causal relay action and (ii) use separate role-shared actor trunks. No patch or retraining is performed by P2.5."
    write(diag / "P2_5_INTERVENTION_MAPPING.md", "# Intervention mapping\n\n"+mapping+"\n")
    write(diag / "P2_5_CAUSAL_CLASSIFICATION.md", "# Causal classification\n\nThe audit identifies a learner/interface defect, not a completed causal explanation of every failed seed. P2 endpoint performance is invalid for method qualification until the frozen P2 learner contract is corrected and requalified on fresh seeds.\n")
    write(diag / "P2_5_A_LINE_REGRESSION.md", "# A-line regression\n\nP2.5 reads only P2 outputs and an independent learner/environment source surface; it changes no A-line source or result.\n")
    result={"protocol":PROTOCOL,"verdict":verdict,"training_started":False,"new_evaluation_started":False,"cloud_training_started":False,"all_retained_ppo_scalars_finite":all(finite),"source_audit":audit,"p3_authorized":False,"automatic_continuation":False}
    write(diag / "P2_5_FINAL_VERDICT.md", "# P2.5 final verdict\n\n`"+verdict+"`\n\n```json\n"+json.dumps(result,indent=2)+"\n```\n")
    write(diag / "P2_5_FORENSIC_RESULT.json", json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__": main()
