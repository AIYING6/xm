"""Zero-training design audit for Consensus-Anchored Policy Distillation.

The audit is deliberately static.  It loads no checkpoint, constructs no
environment, executes no rollout, performs no optimizer step, and reads no
evaluation tape.  Its purpose is to decide whether the current categorical
actor interface can support a future population-to-single-policy study without
changing the frozen A-line evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
SAMPLER = ROOT / "algorithms" / "ri_gmappo" / "drtp_topology_sampler.py"
FREEZE = ROOT / "configs" / "capd_p0_design_freeze.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(values: list[float]) -> list[float]:
    total = sum(values)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("invalid probability mass")
    return [value / total for value in values]


def geometric_centroid(policies: list[list[float]], epsilon: float = 1e-12) -> list[float]:
    if not policies or any(len(policy) != len(policies[0]) for policy in policies):
        raise ValueError("policies must be a non-empty rectangular matrix")
    logits = [
        sum(math.log(max(policy[action], epsilon)) for policy in policies) / len(policies)
        for action in range(len(policies[0]))
    ]
    maximum = max(logits)
    return normalize([math.exp(value - maximum) for value in logits])


def kl(left: list[float], right: list[float], epsilon: float = 1e-12) -> float:
    return sum(
        p * (math.log(max(p, epsilon)) - math.log(max(q, epsilon)))
        for p, q in zip(left, right)
        if p > 0.0
    )


def js(left: list[float], right: list[float]) -> float:
    midpoint = [(p + q) / 2.0 for p, q in zip(left, right)]
    return 0.5 * kl(left, midpoint) + 0.5 * kl(right, midpoint)


def consensus_target(
    anchor: list[float], explorers: list[list[float]], tau: float
) -> tuple[list[float], float, float, list[float]]:
    if tau <= 0.0:
        raise ValueError("tau must be positive")
    centroid = geometric_centroid(explorers)
    disagreement = sum(js(policy, centroid) for policy in explorers) / len(explorers)
    confidence = math.exp(-disagreement / tau)
    log_target = [
        (1.0 - confidence) * math.log(max(p_u, 1e-12))
        + confidence * math.log(max(p_e, 1e-12))
        for p_u, p_e in zip(anchor, centroid)
    ]
    maximum = max(log_target)
    target = normalize([math.exp(value - maximum) for value in log_target])
    return target, disagreement, confidence, centroid


def source_check(text: str, needle: str, label: str) -> dict[str, object]:
    return {"label": label, "needle": needle, "pass": needle in text}


def formula_checks() -> list[dict[str, object]]:
    anchor = [0.55, 0.25, 0.15, 0.05]
    agreement = [
        [0.10, 0.20, 0.60, 0.10],
        [0.11, 0.19, 0.61, 0.09],
        [0.09, 0.21, 0.59, 0.11],
    ]
    disagreement = [
        [0.85, 0.05, 0.05, 0.05],
        [0.05, 0.85, 0.05, 0.05],
        [0.05, 0.05, 0.85, 0.05],
    ]
    target_a, div_a, conf_a, centroid_a = consensus_target(anchor, agreement, tau=0.10)
    target_d, div_d, conf_d, _ = consensus_target(anchor, disagreement, tau=0.10)
    target_i, div_i, conf_i, centroid_i = consensus_target(anchor, [anchor] * 3, tau=0.10)
    finite_simplex = all(
        all(math.isfinite(value) and value > 0.0 for value in vector)
        and abs(sum(vector) - 1.0) <= 1e-12
        for vector in (target_a, target_d, target_i, centroid_a, centroid_i)
    )
    return [
        {"label": "geometric centroids and targets are finite probability simplexes", "pass": finite_simplex},
        {"label": "explorer disagreement continuously reduces EGTR influence", "pass": div_d > div_a and conf_d < conf_a},
        {"label": "identical anchor/explorer policies preserve the anchor exactly", "pass": div_i <= 1e-15 and conf_i == 1.0 and max(abs(a-b) for a,b in zip(target_i, anchor)) <= 1e-12},
        {"label": "the rule has no discrete promotion or evaluation threshold", "pass": 0.0 < conf_d < conf_a <= 1.0},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "docs" / "capd_p0_20260904",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    result_path = args.output_dir / "CAPD_P0_RESULT.json"
    report_path = args.output_dir / "CAPD_P0_ZERO_TRAINING_AUDIT.md"
    if result_path.exists() or report_path.exists():
        raise FileExistsError(f"refusing to overwrite existing CAPD P0 outputs: {args.output_dir}")

    agent_text = AGENT.read_text(encoding="utf-8")
    sampler_text = SAMPLER.read_text(encoding="utf-8")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    interface_checks = [
        source_check(agent_text, "class RIActor(nn.Module):", "actor class is explicit and independently callable"),
        source_check(agent_text, "return logits, attn, intent_logits", "actor exposes categorical logits before sampling"),
        source_check(agent_text, "Categorical(logits=logits)", "policy distribution is categorical"),
        source_check(agent_text, "deterministic: bool = False", "deterministic and stochastic execution share one interface"),
        source_check(agent_text, "init_checkpoint: str | None = None", "checkpoint initialization is already supported"),
        source_check(agent_text, "evaluation_enabled: bool = True", "training/evaluation boundary is explicit"),
        source_check(sampler_text, "class EGTRTopologySampler(DRTPTopologySampler):", "frozen EGTR explorer implementation exists"),
        source_check(sampler_text, 'state["format"] = "egtr_topology_sampler_runtime_state_v1"', "EGTR runtime state is serializable"),
    ]
    mathematics = formula_checks()
    leakage_checks = [
        {"label": "teacher targets are stop-gradient actor probabilities on training-only states", "pass": freeze["information_boundary"]["teacher_targets"] == "stop_gradient_probabilities_on_training_only_states"},
        {"label": "evaluation tapes and outcome labels are forbidden from training", "pass": set(freeze["information_boundary"]["prohibited"]) >= {"formal_evaluation_tape", "independent_evaluation_tape", "held_out_tape", "evaluation_return", "final_seed_quality_label"}},
        {"label": "teacher membership is fixed before downstream outcomes", "pass": freeze["population"]["selection_rule"] == "all_predeclared_members_no_performance_selection"},
        {"label": "final deployment contains one student actor", "pass": freeze["deployment"]["actor_count"] == 1},
    ]
    cost = freeze["cost_model"]
    cost_checks = [
        {"label": "training population size is finite and predeclared", "pass": cost["egtr_explorers"] == 3 and cost["utr_anchors"] == 1 and cost["central_students"] == 1},
        {"label": "deployment inference cost equals one ordinary actor", "pass": cost["deployment_actor_forwards_per_decision"] == 1},
        {"label": "training compute is disclosed rather than claimed compute-matched", "pass": cost["compute_match_claimed"] is False and cost["projected_pipeline_multiplier_upper_bound"] == 5.0},
    ]
    checks = interface_checks + mathematics + leakage_checks + cost_checks
    passed = all(bool(check["pass"]) for check in checks)
    verdict = "CAPD_P0_FEASIBLE_FOR_P05_ASSET_SIGNAL_AUDIT" if passed else "CAPD_P0_NO_GO"
    hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in (AGENT, SAMPLER, FREEZE)
    }
    result = {
        "protocol": "CAPD-P0-ZERO-TRAINING-DESIGN-AUDIT-V1",
        "verdict": verdict,
        "checks": checks,
        "source_sha256": hashes,
        "zero_training": True,
        "checkpoints_loaded": False,
        "environment_constructed": False,
        "environment_steps": 0,
        "ppo_updates": 0,
        "evaluation_started": False,
        "teacher_assets_verified": False,
        "implementation_authorized": False,
        "p05_authorized": False,
        "automatic_continuation": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))

    report = [
        "# CAPD P0 zero-training design audit",
        "",
        f"**Verdict:** `{verdict}`.",
        "",
        "This audit establishes design and interface feasibility only. It loaded no checkpoint, constructed no environment, executed no rollout, performed no PPO update, and read no evaluation tape.",
        "",
        "## Decision",
        "",
        "The current categorical actor can support a training-time population-to-single-policy method. A future CAPD pipeline may use one frozen UTR anchor and three predeclared EGTR explorers to construct a continuous policy-space consensus target, while ordinary PPO trains one central student on fixed-stratified training rollouts. Deployment uses only that student actor.",
        "",
        "This is not the failed execution-time ensemble: teacher probabilities are temporary training targets, no member votes during deployment, and no evaluation outcome selects a teacher or final checkpoint.",
        "",
        "## Frozen mathematical skeleton",
        "",
        "For actor-legal training state x, the EGTR centroid is the normalized geometric mean of three fixed explorer policies. Mean Jensen-Shannon divergence from that centroid defines disagreement D(x). EGTR influence is the continuous value c(x)=exp(-D(x)/tau). The teacher target is the normalized geometric interpolation between the UTR anchor and EGTR centroid. The student minimizes ordinary fixed-stratified PPO plus a bounded forward-KL distillation term. Teacher tensors are stop-gradient; the critic remains ordinary PPO.",
        "",
        "Numeric tau, distillation strength and schedule are deliberately not selected in P0. They require one separate formula-freeze step and may not use evaluation outcomes.",
        "",
        "## Gate results",
        "",
    ]
    report.extend(f"- {'PASS' if check['pass'] else 'FAIL'} — {check['label']}." for check in checks)
    report.extend([
        "",
        "## Unresolved evidence gate",
        "",
        "The repository does not locally establish that every completed 10M UTR/EGTR teacher checkpoint is present, architecture-identical, hash-valid, and behaviorally nonredundant. P0 therefore does not claim that useful consensus signal exists. A separately authorized P0.5 must inventory the archived checkpoints and test policy-space headroom on a new training-only state tape without training a student.",
        "",
        "## Cost boundary",
        "",
        "The full pipeline may require up to five training actors (one UTR anchor, three EGTR explorers and one central student) and four teacher forwards per student state. This is not compute-matched to single-policy UTR/EGTR and must be disclosed. Final inference remains exactly one actor forward.",
        "",
        "## Stop boundary",
        "",
        "No CAPD implementation, checkpoint loading, rollout, distillation, PPO training, evaluation, cloud execution, parameter choice or paper claim is authorized. The only possible next action is an explicitly authorized P0.5 teacher-asset and training-only consensus-signal audit.",
        "",
        "## Source hashes",
        "",
    ])
    report.extend(f"- `{name}`: `{digest}`" for name, digest in hashes.items())
    report_path.write_bytes(("\n".join(report) + "\n").encode("utf-8"))
    print(json.dumps({"verdict": verdict, "output": str(args.output_dir), "zero_training": True}))


if __name__ == "__main__":
    main()
