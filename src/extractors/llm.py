"""M1–M4: trích rút bằng LLM, gọi trực tiếp qua REST (httpx) — không dùng SDK vì
Smart App Control chặn pydantic_core trên máy này.

- Gemini (API):        https://generativelanguage.googleapis.com
- Ollama (model public, chạy local hoặc trên Colab): http://localhost:11434
Cả hai dùng CHUNG prompt + JSON schema để so sánh công bằng.
"""
import json
import os
import random
import time
from pathlib import Path

import httpx

from schema import FIELDS, INVOICE_SCHEMA, parse_invoice

_here = Path(__file__).resolve()
ROOT = _here.parents[2] if len(_here.parents) > 2 else _here.parent  # trên Colab file nằm ở /content

SYSTEM_PROMPT = """You are an information extraction system for retail receipts (English or Vietnamese).
Given the OCR text of ONE receipt, return a JSON object with exactly these keys:
- "seller": name of the store/company that issued the receipt (as printed, usually near the top)
- "address": the seller's address (join multiple lines with a space; exclude phone/fax/tax numbers)
- "date": the purchase date (and time if printed on the same line), copied as printed
- "total": the final amount the customer must pay (after tax/discount/rounding), copied as printed, digits and separators only
Rules: copy values from the text, do not translate or reformat; fix nothing except obvious spacing;
use null if a field is not present. Output JSON only."""


def build_user_prompt(text):
    return f"Receipt OCR text:\n<<<\n{text}\n>>>"


# ------------------------------------------------------------------ few-shot
def load_fewshot(dataset, k=2, seed=0):
    """Lấy k ví dụ cố định từ tập train của cùng dataset (đủ 4 trường, text không quá dài)."""
    path = ROOT / "data" / "processed" / f"{dataset}.jsonl"
    docs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    pool = [d for d in docs if d["split"] == "train" and all(d["gold"].get(f) for f in FIELDS)
            and len(d["text"]) < 1200]
    return random.Random(seed).sample(pool, k)


def fewshot_messages(examples):
    msgs = []
    for ex in examples:
        msgs.append(("user", build_user_prompt(ex["text"])))
        msgs.append(("assistant", json.dumps({f: ex["gold"][f] for f in FIELDS}, ensure_ascii=False)))
    return msgs


# ------------------------------------------------------------------ Gemini
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
THINKING_LEVEL = os.environ.get("GEMINI_THINKING", "minimal")
GEMINI_MIN_GAP = float(os.environ.get("GEMINI_MIN_GAP", "4"))  # giây giữa 2 request


def _api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env = ROOT / ".env"
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
    return key


def gemini_extract(text, model="gemini-3.5-flash", fewshot=None, max_retries=6):
    contents = []
    for role, msg in fewshot_messages(fewshot or []):
        contents.append({"role": "user" if role == "user" else "model", "parts": [{"text": msg}]})
    contents.append({"role": "user", "parts": [{"text": build_user_prompt(text)}]})
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseJsonSchema": INVOICE_SCHEMA,
            # Gemini 3.x mặc định "suy nghĩ" -> tốn token/thời gian; bài toán trích rút không cần nhiều
            "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
        },
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": _api_key()}
    t0 = time.perf_counter()
    time.sleep(GEMINI_MIN_GAP)  # giãn cách để không vượt giới hạn số request/phút
    for attempt in range(max_retries):
        try:
            r = httpx.post(GEMINI_URL.format(model=model), json=body, headers=headers, timeout=120)
        except httpx.TransportError as e:  # rớt mạng / SSL EOF / connection reset -> thử lại
            wait = min(60, 5 * 2 ** attempt)
            print(f"    Gemini lỗi mạng ({type(e).__name__}), đợi {wait}s ...")
            time.sleep(wait)
            continue
        if r.status_code in (429, 500, 503):  # quá tải / hết quota theo phút -> đợi rồi thử lại
            wait = min(60, 5 * 2 ** attempt)
            print(f"    Gemini {r.status_code}, đợi {wait}s ...")
            time.sleep(wait)
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
        data = r.json()
        usage = data.get("usageMetadata", {})
        if not data.get("candidates"):
            # bị bộ lọc an toàn chặn (vd. PROHIBITED_CONTENT) -> ghi nhận là không trích được
            reason = data.get("promptFeedback", {}).get("blockReason", "NO_CANDIDATES")
            return {
                "fields": {f: None for f in FIELDS}, "valid_json": False, "raw_output": f"BLOCKED: {reason}",
                "latency_ms": int((time.perf_counter() - t0) * 1000),
                "tokens_in": usage.get("promptTokenCount"), "tokens_out": 0,
                "model_version": data.get("modelVersion", model),
            }
        raw = "".join(p.get("text", "") for p in data["candidates"][0]["content"].get("parts", []))
        fields, valid = parse_invoice(raw)
        return {
            "fields": fields, "valid_json": valid, "raw_output": raw,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "tokens_in": usage.get("promptTokenCount"),
            "tokens_out": (usage.get("candidatesTokenCount") or 0) + (usage.get("thoughtsTokenCount") or 0),
            "model_version": data.get("modelVersion", model),
        }
    raise RuntimeError(f"Gemini thất bại sau {max_retries} lần thử")


# ------------------------------------------------------------------ Groq (API, OpenAI-compatible)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _env(name):
    if os.environ.get(name):
        return os.environ[name]
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"')


def _parse_reset(s):
    """'1m26.4s' / '8.8s' / '120ms' -> giây."""
    if not s:
        return None
    import re
    total = 0.0
    for val, unit in re.findall(r"([\d.]+)(ms|m|s|h)", s):
        total += float(val) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]
    return total


def groq_extract(text, model="openai/gpt-oss-120b", fewshot=None, max_retries=8):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, msg in fewshot_messages(fewshot or []):
        messages.append({"role": role, "content": msg})
    messages.append({"role": "user", "content": build_user_prompt(text)})
    body = {
        "model": model, "messages": messages, "temperature": 0, "seed": 0,
        "max_completion_tokens": 800,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "invoice", "strict": True, "schema": dict(INVOICE_SCHEMA, additionalProperties=False)}},
    }
    if "gpt-oss" in model:
        body["reasoning_effort"] = "low"
    headers = {"Authorization": f"Bearer {_env('GROQ_API_KEY')}"}
    t0 = time.perf_counter()
    for attempt in range(max_retries):
        try:
            r = httpx.post(GROQ_URL, json=body, headers=headers, timeout=120)
        except httpx.TransportError as e:
            wait = min(60, 5 * 2 ** attempt)
            print(f"    Groq lỗi mạng ({type(e).__name__}), đợi {wait}s ...")
            time.sleep(wait)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            if "requests per day" in r.text.lower() or "(rpd)" in r.text.lower():
                raise RuntimeError("Groq: hết quota lượt gọi trong ngày")
            wait = float(r.headers.get("retry-after") or 0) or _parse_reset(
                r.headers.get("x-ratelimit-reset-tokens")) or 10
            time.sleep(min(90, wait + 0.5))
            continue
        if r.status_code >= 400:
            # vd. lỗi json_validate_failed: mô hình không sinh được JSON đúng schema
            return {"fields": {f: None for f in FIELDS}, "valid_json": False,
                    "raw_output": f"ERROR {r.status_code}: {r.text[:500]}",
                    "latency_ms": int((time.perf_counter() - t0) * 1000), "model_version": model}
        # chủ động giãn nhịp theo quota token/phút còn lại
        remaining = int(r.headers.get("x-ratelimit-remaining-tokens", "9999") or 9999)
        if remaining < 3000:
            time.sleep(min(60, (_parse_reset(r.headers.get("x-ratelimit-reset-tokens")) or 5) + 0.5))
        data = r.json()
        raw = data["choices"][0]["message"].get("content") or ""
        fields, valid = parse_invoice(raw)
        usage = data.get("usage", {})
        return {
            "fields": fields, "valid_json": valid, "raw_output": raw,
            "latency_ms": int(usage.get("total_time", 0) * 1000) or int((time.perf_counter() - t0) * 1000),
            "tokens_in": usage.get("prompt_tokens"), "tokens_out": usage.get("completion_tokens"),
            "model_version": data.get("model", model),
        }
    raise RuntimeError(f"Groq thất bại sau {max_retries} lần thử")


# ------------------------------------------------------------------ DeepSeek (API trả phí, OpenAI-compatible)
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


def deepseek_extract(text, model="deepseek-chat", fewshot=None, max_retries=6):
    """DeepSeek chỉ hỗ trợ JSON mode (json_object), không ép theo schema như Groq/Ollama,
    nên prompt phải mô tả rõ các khoá; parse_invoice() kiểm tra lại đầu ra."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, msg in fewshot_messages(fewshot or []):
        messages.append({"role": role, "content": msg})
    messages.append({"role": "user", "content": build_user_prompt(text)})
    body = {
        "model": model, "messages": messages, "temperature": 0, "max_tokens": 600,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {_env('DEEPSEEK_API_KEY')}"}
    t0 = time.perf_counter()
    for attempt in range(max_retries):
        try:
            r = httpx.post(DEEPSEEK_URL, json=body, headers=headers, timeout=180)
        except httpx.TransportError as e:
            wait = min(60, 5 * 2 ** attempt)
            print(f"    DeepSeek lỗi mạng ({type(e).__name__}), đợi {wait}s ...")
            time.sleep(wait)
            continue
        if r.status_code == 402:
            raise RuntimeError("DeepSeek: tài khoản hết tiền (402 Insufficient Balance)")
        if r.status_code in (429, 500, 502, 503):
            wait = min(60, 5 * 2 ** attempt)
            print(f"    DeepSeek {r.status_code}, đợi {wait}s ...")
            time.sleep(wait)
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"DeepSeek {r.status_code}: {r.text[:300]}")
        data = r.json()
        raw = data["choices"][0]["message"].get("content") or ""
        fields, valid = parse_invoice(raw)
        usage = data.get("usage", {})
        return {
            "fields": fields, "valid_json": valid, "raw_output": raw,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "tokens_in": usage.get("prompt_tokens"), "tokens_out": usage.get("completion_tokens"),
            "model_version": data.get("model", model),
        }
    raise RuntimeError(f"DeepSeek thất bại sau {max_retries} lần thử")


# ------------------------------------------------------------------ Ollama
def ollama_extract(text, model="qwen2.5:3b", fewshot=None, host=None):
    host = host or os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, msg in fewshot_messages(fewshot or []):
        messages.append({"role": role, "content": msg})
    messages.append({"role": "user", "content": build_user_prompt(text)})
    body = {
        "model": model, "messages": messages, "stream": False,
        "format": INVOICE_SCHEMA,
        "options": {"temperature": 0, "num_ctx": 4096, "seed": 0},
    }
    t0 = time.perf_counter()
    r = httpx.post(f"{host}/api/chat", json=body, timeout=600)
    r.raise_for_status()
    data = r.json()
    raw = data["message"]["content"]
    fields, valid = parse_invoice(raw)
    return {
        "fields": fields, "valid_json": valid, "raw_output": raw,
        "latency_ms": int((time.perf_counter() - t0) * 1000),
        "tokens_in": data.get("prompt_eval_count"), "tokens_out": data.get("eval_count"),
        "model_version": model,
    }
