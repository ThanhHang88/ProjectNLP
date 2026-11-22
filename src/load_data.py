"""Đọc SROIE và MC-OCR, đưa về dạng chung:
{id, dataset, lang, split, image_path, text, gold:{seller,address,date,total}}
và ghi ra data/processed/<dataset>.jsonl + SQLite.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize import parse_amount  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"


def lines_to_text(items):
    """items: list (y, x, text). Sắp xếp từ trên xuống, trái sang phải; gộp các ô cùng hàng."""
    items = sorted(items, key=lambda t: (t[0], t[1]))
    rows, cur, cur_y = [], [], None
    for y, x, txt in items:
        if cur and abs(y - cur_y) > 8:  # khác hàng
            rows.append(cur)
            cur = []
        if not cur:
            cur_y = y
        cur.append((x, txt))
    if cur:
        rows.append(cur)
    return "\n".join(" ".join(t for _, t in sorted(r)) for r in rows)


def _read_text(path):
    for enc in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue


# ---------------------------------------------------------------- SROIE
def load_sroie():
    base = RAW / "sroie" / "SROIE2019"
    docs = []
    for split in ("train", "test"):
        for box in sorted((base / split / "box").glob("*.txt")):
            items = []
            for line in _read_text(box).splitlines():
                parts = line.strip().split(",", 8)  # 8 toạ độ, phần còn lại là text (có thể chứa dấu phẩy)
                if len(parts) < 9 or not parts[8].strip():
                    continue
                xs, ys = list(map(int, parts[0:8:2])), list(map(int, parts[1:8:2]))
                items.append((min(ys), min(xs), parts[8].strip()))
            ent_path = base / split / "entities" / box.name
            ent = json.loads(_read_text(ent_path))
            docs.append({
                "id": f"sroie/{box.stem}",
                "dataset": "sroie", "lang": "en", "split": split,
                "image_path": str((base / split / "img" / f"{box.stem}.jpg").relative_to(ROOT)),
                "text": lines_to_text(items),
                "gold": {
                    "seller": ent.get("company"),
                    "address": ent.get("address"),
                    "date": ent.get("date"),
                    "total": ent.get("total"),
                },
            })
    return docs


# ---------------------------------------------------------------- MC-OCR
MCOCR_TEST_SIZE = 200
SEED = 42


def _mcocr_gold(texts, labels):
    by = {}
    for t, l in zip(texts, labels):
        by.setdefault(l.strip(), []).append(t.strip())
    # TOTAL_COST gồm cả nhãn chữ ("Tổng tiền:") lẫn con số -> giữ phần là số tiền (lấy cái cuối)
    totals = [t for t in by.get("TOTAL_COST", []) if parse_amount(t) is not None]
    return {
        "seller": " ".join(by.get("SELLER", [])) or None,
        "address": " ".join(by.get("ADDRESS", [])) or None,
        "date": " ".join(by.get("TIMESTAMP", [])) or None,
        "total": totals[-1] if totals else None,
    }


def load_mcocr():
    import pandas as pd

    base = RAW / "mcocr"
    ocr_path = base / "mcocr_ocr.jsonl"
    if not ocr_path.exists():
        raise NotImplementedError(f"chưa có {ocr_path.name} (chạy colab/01_mcocr_ocr.ipynb rồi chép file vào {base})")

    df = pd.read_csv(base / "mcocr_train_df.csv")
    gold = {}
    for _, r in df.iterrows():
        texts = str(r["anno_texts"]).split("|||")
        labels = str(r["anno_labels"]).split("|||")
        gold[r["img_id"].rsplit(".", 1)[0]] = _mcocr_gold(texts, labels)

    docs = []
    for line in ocr_path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["img_id"] not in gold:
            continue
        items = [(min(b["poly"][1::2]), min(b["poly"][0::2]), b["text"].strip())
                 for b in r["boxes"] if b["text"].strip()]
        docs.append({
            "id": f"mcocr/{r['img_id']}",
            "dataset": "mcocr", "lang": "vi", "split": "train",
            "image_path": f"data/raw/mcocr/kie_data/kie_data/images/{r['img_id']}.jpg",
            "text": lines_to_text(items),
            "gold": gold[r["img_id"]],
        })
    docs.sort(key=lambda d: d["id"])
    rng = random.Random(SEED)
    for d in rng.sample(docs, min(MCOCR_TEST_SIZE, len(docs))):
        d["split"] = "test"
    return docs


# ---------------------------------------------------------------- main
def save(docs, name):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from db import connect, insert_document

    con = connect()
    for name, loader in [("sroie", load_sroie), ("mcocr", load_mcocr)]:
        try:
            docs = loader()
        except NotImplementedError as e:
            print(f"[{name}] bỏ qua: {e}")
            continue
        save(docs, name)
        for d in docs:
            insert_document(con, d)
        con.commit()
        by_split = {}
        for d in docs:
            by_split[d["split"]] = by_split.get(d["split"], 0) + 1
        print(f"[{name}] {len(docs)} tài liệu: {by_split}")
