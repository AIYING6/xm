"""Build a free-format Aerospace submission package from the frozen DRTP manuscript.

This generator is intentionally presentation-only.  It consumes the English
evidence-bounded manuscript and the already generated frozen figure assets.  It
does not touch results, re-score checkpoints, or alter any scientific claim.
"""

from __future__ import annotations

import html
import os
import re
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "q2_final_en"
FIG_SOURCE = ROOT / "paper" / "q2_final_en" / "submission_figures"
OUT = ROOT / os.environ.get("AEROSPACE_OUTPUT_DIR", "paper_submission_aerospace")
SECTIONS = (
    "02_problem_formulation.md",
    "03_introduction_related_work.md",
    "04_method.md",
    "05_experiments.md",
    "06_discussion.md",
    "07_conclusion.md",
)
MAIN_FIGURES = (
    ("fig1_relay_failure_topology_reconfiguration.png", "Figure 1. Relay-node failure changes the legal information and task-support path from Scout--Relay--Attacker to a direct Scout--Attacker path when that direct relation remains physically legal. This is a task-topology illustration, not a performance result."),
    ("fig2_utr_drtp_training_distribution.png", "Figure 2. UTR and DRTP share the same Single-Graph MAPPO backbone and nominal-condition anchor. DRTP changes only the bounded distribution over the six frozen failure/topology groups during training."),
    ("fig3_formal_primary_performance.png", "Figure 3. Formal paired five-seed performance at the common 10M checkpoint. Points show all training seeds; training seed is the independent unit."),
    ("fig4_ood_condition_decomposition.png", "Figure 4. Formal condition-wise decomposition over the ten frozen perturbation members. These members were within training support and are not presented as strict OOD results."),
    ("fig5_seed_reliability_and_safety.png", "Figure 5. Formal seed-level reliability and safety audit. The panel separates mission-score outcomes from collision, timeout, and failure-trigger validity."),
    ("fig6_adaptive_weight_telemetry.png", "Figure 6. DRTP sampler telemetry. These records verify altered training exposure but do not establish a causal policy mechanism."),
    ("fig7_formal_terminal_outcomes.png", "Figure 7. Formal terminal outcomes. Mission-score gains coincide with greater completion and lower timeout, while collision is reported separately as a trade-off."),
)


def normalize(text: str) -> str:
    """Make frozen Markdown readable to ReportLab without changing meaning."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("$", "")
    text = text.replace("\\mathrm{", "").replace("\\mathcal{", "")
    text = text.replace("\\operatorname{", "").replace("}", "}")
    text = text.replace("\\rightarrow", "→").replace("\\longrightarrow", "→")
    text = text.replace("\\times", "×").replace("\\leq", "≤").replace("\\geq", "≥")
    text = text.replace("\\Delta", "Δ")
    text = re.sub(r"([A-Za-z])_\{([^{}]+)\}", r"\1<sub>\2</sub>", text)
    text = text.replace("--", "–")
    return text


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("SubmissionTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=10),
        "subtitle": ParagraphStyle("SubmissionSubtitle", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=12),
        "abstract_head": ParagraphStyle("AbstractHead", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=13, spaceBefore=7, spaceAfter=4),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=17, spaceBefore=14, spaceAfter=7),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, spaceBefore=11, spaceAfter=5),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.2, alignment=TA_JUSTIFY, spaceAfter=6),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9.2, alignment=TA_JUSTIFY),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10, alignment=TA_JUSTIFY, textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=9),
        "equation": ParagraphStyle("Equation", parent=base["Code"], fontName="Courier", fontSize=7.5, leading=9.5, leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=6),
        "reference": ParagraphStyle("Reference", parent=base["BodyText"], fontName="Helvetica", fontSize=7.8, leading=9.5, leftIndent=12, firstLineIndent=-12, spaceAfter=3),
    }


def table_flowable(lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    rows = []
    for line in lines:
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", x.replace(" ", "")) for x in cells):
            continue
        rows.append([Paragraph(normalize(cell), styles["small"]) for cell in cells])
    columns = max(len(row) for row in rows)
    usable = A4[0] - 3.0 * cm
    widths = [usable / columns] * columns
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B7C9DD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def markdown_flowables(text: str, styles: dict[str, ParagraphStyle]) -> list:
    story, paragraph, table, equation = [], [], [], []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            story.append(Paragraph(normalize(" ".join(paragraph)), styles["body"]))
            paragraph = []

    def flush_table() -> None:
        nonlocal table
        if table:
            flush_paragraph()
            story.append(Spacer(1, 3))
            story.append(table_flowable(table, styles))
            story.append(Spacer(1, 7))
            table = []

    def flush_equation() -> None:
        nonlocal equation
        if equation:
            story.append(Paragraph(normalize("<br/>".join(equation)), styles["equation"]))
            equation = []

    in_equation = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip() == "\\[":
            flush_paragraph(); flush_table(); in_equation = True; continue
        if line.strip() == "\\]":
            in_equation = False; flush_equation(); continue
        if in_equation:
            equation.append(line)
            continue
        if line.startswith("|"):
            table.append(line)
            continue
        flush_table()
        if not line.strip():
            flush_paragraph()
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            style = {1: "h1", 2: "h2", 3: "h3"}[len(heading.group(1))]
            story.append(Paragraph(normalize(heading.group(2)), styles[style]))
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            flush_paragraph()
            story.append(Paragraph(normalize(f"**{numbered.group(1)}.** {numbered.group(2)}"), styles["body"]))
            continue
        paragraph.append(line.strip())
    flush_paragraph(); flush_table(); flush_equation()
    return story


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(1.5 * cm, 1.15 * cm, "Aerospace free-format submission draft | DRTP relay-failure UAV coordination")
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.15 * cm, f"Page {doc.page}")
    canvas.restoreState()


def add_figure(story: list, filename: str, caption: str, styles: dict[str, ParagraphStyle]) -> None:
    image_path = OUT / "figures" / filename
    image = Image(str(image_path))
    max_width, max_height = A4[0] - 3.0 * cm, 11.2 * cm
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
    image.drawWidth, image.drawHeight = image.imageWidth * scale, image.imageHeight * scale
    story.append(KeepTogether([image, Paragraph(caption, styles["caption"])]))


def copy_figures() -> None:
    destination = OUT / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    for filename, _ in MAIN_FIGURES:
        shutil.copy2(FIG_SOURCE / filename, destination / filename)
    shutil.copy2(FIG_SOURCE / "figS1_training_diagnostics.png", destination / "figS1_training_diagnostics.png")


def source_to_tex(text: str) -> str:
    def tex_cell(value: str) -> str:
        value = re.sub(r"`([^`]+)`", r"\\texttt{\1}", value)
        return value.replace("%", r"\%").replace("&", r"\&")

    output: list[str] = []
    in_table = False
    for raw in text.splitlines():
        line = raw.rstrip()
        match = re.match(r"^(#{1,3})\s+(.*)$", line)
        if match:
            command = {1: "section", 2: "subsection", 3: "subsubsection"}[len(match.group(1))]
            output.append(f"\\{command}{{{match.group(2)}}}")
            continue
        if line.startswith("|"):
            if not in_table:
                output.extend(["\\begin{center}", "\\begin{tabular}{" + "l" * len(line.strip("|").split("|")) + "}", "\\toprule"])
                in_table = True
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                output.append("\\midrule")
            else:
                escaped = " & ".join(tex_cell(cell) for cell in cells)
                output.append(escaped + " \\\\")
            continue
        if in_table:
            output.extend(["\\bottomrule", "\\end{tabular}", "\\end{center}"])
            in_table = False
        if line.startswith("#"):
            continue
        if line:
            output.append(tex_cell(line))
        else:
            output.append("")
    if in_table:
        output.extend(["\\bottomrule", "\\end{tabular}", "\\end{center}"])
    return "\n".join(output)


def write_latex_sources() -> None:
    sections_dir = OUT / "latex" / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    for source_name in SECTIONS:
        tex_name = source_name.replace(".md", ".tex")
        (sections_dir / tex_name).write_text(source_to_tex((SOURCE / source_name).read_text(encoding="utf-8")), encoding="utf-8")
    references = (SOURCE / "08_references.md").read_text(encoding="utf-8").splitlines()[2:]
    ref_lines = ["\\begin{thebibliography}{99}"]
    for index, line in enumerate(references, 1):
        if line.strip():
            ref_lines.append(f"\\bibitem{{ref{index}}} {line}")
    ref_lines.append("\\end{thebibliography}")
    (OUT / "latex" / "references.tex").write_text("\n".join(ref_lines) + "\n", encoding="utf-8")
    figure_lines = []
    for index, (filename, caption) in enumerate(MAIN_FIGURES, 1):
        figure_lines.extend([
            "\\begin{figure}[htbp]", "\\centering", f"\\includegraphics[width=\\linewidth]{{../figures/{filename}}}",
            f"\\caption{{{caption}}}", f"\\label{{fig:drtp-{index}}}", "\\end{figure}",
        ])
    (OUT / "latex" / "figures.tex").write_text("\n".join(figure_lines) + "\n", encoding="utf-8")
    main = r"""% Aerospace free-format initial-submission manuscript.
% Aerospace accepts free-format initial submissions.  Before upload, replace all
% AUTHOR_INPUT_NEEDED fields with author-confirmed information and, if desired,
% transfer this source to the current official MDPI template.
\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,booktabs,graphicx,hyperref}
\title{Bounded Adaptive Topology-Perturbation Reweighting for Relay-Failure UAV Coordination}
\author{AUTHOR\_INPUT\_NEEDED: authors, affiliations, corresponding author}
\date{}
\begin{document}
\maketitle
\begin{abstract}
""" + (SOURCE / "01_abstract.md").read_text(encoding="utf-8").replace("# Abstract", "").strip() + r"""
\end{abstract}
\noindent\textbf{Keywords:} multi-agent reinforcement learning; unmanned aerial vehicles; relay-node failure; graph coordination; adaptive training distribution; robustness
\input{sections/03_introduction_related_work.tex}
\input{sections/02_problem_formulation.tex}
\input{sections/04_method.tex}
\input{sections/05_experiments.tex}
\input{figures.tex}
\input{sections/06_discussion.tex}
\input{sections/07_conclusion.tex}
\section*{Author Contributions}
AUTHOR\_INPUT\_NEEDED.
\section*{Funding}
AUTHOR\_INPUT\_NEEDED.
\section*{Data Availability Statement}
An anonymous reproducibility package is technically staged. AUTHOR\_INPUT\_NEEDED: external reviewer-access URL, licence, checkpoint access policy, and access date.
\section*{Conflicts of Interest}
AUTHOR\_INPUT\_NEEDED.
\input{references.tex}
\end{document}
"""
    (OUT / "latex" / "main.tex").write_text(main, encoding="utf-8")


def build_main_pdf(styles: dict[str, ParagraphStyle]) -> None:
    path = OUT / "DRTP_Aerospace_Anonymous_Manuscript.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.45 * cm, bottomMargin=1.75 * cm, title="Bounded Adaptive Topology-Perturbation Reweighting for Relay-Failure UAV Coordination")
    story = [
        Paragraph("Bounded Adaptive Topology-Perturbation Reweighting for Relay-Failure UAV Coordination", styles["title"]),
        Paragraph("Aerospace | Article | Anonymous free-format initial-submission draft", styles["subtitle"]),
        Paragraph("AUTHOR_INPUT_NEEDED: author names, affiliations, corresponding author, funding, acknowledgements, conflicts, and external anonymous repository URL.", styles["small"]),
        Spacer(1, 6), Paragraph("Abstract", styles["abstract_head"]),
    ]
    abstract = (SOURCE / "01_abstract.md").read_text(encoding="utf-8").replace("# Abstract", "").strip()
    story.extend(markdown_flowables(abstract, styles))
    story.append(Paragraph("Keywords: multi-agent reinforcement learning; unmanned aerial vehicles; relay-node failure; graph coordination; adaptive training distribution; robustness", styles["body"]))
    injected = {"02_problem_formulation.md": 0, "04_method.md": 1, "05_experiments.md": 2}
    for source_name in SECTIONS:
        story.extend(markdown_flowables((SOURCE / source_name).read_text(encoding="utf-8"), styles))
        if source_name in injected:
            add_figure(story, *MAIN_FIGURES[injected[source_name]], styles)
        if source_name == "05_experiments.md":
            for figure in MAIN_FIGURES[3:]:
                add_figure(story, *figure, styles)
    story.append(Paragraph("Author Contributions", styles["h1"]))
    story.append(Paragraph("AUTHOR_INPUT_NEEDED: CRediT roles, author initials, and confirmation from all authors.", styles["body"]))
    story.append(Paragraph("Funding", styles["h1"]))
    story.append(Paragraph("AUTHOR_INPUT_NEEDED: funder names, grant numbers, and any sponsor-role statement.", styles["body"]))
    story.append(Paragraph("Data Availability Statement", styles["h1"]))
    story.append(Paragraph("The local anonymous reproducibility package has passed its technical staging checks. AUTHOR_INPUT_NEEDED: a live reviewer-access URL, licence, checkpoint/runtime-state access policy, and external download verification before submission.", styles["body"]))
    story.append(Paragraph("Conflicts of Interest", styles["h1"]))
    story.append(Paragraph("AUTHOR_INPUT_NEEDED: conflict-of-interest declaration confirmed by all authors.", styles["body"]))
    story.append(Paragraph("References", styles["h1"]))
    for line in (SOURCE / "08_references.md").read_text(encoding="utf-8").splitlines()[2:]:
        if line.strip():
            story.append(Paragraph(normalize(line), styles["reference"]))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_supplement_pdf(styles: dict[str, ParagraphStyle]) -> None:
    path = OUT / "DRTP_Aerospace_Supplementary_Information.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.45 * cm, bottomMargin=1.75 * cm, title="Supplementary Information")
    story = [
        Paragraph("Supplementary Information", styles["title"]),
        Paragraph("Bounded Adaptive Topology-Perturbation Reweighting for Relay-Failure UAV Coordination", styles["subtitle"]),
    ]
    story.extend(markdown_flowables((SOURCE / "11_supplementary_information.md").read_text(encoding="utf-8"), styles))
    add_figure(story, "figS1_training_diagnostics.png", "Figure S1. Training and PPO diagnostics for the completed formal trajectories. These records provide training-discipline context and are not used for checkpoint promotion or common-distribution performance comparison.", styles)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def write_journal_decision() -> None:
    content = """# A-line journal decision

## Frozen submission order

1. **Primary:** *Aerospace* (MDPI), Article.
2. **Backup:** *Robotics* (MDPI), Article.

## Rationale

The manuscript studies a three-UAV relay-failure coordination task, lightweight 3DOF aircraft motion, graph-structured MARL, relay-path reconfiguration, mission performance, and reliability/safety outcomes. *Aerospace* directly lists artificial intelligence, aerospace-vehicle operation/control/maintenance, and risk/reliability within scope. Its official July 2026 statistics identify it as JCR Q2 in Engineering, Aerospace and CiteScore Q2 in Aerospace Engineering. *Robotics* is a direct topical backup for multi-agent coordination and is currently listed by its publisher as JCR Q2 in Robotics.

The primary manuscript is prepared as an **Aerospace Article**. Aerospace permits free-format initial submission but requires the standard research sections and required declarations. The generated source preserves those sections and retains author-owned fields as explicit placeholders rather than inventing them.

## Do not change without author approval

- The formal and independent cohorts remain separate evidence strata.
- The independent cohort reversal remains visible in the abstract, Results, Discussion, Conclusion, and Supplementary Information.
- No B-line candidate is promoted into the main method.
- No author, funding, repository, licence, or reviewer information is inferred from project files.
"""
    (OUT / "JOURNAL_DECISION.md").write_text(content, encoding="utf-8")


def write_readme() -> None:
    content = """# DRTP Aerospace submission package

This directory is an independent, presentation-only submission package for the frozen A-line DRTP paper. It does not reuse the legacy `paper_latex_3d_en/` EA-RG-MAPPO manuscript.

## Contents

- `DRTP_Aerospace_Anonymous_Manuscript.pdf`: anonymous free-format main manuscript.
- `DRTP_Aerospace_Supplementary_Information.pdf`: supplementary information.
- `latex/main.tex`: LaTeX source structured for an *Aerospace* Article.
- `latex/sections/`: generated section sources.
- `figures/`: copied frozen publication figures.
- `JOURNAL_DECISION.md`: primary and backup journal rationale.

## Before actual upload

Replace every `AUTHOR_INPUT_NEEDED` marker using author-confirmed information. Then provide a genuine external reviewer-access route for the anonymous reproducibility package and run the project release gate. The official *Aerospace* author instructions permit free-format initial submission; an optional transfer to the current MDPI LaTeX class can be completed after author metadata are supplied.
"""
    (OUT / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite existing submission package: {OUT}")
    OUT.mkdir(parents=True)
    copy_figures()
    write_latex_sources()
    write_journal_decision()
    write_readme()
    styles = build_styles()
    build_main_pdf(styles)
    build_supplement_pdf(styles)
    print(OUT)


if __name__ == "__main__":
    main()
