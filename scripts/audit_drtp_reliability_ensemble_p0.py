"""Zero-training feasibility and leakage audit for a Reliable-DRTP ensemble route.

This audit deliberately performs no checkpoint loading, rollout, evaluation, or
training. It turns the current execution interfaces into a pre-registration
contract for a future ensemble/distillation study, should one be authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
EVALUATOR = ROOT / "scripts" / "run_phase_rsg1_development_smoke.py"
DEVELOPMENT_EVALUATOR = ROOT / "scripts" / "run_drtp_sg_development_evaluation.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(text: str, needle: str, label: str) -> dict[str, object]:
    return {"label": label, "needle": needle, "pass": needle in text}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "docs" / "reliable_drtp_ensemble_p0",
        help="Documentation-only output directory; it must be new or empty.",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_dir}")

    agent_source = AGENT.read_text(encoding="utf-8")
    evaluator_source = EVALUATOR.read_text(encoding="utf-8")
    development_source = DEVELOPMENT_EVALUATOR.read_text(encoding="utf-8")
    checks = [
        require(agent_source, "Categorical(logits=logits)", "discrete categorical policy distribution"),
        require(agent_source, "torch.multinomial(probs", "explicit probability sampling path"),
        require(agent_source, "deterministic: bool = False", "deterministic policy-action interface"),
        require(evaluator_source, "deterministic=True", "existing evaluator uses deterministic actions"),
        require(development_source, "tape = json.loads", "evaluation tape is explicit data, not training input"),
        require(development_source, "held_out_tape_used", "evaluation manifest records held-out status"),
        require(agent_source, "evaluation_enabled: bool = True", "training/evaluation mode is an explicit configuration boundary"),
    ]
    passed = all(bool(item["pass"]) for item in checks)
    verdict = "RELIABILITY_ENSEMBLE_P0_DESIGN_FEASIBLE" if passed else "RELIABILITY_ENSEMBLE_P0_NOT_FEASIBLE"
    source_hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in (AGENT, EVALUATOR, DEVELOPMENT_EVALUATOR)
    }

    contract = {
        "protocol": "RELIABILITY-ENSEMBLE-P0-V1",
        "verdict": verdict,
        "zero_training": True,
        "rollouts_started": False,
        "checkpoints_loaded": False,
        "evaluation_started": False,
        "new_algorithm_authorized": False,
        "mainline_a_modified": False,
        "source_hashes": source_hashes,
        "interface_checks": checks,
        "execution_design": {
            "policy_aggregation": "For each agent and state, uniformly average fixed member Categorical probabilities, then take argmax for deterministic evaluation or draw exactly one action from the pooled distribution with a deployment-only generator.",
            "logit_warning": "Do not average raw logits unless that alternative is pre-registered; probability averaging is the frozen candidate because it remains a valid simplex by construction.",
            "runtime_requirements": [
                "All members receive exactly the same observation, graph, role, adjacency and intent tensors.",
                "A member must be a fixed final checkpoint; no checkpoint may be selected using formal, independent or held-out evaluation outcomes.",
                "The ensemble size K, member-seed lists, uniform weights, aggregation rule and deterministic/stochastic execution convention must be frozen before any training.",
                "For stochastic deployment, use one new deployment-only Torch generator after pooling; never let member-specific sampling influence the pooled action.",
            ],
        },
        "distillation_design": {
            "feasible": True,
            "teacher_target": "stop-gradient pooled teacher probabilities from fixed ensemble members",
            "student_loss": "A separately initialized student may add KL(teacher_probs || student_probs) only on training rollout batches or a separately frozen training-only distillation tape.",
            "prohibited_inputs": [
                "formal evaluation tape", "independent cohort evaluation tape", "held-out/unseen tape",
                "evaluation return", "final seed-quality label", "future trajectory information",
            ],
            "no_leakage_rule": "Teacher checkpoints and any distillation examples must be determined exclusively from pre-frozen training seeds and training-only rollouts. Evaluation code may consume the final frozen student/ensemble only after training ends.",
        },
        "fair_comparison_contract": [
            "Compare E-DRTP against E-UTR with the same K, architecture, member budgets, training-seed allocation, fixed-checkpoint convention, aggregation rule and evaluation tape.",
            "Retain single Original DRTP and UTR only as contextual references; do not attribute an ensemble-versus-single difference solely to DRTP.",
            "Treat each ensemble bundle, not each member and not each episode, as one trained policy unit for seed-level inference.",
            "Cohorts must remain separate. Do not pool a favorable cohort with an unfavorable cohort to claim reliability.",
        ],
        "cost_contract": [
            "Execution-only ensemble cost is K actor forward passes per environment decision; the critic is not required for action selection.",
            "Persisted deployment weights scale with K if full agents are kept; a deployment package may omit critics only if this is applied identically to all ensemble arms and documented.",
            "Distillation adds teacher forwards during student training and must report training environment interactions separately from teacher-forward compute; it must not claim equal compute to a single policy.",
        ],
        "next_authorization_boundary": "No ensemble training, distillation training, evaluation, member selection or parameter sweep is authorized by P0. A separate P1 contract must freeze K, candidate member construction, training-only data source, comparator E-UTR, two cohorts, compute budget and gate before execution.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "RELIABILITY_ENSEMBLE_P0_AUDIT.json").write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Reliable-DRTP ensemble/distillation P0 design audit", "",
        f"**Verdict:** {verdict}.", "",
        "This is a zero-training, zero-rollout, zero-evaluation source-interface audit. It does not create an ensemble, train a student, load checkpoints, or alter Mainline A.", "",
        "## Feasibility result", "",
        "The current actor emits categorical logits and the agent constructs Categorical(logits=logits). A future execution-only ensemble can therefore pool each fixed member's action probabilities into one valid categorical distribution. The existing evaluator is deterministic, so a fair future evaluation must use the argmax of the pooled probabilities for every ensemble arm rather than change only one method's action convention.", "",
        "## Mandatory leakage boundary", "",
        "Ensemble members, their weights, and any distillation examples must be chosen solely from pre-frozen training seeds and training-only rollouts. Formal, independent, and held-out evaluation tapes; all evaluation returns; final seed labels; and future trajectory information are prohibited from member selection, teacher targets, thresholds, or loss weights. A distilled student may use stop-gradient pooled teacher probabilities only on its training data.", "",
        "## Mandatory fair-comparison boundary", "",
        "A future study must compare E-DRTP with E-UTR under identical ensemble size K, member training budgets, architecture, seed allocation, checkpoint convention, pooling rule, action convention and evaluation tape. Single-policy DRTP and UTR remain references, not causal controls for an ensemble effect. The independent unit is an ensemble bundle/training seed, never its episodes or constituent members.", "",
        "## Compute disclosure", "",
        "An execution-only ensemble requires K actor forward passes per environment decision. Distillation adds teacher forward compute during student training. Both costs must be reported separately from environment interactions; neither may be presented as a single-policy compute match.", "",
        "## P0 checks", "",
    ]
    lines.extend([f"- {'PASS' if item['pass'] else 'FAIL'} — {item['label']} ({item['needle']})." for item in checks])
    lines.extend(["", "## Stop boundary", "", "P0 authorizes no training, evaluation, checkpoint/member selection, hyperparameter sweep, or paper modification. Any P1 must be separately authorized with a frozen K, member construction rule, training-only distillation source, E-UTR comparator, cohort structure, and GO/NO-GO gate.", "", "## Input hashes", ""])
    lines.extend([f"- {name}: {digest}" for name, digest in source_hashes.items()])
    (args.output_dir / "RELIABILITY_ENSEMBLE_P0_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "output": str(args.output_dir), "zero_training": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
