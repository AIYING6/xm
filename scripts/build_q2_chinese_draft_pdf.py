"""Build a pre-submission Chinese PDF from the frozen Markdown manuscript.

This is a layout export only. It does not modify results, figures, data, or the
manuscript text.  Equations are converted to readable plain-text math for this
pre-submission scientific version; target-journal LaTeX/Word typesetting remains a later
formatting step.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "q2_final_zh"
SOURCE = PAPER / "main_zh.md"
OUT = PAPER / "output" / "DRTP_SG_MAPPO_中文论文终稿_投稿前审稿版.pdf"
FONT = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("NotoSansSC", str(FONT)))
    # A CJK-capable font is safer for formula annotations containing Chinese.
    pdfmetrics.registerFont(TTFont("NotoSansSCBold", str(FONT)))


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("ZhTitle", parent=base["Title"], fontName="NotoSansSCBold",
                                fontSize=20, leading=28, alignment=TA_CENTER,
                                textColor=colors.HexColor("#102a43"), spaceAfter=13),
        "status": ParagraphStyle("ZhStatus", parent=base["Normal"], fontName="NotoSansSC",
                                 fontSize=8.5, leading=13, alignment=TA_CENTER,
                                 textColor=colors.HexColor("#52606d"), spaceAfter=14),
        "h1": ParagraphStyle("ZhH1", parent=base["Heading1"], fontName="NotoSansSCBold",
                             fontSize=15, leading=21, textColor=colors.HexColor("#102a43"),
                             spaceBefore=16, spaceAfter=8, keepWithNext=True),
        "h2": ParagraphStyle("ZhH2", parent=base["Heading2"], fontName="NotoSansSCBold",
                             fontSize=12, leading=18, textColor=colors.HexColor("#1f4e79"),
                             spaceBefore=12, spaceAfter=6, keepWithNext=True),
        "body": ParagraphStyle("ZhBody", parent=base["BodyText"], fontName="NotoSansSC",
                                fontSize=9.5, leading=16, alignment=TA_JUSTIFY,
                                firstLineIndent=18, spaceAfter=5, wordWrap="CJK"),
        "body_noindent": ParagraphStyle("ZhBodyNoIndent", parent=base["BodyText"], fontName="NotoSansSC",
                                         fontSize=9.2, leading=15, alignment=TA_JUSTIFY,
                                         spaceAfter=5, wordWrap="CJK"),
        "caption": ParagraphStyle("ZhCaption", parent=base["BodyText"], fontName="NotoSansSC",
                                   fontSize=8, leading=12, alignment=TA_CENTER,
                                   textColor=colors.HexColor("#334e68"), spaceAfter=8, wordWrap="CJK"),
        "equation": ParagraphStyle("Equation", parent=base["BodyText"], fontName="NotoSansSC",
                                    fontSize=8.2, leading=12, leftIndent=14, rightIndent=14,
                                    textColor=colors.HexColor("#243b53"), backColor=colors.HexColor("#f4f7fb"),
                                    borderColor=colors.HexColor("#d9e2ec"), borderWidth=.4,
                                    borderPadding=5, spaceBefore=5, spaceAfter=7),
    }


def inline(text: str) -> str:
    text = plain_math(text)
    text = escape(text)
    # Backticks frequently wrap Chinese author-input placeholders. Rendering the
    # content in Courier would silently drop CJK glyphs, so preserve it as text.
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text.replace("\\(", "").replace("\\)", "")


EQUATION_REPLACEMENTS = {
    "G_t=(V,E_t,X_t,Z_t),": "G_t = (V, E_t, X_t, Z_t)",
    "A_t[i,j]=1": "A_t[i, j] = 1",
    "t_f=44,\\qquad d_f=80.": "t_f = 44；d_f = 80。",
    "0\\rightarrow1\\rightarrow2\n\\quad\\longrightarrow\\quad\n0\\rightarrow2,": "0 → 1 → 2  重构为  0 → 2",
    "J_{\\mathrm{nominal}},\\qquad J_{F0},": "J_nominal，J_F0",
    "J_{\\mathrm{pert,mean}}=\\frac{1}{10}\\sum_{c\\in\\mathcal C_{\\mathrm{pert}}}J_c,\n\\qquad\nJ_{\\mathrm{pert,worst}}=\\min_{c\\in\\mathcal C_{\\mathrm{pert}}}J_c.": "J_pert,mean = 十个冻结跨扰动条件任务得分的平均值；J_pert,worst = 十个条件中的最小任务得分。",
    "\\Delta J_c=J_{\\mathrm{nominal}}-J_c.": "ΔJ_c = J_nominal − J_c",
    "V_{\\mathrm{trigger},c}=\n\\frac{\\#\\{\\text{在 }R_c\\text{ 中正确触发故障的 episodes}\\}}\n{|R_c|}.": "V_trigger,c = 风险集 R_c 内正确触发故障的 episode 数 / |R_c|",
    "a_{i,t}\\sim\\pi_\\theta(a_{i,t}\\mid o_{i,t},G_{i,t}).": "a_i,t ∼ π_θ(a_i,t | o_i,t, G_i,t)",
    "\\mathcal G=\\{N,F0,TE,TL,DS,DL,CP\\}.": "训练组 G = {N, F0, TE, TL, DS, DL, CP}",
    "p_N=0.50.": "p_N = 0.50",
    "q_k^{\\mathrm{UTR}}=\\frac{1}{6},\\qquad\np_k^{\\mathrm{UTR}}=(1-p_N)q_k^{\\mathrm{UTR}}=\\frac{1}{12}.": "q_k(UTR) = 1/6；p_k(UTR) = (1 − p_N)q_k = 1/12",
    "\\max_\\theta\\left[\np_NJ_N(\\theta)+(1-p_N)\n\\min_{q\\in\\mathcal Q}\\sum_{k\\in\\mathcal F}q_kJ_k(\\theta)\n\\right],": "max_θ [ p_N·J_N(θ) + (1 − p_N)·min_{q∈Q} Σ_{k∈F} q_k·J_k(θ) ]",
    "\\mathcal Q=\\left\\{q\\in\\Delta^6:0.05\\le q_k\\le0.35\\right\\}.": "Q = {q ∈ Δ⁶：0.05 ≤ q_k ≤ 0.35}",
    "\\bar J_{k,u}=(1-\\kappa)\\bar J_{k,u-1}+\\kappa\\widehat J_{k,u};": "J̄_k,u = (1 − κ)J̄_k,u−1 + κĴ_k,u",
    "d_{k,u}=\\operatorname{clip}\\!\\left(\n\\frac{\\bar J_{N,u}-\\bar J_{k,u}}\n{\\max(|\\bar J_{N,u}|,\\epsilon)},0,d_{\\max}\n\\right),": "d_k,u = clip((J̄_N,u − J̄_k,u) / max(|J̄_N,u|, ε), 0, d_max)",
    "\\tilde d_{k,u}=d_{k,u}-\\frac{1}{6}\\sum_{j\\in\\mathcal F}d_{j,u}.": "d̃_k,u = d_k,u − (1/6)Σ_{j∈F} d_j,u",
    "\\tilde q_{k,u+1}=\n\\frac{q_{k,u}\\exp(\\eta\\tilde d_{k,u})}\n{\\sum_{j\\in\\mathcal F}q_{j,u}\\exp(\\eta\\tilde d_{j,u})},": "q̃_k,u+1 = q_k,u·exp(ηd̃_k,u) / Σ_{j∈F}[q_j,u·exp(ηd̃_j,u)]",
    "q_{u+1}=\\Pi_{\\mathcal Q}\\left[(1-\\beta)q_u+\\beta\\tilde q_{u+1}\\right].": "q_u+1 = Π_Q[(1 − β)q_u + βq̃_u+1]",
    "\\frac{J_{F0}^{D}}{J_{F0}^{U}}<0.70\n\\quad\\text{且}\\quad\n\\frac{J_{\\mathrm{pert,worst}}^{D}}{J_{\\mathrm{pert,worst}}^{U}}<0.85,": "J_F0(D)/J_F0(U) < 0.70，且 J_pert,worst(D)/J_pert,worst(U) < 0.85",
    "\\frac{J_{\\mathrm{pert,worst}}^{D}}{J_{\\mathrm{pert,worst}}^{U}}<0.70\n\\quad\\text{且}\\quad\n\\frac{J_{F0}^{D}}{J_{F0}^{U}}<0.85.": "J_pert,worst(D)/J_pert,worst(U) < 0.70，且 J_F0(D)/J_F0(U) < 0.85",
    "\\text{中继节点故障}\n\\rightarrow\n\\text{topology/path reconfiguration}\n\\rightarrow\n\\text{mission degradation},": "中继节点故障 → topology/path reconfiguration → mission degradation",
}


def plain_math(text: str) -> str:
    """Convert the manuscript's frozen LaTex fragments into review-readable math."""
    for raw, readable in EQUATION_REPLACEMENTS.items():
        text = text.replace(raw, readable)
    # Inline formula cleanup for the few non-display expressions in prose.
    # Avoid combining mathematical glyphs here: the internal CJK review font
    # does not provide reliable marks for every Latin/Greek combination.
    text = text.replace("\\Pi_{\\mathcal Q}", "Pi_Q")
    text = text.replace("\\bar J", "Jbar").replace("\\widehat J", "Jhat")
    text = text.replace("\\tilde q", "q_tilde").replace("\\tilde d", "d_tilde")
    text = text.replace("\\epsilon", "epsilon").replace("\\beta", "beta")
    text = text.replace("\\kappa", "kappa").replace("\\eta", "eta")
    text = text.replace("\\overline J", "Jbar")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\Delta", "Δ").replace("\\times", "×")
    text = text.replace("\\mathrm{", "").replace("\\mathcal{", "")
    text = text.replace("\\text{", "").replace("\\}", "}")
    text = text.replace("\\_", "_").replace("\\", "")
    # Markdown prose contains a small number of inline LaTeX metric labels.
    # ReportLab is intentionally not used as a TeX engine here, so flatten
    # their subscript braces into legible paper-facing symbols.
    text = re.sub(r"([A-Za-z]+)_\{([^{}]+)\}", r"\1_\2", text)
    text = re.sub(r"([A-Za-z]+)\^\{([^{}]+)\}", r"\1^\2", text)
    return text


def format_display_math(raw: str) -> str:
    """Use robust substring routing rather than raw LaTex typesetting in a review PDF."""
    compact = " ".join(raw.split())
    if "G_t=" in compact:
        return "G_t = (V, E_t, X_t, Z_t)"
    if "A_t[i,j]" in compact:
        return "A_t[i, j] = 1"
    if "t_f=44" in compact:
        return "t_f = 44，d_f = 80"
    if "0\\rightarrow1\\rightarrow2" in compact:
        return "0 -> 1 -> 2  重构为  0 -> 2"
    if "J_{\\mathrm{nominal}}" in compact and "J_{F0}" in compact and "pert" not in compact:
        return "J_nominal，J_F0"
    if "J_{\\mathrm{pert,mean}}" in compact:
        return "J_pert,mean = 十个冻结跨扰动条件任务得分的平均值；J_pert,worst = 十个条件中的最小任务得分"
    if "\\Delta J_c" in compact:
        return "Delta J_c = J_nominal - J_c"
    if "V_{\\mathrm{trigger},c}" in compact:
        return "V_trigger,c = 风险集 R_c 内正确触发故障的 episode 数 / |R_c|"
    if "a_{i,t}\\sim" in compact:
        return "a_i,t 服从由 pi_theta(a_i,t | o_i,t, G_i,t) 给出的动作分布"
    if "\\mathcal G=" in compact:
        return "训练组 G = {N, F0, TE, TL, DS, DL, CP}"
    if "p_N=0.50" in compact:
        return "p_N = 0.50"
    if "q_k^{\\mathrm{UTR}}" in compact:
        return "q_k(UTR) = 1/6；p_k(UTR) = (1 - p_N)q_k = 1/12"
    if "\\max_\\theta" in compact:
        return "DRTP 概念目标：最大化正常工况回报与六个故障组加权最坏回报的组合。"
    if "\\mathcal Q=" in compact:
        return "有界权重集合 Q：每个故障组权重 q_k 介于 0.05 与 0.35，且六组权重和为 1。"
    if "d_{k,u}=\\operatorname{clip}" in compact:
        return "d_k,u = clip((Jbar_N,u − Jbar_k,u) / max(|Jbar_N,u|, epsilon), 0, d_max)"
    if "\\bar J_{k,u}" in compact:
        return "组 k 的 EMA 回报：Jbar(k,u) = (1 - kappa) Jbar(k,u-1) + kappa Jhat(k,u)"
    if "\\tilde q_{k,u+1}" in compact:
        return "q_tilde(k,u+1) = q_k,u · exp(eta · d_tilde(k,u)) / Σ_j∈F[q_j,u · exp(eta · d_tilde(j,u))]"
    if "\\tilde d_{k,u}" in compact:
        return "d_tilde(k,u) = d_k,u − (1/6) Σ_j∈F d_j,u"
    if "q_{u+1}=\\Pi" in compact:
        return "x_u+1 = (1 − beta)q_u + beta·q_tilde_u+1；q_u+1 = Pi_Q(x_u+1)"
    if "\\frac{\\overline J_{\\mathrm{nominal}}^{D}}" in compact:
        return "正常工况总体保持：DRTP 的五种子总体平均任务得分 / UTR 的总体平均任务得分 ≥ 0.95，且五个配对差值的中位数 ≥ 0。"
    if "\\min\\{0.35" in compact and "\\lambda" in compact:
        return "有界单纯形投影：q_k = min{0.35, max{0.05, x_k − λ}}，且六个故障组权重之和为 1。"
    if compact.startswith("\\frac{J_{\\mathrm{pert,worst}}^{D}"):
        return "灾难性条件 B：J_pert,worst(D) / J_pert,worst(U) < 0.70，且 J_F0(D) / J_F0(U) < 0.85。"
    if compact.startswith("\\frac{J_{F0}^{D}"):
        return "灾难性条件 A：J_F0(D) / J_F0(U) < 0.70，且 J_pert,worst(D) / J_pert,worst(U) < 0.85。"
    if "topology/path reconfiguration" in compact:
        return "中继节点故障 -> topology/path reconfiguration -> mission degradation"
    return plain_math(raw)


def image_flow(path_text: str, alt_text: str, style: dict[str, ParagraphStyle], width: float) -> list:
    image_path = PAPER / path_text
    if not image_path.is_file():
        raise FileNotFoundError(f"manuscript figure missing: {image_path}")
    image = Image(str(image_path))
    aspect = image.imageHeight / image.imageWidth
    image.drawWidth = width
    image.drawHeight = width * aspect
    return [Spacer(1, 4), KeepTogether([image, Paragraph(inline(alt_text), style["caption"])]), Spacer(1, 3)]


def markdown_table(rows: list[str], width: float) -> Table:
    normal_cell = ParagraphStyle(
        "ZhTableCell", fontName="NotoSansSC", fontSize=6.6, leading=8.6,
        alignment=TA_CENTER, wordWrap="CJK",
    )
    header_cell = ParagraphStyle(
        "ZhTableHeader", parent=normal_cell, fontName="NotoSansSCBold",
        textColor=colors.HexColor("#102a43"),
    )
    parsed: list[list[Paragraph]] = []
    for index, line in enumerate(rows):
        cells = [table_cell_text(cell) for cell in line.strip().strip("|").split("|")]
        if index == 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        cell_style = header_cell if not parsed else normal_cell
        parsed.append([Paragraph(inline(cell), cell_style) for cell in cells])
    column_count = max(len(row) for row in parsed)
    for row in parsed:
        row.extend([Paragraph("", normal_cell)] * (column_count - len(row)))
    col_width = width / column_count
    table = Table(parsed, colWidths=[col_width] * column_count, repeatRows=1, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9eaf7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#102a43")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#9fb3c8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def table_cell_text(text: str) -> str:
    """Render Markdown table cells without exposing manuscript LaTex delimiters."""
    text = plain_math(text.strip())
    # Tables contain short metric labels such as ``(J_{nominal})``.  ReportLab
    # treats them as plain strings, so normalize the manuscript notation rather
    # than leaving braces and inline-math wrappers in the review PDF.
    text = re.sub(r"J_\{([^}]+)\}", r"J_\1", text)
    return text.replace("(", "").replace(")", "").replace("{", "").replace("}", "")


def parse_story(width: float) -> list:
    style = styles()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story: list = []
    paragraph: list[str] = []
    table_rows: list[str] = []
    equation: list[str] = []
    in_equation = False
    pending_table_caption: Paragraph | None = None

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(item.strip() for item in paragraph).strip()
            story.append(Paragraph(inline(text), style["body"]))
            paragraph.clear()

    def flush_table() -> None:
        nonlocal pending_table_caption
        if table_rows:
            block = []
            if pending_table_caption is not None:
                block.extend([pending_table_caption, Spacer(1, 3)])
            block.extend([markdown_table(table_rows, width), Spacer(1, 7)])
            story.append(KeepTogether(block))
            table_rows.clear()
            pending_table_caption = None

    def flush_equation() -> None:
        if equation:
            raw = "\n".join(equation).strip()
            story.append(Paragraph(inline(format_display_math(raw)), style["equation"]))
            equation.clear()

    for raw in lines:
        line = raw.rstrip()
        if line == "\\[":
            flush_paragraph(); flush_table(); in_equation = True; continue
        if line == "\\]":
            flush_equation(); in_equation = False; continue
        if in_equation:
            equation.append(line); continue
        if line.startswith("|"):
            flush_paragraph(); table_rows.append(line); continue
        flush_table()
        if not line:
            flush_paragraph(); continue
        if line.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline(line[2:]), style["title"]))
            continue
        if line.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline(line[2:]), style["status"]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline(line[3:]), style["h1"]))
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline(line[4:]), style["h2"]))
            continue
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image_match:
            flush_paragraph()
            story.extend(image_flow(image_match.group(2), image_match.group(1), style, width))
            continue
        if re.match(r"^\d+\. ", line):
            flush_paragraph()
            story.append(Paragraph(inline(line), style["body_noindent"]))
            continue
        if line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline("• " + line[2:]), style["body_noindent"]))
            continue
        if re.match(r"^表\s*\d+", line):
            flush_paragraph()
            pending_table_caption = Paragraph(inline(line), style["caption"])
            continue
        paragraph.append(line)
    flush_paragraph(); flush_table(); flush_equation()
    return story


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d9e2ec"))
    canvas.line(2.0 * cm, 1.5 * cm, A4[0] - 2.0 * cm, 1.5 * cm)
    canvas.setFont("NotoSansSC", 7.2)
    canvas.setFillColor(colors.HexColor("#627d98"))
    canvas.drawString(2.0 * cm, 1.0 * cm, "中文投稿科学终稿｜三层证据整合｜作者与期刊元数据待补")
    canvas.drawRightString(A4[0] - 2.0 * cm, 1.0 * cm, f"第 {doc.page} 页")
    canvas.restoreState()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the frozen Chinese manuscript as a pre-submission scientific PDF."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUT,
        help="PDF path to create (defaults to the pre-submission scientific version).",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=2.0 * cm, rightMargin=2.0 * cm,
                                 topMargin=1.75 * cm, bottomMargin=2.0 * cm,
                                 title="中继节点故障下异构多无人机拓扑鲁棒协同")
    story = parse_story(A4[0] - 4.0 * cm)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    main()
