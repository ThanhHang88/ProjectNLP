# Datasheet – Dữ liệu hoá đơn đã xử lý (SROIE + MC-OCR)

Tài liệu mô tả dữ liệu theo mẫu *Datasheets for Datasets* (Gebru et al., 2021). Đối tượng mô tả là
**dữ liệu đã xử lý của dự án** (`data/processed/*.jsonl`, `data/raw/mcocr/mcocr_ocr.jsonl`, bảng `documents`
và `gold` trong `invoices.db`), được tạo từ hai bộ dữ liệu công khai SROIE và MC-OCR 2021.

## Tóm tắt

| | SROIE | MC-OCR 2021 |
|---|---|---|
| Ngôn ngữ | Tiếng Anh (hoá đơn Malaysia) | Tiếng Việt |
| Nguồn gốc | ICDAR 2019 Robust Reading Challenge | RIVF 2021 MC-OCR Challenge |
| Bản dùng (Kaggle) | `urbikn/sroie-datasetv2` | `domixi1989/vietnamese-receipts-mc-ocr-2021` |
| Số hoá đơn | 973 | 1.151 |
| Train / test | 626 / 347 (chia sẵn của cuộc thi) | 951 / 200 (tự chia ngẫu nhiên, seed 42) |
| Nguồn text OCR | Có sẵn, đã được người kiểm tra | **Tự sinh** bằng VietOCR trên Colab |
| Độ dài text (ký tự, TB / trung vị / max) | 668 / 631 / 1.368 | 546 / 527 / 2.187 |
| Số dòng TB / hoá đơn | 31,3 | 23,2 |
| Trường nhãn | company, address, date, total | SELLER, ADDRESS, TIMESTAMP, TOTAL_COST |

## 1. Động cơ (Motivation)

- **Mục đích tạo:** đánh giá bài toán trích rút thông tin (Key Information Extraction) từ hoá đơn thành JSON,
  so sánh baseline luật, API LLM và mô hình công khai trên **cùng một lược đồ** cho hai ngôn ngữ.
- **Người tạo:** nhóm sinh viên thực hiện đồ án môn Xử lý ngôn ngữ tự nhiên (dữ liệu gốc thuộc ban tổ chức
  ICDAR 2019 và RIVF 2021).
- **Kinh phí:** không có; dùng tài nguyên miễn phí (laptop, Google Colab).

## 2. Thành phần (Composition)

**Mỗi bản ghi** là một hoá đơn bán lẻ, lưu dạng JSON Lines:

```json
{
  "id": "mcocr/mcocr_public_145013aagqw",
  "dataset": "mcocr", "lang": "vi", "split": "test",
  "image_path": "data/raw/mcocr/kie_data/kie_data/images/mcocr_public_145013aagqw.jpg",
  "text": "UNIQLO\nVincom Pham Ngọc Thạch\n...\nTổng cộng 2,442,000\n...",
  "gold": {"seller": "WWW.UNIQLO.COM UNIQLO", "address": "Vincom Phạm Ngọc Thạch ...",
           "date": "Ngày Giờ 01/08/2020 20:13", "total": "2,442,000"}
}
```

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | chuỗi | `<dataset>/<mã ảnh gốc>`, duy nhất |
| `dataset`, `lang` | chuỗi | `sroie`/`mcocr`, `en`/`vi` |
| `split` | chuỗi | `train` hoặc `test` |
| `image_path` | chuỗi | đường dẫn ảnh gốc (ảnh **không** có trong repo, tải lại từ Kaggle) |
| `text` | chuỗi | text OCR, các dòng sắp từ trên xuống, trái sang phải (`\n` ngăn dòng) |
| `gold.seller/address/date/total` | chuỗi hoặc `null` | nhãn chuẩn, giữ nguyên cách viết trên hoá đơn |

**Ánh xạ nhãn:** company/SELLER → `seller`; address/ADDRESS → `address`; date/TIMESTAMP → `date`;
total/TOTAL_COST → `total`. MC-OCR có thể có nhiều ô cùng nhãn: các ô được nối bằng dấu cách; với
TOTAL_COST chỉ giữ ô là số tiền (bỏ ô chữ "Tổng tiền:"), lấy ô cuối.

**Độ phủ nhãn (số hoá đơn có nhãn khác rỗng):**

| | seller | address | date | total |
|---|---|---|---|---|
| SROIE train (626) | 626 | 625 | 626 | 625 |
| SROIE test (347) | 347 | 347 | 347 | 347 |
| MC-OCR train (951) | 886 | 892 | 897 | 841 |
| MC-OCR test (200) | 183 | 183 | 189 | 170 |

**Độ dài nhãn trung bình (ký tự):** SROIE – seller 24,8 · address 70,2 · date 9,6 · total 5,1;
MC-OCR – seller 15,5 · address 50,7 · date 25,5 (thường kèm giờ và tiền tố "Ngày:") · total 7,5.

**Phân bố không đồng đều (MC-OCR):** dữ liệu tập trung vào một số ít cửa hàng; nhiều hoá đơn đến từ Cẩm Phả
(Quảng Ninh) và Gia Lâm (Hà Nội). Hai người bán phổ biến nhất chiếm khoảng 50%: `VinCommerce` (314 hoá đơn), `MINIMART ANAN` (267);
tiếp theo `NHÀ SÁCH GD-TC CẨM PHẢ` (93), `CỬA HÀNG NĂM OÁNH` (58); 82 hoá đơn không có nhãn seller.
Kết quả trên MC-OCR vì vậy **không đại diện** cho hoá đơn Việt Nam nói chung.

**Thông tin nhạy cảm:** hoá đơn có thể chứa tên thu ngân/khách hàng, mã thẻ thành viên, số giao dịch.
Dữ liệu gốc đã được ban tổ chức công bố công khai; dự án không thu thập thêm dữ liệu cá nhân.

**Nhiễu và lỗi đã biết:**
- SROIE: nhãn đã được sửa lỗi OCR (vd. text "SDN BND" nhưng nhãn "SDN BHD") nên chép nguyên văn vẫn có thể bị
  chấm sai. Tỉ lệ gold xuất hiện nguyên văn trong text: seller 98%, address 86%, date 99%, total 99,8%.
- MC-OCR: nhãn theo quy ước riêng (hoá đơn VinMart → seller `VinCommerce`; gộp chữ logo vào tên) và có nhãn sai,
  ví dụ TIMESTAMP = "Tổng tiền 236,990", ngày "13/88/2020", "19/09/20199", TOTAL_COST = số tiền khách trả thay vì tổng.
- MC-OCR: text là OCR máy nên có lỗi dấu và ký tự ("Cảm Phà" ↔ "Cẩm Phả", "0B" ↔ "08").

## 3. Quá trình thu thập (Collection process)

- **SROIE:** ảnh scan hoá đơn từ Malaysia, có vị trí + nội dung từng dòng chữ và nhãn 4 trường do ban tổ chức
  ICDAR 2019 gán.
- **MC-OCR:** ảnh chụp hoá đơn bằng điện thoại tại Việt Nam (có nghiêng, mờ, nền phức tạp), nhãn 4 trường do ban
  tổ chức RIVF 2021 gán. Tập test công khai của cuộc thi **không có nhãn** nên không dùng.
- Cả hai được tải từ bản sao trên Kaggle (tháng 11/2026) bằng `src/download_data.py`.

## 4. Tiền xử lý / làm sạch / gán nhãn

1. **SROIE** (`load_data.load_sroie`): đọc file `box/*.txt` (8 toạ độ + text mỗi dòng), sắp dòng theo toạ độ,
   gộp các ô cùng hàng (lệch dọc ≤ 8 px); đọc nhãn từ `entities/*.txt` (JSON, thử UTF-8 rồi Latin-1).
2. **MC-OCR – vấn đề:** bản Kaggle chỉ có text của các ô đã gán nhãn trong file CSV (dùng làm đầu vào sẽ lộ đáp án);
   file `kie_data` có đủ vị trí ô chữ nhưng **49,1% ô rỗng text** (TIMESTAMP 37%, TOTAL_COST 38%, ADDRESS 61%,
   SELLER 32%).
3. **MC-OCR – giải pháp** ([colab/01_mcocr_ocr.ipynb](colab/01_mcocr_ocr.ipynb)): giữ vị trí ô trong `kie_data`
   (ảnh đã xoay thẳng), cắt ảnh từng ô (đệm 3 px), nhận dạng lại **toàn bộ 40.868 ô** của 1.151 ảnh bằng VietOCR
   `vgg_transformer` trên GPU T4 → `data/raw/mcocr/mcocr_ocr.jsonl`. Chỉ còn 2 ô trả về rỗng. Sau đó sắp dòng
   như SROIE. 4 ảnh không có file vị trí ô bị loại (1.155 → 1.151).
4. **Chia dữ liệu MC-OCR:** sắp theo `id`, chọn ngẫu nhiên 200 hoá đơn làm test (`random.Random(42)`), còn lại train.
   Tập train chỉ dùng làm nguồn 2 ví dụ few-shot (cố định, seed 0, đủ 4 trường, text < 1.200 ký tự).
5. **Không sửa nhãn gốc.** Việc chuẩn hoá (chữ thường, NFC, bỏ dấu câu; ngày → YYYY-MM-DD; tiền → số) chỉ thực hiện
   lúc đánh giá (`src/normalize.py`), áp dụng giống nhau cho nhãn và dự đoán.

Dữ liệu thô (ảnh, file gốc) **không** nằm trong repo vì dung lượng (~3,3 GB) và điều khoản phân phối; chạy
`python src/download_data.py` rồi `python src/load_data.py` để tái tạo đúng các file đã xử lý.

## 5. Mục đích sử dụng (Uses)

- **Phù hợp:** học tập và nghiên cứu về trích rút thông tin, so sánh prompt/mô hình, đánh giá ảnh hưởng của lỗi OCR.
- **Không phù hợp:** đánh giá độ chính xác của hệ thống kế toán/thuế thực tế; suy luận về thói quen chi tiêu của cá
  nhân; làm đại diện cho hoá đơn Việt Nam nói chung (phân bố lệch, xem mục 2).
- **Lưu ý khi so sánh kết quả:** số liệu MC-OCR trong dự án dùng text OCR tự sinh và cách chia tự làm, **không so
  sánh trực tiếp** với bảng xếp hạng của cuộc thi MC-OCR 2021. Số liệu SROIE dùng độ đo exact match sau chuẩn hoá
  của dự án, không phải bộ chấm chính thức của ICDAR.

## 6. Phân phối (Distribution)

- Repo phân phối dữ liệu **đã xử lý** (text + nhãn) để tái lập kết quả; ảnh và file gốc tải từ Kaggle.
- Bản quyền thuộc ban tổ chức ICDAR 2019 (SROIE) và RIVF 2021 (MC-OCR); trang Kaggle ghi giấy phép "other/unknown".
  Người dùng cần tuân theo điều khoản của bộ dữ liệu gốc và **chỉ dùng cho mục đích học tập, nghiên cứu**.

## 7. Bảo trì (Maintenance)

- Dữ liệu cố định theo phiên bản Kaggle tải về tháng 11/2026; không có kế hoạch cập nhật định kỳ.
- Lỗi phát hiện thêm (vd. nhãn sai) có thể báo qua mục *Issues* của repo GitHub.

## Tài liệu tham khảo

- T. Gebru et al., "Datasheets for Datasets," *Communications of the ACM*, 2021.
- Z. Huang et al., "ICDAR2019 Competition on Scanned Receipt OCR and Information Extraction," ICDAR 2019.
- X.-S. Vu et al., "MC-OCR Challenge: Mobile-Captured Image Document Recognition for Vietnamese Receipts," RIVF 2021.
- VietOCR: https://github.com/pbcquoc/vietocr
