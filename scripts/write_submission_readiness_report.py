from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "submission_readiness_report.md"


REQUIRED_MANUSCRIPT_FILES = [
    "paper_latex_3d_en/main.tex",
    "paper_latex_3d_en/references.bib",
    "paper_latex_3d_en/sections/01_introduction.tex",
    "paper_latex_3d_en/sections/02_related_work.tex",
    "paper_latex_3d_en/sections/03_problem.tex",
    "paper_latex_3d_en/sections/04_method.tex",
    "paper_latex_3d_en/sections/05_experiments.tex",
    "paper_latex_3d_en/sections/06_discussion.tex",
    "paper_latex_3d_en/sections/07_conclusion.tex",
]


REQUIRED_EVIDENCE_FILES = [
    "docs/intercept_3d_gate1_hardened_safety_5seed_fixed_update60_summary.md",
    "docs/gate1_safety_fx60_paper_tables.md",
    "docs/gate1_safety_fx60_mechanism/failure_aligned_mechanism_summary.md",
    "docs/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_summary.md",
    "docs/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_summary.md",
    "docs/gate1_safety_fx60_failure_timing_generalization_formal_evidence.md",
    "results/gate1_safety_fx60_paper_tables/main_results.csv",
    "results/gate1_safety_fx60_paper_tables/ablation_results.csv",
    "results/gate1_safety_fx60_paper_tables/seed_aware_deltas.csv",
    "results/gate1_safety_fx60_paper_tables/main_results_latex.tex",
    "results/gate1_safety_fx60_paper_tables/ablation_results_latex.tex",
    "results/gate1_safety_fx60_paper_tables/seed_aware_deltas_latex.tex",
    "results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_summary.csv",
    "results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_generalization_latex.tex",
    "results/figures/gate1_safety_fx60_mechanism_curves.png",
    "results/figures/gate1_safety_fx60_representative_case_timeline.png",
]


REQUIRED_REPRO_FILES = [
    "AGENTS.md",
    "docs/PROJECT_STATE.md",
    "docs/ROADMAP.md",
    "docs/gate1_communication_feasibility_audit.md",
    "docs/actor_critic_observation_boundary.md",
    "docs/gate1_target_freshness_audit.md",
    "docs/gate1_graph_information_audit.md",
    "docs/gate1_safety_fx60_manuscript_consistency_audit.md",
    "docs/gate1_safety_fx60_contribution_evidence_alignment.md",
    "docs/gate1_safety_fx60_method_component_audit.md",
    "docs/gate1_safety_fx60_pdf_readiness_audit.md",
    "docs/gate1_safety_fx60_model_cost_report.md",
    "docs/english_manuscript_readiness_audit.md",
    "docs/latex_reference_integrity_audit.md",
    "results/latex_reference_integrity_audit.csv",
    "results/gate1_safety_fx60_model_costs/model_costs.csv",
    "scripts/check_latex_project.py",
    "scripts/check_paper_claim_consistency.py",
    "scripts/check_english_latex_consistency.py",
    "scripts/audit_latex_reference_integrity.py",
    "scripts/audit_english_manuscript_readiness.py",
    "scripts/build_gate1_safety_fx60_paper_tables.py",
    "scripts/write_submission_readiness_report.py",
]


def exists_status(rel_paths: list[str]) -> tuple[list[str], list[str]]:
    present = []
    missing = []
    for rel in rel_paths:
        path = ROOT / rel
        if path.exists() and path.stat().st_size > 0:
            present.append(rel)
        else:
            missing.append(rel)
    return present, missing


def load_gate1_results() -> list[dict[str, str]]:
    path = ROOT / "results" / "gate1_safety_fx60_paper_tables" / "main_results.csv"
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_gate1_seed_aware_rows() -> list[dict[str, str]]:
    path = ROOT / "results" / "gate1_safety_fx60_paper_tables" / "seed_aware_deltas.csv"
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt_percent(value: str) -> str:
    return f"{100.0 * float(value):.1f}"


def final_result_summary() -> tuple[list[str], list[str]]:
    rows = load_gate1_results()
    lines = []
    warnings = []
    for row in rows:
        method = row["label"]
        recovery = float(row["recovery_mean"])
        recovery_sd = float(row["recovery_sd"])
        tracking = float(row["tracking_mean"])
        chain = float(row["chain_mean"])
        collision = float(row["collision_mean"])
        lines.append(
            f"| {method} | {100.0 * recovery:.1f} ± {100.0 * recovery_sd:.1f} | "
            f"{100.0 * tracking:.1f} | {100.0 * chain:.1f} | {100.0 * collision:.1f} |"
        )
        if row["method"] == "multi_relation" and recovery < 0.80:
            warnings.append(f"full-method recovery below 80% readiness threshold: {recovery:.3f}")
        if row["method"] == "multi_relation" and collision > 0.02:
            warnings.append(f"full-method collision above 2% readiness threshold: {collision:.3f}")
    if len(rows) != 3:
        warnings.append(f"expected 3 Gate1 main-result rows, got {len(rows)}")
    for row in load_gate1_seed_aware_rows():
        if row["comparison"] == "multi_relation_vs_single" and row["metric"] == "post_failure_chain_recovered":
            if float(row["delta_ci_low"]) <= 0.0:
                warnings.append("full-vs-single recovery interval is not separated from zero")
    return lines, warnings


def runtime_limitations() -> list[str]:
    limits = []
    for tool in ["xelatex", "latexmk", "bibtex"]:
        if shutil.which(tool) is None:
            limits.append(f"{tool} is not available in the current runtime")
    if not limits:
        limits.append("LaTeX toolchain appears available in the runtime report")
    return limits


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manuscript_present, manuscript_missing = exists_status(REQUIRED_MANUSCRIPT_FILES)
    evidence_present, evidence_missing = exists_status(REQUIRED_EVIDENCE_FILES)
    repro_present, repro_missing = exists_status(REQUIRED_REPRO_FILES)
    result_lines, result_warnings = final_result_summary()
    tool_limits = runtime_limitations()

    blocking_missing = manuscript_missing + evidence_missing + repro_missing
    blocking_warnings = result_warnings
    pdf_blocked = any("not available" in item for item in tool_limits)

    if not blocking_missing and not blocking_warnings:
        readiness = "Research manuscript package is internally consistent and evidence-backed."
    else:
        readiness = "Research manuscript package still has blocking internal gaps."

    if pdf_blocked:
        submission_status = (
            "Not final submission-ready in this runtime because PDF rendering cannot be verified "
            "without a LaTeX toolchain."
        )
    else:
        submission_status = "Ready for PDF rendering and journal-template formatting checks."

    lines = [
        "# Submission Readiness Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        "```text",
        readiness,
        submission_status,
        "Current strongest claim: EA-RG-MAPPO-S improves post-relay-failure kill-chain recovery in a hardened 3DOF strict-sensing, limited-communication heterogeneous UAV task.",
        "Boundary: full 4v2 red-blue combat, 6DOF JSBSim execution, online missile closure, high-fidelity radar, and human-UAV teaming have not been experimentally validated yet.",
        "```",
        "",
        "## Main Evidence",
        "",
        "| Method | Recovery | Tracking | Chain | Collision |",
        "|---|---:|---:|---:|---:|",
        *result_lines,
        "",
        "## Material Coverage",
        "",
        "| Category | Present | Missing |",
        "|---|---:|---:|",
        f"| Manuscripts | {len(manuscript_present)} | {len(manuscript_missing)} |",
        f"| Result evidence | {len(evidence_present)} | {len(evidence_missing)} |",
        f"| Reproducibility gates | {len(repro_present)} | {len(repro_missing)} |",
        "",
        "## Missing Internal Artifacts",
        "",
    ]
    if blocking_missing:
        lines.extend(f"- `{rel}`" for rel in blocking_missing)
    else:
        lines.append("None.")

    lines.extend(["", "## Quantitative Warnings", ""])
    if result_warnings:
        lines.extend(f"- {warning}" for warning in result_warnings)
    else:
        lines.append("None. Full EA-RG-MAPPO-S recovery/collision values and full-vs-single separation satisfy the current readiness thresholds.")

    lines.extend(["", "## Runtime and Submission Limitations", ""])
    lines.extend(f"- {item}" for item in tool_limits)
    lines.extend(
        [
            "- PDF layout has not been verified in the current runtime.",
            "- Journal-specific template formatting has not been performed.",
            "- Real LAG/JSBSim smoke testing remains blocked until the missing JSBSim data/submodule is available.",
            "",
            "## Recommended Next Actions",
            "",
            "1. Compile `paper_latex_3d_en/main.tex` in an environment with `xelatex`, `bibtex`, and a full LaTeX distribution.",
            "2. Perform visual PDF layout checks for tables, figures, captions, and references.",
            "3. Choose the target journal/template and adapt the English LaTeX project accordingly.",
            "4. If the target venue expects stronger realism, add a limited 5v2 or LAG/JSBSim replay extension after the 3v1 manuscript is stable.",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
