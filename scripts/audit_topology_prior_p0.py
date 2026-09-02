"""Zero-training audit for a topology-informed prior plus micro-adaptation.

This program reads only a frozen, policy-free group specification.  It neither
imports the environment nor reads experiment outputs, checkpoints, evaluation
tapes, returns, or telemetry.  Its purpose is to make an underdetermination
visible rather than invent a structural prior from outcome data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


GROUP_ORDER = ("F0", "TE", "TL", "DS", "DL", "CP")
REFERENCES = [
    ("Jiang et al. (2021), Prioritized Level Replay", "https://proceedings.mlr.press/v139/jiang21b.html"),
    ("Narvekar et al. (2020), Curriculum Learning for Reinforcement Learning Domains", "https://www.jmlr.org/papers/v21/20-212.html"),
    ("Mehta et al. (2020), Active Domain Randomization", "https://arxiv.org/abs/2002.07911"),
    ("Rajeswaran et al. (2017), EPOpt", "https://arxiv.org/abs/1610.01283"),
    ("Schaul et al. (2016), Prioritized Experience Replay", "https://arxiv.org/abs/1511.05952"),
]


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    rule = "|" + "|".join([" --- " for _ in headers]) + "|"
    return "\n".join([line, rule, *["| " + " | ".join(row) + " |" for row in rows]])


def write(path: Path, text: str) -> None:
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/topology_prior_p0_audit_20260902.json")
    parser.add_argument("--output-dir", default="docs/topology_prior_p0_audit_20260902")
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    max_steps = int(cfg["max_steps"])
    groups = cfg["failure_groups"]
    means = {group: sum(member[2] for member in groups[group]) / len(groups[group]) for group in GROUP_ORDER}
    schedule_score = {group: means[group] / max_steps for group in GROUP_ORDER}
    raw_total = sum(means.values())
    diagnostic_q = {group: means[group] / raw_total for group in GROUP_ORDER}
    uniform = 1.0 / len(GROUP_ORDER)
    l1_to_uniform = sum(abs(diagnostic_q[group] - uniform) for group in GROUP_ORDER)
    floor = float(cfg["simplex_bounds"]["floor"])
    cap = float(cfg["simplex_bounds"]["cap"])
    radius = float(cfg["conditional_micro_l1_radius"])
    per_member = []
    for group in GROUP_ORDER:
        for condition, onset, duration in groups[group]:
            per_member.append({
                "group": group, "condition": condition, "onset": onset, "duration": duration,
                "scheduled_relay_unavailable_fraction": duration / max_steps,
                "static_role_graph_deletion": "identical_relay_node_deletion",
            })

    structural = {
        "max_steps": max_steps,
        "all_failure_groups_delete": "relay_agent_index_1",
        "static_role_graph_deletion_is_group_discriminative": False,
        "per_member": per_member,
        "group_schedule_score": schedule_score,
        "diagnostic_duration_normalized_q_not_accepted_as_p0": diagnostic_q,
        "diagnostic_hash": stable_hash({"schedule_score": schedule_score, "q": diagnostic_q}),
    }
    verdict = {
        "protocol": cfg["protocol"],
        "verdict": "P0_PRIOR_UNDERDETERMINED",
        "core_checks": {
            "policy_independent_schedule_score_computable": True,
            "deterministic_replay_of_schedule_score": True,
            "no_evaluation_or_policy_feedback_used": True,
            "static_topology_distinguishes_failure_groups": False,
            "policy_independent_recoverability_computable": False,
            "valid_topology_informed_fixed_prior_determined": False,
            "micro_adaptation_geometry_feasible_conditionally": True,
            "four_arm_design_identifiable_conditionally": True,
            "novelty_claim_ready": False,
        },
        "p0_emitted": False,
        "p1_authorized": False,
        "training_authorized": False,
        "formal_evaluation_used": False,
        "historical_performance_used": False,
        "structural_audit_hash": stable_hash(structural),
    }
    write(out / "TOPOLOGY_PRIOR_P0_AUDIT.json", json.dumps({"verdict": verdict, "structural": structural}, indent=2))

    group_rows = [[g, ", ".join(m[0] for m in groups[g]), f"{means[g]:.1f}", f"{schedule_score[g]:.6f}", "identical"] for g in GROUP_ORDER]
    write(out / "TOPOLOGY_STRUCTURAL_SCORE_AUDIT.md", f"""# Topology structural-score audit

**Status:** policy-free schedule quantities are reproducible; a group-discriminative topology score is **not** established.

All six failure groups set `failed_blue_agent = 1`, i.e. delete the same Relay role. Removing that role from the static Scout–Relay–Attacker support graph removes the same role-compatible edges in every group. The only policy-independent quantity that differs in the frozen group contract is failure timing/duration.

{table(["Group", "Frozen members", "Mean duration", "Scheduled Relay-unavailable fraction" , "Static deletion"], group_rows)}

Actual communication reachability is state-dependent (inter-agent distance and stochastic communication dropout). Active support additionally depends on target information and local attack-window state. These quantities cannot be used as a fixed prior here: evaluating them would require a trajectory and hence policy/RNG-dependent rollout.

The hash of the policy-free schedule calculation is `{structural['diagnostic_hash']}`.
""")

    q_rows = [[g, f"{diagnostic_q[g]:.6f}", f"{floor:.2f}–{cap:.2f}", "yes" if floor <= diagnostic_q[g] <= cap else "no"] for g in GROUP_ORDER]
    write(out / "TOPOLOGY_PRIOR_FORMULATION.md", f"""# Fixed-prior formulation audit

Let `s_g = E[duration_g] / T`, with `T={max_steps}`. This is a deterministic **schedule-exposure** score, not a topology score. A diagnostic normalization would be `q_g = s_g / sum_h s_h`:

{table(["Group", "Diagnostic duration-normalized q", "Legacy bounds", "Within bounds"], q_rows)}

This vector is deliberately **not emitted as p0**. It treats longer relay outages as intrinsically more valuable to sample, but the contract supplies no policy-independent theorem or task-semantic rule that equates outage duration with recoverability, learning utility, or topology severity. A genuine topology-informed prior therefore remains underdetermined.
""")

    write(out / "PRIOR_SIMPLEX_AND_BOUNDS_AUDIT.md", f"""# Prior simplex and bounds audit

For diagnostic purposes only, the duration-normalized vector sums to `1.0`, has range `[{min(diagnostic_q.values()):.6f}, {max(diagnostic_q.values()):.6f}]`, and satisfies the legacy conditional-simplex bounds `[0.05, 0.35]`. Its L1 distance from uniform is `{l1_to_uniform:.6f}`.

A conditional L1 micro-adaptation radius of `{radius:.2f}` is geometrically feasible around that vector: it permits at most `{radius / 2:.2f}` total probability mass transfer and the bounded simplex is non-empty. This is only a geometry result. It does **not** validate the diagnostic vector as a scientific prior or select a training hyperparameter.
""")

    write(out / "MICRO_ADAPTATION_FORMULATION.md", f"""# Bounded micro-adaptation formulation (conditional only)

If a future audit supplies a valid fixed prior `p0`, a mathematically distinct residual sampler could be defined as

`q_t = Project_[floor, cap](p0 + r_t),  sum_g q_t[g]=1,  ||q_t-p0||_1 <= {radius:.2f}`.

`r_t` would be a bounded, training-only residual derived from completed training episodes; it must not read any evaluation tape. This document specifies no update rule, threshold, or training run. The current P0 verdict prevents implementation because `p0` has not been justified as topology-informed.
""")

    write(out / "S2_VS_PRIOR_ADAPTATION_AUDIT.md", """# S2 versus prior-plus-adaptation audit

S2 begins from an adaptive DRTP target, projects it, mixes it with a 0.20 uniform anchor, then applies a final L1 trust region. A valid prior-plus-micro method would instead anchor all residual motion to a **fixed, non-uniform, independently defined** `p0` and bound distance from `p0` directly.

The formulas would be distinguishable only if `p0` is genuinely structural. The present audit cannot establish that condition: the static relay-deletion topology is identical across all groups, while dynamic connectivity is trajectory-dependent. Therefore this is not yet a novelty claim and cannot be presented as an S2 replacement.
""")

    write(out / "NO_LEAKAGE_AUDIT.md", """# No-leakage audit

Allowed inputs in this P0 audit were the frozen group member schedule, role identities, maximum episode length, and source-code semantics. No environment was instantiated.

Forbidden and unused inputs: training/evaluation returns, formal or held-out tapes, checkpoints, trajectories, policy actions, dynamic communication adjacency, target-cache states, attack-window states, completed-episode difficulty, and historical method rankings.

Dynamic route redundancy and mission-support reachability are intentionally excluded because the environment computes them from geometry, dropout RNG, sensing/cache state, and policy-dependent trajectory state. Treating them as fixed topology would silently introduce a policy/rollout dependency.
""")

    refs = "\n".join(f"- [{name}]({url})" for name, url in REFERENCES)
    write(out / "NOVELTY_MAP.md", f"""# Novelty map

Nearest method families:

{refs}

Prioritized Level Replay and active/self-paced domain-randomization use learning- or policy-dependent signals to alter task distributions. Prioritized replay reweights stored transitions rather than frozen environment-condition exposure. The repository's existing SNR control is a static non-uniform reset sampler, but its weights are manually fixed and not derived from topology.

No exact match was identified in this targeted audit for a policy-independent topology prior plus an L1-bounded residual sampler in this relay-failure MARL interface. That absence is not enough for a novelty claim: the proposed `p0` itself is underdetermined. **Novelty status: unresolved / not claimable.**
""")

    write(out / "FOUR_ARM_CAUSAL_DESIGN.md", """# Four-arm causal design (not authorized)

Conditional on a future valid p0, the causal design would separate:

| Arm | Collection distribution | Adaptation | Purpose |
| --- | --- | --- | --- |
| A | UTR uniform | none | stable exposure baseline |
| B | fixed p0 | none | test H1: prior alone |
| C | Original DRTP | full adaptive | adaptive-sampling reference |
| D | fixed p0 | bounded residual only | test H2–H4: controlled adaptation |

H1 asks whether static structural exposure helps; H2 whether residual adaptation adds value beyond p0; H3 whether D reduces sampler-path variability relative to C; H4 whether the effect remains under fresh cohorts. No arm is authorized while p0 is undefined.
""")

    write(out / "STAGED_EXPERIMENT_PLAN.md", """# Staged experiment plan

This is a conditional plan only. P0 stops here.

1. Independently establish a group-discriminative, policy-free structural quantity (without using performance labels).
2. Freeze one p0 and an external comparator mapping before training.
3. Run an exact-interface technical audit: default-off equivalence, RNG isolation, save/resume, and no evaluation leakage.
4. Only then consider a small fresh-seed pilot; no sweep, no automatic continuation.

Because step 1 did not pass, steps 2–4 are **not authorized**.
""")

    write(out / "EXTERNAL_COMPARATOR_PLAN.md", """# External-comparator plan (conditional)

If a later formulation becomes valid, compare against: (1) uniform task sampling, (2) Original DRTP's learning-signal-driven sampler, and (3) one mapped curriculum/domain-randomization comparator whose task distribution can be fixed before outcomes. PLR is a conceptual adaptive-sampling comparator but cannot be claimed as directly implemented without a frozen mapping from its level scoring to this group interface. No external comparator is implemented or evaluated in P0.
""")

    write(out / "TOPOLOGY_PRIOR_P0_CONTRACT.md", """# Topology-Informed Prior + Bounded Micro-Adaptation: P0 contract

**Authorization:** zero-training scientific audit only.

No rollout, training, evaluation, seed change, parameter sweep, checkpoint promotion, or automatic P1 was performed. The requested objective was to determine whether a policy/training-independent topology-informed p0 can be objectively constructed in the existing relay-failure interface.

The audit must return feasibility only when static topology distinguishes group severity without using trajectory outcomes. It must otherwise stop rather than convert duration or historical returns into a post-hoc prior.
""")

    write(out / "P0_FINAL_VERDICT.md", f"""# P0 final verdict

`P0_PRIOR_UNDERDETERMINED`

The interface can implement a deterministic fixed sampler, and the bounded-simplex / `{radius:.2f}` micro-residual geometry is feasible. However, the requested topology-informed fixed prior cannot be scientifically determined under the frozen no-rollout information boundary:

1. every failure group deletes the same Relay node, so static role-topology deletion does not distinguish groups;
2. the remaining distinguishers are timing and duration, which are schedule variables rather than topology;
3. dynamic connectivity, route redundancy, recoverability, and active support require trajectory state and cannot become a policy-independent p0.

Consequently no p0, implementation, training, P1, or novelty claim is authorized. The correct action is to preserve this negative design audit and stop this line at P0.
""")

    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
