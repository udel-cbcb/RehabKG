#!/usr/bin/env python3
"""Regenerate RehabKG_project_presentation.pptx from the markdown source.

The markdown file (RehabKG_project_presentation.md) is the source of truth.
Sections separated by `---` become slides; `**Speaker notes:**` paragraphs
become PowerPoint speaker notes. Every slide is rendered from the markdown
alone; there are no per-slide overrides. Besides headings, bullets, numbered
lists, tables and code fences, the builder understands:

    ::: HEADING | body      consecutive lines -> a row of cards (max 4 per row)
    >> LABEL | caption      consecutive lines -> a vertical labelled flow
    **A** / → / **B**       alternating lines -> a horizontal box flow
    > text                  a highlighted callout bar

Run from the deliverables directory:

    python3 build_slides.py
"""
import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
MD = HERE / "RehabKG_project_presentation.md"
OUT = HERE / "RehabKG_project_presentation.pptx"

NAVY = RGBColor(0x1F, 0x38, 0x64)
ACCENT = RGBColor(0x2E, 0x74, 0xB5)
DARK = RGBColor(0x33, 0x33, 0x33)
GRAY = RGBColor(0x70, 0x70, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CODE_BG = RGBColor(0xF2, 0xF2, 0xF2)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def parse_chunks(text):
    """Split markdown into slide chunks on --- separators."""
    chunks, cur = [], []
    for line in text.splitlines():
        if line.strip() == "---":
            chunks.append(cur)
            cur = []
        else:
            cur.append(line)
    if cur:
        chunks.append(cur)
    return chunks


def split_notes(body_lines):
    """Return (content_lines, notes_text) — notes start at **Speaker notes:**."""
    content, notes = [], []
    in_notes = False
    for line in body_lines:
        if line.strip().startswith("**Speaker notes:**"):
            in_notes = True
            notes.append(line.strip().replace("**Speaker notes:**", "").strip())
        elif in_notes:
            if line.strip():
                notes.append(line.strip())
            # blank lines inside notes just separate paragraphs; keep going
        else:
            content.append(line)
    return content, " ".join(n for n in notes if n)


def add_inline_runs(paragraph, text, size, color=DARK, bold=False):
    """Render **bold** and `code` inline markers as styled runs."""
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            run = paragraph.add_run()
            run.text = text[pos:m.start()]
            run.font.size = size
            run.font.color.rgb = color
            run.font.bold = bold
        token = m.group(0)
        run = paragraph.add_run()
        if token.startswith("**"):
            run.text = token[2:-2]
            run.font.size = size
            run.font.color.rgb = color
            run.font.bold = True
        else:
            run.text = token[1:-1]
            run.font.size = size
            run.font.color.rgb = ACCENT
            run.font.name = "Consolas"
        pos = m.end()
    if pos < len(text):
        run = paragraph.add_run()
        run.text = text[pos:]
        run.font.size = size
        run.font.color.rgb = color
        run.font.bold = bold


def parse_table(lines):
    """Parse consecutive markdown-table lines into (headers, rows, aligns)."""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    headers = rows[0]
    aligns = []
    if len(rows) > 1 and set("".join(rows[1]).replace(":", "").replace("-", "").replace(" ", "")) == set():
        aligns = rows[1]
        rows = rows[2:]
    else:
        rows = rows[1:]
    return headers, rows, aligns


def classify_body(content_lines):
    """Group content lines into typed blocks."""
    blocks, i = [], 0
    n = len(content_lines)
    while i < n:
        line = content_lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("---") and set(stripped) <= {"|", "-", ":", " "}:
            # Markdown table delimiter rows are structure, not content.
            i += 1
            continue
        if stripped.startswith("###"):
            blocks.append(("subhead", stripped.lstrip("#").strip()))
            i += 1
            continue
        if stripped.startswith(":::"):
            cards = []
            while i < n and content_lines[i].strip().startswith(":::"):
                head, _, body = content_lines[i].strip()[3:].partition("|")
                cards.append((head.strip(), body.strip()))
                i += 1
            for k in range(0, len(cards), 4):
                blocks.append(("cards", cards[k:k + 4]))
            continue
        if stripped.startswith(">>"):
            labels, captions = [], []
            while i < n and content_lines[i].strip().startswith(">>"):
                head, _, body = content_lines[i].strip()[2:].partition("|")
                labels.append(head.strip())
                captions.append(body.strip())
                i += 1
            blocks.append(("diagram_flow", (labels, captions)))
            continue
        if stripped.startswith(">"):
            blocks.append(("callout", re.sub(r"^>\s*", "", stripped)))
            i += 1
            continue
        if (stripped.startswith("**") and i + 2 < n
                and content_lines[i + 1].strip() in {"↓", "→"}
                and content_lines[i + 2].strip().startswith("**")):
            labels = [stripped.strip("*")]
            i += 1
            while (i + 1 < n and content_lines[i].strip() in {"↓", "→"}
                   and content_lines[i + 1].strip().startswith("**")):
                labels.append(content_lines[i + 1].strip().strip("*"))
                i += 2
            blocks.append(("flow", labels))
            continue
        if stripped.startswith("```"):
            code = []
            i += 1
            while i < n and not content_lines[i].strip().startswith("```"):
                code.append(content_lines[i])
                i += 1
            i += 1  # closing fence
            blocks.append(("code", "\n".join(code)))
        elif stripped.startswith("|"):
            tbl = []
            while i < n and content_lines[i].strip().startswith("|"):
                tbl.append(content_lines[i])
                i += 1
            blocks.append(("table", tbl))
        elif stripped.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
            blocks.append(("image", (m.group(1), m.group(2)) if m else ("", stripped)))
            i += 1
        elif re.match(r"^[-*] ", stripped):
            items = []
            while i < n and re.match(r"^[-*] ", content_lines[i].strip()):
                items.append(re.sub(r"^[-*] ", "", content_lines[i].strip()))
                i += 1
            blocks.append(("bullets", items))
        elif re.match(r"^\d+\. ", stripped):
            items = []
            while i < n and re.match(r"^\d+\. ", content_lines[i].strip()):
                items.append(content_lines[i].strip())
                i += 1
            blocks.append(("numbered", items))
        else:
            para = [stripped]
            i += 1
            while i < n:
                nxt = content_lines[i].strip()
                if (not nxt or nxt.startswith(("-", "|", "```", "![", "###", ">", ":::"))
                        or re.match(r"^\d+\. ", nxt)):
                    break
                para.append(nxt)
                i += 1
            blocks.append(("para", " ".join(para)))
    return blocks


def slide_base(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # top accent bar
    bar = slide.shapes.add_shape(1, 0, 0, SLIDE_W, Inches(0.12))  # 1 = rectangle
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    return slide


def add_title(slide, title, subtitle=None):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(1.0))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = title
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = NAVY
    if subtitle:
        p2 = tf.add_paragraph()
        run2 = p2.add_run()
        run2.text = subtitle.replace("**", "").replace("`", "")
        run2.font.size = Pt(15)
        run2.font.italic = True
        run2.font.color.rgb = GRAY
    return box


def add_page_number(slide, num, total):
    box = slide.shapes.add_textbox(Inches(12.5), Inches(7.05), Inches(0.7), Inches(0.35))
    p = box.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = f"{num}/{total}"
    run.font.size = Pt(10)
    run.font.color.rgb = GRAY


def render_blocks(slide, blocks, top=Inches(1.5), bottom=Inches(7.0)):
    """Lay out blocks vertically; returns nothing (best-effort fitting)."""
    y = top
    for kind, data in blocks:
        if kind == "subhead":
            h = Inches(0.4)
            box = slide.shapes.add_textbox(Inches(0.7), y, Inches(11.9), h)
            tf = box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = data
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = ACCENT
            y += h
        elif kind == "notes_only":
            continue
        elif kind == "para":
            h = Inches(0.45)
            box = slide.shapes.add_textbox(Inches(0.7), y, Inches(11.9), h)
            tf = box.text_frame
            tf.word_wrap = True
            add_inline_runs(tf.paragraphs[0], data, Pt(16), color=DARK)
            y += h
        elif kind == "bullets":
            per = Inches(0.42)
            h = per * len(data) + Inches(0.1)
            box = slide.shapes.add_textbox(Inches(0.7), y, Inches(11.9), h)
            tf = box.text_frame
            tf.word_wrap = True
            for j, item in enumerate(data):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.level = 0
                run = p.add_run()
                run.text = "•  "
                run.font.size = Pt(16)
                run.font.color.rgb = ACCENT
                run.font.bold = True
                add_inline_runs(p, item, Pt(16))
                p.space_after = Pt(6)
            y += h
        elif kind == "numbered":
            per = Inches(0.5)
            h = per * len(data) + Inches(0.1)
            box = slide.shapes.add_textbox(Inches(0.7), y, Inches(11.9), h)
            tf = box.text_frame
            tf.word_wrap = True
            for j, item in enumerate(data):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                add_inline_runs(p, item, Pt(16))
                p.space_after = Pt(8)
            y += h
        elif kind == "code":
            lines = data.split("\n")
            h = Inches(0.3) * len(lines) + Inches(0.25)
            box = slide.shapes.add_textbox(Inches(0.9), y, Inches(11.5), h)
            tf = box.text_frame
            tf.word_wrap = True
            fill = box.fill
            fill.solid()
            fill.fore_color.rgb = CODE_BG
            for j, cl in enumerate(lines):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                run = p.add_run()
                run.text = cl if cl else " "
                run.font.size = Pt(14)
                run.font.name = "Consolas"
                run.font.color.rgb = DARK
            y += h + Inches(0.1)
        elif kind == "flow":
            labels = data
            gap = Inches(0.28)
            total_w = Inches(11.8)
            box_w = (total_w - gap * (len(labels) - 1)) / len(labels)
            x0 = Inches(0.75)
            h = Inches(0.7)
            for j, label in enumerate(labels):
                x = x0 + j * (box_w + gap)
                box = slide.shapes.add_shape(1, x, y, box_w, h)
                box.fill.solid()
                box.fill.fore_color.rgb = NAVY if j in (0, len(labels) - 1) else ACCENT
                box.line.fill.background()
                tf = box.text_frame
                tf.word_wrap = True
                tf.vertical_anchor = 3
                tf.margin_left = Inches(0.08)
                tf.margin_right = Inches(0.08)
                tf.margin_top = Inches(0.04)
                tf.margin_bottom = Inches(0.04)
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                run = p.add_run()
                run.text = label
                run.font.size = Pt(14)
                run.font.bold = True
                run.font.color.rgb = WHITE
                if j < len(labels) - 1:
                    arrow = slide.shapes.add_textbox(x + box_w, y + Inches(0.16), gap, Inches(0.4))
                    ap = arrow.text_frame.paragraphs[0]
                    ap.alignment = PP_ALIGN.CENTER
                    ar = ap.add_run()
                    ar.text = "→"
                    ar.font.size = Pt(22)
                    ar.font.bold = True
                    ar.font.color.rgb = NAVY
            y += h + Inches(0.08)
        elif kind == "diagram_flow":
            labels, captions = data
            if isinstance(labels, str):
                labels = [part.strip().strip("*") for part in labels.splitlines() if part.strip()]
            if isinstance(captions, str):
                captions = [part.strip() for part in captions.splitlines() if part.strip()]
            if len(captions) != len(labels):
                captions = [""] * len(labels)
            total_w = Inches(11.8)
            x0 = Inches(0.75)
            gap_y = Inches(0.22)
            row_h = Inches(0.55)
            detail_x = Inches(4.35)
            box_w = Inches(3.2)
            for row, (label, caption) in enumerate(zip(labels, captions)):
                row_y = y + row * (row_h + gap_y)
                box = slide.shapes.add_shape(1, x0, row_y, box_w, Inches(0.55))
                box.fill.solid()
                box.fill.fore_color.rgb = NAVY if row in (0, len(labels) - 1) else ACCENT
                box.line.fill.background()
                tf = box.text_frame
                tf.vertical_anchor = 3
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                r = p.add_run()
                r.text = label
                r.font.size = Pt(12)
                r.font.bold = True
                r.font.color.rgb = WHITE
                detail = slide.shapes.add_textbox(detail_x, row_y, total_w - (detail_x - x0), Inches(0.55))
                detail.text_frame.word_wrap = True
                detail.text_frame.vertical_anchor = 3
                dp = detail.text_frame.paragraphs[0]
                dr = dp.add_run()
                dr.text = caption
                dr.font.size = Pt(14)
                dr.font.color.rgb = DARK
            y += len(labels) * (row_h + gap_y)
        elif kind == "columns":
            columns = data
            gap = Inches(0.25)
            total_w = Inches(11.8)
            box_w = (total_w - gap * (len(columns) - 1)) / len(columns)
            x0 = Inches(0.75)
            h = Inches(1.65)
            for j, (heading, body) in enumerate(columns):
                x = x0 + j * (box_w + gap)
                box = slide.shapes.add_shape(1, x, y, box_w, h)
                box.fill.solid()
                box.fill.fore_color.rgb = CODE_BG
                box.line.color.rgb = ACCENT
                box.line.width = Pt(1.5)
                tf = box.text_frame
                tf.clear()
                tf.word_wrap = True
                tf.margin_left = Inches(0.15)
                tf.margin_right = Inches(0.15)
                tf.margin_top = Inches(0.14)
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                r = p.add_run()
                r.text = heading
                r.font.size = Pt(18)
                r.font.bold = True
                r.font.color.rgb = NAVY
                p2 = tf.add_paragraph()
                p2.alignment = PP_ALIGN.CENTER
                p2.space_before = Pt(10)
                r2 = p2.add_run()
                r2.text = body
                r2.font.size = Pt(13)
                r2.font.color.rgb = DARK
            y += h + Inches(0.08)
        elif kind == "compact_columns":
            columns = data
            gap = Inches(0.25)
            total_w = Inches(11.8)
            box_w = (total_w - gap * (len(columns) - 1)) / len(columns)
            x0 = Inches(0.75)
            h = Inches(0.9)
            for j, (heading, body) in enumerate(columns):
                x = x0 + j * (box_w + gap)
                box = slide.shapes.add_shape(1, x, y, box_w, h)
                box.fill.solid()
                box.fill.fore_color.rgb = CODE_BG
                box.line.color.rgb = ACCENT
                box.line.width = Pt(1.5)
                tf = box.text_frame
                tf.clear()
                tf.word_wrap = True
                tf.margin_left = Inches(0.1)
                tf.margin_right = Inches(0.1)
                tf.margin_top = Inches(0.06)
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                r = p.add_run()
                r.text = heading
                r.font.size = Pt(12)
                r.font.bold = True
                r.font.color.rgb = NAVY
                p2 = tf.add_paragraph()
                p2.alignment = PP_ALIGN.CENTER
                p2.space_before = Pt(3)
                r2 = p2.add_run()
                r2.text = body
                r2.font.size = Pt(10)
                r2.font.color.rgb = DARK
            y += h + Inches(0.08)
        elif kind == "cards":
            cards = data
            gap = Inches(0.25)
            total_w = Inches(11.8)
            box_w = (total_w - gap * (len(cards) - 1)) / len(cards)
            longest = max(len(body) for _, body in cards)
            chars_per_line = max(20, int(box_w / Inches(1) * 11))
            body_lines = max(1, -(-longest // chars_per_line))
            h = Inches(0.55) + Inches(0.24) * body_lines
            for j, (heading, body) in enumerate(cards):
                x = Inches(0.75) + j * (box_w + gap)
                box = slide.shapes.add_shape(1, x, y, box_w, h)
                box.fill.solid()
                box.fill.fore_color.rgb = CODE_BG
                box.line.color.rgb = ACCENT
                box.line.width = Pt(1.5)
                tf = box.text_frame
                tf.clear()
                tf.word_wrap = True
                tf.vertical_anchor = 1
                tf.margin_left = Inches(0.12)
                tf.margin_right = Inches(0.12)
                tf.margin_top = Inches(0.08)
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                add_inline_runs(p, heading, Pt(15), color=NAVY, bold=True)
                if body:
                    p2 = tf.add_paragraph()
                    p2.alignment = PP_ALIGN.CENTER
                    p2.space_before = Pt(4)
                    add_inline_runs(p2, body, Pt(12))
            y += h + Inches(0.12)
        elif kind == "callout":
            box_h = Inches(0.42) if len(data) <= 120 else Inches(0.7)
            box = slide.shapes.add_shape(1, Inches(0.9), y, Inches(11.5), box_h)
            box.fill.solid()
            box.fill.fore_color.rgb = CODE_BG
            box.line.color.rgb = ACCENT
            box.line.width = Pt(1.5)
            tf = box.text_frame
            tf.vertical_anchor = 3
            tf.margin_left = Inches(0.15)
            tf.margin_right = Inches(0.15)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            tf.word_wrap = True
            add_inline_runs(p, data, Pt(13), color=NAVY)
            y += box_h + Inches(0.08)
        elif kind == "table":
            headers, rows, aligns = parse_table(data)
            n_rows, n_cols = len(rows) + 1, len(headers)
            is_dense = n_rows > 8
            font_pt = 10 if is_dense else 12
            width = Inches(11.9)
            clean = [[v.replace("**", "").replace("`", "") for v in row[:n_cols]] for row in rows]
            # Column widths proportional to content length (clamped), so short
            # numeric columns don't take a third of the slide.
            lengths = [max([len(headers[c])] + [len(r[c]) for r in clean if c < len(r)])
                       for c in range(n_cols)]
            weights = [min(max(length, 8), 70) for length in lengths]
            col_w = [int(width * w / sum(weights)) for w in weights]
            # ~1 character per 0.085in at 12pt; estimate wrapped lines per row
            char_w = int(Inches(0.085) * font_pt / 12)
            line_h = int(Inches(0.22) * font_pt / 12)

            def row_height(cells):
                lines = max(-(-len(v) // max(1, int((col_w[c] - Inches(0.2)) / char_w)))
                            for c, v in enumerate(cells) if c < n_cols) if cells else 1
                return int(line_h * max(1, lines) + Inches(0.12))

            heights = [row_height(headers)] + [row_height(r) for r in clean]
            tbl_h = sum(heights)
            gtable = slide.shapes.add_table(n_rows, n_cols, Inches(0.7), y, width, tbl_h).table
            for c, w in enumerate(col_w):
                gtable.columns[c].width = w
            for row, h in zip(gtable.rows, heights):
                row.height = h
            for c, head in enumerate(headers):
                cell = gtable.cell(0, c)
                cell.text = head
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(font_pt)
                        r.font.bold = True
                        r.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
            for ri, row in enumerate(rows, start=1):
                for c, val in enumerate(row[:n_cols]):
                    cell = gtable.cell(ri, c)
                    # strip inline markers for table cells
                    cell.text = val.replace("**", "").replace("`", "")
                    for p in cell.text_frame.paragraphs:
                        for r in p.runs:
                            r.font.size = Pt(font_pt)
                            r.font.color.rgb = DARK
                        if c > 0 and aligns and c < len(aligns) and aligns[c].endswith(":"):
                            p.alignment = PP_ALIGN.RIGHT
            y += tbl_h + Inches(0.15)
        elif kind == "image":
            alt, path = data
            img_path = (HERE / path).resolve()
            if img_path.exists():
                pic_w = Inches(10.5)
                pic = slide.shapes.add_picture(str(img_path), Inches(1.4), y, width=pic_w)
                y += pic.height + Inches(0.1)
        if y > bottom:
            break  # safety: don't overflow off the slide
    return y


def build():
    text = MD.read_text(encoding="utf-8")
    # Presenter-only back matter is not a slide.
    text = re.split(r"\n## Presenter source notes\n", text, maxsplit=1)[0]
    chunks = parse_chunks(text)
    # Merge the deck-title chunk with section 1 ("RehabKG") — they are the
    # same content, matching the original 18-slide structure. Keep the
    # section's ### subtitle next to the # title so the header loop sees it.
    if len(chunks) >= 2:
        first = "\n".join(chunks[0])
        second_lines = chunks[1]
        second = "\n".join(second_lines)
        if re.search(r"^# ", first, re.M) and re.search(r"^## 1\. ", second, re.M):
            sub_line = next((l for l in second_lines if l.strip().startswith("### ")), None)
            ch1_rest = [l for l in second_lines
                        if not l.strip().startswith(("## 1.", "### "))]
            ch0_rest = [l for l in chunks[0] if not l.strip().startswith("# ")]
            ch0_title = next(l for l in chunks[0] if l.strip().startswith("# "))
            merged = [ch0_title] + ([sub_line] if sub_line else []) + ch0_rest + ch1_rest
            chunks = [merged] + chunks[2:]
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    total = len(chunks)

    for idx, chunk in enumerate(chunks):
        lines = chunk
        # header: # title (chunk 0) or ## N. Title / ### subtitle, allowing
        # blank lines between them
        title = ""
        subtitle = None
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                i += 1
                continue
            if s.startswith("### "):
                subtitle = s[4:].strip()
                i += 1
            elif s.startswith("## "):
                title = s[3:].strip()
                i += 1
            elif s.startswith("# "):
                title = s[2:].strip()
                i += 1
            else:
                break
        rest = lines[i:]
        content, notes = split_notes(rest)

        slide = slide_base(prs)
        if idx == 0:
            # title slide
            box = slide.shapes.add_textbox(Inches(0.9), Inches(2.2), Inches(11.5), Inches(2.6))
            tf = box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = title
            run.font.size = Pt(40)
            run.font.bold = True
            run.font.color.rgb = NAVY
            if subtitle:
                p1 = tf.add_paragraph()
                run1 = p1.add_run()
                run1.text = subtitle
                run1.font.size = Pt(20)
                run1.font.color.rgb = ACCENT
            for line in content:
                s = line.strip()
                if not s:
                    continue
                if s.startswith(">"):
                    continue  # presenter framing goes to notes, not the slide
                p2 = tf.add_paragraph()
                add_inline_runs(p2, s, Pt(16), color=DARK)
            # move framing quote into notes too if present
            quote = " ".join(l.strip().lstrip("> ").strip() for l in content if l.strip().startswith(">"))
            if quote:
                notes = (quote + " " + notes).strip()
        else:
            add_title(slide, title, subtitle)
            blocks = classify_body(content)
            y_end = render_blocks(slide, blocks)
            if y_end > Inches(7.0):
                print(f"WARNING: slide {idx + 1} ({title}) may overflow")
        add_page_number(slide, idx + 1, total)
        if notes:
            slide.notes_slide.notes_text_frame.text = notes

    prs.save(OUT)
    print(f"Wrote {OUT.name}: {total} slides")


if __name__ == "__main__":
    build()
