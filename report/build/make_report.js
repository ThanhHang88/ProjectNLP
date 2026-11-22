// Sinh báo cáo Word: node make_report.js  -> ../BaoCao_TrichRutThongTin_HoaDon.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, TableOfContents, Footer, PageNumber,
  LevelFormat, VerticalAlign,
} = require("docx");

const R = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "results.json"), "utf8"));
const FIG = path.join(__dirname, "..", "figures");
const FONT = "Times New Roman";
const CONTENT_W = 9071; // A4 - lề trái 3cm - lề phải 2cm (DXA)

// ---------------------------------------------------------------- số liệu
const S = R.datasets.sroie.by_method, M = R.datasets.mcocr.by_method;
const f1 = (d, m, f) => d[m].f1[f].toFixed(1);
const mac = (d, m) => d[m].macro_f1.toFixed(1);
const soft = (d, m) => d[m].soft_macro_f1.toFixed(1);
const sec = (d, m) => (d[m].latency_ms_median / 1000).toFixed(d[m].latency_ms_median < 10000 ? 1 : 0);
const st = R.dataset_stats;
const T = R.tokens;
const side = R.side_experiments;
const METHODS = R.methods;
const FIELDS = ["seller", "address", "date", "total"];
const ORDER_ALL = () => R.methods.map((x) => x.method);
const E = R.errors;

// ---------------------------------------------------------------- helpers
function runs(text, base = {}) {
  // **đậm**, *nghiêng*, `code`
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: "Courier New", size: 22, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (text, o = {}) => new Paragraph({
  children: runs(text), alignment: o.align ?? AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 120, line: 312 }, indent: o.noIndent ? undefined : { firstLine: 567 }, ...o.para,
});
const B = (text, level = 0) => new Paragraph({
  children: runs(text), numbering: { reference: "bullets", level }, alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 60, line: 300 },
});
const N = (text) => new Paragraph({
  children: runs(text), numbering: { reference: "numbers", level: 0 }, alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 60, line: 300 },
});
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], pageBreakBefore: true });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const CAP = (t) => new Paragraph({
  children: [new TextRun({ text: t, italics: true, size: 24 })], alignment: AlignmentType.CENTER,
  spacing: { before: 60, after: 200 },
});
const CODE = (lines) => lines.map((l, i) => new Paragraph({
  children: [new TextRun({ text: l || " ", font: "Courier New", size: 19 })],
  shading: { type: ShadingType.CLEAR, fill: "F3F4F6", color: "auto" },
  spacing: { after: 0, line: 240, before: i === 0 ? 80 : 0 }, indent: { left: 200, right: 200 },
})).concat([new Paragraph({ children: [], spacing: { after: 100 } })]);

function IMG(file, wpx, hpx) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
    children: [new ImageRun({
      type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: wpx, height: hpx },
      altText: { title: file, description: file, name: file },
    })],
  });
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function TABLE(headers, rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (txt, w, isHead, opts = {}) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: isHead ? { type: ShadingType.CLEAR, fill: "D9E8E6", color: "auto" }
      : opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({
      alignment: opts.align ?? (isHead ? AlignmentType.CENTER : AlignmentType.LEFT), spacing: { after: 0, line: 260 },
      keepNext: !!opts.keep,
      children: runs(String(txt), { size: o.size ?? 22, bold: isHead || opts.bold }),
    })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((h, i) => cell(h, widths[i], true, { keep: true })) }),
      ...rows.map((r, ri) => new TableRow({
        cantSplit: true,
        children: r.map((c, i) => {
          const isObj = c && typeof c === "object";
          return cell(isObj ? c.t : c, widths[i], false, {
            align: i >= (o.numFrom ?? 99) ? AlignmentType.CENTER : AlignmentType.LEFT,
            bold: isObj && c.b, fill: isObj && c.fill, keep: ri < rows.length - 1,
          });
        }),
      })),
    ],
  });
}

// đánh dấu giá trị tốt nhất trong mỗi cột
function bestMark(dict, methods, getter) {
  const vals = methods.map((m) => (dict[m] ? getter(dict[m]) : -1));
  const best = Math.max(...vals);
  return methods.map((m, i) => ({ t: dict[m] ? getter(dict[m]).toFixed(1) : "–", b: vals[i] === best }));
}

// ---------------------------------------------------------------- nội dung
const children = [];
const mOrder = METHODS.map((x) => x.method);

// ---------- TRANG BÌA
const center = (t, size, bold = false, after = 120) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after }, children: [new TextRun({ text: t, size, bold })],
});
children.push(
  center("[TÊN TRƯỜNG]", 28, true, 60),
  center("[TÊN KHOA / VIỆN]", 28, true, 1400),
  center("BÁO CÁO BÀI TẬP LỚN", 32, true, 120),
  center("MÔN: XỬ LÝ NGÔN NGỮ TỰ NHIÊN", 28, true, 900),
  center("ĐỀ TÀI", 26, false, 120),
  center("TRÍCH RÚT THÔNG TIN TỪ TÀI LIỆU → JSON/CSDL", 34, true, 80),
  center("Áp dụng cho hoá đơn bán lẻ tiếng Anh (SROIE) và tiếng Việt (MC-OCR),", 26, false, 40),
  center("so sánh API mô hình ngôn ngữ lớn với mô hình công khai (public model)", 26, false, 1500),
);
const coverRow = (k, v) => new Paragraph({
  indent: { left: 2600 }, spacing: { after: 100 },
  children: [new TextRun({ text: k, bold: true, size: 26 }), new TextRun({ text: v, size: 26 })],
});
children.push(
  coverRow("Giảng viên hướng dẫn:  ", "[Họ tên giảng viên]"),
  coverRow("Sinh viên thực hiện:  ", "[Họ tên] – [MSSV]"),
  coverRow("Lớp:  ", "[Mã lớp]"),
  new Paragraph({ children: [], spacing: { after: 1600 } }),
  center("[Địa điểm], tháng 11 năm 2026", 26, false, 0),
);

// ---------- MỤC LỤC
children.push(
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: "MỤC LỤC", bold: true, size: 30 })] }),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({
    spacing: { before: 200 }, children: [new TextRun({
      text: "(Nếu mục lục trống: trong Word nhấn chuột phải vào mục lục → Update Field → Update entire table.)",
      italics: true, size: 22, color: "666666",
    })],
  }),
);

// ---------- TÓM TẮT
const bestS = mac(S, "deepseek-fs"), bestM = mac(M, "deepseek-fs");
children.push(
  H1("TÓM TẮT"),
  P(`Báo cáo trình bày một hệ thống **trích rút thông tin** (Information Extraction – IE) từ văn bản OCR của hoá đơn bán lẻ, chuyển thành **JSON** theo một lược đồ thống nhất gồm bốn trường *seller* (người bán), *address* (địa chỉ), *date* (ngày) và *total* (tổng tiền), sau đó lưu vào cơ sở dữ liệu **SQLite**. Hệ thống được thử nghiệm trên hai bộ dữ liệu công khai: **SROIE** (hoá đơn tiếng Anh, ${st.sroie.n_test} hoá đơn kiểm thử) và **MC-OCR 2021** (hoá đơn tiếng Việt, ${st.mcocr.n_test} hoá đơn kiểm thử).`),
  P(`Năm phương pháp được so sánh trên cùng một quy trình: (M0) luật/regex làm baseline; (M1, M2) mô hình ngôn ngữ lớn gọi qua **API DeepSeek** ở chế độ zero-shot và few-shot; (M3, M4) **mô hình công khai Qwen2.5** 3B và 7B chạy cục bộ bằng Ollama (CPU laptop và GPU Colab). Mọi mô hình ngôn ngữ dùng chung một prompt và một JSON Schema.`),
  P(`Kết quả: DeepSeek few-shot đạt Macro-F1 cao nhất trên cả hai bộ (${bestS}% trên SROIE và ${bestM}% trên MC-OCR), vượt baseline regex lần lượt ${(S["deepseek-fs"].macro_f1 - S.regex.macro_f1).toFixed(1)} và ${(M["deepseek-fs"].macro_f1 - M.regex.macro_f1).toFixed(1)} điểm. Mô hình công khai Qwen2.5-7B đạt ${mac(S, "qwen2.5-7b")}% trên SROIE – gần bằng API zero-shot (${mac(S, "deepseek-zs")}%) – trong khi dữ liệu không rời khỏi máy chủ của người dùng. Tiếng Việt khó hơn rõ rệt do lỗi OCR, quy ước gán nhãn và nhiễu nhãn của MC-OCR. Báo cáo cũng phân tích lỗi chi tiết và ghi lại các thách thức thực tế khi dùng API miễn phí (giới hạn lượt gọi/ngày, bộ lọc an toàn, lỗi mạng).`),
  P("**Từ khoá:** trích rút thông tin, hoá đơn, OCR, LLM, structured output, JSON Schema, few-shot, Qwen2.5, DeepSeek, SROIE, MC-OCR.", { noIndent: true }),
);

// ---------- CHƯƠNG 1
children.push(
  H1("CHƯƠNG 1. GIỚI THIỆU"),
  H2("1.1. Bối cảnh"),
  P("Trong doanh nghiệp, một lượng lớn thông tin nằm trong tài liệu phi cấu trúc: hoá đơn, biên lai, hợp đồng, CV, công văn… Để máy tính có thể tìm kiếm, thống kê hay đối soát, các thông tin này phải được chuyển sang dạng có cấu trúc như bản ghi trong cơ sở dữ liệu hoặc JSON. Việc nhập liệu thủ công tốn thời gian và dễ sai, vì vậy tự động hoá bằng xử lý ngôn ngữ tự nhiên (NLP) là nhu cầu thực tế, ví dụ trong quản lý chi tiêu, kế toán hoặc hoàn tiền công tác phí."),
  P("Sự xuất hiện của các mô hình ngôn ngữ lớn (LLM) làm thay đổi cách giải bài toán này: thay vì huấn luyện một mô hình riêng cho từng loại tài liệu, ta có thể mô tả yêu cầu bằng ngôn ngữ tự nhiên và yêu cầu mô hình trả về JSON. Câu hỏi đặt ra cho người triển khai là nên **gọi API của nhà cung cấp** hay **tự chạy mô hình công khai (public/open-weight)**, và mỗi lựa chọn đánh đổi chất lượng, tốc độ, chi phí, quyền riêng tư như thế nào."),
  H2("1.2. Phát biểu bài toán"),
  P("**Đầu vào:** văn bản OCR của một hoá đơn bán lẻ (tiếng Anh hoặc tiếng Việt), gồm các dòng chữ theo thứ tự từ trên xuống, có thể chứa lỗi nhận dạng ký tự."),
  P("**Đầu ra:** một đối tượng JSON theo lược đồ cố định gồm bốn trường, mỗi trường là chuỗi hoặc `null` nếu không có trong văn bản, và được lưu thành một bản ghi trong cơ sở dữ liệu SQLite:"),
  ...CODE(['{ "seller": "MINIMART ANAN",', '  "address": "Chợ Sủi Phú Thị Gia Lâm",', '  "date": "11/08/2020 08:06",', '  "total": "74,000" }']),
  H2("1.3. Mục tiêu và phạm vi"),
  B("Xây dựng quy trình đầy đủ: dữ liệu → text OCR → trích rút → kiểm tra JSON → lưu SQLite → đánh giá."),
  B("Cài đặt và so sánh **API** (DeepSeek) với **mô hình công khai** (Qwen2.5-3B/7B), kèm baseline dựa trên luật."),
  B("Đánh giá trên **hai ngôn ngữ** (tiếng Anh – SROIE, tiếng Việt – MC-OCR) với cùng lược đồ và cùng độ đo."),
  B("Phân tích lỗi và rút ra khuyến nghị khi triển khai thực tế."),
  P("Phạm vi: chỉ xử lý **văn bản** OCR (không dùng thông tin bố cục/ảnh làm đầu vào cho mô hình), bốn trường thông tin, không huấn luyện lại (fine-tune) mô hình. Phần cứng là laptop ThinkPad T480s (Intel Core i5 thế hệ 8, 16 GB RAM, không có GPU rời) và Google Colab (GPU T4) miễn phí."),
  H2("1.4. Đóng góp chính"),
  B("Một lược đồ JSON và một prompt dùng chung cho hai bộ dữ liệu khác ngôn ngữ."),
  B("Bổ sung text OCR đầy đủ cho MC-OCR bằng VietOCR (dataset trên Kaggle chỉ có text của các trường đã gán nhãn, ~49% ô chữ bị rỗng)."),
  B("Bảng so sánh định lượng 5 phương pháp × 2 bộ dữ liệu × 4 trường, kèm thời gian xử lý, số token và tỉ lệ JSON hợp lệ."),
  B("Phân loại lỗi và ghi nhận các vấn đề thực tế khi dùng API miễn phí."),
);

// ---------- CHƯƠNG 2
children.push(
  H1("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT"),
  H2("2.1. Trích rút thông tin"),
  P("Trích rút thông tin là nhiệm vụ tự động rút ra dữ liệu có cấu trúc từ văn bản phi cấu trúc. Các bài toán con điển hình gồm: **nhận dạng thực thể có tên** (NER – tìm và phân loại các cụm từ như tên người, tổ chức, ngày tháng, số tiền), **trích rút quan hệ** (quan hệ giữa các thực thể), **trích rút sự kiện**, và **điền khe thông tin** (slot filling) – điền các trường của một biểu mẫu định sẵn. Với tài liệu như hoá đơn, bài toán thường được gọi là **Key Information Extraction (KIE)**: cho trước danh sách khoá (seller, date, total…), tìm giá trị tương ứng. Đề tài này thuộc dạng KIE/slot filling."),
  H2("2.2. Các hướng tiếp cận"),
  P("**Dựa trên luật (rule-based):** dùng biểu thức chính quy và từ khoá (\"TOTAL\", \"Tổng cộng\"…). Ưu điểm là nhanh, dễ giải thích, không cần dữ liệu huấn luyện; nhược điểm là khó bao quát các biến thể định dạng và dễ vỡ khi gặp mẫu mới."),
  P("**Học máy có giám sát:** gán nhãn chuỗi (BIO) với CRF, BiLSTM-CRF, hoặc mô hình Transformer như BERT/PhoBERT; với tài liệu có bố cục, các mô hình đa phương thức như LayoutLM kết hợp vị trí chữ và ảnh. Cách này cho độ chính xác cao nhưng cần dữ liệu gán nhãn và huấn luyện riêng cho từng loại tài liệu."),
  P("**Mô hình ngôn ngữ lớn (LLM):** mô hình được huấn luyện trước trên lượng văn bản rất lớn có khả năng làm theo chỉ dẫn. Ta mô tả các trường cần lấy trong prompt và yêu cầu mô hình sinh JSON. Không cần huấn luyện lại, dễ mở rộng sang trường hoặc loại tài liệu mới, nhưng tốn tài nguyên tính toán và có nguy cơ \"bịa\" (hallucination)."),
  H2("2.3. Học trong ngữ cảnh: zero-shot và few-shot"),
  P("Với **zero-shot**, mô hình chỉ nhận mô tả nhiệm vụ. Với **few-shot** (in-context learning), prompt có thêm một vài cặp ví dụ (đầu vào → đầu ra mong muốn) để mô hình bắt chước quy ước. Few-shot đặc biệt hữu ích khi bộ dữ liệu có quy ước gán nhãn riêng, ví dụ SROIE không tính mã số đăng ký công ty vào tên người bán. Đổi lại, prompt dài hơn nên tốn token và thời gian hơn."),
  H2("2.4. Đầu ra có cấu trúc (structured output)"),
  P("Để đầu ra luôn là JSON hợp lệ, có hai cơ chế: (1) **JSON mode** – mô hình được buộc sinh JSON hợp lệ về cú pháp nhưng không bảo đảm đúng các khoá; (2) **ràng buộc theo JSON Schema** (constrained decoding) – bộ giải mã chỉ cho phép các token tạo ra JSON đúng lược đồ. Ollama hỗ trợ cơ chế (2) qua tham số `format`; API DeepSeek hỗ trợ cơ chế (1). Trong cả hai trường hợp, hệ thống vẫn kiểm tra lại đầu ra trước khi ghi vào cơ sở dữ liệu."),
  H2("2.5. Độ đo đánh giá"),
  P("Với mỗi trường, giá trị dự đoán và giá trị chuẩn (gold) được **chuẩn hoá** trước khi so sánh: chữ thường, chuẩn Unicode NFC, bỏ dấu câu và khoảng trắng (seller, address); đưa ngày về dạng YYYY-MM-DD; đưa số tiền về số thực (hiểu được cả \"12.500đ\" và \"1,234.50\"). Một dự đoán đúng khi trùng khớp hoàn toàn sau chuẩn hoá (exact match). Ta tính:"),
  B("**Precision** = số dự đoán đúng / số dự đoán khác rỗng;"),
  B("**Recall** = số dự đoán đúng / số giá trị gold khác rỗng;"),
  B("**F1** = 2·P·R / (P + R); **Macro-F1** là trung bình F1 của bốn trường."),
  P("Ngoài ra, **soft F1** chấp nhận seller/address có độ tương đồng chuỗi (rapidfuzz ratio) ≥ 90% – phản ánh các trường hợp chỉ sai vài ký tự do OCR. Các chỉ số phụ gồm tỉ lệ JSON hợp lệ, thời gian xử lý trung vị mỗi hoá đơn và số token."),
);

// ---------- CHƯƠNG 3
const statRows = [
  ["Ngôn ngữ", "Tiếng Anh (Malaysia)", "Tiếng Việt"],
  ["Tổng số hoá đơn dùng", String(st.sroie.n_total), String(st.mcocr.n_total)],
  ["Tập train / test", `${st.sroie.n_train} / ${st.sroie.n_test} (chia sẵn)`, `${st.mcocr.n_train} / ${st.mcocr.n_test} (tự chia, seed 42)`],
  ["Số từ TB / hoá đơn", String(st.sroie.avg_words), String(st.mcocr.avg_words)],
  ["Số dòng TB / hoá đơn", String(st.sroie.avg_lines), String(st.mcocr.avg_lines)],
  ["Nguồn text OCR", "Có sẵn (đã được người kiểm tra)", "Tự chạy VietOCR trên Colab"],
  ["Tập test có nhãn đủ 4 trường", `${st.sroie.gold_coverage_test.total}/${st.sroie.n_test}`,
    `seller ${st.mcocr.gold_coverage_test.seller}, address ${st.mcocr.gold_coverage_test.address}, date ${st.mcocr.gold_coverage_test.date}, total ${st.mcocr.gold_coverage_test.total} / ${st.mcocr.n_test}`],
];
children.push(
  H1("CHƯƠNG 3. DỮ LIỆU"),
  H2("3.1. SROIE (tiếng Anh)"),
  P("SROIE (Scanned Receipts OCR and Information Extraction) là bộ dữ liệu của cuộc thi ICDAR 2019 gồm ảnh hoá đơn bán lẻ ở Malaysia. Mỗi hoá đơn có file vị trí và nội dung từng dòng chữ (đã được kiểm tra thủ công) và file nhãn JSON cho bốn trường company, address, date, total. Chúng tôi dùng bản trên Kaggle (`urbikn/sroie-datasetv2`) với 626 hoá đơn train và 347 hoá đơn test."),
  H2("3.2. MC-OCR 2021 (tiếng Việt)"),
  P("MC-OCR là bộ dữ liệu của cuộc thi RIVF 2021 gồm ảnh chụp hoá đơn bán lẻ tại Việt Nam (siêu thị, cửa hàng tiện lợi, quán cà phê…), gán nhãn bốn trường SELLER, ADDRESS, TIMESTAMP, TOTAL_COST. Chúng tôi dùng bản trên Kaggle (`domixi1989/vietnamese-receipts-mc-ocr-2021`). Tập test công khai của cuộc thi không có nhãn, vì vậy tập train có nhãn (1.155 ảnh) được chia ngẫu nhiên (seed 42) thành 200 hoá đơn test và phần còn lại làm nguồn ví dụ few-shot."),
  H2("3.3. Vấn đề text OCR của MC-OCR và cách giải quyết"),
  P("Khác với SROIE, MC-OCR **không cung cấp text OCR đầy đủ** cho từng hoá đơn. Kiểm tra cho thấy: file CSV chỉ chứa text của các trường đáp án (dùng làm đầu vào sẽ \"lộ đáp án\"); file `kie_data` có đủ vị trí các ô chữ nhưng **49,1% ô có nội dung rỗng**, và tỉ lệ rỗng ở chính các ô cần trích rất cao (TIMESTAMP 37%, TOTAL_COST 38%, ADDRESS 61%, SELLER 32%)."),
  P("Giải pháp: giữ nguyên **vị trí các ô chữ** do dataset cung cấp, cắt ảnh theo từng ô và dùng **VietOCR** (mô hình công khai VGG-Transformer cho tiếng Việt) để nhận dạng lại **toàn bộ** các ô, chạy trên GPU của Google Colab. Các dòng được sắp xếp theo toạ độ (trên → dưới, trái → phải) để tạo văn bản đầu vào. Vì vậy text MC-OCR là **text OCR máy** có lỗi thật (sai dấu, nhầm \"0\"/\"B\"…), trong khi text SROIE gần như sạch – đây là một nguyên nhân quan trọng của chênh lệch kết quả giữa hai bộ."),
  H2("3.4. Lược đồ chung và thống kê"),
  P("Hai bộ dữ liệu có cùng bốn trường nên có thể dùng chung lược đồ: company/SELLER → `seller`, address/ADDRESS → `address`, date/TIMESTAMP → `date`, total/TOTAL_COST → `total`. Với MC-OCR, nhãn TOTAL_COST gồm cả chữ \"Tổng tiền:\" lẫn con số; chúng tôi chỉ giữ phần là số tiền. Bảng 3.1 tóm tắt thống kê."),
  TABLE(["Thuộc tính", "SROIE", "MC-OCR"], statRows, [2900, 2800, 3371]),
  CAP("Bảng 3.1. Thống kê hai bộ dữ liệu sau tiền xử lý"),
  P("Lưu ý về chất lượng nhãn: nhãn SROIE đã được sửa lỗi OCR (ví dụ text OCR \"SDN BND\" nhưng nhãn là \"SDN BHD\"), nên kể cả khi chép đúng nguyên văn từ text vẫn có thể bị chấm sai; trước khi chạy mô hình, giá trị gold xuất hiện nguyên văn trong text ở 98% (seller), 86% (address), 99% (date) và 99,8% (total) số hoá đơn. Nhãn MC-OCR có quy ước riêng (ví dụ hoá đơn VinMart được gán seller là \"VinCommerce\") và có một phần nhãn nhiễu (xem Chương 6)."),
);

// ---------- CHƯƠNG 4
children.push(
  H1("CHƯƠNG 4. PHƯƠNG PHÁP VÀ HỆ THỐNG"),
  H2("4.1. Kiến trúc tổng thể"),
  P("Hệ thống được viết bằng Python, gồm các module: đọc và chuẩn hoá dữ liệu (`load_data.py`), các bộ trích rút (`extractors/`), chuẩn hoá giá trị (`normalize.py`), cơ sở dữ liệu (`db.py`), chạy thí nghiệm (`run_experiment.py`) và đánh giá (`evaluate.py`, `analyze.py`). Hình 4.1 mô tả luồng xử lý."),
  IMG("fig_pipeline.png", 600, 195),
  CAP("Hình 4.1. Quy trình trích rút thông tin từ hoá đơn vào cơ sở dữ liệu"),
  H2("4.2. Các phương pháp so sánh"),
  TABLE(["Mã", "Phương pháp", "Loại", "Chạy ở đâu", "Ràng buộc đầu ra"], [
    ["M0", "Regex + heuristic", "Baseline (luật)", "Laptop", "–"],
    ["M1", "DeepSeek (deepseek-chat), zero-shot", "API trả phí", "Máy chủ DeepSeek", "JSON mode"],
    ["M2", "DeepSeek, few-shot (2 ví dụ)", "API trả phí", "Máy chủ DeepSeek", "JSON mode"],
    ["M3", "Qwen2.5-3B-Instruct (Q4)", "Model public", "Laptop, CPU (Ollama)", "JSON Schema"],
    ["M4", "Qwen2.5-7B-Instruct (Q4)", "Model public", "Colab GPU T4 (Ollama)", "JSON Schema"],
  ], [700, 3000, 1500, 2071, 1800]),
  CAP("Bảng 4.1. Năm phương pháp trong thực nghiệm"),
  H3("M0 – Baseline dựa trên luật"),
  P("Ngày: biểu thức chính quy cho các dạng dd/mm/yyyy, yyyy-mm-dd, \"25 Dec 2018\". Tổng tiền: duyệt từ cuối hoá đơn lên, tìm dòng chứa từ khoá theo thứ tự ưu tiên (\"ROUNDED TOTAL\", \"GRAND TOTAL\", \"TOTAL\"; \"Tổng cộng\", \"Thanh toán\", \"Tổng tiền\"…), bỏ qua \"SUBTOTAL\"/\"Tạm tính\", lấy số cuối cùng. Người bán: dòng đầu chứa từ gợi ý (SDN BHD, CÔNG TY, SIÊU THỊ…) hoặc dòng đầu có đủ chữ cái. Địa chỉ: các dòng ngay sau tên người bán có chứa số hoặc từ chỉ địa chỉ (JALAN, ĐƯỜNG, PHƯỜNG…), dừng khi gặp TEL/GST/MST."),
  H3("M1–M4 – Mô hình ngôn ngữ"),
  P("Tất cả các mô hình ngôn ngữ dùng **cùng một system prompt** (Phụ lục A), cùng định dạng đầu vào và cùng lược đồ JSON; nhiệt độ (temperature) = 0 để kết quả ổn định. Few-shot (M2) thêm 2 hoá đơn mẫu lấy cố định từ tập train của cùng bộ dữ liệu (có đủ 4 trường, độ dài < 1.200 ký tự) dưới dạng các lượt hội thoại người dùng → trợ lý."),
  P("**API (M1, M2):** gọi REST tới `api.deepseek.com` (chuẩn OpenAI) với `response_format = json_object`. **Model public (M3, M4):** chạy bằng **Ollama** với tham số `format` là JSON Schema, nên bộ giải mã chỉ sinh JSON đúng lược đồ. M3 chạy trên CPU của laptop; M4 chạy trên GPU T4 của Colab với đúng file prompt đó (`llm.py`) rồi nhập kết quả về cơ sở dữ liệu."),
  H2("4.3. Lược đồ JSON"),
  ...CODE([
    '{ "type": "object",',
    '  "properties": {',
    '    "seller":  {"type": ["string","null"], "description": "Tên cửa hàng / công ty bán hàng"},',
    '    "address": {"type": ["string","null"], "description": "Địa chỉ người bán"},',
    '    "date":    {"type": ["string","null"], "description": "Ngày (và giờ) in trên hoá đơn"},',
    '    "total":   {"type": ["string","null"], "description": "Tổng tiền phải trả"} },',
    '  "required": ["seller","address","date","total"] }',
  ]),
  P("Các trường được giữ ở dạng chuỗi \"như in trên hoá đơn\" để tránh mô hình tự đổi định dạng; việc chuẩn hoá ngày/tiền được thực hiện bằng code (`normalize.py`), giúp kết quả nhất quán và kiểm soát được. Đầu ra của mô hình được kiểm tra: phải là JSON object, các khoá thiếu hoặc rỗng được chuyển thành `null`; nếu không phân tích được, bản ghi được đánh dấu `valid_json = 0`."),
  H2("4.4. Cơ sở dữ liệu SQLite"),
  P("Cơ sở dữ liệu `invoices.db` gồm 3 bảng. Mọi phương pháp ghi vào cùng bảng `extractions`, nên việc đánh giá chỉ là một câu lệnh JOIN với bảng `gold`. Ràng buộc UNIQUE(doc_id, method) cho phép chạy lại thí nghiệm mà không gọi lại API cho các hoá đơn đã xử lý (cache), rất quan trọng khi bị gián đoạn mạng hoặc giới hạn lượt gọi."),
  ...CODE([
    "-- Ví dụ truy vấn: các hoá đơn > 500.000đ của một cửa hàng, theo kết quả DeepSeek few-shot",
    "SELECT d.id, e.seller, e.date, e.total FROM extractions e JOIN documents d ON d.id = e.doc_id",
    "WHERE e.method = 'deepseek-fs' AND d.dataset = 'mcocr' AND e.seller LIKE '%Co.op%';",
  ]),
  TABLE(["Bảng", "Các cột chính", "Ý nghĩa"], [
    ["documents", "id, dataset, lang, split, image_path, raw_text", "Hoá đơn và text OCR đầu vào"],
    ["gold", "doc_id, seller, address, date, total", "Nhãn chuẩn của bộ dữ liệu"],
    ["extractions", "doc_id, method, model_version, seller, address, date, total, raw_output, valid_json, latency_ms, tokens_in, tokens_out", "Kết quả của từng phương pháp, kèm chi phí và thời gian"],
  ], [1600, 4300, 3171]),
  CAP("Bảng 4.2. Lược đồ cơ sở dữ liệu"),
);

// ---------- CHƯƠNG 5
const resRows = (D) => {
  const cols = FIELDS.map((f) => bestMark(D, mOrder, (v) => v.f1[f]));
  const macro = bestMark(D, mOrder, (v) => v.macro_f1);
  const softc = bestMark(D, mOrder, (v) => v.soft_macro_f1);
  return METHODS.map((x, i) => [`${x.code}. ${x.label}`, ...cols.map((c) => c[i]), macro[i], softc[i]]);
};
const gaps = ORDER_ALL().map((m) => S[m].macro_f1 - M[m].macro_f1);
const W6 = [2771, 1000, 1000, 1000, 1000, 1150, 1150];
children.push(
  H1("CHƯƠNG 5. THỰC NGHIỆM VÀ KẾT QUẢ"),
  H2("5.1. Cấu hình thực nghiệm"),
  B("Laptop: ThinkPad T480s, Intel Core i5 thế hệ 8, 16 GB RAM, không GPU rời, Windows 11; Python 3.14; Ollama 0.40 (Qwen2.5-3B bản lượng tử hoá Q4, khoảng 1,9 GB)."),
  B("Google Colab: GPU T4 cho VietOCR (OCR MC-OCR) và Qwen2.5-7B (Q4, khoảng 4,7 GB)."),
  B("API: DeepSeek `deepseek-chat` (API trả về phiên bản `deepseek-flash`), temperature 0, max_tokens 600."),
  B(`Tập test: ${st.sroie.n_test} hoá đơn SROIE và ${st.mcocr.n_test} hoá đơn MC-OCR; mọi phương pháp chạy trên toàn bộ tập test.`),
  H2("5.2. Kết quả tổng thể"),
  P("Bảng 5.1 và 5.2 trình bày F1 (%) theo từng trường, Macro-F1 và soft Macro-F1; giá trị tốt nhất mỗi cột được in đậm. Hình 5.1 so sánh Macro-F1 giữa các phương pháp."),
  TABLE(["Phương pháp", "seller", "address", "date", "total", "Macro-F1", "Soft Macro-F1"], resRows(S), W6, { numFrom: 1 }),
  CAP("Bảng 5.1. Kết quả trên SROIE (tiếng Anh, 347 hoá đơn test)"),
  TABLE(["Phương pháp", "seller", "address", "date", "total", "Macro-F1", "Soft Macro-F1"], resRows(M), W6, { numFrom: 1 }),
  CAP("Bảng 5.2. Kết quả trên MC-OCR (tiếng Việt, 200 hoá đơn test)"),
  IMG("fig_macro_f1.png", 600, 288),
  CAP("Hình 5.1. Macro-F1 của 5 phương pháp trên hai bộ dữ liệu"),
  P(`**Nhận xét chung.** Mọi phương pháp dùng LLM đều vượt baseline regex trên cả hai bộ. Trên SROIE, DeepSeek few-shot đạt ${mac(S, "deepseek-fs")}%, cao hơn regex ${(S["deepseek-fs"].macro_f1 - S.regex.macro_f1).toFixed(1)} điểm; cải thiện lớn nhất ở *total* (${f1(S, "regex", "total")}% → ${f1(S, "deepseek-fs", "total")}%) và *address* (${f1(S, "regex", "address")}% → ${f1(S, "deepseek-fs", "address")}%) – hai trường mà luật cứng khó xử lý vì nhiều biến thể (nhiều dòng TOTAL, địa chỉ trải trên nhiều dòng). Trường *date* dễ nhất: các LLM đều đạt khoảng 99% trên SROIE.`),
  H2("5.3. Kết quả theo từng trường"),
  IMG("fig_fields_sroie.png", 600, 272),
  CAP("Hình 5.2. F1 theo trường trên SROIE"),
  IMG("fig_fields_mcocr.png", 600, 272),
  CAP("Hình 5.3. F1 theo trường trên MC-OCR"),
  P(`Trên MC-OCR, *date* (${f1(M, "deepseek-fs", "date")}%) và *total* (${f1(M, "deepseek-fs", "total")}%) vẫn khá tốt, nhưng *address* rất thấp với mọi phương pháp (tối đa ${Math.max(...mOrder.map((m) => M[m].f1.address)).toFixed(1)}%). Soft F1 của address cao hơn nhiều (DeepSeek few-shot: ${M["deepseek-fs"].soft_f1.address.toFixed(1)}%), cho thấy một phần đáng kể lỗi (${E.mcocr["deepseek-fs"].address.near_match || 0} trường hợp với DeepSeek few-shot) chỉ là **sai vài ký tự do OCR** (\"Cảm Phà\" thay vì \"Cẩm Phả\"); phần còn lại chủ yếu do khác quy ước gán nhãn (nhãn gộp cả tên chi nhánh, tiền tố \"Đc:\") hoặc chọn thiếu/thừa dòng địa chỉ.`),
  H2("5.4. API so với mô hình công khai"),
  TABLE(["Tiêu chí", "M1/M2 DeepSeek (API)", "M3 Qwen2.5-3B (CPU)", "M4 Qwen2.5-7B (GPU)"], [
    ["Macro-F1 SROIE", `${mac(S, "deepseek-zs")} / ${mac(S, "deepseek-fs")}`, mac(S, "qwen2.5-3b"), mac(S, "qwen2.5-7b")],
    ["Macro-F1 MC-OCR", `${mac(M, "deepseek-zs")} / ${mac(M, "deepseek-fs")}`, mac(M, "qwen2.5-3b"), mac(M, "qwen2.5-7b")],
    ["Thời gian trung vị / hoá đơn", `~${sec(S, "deepseek-zs")} s`, `~${sec(S, "qwen2.5-3b")} s`, `~${sec(S, "qwen2.5-7b")} s`],
    ["Token vào / ra TB", `${T["deepseek-zs"].avg_in} / ${T["deepseek-zs"].avg_out} (zero-shot); ${T["deepseek-fs"].avg_in} / ${T["deepseek-fs"].avg_out} (few-shot)`,
      `${T["qwen2.5-3b"].avg_in} / ${T["qwen2.5-3b"].avg_out}`, `${T["qwen2.5-7b"].avg_in} / ${T["qwen2.5-7b"].avg_out}`],
    ["JSON hợp lệ", `${S["deepseek-zs"].valid_json}%`, `${S["qwen2.5-3b"].valid_json}%`, `${S["qwen2.5-7b"].valid_json}%`],
    ["Chi phí", "Trả theo token: [điền chi phí thực tế từ trang Usage của DeepSeek] cho toàn bộ ~1.094 lần gọi", "Miễn phí (điện năng, laptop)", "Miễn phí (Colab)"],
    ["Quyền riêng tư", "Hoá đơn gửi ra máy chủ bên thứ ba", "Dữ liệu ở trên máy", "Dữ liệu ở trên máy chủ tự quản lý"],
    ["Phụ thuộc", "Mạng, số dư tài khoản, chính sách nhà cung cấp", "Phần cứng cục bộ", "Cần GPU"],
  ], [2100, 2700, 2135, 2136], { size: 21 }),
  CAP("Bảng 5.3. So sánh API và mô hình công khai"),
  IMG("fig_speed_quality.png", 540, 299),
  CAP("Hình 5.4. Đánh đổi giữa chất lượng (Macro-F1) và thời gian xử lý"),
  P(`API cho chất lượng cao nhất và nhanh nhất (khoảng 1 giây/hoá đơn), không cần phần cứng mạnh. Mô hình công khai 7B trên GPU đạt chất lượng **gần bằng API zero-shot** trên SROIE (${mac(S, "qwen2.5-7b")}% so với ${mac(S, "deepseek-zs")}%) và giữ dữ liệu trong hạ tầng của người dùng – phù hợp với hoá đơn chứa thông tin nhạy cảm. Mô hình 3B chạy được trên laptop không GPU nhưng chậm (~${sec(S, "qwen2.5-3b")} giây/hoá đơn) và kém hơn rõ rệt ở seller/address. Nhờ ràng buộc theo JSON Schema (Ollama) và JSON mode (DeepSeek), **100% đầu ra là JSON hợp lệ** ở mọi mô hình.`),
  H2("5.5. Zero-shot so với few-shot"),
  P(`Thêm hai ví dụ (few-shot) tăng Macro-F1 của DeepSeek từ ${mac(S, "deepseek-zs")}% lên ${mac(S, "deepseek-fs")}% (SROIE) và từ ${mac(M, "deepseek-zs")}% lên ${mac(M, "deepseek-fs")}% (MC-OCR). Mức tăng tập trung ở *seller*: SROIE ${f1(S, "deepseek-zs", "seller")}% → ${f1(S, "deepseek-fs", "seller")}%, MC-OCR ${f1(M, "deepseek-zs", "seller")}% → ${f1(M, "deepseek-fs", "seller")}%. Lý do: ví dụ giúp mô hình học **quy ước gán nhãn** của từng bộ dữ liệu (SROIE bỏ mã số đăng ký công ty như \"(519537-X)\"; MC-OCR dùng tên pháp nhân). Chi phí là số token đầu vào tăng khoảng ${(T["deepseek-fs"].avg_in / T["deepseek-zs"].avg_in).toFixed(1)} lần (${T["deepseek-zs"].avg_in} → ${T["deepseek-fs"].avg_in} token/hoá đơn).`),
  H2("5.6. Tiếng Anh so với tiếng Việt"),
  P(`Cùng một phương pháp, kết quả trên MC-OCR thấp hơn SROIE khoảng ${Math.min(...gaps).toFixed(0)}–${Math.max(...gaps).toFixed(0)} điểm Macro-F1. Nguyên nhân chính không nằm ở khả năng hiểu tiếng Việt của mô hình mà ở **dữ liệu**: (1) text MC-OCR là OCR máy, có lỗi dấu và ký tự, trong khi so sánh exact match đòi hỏi khớp từng ký tự với nhãn đã được người sửa; (2) quy ước gán nhãn đặc thù (VinCommerce, gộp chữ logo vào tên); (3) nhiễu nhãn (Chương 6); (4) ảnh chụp bằng điện thoại, nghiêng, mờ. Soft Macro-F1 thu hẹp khoảng cách (DeepSeek few-shot: ${soft(M, "deepseek-fs")}% so với ${soft(S, "deepseek-fs")}%).`),
);

// ---------- CHƯƠNG 6
const ec = (ds, m, f, k) => (E[ds][m][f][k] || 0);
const errRow = (ds, m, label) => [label, ...FIELDS.map((f) => {
  const n = ["near_match", "partial", "wrong", "missed"].map((k) => ec(ds, m, f, k));
  return `${n[0]} / ${n[1]} / ${n[2]} / ${n[3]}`;
})];
children.push(
  H1("CHƯƠNG 6. PHÂN TÍCH LỖI"),
  P("Mỗi dự đoán sai được phân vào một trong các loại: **near-match** (seller/address giống ≥ 90%, chỉ sai vài ký tự), **partial** (dự đoán chứa gold hoặc ngược lại – thừa/thiếu một phần), **wrong** (sai hẳn), **missed** (bỏ sót – trả null dù có gold). Bảng 6.1 thống kê cho hai mô hình tốt nhất mỗi nhóm."),
  TABLE(["Mô hình · bộ dữ liệu", "seller", "address", "date", "total"], [
    errRow("sroie", "deepseek-fs", "DeepSeek few-shot · SROIE"),
    errRow("sroie", "qwen2.5-7b", "Qwen2.5-7B · SROIE"),
    errRow("mcocr", "deepseek-fs", "DeepSeek few-shot · MC-OCR"),
    errRow("mcocr", "qwen2.5-7b", "Qwen2.5-7B · MC-OCR"),
  ], [2871, 1550, 1550, 1550, 1550], { numFrom: 1, size: 21 }),
  CAP("Bảng 6.1. Số lỗi theo loại: near-match / partial / wrong / missed"),
  H2("6.1. Các nhóm lỗi chính"),
  P("**(a) Khác quy ước gán nhãn (partial).** Lỗi phổ biến nhất ở seller trên SROIE: mô hình chép cả mã số đăng ký, ví dụ dự đoán \"99 SPEED MART S/B (519537-X)\" trong khi nhãn là \"99 SPEED MART S/B\". Few-shot giảm đáng kể lỗi này. Ở address, nhãn đôi khi gồm cả dòng tên chi nhánh, đôi khi không."),
  P("**(b) Lỗi OCR (near-match).** Trên MC-OCR, nhiều địa chỉ chỉ sai dấu: \"Chợ Sủi Phù Thị\" thay vì \"Chợ Sủi Phú Thị\", \"TP Cẩm Hà\" thay vì \"TP Cẩm Phả\". Số tiền cũng bị ảnh hưởng: một hoá đơn có text OCR ghi \"22.000\" ở cả ba dòng tổng/tiền khách trả/tiền mặt trong khi nhãn là \"222.000\"; nhãn \"B.119.014\" (ký tự B do OCR) so với dự đoán \"3.119.014\"."),
  P("**(c) Nhập nhằng giữa các con số tiền.** Hoá đơn có nhiều con số: tổng trước/sau làm tròn, tiền khách đưa, tiền thối. Ví dụ hoá đơn SROIE có \"TOTAL RM42.88\" và \"CASH RM42.90\": mô hình chọn nhầm số tiền mặt khách đưa (42.90) thay vì tổng (42.88)."),
  P("**(d) Quy ước tên pháp nhân.** Hoá đơn VinMart in tên chi nhánh (\"VM+ QNH 88 Trần Phú\") nhưng nhãn là \"VinCommerce\"; KFC được gán \"Cty LD TNHH KFC Viet Nam\". Mô hình chỉ đoán đúng khi tên này xuất hiện trong text hoặc được học qua ví dụ few-shot."),
  P("**(e) Nhiễu nhãn của dataset.** Một số nhãn MC-OCR sai: TIMESTAMP là \"Tổng tiền 236,990\", ngày \"13/88/2020\" hoặc \"19/09/20199\"; một hoá đơn có \"Tổng cộng: 74,000\" và \"Tiền khách trả: VND 200,000\" nhưng nhãn TOTAL_COST lại là 200,000 (mô hình trả lời 74,000 – đúng). Ở các trường hợp này mô hình trả lời đúng ngày thực trên hoá đơn nhưng vẫn bị chấm sai. Ngoài ra ~8–15% hoá đơn test MC-OCR thiếu nhãn cho một số trường (cột gold_missing trong `results.json`)."),
  H2("6.2. Một lỗi của chính hệ thống đánh giá"),
  P("Trong quá trình phân tích, chúng tôi phát hiện hàm chuẩn hoá ngày ban đầu hiểu nhầm chuỗi \"11/08/2020-21-19\" thành năm 2020, tháng 21 và bắt nhầm phần giờ trong \"21:05:55 - 14/08/2020\". Sau khi sửa (chỉ chấp nhận ngày hợp lệ, ưu tiên năm 4 chữ số), toàn bộ phương pháp được chấm lại. Điều này cho thấy với bài toán trích rút, **bước chuẩn hoá và đánh giá cũng cần được kiểm thử cẩn thận** như chính mô hình."),
);

// ---------- CHƯƠNG 7
const g = side["gemini-zs"], q = side["gptoss120b-zs"];
children.push(
  H1("CHƯƠNG 7. THÁCH THỨC KHI TRIỂN KHAI THỰC TẾ"),
  P("Ngoài độ chính xác, quá trình thực nghiệm gặp nhiều vấn đề thực tế có giá trị tham khảo khi chọn giữa API và mô hình công khai:"),
  TABLE(["Vấn đề", "Hiện tượng", "Cách xử lý"], [
    ["Giới hạn gói miễn phí Gemini", "Gemini 3.5 Flash chỉ cho 20 lần gọi/ngày (lỗi 429 GenerateRequestsPerDay)", `Dừng sau ${g ? g.n : 41} hoá đơn (Macro-F1 ${g ? g.macro_f1 : "–"}% trên mẫu nhỏ); chuyển nhà cung cấp`],
    ["Bộ lọc an toàn", `Gemini chặn ${g ? g.blocked : 1} hoá đơn SROIE bình thường với lý do PROHIBITED_CONTENT`, "Ghi nhận là \"không trích được\" thay vì để chương trình lỗi"],
    ["Giới hạn token/ngày của Groq", "GPT-OSS-120B miễn phí: 200.000 token/ngày → chỉ ~300 hoá đơn/ngày", `Hoàn thành SROIE zero-shot (Macro-F1 ${q ? q.macro_f1 : "–"}%), dừng phần còn lại`],
    ["Mạng không ổn định", "Lỗi SSL EOF, connection reset khi gọi API hàng loạt", "Tự động thử lại với thời gian chờ tăng dần (exponential backoff)"],
    ["Bảo mật Windows", "Smart App Control chặn DLL của pydantic_core (và SDK phụ thuộc)", "Gọi REST trực tiếp bằng httpx thay cho SDK"],
    ["Thiếu text OCR (MC-OCR)", "49% ô chữ rỗng trong dataset", "Chạy VietOCR trên Colab (Chương 3)"],
    ["Tài nguyên cục bộ", "Qwen-3B trên CPU ~23 giây/hoá đơn, máy nóng", "Chạy nền có cache/resume; mô hình 7B chuyển sang Colab"],
  ], [2100, 3600, 3371], { size: 21 }),
  CAP("Bảng 7.1. Các vấn đề gặp phải và cách xử lý"),
  P("Bài học: với API, chi phí thực sự không chỉ là tiền token mà còn là **giới hạn lượt gọi, chính sách nội dung và sự phụ thuộc vào nhà cung cấp**; hệ thống cần có cơ chế cache, thử lại và ghi nhận lỗi rõ ràng. Với mô hình công khai, chi phí là **phần cứng và thời gian**, đổi lại toàn quyền kiểm soát dữ liệu và kết quả lặp lại được."),
);

// ---------- CHƯƠNG 8
children.push(
  H1("CHƯƠNG 8. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN"),
  H2("8.1. Kết luận"),
  B(`Đã xây dựng hoàn chỉnh quy trình trích rút thông tin hoá đơn → JSON → SQLite và đánh giá 5 phương pháp trên ${st.sroie.n_test + st.mcocr.n_test} hoá đơn test thuộc hai ngôn ngữ.`),
  B(`LLM vượt trội so với luật: DeepSeek few-shot đạt Macro-F1 ${mac(S, "deepseek-fs")}% (SROIE) và ${mac(M, "deepseek-fs")}% (MC-OCR), so với ${mac(S, "regex")}% và ${mac(M, "regex")}% của regex.`),
  B(`Mô hình công khai Qwen2.5-7B đạt ${mac(S, "qwen2.5-7b")}% trên SROIE – gần bằng API zero-shot – và là lựa chọn tốt khi cần giữ dữ liệu nội bộ; bản 3B chạy được trên laptop nhưng chậm và kém hơn.`),
  B("Few-shot cải thiện rõ ở trường phụ thuộc quy ước gán nhãn (seller). Ràng buộc đầu ra bằng JSON Schema/JSON mode cho 100% JSON hợp lệ."),
  B("Chất lượng OCR và chất lượng nhãn là yếu tố giới hạn chính đối với tiếng Việt."),
  H2("8.2. Hướng phát triển"),
  B("Cải thiện OCR tiếng Việt (mô hình nhận dạng tốt hơn, sửa lỗi chính tả sau OCR) hoặc dùng mô hình đa phương thức đọc trực tiếp ảnh hoá đơn."),
  B("Bổ sung thông tin bố cục (toạ độ dòng chữ) vào prompt hoặc dùng LayoutLM/LayoutXLM; tinh chỉnh (fine-tune LoRA) Qwen trên tập train MC-OCR."),
  B("Mở rộng lược đồ: danh sách mặt hàng, số lượng, đơn giá, thuế, mã số thuế; kiểm tra chéo (tổng các dòng = tổng tiền)."),
  B("Chọn ví dụ few-shot động theo độ tương đồng (retrieval), tự đánh giá độ tin cậy để chuyển các trường hợp khó cho người kiểm tra."),
  B("Xây dựng giao diện demo (Streamlit): tải ảnh/text → JSON → lưu SQLite → tra cứu."),
);

// ---------- TÀI LIỆU THAM KHẢO
const refs = [
  "Z. Huang, K. Chen, J. He, X. Bai, D. Karatzas, S. Lu, C. V. Jawahar, \"ICDAR2019 Competition on Scanned Receipt OCR and Information Extraction,\" Proc. ICDAR, 2019.",
  "X.-S. Vu et al., \"MC-OCR Challenge: Mobile-Captured Image Document Recognition for Vietnamese Receipts,\" Proc. RIVF, 2021.",
  "Y. Xu, M. Li, L. Cui, S. Huang, F. Wei, M. Zhou, \"LayoutLM: Pre-training of Text and Layout for Document Image Understanding,\" Proc. KDD, 2020.",
  "T. Brown et al., \"Language Models are Few-Shot Learners,\" NeurIPS, 2020.",
  "Qwen Team, \"Qwen2.5 Technical Report,\" arXiv:2412.15115, 2024.",
  "DeepSeek-AI, \"DeepSeek-V3 Technical Report,\" arXiv:2412.19437, 2024.",
  "D. Q. Nguyen, A. T. Nguyen, \"PhoBERT: Pre-trained language models for Vietnamese,\" Findings of EMNLP, 2020.",
  "Q. Pham, \"VietOCR – Nhận dạng tiếng Việt sử dụng Transformer và AttentionOCR,\" GitHub: pbcquoc/vietocr.",
  "Ollama – chạy mô hình ngôn ngữ cục bộ, https://ollama.com; tài liệu Structured Outputs.",
  "D. Jurafsky, J. H. Martin, Speech and Language Processing (3rd ed. draft), chương Information Extraction.",
];
children.push(H1("TÀI LIỆU THAM KHẢO"));
refs.forEach((r, i) => children.push(new Paragraph({
  children: [new TextRun({ text: `[${i + 1}] `, bold: true }), ...runs(r)],
  spacing: { after: 100, line: 300 }, indent: { left: 567, hanging: 567 }, alignment: AlignmentType.LEFT,
})));

// ---------- PHỤ LỤC
const prompt = fs.readFileSync(path.join(__dirname, "..", "..", "src", "extractors", "llm.py"), "utf8")
  .match(/SYSTEM_PROMPT = """([\s\S]*?)"""/)[1].split("\n");
children.push(
  H1("PHỤ LỤC"),
  H2("A. System prompt dùng chung cho M1–M4"),
  ...CODE(prompt),
  P("Đầu vào người dùng có dạng `Receipt OCR text: <<< … >>>`. Với few-shot, 2 hoá đơn mẫu và JSON đáp án của chúng được chèn trước dưới dạng các lượt hội thoại.", { noIndent: true }),
  H2("B. Cấu trúc mã nguồn và cách chạy"),
  ...CODE([
    "NLP_FN/",
    "├── colab/01_mcocr_ocr.ipynb        # OCR MC-OCR bằng VietOCR (Colab GPU)",
    "├── colab/02_qwen7b_extract.ipynb   # M4 Qwen2.5-7B (Colab GPU)",
    "├── src/load_data.py                # đọc SROIE/MC-OCR → JSONL + SQLite",
    "├── src/schema.py                   # JSON Schema + kiểm tra đầu ra",
    "├── src/normalize.py                # chuẩn hoá ngày/tiền/chuỗi",
    "├── src/extractors/regex_baseline.py, llm.py",
    "├── src/run_experiment.py           # chạy 1 phương pháp, lưu SQLite (có cache)",
    "├── src/evaluate.py, analyze.py     # P/R/F1, phân tích lỗi, biểu đồ",
    "└── invoices.db                     # cơ sở dữ liệu kết quả",
    "",
    "python src/load_data.py",
    "python src/run_experiment.py --method deepseek-fs --dataset mcocr",
    "python src/evaluate.py",
  ]),
);

// ---------------------------------------------------------------- tài liệu
const doc = new Document({
  creator: "[Họ tên sinh viên]",
  title: "Trích rút thông tin từ hoá đơn → JSON/CSDL",
  styles: {
    default: { document: { run: { font: FONT, size: 26 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 30, bold: true, color: "0F4C46" },
        paragraph: { spacing: { before: 120, after: 240 }, keepNext: true, alignment: AlignmentType.CENTER, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 27, bold: true },
        paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, italics: true },
        paragraph: { spacing: { before: 160, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1701, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 22 })] })] }) },
    children,
  }],
});

const out = path.join(__dirname, "..", "BaoCao_TrichRutThongTin_HoaDon.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("Wrote", out); });
