"""Convert docs/PROJECT_DOCUMENTATION.md into a .docx for Google Docs import.

    uv run python docs/build_docx.py
    uv run python docs/build_docx.py docs/PRESENTATION_NOTES.md docs/CodeSentinel_Presentation_Notes.docx
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent
SRC = HERE / "PROJECT_DOCUMENTATION.md"
OUT = HERE / "CodeSentinel_Week3_Project_Documentation.docx"
INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def add_inline(par, text: str, bold: bool = False):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2])
            r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0x1F, 0x6F, 0x50)
        elif part.startswith("["):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
            r = par.add_run(m.group(1))
            r.underline = True
        else:
            r = par.add_run(part)
        if bold:
            r.bold = True


def shade(cell, hex_fill: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def build():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    for section in doc.sections:
        section.left_margin = section.right_margin = Inches(0.9)

    lines = SRC.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            p = doc.add_paragraph()
            r = p.add_run("\n".join(code))
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r_idx, row in enumerate(rows):
                for c_idx, val in enumerate(row[: len(rows[0])]):
                    cell = table.cell(r_idx, c_idx)
                    cell.text = ""
                    add_inline(cell.paragraphs[0], val, bold=r_idx == 0)
                    for par in cell.paragraphs:
                        for run in par.runs:
                            run.font.size = Pt(9.5)
                    if r_idx == 0:
                        shade(cell, "E8F5EE")
            doc.add_paragraph()
            continue
        if m := re.match(r"!\[[^\]]*\]\(([^)]+)\)", line):
            img = HERE / m.group(1)
            if img.exists():
                doc.add_picture(str(img), width=Inches(6.6))
            i += 1
            continue
        if m := re.match(r"(#{1,4}) (.*)", line):
            level = len(m.group(1))
            doc.add_heading(m.group(2), level=0 if level == 1 else level - 1)
        elif line.startswith("> "):
            p = doc.add_paragraph(style="Intense Quote")
            add_inline(p, line[2:])
        elif re.match(r"\s*[*-] ", line):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, re.sub(r"^\s*[*-] ", "", line))
        elif re.match(r"\d+\. ", line):
            p = doc.add_paragraph(style="List Number")
            add_inline(p, re.sub(r"^\d+\. ", "", line))
        elif line.strip():
            p = doc.add_paragraph()
            add_inline(p, line)
        i += 1
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        SRC, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    build()
