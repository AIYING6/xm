"""Build a review PDF from the Chinese Q2 manuscript Markdown sections."""

from __future__ import annotations

import re
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "q2_draft_zh"
OUTPUT = Path(os.environ.get("Q2_DRAFT_PDF_OUTPUT", ROOT / "output" / "pdf" / "中继故障拓扑重构与训练可靠性_中文初稿.pdf"))
FONT = Path(r"C:\Windows\Fonts\NotoSerifSC-VF.ttf")

SECTIONS = [
    "01_摘要与关键词.md",
    "02_引言.md",
    "03_相关研究.md",
    "04_问题定义与范围.md",
    "05_方法.md",
    "06_实验设置与统计.md",
    "07_结果.md",
    "08_讨论与局限.md",
    "09_数据与代码可用性.md",
    "10_结论.md",
]


def clean_inline(text: str) -> str:
    text = text.strip()
    text = re.sub(r"`([^`]*)`", r"<font name='NotoSerifSC'>\1</font>", text)
    text = text.replace("**", "")
    return text.replace("&", "&amp;").replace("&amp;lt;", "&lt;").replace("&amp;gt;", "&gt;")


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def parse_section(path: Path, styles: dict[str, ParagraphStyle]):
    story = []
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            start = i
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            rows = table_rows([x.strip() for x in lines[start:i]])
            if rows:
                rendered = [[Paragraph(clean_inline(cell), styles["TableCell"]) for cell in row] for row in rows]
                widths = [16.5 * cm / len(rows[0])] * len(rows[0])
                table = Table(rendered, colWidths=widths, repeatRows=1, hAlign="CENTER")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#A6A6A6")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FC")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.extend([Spacer(1, 0.12 * cm), table, Spacer(1, 0.22 * cm)])
            continue
        if line.startswith("# "):
            story.extend([Spacer(1, 0.15 * cm), Paragraph(clean_inline(line[2:]), styles["H1"]), Spacer(1, 0.18 * cm)])
            i += 1
            continue
        if line.startswith("## "):
            story.extend([Spacer(1, 0.12 * cm), Paragraph(clean_inline(line[3:]), styles["H2"]), Spacer(1, 0.1 * cm)])
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line) or line.startswith("- "):
            story.append(Paragraph(clean_inline(line), styles["Bullet"]))
            i += 1
            continue
        paragraph = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line or next_line.startswith("#") or next_line.startswith("|") or re.match(r"^(\d+\.\s+|-\s+)", next_line):
                break
            paragraph.append(next_line)
            i += 1
        story.extend([Paragraph(clean_inline(" ".join(paragraph)), styles["Body"]), Spacer(1, 0.12 * cm)])
    return story


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8E2EF"))
    canvas.line(doc.leftMargin, A4[1] - 1.25 * cm, A4[0] - doc.rightMargin, A4[1] - 1.25 * cm)
    canvas.setFont("NotoSerifSC", 8)
    canvas.setFillColor(colors.HexColor("#59636E"))
    canvas.drawString(doc.leftMargin, A4[1] - 0.92 * cm, "中继故障拓扑重构与训练可靠性 - 中文初稿（审阅版）")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.78 * cm, f"第 {doc.page} 页")
    canvas.restoreState()


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not FONT.exists():
        raise FileNotFoundError(FONT)
    pdfmetrics.registerFont(TTFont("NotoSerifSC", str(FONT)))
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle("TitleZh", parent=base["Title"], fontName="NotoSerifSC", fontSize=21, leading=30, alignment=TA_CENTER, textColor=colors.HexColor("#17365D")),
        "Subtitle": ParagraphStyle("SubtitleZh", parent=base["Normal"], fontName="NotoSerifSC", fontSize=11, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#59636E")),
        "H1": ParagraphStyle("H1Zh", parent=base["Heading1"], fontName="NotoSerifSC", fontSize=16, leading=24, textColor=colors.HexColor("#17365D"), spaceBefore=10, spaceAfter=6),
        "H2": ParagraphStyle("H2Zh", parent=base["Heading2"], fontName="NotoSerifSC", fontSize=12, leading=19, textColor=colors.HexColor("#1F4E79"), spaceBefore=7, spaceAfter=4),
        "Body": ParagraphStyle("BodyZh", parent=base["BodyText"], fontName="NotoSerifSC", fontSize=10, leading=18, alignment=TA_LEFT, firstLineIndent=20, spaceAfter=3),
        "Bullet": ParagraphStyle("BulletZh", parent=base["BodyText"], fontName="NotoSerifSC", fontSize=10, leading=17, leftIndent=12, firstLineIndent=-10),
        "TableCell": ParagraphStyle("TableCellZh", parent=base["BodyText"], fontName="NotoSerifSC", fontSize=7.4, leading=10, alignment=TA_CENTER),
    }
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=2.25 * cm, rightMargin=2.25 * cm, topMargin=1.8 * cm, bottomMargin=1.45 * cm, title="中继故障拓扑重构与训练可靠性")
    story = [
        Spacer(1, 3.5 * cm),
        Paragraph("中继故障拓扑重构与训练可靠性", styles["Title"]),
        Spacer(1, 0.25 * cm),
        Paragraph("异构多无人机协同的受控训练分布比较与可审计证据链", styles["Subtitle"]),
        Spacer(1, 1.3 * cm),
        Paragraph("中文初稿（审阅版）", styles["Subtitle"]),
        Spacer(1, 0.2 * cm),
        Paragraph("2026-08-26 | 结果以 UTR/SNR/DRTP 前瞻性 five-seed 10M 比较为主", styles["Subtitle"]),
        Spacer(1, 0.8 * cm),
        Paragraph("说明：本版本用于论文结构、论点和数据呈现审阅。它完整保留历史 DRTP 的高收益与反向 seed，但不将 DRTP/SNR 写作已验证的可靠主算法。", styles["Body"]),
        PageBreak(),
    ]
    for filename in SECTIONS:
        story.extend(parse_section(SOURCE / filename, styles))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
