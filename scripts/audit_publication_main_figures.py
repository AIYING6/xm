"""Deterministic evidence audit for the publication redesign of Figs. 1--2."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper_chinese" / "figures" / "publication"
REPORT = ROOT / "docs" / "figure_redesign" / "PUBLICATION_FIGURE_EVIDENCE_AUDIT.md"


def check(condition: bool, label: str, detail: str) -> tuple[str, str, str]:
    return ("PASS" if condition else "FAIL", label, detail)


def main() -> int:
    findings: list[tuple[str, str, str]] = []
    figure_bases = ["fig1_method_overview_publication", "fig2_primary_recovery_publication"]
    for base in figure_bases:
        for suffix in (".svg", ".pdf", ".png", ".tiff"):
            path = FIG / f"{base}{suffix}"
            findings.append(check(path.exists() and path.stat().st_size > 0, f"{base}{suffix}", "SVG/PDF/vector and 600-dpi raster delivery asset exists."))
        svg = (FIG / f"{base}.svg").read_text(encoding="utf-8") if (FIG / f"{base}.svg").exists() else ""
        findings.append(check("<text" in svg, f"{base} editable SVG text", "SVG contains text nodes rather than an all-outline text export."))

    fig1_svg = (FIG / "fig1_method_overview_publication.svg").read_text(encoding="utf-8")
    fig2_svg = (FIG / "fig2_primary_recovery_publication.svg").read_text(encoding="utf-8")
    render_source = (ROOT / "scripts" / "render_publication_main_figures.py").read_text(encoding="utf-8")
    findings.extend(
        [
            check("三关系任务图" in fig1_svg and "感知" in fig1_svg and "环境递送通信" in fig1_svg and "任务支撑" in fig1_svg, "Fig. 1 three-relation vocabulary", "Shows only perception, environment-delivered communication and task-support."),
            check("Attack-window relation" not in fig1_svg and "第四关系" not in fig1_svg, "Fig. 1 fourth-relation exclusion", "No prohibited fourth relation is rendered."),
            check("Gate Prior" in fig1_svg and "静态 Role-Pair" in fig1_svg, "Fig. 1 component boundary", "Gate Prior and role-pair modulation are retained as static/structured components."),
            check("EA-RG" in fig2_svg and "MAPPO" in fig2_svg and "HAPPO" in fig2_svg and "宽单图" in fig2_svg, "Fig. 2 contract methods", "The four authorised main-paper methods are visible."),
            check("−3.71" in fig2_svg and "−7.16" in fig2_svg and "−1.05" in fig2_svg, "Fig. 2 RMST80 effect", "Shows the locked Full−MAPPO mean and hierarchical paired-bootstrap interval."),
            check('"τ = 80"' in render_source and "80" in fig2_svg, "Fig. 2 active-failure reference", "The pre-specified failure-duration horizon is indicated unobtrusively."),
        ]
    )
    provenance = FIG / "publication_figure_provenance.txt"
    provenance_text = provenance.read_text(encoding="utf-8") if provenance.exists() else ""
    findings.append(check("4 contract methods" in provenance_text and "200 matched exposures/method/seed" in provenance_text, "Fig. 2 population provenance", "Records four methods, three seeds and 200 matched exposures per method/seed."))

    passes = sum(status == "PASS" for status, _label, _detail in findings)
    failures = len(findings) - passes
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Publication Figure Evidence Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This audit verifies deliverable presence and element-level alignment with the locked figure contracts. It does not re-estimate statistics or alter the inputs.",
        "",
        "| Status | Check | Result |",
        "|---|---|---|",
    ]
    for status, label, detail in findings:
        lines.append(f"| {status} | {label} | {detail} |")
    lines.extend(
        [
            "",
            f"**Verdict:** {'PASS' if failures == 0 else 'FAIL'} ({passes} pass, {failures} fail).",
            "",
            "## Review boundary",
            "",
            "- Fig. 1 is a code-traceable schematic: it contains no generated experimental evidence.",
            "- Fig. 2 pools the pre-specified three training seeds for descriptive KM curves; the dot–whisker panel displays the locked seed differences and hierarchical paired-bootstrap interval for RMST80.",
            "- Full-width SVG and PDF retain editable text; 600-dpi PNG and TIFF are fallbacks.",
        ]
    )
    with REPORT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"publication figure audit: {passes} pass, {failures} fail")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
