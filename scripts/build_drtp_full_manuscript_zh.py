# -*- coding: utf-8 -*-
"""Build the full Chinese DRTP manuscript from the evidence-grounded source.

This is deliberately a manuscript builder rather than a report generator.  It
keeps the complete task model, controlled intervention, formal results, and
evidence boundary in one journal-style document.  Quantitative statements are
read from the maintained manuscript source and its frozen evidence artefacts;
no pending 6-UAV or ablation result is inserted.
"""
from __future__ import annotations

import re
import os
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("DRTP_MANUSCRIPT_SOURCE", ROOT / "paper" / "q2_final_zh" / "main_zh.md"))
OUT = ROOT / "docs" / "drtp_submission_ready"
DOCX = Path(os.environ.get("DRTP_MANUSCRIPT_DOCX", OUT / "DRTP_FINAL_MANUSCRIPT_SUBMISSION_READY_FULL.docx"))
PDF = Path(os.environ.get("DRTP_MANUSCRIPT_PDF", OUT / "DRTP_FINAL_MANUSCRIPT_SUBMISSION_READY_FULL.pdf"))


def set_font(run, name="宋体", size=10.5, bold=None, color=None, italic=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), fill)
    tc_pr.append(node)


def set_cell_border(cell, color="B7C9D6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for side in ("top", "left", "bottom", "right"):
        edge = borders.find(qn("w:" + side))
        if edge is None:
            edge = OxmlElement("w:" + side)
            borders.append(edge)
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "4")
        edge.set(qn("w:color"), color)


def clean_inline(text):
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("--", "—")
    # The maintained source is Markdown/LaTex-oriented.  Word does not render
    # the source markup, so normalize the small, recurring formula vocabulary
    # into readable manuscript notation instead of leaking commands on the page.
    for _ in range(3):
        text = re.sub(r"\\(?:mathrm|mathcal|operatorname|text)\{([^{}]*)\}", r"\1", text)
        text = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", text)
    text = (text.replace("\\sum", "Σ").replace("\\min", "min").replace("\\max", "max")
                .replace("\\cdot", "·").replace("\\rightarrow", "→").replace("\\qquad", "  ").replace("\\quad", "  ")
                .replace("\\epsilon", "ε").replace("\\kappa", "κ").replace("\\beta", "β")
                .replace("\\eta", "η").replace("\\tilde", "~").replace("\\Pi", "Π")
                .replace("\\mathcal ", "").replace("\\mathrm ", "").replace("\\operatorname ", "")
                .replace("\\in", "∈").replace("\\left", "").replace("\\right", ""))
    text = text.replace("\\{", "{").replace("\\}", "}").replace("\\", "")
    text = re.sub(r"\$([^$]+)\$", r"\1", text)
    return text.strip()


def add_body(doc, text, first=True, font=10.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.48
    pf.space_after = Pt(4.2)
    pf.first_line_indent = Cm(0.74) if first else Cm(0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(clean_inline(text))
    set_font(r, "宋体", font)
    return p


def add_math(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(clean_inline(text))
    set_font(r, "Cambria Math", 9.5, italic=True)


def add_heading(doc, text, level):
    p = doc.add_paragraph(style=f"Heading {min(level, 3)}")
    pf = p.paragraph_format
    pf.keep_with_next = True
    pf.space_before = Pt(15 if level == 1 else 9)
    pf.space_after = Pt(5)
    if level == 1:
        r = p.add_run(clean_inline(text))
        set_font(r, "黑体", 15, True, (20, 61, 91))
    elif level == 2:
        r = p.add_run(clean_inline(text))
        set_font(r, "黑体", 12, True)
    else:
        r = p.add_run(clean_inline(text))
        set_font(r, "宋体", 10.8, True)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph(style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run(clean_inline(text))
    set_font(r, "宋体", 8.5, italic=True)


def parse_table(lines):
    rows = []
    for line in lines:
        if re.match(r"^\|\s*[-: ]+\|", line):
            continue
        cells = [clean_inline(x) for x in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def add_table(doc, rows):
    if not rows:
        return
    cols = max(len(x) for x in rows)
    table = doc.add_table(rows=1, cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for row_idx, row in enumerate(rows):
        cells = table.rows[0].cells if row_idx == 0 else table.add_row().cells
        for col in range(cols):
            value = row[col] if col < len(row) else ""
            cell = cells[col]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            if row_idx == 0:
                shade(cell, "1A4C72")
            elif row_idx % 2 == 0:
                shade(cell, "EEF4F8")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(value)
            set_font(r, "宋体", 7.4 if cols > 6 else 8.1,
                     bold=(row_idx == 0), color=(255, 255, 255) if row_idx == 0 else None)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_picture(doc, markdown_path):
    path = (SOURCE.parent / markdown_path).resolve()
    if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        return False
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.add_picture(str(path), width=Cm(15.8))
    return True


def add_bullets(doc, line):
    text = clean_inline(re.sub(r"^\s*[-*]\s+", "", line))
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.35
    r = p.add_run(text)
    set_font(r, "宋体", 10.2)


def source_after_front_matter():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, x in enumerate(lines) if x.startswith("## 1 引言"))
    # The source carries a machine-facing availability section. Keep the full
    # references but exclude authorship boilerplate from a blinded submission draft.
    end = next((i for i, x in enumerate(lines[start:], start) if x.startswith("## 作者贡献")), len(lines))
    return lines[start:end]


def transform_section_title(text):
    replacements = {
        "## 3 问题建模": "## 3 系统任务、信息边界与实验问题",
        "## 4 方法": "## 4 有界自适应拓扑扰动重加权方法",
        "## 5 实验协议": "## 5 实验设计与证据组织",
        "## 6 结果": "## 6 受控结果与证据分析",
        "## 7 讨论": "## 7 讨论：训练暴露塑形的作用范围",
    }
    return replacements.get(text, text)


def read_front_matter():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), "DRTP manuscript")
    abstract_start = lines.index("## 摘要") + 1
    keyword_start = lines.index("## 关键词")
    abstract = " ".join(line.strip() for line in lines[abstract_start:keyword_start] if line.strip())
    body_start = next(i for i, line in enumerate(lines[keyword_start + 1:], keyword_start + 1) if line.startswith("## 1 "))
    keywords = " ".join(line.strip() for line in lines[keyword_start + 1:body_start] if line.strip())
    return title, abstract, keywords


def add_front_matter(doc):
    title, abstract, keywords = read_front_matter()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(clean_inline(title))
    set_font(r, "黑体", 18, True, (20, 61, 91))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(15)
    r = p.add_run("一种有界自适应拓扑扰动重加权的双 cohort 受控实证研究")
    set_font(r, "宋体", 12.5, False, (76, 86, 96))

    add_heading(doc, "摘  要", 1)
    add_body(doc, abstract)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(9)
    r = p.add_run("关键词：")
    set_font(r, "黑体", 10.5, True)
    r = p.add_run(clean_inline(keywords))
    set_font(r, "宋体", 10.5)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0); sec.page_height = Cm(29.7)
    sec.top_margin = Cm(1.9); sec.bottom_margin = Cm(1.8)
    sec.left_margin = Cm(2.05); sec.right_margin = Cm(2.05)
    sec.header_distance = Cm(0.8); sec.footer_distance = Cm(0.75)
    styles = doc.styles
    styles["Normal"].font.name = "宋体"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    styles["Normal"].font.size = Pt(10.5)
    for index, size in ((1, 15), (2, 12), (3, 10.8)):
        heading = styles[f"Heading {index}"]
        heading.font.name = "黑体" if index < 3 else "宋体"
        heading._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体" if index < 3 else "宋体")
        heading.font.size = Pt(size)
        heading.font.bold = True
    styles["Caption"].font.name = "宋体"
    styles["Caption"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    styles["Caption"].font.size = Pt(8.5)
    if "List Bullet" in styles:
        styles["List Bullet"].font.name = "宋体"
        styles["List Bullet"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    header = sec.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = header.add_run("面向中继拓扑退化的异构多无人机协同训练暴露塑形")
    set_font(hr, "宋体", 8.3, color=(90, 90, 90))
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run("投稿稿件")
    set_font(fr, "宋体", 8.3, color=(90, 90, 90))

    add_front_matter(doc)
    lines = source_after_front_matter()
    i = 0
    in_math = False
    math_lines = []
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()
        if stripped == "\\[":
            in_math = True; math_lines = []; i += 1; continue
        if in_math:
            if stripped == "\\]":
                add_math(doc, " ".join(math_lines)); in_math = False
            else:
                math_lines.append(stripped)
            i += 1; continue
        if not stripped:
            i += 1; continue
        if stripped.startswith("!["):
            match = re.search(r"\]\(([^)]+)\)", stripped)
            if match: add_picture(doc, match.group(1))
            i += 1; continue
        if stripped.startswith("**图") or stripped.startswith("**表"):
            add_caption(doc, stripped)
            i += 1; continue
        if stripped.startswith("|"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                buf.append(lines[i].strip()); i += 1
            add_table(doc, parse_table(buf)); continue
        if stripped.startswith("### "):
            add_heading(doc, transform_section_title(stripped[4:]), 2)
        elif stripped.startswith("## "):
            # Preserve the semantic replacement map while never exposing
            # Markdown markers in the rendered manuscript heading.
            mapped = transform_section_title(stripped)
            add_heading(doc, mapped[3:] if mapped.startswith("## ") else mapped, 1)
        elif stripped.startswith("# "):
            add_heading(doc, transform_section_title(stripped[2:]), 1)
        elif re.match(r"^[-*]\s+", stripped):
            add_bullets(doc, stripped)
        elif re.match(r"^\d+\.\s", stripped) or stripped.startswith("（") and "）" in stripped[:5]:
            add_body(doc, stripped, first=False)
        elif stripped.startswith("**") and stripped.endswith("**"):
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(3)
            r = p.add_run(clean_inline(stripped)); set_font(r, "宋体", 10.5, True)
        else:
            add_body(doc, stripped)
        i += 1

    doc.save(DOCX)
    return DOCX


if __name__ == "__main__":
    print(build())
