"""Xuất các hóa đơn test ra colab/test_docs.jsonl để chạy Qwen2.5-7B trên Colab."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
con = connect()
rows = con.execute("SELECT id, dataset, raw_text FROM documents WHERE split='test' ORDER BY id").fetchall()
with open(ROOT / "colab" / "test_docs.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps({"id": r["id"], "dataset": r["dataset"], "text": r["raw_text"]}, ensure_ascii=False) + "\n")
print(len(rows), "docs -> colab/test_docs.jsonl")
