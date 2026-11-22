"""Tổng hợp kết quả cuối cùng cho báo cáo/slide.

Sinh ra report/results.json (mọi con số dùng trong report & slide) và report/figures/*.png
  python src/analyze.py
"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect  # noqa: E402
from evaluate import fetch, score  # noqa: E402
from normalize import NORMALIZERS  # noqa: E402
from schema import FIELDS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report"
FIG = OUT / "figures"

METHODS = [  # (mã, method trong DB, nhãn hiển thị, loại)
    ("M0", "regex", "Regex (luật)", "Baseline"),
    ("M1", "deepseek-zs", "DeepSeek zero-shot", "API"),
    ("M2", "deepseek-fs", "DeepSeek few-shot", "API"),
    ("M3", "qwen2.5-3b", "Qwen2.5-3B (CPU)", "Model public"),
    ("M4", "qwen2.5-7b", "Qwen2.5-7B (Colab GPU)", "Model public"),
]
DATASETS = [("sroie", "SROIE (EN)"), ("mcocr", "MC-OCR (VI)")]


def classify(field, g, p):
    """Loại lỗi cho một trường."""
    gn, pn = NORMALIZERS[field](g), NORMALIZERS[field](p)
    if not gn and not pn:
        return "both_empty"
    if not gn:
        return "gold_missing"      # gold không có nhưng mô hình vẫn trả lời
    if not pn:
        return "missed"            # bỏ sót
    if gn == pn:
        return "correct"
    from rapidfuzz import fuzz
    if field in ("seller", "address") and fuzz.ratio(gn, pn) >= 90:
        return "near_match"        # sai vài ký tự (thường do OCR)
    if gn in pn or pn in gn:
        return "partial"           # thừa/thiếu một phần
    return "wrong"


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    con = connect()
    rows = fetch(con, None, "test")
    groups = {}
    for r in rows:
        groups.setdefault((r["dataset"], r["method"]), []).append(r)

    res = {"methods": [], "datasets": {}, "errors": {}, "examples": {}}
    for code, m, label, kind in METHODS:
        res["methods"].append({"code": code, "method": m, "label": label, "kind": kind})

    for ds, ds_label in DATASETS:
        dres = {"label": ds_label, "by_method": {}}
        for code, m, label, kind in METHODS:
            rs = groups.get((ds, m), [])
            if not rs:
                continue
            s, ss = score(rs), score(rs, soft=True)
            lat = [r["latency_ms"] for r in rs if r["latency_ms"] is not None]
            dres["by_method"][m] = {
                "n": len(rs),
                "f1": {f: round(s[f][2] * 100, 1) for f in FIELDS},
                "precision": {f: round(s[f][0] * 100, 1) for f in FIELDS},
                "recall": {f: round(s[f][1] * 100, 1) for f in FIELDS},
                "macro_f1": round(sum(v[2] for v in s.values()) / 4 * 100, 1),
                "soft_macro_f1": round(sum(v[2] for v in ss.values()) / 4 * 100, 1),
                "soft_f1": {f: round(ss[f][2] * 100, 1) for f in FIELDS},
                "valid_json": round(100 * sum(r["valid_json"] for r in rs) / len(rs), 1),
                "latency_ms_median": int(statistics.median(lat)) if lat else 0,
                "latency_ms_mean": int(statistics.mean(lat)) if lat else 0,
            }
            # phân loại lỗi
            cnt = {f: Counter(classify(f, r[f"g_{f}"], r[f"p_{f}"]) for r in rs) for f in FIELDS}
            res["errors"].setdefault(ds, {})[m] = {f: dict(c) for f, c in cnt.items()}
        res["datasets"][ds] = dres

    # token & chi phí DeepSeek, Qwen
    tok = {}
    for m in ("deepseek-zs", "deepseek-fs", "qwen2.5-3b", "qwen2.5-7b"):
        t = con.execute("SELECT count(*), avg(tokens_in), avg(tokens_out), sum(tokens_in), sum(tokens_out) "
                        "FROM extractions e JOIN documents d ON d.id=e.doc_id WHERE d.split='test' AND method=?",
                        (m,)).fetchone()
        tok[m] = {"n": t[0], "avg_in": round(t[1] or 0), "avg_out": round(t[2] or 0),
                  "sum_in": t[3] or 0, "sum_out": t[4] or 0}
    res["tokens"] = tok

    # ví dụ lỗi tiêu biểu (cho phần phân tích lỗi)
    ex = []
    q = """SELECT e.doc_id, e.method, {cols} FROM extractions e JOIN gold g ON g.doc_id=e.doc_id
           JOIN documents d ON d.id=e.doc_id WHERE d.split='test' AND e.method IN ('deepseek-fs','qwen2.5-7b')"""
    cols = ", ".join(f"g.{f} AS g_{f}, e.{f} AS p_{f}" for f in FIELDS)
    for r in con.execute(q.format(cols=cols)):
        for f in FIELDS:
            c = classify(f, r[f"g_{f}"], r[f"p_{f}"])
            if c in ("wrong", "partial", "near_match", "missed"):
                ex.append({"doc": r["doc_id"], "method": r["method"], "field": f, "type": c,
                           "gold": r[f"g_{f}"], "pred": r[f"p_{f}"]})
    res["examples"] = ex

    # thống kê dataset
    st = {}
    for ds, _ in DATASETS:
        rs = con.execute("SELECT split, raw_text FROM documents WHERE dataset=?", (ds,)).fetchall()
        lens = [len(r["raw_text"].split()) for r in rs]
        lines = [len(r["raw_text"].splitlines()) for r in rs]
        gold = con.execute(f"SELECT {', '.join(FIELDS)} FROM gold g JOIN documents d ON d.id=g.doc_id "
                           "WHERE d.dataset=? AND d.split='test'", (ds,)).fetchall()
        st[ds] = {
            "n_total": len(rs),
            "n_train": sum(r["split"] == "train" for r in rs),
            "n_test": sum(r["split"] == "test" for r in rs),
            "avg_words": round(statistics.mean(lens), 1),
            "avg_lines": round(statistics.mean(lines), 1),
            "gold_coverage_test": {f: sum(1 for g in gold if g[f]) for f in FIELDS},
        }
    res["dataset_stats"] = st

    # các thử nghiệm phụ (API miễn phí) – chỉ để ghi nhận
    side = {}
    for m in ("gemini-zs", "gptoss120b-zs"):
        rs = groups.get(("sroie", m), [])
        if rs:
            s = score(rs)
            side[m] = {"n": len(rs), "macro_f1": round(sum(v[2] for v in s.values()) / 4 * 100, 1),
                       "blocked": con.execute("SELECT count(*) FROM extractions WHERE method=? AND raw_output LIKE "
                                              "'BLOCKED%'", (m,)).fetchone()[0]}
    res["side_experiments"] = side

    (OUT / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    make_figures(res)
    print_summary(res)


def make_figures(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    colors = ["#9AA5B1", "#0F766E", "#14B8A6", "#B45309", "#F59E0B"]
    ms = [m for _, m, _, _ in METHODS]
    labels = [lab for _, _, lab, _ in METHODS]

    # Hình 1: Macro F1 theo phương pháp × dataset
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=200)
    w = 0.16
    for i, m in enumerate(ms):
        vals = [res["datasets"][ds]["by_method"].get(m, {}).get("macro_f1", 0) for ds, _ in DATASETS]
        xs = [j + (i - 2) * w for j in range(len(DATASETS))]
        bars = ax.bar(xs, vals, w * 0.92, label=labels[i], color=colors[i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(range(len(DATASETS)), [lab for _, lab in DATASETS])
    ax.set_ylabel("Macro F1 (%)")
    ax.set_ylim(0, 105)
    ax.legend(ncol=3, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout()
    fig.savefig(FIG / "fig_macro_f1.png")
    plt.close(fig)

    # Hình 2: F1 theo trường cho từng dataset
    for ds, ds_label in DATASETS:
        fig, ax = plt.subplots(figsize=(7.5, 3.4), dpi=200)
        for i, m in enumerate(ms):
            d = res["datasets"][ds]["by_method"].get(m)
            if not d:
                continue
            vals = [d["f1"][f] for f in FIELDS]
            xs = [j + (i - 2) * w for j in range(4)]
            ax.bar(xs, vals, w * 0.92, label=labels[i], color=colors[i])
        ax.set_xticks(range(4), ["seller", "address", "date", "total"])
        ax.set_ylabel("F1 (%)")
        ax.set_ylim(0, 105)
        ax.set_title(ds_label, fontsize=11, loc="left")
        ax.legend(ncol=5, fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1))
        fig.tight_layout()
        fig.savefig(FIG / f"fig_fields_{ds}.png")
        plt.close(fig)

    # Hình 3: Chất lượng vs tốc độ
    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=200)
    for i, m in enumerate(ms[1:], 1):
        for ds, ds_label in DATASETS:
            d = res["datasets"][ds]["by_method"].get(m)
            if not d:
                continue
            ax.scatter(d["latency_ms_median"] / 1000, d["macro_f1"], s=70, color=colors[i],
                       marker="o" if ds == "sroie" else "s", zorder=3)
            left = m == "deepseek-zs"
            ax.annotate(f"{labels[i].split(' (')[0]} · {ds_label.split(' ')[0]}",
                        (d["latency_ms_median"] / 1000, d["macro_f1"]), fontsize=7,
                        xytext=(-8, -3) if left else (8, 2), textcoords="offset points",
                        ha="right" if left else "left")
    ax.set_xscale("log")
    ax.set_xlim(0.15, 60)
    ax.set_xlabel("Thời gian xử lý trung vị / hoá đơn (giây, thang log)")
    ax.set_ylabel("Macro F1 (%)")
    ax.grid(alpha=0.3)
    ax.text(0.99, 0.98, "● SROIE   ■ MC-OCR", transform=ax.transAxes, ha="right", va="top", fontsize=8, color="#555")
    fig.tight_layout()
    fig.savefig(FIG / "fig_speed_quality.png")
    plt.close(fig)

    # Hình 0: sơ đồ pipeline
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(8, 2.6), dpi=200)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 32)
    ax.axis("off")
    steps = [
        ("Ảnh hoá đơn\n(SROIE / MC-OCR)", "#E5E7EB"),
        ("Text OCR\n(có sẵn / VietOCR)", "#E5E7EB"),
        ("Trích rút\nM0–M4", "#CCFBF1"),
        ("Kiểm tra JSON\n+ chuẩn hoá", "#FEF3C7"),
        ("SQLite\ninvoices.db", "#FEF3C7"),
        ("Đánh giá\nP / R / F1", "#E5E7EB"),
    ]
    bw, gap, y = 14.2, 2.8, 12
    for k, (txt, col) in enumerate(steps):
        x = 1 + k * (bw + gap)
        ax.add_patch(FancyBboxPatch((x, y), bw, 12, boxstyle="round,pad=0.4,rounding_size=1.5",
                                    fc=col, ec="#374151", lw=0.8))
        ax.text(x + bw / 2, y + 6, txt, ha="center", va="center", fontsize=7.5)
        if k < len(steps) - 1:
            ax.annotate("", xy=(x + bw + gap - 0.3, y + 6), xytext=(x + bw + 0.5, y + 6),
                        arrowprops=dict(arrowstyle="->", color="#374151", lw=0.9))
    x2 = 1 + 2 * (bw + gap)
    ax.text(x2 + bw / 2, 6.5, "API: DeepSeek (M1, M2)\nModel public: Qwen2.5 3B/7B (M3, M4)\nBaseline: Regex (M0)",
            ha="center", va="center", fontsize=6.8, color="#374151")
    fig.tight_layout()
    fig.savefig(FIG / "fig_pipeline.png")
    plt.close(fig)


def print_summary(res):
    for ds, d in res["datasets"].items():
        print(f"\n== {d['label']}")
        for m, v in d["by_method"].items():
            print(f"  {m:13} n={v['n']:3}  F1={v['f1']}  macro={v['macro_f1']}  soft={v['soft_macro_f1']} "
                  f"json={v['valid_json']}  med_ms={v['latency_ms_median']}")
    print("\ntokens:", res["tokens"])
    print("side:", res["side_experiments"])
    print("stats:", res["dataset_stats"])


if __name__ == "__main__":
    main()
