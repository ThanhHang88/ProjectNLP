"""Schema chung cho hóa đơn của cả SROIE (tiếng Anh) và MC-OCR (tiếng Việt).

SROIE:  company  / address / date      / total
MC-OCR: SELLER   / ADDRESS / TIMESTAMP / TOTAL_COST

Dùng JSON Schema thuần (dict) thay cho pydantic vì Windows Smart App Control
chặn DLL của pydantic_core trên máy này. Gemini và Ollama đều nhận JSON Schema trực tiếp.
"""
import json

FIELDS = ["seller", "address", "date", "total"]

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "seller": {"type": ["string", "null"], "description": "Tên cửa hàng / công ty bán hàng"},
        "address": {"type": ["string", "null"], "description": "Địa chỉ người bán"},
        "date": {"type": ["string", "null"],
                 "description": "Ngày (và giờ nếu có) in trên hóa đơn, giữ nguyên như trong văn bản"},
        "total": {"type": ["string", "null"], "description": "Tổng tiền phải trả, giữ nguyên như trong văn bản"},
    },
    "required": FIELDS,
}


def parse_invoice(raw):
    """Kiểm tra đầu ra của mô hình. Trả về (fields, valid_json)."""
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(data, dict):
            raise ValueError("không phải object")
    except Exception:
        return {f: None for f in FIELDS}, False
    out = {}
    for f in FIELDS:
        v = data.get(f)
        out[f] = None if v in (None, "", "null") else str(v).strip()
    return out, True
