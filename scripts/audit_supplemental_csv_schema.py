from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "supplemental_csv_schema_audit.csv"
OUT_MD = ROOT / "docs" / "supplemental_csv_schema_audit.md"


RATE_COLUMNS = {
    "success_rate",
    "success",
    "chain_closed",
    "attack_window_formed",
    "attack_window_rate",
    "tracking_rate",
    "comm_connectivity",
    "collision_rate",
    "collision",
    "timeout_rate",
    "timeout",
    "constraint_violation",
    "success_mean",
    "success_std",
    "collision_mean",
    "collision_std",
    "timeout_mean",
    "timeout_std",
    "mean_success",
    "worst_success",
    "success_range",
    "mean_collision",
    "worst_collision",
    "collision_range",
    "mean_margin",
    "conservative_margin",
}


@dataclass(frozen=True)
class CsvSchemaSpec:
    name: str
    path: str
    expected_rows: int
    columns: tuple[str, ...]
    expected_values: dict[str, tuple[str, ...]] = field(default_factory=dict)
    require_exact_columns: bool = True
    note: str = ""


COMMON_EVAL_COLUMNS = (
    "method",
    "seed",
    "kind",
    "model",
    "episodes",
    "target_policy",
    "target_speed",
    "radius",
    "success_rate",
    "collision_rate",
    "timeout_rate",
    "avg_steps",
    "avg_mean_distance",
    "intent_accuracy",
)

COMMON_SUMMARY_COLUMNS = (
    "method",
    "episodes",
    "radius",
    "success_mean",
    "success_std",
    "collision_mean",
    "collision_std",
    "timeout_mean",
    "timeout_std",
    "avg_steps_mean",
    "avg_steps_std",
    "n",
)

METHODS = ("EA-RG-MAPPO-S", "GAT-MAPPO", "MAPPO")
SEEDS = ("0", "1", "2")
MAIN_RADII = ("4", "6", "8", "10")


SPECS = [
    CsvSchemaSpec(
        "final_main_raw",
        "results/final_comm_300_eval.csv",
        36,
        COMMON_EVAL_COLUMNS,
        {"method": METHODS, "seed": SEEDS, "episodes": ("300",), "target_policy": ("mixed",), "target_speed": ("0.75",), "radius": MAIN_RADII},
        note="Raw final 300-episode rows.",
    ),
    CsvSchemaSpec(
        "final_main_summary",
        "results/final_comm_300_summary.csv",
        12,
        COMMON_SUMMARY_COLUMNS,
        {"method": METHODS, "episodes": ("300",), "radius": MAIN_RADII, "n": ("3",)},
        note="Aggregated final 300-episode rows.",
    ),
    CsvSchemaSpec(
        "final_main_paired_statistics",
        "results/final_300_paired_statistics.csv",
        16,
        ("baseline", "radius", "metric", "n", "mean_diff", "std_diff", "ci95_low", "ci95_high", "t_stat", "cohen_dz", "seed_diffs"),
        {"baseline": ("GAT-MAPPO", "MAPPO"), "radius": MAIN_RADII, "metric": ("collision_reduction", "success_gain"), "n": ("3",)},
        note="Seed-paired final descriptive statistics.",
    ),
    CsvSchemaSpec(
        "comm_dropout_raw",
        "results/comm_dropout_robustness_eval.csv",
        54,
        (*COMMON_EVAL_COLUMNS[:8], "comm_dropout_prob", *COMMON_EVAL_COLUMNS[8:]),
        {"method": METHODS, "seed": SEEDS, "episodes": ("50",), "target_policy": ("mixed",), "target_speed": ("0.75",), "radius": ("4", "8"), "comm_dropout_prob": ("0", "0.25", "0.5")},
        note="Raw communication-dropout diagnostic rows.",
    ),
    CsvSchemaSpec(
        "comm_dropout_summary",
        "results/comm_dropout_robustness_summary.csv",
        18,
        ("method", "episodes", "radius", "comm_dropout_prob", "success_mean", "success_std", "collision_mean", "collision_std", "timeout_mean", "timeout_std", "avg_steps_mean", "avg_steps_std", "n"),
        {"method": METHODS, "episodes": ("50",), "radius": ("4", "8"), "comm_dropout_prob": ("0", "0.25", "0.5"), "n": ("3",)},
        note="Aggregated communication-dropout diagnostic rows.",
    ),
    CsvSchemaSpec(
        "comm_dropout_paired_statistics",
        "results/comm_dropout_paired_statistics.csv",
        24,
        ("baseline", "radius", "comm_dropout_prob", "metric", "n", "mean_diff", "std_diff", "ci95_low", "ci95_high", "t_stat", "cohen_dz", "seed_diffs"),
        {"baseline": ("GAT-MAPPO", "MAPPO"), "radius": ("4", "8"), "comm_dropout_prob": ("0", "0.25", "0.5"), "metric": ("collision_reduction", "success_gain"), "n": ("3",)},
        note="Seed-paired dropout descriptive statistics.",
    ),
    CsvSchemaSpec(
        "aggregate_robustness",
        "results/aggregate_robustness_summary.csv",
        6,
        ("scope", "method", "n_conditions", "mean_success", "worst_success", "success_range", "mean_collision", "worst_collision", "collision_range", "mean_margin", "conservative_margin"),
        {"scope": ("dropout_diagnostic", "final_cross_radius"), "method": METHODS, "n_conditions": ("4", "6")},
        note="Cross-condition aggregate robustness summary.",
    ),
    CsvSchemaSpec(
        "claim_evidence_matrix",
        "results/claim_evidence_matrix.csv",
        9,
        ("claim_id", "claim_type", "recommended_wording", "primary_evidence", "supporting_assets", "quantitative_evidence", "boundary", "status"),
        {"claim_id": ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"), "status": ("ok",)},
        note="Generated paper claim-to-evidence matrix.",
    ),
    CsvSchemaSpec(
        "manuscript_evidence_reference_audit",
        "results/manuscript_evidence_reference_audit.csv",
        51,
        ("claim_id", "language", "manuscript_path", "evidence_type", "marker", "status", "notes"),
        {"claim_id": ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"), "language": ("en", "zh"), "status": ("ok",)},
        note="Generated manuscript evidence-reference audit.",
    ),
    CsvSchemaSpec(
        "bilingual_numeric_consistency_audit",
        "results/bilingual_numeric_consistency_audit.csv",
        47,
        ("claim_id", "source", "value", "english_file", "chinese_file", "status", "notes"),
        {"claim_id": ("C1", "C2", "C3", "C4", "C5", "C6", "C9"), "status": ("ok",)},
        note="Generated bilingual manuscript numeric consistency audit.",
    ),
    CsvSchemaSpec(
        "latex_reference_integrity_audit",
        "results/latex_reference_integrity_audit.csv",
        86,
        ("project", "check_type", "item", "status", "notes"),
        {"project": ("chinese", "english"), "status": ("ok",)},
        note="Generated bilingual LaTeX label/reference integrity audit.",
    ),
    CsvSchemaSpec(
        "bilingual_manuscript_completeness_audit",
        "results/bilingual_manuscript_completeness_audit.csv",
        36,
        ("project", "check", "value", "status", "notes"),
        {"project": ("chinese", "english"), "status": ("action_item", "ok")},
        note="Generated bilingual manuscript completeness audit.",
    ),
    CsvSchemaSpec(
        "submission_action_register",
        "results/submission_action_register.csv",
        10,
        ("item_id", "priority", "status", "category", "action", "evidence", "next_step"),
        {"item_id": ("A1", "A10", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")},
        note="Generated submission-facing action item register.",
    ),
    CsvSchemaSpec(
        "experiment_extension_decision_plan",
        "results/experiment_extension_decision_plan.csv",
        7,
        ("option_id", "priority", "status", "experiment", "purpose", "current_evidence", "dependency", "estimated_cost", "decision_rule", "paper_use"),
        {"option_id": ("E1", "E2", "E3", "E4", "E5", "E6", "E7")},
        note="Generated optional next-experiment decision plan.",
    ),
    CsvSchemaSpec(
        "reproducibility_checksum_manifest",
        "results/reproducibility_checksum_manifest.csv",
        184,
        ("path", "artifact_group", "size_bytes", "sha256"),
        note="Generated stable artifact SHA256/size manifest.",
    ),
    CsvSchemaSpec(
        "reproducibility_checksum_verification",
        "results/reproducibility_checksum_verification.csv",
        184,
        ("path", "artifact_group", "expected_size_bytes", "actual_size_bytes", "expected_sha256", "actual_sha256", "status", "notes"),
        {"status": ("OK",)},
        note="Generated checksum manifest verification rows.",
    ),
    CsvSchemaSpec(
        "radius_interpolation_raw",
        "results/radius_interpolation_eval.csv",
        27,
        COMMON_EVAL_COLUMNS,
        {"method": METHODS, "seed": SEEDS, "episodes": ("50",), "target_policy": ("mixed",), "target_speed": ("0.75",), "radius": ("5", "7", "9")},
        note="Raw held-out communication-radius interpolation rows.",
    ),
    CsvSchemaSpec(
        "radius_interpolation_summary",
        "results/radius_interpolation_summary.csv",
        9,
        COMMON_SUMMARY_COLUMNS,
        {"method": METHODS, "episodes": ("50",), "radius": ("5", "7", "9"), "n": ("3",)},
        note="Aggregated held-out communication-radius interpolation rows.",
    ),
    CsvSchemaSpec(
        "legacy_comm_ablation",
        "results/paper_comm_results.csv",
        20,
        ("method", "result_type", "radius", "success_mean", "success_std", "collision_mean", "collision_std", "timeout_mean", "timeout_std", "avg_steps_mean", "avg_steps_std"),
        {"method": ("GAT-MAPPO", "MAPPO", "RI edge fixed-r8", "RI edge staged", "RI no-edge"), "result_type": ("mean_std",), "radius": MAIN_RADII},
        note="Legacy 100-episode communication ablation context.",
    ),
    CsvSchemaSpec(
        "per_seed_appendix",
        "results/per_seed_comm_appendix.csv",
        36,
        ("method", "seed", "radius", "success_rate", "collision_rate", "timeout_rate", "avg_steps"),
        {"method": METHODS, "seed": SEEDS, "radius": MAIN_RADII},
        note="Per-seed appendix scatter data.",
    ),
    CsvSchemaSpec(
        "speed_robustness_raw",
        "results/speed_robustness_eval.csv",
        54,
        COMMON_EVAL_COLUMNS,
        {"method": METHODS, "seed": SEEDS, "episodes": ("100",), "target_policy": ("mixed",), "target_speed": ("0.6", "0.75", "0.9"), "radius": ("4", "8")},
        note="Raw target-speed robustness rows.",
    ),
    CsvSchemaSpec(
        "speed_robustness_summary",
        "results/speed_robustness_summary.csv",
        18,
        ("method", "episodes", "radius", "target_speed", "success_mean", "success_std", "collision_mean", "collision_std", "timeout_mean", "timeout_std", "avg_steps_mean", "avg_steps_std", "n"),
        {"method": METHODS, "episodes": ("100",), "radius": ("4", "8"), "target_speed": ("0.6", "0.75", "0.9"), "n": ("3",)},
        note="Aggregated target-speed robustness rows.",
    ),
    CsvSchemaSpec(
        "edge_feature_ablation_raw",
        "results/edge_feature_ablation_eval.csv",
        42,
        ("method", "seed", "model", "episodes", "target_policy", "target_speed", "radius", "ablation", "zero_dims", "zero_dim_names", "success_rate", "collision_rate", "timeout_rate", "avg_steps", "avg_mean_distance", "intent_accuracy"),
        {"method": ("EA-RG-MAPPO-S",), "seed": SEEDS, "episodes": ("30",), "target_policy": ("mixed",), "target_speed": ("0.75",), "radius": ("4", "8")},
        note="Raw evaluation-time edge-feature masking rows.",
    ),
    CsvSchemaSpec(
        "edge_feature_ablation_summary",
        "results/edge_feature_ablation_summary.csv",
        14,
        ("radius", "ablation", "episodes", "n", "zero_dims", "zero_dim_names", "success_mean", "success_std", "collision_mean", "collision_std", "timeout_mean", "timeout_std", "avg_steps_mean", "avg_steps_std"),
        {"radius": ("4", "8"), "episodes": ("30",), "n": ("3",)},
        note="Aggregated evaluation-time edge-feature masking rows.",
    ),
    CsvSchemaSpec(
        "figure_asset_audit",
        "results/figure_asset_audit.csv",
        29,
        ("figure", "width", "height", "file_size_kb", "gray_std", "sampled_unique_colors", "status", "notes"),
        {"status": ("ok",)},
        note="Generated figure technical audit.",
    ),
    CsvSchemaSpec(
        "evaluation_budget_audit",
        "results/evaluation_budget_audit.csv",
        6,
        ("name", "csv_path", "expected_rows", "actual_rows", "expected_episodes", "actual_episodes", "latex_path", "latex_marker", "status", "notes"),
        {"status": ("ok",)},
        note="Generated evaluation-budget audit.",
    ),
    CsvSchemaSpec(
        "method_naming_audit",
        "results/method_naming_audit.csv",
        28,
        ("file", "final_name_count", "old_name_count", "required_marker_missing", "status", "notes"),
        {"status": ("ok",)},
        note="Generated method-name consistency audit.",
    ),
    CsvSchemaSpec(
        "lag_jsbsim_migration_probe",
        "results/lag_jsbsim_migration_probe.csv",
        29,
        ("kind", "item", "status", "detail"),
        note="LAG/JSBSim migration-readiness probe.",
    ),
    CsvSchemaSpec(
        "lag_role_graph_adapter_test",
        "results/lag_role_graph_adapter_test.csv",
        26,
        ("check", "status", "detail"),
        {"status": ("ok",)},
        note="LAG-like state-to-role-graph adapter test.",
    ),
    CsvSchemaSpec(
        "lag_role_graph_wrapper_test",
        "results/lag_role_graph_wrapper_test.csv",
        11,
        ("check", "status", "detail"),
        {"status": ("ok",)},
        note="LAG-like reset/step graph wrapper test.",
    ),
    CsvSchemaSpec(
        "intercept_3d_smoke_test",
        "results/intercept_3d_smoke_test.csv",
        15,
        (
            "policy",
            "seed",
            "success",
            "timeout",
            "collision",
            "constraint_violation",
            "steps",
            "mean_range",
            "tracking_rate",
            "attack_window_rate",
            "comm_connectivity",
            "mean_message_age",
            "reward_sum",
        ),
        {"policy": ("geometric", "geometric_dropout", "random"), "seed": ("0", "1", "2", "3", "4")},
        note="3DOF heterogeneous interception environment smoke test.",
    ),
    CsvSchemaSpec(
        "intercept_3d_policy_eval",
        "results/intercept_3d_policy_eval.csv",
        3,
        (
            "method",
            "checkpoint",
            "policy_source",
            "seed",
            "episode",
            "episodes",
            "target_policy",
            "strict_target_sensing",
            "agent_target_info_bottleneck",
            "target_prior_position",
            "max_target_message_age_steps",
            "min_target_confidence",
            "communication_range_scale",
            "communication_dropout_prob",
            "message_delay_steps",
            "radar_dropout_prob",
            "failed_blue_agent",
            "node_failure_start_step",
            "node_failure_duration_steps",
            "min_success_step",
            "graph_relation_ablation",
            "graph_message_ablation",
            "graph_input_ablation",
            "deterministic",
            "success",
            "chain_closed",
            "attack_window_formed",
            "attack_window_rate",
            "tracking_rate",
            "comm_connectivity",
            "mean_message_age",
            "collision",
            "timeout",
            "constraint_violation",
            "steps",
            "first_attack_window_step",
            "first_chain_close_step",
            "post_failure_chain_recovered",
            "post_failure_chain_recovery_steps",
            "post_failure_chain_recovery_steps_censored",
            "post_failure_chain_recovered_only_steps",
            "post_failure_chain_maintained",
            "post_failure_chain_recovered_after_loss",
            "pre_failure_chain_established",
            "pre_failure_chain_maintained",
            "pre_failure_chain_recovered_after_loss",
            "post_failure_chain_first_established",
            "post_failure_chain_never_established",
            "post_failure_chain_unrecovered",
            "post_failure_fresh_info_recovered",
            "post_failure_fresh_info_recovery_steps",
            "post_failure_fresh_info_acquired_without_prior_loss",
            "post_failure_fresh_info_first_established",
            "post_failure_fresh_direct_recovered",
            "post_failure_fresh_comm_recovered",
            "post_failure_post_delivered_old_info_recovered",
            "post_failure_stale_cache_recovered",
            "post_failure_first_chain_step",
            "chain_closed_during_failure_rate",
            "tracking_during_failure_rate",
            "connectivity_during_failure",
            "avg_mean_range",
            "final_mean_range",
            "episode_min_blue_red_distance",
            "episode_min_blue_blue_distance",
            "final_min_blue_red_distance",
            "final_min_blue_blue_distance",
            "reward_sum",
        ),
        {
            "method": ("EA-RG-MAPPO-S",),
            "policy_source": ("checkpoint",),
            "episodes": ("3",),
            "target_policy": ("evasive",),
            "strict_target_sensing": ("False",),
            "agent_target_info_bottleneck": ("False",),
            "max_target_message_age_steps": ("80",),
            "min_target_confidence": ("0.2",),
            "communication_range_scale": ("1",),
            "communication_dropout_prob": ("0",),
            "message_delay_steps": ("0",),
            "radar_dropout_prob": ("0",),
            "failed_blue_agent": ("-1",),
            "node_failure_start_step": ("0",),
            "node_failure_duration_steps": ("0",),
            "min_success_step": ("0",),
            "graph_relation_ablation": ("none",),
            "graph_message_ablation": ("none",),
            "graph_input_ablation": ("none",),
            "deterministic": ("True",),
        },
        note="3DOF checkpoint evaluation smoke diagnostic; not a paper learning result.",
    ),
]


def normalize_value(value: str) -> str:
    text = value.strip()
    if text == "":
        return text
    try:
        return f"{float(text):g}"
    except ValueError:
        return text


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def check_numeric_ranges(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    errors = []
    for column in columns:
        if column not in RATE_COLUMNS:
            continue
        for idx, row in enumerate(rows, start=1):
            value = row.get(column, "")
            if value == "":
                continue
            try:
                numeric = float(value)
            except ValueError:
                errors.append(f"{column}: non_numeric row={idx} value={value}")
                continue
            if not 0.0 <= numeric <= 1.0:
                errors.append(f"{column}: out_of_range row={idx} value={value}")
    return errors


def audit_spec(spec: CsvSchemaSpec) -> dict[str, str]:
    path = ROOT / spec.path
    errors: list[str] = []
    if not path.exists() or path.stat().st_size <= 0:
        return {
            "name": spec.name,
            "path": spec.path,
            "expected_rows": str(spec.expected_rows),
            "actual_rows": "0",
            "expected_columns": str(len(spec.columns)),
            "actual_columns": "0",
            "domain_checks": "",
            "status": "failed",
            "notes": "missing_or_empty",
        }

    columns, rows = read_csv(path)
    missing = [column for column in spec.columns if column not in columns]
    unexpected = [column for column in columns if column not in spec.columns] if spec.require_exact_columns else []
    if missing:
        errors.append(f"missing_columns={','.join(missing)}")
    if unexpected:
        errors.append(f"unexpected_columns={','.join(unexpected)}")
    if len(rows) != spec.expected_rows:
        errors.append(f"row_count expected={spec.expected_rows} actual={len(rows)}")

    domain_summaries = []
    for column, expected_values in spec.expected_values.items():
        if column not in columns:
            continue
        actual = sorted({normalize_value(row.get(column, "")) for row in rows})
        expected = sorted({normalize_value(value) for value in expected_values})
        domain_summaries.append(f"{column}={','.join(actual)}")
        if actual != expected:
            errors.append(f"{column}_domain expected={expected} actual={actual}")

    errors.extend(check_numeric_ranges(rows, columns))

    return {
        "name": spec.name,
        "path": spec.path,
        "expected_rows": str(spec.expected_rows),
        "actual_rows": str(len(rows)),
        "expected_columns": str(len(spec.columns)),
        "actual_columns": str(len(columns)),
        "domain_checks": "; ".join(domain_summaries),
        "status": "ok" if not errors else "failed",
        "notes": spec.note if not errors else "; ".join(errors),
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name",
        "path",
        "expected_rows",
        "actual_rows",
        "expected_columns",
        "actual_columns",
        "domain_checks",
        "status",
        "notes",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row["status"] != "ok"]
    lines = [
        "# Supplemental CSV Schema Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check that supplementary CSV files keep the expected columns, row counts, key value domains, and rate ranges.",
        "This audit complements the quantitative claim checks; it does not rerun experiments.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"csv_files_checked = {len(rows)}",
        f"failures = {len(failures)}",
        "```",
        "",
        "## Rows",
        "",
        "| Name | Rows | Columns | Status | Notes |",
        "|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['name']}` | {row['actual_rows']} / {row['expected_rows']} | "
            f"{row['actual_columns']} / {row['expected_columns']} | {row['status']} | {row['notes']} |"
        )

    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures:
            lines.append(f"- `{row['path']}`: {row['notes']}")

    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Passing this audit means the CSV files are structurally consistent with the current paper package.",
            "It does not prove that a diagnostic has the same evidentiary weight as the 300-episode final main evaluation.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [audit_spec(spec) for spec in SPECS]
    write_csv(rows)
    write_report(rows)
    failures = [row for row in rows if row["status"] != "ok"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"csv files checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row['name']} {row['notes']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
