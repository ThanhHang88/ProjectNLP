"""Chạy một phương pháp trích rút trên một dataset/split và lưu kết quả vào SQLite.

Ví dụ:
  python src/run_experiment.py --method regex --dataset sroie
  python src/run_experiment.py --method gemini-zs --dataset mcocr --limit 20
Kết quả đã có trong DB sẽ được bỏ qua (cache) trừ khi dùng --force.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect, has_extraction, save_extraction  # noqa: E402


LLM_METHODS = {
    # method         : (backend,  model,                    few-shot?)
    "gemini-zs":       ("gemini", "gemini-3.5-flash",       False),
    "gemini-fs":       ("gemini", "gemini-3.5-flash",       True),
    "gemini-lite-zs":  ("gemini", "gemini-3.5-flash-lite",  False),
    "gptoss120b-zs":   ("groq",   "openai/gpt-oss-120b",    False),
    "gptoss120b-fs":   ("groq",   "openai/gpt-oss-120b",    True),
    "deepseek-zs":     ("deepseek", "deepseek-chat",        False),
    "deepseek-fs":     ("deepseek", "deepseek-chat",        True),
    "qwen2.5-3b":      ("ollama", "qwen2.5:3b",             False),
    "qwen2.5-7b":      ("ollama", "qwen2.5:7b",             False),
}


def get_extractor(method, dataset=None):
    if method in LLM_METHODS:
        from extractors import llm
        backend, model, use_fs = LLM_METHODS[method]
        shots = llm.load_fewshot(dataset) if use_fs else None
        fn = {"gemini": llm.gemini_extract, "groq": llm.groq_extract, "deepseek": llm.deepseek_extract,
              "ollama": llm.ollama_extract}[backend]
        return lambda doc: fn(doc["raw_text"], model=model, fewshot=shots)
    if method == "regex":
        from extractors import regex_baseline

        def run(doc):
            t = time.perf_counter()
            out = regex_baseline.extract(doc["raw_text"], doc["lang"])
            return {"fields": out, "latency_ms": int((time.perf_counter() - t) * 1000), "raw_output": None}
        return run
    raise ValueError(f"Chưa cài method: {method}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True)
    ap.add_argument("--dataset", required=True, choices=["sroie", "mcocr"])
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    con = connect()
    docs = con.execute(
        "SELECT id, lang, raw_text FROM documents WHERE dataset=? AND split=? ORDER BY id",
        (args.dataset, args.split),
    ).fetchall()
    if args.limit:
        docs = docs[: args.limit]
    run = get_extractor(args.method, args.dataset)

    done = skipped = failed = 0
    for i, doc in enumerate(docs, 1):
        if not args.force and has_extraction(con, doc["id"], args.method):
            skipped += 1
            continue
        try:
            r = run(doc)
            save_extraction(con, doc["id"], args.method, r["fields"],
                            raw_output=r.get("raw_output"), valid_json=r.get("valid_json", True),
                            latency_ms=r.get("latency_ms"), tokens_in=r.get("tokens_in"),
                            tokens_out=r.get("tokens_out"), model_version=r.get("model_version"))
            done += 1
        except Exception as e:  # ghi lại lỗi và chạy tiếp
            failed += 1
            print(f"  [lỗi] {doc['id']}: {e}")
        if i % 25 == 0:
            print(f"  {i}/{len(docs)}")
    print(f"[{args.method}/{args.dataset}/{args.split}] mới: {done}, bỏ qua (đã có): {skipped}, lỗi: {failed}")


if __name__ == "__main__":
    main()
