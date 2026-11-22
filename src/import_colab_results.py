"""Nhập kết quả chạy trên Colab (vd. colab/qwen2.5-7b_results.jsonl) vào SQLite.

  python src/import_colab_results.py colab/qwen2.5-7b_results.jsonl --method qwen2.5-7b
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect, save_extraction  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("path")
ap.add_argument("--method", required=True)
args = ap.parse_args()

con = connect()
n = 0
for line in open(args.path, encoding="utf-8"):
    r = json.loads(line)
    save_extraction(con, r["id"], args.method, r["fields"], raw_output=r.get("raw_output"),
                    valid_json=r.get("valid_json", True), latency_ms=r.get("latency_ms"),
                    tokens_in=r.get("tokens_in"), tokens_out=r.get("tokens_out"),
                    model_version=r.get("model_version"))
    n += 1
print(f"Đã nhập {n} kết quả cho method={args.method}")
