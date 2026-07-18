from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)
DEFAULT_REPORT = ROOT / "docs" / "paper_asset_build_report.md"


@dataclass
class StepResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


GENERATION_STEPS = [
    ("Runtime environment report", ["scripts/write_runtime_environment_report.py"]),
    ("Checkpoint inventory", ["scripts/write_checkpoint_inventory.py"]),
    ("Submission action register", ["scripts/write_submission_action_register.py"]),
    ("Experiment extension decision plan", ["scripts/write_experiment_extension_decision_plan.py"]),
    ("Supplemental data README", ["scripts/write_supplemental_data_readme.py"]),
    ("Submission readiness report", ["scripts/write_submission_readiness_report.py"]),
    ("Submission package manifest", ["scripts/write_submission_package_manifest.py"]),
    ("English manuscript readiness audit", ["scripts/audit_english_manuscript_readiness.py"]),
    ("Bilingual manuscript completeness audit", ["scripts/audit_bilingual_manuscript_completeness.py"]),
    ("Final 300 paired statistics", ["scripts/analyze_final_300_statistics.py"]),
    ("Communication dropout paired statistics", ["scripts/analyze_comm_dropout_statistics.py"]),
    ("Aggregate robustness summary", ["scripts/analyze_aggregate_robustness.py"]),
    ("Claim evidence matrix", ["scripts/write_claim_evidence_matrix.py"]),
    ("Manuscript evidence reference audit", ["scripts/audit_manuscript_evidence_references.py"]),
    ("Bilingual numeric consistency audit", ["scripts/audit_bilingual_numeric_consistency.py"]),
    ("LaTeX reference integrity audit", ["scripts/audit_latex_reference_integrity.py"]),
    ("LaTeX tables", ["scripts/make_latex_tables.py"]),
    ("Final 300 figures", ["scripts/plot_final_300_results.py"]),
    ("Communication ablation figures", ["scripts/plot_comm_results.py"]),
    ("Per-seed appendix", ["scripts/build_paper_appendix.py"]),
    ("Edge feature ablation figure", ["scripts/plot_edge_feature_ablation.py"]),
    ("Speed robustness figures", ["scripts/plot_speed_robustness.py"]),
    ("Communication dropout figures", ["scripts/plot_comm_dropout_robustness.py"]),
    ("Radius interpolation figures", ["scripts/plot_radius_interpolation.py"]),
    ("Figure asset audit", ["scripts/audit_figure_assets.py"]),
    ("Evaluation budget audit", ["scripts/audit_evaluation_budget_consistency.py"]),
    ("Method naming audit", ["scripts/audit_method_naming_consistency.py"]),
    ("LAG graph synthetic smoke", ["scripts/lag_graph_smoke_test.py", "--mode", "synthetic", "--steps", "100"]),
    ("LAG JSBSim migration probe", ["scripts/probe_lag_jsbsim_migration.py"]),
    ("LAG role graph adapter test", ["scripts/test_lag_role_graph_adapter.py"]),
    ("LAG role graph wrapper test", ["scripts/test_lag_role_graph_wrapper.py"]),
    ("3DOF interception environment smoke", ["scripts/smoke_test_intercept_3d_env.py"]),
    ("3DOF RI-GMAPPO checkpoint evaluation", ["scripts/evaluate_ri_gmappo_3d.py"]),
    ("3DOF paper-facing main table", ["scripts/build_3d_paper_tables.py"]),
    ("3DOF manuscript figure assets", ["scripts/plot_3d_manuscript_figures.py"]),
    ("3DOF relay-failure case candidates", ["scripts/find_3d_relay_failure_case_candidates.py"]),
    ("3DOF relay-failure case replay", ["scripts/replay_3d_relay_failure_case.py"]),
    ("3DOF task-support ablation pilot summary", ["scripts/analyze_3d_task_support_ablation_pilot.py"]),
    ("3DOF formal task-support ablation summary", ["scripts/analyze_3d_task_support_ablation_formal.py"]),
    ("3DOF formal role-pair gate ablation summary", ["scripts/analyze_3d_role_pair_gate_ablation_formal.py"]),
    ("Reproducibility checksum manifest", ["scripts/write_reproducibility_checksum_manifest.py"]),
    ("Reproducibility checksum verification", ["scripts/verify_reproducibility_checksum_manifest.py"]),
    ("Supplemental CSV schema audit", ["scripts/audit_supplemental_csv_schema.py"]),
    ("Result provenance audit", ["scripts/audit_result_provenance.py"]),
    ("Submission package manifest refresh", ["scripts/write_submission_package_manifest.py"]),
    ("Supplemental data README refresh", ["scripts/write_supplemental_data_readme.py"]),
]

CHECK_STEPS = [
    ("LaTeX static check", ["scripts/check_latex_project.py"]),
    ("Quantitative claim consistency", ["scripts/check_paper_claim_consistency.py"]),
    ("English LaTeX consistency", ["scripts/check_english_latex_consistency.py"]),
    ("Paper text risk audit", ["scripts/check_paper_text_risk.py"]),
]

FINAL_CHECK_STEP = ("Reproducibility artifact gate", ["scripts/check_reproducibility_artifacts.py"])


def run_step(name: str, args: list[str]) -> StepResult:
    command = [str(PYTHON), *args]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return StepResult(
        name=name,
        command=command,
        returncode=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def status_text(result: StepResult) -> str:
    return "OK" if result.returncode == 0 else "FAILED"


def short_output(text: str, max_lines: int = 20) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join([*lines[:8], "...", *lines[-8:]])


def write_report(results: list[StepResult], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Paper Asset Build Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Regenerate paper tables/figures from existing result files and run non-training validation gates.",
        "This script does not retrain policies or rerun long evaluation jobs.",
        "```",
        "",
        "## Summary",
        "",
        "| Step | Status |",
        "|---|---|",
    ]
    for result in results:
        lines.append(f"| {result.name} | {status_text(result)} |")

    lines.extend(["", "## Step Details", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.name}",
                "",
                f"Status: `{status_text(result)}`",
                "",
                "Command:",
                "",
                "```text",
                " ".join(result.command),
                "```",
                "",
            ]
        )
        if result.stdout:
            lines.extend(["stdout:", "", "```text", short_output(result.stdout), "```", ""])
        if result.stderr:
            lines.extend(["stderr:", "", "```text", short_output(result.stderr), "```", ""])

    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate lightweight paper assets and run validation gates.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results: list[StepResult] = []

    for name, command in [*GENERATION_STEPS, *CHECK_STEPS]:
        result = run_step(name, command)
        results.append(result)
        write_report(results, args.report)
        print(f"{name}: {status_text(result)}", flush=True)
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    # Ensure the report exists before the artifact gate checks it.
    write_report(results, args.report)
    final_result = run_step(*FINAL_CHECK_STEP)
    results.append(final_result)
    write_report(results, args.report)
    print(f"{final_result.name}: {status_text(final_result)}", flush=True)
    if final_result.returncode != 0:
        raise SystemExit(final_result.returncode)


if __name__ == "__main__":
    main()
