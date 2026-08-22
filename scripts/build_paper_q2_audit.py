from __future__ import annotations

import json
from pathlib import Path
from datetime import date


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ART = ROOT / "artifacts" / "paper_q2"


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    generated = str(date.today())
    drtp_metrics = {
        "J_nominal": {"wins": 4, "mean_delta": 46.231, "median_delta": 40.794, "worst_delta": -16.254, "sd": 63.390},
        "J_F0": {"wins": 3, "mean_delta": 26.404, "median_delta": 29.804, "worst_delta": -113.951, "sd": 99.467},
        "J_OOD_mean": {"wins": 3, "mean_delta": 34.218, "median_delta": 26.305, "worst_delta": -88.126, "sd": 88.629},
        "J_OOD_worst": {"wins": 4, "mean_delta": 31.479, "median_delta": 23.688, "worst_delta": -97.100, "sd": 87.658},
    }
    drtp_seed_deltas = [
        {"seed": 1901, "contract": "development_3M", "J_nominal": 40.794, "J_F0": 133.589, "J_OOD_mean": 131.498, "J_OOD_worst": 130.631},
        {"seed": 1902, "contract": "development_3M", "J_nominal": 6.908, "J_F0": -21.687, "J_OOD_mean": -5.785, "J_OOD_worst": 7.552},
        {"seed": 2001, "contract": "heldout_10M", "J_nominal": 149.059, "J_F0": 104.265, "J_OOD_mean": 107.200, "J_OOD_worst": 92.626},
        {"seed": 2002, "contract": "heldout_10M", "J_nominal": -16.254, "J_F0": -113.951, "J_OOD_mean": -88.126, "J_OOD_worst": -97.100},
        {"seed": 2003, "contract": "heldout_10M", "J_nominal": 50.650, "J_F0": 29.804, "J_OOD_mean": 26.305, "J_OOD_worst": 23.688},
    ]
    t1_rows = [
        {"seed": 2201, "J_nominal": 84.409, "J_F0": 60.938, "J_OOD_mean": 61.909, "J_OOD_worst": 53.845, "collision": 0.000, "timeout": 1.000},
        {"seed": 2202, "J_nominal": 188.756, "J_F0": 165.788, "J_OOD_mean": 164.521, "J_OOD_worst": 152.470, "collision": 0.061, "timeout": 0.666},
        {"seed": 2203, "J_nominal": 98.946, "J_F0": 57.777, "J_OOD_mean": 58.979, "J_OOD_worst": 49.154, "collision": 0.083, "timeout": 0.917},
        {"seed": 2204, "J_nominal": 121.801, "J_F0": 116.938, "J_OOD_mean": 116.834, "J_OOD_worst": 109.139, "collision": 0.021, "timeout": 0.973},
        {"seed": 2205, "J_nominal": 61.882, "J_F0": 44.521, "J_OOD_mean": 45.089, "J_OOD_worst": 38.109, "collision": 0.000, "timeout": 1.000},
    ]
    ledger = [
        {"asset": "S1/S1B/S2 problem and mechanism freeze", "classification": "MAIN_TEXT", "contract": "S2 frozen", "sources": ["docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md", "docs/PHASE_S2_FINAL_FREEZE_REPORT.md", "docs/PHASE_S2_CLAIM_EVIDENCE_BOUNDARY.md"], "status": "reusable", "notes": "Supports relay-node-induced topology/path reconfiguration; not information-loss or recovery."},
        {"asset": "T1 clean UTR five-seed reference", "classification": "MAIN_TEXT", "contract": "T1 1M, seeds 2201-2205", "sources": ["docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md", "docs/T1_SEED_LEVEL_REFERENCE_AND_RANKING.md", "results/development/t1_telemetry_native_reference_1m_run1"], "status": "reusable", "records": 5, "metrics": ["J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout", "exposure"], "notes": "Clean baseline reference; descriptive, not a universal superiority claim."},
        {"asset": "DRTP paired historical audit", "classification": "MAIN_TEXT", "contract": "development_3M + heldout_10M, separate contracts", "sources": ["docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md", "docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.json", "docs/DRTP_Q2R_ZERO_TRAINING_FAIR_REVIEW.md"], "status": "reusable_with_boundary", "records": 5, "metrics": list(drtp_metrics), "notes": "Report development and held-out sets separately; never pool them as one homogeneous experiment."},
        {"asset": "DRTP held-out final evidence", "classification": "MAIN_TEXT", "contract": "v2 held-out 10M, seeds 2001-2003", "sources": ["docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md", "docs/DRTP_HELDOUT_FAILURE_FORENSIC_REVIEW.md"], "status": "reusable_with_negative_result", "records": 6, "metrics": ["J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout", "constraint", "exposure"], "notes": "Must retain seed2002 reversal and overall held-out FAIL."},
        {"asset": "FL failure learnability upper bound", "classification": "SUPPLEMENTARY", "contract": "FL maturity 1M, seeds 1801-1802", "sources": ["docs/PHASE_FL_TRAINING_MATURITY_UPPER_BOUND_REPORT.md"], "status": "reusable_for_limitation", "records": 4, "notes": "Shows F0 can be learned by a specialist; not a main method comparison."},
        {"asset": "G0 unseen topology generalization audit", "classification": "SUPPLEMENTARY", "contract": "zero-training diagnostic", "sources": ["docs/G0_FINAL_DECISION.md", "docs/G0_ZERO_SHOT_RESULTS.md", "docs/G0_GENERALIZATION_GAP_ANALYSIS.md"], "status": "reusable_for_limitation", "records": 0, "notes": "Decision C; do not claim a universal topology-generalization gap."},
        {"asset": "TC-SAM / EDR / TCR / SPC / CTP negative evidence", "classification": "SUPPLEMENTARY", "contract": "historical development contracts", "sources": ["docs/TC_SAM_D1_FINAL_DECISION.md", "docs/EDR_D1_FINAL_DECISION.md", "docs/TCR_SPC_PHASE_C_V2_REANALYSIS_REPORT.md", "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md"], "status": "reusable_as_negative_evidence", "notes": "Do not use to inflate method count or imply a selective benchmark."},
        {"asset": "Old EA-RG / multi-relation paper draft", "classification": "INVALID_NON_COMPARABLE", "contract": "legacy recovery paper", "sources": ["paper_latex_3d_en/main.tex", "paper_latex_3d_en/README.md", "docs/PAPER_CODE_EQUIVALENCE_AUDIT_V3.md"], "status": "do_not_reuse_claims", "notes": "Claims recovery, old Full, and old metrics incompatible with frozen DRTP problem/claim boundary."},
        {"asset": "Gate1 safety/fx60 paper tables", "classification": "INVALID_NON_COMPARABLE", "contract": "legacy recovery/fx60 table contract", "sources": ["results/gate1_safety_fx60_paper_tables/main_results.csv", "results/gate1_safety_fx60_paper_tables/ablation_results.csv", "results/gate1_safety_fx60_paper_tables/capacity_control_results.csv", "results/gate1_safety_fx60_paper_tables/seed_aware_deltas.csv"], "status": "do_not_mix", "notes": "Uses recovery/chain metrics and old method labels; not commensurate with T1/DRTP frozen estimands."},
        {"asset": "Old M0 TC-SAM positioning/feasibility", "classification": "INTERNAL_ONLY", "contract": "superseded", "sources": ["docs/M0_Q2_PAPER_POSITIONING.md", "docs/M0_OFFLINE_FEASIBILITY.md"], "status": "historical_only", "notes": "Superseded by DRTP positioning and should not be cited as current method definition."},
    ]
    for row in ledger:
        row["source_exists"] = all(exists(s) for s in row["sources"])

    asset_ledger = {
        "schema": "paper-q2-asset-ledger-v1",
        "generated": generated,
        "training_started_by_this_audit": False,
        "frozen_mainline": "relay failure -> legal communication topology/path reconfiguration -> mission degradation -> topology-robust MARL",
        "graph_convention": "A[receiver,sender]",
        "rows": ledger,
        "drtp_seed_level_deltas": drtp_seed_deltas,
        "t1_reference_rows": t1_rows,
        "historical_decisions_preserved": ["DRTP_Q2_LIMITATION_ONLY", "DRTP_HELDOUT_FAIL", "TC_SAM_DEV_FAIL", "EDR_DEV_FAIL", "G0_NO_ACTIONABLE_TOPOLOGY_GENERALIZATION_GAP"],
    }

    gap = {
        "schema": "paper-q2-experiment-gap-v1",
        "generated": generated,
        "new_training_authorized": False,
        "items": [
            {"id": "M0", "priority": "MUST_HAVE", "item": "Claim/provenance alignment", "status": "COMPLETE_ZERO_TRAINING", "need": "Replace legacy recovery framing and keep development/held-out contracts separate."},
            {"id": "M1", "priority": "MUST_HAVE", "item": "Seed-level statistics", "status": "COMPLETE_ZERO_TRAINING", "need": "Report all paired seeds, mean, median, IQR/MAD, worst delta, and contract-stratified summaries."},
            {"id": "M2", "priority": "MUST_HAVE", "item": "OOD and safety decomposition", "status": "COMPLETE_AUDIT; PRESENTATION_REQUIRED", "need": "Show F0, timing, duration, compound, worst condition, timeout, collision, constraints, exposure."},
            {"id": "M3", "priority": "MUST_HAVE", "item": "One strong external comparator", "status": "OPEN; NO TRAINING AUTHORIZED", "need": "Assess whether a directly relevant robust/topology-aware MARL comparator can be implemented under a separately frozen contract; do not substitute an incomparable legacy table."},
            {"id": "M4", "priority": "HIGH_VALUE", "item": "Ablation of DRTP components", "status": "OPEN; NO TRAINING AUTHORIZED", "need": "Uniform topology training, nominal anchor, and adaptive weighting ablations only if a new contract is separately authorized."},
            {"id": "M5", "priority": "HIGH_VALUE", "item": "Scalability", "status": "OPEN; NO TRAINING AUTHORIZED", "need": "4/5-UAV or a defensible scope limitation; use only fair matched protocols."},
            {"id": "M6", "priority": "MUST_HAVE", "item": "Compute and reproducibility", "status": "COMPLETE_ZERO_TRAINING", "need": "Report parameter count, training budget, wall-clock provenance where available, inference path, tape hashes, and checkpoint provenance."},
            {"id": "D0", "priority": "DO_NOT_DO", "item": "New algorithm search/rescue", "status": "CLOSED", "need": "No DRTP-v2, SAM-v2, EDR-v2, new encoder, loss, or curriculum."},
            {"id": "D1", "priority": "DO_NOT_DO", "item": "Post-hoc seed/checkpoint selection", "status": "PROHIBITED", "need": "Retain seed1902 development limitation and held-out seed2002 reversal."},
            {"id": "D2", "priority": "DO_NOT_DO", "item": "Universal topology generalization claim", "status": "CLOSED_BY_G0", "need": "Do not reopen G0 without a new scientific gap and authorization."},
        ],
    }

    manifest = {
        "schema": "paper-q2-main-result-manifest-v1",
        "generated": generated,
        "training_started": False,
        "main_claim": "DRTP substantially improves average and median robustness across relay-failure topology perturbations, while remaining seed-sensitive.",
        "main_assets": [
            {"id": "problem_mechanism", "sources": ["docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md", "docs/PHASE_S2_FINAL_FREEZE_REPORT.md"], "role": "problem_and_mechanism"},
            {"id": "t1_utr_reference", "sources": ["docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md", "docs/T1_SEED_LEVEL_REFERENCE_AND_RANKING.md"], "role": "clean_reference"},
            {"id": "drtp_development", "sources": ["docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md"], "role": "development_performance_with_limitation"},
            {"id": "drtp_heldout", "sources": ["docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md"], "role": "heldout_reliability_and_failure"},
        ],
        "metric_hierarchy": {"primary": ["J_F0", "J_OOD_mean", "J_OOD_worst", "timeout"], "secondary": ["J_nominal", "collision", "constraint_violation", "exposure", "path_switch", "task_support", "maneuver_cost"]},
        "contract_separation": ["T1_1M_2201_2205", "DRTP_development_3M_1901_1902", "DRTP_heldout_10M_2001_2003"],
        "forbidden_claims": ["stable_algorithm", "reliably superior", "information restoration", "Relay unique mediator", "strict recovery guarantee", "universal topology generalization"],
    }

    stats = f"""# PAPER-Q2 Statistical Analysis Plan

**Status:** frozen planning artifact; zero training. **Generated:** {generated}

## Statistical unit and contract separation

The independent unit is the **training seed**, not an episode and not a pooled row. Paired differences are computed only within the same seed and the same frozen contract. T1 UTR (seeds 2201–2205), DRTP development (1901–1902, 3M), and DRTP held-out (2001–2003, 10M) are reported as separate strata. A cross-stratum summary, if shown, is descriptive only and never an inferential claim.

## Metric hierarchy

Primary robustness outcomes: `J_F0`, `J_OOD_mean`, `J_OOD_worst`, and timeout rate. Secondary outcomes: `J_nominal`, collision rate, constraint violation, exposure/risk-set validity, path switching, task-support utilization, and maneuver/control burden.

For each method and contract report raw seed values, paired DRTP−UTR deltas, win count, mean, median, IQR or MAD, worst paired degradation, and dispersion. For n=5, use seed-level paired bootstrap only as a descriptive interval and label it as such; do not imply asymptotic population inference. For n=2 or n=3 strata, show all points and avoid formal significance claims.

## Required plots/tables

Show all seed points, not only pooled means. Use paired slope/dot plots for deltas, condition-wise distributions for OOD, and separate safety panels. Any interval must state whether it is seed bootstrap, episode bootstrap, or a descriptive spread; episode bootstrap cannot replace seed replication.

## Missing-data and invalidity policy

No post-hoc seed exclusion, checkpoint promotion, or censoring of pre-trigger terminations. Technical invalidity is reserved for documented crash, corruption, or protocol failure. Policy failures remain performance/safety outcomes. Historical `DRTP_Q2_LIMITATION_ONLY` and held-out FAIL are immutable.

## Interpretation boundary

Positive mean and median do not establish seed stability. A result can support “higher average/median robustness with non-negligible initialization sensitivity” only if the worst seed, held-out reversal, safety deltas, and contract separation are all visible.
"""

    figures = f"""# PAPER-Q2 Figure and Table Plan

**Status:** zero-training publication plan; generated {generated}.

## Main paper

1. **Figure 1 — Problem and legal topology reconfiguration.** Heterogeneous roles, receiver-row adjacency convention, relay failure, and legal path change. Do not draw an information blackout.
2. **Figure 2 — Failure mechanism timeline.** Before/after failure traces for active path composition, task-support source, path switching, cache age/availability, maneuver burden, and mission score. The intended chain is topology/path reorganization → coordination/task degradation.
3. **Figure 3 — Main paired performance.** T1 reference plus DRTP development and held-out strata, with `J_nominal`, `J_F0`, `J_OOD_mean`, and `J_OOD_worst`; keep budgets/tapes visibly separated.
4. **Figure 4 — Seed-level paired effects.** Five historical paired deltas, win count, median, IQR/MAD, and the negative seed2002 reversal. No mean-only bar chart.
5. **Figure 5 — OOD decomposition.** Timing, duration, and compound condition distributions and worst-condition identity; show per-seed values.
6. **Figure 6 — Safety and evaluation validity.** Timeout, collision, constraint violation, survival-to-onset, risk-set trigger validity, and pre-trigger collision. Overall metrics retain all episodes.
7. **Table 1 — Frozen task, information boundary, and evaluation contract.** Include graph convention, failure semantics, estimands, tapes, and prohibited claims.
8. **Table 2 — Method and compute comparison.** UTR/DRTP definitions, parameter count, training budgets, exposure groups, inference overhead, and provenance.
9. **Table 3 — Full seed-level results.** Every DRTP/UTR pair in each contract stratum, raw values and deltas.
10. **Table 4 — Reliability and limitation.** Retention gates, held-out FAIL, seed2002 reversal, and explicit claim boundary.

## Supplementary

Include raw per-condition tables, complete telemetry definitions, tape hashes, evaluator audit, FL specialist learnability result, G0 limitation result, negative candidate-method results, and code/config hashes. Legacy recovery tables remain archived but are not merged into the DRTP evidence chain.
"""

    outline = f"""# PAPER-Q2 Full Outline

**Working paper type:** algorithmic MARL research paper with a topology-robustness task and explicit reliability analysis. **Generated:** {generated}

## One-sentence argument

Relay-node failure need not remove all legal information; it can reorganize communication paths and task support, and DRTP can improve average and median performance across the resulting perturbation groups, but the evidence also exposes non-negligible seed sensitivity that must remain part of the conclusion.

## Sections

1. **Introduction:** topology perturbation is a structural coordination problem; distinguish it from blackout/recovery; state the reliability question.
2. **Related work:** robust MARL, topology-aware MARL, communication-aware UAV MARL, distributionally robust RL; position DRTP as an empirical topology-group weighting mechanism, not a new universal robust-RL theorem.
3. **Problem formulation:** heterogeneous roles, communication/task graph, receiver-row adjacency, legal relay failure, nominal/F0/OOD conditions, estimands and risk-set validity.
4. **Method:** seven topology groups, 50% nominal anchor, bounded adaptive weighting, update equations, implementation mapping, no extra encoder/reward/critic information.
5. **Experimental protocol:** T1 reference; DRTP development and held-out strata; seeds, budgets, tapes, checkpoint policy, safety and exposure accounting.
6. **Results:** absolute returns first; paired deltas and seed-level dispersion; OOD decomposition; safety; mechanism telemetry.
7. **Reliability and limitations:** development NO-GO, held-out FAIL, seed1902 and seed2002, why mean/median gains cannot be called stability.
8. **Discussion:** what topology-robust MARL evidence supports, what it does not; deployment implications and reproducibility.
9. **Conclusion:** bounded claim only.

## Required result order

Absolute `J_nominal/J_F0/J_OOD` and safety first; relative deltas second; mechanism interpretation third; reliability limitation immediately adjacent, not hidden in an appendix.
"""

    abstract = f"""# PAPER-Q2 Result-Free Abstract

Relay-node failures in heterogeneous multi-UAV missions can change the legal communication topology and task-support paths without producing a complete information blackout. This paper formulates that event as a topology-robust multi-agent coordination problem and evaluates mission degradation under nominal, canonical failure, and out-of-distribution timing, duration, and compound perturbations. We introduce DRTP-SG-MAPPO, which keeps a matched single-graph MAPPO backbone and a fixed nominal exposure anchor while adaptively reweights predefined topology-perturbation training groups within bounded limits. The evaluation is organized around paired nominal–failure outcomes, absolute mission performance, safety, risk-set failure-trigger validity, and seed-level reliability rather than pooled episodes alone. The study explicitly separates development and held-out contracts and reports both average/median robustness and adverse initialization outcomes. The resulting contribution is a reproducible account of topology-path reorganization and a bounded empirical test of adaptive perturbation weighting; it does not claim information restoration, a unique relay mediator, universal topology generalization, or seed-stable superiority.

**Status:** result-free scaffold; insert only contract-matched evidence after final table audit. **Generated:** {generated}.
"""

    claims = f"""# PAPER-Q2 Allowed and Prohibited Claims

**Generated:** {generated}. This document is a hard writing boundary.

## Allowed

- Relay failure induces legal communication-path/topology reorganization and measurable mission degradation in the frozen task.
- DRTP uses a matched single-graph backbone, a nominal exposure anchor, predefined topology perturbation groups, and bounded adaptive weighting.
- Across the historical paired audit, DRTP improves average and median robustness on several primary metrics while showing non-negligible initialization sensitivity.
- Seed-level reliability, safety, and held-out failure are part of the result, not anomalies to hide.
- The mechanism is topology/path reorganization and coordination/task-support degradation, not mandatory information loss.

## Prohibited

- “DRTP is stable,” “reliably superior,” “consistently outperforms,” or “robust for every seed.”
- “Relay is the necessary or unique information mediator.”
- “Failure causes information blackout/loss” or “DRTP restores lost information.”
- Strict recovery guarantee, universal topology generalization, or deployment guarantee.
- Pooling 3M development and 10M held-out results as one homogeneous experiment.
- Treating a ratio such as `J_OOD/J_F0` as an absolute-superiority hard gate.
- Hiding seed1902 development NO-GO, held-out seed2002 reversal, or safety reversals.
- Reusing old EA-RG recovery claims, old Gate1 tables, or legacy multi-relation figures as DRTP evidence.
"""

    reviewer = f"""# PAPER-Q2 Reviewer Attack Response Plan

**Generated:** {generated}. This is a response matrix, not a claim that the concerns are already solved.

| Likely reviewer attack | Evidence-based response | Remaining action |
|---|---|---|
| DRTP is seed-sensitive | Agree. Show all paired seeds, mean/median, worst delta, held-out seed2002 reversal, and use seed sensitivity as a limitation. | Keep raw table in main/supplement. |
| Held-out FAIL invalidates the method | It invalidates a stable-superiority claim, not the descriptive claim of higher average/median historical robustness. | Tone and title must remain bounded. |
| Gains may be absolute-scale or denominator artifacts | Report absolute returns before deltas; do not use self-reference ratios as hard gates; preserve worst seed. | Complete metric audit. |
| This is just more training exposure | UTR/DRTP share the seven topology groups and nominal anchor; identify this as an empirical adaptive weighting question. | Add comparator/ablation only under a new contract. |
| No strong external comparator | Acknowledge MAPPO/UTR are internal controls and old recovery tables are incomparable. | One directly relevant comparator is the main open Q2 gap. |
| Novelty is only reweighting | Position the contribution as a problem–method–reliability package, not a new robust-RL theorem. | Refresh related work and avoid “first” language. |
| Failure exposure is invalid | Report overall unconditional metrics plus survival-to-onset and trigger validity on the risk set. | Include evaluator audit in supplement. |
| Why not claim information loss? | Existing exposed episodes have legal Scout→Attacker direct paths; evidence supports path reorganization, not blackout. | Do not regress wording. |
| Why not use old paper results? | Old EA-RG recovery and Gate1 tables use different estimands/contracts and are marked non-comparable. | Keep them archived only. |

## Reviewer-safe sentence

“The evidence supports a high-average, seed-sensitive topology-robustness effect; it does not support a claim of uniformly reliable superiority.”
"""

    prior = f"""# PAPER-Q2 Prior-Art Refresh

**Generated:** {generated}. Focused refresh only; no new algorithm search or training authorization.

## Positioning map

1. **Robust MARL under policy/environment variation.** Robust MARL work has addressed continuous-action multi-agent robustness and adversarial or opponent-policy changes. This establishes that robustness in MARL is broader than communication topology failure, so the paper must state its event semantics precisely. Primary source: [Robust Multi-Agent Reinforcement Learning](https://aima.eecs.berkeley.edu/~russell/papers/aaai19-marl.pdf).
2. **Topology-aware coordination.** TAPE explicitly uses agent topology in cooperative policy-gradient learning. The present distinction is not “graphs are new”; it is relay-node-induced path reorganization in a heterogeneous UAV mission plus reliability-aware evaluation. Primary source: [TAPE: Leveraging Agent Topology for Cooperative Multi-Agent Policy Gradient](https://ojs.aaai.org/index.php/AAAI/article/view/29699).
3. **Distributionally robust RL.** Distributionally robust Q-learning and later DRRL theory optimize against distributional/environmental shifts. DRTP should be positioned as an empirical, bounded topology-group weighting mechanism, not as a general DRMDP solution or theoretical worst-case guarantee. Primary sources: [Distributionally Robust Q-Learning](https://proceedings.mlr.press/v162/liu22a.html) and [On the Foundation of Distributionally Robust Reinforcement Learning](https://arxiv.org/abs/2311.09018).
4. **UAV relay and communication MARL.** Recent UAV relay work uses MARL for connectivity, trajectory, power, or covert communication objectives. These motivate the application context but do not by themselves establish the specific relay-failure/path-reconfiguration estimand used here. Primary sources: [Fast connectivity restoration of UAV communication networks](https://doi.org/10.1016/j.adhoc.2025.103785) and [Multi-hop UAV relay covert communication](https://doi.org/10.1016/j.cja.2025.103440).

## Novelty boundary

Do not claim the first topology-aware MARL, first robust MARL, first DRRL, or first UAV relay MARL. The defensible contribution is the integrated problem formulation, legal topology/path mechanism audit, bounded adaptive weighting across predefined perturbation groups, and an unusually explicit seed-level reliability/safety evaluation.
"""

    readiness = f"""# PAPER-Q2 Final Readiness Decision

**Generated:** {generated}  
**Decision:** `B — CONDITIONAL_MANUSCRIPT_READY_WITH_EXPLICIT_SEED_SENSITIVITY`

## Why this is not A

The frozen evidence supports a coherent paper and a defensible bounded DRTP claim, but a normal Q2 submission still has open presentation/comparator gaps: a directly relevant external comparator is not yet in the current evidence chain, component ablations are not complete under the DRTP contract, and scalability is not established. These are future, separately authorized additions; no training is started by this audit.

## Why this is not C

The problem formulation, failure semantics, legal topology/path mechanism, paired estimands, T1 reference, DRTP development/held-out records, and seed-level limitation evidence are already sufficient for a serious manuscript backbone. The historical negative results do not erase the evidence; they bound the claim.

## Five title candidates

1. **Topology-Robust Heterogeneous Multi-UAV Coordination under Relay-Node-Induced Communication-Path Reconfiguration**
2. **Distributionally Robust Multi-UAV Coordination under Relay Failures and Communication-Path Reorganization**
3. **When Relay Failure Rewrites the Path: Seed-Sensitive Topology-Robust MARL for Heterogeneous UAV Teams**
4. **Adaptive Topology-Perturbation Training for Relay-Failure Robust Heterogeneous UAV Coordination**
5. **Average Robustness versus Seed Reliability in Heterogeneous UAV Coordination under Communication Topology Disruptions**

## Required next paper actions (not training authorization)

- Freeze the manuscript terminology and replace the legacy recovery draft with a new DRTP paper scaffold.
- Build tables/figures from the machine-readable manifest, preserving contract strata.
- Decide whether one external comparator and one compact ablation are worth a separately authorized experiment; otherwise state the limitation.
- Run a final claim/provenance audit before submission.

## Immutable historical boundaries

`DRTP_Q2_LIMITATION_ONLY`, development NO-GO, held-out FAIL, seed1902 limitation, and seed2002 reversal remain unchanged. No new training, held-out confirmation, canonical seeds, or algorithm search is authorized by PAPER-Q2-P0.
"""

    write("docs/PAPER_Q2_COMPLETE_ASSET_LEDGER.md", "# PAPER-Q2 Complete Asset Ledger\n\nGenerated machine-readable companion: `artifacts/paper_q2/asset_ledger.json`.\n\n## Classification rules\n\n- **MAIN_TEXT:** contract-matched and directly supports the frozen DRTP claim.\n- **SUPPLEMENTARY:** useful negative, mechanism, or audit evidence but not the headline result.\n- **INTERNAL_ONLY:** historical planning or superseded material.\n- **INVALID_NON_COMPARABLE:** not allowed in the current evidence chain because estimands/contracts differ.\n\n## Ledger\n\n" + "\n".join(f"### {r['asset']}\n- Classification: **{r['classification']}**\n- Contract: {r.get('contract', 'not stated')}\n- Status: {r['status']}\n- Sources: " + ", ".join(f"`{s}`" for s in r['sources']) + f"\n- Notes: {r['notes']}" for r in ledger) + "\n\n## Frozen historical decisions\n\nDRTP development `NO-GO`, DRTP held-out `FAIL`, TC-SAM `DEV_FAIL`, EDR `DEV_FAIL`, and G0 `NO_ACTIONABLE_TOPOLOGY_GENERALIZATION_GAP` are retained. No negative result is deleted or rewritten.\n")
    write("docs/PAPER_Q2_EXPERIMENT_GAP_AUDIT.md", "# PAPER-Q2 Experiment Gap Audit\n\nGenerated companion: `artifacts/paper_q2/experiment_gap.json`.\n\nNo training is authorized in this audit.\n\n" + "\n".join(f"## {x['id']} — {x['priority']} — {x['item']}\n- Status: **{x['status']}**\n- Requirement: {x['need']}" for x in gap['items']))
    write("docs/PAPER_Q2_STATISTICAL_ANALYSIS_PLAN.md", stats)
    write("docs/PAPER_Q2_FIGURE_TABLE_PLAN.md", figures)
    write("docs/PAPER_Q2_FULL_OUTLINE.md", outline)
    write("docs/PAPER_Q2_RESULT_FREE_ABSTRACT.md", abstract)
    write("docs/PAPER_Q2_ALLOWED_PROHIBITED_CLAIMS.md", claims)
    write("docs/PAPER_Q2_REVIEWER_ATTACK_RESPONSE.md", reviewer)
    write("docs/PAPER_Q2_PRIOR_ART_REFRESH.md", prior)
    write("docs/PAPER_Q2_FINAL_READINESS_DECISION.md", readiness)
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "asset_ledger.json").write_text(json.dumps(asset_ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ART / "experiment_gap.json").write_text(json.dumps(gap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ART / "main_result_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"generated": generated, "docs": 10, "ledger_rows": len(ledger), "training_started": False, "decision": "B"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
