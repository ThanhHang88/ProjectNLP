"""Sinh slide theo template HUST (4:3):  python report/build/make_slides.py
-> report/Slide_TrichRutThongTin_HoaDon.pptx

Mở template_hust.pptx, giữ trang bìa (slide 3) và trang cảm ơn (slide 13), xoá các slide mẫu còn lại,
rồi thêm slide nội dung bằng các layout của template. Số liệu đọc từ report/results.json.
"""
import copy
import json
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
R = json.loads((ROOT / "report" / "results.json").read_text(encoding="utf-8"))
S, M = R["datasets"]["sroie"]["by_method"], R["datasets"]["mcocr"]["by_method"]
ST, TOK, SIDE = R["dataset_stats"], R["tokens"], R["side_experiments"]
METHODS = R["methods"]
ORDER = [m["method"] for m in METHODS]
FIELDS = ["seller", "address", "date", "total"]

# ---------------------------------------------------------------- màu HUST (lấy từ template)
RED, GOLD = RGBColor(0xC0, 0x20, 0x34), RGBColor(0xE8, 0xA3, 0x18)
DARK, GRAY, MUTED = RGBColor(0x1F, 0x29, 0x33), RGBColor(0x52, 0x60, 0x6D), RGBColor(0x7B, 0x87, 0x94)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
T_RED, T_GOLD, T_GRAY = RGBColor(0xFB, 0xEA, 0xEC), RGBColor(0xFD, 0xF3, 0xE1), RGBColor(0xF3, 0xF4, 0xF6)
CODE_BG = RGBColor(0x2B, 0x2F, 0x36)
SERIES = [RGBColor(0x9A, 0xA5, 0xB1), RGBColor(0x8E, 0x18, 0x27), RGBColor(0xC0, 0x20, 0x34),
          RGBColor(0xB4, 0x53, 0x09), GOLD]
FONT, MONO = "Arial", "Courier New"

mac = lambda D, m: f'{D[m]["macro_f1"]:.1f}'
def sec(D, m):
    v = D[m]["latency_ms_median"] / 1000
    return f"{v:.1f}" if v < 10 else f"{v:.0f}"

# ---------------------------------------------------------------- mở template, dọn slide mẫu
prs = Presentation(str(HERE / "template_hust.pptx"))
LAYOUT = {l.name: l for l in prs.slide_layouts}
sld_ids = prs.slides._sldIdLst
ids = list(sld_ids)
title_slide, thanks_id = prs.slides[2], ids[12]
for i, sid in enumerate(ids):
    if i not in (2, 12):
        prs.part.drop_rel(sid.rId)
        sld_ids.remove(sid)


# ---------------------------------------------------------------- helpers
def add_slide_number(slide):
    for ph in slide.slide_layout.placeholders:
        if ph.placeholder_format.type is not None and "SLIDE_NUMBER" in str(ph.placeholder_format.type):
            slide.shapes._spTree.append(copy.deepcopy(ph._element))
            return


def remove_placeholders(slide, keep_title=True):
    for ph in list(slide.placeholders):
        if keep_title and ph.placeholder_format.idx == 0:
            continue
        ph._element.getparent().remove(ph._element)


def content_slide(title, notes=""):
    s = prs.slides.add_slide(LAYOUT["1_Comparison"])
    remove_placeholders(s)
    s.shapes.title.text = title
    add_slide_number(s)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def section_slide(title, lines, notes=""):
    s = prs.slides.add_slide(LAYOUT["1_Title Only"])
    s.shapes.title.text = title
    body = [p for p in s.placeholders if p.placeholder_format.idx == 13][0]
    tf = body.text_frame
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        for r in p.runs:
            r.font.size, r.font.name, r.font.color.rgb = Pt(20), FONT, DARK
        p.space_after = Pt(10)
    add_slide_number(s)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def _set_bullet(p, char="•"):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.25)))
    pPr.set("indent", str(-Inches(0.2)))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", char)


def text(slide, x, y, w, h, content, size=14, color=DARK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font=FONT, bullets=False, gap=4, name=None):
    """content: str | list[str] (đoạn) | list[list[(text, {opts})]] (đoạn gồm nhiều run)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = content if isinstance(content, list) else [content]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(gap)
        runs = para if isinstance(para, list) else [(para, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = o.get("color", color)
        if bullets:
            _set_bullet(p)
    return tb


def box(slide, x, y, w, h, fill, rounded=True, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        shp.adjustments[0] = 0.08
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def badge(slide, x, y, label, fill, d=0.5, size=13):
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    c.fill.solid()
    c.fill.fore_color.rgb = fill
    c.line.fill.background()
    c.shadow.inherit = False
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(size), True, FONT, WHITE


def code(slide, x, y, w, h, lines, size=11):
    box(slide, x, y, w, h, CODE_BG)
    text(slide, x + 0.2, y + 0.18, w - 0.4, h - 0.36, lines, size=size, color=RGBColor(0xF1, 0xF3, 0xF5),
         font=MONO, gap=0)


def table(slide, x, y, w, rows, col_w, size=11, row_h=0.3, head_fill=RED, best=None):
    """rows[0] là tiêu đề. best: tập (r, c) cần tô đậm."""
    nr, nc = len(rows), len(rows[0])
    gt = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
    tbl = gt.table
    tblPr = tbl._tbl.tblPr
    for a in ("bandRow", "firstRow"):
        tblPr.set(a, "0")
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # No Style, Table Grid
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i in range(nr):
        tbl.rows[i].height = Inches(row_h)
        for j in range(nc):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = head_fill if i == 0 else (T_GRAY if i % 2 else WHITE)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(rows[i][j])
            is_best = best and (i, j) in best
            r.font.name, r.font.size = FONT, Pt(size)
            r.font.bold = i == 0 or is_best or (j == 0 and head_fill == RED and nc <= 3)
            r.font.color.rgb = WHITE if i == 0 else (RED if is_best else DARK)
    return gt


def bar_chart(slide, x, y, w, h, categories, series, title, horizontal=False, colors=None, legend=True,
              max_val=100, number_format='0.0', label_size=9):
    cd = CategoryChartData()
    cd.categories = categories
    for name, vals in series:
        cd.add_series(name, vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    ch = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    ch.font.name, ch.font.size, ch.font.color.rgb = FONT, Pt(10), DARK
    ch.has_title = True
    ch.chart_title.text_frame.text = title
    tp = ch.chart_title.text_frame.paragraphs[0]
    tp.runs[0].font.size, tp.runs[0].font.bold, tp.runs[0].font.name = Pt(12), False, FONT
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.overlap = 0 if not horizontal else 0
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format, dl.number_format_is_linked = number_format, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size, dl.font.name, dl.font.color.rgb = Pt(label_size), FONT, DARK
    for i, s_ in enumerate(plot.series):
        s_.format.fill.solid()
        s_.format.fill.fore_color.rgb = (colors or SERIES)[i % len(colors or SERIES)]
        s_.invert_if_negative = False
    va, ca = ch.value_axis, ch.category_axis
    va.maximum_scale, va.minimum_scale = max_val, 0
    va.has_major_gridlines = not horizontal
    if va.has_major_gridlines:
        va.major_gridlines.format.line.color.rgb = RGBColor(0xE4, 0xE7, 0xEB)
    va.visible = not horizontal
    va.tick_labels.font.size, va.tick_labels.font.color.rgb = Pt(9), MUTED
    va.format.line.fill.background()
    ca.tick_labels.font.size, ca.tick_labels.font.color.rgb = Pt(11), DARK
    ca.format.line.color.rgb = RGBColor(0xC8, 0xCD, 0xD2)
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size, ch.legend.font.name = Pt(9), FONT
    return ch


# ================================================================ 1. TRANG BÌA (slide mẫu số 3)
tbs = [sh for sh in title_slide.shapes if sh.has_text_frame]
def set_text(shape, paras, size, color, bold):
    tf = shape.text_frame
    tf.word_wrap = True
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    p0 = tf.paragraphs[0]
    for r in list(p0.runs):
        r._r.getparent().remove(r._r)
    for i, t in enumerate(paras):
        p = p0 if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = t
        r.font.size, r.font.bold, r.font.color.rgb = Pt(size), bold, color

tbs[0].top, tbs[0].height, tbs[0].width = Inches(2.15), Inches(1.5), Inches(7.2)
set_text(tbs[0], ["TRÍCH RÚT THÔNG TIN", "HOÁ ĐƠN → JSON / CSDL"], 30, RED, True)
tbs[1].top, tbs[1].height, tbs[1].width = Inches(3.85), Inches(1.2), Inches(6.6)
set_text(tbs[1], ["So sánh API mô hình ngôn ngữ lớn và mô hình công khai",
                  "trên hoá đơn tiếng Anh (SROIE) và tiếng Việt (MC-OCR)"], 15, DARK, False)
text(title_slide, 0.45, 5.45, 6.0, 1.3, [
    [("Môn: ", {"bold": True}), ("Xử lý ngôn ngữ tự nhiên", {})],
    [("Sinh viên: ", {"bold": True}), ("[Họ tên] – [MSSV]", {})],
    [("GVHD: ", {"bold": True}), ("[Họ tên giảng viên]", {})],
], size=13, color=GRAY, gap=3)
title_slide.notes_slide.notes_text_frame.text = (
    "Giới thiệu đề tài: trích rút thông tin từ tài liệu thành JSON và lưu cơ sở dữ liệu, dùng API và mô hình "
    "công khai. Đối tượng là hoá đơn bán lẻ, hai bộ dữ liệu tiếng Anh và tiếng Việt.")

# ================================================================ 2. BÀI TOÁN
s = content_slide("Bài toán: văn bản OCR → bản ghi có cấu trúc",
                  "Đầu vào là văn bản OCR, có thể có lỗi nhận dạng. Đầu ra là JSON đúng lược đồ 4 trường, "
                  "ghi vào SQLite. Đây là bài toán Key Information Extraction.")
code(s, 0.4, 1.15, 4.15, 3.0, ["MINIMART ANAN", "Chợ Sủi Phú Thị Gia Lâm", "HÓA ĐƠN BÁN HÀNG",
                               "Sữa TH true milk  20,000", "Tổng cộng :     74,000", "Tiền khách trả: 24,000",
                               "Ngày: 11/08/2020-08:06"], size=12)
text(s, 0.4, 4.25, 4.15, 0.3, "Đầu vào: text OCR của 1 hoá đơn", size=11, color=GRAY)
arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.68), Inches(2.4), Inches(0.6), Inches(0.5))
arrow.fill.solid(); arrow.fill.fore_color.rgb = GOLD; arrow.line.fill.background(); arrow.shadow.inherit = False
box(s, 5.4, 1.15, 4.2, 3.0, T_RED)
text(s, 5.6, 1.4, 3.9, 2.6, ["{", '  "seller":  "MINIMART ANAN",', '  "address": "Chợ Sủi Phú Thị',
                             '              Gia Lâm",', '  "date":    "11/08/2020 08:06",',
                             '  "total":   "74,000"', "}"], size=12, font=MONO, color=DARK, gap=0)
text(s, 5.4, 4.25, 4.2, 0.3, "Đầu ra: JSON 4 trường → lưu SQLite", size=11, color=GRAY)
box(s, 0.4, 4.85, 9.2, 1.2, T_GRAY)
text(s, 0.65, 5.05, 8.7, 0.9, [
    [("Bài toán KIE / slot filling: ", {"bold": True, "color": RED}),
     ("điền 4 trường seller · address · date · total; null nếu không có.", {})],
    [("So sánh: ", {"bold": True, "color": RED}),
     ("baseline luật (regex) · API (DeepSeek) · mô hình công khai (Qwen2.5 3B/7B).", {})],
], size=15, gap=8)

# ================================================================ SECTION: DỮ LIỆU & PHƯƠNG PHÁP
section_slide("Dữ liệu & phương pháp", ["Hai bộ dữ liệu, một lược đồ chung", "Bổ sung OCR cho MC-OCR",
                                         "Quy trình và 5 phương pháp", "Prompt, JSON Schema, SQLite, đánh giá"])

# ================================================================ 3. DỮ LIỆU
s = content_slide("Hai bộ dữ liệu, một lược đồ chung",
                  "Hai bộ dữ liệu có cùng 4 trường nên dùng chung lược đồ, prompt và cách đánh giá. SROIE có text "
                  "OCR sạch; MC-OCR là ảnh chụp điện thoại, chúng tôi phải tự OCR.")
def ds_card(x, title, sub, stats, fill):
    box(s, x, 1.1, 4.5, 3.05, fill)
    text(s, x + 0.25, 1.25, 4.0, 0.45, title, size=20, bold=True, color=RED)
    text(s, x + 0.25, 1.72, 4.0, 0.35, sub, size=11, color=GRAY)
    for i, (n, lab) in enumerate(stats):
        text(s, x + 0.25 + i * 1.4, 2.3, 1.35, 0.6, n, size=26, bold=True, color=DARK)
        text(s, x + 0.25 + i * 1.4, 2.95, 1.3, 1.0, lab, size=10.5, color=GRAY)
ds_card(0.4, "SROIE", "ICDAR 2019 · hoá đơn Malaysia · tiếng Anh",
        [(str(ST["sroie"]["n_test"]), "hoá đơn test\n(chia sẵn)"), (str(ST["sroie"]["avg_lines"]), "dòng / hoá đơn"),
         ("Sạch", "text OCR đã được\nngười kiểm tra")], T_GRAY)
ds_card(5.1, "MC-OCR 2021", "RIVF 2021 · ảnh điện thoại · tiếng Việt",
        [(str(ST["mcocr"]["n_test"]), "hoá đơn test\n(tự chia, seed 42)"), (str(ST["mcocr"]["avg_lines"]), "dòng / hoá đơn"),
         ("OCR", "tự chạy VietOCR,\ncòn lỗi dấu")], T_GOLD)
text(s, 0.4, 4.4, 6, 0.35, "Ánh xạ nhãn → lược đồ chung", size=13, bold=True, color=DARK)
for i, (a, b, c) in enumerate([("company", "SELLER", "seller"), ("address", "ADDRESS", "address"),
                               ("date", "TIMESTAMP", "date"), ("total", "TOTAL_COST", "total")]):
    x = 0.4 + i * 2.33
    box(s, x, 4.85, 2.17, 1.15, T_RED)
    text(s, x + 0.15, 4.95, 1.9, 0.4, f"{a} / {b}", size=10, color=GRAY)
    text(s, x + 0.15, 5.4, 1.9, 0.45, f"→ {c}", size=16, bold=True, color=RED, font=MONO)
text(s, 0.4, 6.2, 9.2, 0.45, f"Cả hai bộ: {ST['sroie']['n_total']} + {ST['mcocr']['n_total']} hoá đơn; MC-OCR lệch nguồn "
     "(VinCommerce và MINIMART ANAN ≈ 50%).", size=11, color=GRAY)

# ================================================================ 4. MC-OCR THIẾU TEXT
s = content_slide("MC-OCR thiếu text OCR – giải bằng VietOCR",
                  "Bản MC-OCR trên Kaggle có gần một nửa ô chữ rỗng. Nếu dùng nguyên, đáp án không có trong đầu vào. "
                  "Chúng tôi chạy lại OCR bằng VietOCR trên Colab.")
text(s, 0.4, 1.1, 2.6, 1.1, "49%", size=60, bold=True, color=RED)
text(s, 0.4, 2.25, 2.6, 1.2, "ô chữ trong dataset Kaggle có nội dung rỗng – đúng ở các ô cần trích", size=13)
bar_chart(s, 3.05, 1.0, 3.4, 3.1, ["SELLER", "TIMESTAMP", "TOTAL_COST", "ADDRESS"],
          [("Ô rỗng (%)", (32, 37, 38, 61))], "Tỉ lệ ô rỗng theo trường", horizontal=True,
          colors=[RED], legend=False, max_val=75, number_format='0"%"', label_size=10)
box(s, 6.6, 1.1, 3.0, 3.0, T_GRAY)
text(s, 6.8, 1.25, 2.6, 0.4, "Giải pháp", size=15, bold=True, color=RED)
text(s, 6.8, 1.7, 2.65, 2.3, ["Giữ vị trí các ô chữ có sẵn", "Cắt ảnh từng ô, nhận dạng lại bằng VietOCR",
                              "GPU Colab, 40.868 ô", "Sắp dòng theo toạ độ"], size=12, bullets=True, gap=5)
box(s, 0.4, 4.4, 9.2, 1.55, T_GOLD)
text(s, 0.65, 4.6, 8.7, 1.25, [
    [("Hệ quả: ", {"bold": True, "color": RED}),
     ("text MC-OCR là OCR máy, có lỗi thật (\"Cảm Phà\" thay vì \"Cẩm Phả\", \"0B\" thay vì \"08\"), trong khi nhãn "
      "đã được người sửa → so khớp chính xác khắt khe hơn SROIE.", {})],
    [("Không dùng file CSV làm đầu vào ", {"bold": True, "color": RED}),
     ("vì nó chỉ chứa text của chính đáp án (lộ đáp án).", {})],
], size=14, gap=10)

# ================================================================ 5. QUY TRÌNH
s = content_slide("Quy trình xử lý",
                  "Sáu bước. Bước trích rút là chỗ duy nhất khác nhau giữa các phương pháp; mọi thứ khác dùng "
                  "chung để so sánh công bằng.")
steps = [("Dữ liệu", "Ảnh + nhãn SROIE, MC-OCR"), ("OCR", "Text có sẵn hoặc VietOCR (Colab)"),
         ("Trích rút", "M0–M4, cùng prompt + schema"), ("Kiểm tra", "Parse JSON, khoá thiếu → null"),
         ("Lưu CSDL", "SQLite: documents, gold, extractions"), ("Đánh giá", "Chuẩn hoá → P / R / F1")]
for i, (h, d) in enumerate(steps):
    x, y = 0.4 + (i % 3) * 3.1, 1.15 + (i // 3) * 1.75
    hl = i == 2
    box(s, x, y, 2.9, 1.5, T_RED if hl else T_GRAY)
    badge(s, x + 0.2, y + 0.2, str(i + 1), RED if hl else GRAY, d=0.48)
    text(s, x + 0.85, y + 0.22, 1.95, 0.45, h, size=16, bold=True, color=RED if hl else DARK)
    text(s, x + 0.85, y + 0.68, 1.95, 0.75, d, size=11, color=GRAY)
for i in (0, 1, 3, 4):
    x, y = 0.4 + (i % 3) * 3.1 + 2.92, 1.15 + (i // 3) * 1.75 + 0.6
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(0.16), Inches(0.28))
    a.fill.solid(); a.fill.fore_color.rgb = GOLD; a.line.fill.background(); a.shadow.inherit = False
box(s, 0.4, 4.85, 9.2, 1.3, T_GOLD)
text(s, 0.65, 5.05, 8.7, 1.0, [
    [("Thiết kế để chạy lại an toàn: ", {"bold": True, "color": RED}),
     ("UNIQUE(doc_id, method) trong bảng extractions làm cache – bị ngắt mạng hay hết quota thì chạy lại, "
      "không gọi lại API cho hoá đơn đã xong.", {})],
    [("Đánh giá ", {"bold": True, "color": RED}), ("chỉ là 1 câu JOIN với bảng gold.", {})],
], size=14, gap=8)

# ================================================================ 6. PHƯƠNG PHÁP
s = content_slide("Năm phương pháp, ba nhóm",
                  "M0 là baseline. M1, M2 là API DeepSeek, khác nhau ở có ví dụ mẫu hay không. M3, M4 là mô hình công "
                  "khai Qwen2.5 chạy bằng Ollama. Mọi mô hình ngôn ngữ dùng cùng system prompt và lược đồ JSON.")
rows = [("M0", "Regex + heuristic", "Baseline luật", "Từ khoá TOTAL / Tổng cộng, mẫu ngày, dòng đầu = người bán", SERIES[0]),
        ("M1", "DeepSeek zero-shot", "API", "deepseek-chat, JSON mode, temperature 0", SERIES[1]),
        ("M2", "DeepSeek few-shot", "API", "Thêm 2 hoá đơn mẫu cùng bộ dữ liệu", SERIES[2]),
        ("M3", "Qwen2.5-3B", "Model public", "Ollama trên CPU laptop, ép JSON Schema", SERIES[3]),
        ("M4", "Qwen2.5-7B", "Model public", "Ollama trên GPU T4 Colab, cùng prompt", SERIES[4])]
for i, (c, n, k, d, col) in enumerate(rows):
    y = 1.15 + i * 1.08
    box(s, 0.4, y, 9.2, 0.92, T_GRAY if i % 2 == 0 else WHITE, line=None if i % 2 == 0 else RGBColor(0xE4, 0xE7, 0xEB))
    badge(s, 0.58, y + 0.2, c, col, d=0.52, size=12)
    text(s, 1.3, y + 0.1, 2.4, 0.72, n, size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 3.7, y + 0.1, 1.5, 0.72, k, size=12, bold=True, color=RED if k != "Baseline luật" else GRAY,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 5.2, y + 0.1, 4.25, 0.72, d, size=12, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ 7. PROMPT / SCHEMA / DB
s = content_slide("Prompt chung, JSON Schema và SQLite",
                  "Prompt viết bằng tiếng Anh nhưng xử lý được cả hoá đơn tiếng Việt. Ollama ép đầu ra đúng JSON Schema; "
                  "DeepSeek dùng JSON mode. Kết quả mọi phương pháp ghi chung một bảng.")
text(s, 0.4, 1.05, 4.5, 0.35, "System prompt (rút gọn)", size=13, bold=True)
code(s, 0.4, 1.45, 4.5, 3.0, ["Extract from ONE receipt", "a JSON object:", "- seller: store/company name",
                              "- address: seller's address", "- date: purchase date", "- total: final amount to pay",
                              "Copy values, don't translate;", "null if absent. JSON only."], size=11)
text(s, 5.1, 1.05, 4.5, 0.35, "Lược đồ ép đầu ra", size=13, bold=True)
code(s, 5.1, 1.45, 4.5, 3.0, ['{"type": "object",', ' "properties": {', '  "seller":  {"type":',
                              '     ["string","null"]},', '  "address": {...},', '  "date":    {...},',
                              '  "total":   {...}},', ' "required": [4 trường]}'], size=11)
box(s, 0.4, 4.7, 9.2, 1.35, T_RED)
text(s, 0.65, 4.9, 8.7, 1.05, [
    [("SQLite invoices.db: ", {"bold": True, "color": RED}),
     ("documents (text đầu vào) · gold (nhãn) · extractions (kết quả + model_version, latency, token, valid_json).", {})],
    [("Ngày / tiền giữ nguyên chuỗi, chuẩn hoá bằng code để nhất quán.", {"italic": True, "color": GRAY})],
], size=14, gap=8)

# ================================================================ 8. ĐÁNH GIÁ
s = content_slide("Đánh giá: chuẩn hoá rồi so khớp",
                  "So khớp chính xác sau chuẩn hoá. Chúng tôi phát hiện và sửa một lỗi trong hàm chuẩn hoá ngày (bắt "
                  "nhầm giờ thành tháng) rồi chấm lại toàn bộ.")
ev = [("seller, address", "chữ thường, NFC, bỏ dấu câu + khoảng trắng", '"OJC Marketing, SDN BHD" → ojcmarketingsdnbhd'),
      ("date", "về YYYY-MM-DD, chỉ nhận ngày hợp lệ", '"Ngày: 11/08/2020 - 21:19" → 2020-08-11'),
      ("total", "đọc số, phân biệt dấu nghìn / thập phân", '"12.500đ" → 12500 · "RM 1,234.50" → 1234.5')]
for i, (f, r_, e) in enumerate(ev):
    y = 1.15 + i * 1.15
    box(s, 0.4, y, 5.9, 1.0, T_GRAY)
    text(s, 0.6, y + 0.12, 1.45, 0.76, f, size=13, bold=True, color=RED, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 2.1, y + 0.12, 4.1, 0.76, [[(r_, {})], [(e, {"font": MONO, "size": 9.5, "color": GRAY})]],
         size=12, anchor=MSO_ANCHOR.MIDDLE, gap=2)
box(s, 6.5, 1.15, 3.1, 3.3, RED)
text(s, 6.75, 1.35, 2.65, 3.0, [
    [("Precision", {"bold": True, "color": GOLD})], [("đúng / số dự đoán khác rỗng", {})],
    [("Recall", {"bold": True, "color": GOLD})], [("đúng / số nhãn khác rỗng", {})],
    [("Macro-F1", {"bold": True, "color": GOLD})], [("trung bình F1 của 4 trường", {})],
], size=13, color=WHITE, gap=3)
box(s, 0.4, 4.75, 9.2, 1.3, T_GOLD)
text(s, 0.65, 4.95, 8.7, 1.0, [
    [("Soft F1: ", {"bold": True, "color": RED}),
     ("seller/address giống ≥ 90% (rapidfuzz) cũng tính đúng – đo riêng ảnh hưởng của lỗi vài ký tự do OCR.", {})],
    [("Chỉ số phụ: ", {"bold": True, "color": RED}), ("% JSON hợp lệ, thời gian trung vị, số token.", {})],
], size=14, gap=8)

# ================================================================ SECTION: KẾT QUẢ
section_slide("Kết quả", ["Tổng thể: LLM so với regex", "Theo từng trường", "API hay mô hình công khai?",
                          "Few-shot và tiếng Anh / tiếng Việt"])

# ================================================================ 9. KẾT QUẢ TỔNG THỂ
s = content_slide("LLM vượt baseline rõ rệt trên cả hai ngôn ngữ",
                  f"Mọi mô hình ngôn ngữ vượt regex. DeepSeek few-shot tốt nhất ở cả hai bộ. Qwen-7B đạt {mac(S, 'qwen2.5-7b')} "
                  f"trên SROIE, gần bằng DeepSeek zero-shot {mac(S, 'deepseek-zs')}. Tiếng Việt thấp hơn khoảng 20 điểm.")
bar_chart(s, 0.25, 1.0, 6.45, 5.75, ["SROIE (EN)", "MC-OCR (VI)"],
          [(f'{m["code"]} {m["label"]}', (S[m["method"]]["macro_f1"], M[m["method"]]["macro_f1"])) for m in METHODS],
          "Macro-F1 (%) trên tập test")
def callout(y, big, small, col):
    text(s, 6.95, y, 2.65, 0.75, big, size=34, bold=True, color=col)
    text(s, 6.95, y + 0.78, 2.65, 0.7, small, size=11.5, color=GRAY)
callout(1.25, f"{mac(S, 'deepseek-fs')}%", "SROIE – DeepSeek few-shot, tốt nhất", RED)
callout(3.0, f"+{S['deepseek-fs']['macro_f1'] - S['regex']['macro_f1']:.1f}", "điểm so với regex trên SROIE", RED)
callout(4.75, f"{mac(M, 'deepseek-fs')}%", "MC-OCR – vẫn tốt nhất nhưng thấp hơn nhiều", RGBColor(0xB4, 0x53, 0x09))

# ================================================================ 10. THEO TRƯỜNG
s = content_slide("Theo trường: date dễ, address tiếng Việt khó",
                  "Trường date gần như được giải quyết. Address tiếng Việt thấp chủ yếu do lỗi dấu từ OCR và quy ước "
                  "nhãn – soft F1 cho thấy mô hình thường lấy đúng vùng địa chỉ.")
def field_rows(D, name):
    best_v = [max(D[m]["f1"][f] for m in ORDER) for f in FIELDS]
    rows = [[name, "seller", "address", "date", "total", "Macro"]]
    best = set()
    for i, m in enumerate(METHODS):
        vals = [D[m["method"]]["f1"][f] for f in FIELDS]
        rows.append([f'{m["code"]} {m["label"].split(" (")[0]}'] + [f"{v:.1f}" for v in vals] +
                    [f'{D[m["method"]]["macro_f1"]:.1f}'])
        for j, v in enumerate(vals):
            if v == best_v[j]:
                best.add((i + 1, j + 1))
    bm = max(D[m]["macro_f1"] for m in ORDER)
    for i, m in enumerate(METHODS):
        if D[m["method"]]["macro_f1"] == bm:
            best.add((i + 1, 5))
    return rows, best
for k, (D, nm, y) in enumerate([(S, "SROIE (EN)", 1.05), (M, "MC-OCR (VI)", 3.05)]):
    rows, best = field_rows(D, nm)
    table(s, 0.4, y, 9.2, rows, [3.0, 1.24, 1.24, 1.24, 1.24, 1.24], size=11, row_h=0.3, best=best)
box(s, 0.4, 5.05, 9.2, 1.2, T_GRAY)
text(s, 0.65, 5.2, 8.7, 0.95, [
    f'date ≈ 99% trên SROIE với mọi LLM; total tăng mạnh nhất so với regex ({S["regex"]["f1"]["total"]:.1f} → '
    f'{S["deepseek-fs"]["f1"]["total"]:.1f}).',
    f'address MC-OCR ≤ {max(M[m]["f1"]["address"] for m in ORDER):.1f}% so khớp chính xác, nhưng soft F1 lên '
    f'{M["deepseek-fs"]["soft_f1"]["address"]:.1f}% → nhiều lỗi chỉ sai vài ký tự do OCR.',
    "Số đỏ đậm = tốt nhất mỗi cột.",
], size=12.5, bullets=True, gap=4)

# ================================================================ 11. API vs PUBLIC
s = content_slide("API hay mô hình công khai? Một phép đánh đổi",
                  "Cả ba lựa chọn đều cho 100% JSON hợp lệ. API tốt và nhanh nhất nhưng phụ thuộc nhà cung cấp và gửi "
                  "dữ liệu ra ngoài. Qwen-7B là điểm cân bằng tốt nếu có GPU.")
cols = [("API · DeepSeek", SERIES[2], f"{mac(S, 'deepseek-zs')} / {mac(S, 'deepseek-fs')}", f"~{sec(S, 'deepseek-zs')} s",
         ["Tốt và nhanh nhất", "Không cần phần cứng", "Trả tiền theo token", "Hoá đơn gửi ra bên thứ ba"], T_RED),
        ("Qwen2.5-7B · GPU", GOLD, mac(S, "qwen2.5-7b"), f"~{sec(S, 'qwen2.5-7b')} s",
         ["Gần bằng API zero-shot", "Dữ liệu ở hạ tầng mình", "Cần GPU (Colab T4)", "Kết quả lặp lại được"], T_GOLD),
        ("Qwen2.5-3B · CPU", SERIES[3], mac(S, "qwen2.5-3b"), f"~{sec(S, 'qwen2.5-3b')} s",
         ["Chạy trên laptop 16 GB", "Miễn phí, offline", "Chậm, máy nóng", "Kém ở seller / address"], T_GRAY)]
for i, (h, col, f, t, pts, fill) in enumerate(cols):
    x = 0.4 + i * 3.1
    box(s, x, 1.1, 2.95, 4.35, fill)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.2), Inches(1.32), Inches(0.24), Inches(0.24))
    c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background(); c.shadow.inherit = False
    text(s, x + 0.55, 1.22, 2.3, 0.45, h, size=13.5, bold=True)
    text(s, x + 0.2, 1.8, 2.6, 0.6, f, size=26, bold=True, color=RED)
    text(s, x + 0.2, 2.42, 2.6, 0.3, "Macro-F1 SROIE (%)", size=10, color=GRAY)
    text(s, x + 0.2, 2.85, 2.6, 0.55, t, size=22, bold=True)
    text(s, x + 0.2, 3.42, 2.6, 0.3, "thời gian trung vị / hoá đơn", size=10, color=GRAY)
    text(s, x + 0.2, 3.95, 2.6, 2.5, pts, size=12, bullets=True, gap=5)

# ================================================================ 12. FEW-SHOT & EN/VI
s = content_slide("Few-shot dạy quy ước; tiếng Việt khó vì dữ liệu",
                  "Few-shot giúp nhiều nhất ở trường seller vì đó là trường phụ thuộc quy ước gán nhãn. Khoảng cách tiếng "
                  "Anh – tiếng Việt chủ yếu đến từ chất lượng OCR và nhãn, không phải khả năng hiểu tiếng Việt.")
box(s, 0.4, 1.1, 4.5, 4.3, T_RED)
text(s, 0.65, 1.3, 4.0, 0.4, "Zero-shot → few-shot (DeepSeek)", size=14, bold=True)
text(s, 0.65, 1.85, 2.0, 0.8, f'+{S["deepseek-fs"]["f1"]["seller"] - S["deepseek-zs"]["f1"]["seller"]:.1f}',
     size=34, bold=True, color=RED)
text(s, 0.65, 2.7, 2.0, 0.5, "điểm F1 seller SROIE", size=10.5, color=GRAY)
text(s, 2.7, 1.85, 2.0, 0.8, f'+{M["deepseek-fs"]["f1"]["seller"] - M["deepseek-zs"]["f1"]["seller"]:.1f}',
     size=34, bold=True, color=RED)
text(s, 2.7, 2.7, 2.0, 0.5, "điểm F1 seller MC-OCR", size=10.5, color=GRAY)
text(s, 0.65, 3.45, 4.0, 3.0, ['Ví dụ dạy quy ước nhãn: bỏ mã số công ty "(519537-X)", dùng tên pháp nhân',
                               f'Đổi lại: token đầu vào ×{TOK["deepseek-fs"]["avg_in"] / TOK["deepseek-zs"]["avg_in"]:.1f} '
                               f'({TOK["deepseek-zs"]["avg_in"]} → {TOK["deepseek-fs"]["avg_in"]})'],
     size=12.5, bullets=True, gap=6)
box(s, 5.1, 1.1, 4.5, 4.3, T_GOLD)
text(s, 5.35, 1.3, 4.0, 0.4, "Tiếng Anh → tiếng Việt", size=14, bold=True)
text(s, 5.35, 1.85, 4.0, 0.8, f'−{S["deepseek-fs"]["macro_f1"] - M["deepseek-fs"]["macro_f1"]:.1f}',
     size=34, bold=True, color=RGBColor(0xB4, 0x53, 0x09))
text(s, 5.35, 2.7, 4.0, 0.5, "điểm Macro-F1 (DeepSeek few-shot)", size=10.5, color=GRAY)
text(s, 5.35, 3.45, 4.0, 3.0, ["Text là OCR máy, lỗi dấu và ký tự", 'Quy ước nhãn riêng (VinMart → "VinCommerce")',
                               'Nhãn nhiễu: "13/88/2020", TIMESTAMP = "Tổng tiền…"', "Ảnh chụp điện thoại: nghiêng, mờ"],
     size=12.5, bullets=True, gap=6)

# ================================================================ SECTION: PHÂN TÍCH & KẾT LUẬN
section_slide("Phân tích & kết luận", ["Các nhóm lỗi điển hình", "Thách thức khi dùng API miễn phí",
                                       "Kết luận và hướng phát triển"])

# ================================================================ 13. PHÂN TÍCH LỖI
s = content_slide("Phân tích lỗi: mô hình thường không sai một mình",
                  "Năm nhóm lỗi điển hình. Ở dòng cuối, mô hình trả lời đúng nhưng bị chấm sai vì nhãn của dataset sai.")
errs = [["Loại lỗi", "Nhãn (gold)", "Dự đoán"],
        ["Quy ước nhãn", "99 SPEED MART S/B", "99 SPEED MART S/B (519537-X)"],
        ["Lỗi OCR", "Chợ Sủi Phú Thị Gia Lâm", "Chợ Sủi Phù Thị Gia Lâm"],
        ["Nhầm con số", "TOTAL RM42.88", "CASH RM42.90 (tiền khách đưa)"],
        ["Tên pháp nhân", "VinCommerce", "VM+ QNH 88 Trần Phú"],
        ["Nhãn sai", "200,000 (tiền khách trả)", "74,000 (tổng cộng – đúng)"]]
gt = table(s, 0.4, 1.15, 9.2, errs, [2.0, 3.3, 3.9], size=12, row_h=0.5)
for i in range(1, 6):
    for j in (1, 2):
        gt.table.cell(i, j).text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    r = gt.table.cell(i, 0).text_frame.paragraphs[0].runs[0]
    r.font.bold, r.font.color.rgb = True, RED
box(s, 0.4, 4.45, 9.2, 1.45, T_GOLD)
text(s, 0.65, 4.65, 8.7, 1.15, [
    [("Bài học: ", {"bold": True, "color": RED}),
     ("nhiều \"lỗi\" đến từ OCR, quy ước gán nhãn hoặc nhãn sai, không chỉ từ mô hình.", {})],
    [("Hàm chuẩn hoá cũng phải được kiểm thử: ", {"bold": True, "color": RED}),
     ("đã sửa lỗi hiểu nhầm \"11/08/2020-21-19\" thành tháng 21 rồi chấm lại toàn bộ.", {})],
], size=14, gap=10)

# ================================================================ 14. API MIỄN PHÍ
s = content_slide("Dùng API miễn phí: các vấn đề thực tế",
                  "Đây là kinh nghiệm thực tế: API miễn phí có nhiều giới hạn ẩn. Đó cũng là lý do kết quả API chính thức "
                  "dùng DeepSeek trả phí.")
gz = SIDE.get("gemini-zs", {"n": 41, "blocked": 1})
issues = [("20", "lượt gọi / ngày", f"Gemini 3.5 Flash miễn phí → dừng ở {gz['n']} hoá đơn", T_GOLD),
          ("200K", "token / ngày", "Groq GPT-OSS-120B → ~300 hoá đơn / ngày", T_GOLD),
          (str(gz["blocked"]), "hoá đơn bị chặn", "Bộ lọc an toàn Gemini: PROHIBITED_CONTENT", T_GOLD),
          ("SSL", "lỗi mạng", "Tự thử lại với thời gian chờ tăng dần", T_GRAY)]
for i, (n, u, d, fill) in enumerate(issues):
    x, y = 0.4 + (i % 2) * 4.7, 1.1 + (i // 2) * 2.15
    box(s, x, y, 4.5, 1.95, fill)
    text(s, x + 0.25, y + 0.25, 1.75, 0.8, n, size=32, bold=True, color=RED)
    text(s, x + 0.25, y + 1.1, 1.75, 0.6, u, size=11, color=GRAY)
    text(s, x + 2.05, y + 0.25, 2.25, 1.45, d, size=13, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.4, 5.6, 9.2, 0.9, "→ Chuyển sang DeepSeek trả phí (rẻ, không giới hạn chặt). Cache theo (hoá đơn, phương pháp) "
     "giúp không mất kết quả khi bị gián đoạn.", size=13.5, bold=True, color=RED)

# ================================================================ 15. KẾT LUẬN (layout panel HUST)
s = prs.slides.add_slide(LAYOUT["1_Title Only"])
s.shapes.title.text = "Kết luận & hướng phát triển"
body = [p for p in s.placeholders if p.placeholder_format.idx == 13][0]
body._element.getparent().remove(body._element)
text(s, 3.85, 1.15, 5.8, 2.4, [
    f"LLM + JSON Schema: 100% JSON hợp lệ, Macro-F1 {mac(S, 'deepseek-fs')}% (EN) và {mac(M, 'deepseek-fs')}% (VI), "
    "vượt xa regex",
    f"Mô hình công khai 7B đạt {mac(S, 'qwen2.5-7b')}% trên SROIE – lựa chọn tốt khi cần giữ dữ liệu nội bộ",
    "Với tiếng Việt, nút thắt là chất lượng OCR và nhãn",
], size=15, bullets=True, gap=12)
box(s, 3.85, 3.7, 5.8, 1.3, T_GOLD)
text(s, 4.05, 3.85, 5.4, 1.05, [
    [("Hướng phát triển", {"bold": True, "color": RED})],
    [("OCR tốt hơn hoặc mô hình đọc ảnh · fine-tune LoRA · thêm danh sách mặt hàng · demo Streamlit", {})],
], size=13, gap=6)
add_slide_number(s)
s.notes_slide.notes_text_frame.text = "Tóm tắt ba kết luận chính và hướng phát triển."

# ================================================================ CẢM ƠN – đưa về cuối
sld_ids.remove(thanks_id)
sld_ids.append(thanks_id)
thanks = prs.slides[len(prs.slides) - 1]
for sh in thanks.shapes:
    if sh.has_text_frame and "THANK" in sh.text_frame.text.upper():
        r = sh.text_frame.paragraphs[0].runs
        r[0].text = "XIN CẢM ƠN!"
        for extra in r[1:]:
            extra.text = ""
thanks.notes_slide.notes_text_frame.text = "Cảm ơn thầy/cô và các bạn đã lắng nghe. Mời đặt câu hỏi."

# Đánh số lại tên part (slide giữ từ template trùng tên với slide mới thêm)
from pptx.opc.packuri import PackURI
for i, sl in enumerate(prs.slides, 1):
    sl.part.partname = PackURI(f"/ppt/slides/slide{i}.xml")
    if sl.has_notes_slide:
        sl.notes_slide.part.partname = PackURI(f"/ppt/notesSlides/notesSlide{i}.xml")

prs.core_properties.title = "Trích rút thông tin hoá đơn → JSON/CSDL"
out = ROOT / "report" / "Slide_TrichRutThongTin_HoaDon.pptx"
prs.save(str(out))
print("Wrote", out, len(prs.slides), "slides")
