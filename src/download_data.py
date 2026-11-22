"""Tải 2 dataset từ Kaggle vào data/raw/.

Cần Kaggle API token: đặt biến môi trường KAGGLE_API_TOKEN (token dạng KGAT_...)
hoặc file ~/.kaggle/kaggle.json (dạng cũ {"username":..., "key":...}).

  python src/download_data.py            # tải cả hai
  python src/download_data.py sroie      # chỉ SROIE (~0.9GB)
  python src/download_data.py mcocr      # chỉ MC-OCR (~2.3GB)

Gọi Kaggle CLI qua Python (không qua kaggle.exe) để tránh bị Windows Smart App Control chặn.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = {
    "sroie": "urbikn/sroie-datasetv2",
    "mcocr": "domixi1989/vietnamese-receipts-mc-ocr-2021",
}


def main():
    if not os.environ.get("KAGGLE_API_TOKEN"):
        tok = Path.home() / ".kaggle" / "kaggle.json"
        if tok.exists() and tok.read_text(encoding="utf-8").strip().startswith("KGAT_"):
            os.environ["KAGGLE_API_TOKEN"] = tok.read_text(encoding="utf-8").strip()
    from kaggle.cli import main as kaggle_main

    names = sys.argv[1:] or list(DATASETS)
    for name in names:
        out = ROOT / "data" / "raw" / name
        out.mkdir(parents=True, exist_ok=True)
        print(f"== Tải {DATASETS[name]} -> {out}")
        sys.argv = ["kaggle", "datasets", "download", "-d", DATASETS[name], "-p", str(out), "--unzip"]
        kaggle_main()
    print("Xong. Chạy tiếp: python src/load_data.py")


if __name__ == "__main__":
    main()
