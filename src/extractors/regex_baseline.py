"""M0 – Baseline dựa trên luật (regex + heuristic), không dùng mô hình học máy."""
import re

DATE_RE = re.compile(
    r"\b\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4}\b"
    r"|\b20\d\d[./-]\d{1,2}[./-]\d{1,2}\b"
    r"|\b\d{1,2}[\s-]*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s,-]*\d{2,4}\b",
    re.I,
)
AMOUNT_RE = re.compile(r"\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?")

TOTAL_KEYS = {
    "en": [r"rounded\s*total", r"grand\s*total", r"total\s*(?:amount|incl|inclusive|\(rm\))", r"nett?\s*total",
           r"amount\s*due", r"\btotal\b"],
    "vi": [r"t[ổo]ng\s*c[ộo]ng", r"t[ổo]ng\s*thanh\s*to[áa]n", r"thanh\s*to[áa]n", r"t[ổo]ng\s*ti[ềe]n",
           r"t[ổo]ng", r"total"],
}
SKIP_TOTAL = re.compile(r"sub\s*-?\s*total|total\s*qty|total\s*item|tạm\s*tính|t[ổo]ng\s*s[ốo]\s*l", re.I)
COMPANY_HINT = re.compile(r"SDN\.?\s*BHD|ENTERPRISE|TRADING|RESTAURANT|STORE|MART|CỬA HÀNG|SIÊU THỊ|CÔNG TY|"
                          r"VINMART|CO\.?OP|BÁCH HÓA|MINI ?STOP|CIRCLE ?K|FAMILYMART|BHX", re.I)
ADDR_STOP = re.compile(r"TEL|FAX|GST|PHONE|ĐT|Đ\.T|SĐT|HOTLINE|MST|INVOICE|RECEIPT|HÓA ĐƠN|DATE|NGÀY|"
                       r"DOC|CASH|BILL|\(\d{4,}|ROC|REG", re.I)
ADDR_HINT = re.compile(r"\d|JALAN|JLN|TAMAN|LOT|NO\.|ĐƯỜNG|PHƯỜNG|QUẬN|P\.|Q\.|TP\.|SỐ|ĐC|ĐỊA CHỈ|HÀ NỘI|HCM",
                       re.I)


def find_date(text):
    m = DATE_RE.search(text)
    return m.group(0) if m else None


def find_total(lines, lang):
    for key in TOTAL_KEYS[lang]:
        # duyệt từ dưới lên: tổng cuối cùng thường là số phải trả
        for i in range(len(lines) - 1, -1, -1):
            ln = lines[i]
            if SKIP_TOTAL.search(ln) or not re.search(key, ln, re.I):
                continue
            tail = re.split(key, ln, flags=re.I)[-1]
            nums = AMOUNT_RE.findall(tail)
            if not nums and i + 1 < len(lines):
                nums = AMOUNT_RE.findall(lines[i + 1])
            if nums:
                return nums[-1].strip()
    return None


def find_seller(lines):
    for ln in lines[:8]:
        if COMPANY_HINT.search(ln):
            return ln.strip()
    for ln in lines[:5]:
        if len(re.sub(r"[^A-Za-zÀ-ỹ]", "", ln)) >= 4:
            return ln.strip()
    return lines[0].strip() if lines else None


def find_address(lines, seller):
    start = lines.index(seller) + 1 if seller in lines else 0
    out = []
    for ln in lines[start:start + 8]:
        if ADDR_STOP.search(ln):
            if out:
                break
            continue
        if out or ADDR_HINT.search(ln):
            out.append(ln.strip())
        if len(out) >= 4:
            break
    return " ".join(out) or None


def extract(text, lang="en"):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    seller = find_seller(lines)
    return {
        "seller": seller,
        "address": find_address(lines, seller),
        "date": find_date(text),
        "total": find_total(lines, lang),
    }
