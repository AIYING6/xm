"""Build the zero-training PAPER-Q2 closeout package from frozen evidence.

This script deliberately reads the existing P1 evidence assets.  It does not
read checkpoints for performance selection, train policies, or alter results.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "artifacts" / "paper_q2_closeout"
P1 = ROOT / "artifacts" / "paper_q2_p1"
TODAY = date.today().isoformat()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    divider = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(str(item) for item in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def main() -> None:
    main_rows = read_csv(P1 / "main_table.csv")
    seed_rows = read_csv(P1 / "seed_level_results.csv")
    stats = json.loads((P1 / "statistical_summary.json").read_text(encoding="utf-8"))
    provenance = json.loads((P1 / "result_provenance.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    # Machine-readable final evidence assets.
    write_csv(OUT / "final_main_results.csv", list(main_rows[0]), main_rows)
    write_csv(OUT / "final_seed_level_results.csv", list(seed_rows[0]), seed_rows)
    reliability_rows = []
    for metric, entry in stats["primary_metrics"].items():
        reliability_rows.append({
            "metric": metric,
            "training_seed_unit": "5 historical paired seeds; descriptive cross-contract summary only",
            "wins": f"{entry['win_count']}/{entry['n']}",
            "mean_delta_drtp_minus_utr": entry["mean"],
            "median_delta_drtp_minus_utr": entry["median"],
            "std": entry["std"],
            "iqr": entry["IQR"],
            "mad": entry["MAD"],
            "worst_delta": entry["worst_delta"],
            "paired_dz_descriptive": entry["paired_dz"],
            "bootstrap_mean_ci_low_descriptive": entry["descriptive_seed_bootstrap_95_ci"][0],
            "bootstrap_mean_ci_high_descriptive": entry["descriptive_seed_bootstrap_95_ci"][1],
            "interpretation": "positive center does not establish seed stability",
        })
    write_csv(
        OUT / "final_reliability_results.csv",
        list(reliability_rows[0]),
        reliability_rows,
    )
    stratified_rows = []
    for contract, metrics in stats["contract_stratified"].items():
        for metric, entry in metrics.items():
            stratified_rows.append({
                "contract": contract,
                "metric": metric,
                "n_training_seeds": entry["n"],
                "wins": entry["win_count"],
                "mean_delta": entry["mean"],
                "median_delta": entry["median"],
                "std": entry["std"],
                "iqr": entry["IQR"],
                "mad": entry["MAD"],
                "worst_delta": entry["worst_delta"],
                "inference_boundary": "descriptive within frozen contract; no population-level claim",
            })
    write_csv(
        OUT / "final_stratified_statistics.csv",
        list(stratified_rows[0]),
        stratified_rows,
    )
    write_csv(
        OUT / "efficiency_results.csv",
        ["item", "UTR_SG", "DRTP_SG", "comparison_status", "source_or_boundary"],
        [
            {"item": "trainable parameters", "UTR_SG": "116,728", "DRTP_SG": "116,728", "comparison_status": "matched", "source_or_boundary": "frozen DRTP method contract"},
            {"item": "actor/critic backbone", "UTR_SG": "same Single-Graph MAPPO", "DRTP_SG": "same Single-Graph MAPPO", "comparison_status": "matched", "source_or_boundary": "frozen DRTP method contract"},
            {"item": "topology training groups", "UTR_SG": "same 7 groups + 50% nominal anchor", "DRTP_SG": "same 7 groups + 50% nominal anchor", "comparison_status": "matched", "source_or_boundary": "DRTP method contract"},
            {"item": "extra inference module", "UTR_SG": "none", "DRTP_SG": "none", "comparison_status": "matched at inference", "source_or_boundary": "adaptive weighting is training-only"},
            {"item": "checkpoint model bytes (P3 architecture check)", "UTR_SG": "479,288", "DRTP_SG": "479,288", "comparison_status": "equal architectural serialization example", "source_or_boundary": "results/development/drtp_s1r_p3/runs/*/actor_critic_latest.pt"},
            {"item": "wall-clock / peak GPU memory", "UTR_SG": "not available under a common hardware log", "DRTP_SG": "not available under a common hardware log", "comparison_status": "not claimed", "source_or_boundary": "no cross-hardware or incomplete-log comparison is permitted"},
        ],
    )
    comparator_rows = [
        {
            "method": "TAPE (AAAI 2024)",
            "nearest_relevance": "topology-aware cooperative MARL",
            "same_problem_estimand": "no",
            "same_actor_information_boundary": "no demonstrated drop-in mapping",
            "same_action_and_learner_contract": "no",
            "architecture_or_objective_change_required": "yes",
            "implementation_ready_under_frozen_contract": "not established",
            "scientifically_relevant": "yes, positioning only",
            "fair_drop_in": "no",
            "decision": "do not train",
            "source": "https://ojs.aaai.org/index.php/AAAI/article/view/29699",
        },
        {
            "method": "M3DDPG (AAAI 2019)",
            "nearest_relevance": "robust multi-agent learning under changing opponents",
            "same_problem_estimand": "no",
            "same_actor_information_boundary": "no demonstrated drop-in mapping",
            "same_action_and_learner_contract": "no; minimax DDPG differs from frozen MAPPO",
            "architecture_or_objective_change_required": "yes",
            "implementation_ready_under_frozen_contract": "not established",
            "scientifically_relevant": "yes, positioning only",
            "fair_drop_in": "no",
            "decision": "do not train",
            "source": "https://ojs.aaai.org/index.php/AAAI/article/view/4327",
        },
    ]
    write_csv(OUT / "external_comparator_matrix.csv", list(comparator_rows[0]), comparator_rows)
    claims = [
        ("C1", "Relay failure produces legal topology/path reconfiguration and mission degradation.", "S1B/S2 frozen topology validation", "Main Fig. 1–2; Table 1", "allowed"),
        ("C2", "UTR versus DRTP isolates adaptive group weighting at matched capacity and exposure.", "frozen DRTP contract; Table 2", "Main Table 2; ablation subsection", "allowed"),
        ("C3", "Historical paired DRTP gains have positive mean and median across primary returns.", "final_seed_level_results.csv; final_reliability_results.csv", "Main Fig. 3–5; Table 3", "descriptive only"),
        ("C4", "DRTP is seed-sensitive and has a reproducible catastrophic adverse seed.", "held-out seed2002; REL-A0", "Main Fig. 4, 6; Table 4", "mandatory limitation"),
        ("C5", "Safety is mixed rather than uniformly improved.", "main results; held-out audit", "Main Fig. 6; Table 4", "mandatory limitation"),
        ("C6", "All-episode outcomes and risk-set trigger validity are distinct estimands.", "Phase-C exposure audits", "Supplementary evaluator audit", "allowed"),
        ("C7", "No fair external drop-in comparator was identified under the frozen contract.", "external_comparator_matrix.csv", "Related work / limitation", "not a superiority claim"),
        ("C8", "The reported setting is a 3-UAV heterogeneous simulation.", "frozen environment contract", "Methods / limitations", "scope restriction"),
        ("C9", "DRTP is stable, universally robust, or consistently superior.", "no supporting evidence", "not permitted", "prohibited"),
    ]
    write_csv(
        OUT / "claim_evidence_matrix.csv",
        ["claim_id", "claim_or_boundary", "evidence", "paper_destination", "status"],
        [{"claim_id": row[0], "claim_or_boundary": row[1], "evidence": row[2], "paper_destination": row[3], "status": row[4]} for row in claims],
    )
    figure_rows = [
        ("Figure 1", "Problem/topology reconfiguration schematic", "docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md", "telemetry-grounded schematic; no invented data", "main"),
        ("Figure 2", "Topology/path to mission-degradation mechanism timeline", "docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md; S2 frozen reports", "telemetry-grounded sequence", "main"),
        ("Figure 3", "Stratified UTR/DRTP absolute returns", "final_main_results.csv", "keep 3M development and 10M held-out separate", "main"),
        ("Figure 4", "Five paired seed effects and adverse seed2002", "final_seed_level_results.csv; final_reliability_results.csv", "all points, no mean-only plot", "main"),
        ("Figure 5", "OOD decomposition", "docs/DRTP_REL_A0_FINAL_REPORT.md", "condition/tape source must remain labeled", "main"),
        ("Figure 6", "Safety and evaluation-validity outcomes", "final_main_results.csv; docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md", "retain all failures and strata", "main"),
        ("Table 1", "Frozen task and information boundary", "S2 contract / topology reports", "provenance table", "main"),
        ("Table 2", "Matched method/compute comparison", "efficiency_results.csv", "wall-clock comparability unavailable", "main"),
        ("Table 3", "Full seed-level paired results", "final_seed_level_results.csv", "all seeds retained", "main"),
        ("Table 4", "Reliability limitation", "final_reliability_results.csv", "show worst reversal", "main"),
    ]
    write_csv(
        OUT / "figure_source_manifest.csv",
        ["item", "content", "source", "integrity_rule", "placement"],
        [{"item": r[0], "content": r[1], "source": r[2], "integrity_rule": r[3], "placement": r[4]} for r in figure_rows],
    )

    final_decision = {
        "schema": "paper-q2-closeout-decision-v1",
        "date": TODAY,
        "historical_decisions_preserved": ["DRTP_Q2_LIMITATION_ONLY", "held-out FAIL", "development NO-GO"],
        "external_comparator_audit": "E2_NO_FAIR_EXTERNAL_COMPARATOR",
        "external_comparator_training_required": False,
        "new_algorithm_started": False,
        "seed_rescue_started": False,
        "remaining_scientific_experiment_count": 0,
        "remaining_training_budget": 0,
        "submission_decision": "B_Q2_SUBMISSION_READY_WITH_EXPLICIT_LIMITATIONS",
        "reason": "Evidence is traceable and bounded, but seed sensitivity, mixed safety, no fair external drop-in, and 3-UAV scope must be explicit.",
    }
    write(OUT / "final_submission_decision.json", json.dumps(final_decision, indent=2, ensure_ascii=False))

    main_table = md_table(
        ["Contract", "Method", "Seed scope", "J_N", "J_F0", "J_OOD mean", "J_OOD worst", "Timeout", "Collision"],
        [[r["contract"], r["method"], r["seed_scope"], r["J_nominal"], r["J_F0"], r["J_OOD_mean"], r["J_OOD_worst"], r["timeout"], r["collision"]] for r in main_rows],
    )
    seed_table = md_table(
        ["Seed", "Stratum", "ΔJ_N", "ΔF0", "ΔOOD mean", "ΔOOD worst", "Note"],
        [[r["seed"], r["contract"], r["delta_nominal"], r["delta_F0"], r["delta_OOD_mean"], r["delta_OOD_worst"], r["direction_note"]] for r in seed_rows],
    )
    summary_table = md_table(
        ["Metric", "Wins", "Mean Δ", "Median Δ", "SD", "IQR", "MAD", "Worst Δ"],
        [[r["metric"], r["wins"], r["mean_delta_drtp_minus_utr"], r["median_delta_drtp_minus_utr"], r["std"], r["iqr"], r["mad"], r["worst_delta"]] for r in reliability_rows],
    )

    write(DOCS / "PAPER_Q2_FINAL_EVIDENCE_FREEZE.md", f"""# PAPER-Q2 Final Evidence Freeze

**Date:** {TODAY}
**Status:** frozen zero-training closeout evidence.

## Immutable historical decisions

`DRTP_Q2_LIMITATION_ONLY`, the DRTP development `NO-GO`, and the held-out `FAIL` remain historical facts. This closeout does not relabel any of them as PASS.

## Evidence retained

{main_table}

The central causal ablation is matched UTR-SG-MAPPO versus DRTP-SG-MAPPO: the architecture, parameter count, PPO, seven topology groups, nominal anchor, environment, reward, actor boundary, budget, and evaluation protocol are matched; only group weighting differs.

## Mandatory limitations

- The 3M development and 10M held-out records are separate contract strata, not homogeneous replicates.
- All paired seeds remain visible, including development seed1902 and held-out seed2002.
- The evidence supports higher historical average/median robustness with non-negligible seed sensitivity; it does not support stable or universal superiority.
- The scope is the frozen 3-UAV heterogeneous simulation; scalability and hardware validation are not claimed.

## Claim boundary

Allowed wording: “DRTP shows higher average and median historical paired robustness under the frozen topology-perturbation protocol, while exhibiting non-negligible training-seed sensitivity.”

Prohibited wording: “stable,” “reliably superior,” “consistently outperforms,” “universal topology generalization,” or “deployment-ready.”
""")

    write(DOCS / "PAPER_Q2_EXTERNAL_COMPARATOR_AUDIT.md", f"""# PAPER-Q2 External Comparator Audit

**Decision:** `E2 — NO_FAIR_EXTERNAL_COMPARATOR`
**Training started:** no.

{md_table(list(comparator_rows[0]), [[r[k] for k in comparator_rows[0]] for r in comparator_rows])}

TAPE is directly relevant as topology-aware cooperative MARL, but its topology/action/task semantics do not provide a drop-in implementation for the frozen heterogeneous Scout–Relay–Attacker relay-failure estimand. M3DDPG is directly relevant as robust MARL, but its minimax DDPG learner and opponent-variation framing are incompatible with the frozen MAPPO actor and information boundary. Implementing either would alter the scientific comparison rather than add a fair comparator.

Therefore no `PAPER_Q2_EXTERNAL_COMPARATOR_TRAINING_CONTRACT.md` is created, and no external-comparator training is authorized. The manuscript must state that the main empirical ablation is the capacity- and exposure-matched UTR versus DRTP comparison.
""")

    write(DOCS / "PAPER_Q2_EFFICIENCY_AUDIT.md", """# PAPER-Q2 Efficiency Audit

**Status:** partial but publication-safe.

UTR and DRTP have identical 116,728 trainable parameters and use the same Single-Graph actor/critic. DRTP adds no inference-time network or input and changes only the training-time topology-group weighting controller. The retained P3 architecture check stores equal model files of 479,288 bytes for the matched architecture.

No common-hardware, complete wall-clock or peak-memory log supports a fair numerical comparison. Such a comparison is therefore intentionally **not claimed**. The paper may report matched parameter count and training-only controller scope, but must not report invented speedup, GPU-memory, or hardware-efficiency claims.
""")

    write(DOCS / "PAPER_Q2_FINAL_STATISTICS_REPORT.md", f"""# PAPER-Q2 Final Statistics Report

**Independent unit:** training seed. Episodes are evaluation samples, not independent training replicates.

## Absolute strata

{main_table}

## Paired reliability summary

{summary_table}

## Full paired seed record

{seed_table}

The five-pair cross-stratum summary is descriptive only because the two development pairs use a 3M contract and the three held-out pairs use a 10M contract. No pooled-episode significance test or homogeneous confirmatory p-value is permitted. The severe seed2002 reversal remains a required main-text reliability result.
""")

    write(DOCS / "PAPER_Q2_FINAL_CLAIM_EVIDENCE_MATRIX.md", "# PAPER-Q2 Final Claim–Evidence Matrix\n\n" + md_table(["ID", "Claim/boundary", "Evidence", "Destination", "Status"], [list(row) for row in claims]) + "\n")

    write(DOCS / "PAPER_Q2_FINAL_FIGURE_TABLE_PLAN.md", "# PAPER-Q2 Final Figure and Table Plan\n\n" + md_table(["Item", "Content", "Traceable source", "Integrity rule", "Placement"], [list(row) for row in figure_rows]) + "\n\nEvery quantitative panel must be generated from the listed source; the development and held-out strata must never be merged into a single confirmatory bar.\n")

    write(DOCS / "PAPER_Q2_FINAL_REVIEWER_AUDIT.md", """# PAPER-Q2 Final Reviewer Audit

## Reviewer 1 — novelty and positioning

**Major concern:** adaptive weighting can look like a standard reweighting heuristic, and there is no external drop-in baseline.
**Evidence-based resolution:** frame the contribution as a bounded problem–method–reliability package: relay-node-induced legal path reconfiguration, a capacity/exposure-matched UTR-versus-DRTP ablation, and full seed-level reliability reporting. The external comparator audit documents why TAPE and M3DDPG are not fair frozen-contract drop-ins.
**Remaining limitation:** novelty is application/method-system integration, not a new robust-RL theorem.

## Reviewer 2 — experimental rigor and validity

**Major concern:** positive averages may conceal a bad seed or invalid failure exposure.
**Evidence-based resolution:** show all five paired seeds, including seed1902 and seed2002; report mean, median, spread, worst delta, safety, survival-to-onset, and risk-set trigger validity. Preserve the historical development NO-GO and held-out FAIL.
**Remaining limitation:** seed stability is not established.

## Reviewer 3 — UAV relevance and generality

**Major concern:** results are simulation-only and limited to three heterogeneous UAV roles.
**Evidence-based resolution:** make the information boundary, legal topology/path mechanism, failure semantics, and evaluation protocol explicit. Do not claim hardware validation, scalability, universal topology generalization, or deployment readiness.
**Remaining limitation:** 4/5-UAV, HIL, and real-flight evidence are absent.

## Cross-review synthesis

The manuscript is defensible only if its title, abstract, results, and conclusion consistently say “higher average/median robustness with explicit seed sensitivity,” retain the adverse seed and mixed safety outcomes, and identify UTR-versus-DRTP as the primary matched ablation. This audit does not authorize another algorithm or experiment.
""")

    write(DOCS / "PAPER_Q2_FINAL_SUBMISSION_READINESS.md", f"""# PAPER-Q2 Final Submission Readiness

**Date:** {TODAY}
**Decision:** `B — Q2_SUBMISSION_READY_WITH_EXPLICIT_LIMITATIONS`

## GO conditions met

- The problem, actor information boundary, failure semantics, and legal topology/path mechanism are traceable to frozen reports.
- The primary UTR-versus-DRTP comparison is capacity-, exposure-, PPO-, and evaluation-matched.
- Absolute outcomes, all paired seed deltas, dispersion, the adverse seed, and safety limitations are preserved.
- A strict external-comparator audit found no fair drop-in; no comparator training is silently substituted.
- The figure/table source manifest makes every planned quantitative panel traceable.

## Required manuscript limitations

1. DRTP has non-negligible training-seed sensitivity and cannot be described as uniformly reliable.
2. Development 3M and held-out 10M results are separated strata.
3. Safety is mixed; seed2002 is retained.
4. The work is limited to a frozen 3-UAV simulation and does not establish scalability or deployment performance.
5. There is no fair frozen-contract external comparator; this is disclosed rather than hidden.

## Stop rule

Remaining scientific experiment count: **0**. Remaining training budget: **0**. No new algorithm, seed rescue, external comparator, OOD expansion, canonical run, scalability study, or HIL test is authorized by this readiness decision.
""")

    print("PAPER-Q2 closeout package built")
    print("external comparator audit: E2_NO_FAIR_EXTERNAL_COMPARATOR")
    print("submission decision: B_Q2_SUBMISSION_READY_WITH_EXPLICIT_LIMITATIONS")


if __name__ == "__main__":
    main()
