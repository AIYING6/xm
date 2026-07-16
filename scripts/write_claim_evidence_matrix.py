from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "claim_evidence_matrix.csv"
OUT_MD = ROOT / "docs" / "claim_evidence_matrix.md"


@dataclass(frozen=True)
class ClaimRow:
    claim_id: str
    claim_type: str
    recommended_wording: str
    primary_evidence: str
    supporting_assets: str
    quantitative_evidence: str
    boundary: str
    status: str


def read_rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def row_by(rows: list[dict[str, str]], **criteria: object) -> dict[str, str]:
    matches = []
    for row in rows:
        ok = True
        for key, value in criteria.items():
            if isinstance(value, float):
                ok = abs(float(row[key]) - value) < 1e-6
            else:
                ok = row[key] == str(value)
            if not ok:
                break
        if ok:
            matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one row for {criteria}, got {len(matches)}")
    return matches[0]


def fmt(value: float) -> str:
    return f"{value:.3f}"


def status(condition: bool) -> str:
    return "ok" if condition else "failed"


def main_claim() -> ClaimRow:
    rows = read_rows("results/final_comm_300_summary.csv")
    radii = [4.0, 6.0, 8.0, 10.0]
    evidence = []
    ok = True
    for radius in radii:
        ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius)
        mappo = row_by(rows, method="MAPPO", radius=radius)
        gat = row_by(rows, method="GAT-MAPPO", radius=radius)
        ok = ok and f(ea, "collision_mean") < f(mappo, "collision_mean")
        ok = ok and f(ea, "collision_mean") < f(gat, "collision_mean")
        ok = ok and f(ea, "collision_mean") <= 0.10
        ok = ok and f(ea, "success_mean") >= 0.87
        evidence.append(
            f"r{int(radius)} success={fmt(f(ea, 'success_mean'))}, collision={fmt(f(ea, 'collision_mean'))}"
        )
    return ClaimRow(
        "C1",
        "main_result",
        "EA-RG-MAPPO-S improves finite-communication pursuit stability and consistently lowers collision rates against MAPPO and GAT-MAPPO in the simplified 2D UAV pursuit benchmark.",
        "results/final_comm_300_summary.csv",
        "results/latex_final_comm_300_table.tex; results/figures/final_300_success_rate.png; results/figures/final_300_collision_rate.png",
        "; ".join(evidence),
        "Do not claim full 6DOF combat, missile/radar, or human-UAV teaming validation from this result.",
        status(ok),
    )


def seed_paired_claim() -> ClaimRow:
    rows = read_rows("results/final_300_paired_statistics.csv")
    ok = all(f(row, "mean_diff") > 0 for row in rows)
    positive_ci = [
        row
        for row in rows
        if row["baseline"] == "GAT-MAPPO"
        and row["metric"] in {"success_gain", "collision_reduction"}
        and row["radius"] in {"4", "8", "10"}
        and f(row, "ci95_low") > 0
    ]
    ok = ok and len(positive_ci) >= 4
    examples = []
    for baseline, radius, metric in [
        ("MAPPO", 4.0, "collision_reduction"),
        ("GAT-MAPPO", 4.0, "collision_reduction"),
        ("GAT-MAPPO", 8.0, "success_gain"),
    ]:
        row = row_by(rows, baseline=baseline, radius=radius, metric=metric)
        examples.append(
            f"{baseline} r{int(radius)} {metric}: mean_diff={fmt(f(row, 'mean_diff'))}, ci95=[{fmt(f(row, 'ci95_low'))},{fmt(f(row, 'ci95_high'))}]"
        )
    return ClaimRow(
        "C2",
        "statistical_support",
        "Seed-paired descriptive statistics provide effect-direction context across the three tested seeds.",
        "results/final_300_paired_statistics.csv",
        "results/latex_final_300_paired_ci_table.tex; results/final_300_paired_statistics.md",
        "; ".join(examples),
        "The project uses descriptive paired intervals over three seeds; intervals that cross zero should be reported cautiously and not treated as strong hypothesis-test evidence.",
        status(ok),
    )


def dropout_claim() -> ClaimRow:
    rows = read_rows("results/comm_dropout_robustness_summary.csv")
    ok = True
    examples = []
    for radius in [4.0, 8.0]:
        for dropout in [0.0, 0.25, 0.5]:
            ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius, comm_dropout_prob=dropout)
            mappo = row_by(rows, method="MAPPO", radius=radius, comm_dropout_prob=dropout)
            gat = row_by(rows, method="GAT-MAPPO", radius=radius, comm_dropout_prob=dropout)
            ok = ok and f(ea, "collision_mean") < f(mappo, "collision_mean")
            ok = ok and f(ea, "collision_mean") < f(gat, "collision_mean")
            if dropout == 0.5:
                examples.append(
                    f"r{int(radius)} p=0.5 collision: EA={fmt(f(ea, 'collision_mean'))}, MAPPO={fmt(f(mappo, 'collision_mean'))}, GAT={fmt(f(gat, 'collision_mean'))}"
                )
    return ClaimRow(
        "C3",
        "robustness_diagnostic",
        "Under evaluation-time communication dropout, EA-RG-MAPPO-S retains lower collision rates than both baselines at the tested radii.",
        "results/comm_dropout_robustness_summary.csv",
        "results/latex_comm_dropout_robustness_table.tex; results/figures/comm_dropout_success_rate.png; results/figures/comm_dropout_collision_rate.png",
        "; ".join(examples),
        "This is a 50-episode-per-seed diagnostic, so it should be presented as appendix robustness evidence.",
        status(ok),
    )


def aggregate_claim() -> ClaimRow:
    rows = read_rows("results/aggregate_robustness_summary.csv")
    ok = True
    examples = []
    for scope in ["final_cross_radius", "dropout_diagnostic"]:
        ea = row_by(rows, scope=scope, method="EA-RG-MAPPO-S")
        mappo = row_by(rows, scope=scope, method="MAPPO")
        gat = row_by(rows, scope=scope, method="GAT-MAPPO")
        ok = ok and f(ea, "mean_success") > f(mappo, "mean_success") > 0
        ok = ok and f(ea, "mean_success") > f(gat, "mean_success") > 0
        ok = ok and f(ea, "mean_collision") < f(mappo, "mean_collision")
        ok = ok and f(ea, "mean_collision") < f(gat, "mean_collision")
        ok = ok and f(ea, "conservative_margin") > f(mappo, "conservative_margin")
        ok = ok and f(ea, "conservative_margin") > f(gat, "conservative_margin")
        examples.append(
            f"{scope}: EA mean_success={fmt(f(ea, 'mean_success'))}, mean_collision={fmt(f(ea, 'mean_collision'))}, conservative_margin={fmt(f(ea, 'conservative_margin'))}"
        )
    return ClaimRow(
        "C4",
        "aggregate_diagnostic",
        "Aggregate descriptive metrics summarize that EA-RG-MAPPO-S has the strongest success-collision margin across the evaluated finite-communication conditions.",
        "results/aggregate_robustness_summary.csv",
        "results/latex_aggregate_robustness_table.tex; results/aggregate_robustness_summary.md",
        "; ".join(examples),
        "The aggregate score is for organization and description only; it is not a new training objective or replacement for per-radius tables.",
        status(ok),
    )


def interpolation_claim() -> ClaimRow:
    rows = read_rows("results/radius_interpolation_summary.csv")
    ok = True
    examples = []
    for radius in [5.0, 7.0, 9.0]:
        ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius)
        mappo = row_by(rows, method="MAPPO", radius=radius)
        gat = row_by(rows, method="GAT-MAPPO", radius=radius)
        ok = ok and f(ea, "collision_mean") < f(mappo, "collision_mean")
        ok = ok and f(ea, "collision_mean") < f(gat, "collision_mean")
        ok = ok and f(ea, "success_mean") >= 0.86
        examples.append(
            f"r{int(radius)} collision: EA={fmt(f(ea, 'collision_mean'))}, MAPPO={fmt(f(mappo, 'collision_mean'))}, GAT={fmt(f(gat, 'collision_mean'))}"
        )
    return ClaimRow(
        "C5",
        "generalization_diagnostic",
        "On held-out communication radii, the final method preserves lower collision rates than the baselines.",
        "results/radius_interpolation_summary.csv",
        "results/latex_radius_interpolation_table.tex; results/figures/radius_interpolation_success_rate.png; results/figures/radius_interpolation_collision_rate.png",
        "; ".join(examples),
        "This is a 50-episode-per-seed interpolation diagnostic, not the main evaluation table.",
        status(ok),
    )


def speed_claim() -> ClaimRow:
    rows = read_rows("results/speed_robustness_summary.csv")
    ok = True
    examples = []
    for radius in [4.0, 8.0]:
        ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius, target_speed=0.9)
        mappo = row_by(rows, method="MAPPO", radius=radius, target_speed=0.9)
        gat = row_by(rows, method="GAT-MAPPO", radius=radius, target_speed=0.9)
        ok = ok and f(ea, "collision_mean") < f(mappo, "collision_mean")
        ok = ok and f(ea, "collision_mean") < f(gat, "collision_mean")
        examples.append(
            f"r{int(radius)} speed=0.90 collision: EA={fmt(f(ea, 'collision_mean'))}, MAPPO={fmt(f(mappo, 'collision_mean'))}, GAT={fmt(f(gat, 'collision_mean'))}"
        )
    return ClaimRow(
        "C6",
        "robustness_diagnostic",
        "The low-collision behavior remains visible under a stronger mixed-target speed setting.",
        "results/speed_robustness_summary.csv",
        "results/latex_speed_robustness_table.tex; results/figures/speed_robustness_collision_r4.png; results/figures/speed_robustness_collision_r8.png",
        "; ".join(examples),
        "This robustness check uses 100 episodes per seed and should not replace the 300-episode main table.",
        status(ok),
    )


def edge_masking_claim() -> ClaimRow:
    rows = read_rows("results/edge_feature_ablation_summary.csv")
    ok = True
    examples = []
    for radius in [4.0, 8.0]:
        base = row_by(rows, radius=radius, ablation="none")
        comm = row_by(rows, radius=radius, ablation="zero_comm_target_flags")
        all_edge = row_by(rows, radius=radius, ablation="zero_all_edge_features")
        ok = ok and f(comm, "success_mean") < f(base, "success_mean")
        ok = ok and f(comm, "collision_mean") > f(base, "collision_mean")
        ok = ok and abs(f(all_edge, "success_mean") - f(base, "success_mean")) <= 0.05
        examples.append(
            f"r{int(radius)} comm/target mask: success {fmt(f(base, 'success_mean'))}->{fmt(f(comm, 'success_mean'))}, collision {fmt(f(base, 'collision_mean'))}->{fmt(f(comm, 'collision_mean'))}"
        )
    return ClaimRow(
        "C7",
        "mechanism_diagnostic",
        "Evaluation-time masking suggests the communication/target edge-feature group has the most consistent diagnostic effect.",
        "results/edge_feature_ablation_summary.csv",
        "results/latex_edge_feature_ablation_table.tex; results/figures/edge_feature_ablation_delta.png",
        "; ".join(examples),
        "This is evaluation-time masking without retraining; do not present it as a structural ablation proof.",
        status(ok),
    )


def lag_boundary_claim() -> ClaimRow:
    adapter = read_rows("results/lag_role_graph_adapter_test.csv")
    wrapper = read_rows("results/lag_role_graph_wrapper_test.csv")
    probe = read_rows("results/lag_jsbsim_migration_probe.csv")
    adapter_ok = all(row["status"] == "ok" for row in adapter)
    wrapper_ok = all(row["status"] == "ok" for row in wrapper)
    has_real_blocker = any(row["status"] in {"failed", "missing"} for row in probe)
    return ClaimRow(
        "C8",
        "extension_boundary",
        "The role-graph interface has been prepared and smoke-tested for LAG-like 6DOF states, but real JSBSim/LAG validation is still blocked by missing runtime assets/imports.",
        "results/lag_role_graph_adapter_test.csv; results/lag_role_graph_wrapper_test.csv; results/lag_jsbsim_migration_probe.csv",
        "docs/lag_role_graph_adapter_test.md; docs/lag_role_graph_wrapper_test.md; docs/lag_jsbsim_migration_probe.md",
        f"adapter_checks={len(adapter)}, wrapper_checks={len(wrapper)}, probe_rows={len(probe)}, real_lag_blocker_present={has_real_blocker}",
        "Use this only as migration-readiness evidence, not as completed 6DOF combat validation.",
        status(adapter_ok and wrapper_ok and has_real_blocker),
    )


def intent_boundary_claim() -> ClaimRow:
    text = (ROOT / "docs" / "english_experiments_draft.md").read_text(encoding="utf-8")
    has_boundary = "balanced accuracy of 0.200" in text and "cannot support a high-accuracy intent-recognition claim" in text
    return ClaimRow(
        "C9",
        "negative_boundary",
        "The auxiliary target-intent branch is retained only as a diagnostic and should not be used as a main contribution.",
        "docs/english_experiments_draft.md",
        "results/visualization_and_intent_diagnostics.md; results/figures/intent_confusion_ri_staged_r8.png; results/figures/intent_confusion_ri_balanced_seed1_r8.png",
        "plain_accuracy=0.587, balanced_accuracy=0.200",
        "Do not claim high-accuracy intent recognition in the current paper.",
        status(has_boundary),
    )


def build_rows() -> list[ClaimRow]:
    return [
        main_claim(),
        seed_paired_claim(),
        dropout_claim(),
        aggregate_claim(),
        interpolation_claim(),
        speed_claim(),
        edge_masking_claim(),
        lag_boundary_claim(),
        intent_boundary_claim(),
    ]


def write_csv(rows: list[ClaimRow]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(ClaimRow.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_markdown(rows: list[ClaimRow]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row.status != "ok"]
    lines = [
        "# Claim Evidence Matrix",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Bind each paper-facing claim to concrete result files, figures/tables, quantitative values, and wording boundaries.",
        "This matrix is generated from current result CSVs and should be used while drafting or revising the manuscript.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"claims_checked = {len(rows)}",
        f"failures = {len(failures)}",
        "```",
        "",
        "## Matrix",
        "",
        "| ID | Type | Recommended wording | Evidence | Boundary | Status |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        evidence = f"{row.quantitative_evidence}<br>`{row.primary_evidence}`"
        lines.append(
            f"| {row.claim_id} | {row.claim_type} | {row.recommended_wording} | {evidence} | {row.boundary} | {row.status} |"
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures:
            lines.append(f"- {row.claim_id}: {row.recommended_wording}")
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Use the recommended wording as a ceiling, not a starting point for stronger claims.",
            "Any new experiment, renamed method, or changed result table should regenerate this matrix before manuscript edits.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    failures = [row for row in rows if row.status != "ok"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"claims checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row.claim_id} {row.recommended_wording}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
