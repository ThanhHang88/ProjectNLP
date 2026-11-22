// Sinh slide: node make_slides.js -> ../Slide_TrichRutThongTin_HoaDon.pptx
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const R = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "results.json"), "utf8"));
const S = R.datasets.sroie.by_method, M = R.datasets.mcocr.by_method;
const st = R.dataset_stats, T = R.tokens, side = R.side_experiments;
const FIELDS = ["seller", "address", "date", "total"];
const ORDER = R.methods.map((m) => m.method);
const mac = (D, m) => D[m].macro_f1.toFixed(1);
const sec = (D, m) => { const v = D[m].latency_ms_median / 1000; return v < 10 ? v.toFixed(1) : v.toFixed(0); };

// ---------------------------------------------------------------- theme
const THEME = {
  name: "Receipt IE",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2933", lt1: "FFFFFF", dk2: "0B3B37", lt2: "EEF6F5",
    accent1: "0F766E", accent2: "14B8A6", accent3: "B45309", accent4: "F59E0B",
    accent5: "9AA5B1", accent6: "DC2626", hlink: "0F766E", folHlink: "0B3B37",
  },
};
const HEX = THEME.colors;
const SERIES = [HEX.accent5, HEX.accent1, HEX.accent2, HEX.accent3, HEX.accent4];

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Trích rút thông tin từ hoá đơn → JSON/CSDL";
pres.author = "[Họ tên sinh viên]";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.6, fontSize: 40, bold: true,
      color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.8, w: 11.7, h: 1.2, fontSize: 20,
      color: "CFE9E5", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "7B8794", align: "right" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 32, bold: true,
      color: C.text2, fontFace: THEME.headFontFace, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "Trích rút thông tin hoá đơn → JSON/CSDL", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: "7B8794", margin: 0 } } },
  ],
});

// ---------------------------------------------------------------- helpers
let SN = 0;
function slide(master, section) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  SN += 1;
  return s;
}
const T_ = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top", ...o });
function card(s, x, y, w, h, fill = HEX.lt2, name = "card") {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name });
}
function badge(s, x, y, txt, fill, d = 0.6, fs = 16) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  T_(s, txt, { x, y, w: d, h: d, fontSize: fs, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
}
function code(s, lines, x, y, w, h, fs = 13) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: "1F2933" }, line: { color: "1F2933" } });
  T_(s, lines.join("\n"), { x: x + 0.25, y: y + 0.2, w: w - 0.5, h: h - 0.4, fontFace: "Courier New", fontSize: fs, color: "E5F3F1" });
}
const bullets = (items, o = {}) => items.map((t, i) => ({
  text: t, options: { bullet: { indent: 18 }, breakLine: i < items.length - 1, paraSpaceAfter: o.gap ?? 8 },
}));

// ================================================================ 1. TITLE
pres.addSection({ title: "Mở đầu" });
let s = slide("TITLE_DARK", "Mở đầu");
s.addText("Trích rút thông tin từ hoá đơn → JSON/CSDL", { placeholder: "title" });
s.addText("So sánh API mô hình ngôn ngữ lớn và mô hình công khai trên hoá đơn tiếng Anh (SROIE) và tiếng Việt (MC-OCR)", { placeholder: "body" });
T_(s, "Môn Xử lý ngôn ngữ tự nhiên  ·  [Họ tên] – [MSSV]  ·  GVHD: [Họ tên giảng viên]", { x: 0.8, y: 6.3, w: 11.7, h: 0.4, fontSize: 14, color: "9FD8D0" });
s.addNotes("Giới thiệu đề tài: trích rút thông tin từ tài liệu thành JSON và lưu cơ sở dữ liệu, dùng API và mô hình công khai. Đối tượng là hoá đơn bán lẻ, hai bộ dữ liệu tiếng Anh và tiếng Việt.");

// ================================================================ 2. BÀI TOÁN
s = slide("CONTENT", "Mở đầu");
s.addText("Bài toán: từ văn bản OCR đến bản ghi có cấu trúc", { placeholder: "title" });
code(s, ["MINIMART ANAN", "Chợ Sủi Phú Thị Gia Lâm", "HÓA ĐƠN BÁN HÀNG", "Sữa TH true milk ...  20,000", "Tổng cộng :          74,000", "Tiền khách trả: VND   24,000", "Số GD: ... Ngày: 11/08/2020-08:06"],
  0.6, 1.55, 5.4, 3.4, 14);
T_(s, "Đầu vào: text OCR của 1 hoá đơn", { x: 0.6, y: 5.05, w: 5.4, h: 0.4, fontSize: 14, color: "52606D" });
s.addShape(pres.shapes.RIGHT_ARROW, { x: 6.25, y: 2.9, w: 0.8, h: 0.6, fill: { color: HEX.accent4 }, line: { color: HEX.accent4 } });
card(s, 7.3, 1.55, 5.4, 3.4, HEX.lt2, "json");
T_(s, '{\n  "seller":  "MINIMART ANAN",\n  "address": "Chợ Sủi Phú Thị Gia Lâm",\n  "date":    "11/08/2020 08:06",\n  "total":   "74,000"\n}',
  { x: 7.6, y: 1.85, w: 5.0, h: 2.9, fontFace: "Courier New", fontSize: 15, color: C.text2 });
T_(s, "Đầu ra: JSON theo lược đồ 4 trường → lưu SQLite", { x: 7.3, y: 5.05, w: 5.4, h: 0.4, fontSize: 14, color: "52606D" });
T_(s, [
  { text: "Bài toán KIE / slot filling: ", options: { bold: true, color: C.accent1 } },
  { text: "điền 4 trường seller · address · date · total, giá trị null nếu không có. So sánh baseline luật, API (DeepSeek) và mô hình công khai (Qwen2.5)." },
], { x: 0.6, y: 5.75, w: 12.1, h: 0.9, fontSize: 16 });
s.addNotes("Đầu vào là văn bản OCR, có thể có lỗi nhận dạng. Đầu ra là JSON đúng lược đồ 4 trường, sau đó ghi vào SQLite. Đây là dạng bài toán Key Information Extraction.");

// ================================================================ 3. DỮ LIỆU
pres.addSection({ title: "Dữ liệu và phương pháp" });
s = slide("CONTENT", "Dữ liệu và phương pháp");
s.addText("Hai bộ dữ liệu, một lược đồ chung", { placeholder: "title" });
const dsCard = (x, title, sub, stats, fill) => {
  card(s, x, 1.5, 5.9, 3.3, fill);
  T_(s, title, { x: x + 0.35, y: 1.7, w: 5.2, h: 0.5, fontSize: 24, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  T_(s, sub, { x: x + 0.35, y: 2.2, w: 5.2, h: 0.4, fontSize: 14, color: "52606D" });
  stats.forEach(([n, l], i) => {
    T_(s, n, { x: x + 0.35 + i * 1.85, y: 2.85, w: 1.8, h: 0.8, fontSize: 36, bold: true, color: C.accent1 });
    T_(s, l, { x: x + 0.35 + i * 1.85, y: 3.65, w: 1.75, h: 0.9, fontSize: 13, color: "52606D" });
  });
};
dsCard(0.6, "SROIE", "ICDAR 2019 · hoá đơn Malaysia · tiếng Anh",
  [[String(st.sroie.n_test), "hoá đơn test\n(chia sẵn)"], [String(st.sroie.avg_lines), "dòng / hoá đơn"], ["Sạch", "text OCR đã được\nngười kiểm tra"]], HEX.lt2);
dsCard(6.8, "MC-OCR 2021", "RIVF 2021 · ảnh chụp điện thoại · tiếng Việt",
  [[String(st.mcocr.n_test), "hoá đơn test\n(tự chia, seed 42)"], [String(st.mcocr.avg_lines), "dòng / hoá đơn"], ["OCR", "tự chạy VietOCR,\ncòn lỗi dấu"]], "FDF3E1");
const maps = [["company", "SELLER", "seller"], ["address", "ADDRESS", "address"], ["date", "TIMESTAMP", "date"], ["total", "TOTAL_COST", "total"]];
T_(s, "Ánh xạ nhãn → lược đồ chung", { x: 0.6, y: 5.0, w: 6, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
maps.forEach(([a, b, c], i) => {
  const x = 0.6 + i * 3.05;
  card(s, x, 5.45, 2.85, 1.25, "F4F5F7");
  T_(s, `${a} / ${b}`, { x: x + 0.2, y: 5.55, w: 2.5, h: 0.45, fontSize: 13, color: "52606D" });
  T_(s, `→ ${c}`, { x: x + 0.2, y: 6.0, w: 2.5, h: 0.5, fontSize: 20, bold: true, color: C.accent1, fontFace: "Courier New" });
});
s.addNotes("Hai bộ dữ liệu có cùng 4 trường nên dùng chung một lược đồ, một prompt và một cách đánh giá. SROIE có text OCR sạch; MC-OCR là ảnh chụp điện thoại, chúng tôi phải tự OCR.");

// ================================================================ 4. THÁCH THỨC MC-OCR
s = slide("CONTENT", "Dữ liệu và phương pháp");
s.addText("MC-OCR thiếu text OCR – giải bằng VietOCR", { placeholder: "title" });
T_(s, "49%", { x: 0.6, y: 1.5, w: 3.6, h: 1.4, fontSize: 80, bold: true, color: C.accent3, fontFace: THEME.headFontFace });
T_(s, "ô chữ trong dataset Kaggle có nội dung rỗng – đúng ở các ô cần trích", { x: 0.6, y: 2.95, w: 3.6, h: 1.0, fontSize: 16, color: C.text1 });
s.addChart(pres.charts.BAR, [{ name: "Ô rỗng (%)", labels: ["SELLER", "TIMESTAMP", "TOTAL_COST", "ADDRESS"], values: [32, 37, 38, 61] }], {
  x: 4.5, y: 1.45, w: 4.1, h: 3.1, barDir: "bar", chartColors: [HEX.accent3], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0\"%\"", dataLabelFontSize: 12, dataLabelColor: "1F2933", dataLabelFontFace: "+mn-lt",
  catAxisLabelColor: "52606D", catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true,
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, valAxisMaxVal: 75,
  showTitle: true, title: "Tỉ lệ ô rỗng theo trường", titleFontSize: 13, titleColor: "1F2933", titleFontFace: "+mn-lt",
});
card(s, 8.9, 1.5, 3.8, 3.05, HEX.lt2);
T_(s, "Giải pháp", { x: 9.15, y: 1.65, w: 3.3, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
T_(s, bullets(["Giữ vị trí các ô chữ có sẵn", "Cắt ảnh từng ô, nhận dạng lại bằng VietOCR (model public)", "Chạy trên GPU Colab, ~40.000 ô", "Sắp dòng theo toạ độ → text đầu vào"], { gap: 6 }),
  { x: 9.15, y: 2.15, w: 3.35, h: 2.3, fontSize: 14 });
card(s, 0.6, 4.95, 12.1, 1.6, "FDF3E1");
T_(s, [
  { text: "Hệ quả: ", options: { bold: true, color: C.accent3 } },
  { text: "text MC-OCR là OCR máy có lỗi thật (\"Cảm Phà\" thay vì \"Cẩm Phả\", \"0B\" thay vì \"08\"), còn nhãn đã được người sửa → exact match khắt khe hơn SROIE. Không dùng file CSV làm đầu vào vì nó chỉ chứa text của đáp án (lộ đáp án)." },
], { x: 0.9, y: 5.15, w: 11.5, h: 1.25, fontSize: 16 });
s.addNotes("Phát hiện quan trọng khi chuẩn bị dữ liệu: bản MC-OCR trên Kaggle có gần một nửa ô chữ rỗng. Nếu dùng nguyên, đáp án không có trong đầu vào. Chúng tôi chạy lại OCR bằng VietOCR trên Colab.");

// ================================================================ 5. PIPELINE
s = slide("CONTENT", "Dữ liệu và phương pháp");
s.addText("Quy trình xử lý", { placeholder: "title" });
const steps = [
  ["Dữ liệu", "Ảnh + nhãn\nSROIE, MC-OCR"], ["OCR", "Text có sẵn hoặc\nVietOCR (Colab)"], ["Trích rút", "M0–M4, cùng\nprompt + schema"],
  ["Kiểm tra", "Parse JSON,\nkhoá thiếu → null"], ["Lưu CSDL", "SQLite: documents,\ngold, extractions"], ["Đánh giá", "Chuẩn hoá →\nP / R / F1"],
];
steps.forEach(([h, d], i) => {
  const x = 0.6 + i * 2.07;
  card(s, x, 2.0, 1.85, 2.6, i === 2 ? "D5F2EE" : HEX.lt2);
  badge(s, x + 0.62, 2.2, String(i + 1), i === 2 ? HEX.accent1 : HEX.dk2);
  T_(s, h, { x: x + 0.1, y: 3.0, w: 1.65, h: 0.45, fontSize: 18, bold: true, color: C.text2, align: "center" });
  T_(s, d, { x: x + 0.1, y: 3.5, w: 1.65, h: 0.95, fontSize: 13, color: "52606D", align: "center" });
});
T_(s, [
  { text: "Thiết kế để chạy lại an toàn: ", options: { bold: true, color: C.accent1 } },
  { text: "UNIQUE(doc_id, method) trong bảng extractions làm cache – bị ngắt mạng hay hết quota thì chạy lại, không gọi lại API cho hoá đơn đã xong. Đánh giá chỉ là 1 câu JOIN với bảng gold." },
], { x: 0.6, y: 5.1, w: 12.1, h: 1.2, fontSize: 16 });
s.addNotes("Sáu bước. Bước trích rút là chỗ duy nhất khác nhau giữa các phương pháp; mọi thứ khác dùng chung để so sánh công bằng.");

// ================================================================ 6. PHƯƠNG PHÁP
s = slide("CONTENT", "Dữ liệu và phương pháp");
s.addText("Năm phương pháp, ba nhóm", { placeholder: "title" });
const methods = [
  ["M0", "Regex + heuristic", "Baseline luật", "Từ khoá TOTAL / Tổng cộng, mẫu ngày, dòng đầu là người bán", HEX.accent5],
  ["M1", "DeepSeek zero-shot", "API", "deepseek-chat, JSON mode, temperature 0", HEX.accent1],
  ["M2", "DeepSeek few-shot", "API", "Thêm 2 hoá đơn mẫu cùng bộ dữ liệu", HEX.accent2],
  ["M3", "Qwen2.5-3B", "Model public", "Ollama trên CPU laptop, ràng buộc JSON Schema", HEX.accent3],
  ["M4", "Qwen2.5-7B", "Model public", "Ollama trên GPU T4 Colab, cùng prompt", HEX.accent4],
];
methods.forEach(([c, n, k, d, col], i) => {
  const y = 1.45 + i * 1.07;
  card(s, 0.6, y, 12.1, 0.92, i % 2 ? "FFFFFF" : "F4F5F7");
  badge(s, 0.8, y + 0.16, c, col, 0.6, 14);
  T_(s, n, { x: 1.65, y: y + 0.12, w: 3.4, h: 0.7, fontSize: 19, bold: true, color: C.text2, valign: "middle" });
  T_(s, k, { x: 5.1, y: y + 0.12, w: 1.9, h: 0.7, fontSize: 15, bold: true, color: col === HEX.accent4 ? C.accent3 : col === HEX.accent5 ? C.text1 : C.accent1, valign: "middle" });
  T_(s, d, { x: 7.1, y: y + 0.12, w: 5.4, h: 0.7, fontSize: 15, color: "52606D", valign: "middle" });
});
s.addNotes("M0 là baseline. M1 và M2 là API DeepSeek, khác nhau ở có ví dụ mẫu hay không. M3 và M4 là mô hình công khai Qwen2.5 chạy bằng Ollama. Tất cả mô hình ngôn ngữ dùng cùng system prompt và cùng lược đồ JSON.");

// ================================================================ 7. PROMPT + SCHEMA + DB
s = slide("CONTENT", "Dữ liệu và phương pháp");
s.addText("Prompt chung, JSON Schema và SQLite", { placeholder: "title" });
T_(s, "System prompt (rút gọn)", { x: 0.6, y: 1.4, w: 6, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
code(s, ["Extract from ONE receipt a JSON object:", "- seller: store/company name", "- address: seller's address", "- date: purchase date, as printed", "- total: final amount to pay", "Copy values, do not translate;", "use null if absent. Output JSON only."], 0.6, 1.85, 6.0, 3.0, 13);
T_(s, "Lược đồ ép đầu ra", { x: 6.95, y: 1.4, w: 5.8, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
code(s, ['{"type": "object",', ' "properties": {', '   "seller":  {"type": ["string","null"]},', '   "address": {"type": ["string","null"]},', '   "date":    {"type": ["string","null"]},', '   "total":   {"type": ["string","null"]}},', ' "required": [all 4]}'], 6.95, 1.85, 5.75, 3.0, 13);
card(s, 0.6, 5.15, 12.1, 1.5, HEX.lt2);
T_(s, [
  { text: "SQLite invoices.db  ", options: { bold: true, color: C.accent1 } },
  { text: "documents (text đầu vào) · gold (nhãn) · extractions (kết quả + model_version, latency, token, valid_json). ", options: {} },
  { text: "Ngày/tiền giữ nguyên chuỗi, chuẩn hoá bằng code để nhất quán.", options: { italic: true } },
], { x: 0.9, y: 5.35, w: 11.5, h: 1.15, fontSize: 16 });
s.addNotes("Prompt viết bằng tiếng Anh nhưng xử lý được cả hoá đơn tiếng Việt. Ollama ép đầu ra đúng JSON Schema; DeepSeek dùng JSON mode. Kết quả mọi phương pháp ghi chung một bảng.");

// ================================================================ 8. ĐÁNH GIÁ
s = slide("CONTENT", "Dữ liệu và phương pháp");
s.addText("Đánh giá: chuẩn hoá rồi so khớp", { placeholder: "title" });
const ev = [
  ["seller, address", "chữ thường, NFC, bỏ dấu câu + khoảng trắng", "\"OJC Marketing, SDN BHD\" → ojcmarketingsdnbhd"],
  ["date", "đưa về YYYY-MM-DD, chỉ nhận ngày hợp lệ", "\"Ngày: 11/08/2020 - 21:19\" → 2020-08-11"],
  ["total", "đọc số, phân biệt dấu nghìn / thập phân", "\"12.500đ\" → 12500 · \"RM 1,234.50\" → 1234.50"],
];
ev.forEach(([f, r, e], i) => {
  const y = 1.5 + i * 1.12;
  card(s, 0.6, y, 7.6, 0.95, i % 2 ? "FFFFFF" : "F4F5F7");
  T_(s, f, { x: 0.85, y: y + 0.12, w: 1.9, h: 0.7, fontSize: 17, bold: true, color: C.accent1, valign: "middle" });
  T_(s, [{ text: r, options: { breakLine: true } }, { text: e, options: { fontFace: "Courier New", fontSize: 12, color: "52606D" } }],
    { x: 2.8, y: y + 0.1, w: 5.3, h: 0.78, fontSize: 14, valign: "middle" });
});
card(s, 8.55, 1.5, 4.15, 3.2, HEX.dk2);
T_(s, [
  { text: "Precision", options: { bold: true, color: "9FD8D0", breakLine: true } },
  { text: "đúng / số dự đoán khác rỗng", options: { breakLine: true, paraSpaceAfter: 8 } },
  { text: "Recall", options: { bold: true, color: "9FD8D0", breakLine: true } },
  { text: "đúng / số nhãn khác rỗng", options: { breakLine: true, paraSpaceAfter: 8 } },
  { text: "Macro-F1", options: { bold: true, color: "9FD8D0", breakLine: true } },
  { text: "trung bình F1 của 4 trường" },
], { x: 8.85, y: 1.7, w: 3.6, h: 2.85, fontSize: 15, color: "FFFFFF" });
T_(s, [
  { text: "Soft F1: ", options: { bold: true, color: C.accent3 } },
  { text: "seller/address giống ≥ 90% (rapidfuzz) cũng tính đúng – đo riêng ảnh hưởng của lỗi vài ký tự do OCR. Chỉ số phụ: % JSON hợp lệ, thời gian trung vị, số token." },
], { x: 0.6, y: 5.15, w: 12.1, h: 1.2, fontSize: 16 });
s.addNotes("Exact match sau chuẩn hoá. Chúng tôi phát hiện và sửa một lỗi trong hàm chuẩn hoá ngày (bắt nhầm giờ thành tháng) rồi chấm lại toàn bộ.");

// ================================================================ 9. KẾT QUẢ TỔNG THỂ
pres.addSection({ title: "Kết quả" });
s = slide("CONTENT", "Kết quả");
s.addText("LLM vượt baseline rõ rệt trên cả hai ngôn ngữ", { placeholder: "title" });
const labels = ["SROIE (EN)", "MC-OCR (VI)"];
s.addChart(pres.charts.BAR, R.methods.map((m) => ({ name: `${m.code} ${m.label}`, labels, values: [S[m.method].macro_f1, M[m.method].macro_f1] })), {
  x: 0.5, y: 1.35, w: 8.3, h: 5.4, barDir: "col", barGapWidthPct: 60, chartColors: SERIES,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 11, dataLabelColor: "1F2933", dataLabelFontFace: "+mn-lt",
  catAxisLabelColor: "1F2933", catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt",
  valAxisLabelColor: "7B8794", valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisMaxVal: 100, valAxisMinVal: 0,
  valGridLine: { color: "E4E7EB", size: 0.75 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: "1F2933",
  showTitle: true, title: "Macro-F1 (%) trên tập test", titleFontSize: 14, titleColor: "1F2933", titleFontFace: "+mn-lt",
});
const callout = (y, big, small, col) => {
  T_(s, big, { x: 9.2, y, w: 3.5, h: 0.85, fontSize: 40, bold: true, color: col, fontFace: THEME.headFontFace });
  T_(s, small, { x: 9.2, y: y + 0.85, w: 3.5, h: 0.75, fontSize: 14, color: "52606D" });
};
callout(1.5, `${mac(S, "deepseek-fs")}%`, "SROIE – DeepSeek few-shot, tốt nhất", C.accent1);
callout(3.25, `+${(S["deepseek-fs"].macro_f1 - S.regex.macro_f1).toFixed(1)}`, "điểm so với regex trên SROIE", C.accent1);
callout(5.0, `${mac(M, "deepseek-fs")}%`, "MC-OCR – vẫn tốt nhất nhưng thấp hơn nhiều", C.accent3);
s.addNotes(`Mọi mô hình ngôn ngữ vượt regex. DeepSeek few-shot tốt nhất ở cả hai bộ. Qwen-7B đạt ${mac(S, "qwen2.5-7b")} trên SROIE, gần bằng DeepSeek zero-shot ${mac(S, "deepseek-zs")}. Tiếng Việt thấp hơn khoảng 20 điểm.`);

// ================================================================ 10. THEO TRƯỜNG
s = slide("CONTENT", "Kết quả");
s.addText("Theo trường: date dễ, address tiếng Việt khó nhất", { placeholder: "title" });
const head = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.dk2 }, align: "center", valign: "middle" } });
function fieldTable(D, title, x) {
  const best = FIELDS.map((f) => Math.max(...ORDER.map((m) => D[m].f1[f])));
  const rows = [[head(title), ...FIELDS.map(head)]];
  R.methods.forEach((m, i) => rows.push([
    { text: `${m.code} ${m.label.split(" (")[0]}`, options: { fontSize: 12, fill: { color: i % 2 ? "FFFFFF" : "F4F5F7" } } },
    ...FIELDS.map((f, j) => ({ text: D[m.method].f1[f].toFixed(1), options: {
      align: "center", bold: D[m.method].f1[f] === best[j], color: D[m.method].f1[f] === best[j] ? HEX.accent1 : "1F2933",
      fill: { color: i % 2 ? "FFFFFF" : "F4F5F7" } } })),
  ]));
  s.addTable(rows, { x, y: 1.5, w: 5.95, colW: [2.35, 0.9, 0.9, 0.9, 0.9], fontSize: 13, fontFace: "Calibri", color: "1F2933",
    border: { type: "solid", pt: 0.5, color: "D9DEE3" }, rowH: 0.42, valign: "middle" });
}
fieldTable(S, "SROIE", 0.6);
fieldTable(M, "MC-OCR", 6.75);
card(s, 0.6, 4.4, 12.1, 2.2, HEX.lt2);
T_(s, bullets([
  `date ~99% trên SROIE với mọi LLM; total tăng mạnh nhất so với regex (${S.regex.f1.total.toFixed(1)} → ${S["deepseek-fs"].f1.total.toFixed(1)}).`,
  `address MC-OCR ≤ ${Math.max(...ORDER.map((m) => M[m].f1.address)).toFixed(1)}% exact, nhưng soft F1 lên ${M["deepseek-fs"].soft_f1.address.toFixed(1)}% → nhiều lỗi chỉ sai vài ký tự do OCR.`,
  "Giá trị tốt nhất mỗi cột tô màu; F1 tính theo exact match sau chuẩn hoá.",
], { gap: 6 }), { x: 0.9, y: 4.6, w: 11.5, h: 1.9, fontSize: 16 });
s.addNotes("Trường date gần như được giải quyết. Address tiếng Việt thấp chủ yếu do lỗi dấu từ OCR – soft F1 cho thấy mô hình lấy đúng vùng địa chỉ.");

// ================================================================ 11. API vs PUBLIC
s = slide("CONTENT", "Kết quả");
s.addText("API hay mô hình công khai? Một phép đánh đổi", { placeholder: "title" });
const cols = [
  ["API · DeepSeek", HEX.accent1, `${mac(S, "deepseek-zs")} / ${mac(S, "deepseek-fs")}`, `~${sec(S, "deepseek-zs")} s`, ["Chất lượng và tốc độ tốt nhất", "Không cần phần cứng", "Trả tiền theo token", "Hoá đơn gửi ra bên thứ ba"]],
  ["Qwen2.5-7B · GPU", HEX.accent4, mac(S, "qwen2.5-7b"), `~${sec(S, "qwen2.5-7b")} s`, ["Gần bằng API zero-shot", "Dữ liệu ở hạ tầng của mình", "Cần GPU (Colab T4)", "Kết quả lặp lại được"]],
  ["Qwen2.5-3B · CPU", HEX.accent3, mac(S, "qwen2.5-3b"), `~${sec(S, "qwen2.5-3b")} s`, ["Chạy trên laptop 16 GB RAM", "Miễn phí, offline", "Chậm, máy nóng", "Kém ở seller / address"]],
];
cols.forEach(([h, col, f, t, pts], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 1.45, 3.9, 5.2, i === 0 ? HEX.lt2 : "F4F5F7");
  s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 1.7, w: 0.35, h: 0.35, fill: { color: col }, line: { color: col } });
  T_(s, h, { x: x + 0.8, y: 1.62, w: 3.0, h: 0.5, fontSize: 18, bold: true, color: C.text2 });
  T_(s, f, { x: x + 0.3, y: 2.3, w: 3.4, h: 0.75, fontSize: 32, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  T_(s, "Macro-F1 SROIE (%)", { x: x + 0.3, y: 3.05, w: 3.4, h: 0.35, fontSize: 12, color: "52606D" });
  T_(s, t, { x: x + 0.3, y: 3.45, w: 3.4, h: 0.6, fontSize: 26, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  T_(s, "thời gian trung vị / hoá đơn", { x: x + 0.3, y: 4.05, w: 3.4, h: 0.35, fontSize: 12, color: "52606D" });
  T_(s, bullets(pts, { gap: 4 }), { x: x + 0.3, y: 4.55, w: 3.4, h: 1.95, fontSize: 14 });
});
s.addNotes("Cả ba lựa chọn đều cho 100% JSON hợp lệ. API tốt và nhanh nhất nhưng phụ thuộc nhà cung cấp và gửi dữ liệu ra ngoài. Qwen-7B là điểm cân bằng tốt nếu có GPU.");

// ================================================================ 12. FEW-SHOT & EN vs VI
s = slide("CONTENT", "Kết quả");
s.addText("Few-shot dạy quy ước; tiếng Việt khó vì dữ liệu", { placeholder: "title" });
card(s, 0.6, 1.45, 5.9, 5.2, HEX.lt2);
T_(s, "Zero-shot → few-shot (DeepSeek)", { x: 0.9, y: 1.65, w: 5.4, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
T_(s, `+${(S["deepseek-fs"].f1.seller - S["deepseek-zs"].f1.seller).toFixed(1)}`, { x: 0.9, y: 2.2, w: 2.6, h: 1.0, fontSize: 48, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
T_(s, "điểm F1 seller trên SROIE", { x: 0.9, y: 3.2, w: 2.6, h: 0.6, fontSize: 13, color: "52606D" });
T_(s, `+${(M["deepseek-fs"].f1.seller - M["deepseek-zs"].f1.seller).toFixed(1)}`, { x: 3.6, y: 2.2, w: 2.6, h: 1.0, fontSize: 48, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
T_(s, "điểm F1 seller trên MC-OCR", { x: 3.6, y: 3.2, w: 2.6, h: 0.6, fontSize: 13, color: "52606D" });
T_(s, bullets([
  "Ví dụ dạy quy ước nhãn: bỏ mã số công ty \"(519537-X)\", dùng tên pháp nhân",
  `Đổi lại: token đầu vào ×${(T["deepseek-fs"].avg_in / T["deepseek-zs"].avg_in).toFixed(1)} (${T["deepseek-zs"].avg_in} → ${T["deepseek-fs"].avg_in})`,
], { gap: 6 }), { x: 0.9, y: 4.1, w: 5.4, h: 2.3, fontSize: 15 });
card(s, 6.8, 1.45, 5.9, 5.2, "FDF3E1");
T_(s, "Tiếng Anh → tiếng Việt", { x: 7.1, y: 1.65, w: 5.4, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
T_(s, `−${(S["deepseek-fs"].macro_f1 - M["deepseek-fs"].macro_f1).toFixed(1)}`, { x: 7.1, y: 2.2, w: 5.4, h: 1.0, fontSize: 48, bold: true, color: C.accent3, fontFace: THEME.headFontFace });
T_(s, "điểm Macro-F1 (DeepSeek few-shot)", { x: 7.1, y: 3.2, w: 5.4, h: 0.6, fontSize: 13, color: "52606D" });
T_(s, bullets(["Text là OCR máy, lỗi dấu và ký tự", "Quy ước nhãn riêng (VinMart → \"VinCommerce\")", "Nhãn nhiễu: \"13/88/2020\", TIMESTAMP = \"Tổng tiền…\"", "Ảnh chụp điện thoại: nghiêng, mờ"], { gap: 6 }),
  { x: 7.1, y: 4.1, w: 5.4, h: 2.3, fontSize: 15 });
s.addNotes("Few-shot giúp nhiều nhất ở trường seller vì đó là trường phụ thuộc quy ước gán nhãn. Khoảng cách tiếng Anh – tiếng Việt chủ yếu đến từ chất lượng OCR và nhãn, không phải khả năng hiểu tiếng Việt.");

// ================================================================ 13. PHÂN TÍCH LỖI
pres.addSection({ title: "Phân tích" });
s = slide("CONTENT", "Phân tích");
s.addText("Phân tích lỗi: mô hình thường không sai một mình", { placeholder: "title" });
const errs = [
  ["Quy ước nhãn", "99 SPEED MART S/B", "99 SPEED MART S/B (519537-X)"],
  ["Lỗi OCR", "Chợ Sủi Phú Thị Gia Lâm", "Chợ Sủi Phù Thị Gia Lâm"],
  ["Nhầm con số", "TOTAL RM42.88", "CASH RM42.90 (tiền khách đưa)"],
  ["Tên pháp nhân", "VinCommerce", "VM+ QNH 88 Trần Phú"],
  ["Nhãn sai", "200,000 (tiền khách trả)", "74,000 (tổng cộng – đúng)"],
];
const eh = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.dk2 }, valign: "middle" } });
s.addTable([[eh("Loại lỗi"), eh("Nhãn (gold)"), eh("Dự đoán")], ...errs.map((r, i) => r.map((c, j) => ({
  text: c, options: { fill: { color: i % 2 ? "FFFFFF" : "F4F5F7" }, bold: j === 0, color: j === 0 ? HEX.accent1 : "1F2933" } })))],
{ x: 0.6, y: 1.5, w: 12.1, colW: [2.6, 4.5, 5.0], fontSize: 15, fontFace: "Calibri", rowH: 0.55, valign: "middle",
  border: { type: "solid", pt: 0.5, color: "D9DEE3" } });
T_(s, [
  { text: "Bài học: ", options: { bold: true, color: C.accent3 } },
  { text: "nhiều \"lỗi\" đến từ OCR, quy ước gán nhãn hoặc nhãn sai. Hàm chuẩn hoá cũng phải được kiểm thử – chúng tôi đã sửa lỗi hiểu nhầm \"11/08/2020-21-19\" thành tháng 21 rồi chấm lại." },
], { x: 0.6, y: 5.25, w: 12.1, h: 1.3, fontSize: 16 });
s.addNotes("Năm nhóm lỗi điển hình. Ở dòng cuối, mô hình trả lời đúng nhưng bị chấm sai vì nhãn của dataset sai.");

// ================================================================ 14. THÁCH THỨC TRIỂN KHAI
s = slide("CONTENT", "Phân tích");
s.addText("Dùng API miễn phí: các vấn đề thực tế", { placeholder: "title" });
const issues = [
  ["20", "lượt gọi / ngày", `Gemini 3.5 Flash miễn phí → dừng ở ${side["gemini-zs"] ? side["gemini-zs"].n : 41} hoá đơn`],
  ["200K", "token / ngày", "Groq GPT-OSS-120B → ~300 hoá đơn / ngày"],
  [String(side["gemini-zs"] ? side["gemini-zs"].blocked : 1), "hoá đơn bị chặn", "Bộ lọc an toàn Gemini: PROHIBITED_CONTENT"],
  ["SSL", "lỗi mạng", "Tự thử lại với thời gian chờ tăng dần"],
];
issues.forEach(([n, u, d], i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.25;
  card(s, x, y, 5.95, 2.0, i < 3 ? "FDF3E1" : "F4F5F7");
  T_(s, n, { x: x + 0.3, y: y + 0.25, w: 2.3, h: 0.9, fontSize: 40, bold: true, color: C.accent3, fontFace: THEME.headFontFace });
  T_(s, u, { x: x + 0.3, y: y + 1.15, w: 2.3, h: 0.5, fontSize: 13, color: "52606D" });
  T_(s, d, { x: x + 2.7, y: y + 0.3, w: 3.05, h: 1.4, fontSize: 15, valign: "middle" });
});
T_(s, "→ Chuyển sang DeepSeek trả phí (rẻ, không giới hạn chặt). Cache theo (hoá đơn, phương pháp) giúp không mất kết quả khi bị gián đoạn.",
  { x: 0.6, y: 6.1, w: 12.1, h: 0.6, fontSize: 15, color: C.text2, bold: true });
s.addNotes("Đây là phần kinh nghiệm thực tế: API miễn phí có nhiều giới hạn ẩn. Đó cũng là lý do kết quả API chính thức dùng DeepSeek.");

// ================================================================ 15. KẾT LUẬN
pres.addSection({ title: "Kết luận" });
s = slide("TITLE_DARK", "Kết luận");
s.addText("Kết luận và hướng phát triển", { placeholder: "title" });
T_(s, bullets([
  `LLM + JSON Schema: 100% JSON hợp lệ, Macro-F1 ${mac(S, "deepseek-fs")}% (EN) và ${mac(M, "deepseek-fs")}% (VI), vượt xa regex`,
  `Mô hình công khai 7B đạt ${mac(S, "qwen2.5-7b")}% trên SROIE – lựa chọn tốt khi cần giữ dữ liệu nội bộ`,
  "Với tiếng Việt, nút thắt là chất lượng OCR và nhãn",
  "Tiếp theo: OCR tốt hơn hoặc mô hình đọc ảnh, fine-tune LoRA, thêm danh sách mặt hàng, demo Streamlit",
], { gap: 10 }), { x: 0.8, y: 3.85, w: 11.7, h: 2.9, fontSize: 18, color: "FFFFFF" });
s.addNotes("Tóm tắt ba kết luận chính và hướng phát triển. Cảm ơn thầy/cô và các bạn đã lắng nghe.");

// ---------------------------------------------------------------- write
const out = path.join(__dirname, "..", "Slide_TrichRutThongTin_HoaDon.pptx");
pres.writeFile({ fileName: out }).then(async () => {
  // Ghi bảng màu vào theme của file (cần script apply_theme.js của skill pptx; không có thì dùng màu mặc định)
  if (process.env.PPTX_SKILL) {
    const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
    await applyTheme(out, THEME);
  } else {
    console.warn("PPTX_SKILL chưa đặt – bỏ qua applyTheme (slide dùng bảng màu mặc định của Office).");
  }
  console.log("Wrote", out, SN, "slides");
});
