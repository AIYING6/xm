from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "supplemental_data_readme.md"


@dataclass(frozen=True)
class DataItem:
    rel: str
    role: str
    budget: str
    use_in_paper: str


DATA_ITEMS = [
    DataItem("results/final_comm_300_eval.csv", "Raw final main evaluation rows.", "300 episodes per seed.", "Main-result evidence."),
    DataItem("results/final_comm_300_summary.csv", "Aggregated final main evaluation summary.", "300 episodes per seed.", "Main table and main figures."),
    DataItem("results/final_300_paired_statistics.csv", "Seed-paired descriptive confidence intervals.", "Three paired seeds.", "Statistical appendix table."),
    DataItem("results/comm_dropout_robustness_eval.csv", "Raw communication-dropout robustness diagnostic rows.", "50 episodes per seed.", "Appendix robustness diagnostic."),
    DataItem("results/comm_dropout_robustness_summary.csv", "Aggregated communication-dropout robustness diagnostic.", "50 episodes per seed.", "Appendix dropout table and figures."),
    DataItem("results/comm_dropout_paired_statistics.csv", "Seed-paired dropout descriptive statistics.", "Three paired seeds.", "Appendix dropout confidence-interval table."),
    DataItem("results/aggregate_robustness_summary.csv", "Cross-condition aggregate robustness summary.", "Aggregates existing diagnostics.", "Appendix robustness synthesis."),
    DataItem("results/claim_evidence_matrix.csv", "Paper claim-to-evidence matrix.", "Generated evidence audit.", "Binds manuscript claims to files, values, and wording boundaries."),
    DataItem("results/manuscript_evidence_reference_audit.csv", "Manuscript evidence-reference audit.", "Generated manuscript audit.", "Checks that Chinese and English LaTeX cite required evidence markers."),
    DataItem("results/bilingual_numeric_consistency_audit.csv", "Bilingual numeric consistency audit.", "Generated manuscript audit.", "Checks key values against Chinese and English LaTeX sources."),
    DataItem("results/latex_reference_integrity_audit.csv", "LaTeX label/reference integrity audit.", "Generated manuscript audit.", "Checks key table/figure labels and references in Chinese and English LaTeX."),
    DataItem("results/bilingual_manuscript_completeness_audit.csv", "Bilingual manuscript completeness audit.", "Generated manuscript audit.", "Checks structure, counts, markers, and submission action items."),
    DataItem("results/submission_action_register.csv", "Submission action register.", "Generated submission planning artifact.", "Tracks open, blocked, and deferred tasks before actual journal submission."),
    DataItem("results/experiment_extension_decision_plan.csv", "Experiment extension decision plan.", "Generated planning artifact.", "Prioritizes optional next experiments and future-system extensions."),
    DataItem("results/reproducibility_checksum_manifest.csv", "Stable artifact checksum manifest.", "Generated reproducibility artifact.", "Records SHA256 and file sizes for stable package files."),
    DataItem("results/reproducibility_checksum_verification.csv", "Checksum manifest verification rows.", "Generated reproducibility artifact.", "Verifies stable package files against recorded SHA256 and file sizes."),
    DataItem("results/radius_interpolation_eval.csv", "Raw held-out communication-radius interpolation rows.", "50 episodes per seed.", "Appendix interpolation diagnostic."),
    DataItem("results/radius_interpolation_summary.csv", "Held-out communication-radius interpolation summary.", "50 episodes per seed.", "Appendix interpolation table and figures."),
    DataItem("results/paper_comm_results.csv", "Legacy 100-episode communication-radius ablation summary.", "100 episodes per seed.", "Appendix/training-time ablation context."),
    DataItem("results/per_seed_comm_appendix.csv", "Per-seed appendix rows for baseline comparison.", "100 episodes per seed.", "Seed-variation scatter plots."),
    DataItem("results/speed_robustness_eval.csv", "Raw target-speed robustness rows.", "100 episodes per seed.", "Appendix target-speed diagnostic."),
    DataItem("results/speed_robustness_summary.csv", "Target-speed robustness summary.", "100 episodes per seed.", "Appendix robustness table and figures."),
    DataItem("results/edge_feature_ablation_eval.csv", "Raw evaluation-time edge-feature masking rows.", "30 episodes per seed.", "Mechanism diagnostic only."),
    DataItem("results/edge_feature_ablation_summary.csv", "Edge-feature masking summary.", "30 episodes per seed.", "Mechanism diagnostic table and figure."),
    DataItem("results/figure_asset_audit.csv", "Generated figure-asset quality checks.", "Asset audit.", "Technical reproducibility audit."),
    DataItem("results/evaluation_budget_audit.csv", "Episode-budget consistency checks.", "Asset audit.", "Prevents mixing main and appendix budgets."),
    DataItem("results/method_naming_audit.csv", "Method-name consistency checks.", "Asset audit.", "Prevents stale method names in publishable text."),
    DataItem("results/supplemental_csv_schema_audit.csv", "Supplemental CSV schema checks.", "Asset audit.", "Prevents schema, row-count, and key-domain drift."),
    DataItem("results/result_provenance_audit.csv", "Result artifact provenance checks.", "Asset audit.", "Maps tables/figures/reports to source data and scripts."),
    DataItem("results/lag_jsbsim_migration_probe.csv", "LAG/JSBSim migration-readiness probe.", "Interface diagnostic.", "Future extension evidence, not main validation."),
    DataItem("results/lag_role_graph_adapter_test.csv", "LAG-like role-graph adapter checks.", "Interface diagnostic.", "Future 6DOF migration evidence."),
    DataItem("results/lag_role_graph_wrapper_test.csv", "LAG-like reset/step graph wrapper checks.", "Interface diagnostic.", "Future 6DOF migration evidence."),
    DataItem("results/intercept_3d_smoke_test.csv", "3DOF heterogeneous interception environment smoke test.", "Environment interface diagnostic.", "Next-stage 3DOF migration evidence, not a learning result."),
    DataItem("results/intercept_3d_policy_eval.csv", "3DOF EA-RG-MAPPO-S checkpoint evaluation rows.", "3-episode smoke diagnostic.", "Checkpoint-loading and metric-schema evidence, not a learning result."),
]


def row_count(rel: str) -> str:
    path = ROOT / rel
    if not path.exists() or path.stat().st_size <= 0:
        return "missing"
    with path.open("r", encoding="utf-8", newline="") as f:
        return str(sum(1 for _ in csv.DictReader(f)))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Supplemental Data README",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Describe the CSV files that may be included as supplementary evidence for EA-RG-MAPPO-S.",
        "The main claim should rely on the 300-episode final evaluation; lower-budget files are appendix or diagnostic evidence.",
        "```",
        "",
        "## Data Inventory",
        "",
        "| File | Rows | Role | Budget | Paper Use |",
        "|---|---:|---|---|---|",
    ]
    for item in DATA_ITEMS:
        lines.append(
            f"| `{item.rel}` | {row_count(item.rel)} | {item.role} | {item.budget} | {item.use_in_paper} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "```text",
            "Use final_comm_300_summary.csv as the primary quantitative basis.",
            "Use dropout, radius-interpolation, speed, and edge-feature files as appendix diagnostics.",
            "Use LAG/JSBSim files only as migration-readiness evidence until real JSBSim data are restored and evaluated.",
            "Do not use intent diagnostic files as primary contribution evidence.",
            "```",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
