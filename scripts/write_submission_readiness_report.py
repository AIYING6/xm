from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "submission_readiness_report.md"


REQUIRED_MANUSCRIPT_FILES = [
    "paper_latex/main.tex",
    "paper_latex_en/main.tex",
    "docs/paper_manuscript_zh_v1.md",
    "docs/english_manuscript_draft.md",
]


REQUIRED_EVIDENCE_FILES = [
    "results/final_comm_300_summary.csv",
    "results/latex_final_comm_300_table.tex",
    "results/latex_ablation_comm_table.tex",
    "results/latex_speed_robustness_table.tex",
    "results/latex_edge_feature_ablation_table.tex",
    "results/figures/final_300_success_rate.png",
    "results/figures/final_300_collision_rate.png",
    "results/figures/method_overview_ea_rg_mappo_s.png",
]


REQUIRED_REPRO_FILES = [
    "docs/reproducibility_manifest.md",
    "docs/reproducibility_checksum_manifest.md",
    "docs/reproducibility_checksum_verification.md",
    "docs/runtime_environment_report.md",
    "docs/checkpoint_inventory.md",
    "docs/paper_asset_build_report.md",
    "results/reproducibility_checksum_manifest.csv",
    "results/reproducibility_checksum_verification.csv",
    "scripts/build_paper_assets.py",
    "scripts/check_latex_project.py",
    "scripts/check_paper_claim_consistency.py",
    "scripts/check_english_latex_consistency.py",
    "scripts/check_paper_text_risk.py",
    "scripts/check_reproducibility_artifacts.py",
    "scripts/write_reproducibility_checksum_manifest.py",
    "scripts/verify_reproducibility_checksum_manifest.py",
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


def load_final_ea_results() -> list[dict[str, str]]:
    path = ROOT / "results" / "final_comm_300_summary.csv"
    with path.open("r", encoding="utf-8", newline="") as f:
        return [row for row in csv.DictReader(f) if row["method"] == "EA-RG-MAPPO-S"]


def final_result_summary() -> tuple[list[str], list[str]]:
    rows = load_final_ea_results()
    lines = []
    warnings = []
    for row in rows:
        radius = float(row["radius"])
        success = float(row["success_mean"])
        success_std = float(row["success_std"])
        collision = float(row["collision_mean"])
        collision_std = float(row["collision_std"])
        lines.append(
            f"| {radius:.0f} | {success:.3f} ± {success_std:.3f} | "
            f"{collision:.3f} ± {collision_std:.3f} |"
        )
        if success < 0.85:
            warnings.append(f"success below readiness threshold at radius={radius:.0f}: {success:.3f}")
        if collision > 0.10:
            warnings.append(f"collision above readiness threshold at radius={radius:.0f}: {collision:.3f}")
    if len(rows) != 4:
        warnings.append(f"expected 4 EA-RG-MAPPO-S final rows, got {len(rows)}")
    return lines, warnings


def runtime_limitations() -> list[str]:
    report = ROOT / "docs" / "runtime_environment_report.md"
    if not report.exists():
        return ["runtime environment report is missing"]
    text = report.read_text(encoding="utf-8")
    limits = []
    for tool in ["xelatex", "latexmk", "bibtex"]:
        if f"{tool}: not found" in text:
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
        "Current strongest claim: EA-RG-MAPPO-S improves limited-communication stability and reduces collision in simplified 2D heterogeneous UAV pursuit.",
        "Boundary: full 6DOF air combat, missile/radar modeling, and human-UAV teaming have not been experimentally validated yet.",
        "```",
        "",
        "## Main Evidence",
        "",
        "| Radius | EA-RG-MAPPO-S Success | EA-RG-MAPPO-S Collision |",
        "|---:|---:|---:|",
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
        lines.append("None. Final EA-RG-MAPPO-S success/collision values satisfy the current readiness thresholds.")

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
            "1. Compile `paper_latex/main.tex` and `paper_latex_en/main.tex` in an environment with `xelatex`, `bibtex`, and a full LaTeX distribution.",
            "2. Perform visual PDF layout checks for tables, figures, captions, and references.",
            "3. Choose the target journal/template and adapt the English LaTeX project accordingly.",
            "4. If the target venue expects stronger statistics, extend the final comparison to five seeds or add a small LAG/JSBSim migration experiment.",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
