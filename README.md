# ProjectNLP – Trích rút thông tin hoá đơn → JSON → SQLite

Đồ án môn Xử lý ngôn ngữ tự nhiên. Hệ thống đọc **text OCR của hoá đơn bán lẻ**, trích 4 trường
`seller`, `address`, `date`, `total` thành **JSON**, lưu vào **SQLite**, rồi so sánh 5 phương pháp:

| Mã | Phương pháp | Loại |
|---|---|---|
| M0 | Regex + heuristic | Baseline luật |
| M1 / M2 | DeepSeek (`deepseek-chat`) zero-shot / few-shot | API |
| M3 | Qwen2.5-3B qua Ollama (CPU) | Model public |
| M4 | Qwen2.5-7B qua Ollama (Colab GPU) | Model public |

Dữ liệu: **SROIE** (tiếng Anh, 347 hoá đơn test) và **MC-OCR 2021** (tiếng Việt, 200 hoá đơn test) –
xem [DATASHEET.md](DATASHEET.md).

## Kết quả (Macro-F1 %, exact match sau chuẩn hoá)

| Phương pháp | SROIE (EN) | MC-OCR (VI) | Thời gian / hoá đơn |
|---|---|---|---|
| M0 Regex | 68.8 | 48.5 | ~0 s |
| M1 DeepSeek zero-shot | 88.9 | 64.9 | ~1 s |
| **M2 DeepSeek few-shot** | **92.0** | **69.6** | ~1 s |
| M3 Qwen2.5-3B (CPU) | 81.1 | 56.3 | ~23 s |
| M4 Qwen2.5-7B (GPU T4) | 88.4 | 61.8 | ~3.7 s |

100% đầu ra của các mô hình ngôn ngữ là JSON hợp lệ. Chi tiết: [báo cáo](report/BaoCao_TrichRutThongTin_HoaDon.docx),
[slide](report/Slide_TrichRutThongTin_HoaDon.pptx), số liệu đầy đủ trong [report/results.json](report/results.json).

---

## Hướng dẫn cài đặt

### 1. Yêu cầu

| Thành phần | Dùng cho | Bắt buộc? |
|---|---|---|
| Python ≥ 3.10 | Toàn bộ code | Có |
| Git | Tải mã nguồn | Có |
| Tài khoản Kaggle + API token | Tải dataset (chỉ khi muốn chạy lại từ đầu) | Tuỳ chọn |
| API key DeepSeek | M1, M2 | Tuỳ chọn |
| [Ollama](https://ollama.com) | M3 (và M4 nếu có GPU) | Tuỳ chọn |
| Google Colab (GPU T4) | OCR MC-OCR, M4 | Tuỳ chọn |
| Node.js ≥ 18 | Sinh lại báo cáo / slide | Tuỳ chọn |

> Repo đã kèm sẵn **kết quả** (`invoices.db`), **dữ liệu đã xử lý** (`data/processed/`) và **text OCR của MC-OCR**
> (`data/raw/mcocr/mcocr_ocr.jsonl`), nên chỉ cần bước 2 là xem/đánh giá lại được kết quả, không cần API hay GPU.

### 2. Cài đặt cơ bản

```bash
git clone https://github.com/ThanhHang88/ProjectNLP.git
cd ProjectNLP

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Kiểm tra nhanh – in lại bảng kết quả từ `invoices.db` có sẵn:

```bash
python src/evaluate.py
```

### 3. Khoá API (chỉ khi chạy lại M1/M2)

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Mở `.env`, điền `DEEPSEEK_API_KEY=sk-...` (tạo tại platform.deepseek.com → API keys, cần nạp tiền; toàn bộ
thí nghiệm tốn khoảng 1,1 triệu token vào + 0,08 triệu token ra). **Không commit file `.env`** – đã có trong `.gitignore`.

### 4. Tải dataset (chỉ khi muốn chạy lại từ đầu)

1. Kaggle → *Settings* → *API* → *Create New Token*. Với token dạng `KGAT_...`: đặt vào biến môi trường
   `KAGGLE_API_TOKEN` hoặc lưu vào file `~/.kaggle/access_token`. Token dạng cũ (JSON có `username`, `key`)
   đặt ở `~/.kaggle/kaggle.json`.
2. Tải (~3,2 GB):

   ```bash
   python src/download_data.py
   ```

3. Đọc và chuẩn hoá dữ liệu → `data/processed/*.jsonl` + bảng `documents`, `gold` trong `invoices.db`:

   ```bash
   python src/load_data.py
   ```

   MC-OCR dùng `data/raw/mcocr/mcocr_ocr.jsonl` (đã có trong repo). Muốn tự sinh lại file này: mở
   [colab/01_mcocr_ocr.ipynb](colab/01_mcocr_ocr.ipynb) trên Colab (GPU T4) → *Run all* → chép file kết quả vào `data/raw/mcocr/`.

### 5. Chạy thí nghiệm

Mỗi lệnh chạy 1 phương pháp trên 1 dataset (tập test) và ghi vào `invoices.db`. Hoá đơn đã có kết quả sẽ
được **bỏ qua** (cache) – bị ngắt giữa chừng thì chạy lại cùng lệnh. Thêm `--force` để chạy lại toàn bộ,
`--limit 5` để thử nhanh.

```bash
# M0 – regex
python src/run_experiment.py --method regex --dataset sroie
python src/run_experiment.py --method regex --dataset mcocr

# M1, M2 – DeepSeek (cần .env)
python src/run_experiment.py --method deepseek-zs --dataset sroie
python src/run_experiment.py --method deepseek-fs --dataset mcocr

# M3 – Qwen2.5-3B (cần Ollama)
ollama pull qwen2.5:3b
python src/run_experiment.py --method qwen2.5-3b --dataset sroie
```

**M4 – Qwen2.5-7B trên Colab:**

```bash
python src/export_for_colab.py          # tạo colab/test_docs.jsonl
```

Mở [colab/02_qwen7b_extract.ipynb](colab/02_qwen7b_extract.ipynb) trên Colab (GPU T4) → *Run all* → tải lên
`colab/test_docs.jsonl`, `src/extractors/llm.py`, `src/schema.py` → tải về `qwen2.5-7b_results.jsonl`, rồi:

```bash
python src/import_colab_results.py colab/qwen2.5-7b_results.jsonl --method qwen2.5-7b
```

Các method khác có sẵn: `gemini-zs`, `gemini-fs`, `gptoss120b-zs`, `gptoss120b-fs` (cần `GEMINI_API_KEY` / `GROQ_API_KEY`;
gói miễn phí bị giới hạn mạnh, xem Chương 7 báo cáo).

### 6. Đánh giá, phân tích, sinh báo cáo

```bash
python src/evaluate.py                  # bảng P/R/F1 theo method × dataset
python src/analyze.py                   # report/results.json + report/figures/*.png

# (tuỳ chọn) sinh lại slide theo template HUST (report/build/template_hust.pptx)
pip install python-pptx
python report/build/make_slides.py      # -> report/Slide_TrichRutThongTin_HoaDon.pptx

# (tuỳ chọn) sinh lại báo cáo Word
cd report/build
npm install
node make_report.js                     # -> report/BaoCao_TrichRutThongTin_HoaDon.docx
```

> Slide dùng template HUST khổ 4:3: giữ trang bìa và trang cảm ơn của template, các slide nội dung dùng layout
> có dải đỏ + logo Bách Khoa. Tiêu đề dùng font Lato của template (máy chưa cài sẽ tự thay font khác).

### 7. Xem cơ sở dữ liệu

`invoices.db` mở được bằng extension **SQLite Viewer** (VS Code) hoặc **DB Browser for SQLite**:

| Bảng | Nội dung |
|---|---|
| `documents` | id, dataset, lang, split, image_path, raw_text |
| `gold` | nhãn chuẩn: seller, address, date, total |
| `extractions` | kết quả mỗi method + model_version, raw_output, valid_json, latency_ms, tokens_in/out |

```sql
SELECT d.id, e.seller, e.date, e.total, g.total AS gold_total
FROM extractions e JOIN documents d ON d.id = e.doc_id JOIN gold g ON g.doc_id = e.doc_id
WHERE e.method = 'deepseek-fs' AND d.dataset = 'mcocr' LIMIT 10;
```

### Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `DLL load failed ... Application Control policy` (Windows 11) | Smart App Control chặn DLL chưa ký (vd. `pydantic_core`). Code đã gọi API bằng REST qua `httpx` nên không cần SDK; đừng cài `google-genai`, `ollama` (Python SDK). |
| `kaggle.exe: Permission denied` | Dùng `python src/download_data.py` (gọi Kaggle qua Python). |
| `UnicodeEncodeError: 'charmap'` khi in tiếng Việt trên Windows | Đặt `PYTHONIOENCODING=utf-8` trước lệnh. |
| Lỗi 429 / mạng chập chờn khi gọi API | Code tự thử lại; nếu vẫn dừng, chạy lại cùng lệnh (cache sẽ tiếp tục). |
| Qwen-3B rất chậm | Bình thường trên CPU (~20–30 s/hoá đơn). Dùng `--limit` để thử, hoặc chạy 7B trên Colab. |

## Cấu trúc thư mục

```
ProjectNLP/
├── src/
│   ├── download_data.py        # tải dataset từ Kaggle
│   ├── load_data.py            # đọc SROIE/MC-OCR → JSONL + SQLite
│   ├── schema.py               # JSON Schema + kiểm tra đầu ra
│   ├── normalize.py            # chuẩn hoá ngày / tiền / chuỗi
│   ├── db.py                   # SQLite
│   ├── extractors/regex_baseline.py, llm.py
│   ├── run_experiment.py       # chạy 1 method (có cache)
│   ├── export_for_colab.py, import_colab_results.py
│   └── evaluate.py, analyze.py
├── colab/                      # notebook OCR (VietOCR) và Qwen-7B
├── data/processed/             # dữ liệu đã chuẩn hoá (JSONL)
├── data/raw/mcocr/mcocr_ocr.jsonl   # text OCR MC-OCR tự sinh
├── invoices.db                 # CSDL kết quả
├── report/                     # báo cáo, slide, hình, results.json, script sinh
├── DATASHEET.md                # mô tả dữ liệu
├── requirements.txt
└── .env.example
```
