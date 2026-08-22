"""Write the maintained G0 evidence reports from machine-readable outputs."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


PRIMARY = [
    "U1_scout_node_failure",
    "U2_static_symmetric_direct_prune",
    "U3_static_directed_scout_to_attacker_prune",
    "U4_scout_failure_symmetric_direct_prune",
    "U5_relay_failure_directed_direct_prune",
]
PARAMETER = ["parameter_timing_20_80", "parameter_duration_44_140"]
LABEL = {
    "reference_nominal": "reference nominal",
    "seen_f0_44_80": "seen F0 (44,80)",
    "parameter_timing_20_80": "parameter timing (20,80)",
    "parameter_duration_44_140": "parameter duration (44,140)",
    "U1_scout_node_failure": "U1 scout node failure",
    "U2_static_symmetric_direct_prune": "U2 symmetric direct-link prune",
    "U3_static_directed_scout_to_attacker_prune": "U3 directed Scout→Attacker prune",
    "U4_scout_failure_symmetric_direct_prune": "U4 scout failure + symmetric prune",
    "U5_relay_failure_directed_direct_prune": "U5 relay failure + directed prune",
    "U6_relay_failure_symmetric_direct_prune": "U6 relay failure + symmetric prune (diagnostic)",
}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: str) -> float:
    return float(value)


def table(rows: list[dict[str, str]], columns: list[tuple[str, str]], digits: int = 3) -> str:
    lines = ["| " + " | ".join(label for _, label in columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if key in {"seed", "training_seed", "training_seeds", "episodes"}:
                try:
                    value = str(int(float(value)))
                except (TypeError, ValueError):
                    pass
                values.append(str(value))
                continue
            try:
                value = f"{float(value):.{digits}f}"
            except (TypeError, ValueError):
                pass
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def method_rows(topology: list[dict[str, str]], method: str) -> list[dict[str, str]]:
    return [row for row in topology if row["method"] == method]


def generate(artifacts: Path, docs: Path) -> None:
    manifest = json.loads((artifacts / "topology_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((artifacts / "generalization_summary.json").read_text(encoding="utf-8"))
    topology = read(artifacts / "topology_results.csv")
    seed = read(artifacts / "seed_topology_results.csv")
    utr = method_rows(topology, "UTR-SG-MAPPO")
    drtp = method_rows(topology, "DRTP-SG-MAPPO")
    conditions = [item["id"] for item in manifest["evaluation_conditions"]]

    core_cols = [("condition", "condition"), ("family", "family"), ("training_seeds", "seeds"), ("J", "J"), ("J_seed_sd", "seed SD"), ("collision", "collision"), ("timeout", "timeout"), ("constraint_violation", "constraint")]
    write(docs / "G0_ZERO_SHOT_RESULTS.md", f"""# G0 zero-shot results

## Status

This is a frozen-policy, development-only evaluation. No optimizer, rollout update, checkpoint promotion, or training step was executed. The raw evidence contains {summary['raw_records']} episode records, aggregated into {summary['seed_condition_records']} method×training-seed×condition records and {summary['topology_records']} method×condition summaries.

The primary method is UTR-SG-MAPPO with the five clean T1 development seeds. Historical DRTP checkpoints are reported separately by contract and are not pooled into the primary decision.

## UTR-SG-MAPPO

{table(utr, core_cols)}

## DRTP-SG-MAPPO (descriptive, contract-separated)

{table(drtp, core_cols)}

## Risk-set validity and safety diagnostics

For every failure condition, the report retains all episodes in unconditional return and safety metrics. Trigger validity is reported among episodes alive at the scheduled onset. Pre-trigger termination is a policy outcome, not an evaluator failure. The machine-readable seed table contains `failure_exposure_all_episodes`, `survival_to_onset_fraction`, `trigger_success_among_risk_set`, and `pre_trigger_collision` for every cell.

## Provenance

- Topology manifest: `artifacts/g0/topology_manifest.json`
- Episode-level evidence: `artifacts/g0/g0_episode_results.csv`
- Seed-level evidence: `artifacts/g0/seed_topology_results.csv`
- Pooled condition evidence: `artifacts/g0/topology_results.csv`
- Summary: `artifacts/g0/generalization_summary.json`
- Figures: `artifacts/g0/figures/`
""")

    utr_stats = summary["utr_seed_statistics"]
    stats_cols = [("seed", "seed"), ("J_seen_F0", "J seen F0"), ("J_structural_primary_mean", "J structural mean"), ("J_parameter_mean", "J parameter mean"), ("structural_gap", "structural gap"), ("parameter_gap", "parameter gap"), ("structural_minus_parameter_gap", "structural−parameter")]
    write(docs / "G0_STRUCTURAL_VS_PARAMETER_OOD.md", f"""# G0 structural versus parameter OOD

## Frozen comparison

Parameter OOD changes failure timing or duration within the previously exposed Relay-1 failure family. Structural OOD changes failed node, communication-edge availability, directionality, or their composition. The comparison was defined before evaluation and uses the same deterministic episode namespace and policy checkpoints.

## UTR seed-level gaps

{table(utr_stats, stats_cols)}

The structural gap is `J_seen_F0 − mean(J_U1…J_U5)`. The parameter gap is `J_seen_F0 − mean(J_timing,J_duration)`. A positive structural-minus-parameter value means structural OOD is more damaging for that seed under the frozen definition.

## Decision rule application

- Median structural gap: `{summary['median_structural_gap']:.6f}`
- Median structural-minus-parameter gap: `{summary['median_structural_minus_parameter_gap']:.6f}`
- Positive seed differences: `{summary['seed_positive_structural_minus_parameter_gap']}/5`
- Primary topology cells above A threshold: `{summary['primary_topology_count_above_A_threshold']}/5`
- A pooled threshold: `{summary['pooled_A_threshold']:.6f}`
- Pre-registered outcome: **{summary['decision']}**

No threshold was selected after looking at performance. U6 is excluded from the primary mean because the frozen feasibility audit marked it diagnostic-only.
""")

    write(docs / "G0_GENERALIZATION_GAP_ANALYSIS.md", f"""# G0 generalization-gap analysis

## Main result

The frozen G0 outcome is **{summary['decision']}**. The inference unit is the training seed, not pooled episodes. Structural topology conditions U1–U5 are evaluated as a family, while U6 remains a physically-infeasible diagnostic condition and cannot create a primary generalization claim.

## What is and is not supported

- Supported: the observed relationship between frozen policy performance and the pre-registered topology suite.
- Not supported: communication blackout, Relay-unique information mediation, recovery, or causal claims that require information loss.
- Not supported: generalization to arbitrary graph sizes, arbitrary graph distributions, or unseen agent counts; the suite is fixed-size and task-specific.

## Seed-level evidence

{table(utr_stats, stats_cols)}

The seed table and condition table must be used for any later manuscript table. Means across episodes are descriptive within each frozen policy/condition cell; the five training seeds remain the independent units for the generalization decision.

## Historical DRTP boundary

DRTP checkpoints are shown as contract-separated descriptive evidence. They are not pooled with UTR and cannot alter the UTR pre-registered A/B/C decision. Historical DRTP failures and contracts remain unchanged.
""")

    write(docs / "G0_PRIOR_ART_AND_REVIEWER_ATTACK.md", """# G0 prior-art and reviewer-attack review

## Focused literature position

| Work | Relevant lesson | Boundary for G0 |
|---|---|---|
| Agarwal, Kumar and Sycara, *Learning Transferable Cooperative Behavior in Multi-Agent Teams* (2019) | Transferable cooperative behavior requires an explicit transfer/generalization question rather than a single in-distribution score. | G0 defines a frozen structural topology family and reports seed-level transfer evidence, but does not claim universal transfer. |
| Weil et al., *Towards Generalizability of Multi-Agent Reinforcement Learning in Graphs with Recurrent Message Passing* (2024) | Graph-structured MARL generalization is sensitive to graph structure and message-passing design. | G0 tests topology structure changes without changing the actor or adding recurrence. |
| Anil et al., *MOHITO* (UAI 2025) | Hypergraph/task-open formulations make relational structure explicit for changing multi-agent systems. | G0 is a fixed-size communication/task benchmark and does not claim task-open or variable-size generalization. |
| Li et al., *Disentangled Graph Self-supervised Learning for OOD Generalization* (ICML 2024) | OOD graph generalization requires careful separation of structural and nuisance shifts. | G0 separates timing/duration parameter OOD from structural topology OOD and does not infer mechanism from return alone. |

## Reviewer attacks and responses

1. **“The suite is just another failure-timing sweep.”** Response: timing/duration are explicitly the parameter-OOD comparator; U1–U5 alter node/edge structure or directionality.
2. **“U6 is an impossible graph.”** Response: U6 is retained only as diagnostic-only and is excluded from primary inference by the frozen feasibility audit.
3. **“You pooled episodes as repetitions.”** Response: the decision unit is training seed; pooled episodes are used only to estimate within-cell policy performance.
4. **“The actor saw the topology label.”** Response: topology modes configure the environment only; no topology descriptor or global route label is supplied to the actor. Actor-boundary and graph-legality checks are part of the audit.
5. **“This proves arbitrary topology generalization.”** Response: it does not. The claim is limited to the fixed-size, legal, pre-registered U1–U5 family.
6. **“The Relay is a unique information mediator.”** Response: that claim is explicitly outside the evidence boundary; direct legal paths and path reconfiguration are retained.

## Sources

- https://arxiv.org/abs/1906.09347
- https://arxiv.org/abs/2402.05027
- https://proceedings.mlr.press/v286/anil25a.html
- https://proceedings.mlr.press/v235/li24br.html
""")

    write(docs / "G0_FINAL_DECISION.md", f"""# G0 final decision

## Decision

**{summary['decision']}**

## Evidence boundary

G0 is a zero-shot, frozen-policy, development-only validation. It used the frozen topology manifest and existing checkpoints only. No training, optimizer step, checkpoint promotion, held-out seed, or canonical seed was used.

The exact primary decision was computed from UTR-SG-MAPPO's five T1 clean development seeds using the pre-registered structural-versus-parameter gap rules. Historical DRTP checkpoints remain separate descriptive evidence and do not change the primary decision.

## Interpretation

The decision is not a claim of universal graph generalization. It is a bounded statement about whether the fixed-size legal U1–U5 topology family produces an actionable zero-shot gap relative to the seen Relay-failure family and its timing/duration comparator.

## Required stopping rule

The G0 phase stops here. No DRTP-v2, new encoder, new loss, canonical seed, held-out experiment, or additional training is authorized by this report. Any next phase requires a separately frozen contract.

## Audit assets

- `docs/G0_TRAIN_TOPOLOGY_EXPOSURE_MANIFEST.md`
- `docs/G0_FROZEN_UNSEEN_TOPOLOGY_SUITE.md`
- `docs/G0_TOPOLOGY_LEGALITY_AND_FEASIBILITY_AUDIT.md`
- `docs/G0_ZERO_SHOT_RESULTS.md`
- `docs/G0_STRUCTURAL_VS_PARAMETER_OOD.md`
- `docs/G0_GENERALIZATION_GAP_ANALYSIS.md`
- `docs/G0_PRIOR_ART_AND_REVIEWER_ATTACK.md`
- `artifacts/g0/generalization_summary.json`
""")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/g0"))
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    args = parser.parse_args()
    generate(args.artifacts.resolve(), args.docs.resolve())
    print("wrote G0 reports")


if __name__ == "__main__":
    main()
