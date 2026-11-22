"""Đánh giá: Precision / Recall / F1 theo từng trường (exact match sau chuẩn hoá),
thêm F1 'mềm' (rapidfuzz >= 0.9) cho seller/address, và tỉ lệ JSON hợp lệ, latency.

Dùng:  python src/evaluate.py                # tất cả method, mọi dataset (split test)
       python src/evaluate.py --dataset mcocr
"""
import argparse
import sys
from pathlib import Path

from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect  # noqa: E402
from normalize import NORMALIZERS  # noqa: E402
from schema import FIELDS  # noqa: E402


def score(rows, soft=False):
    res = {}
    for f in FIELDS:
        tp = n_pred = n_gold = 0
        for r in rows:
            g, p = NORMALIZERS[f](r[f"g_{f}"]), NORMALIZERS[f](r[f"p_{f}"])
            n_gold += bool(g)
            n_pred += bool(p)
            if g and p:
                ok = (g == p) or (soft and f in ("seller", "address") and fuzz.ratio(g, p) >= 90)
                tp += ok
        prec = tp / n_pred if n_pred else 0.0
        rec = tp / n_gold if n_gold else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        res[f] = (prec, rec, f1)
    return res


def fetch(con, dataset, split):
    q = f"""
    SELECT e.method, d.dataset, e.valid_json, e.latency_ms,
           {", ".join(f"g.{f} AS g_{f}, e.{f} AS p_{f}" for f in FIELDS)}
    FROM extractions e JOIN documents d ON d.id = e.doc_id JOIN gold g ON g.doc_id = e.doc_id
    WHERE d.split = ? {"AND d.dataset = ?" if dataset else ""}
    """
    return con.execute(q, (split, dataset) if dataset else (split,)).fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset")
    ap.add_argument("--split", default="test")
    args = ap.parse_args()

    rows = fetch(connect(), args.dataset, args.split)
    groups = {}
    for r in rows:
        groups.setdefault((r["dataset"], r["method"]), []).append(r)

    hdr = f"{'dataset':7} {'method':14} {'n':>4} " + " ".join(f"{f:>8}" for f in FIELDS) + \
          f" {'macroF1':>8} {'softF1':>7} {'json%':>6} {'ms/doc':>7}"
    print(hdr)
    print("-" * len(hdr))
    for (ds, m), rs in sorted(groups.items()):
        s, ss = score(rs), score(rs, soft=True)
        macro = sum(v[2] for v in s.values()) / len(FIELDS)
        soft = sum(v[2] for v in ss.values()) / len(FIELDS)
        js = 100 * sum(r["valid_json"] for r in rs) / len(rs)
        lat = [r["latency_ms"] for r in rs if r["latency_ms"] is not None]
        lat = sum(lat) / len(lat) if lat else 0
        print(f"{ds:7} {m:14} {len(rs):>4} " + " ".join(f"{s[f][2]*100:8.1f}" for f in FIELDS) +
              f" {macro*100:8.1f} {soft*100:7.1f} {js:6.1f} {lat:7.0f}")
    print("\n(Số trong cột trường = F1 % exact-match sau chuẩn hoá; softF1 cho seller/address chấp nhận fuzzy ≥ 90)")


if __name__ == "__main__":
    main()
