"""Chuẩn hoá giá trị trước khi so sánh với gold (dùng chung cho mọi phương pháp)."""
import re
import unicodedata

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def norm_text(s):
    """seller/address: NFC, chữ thường, bỏ mọi ký tự không phải chữ/số (dấu câu, khoảng trắng)."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", str(s)).casefold()
    return "".join(ch for ch in s if ch.isalnum())


def norm_date(s):
    """Đưa về YYYY-MM-DD nếu nhận ra được, ngược lại trả về norm_text."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", str(s))

    def ok(y, mo, d):
        return 1990 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31

    def fmt(y, mo, d):
        return f"{y:04d}-{mo:02d}-{d:02d}"

    def year(y):
        return int(y) + 2000 if len(y) == 2 else int(y)

    # Thử lần lượt các mẫu, ưu tiên năm 4 chữ số; chỉ nhận ngày hợp lệ (tránh bắt nhầm giờ 21:05:55)
    patterns = [
        (r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})(?!\d)", "dmy"),
        (r"(?<!\d)(\d{4})[./-](\d{1,2})[./-](\d{1,2})(?!\d)", "ymd"),
        (r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2})(?!\d)", "dmy"),
    ]
    for pat, order in patterns:
        for m in re.finditer(pat, s):
            a, b, c = m.groups()
            y, mo, d = (year(c), int(b), int(a)) if order == "dmy" else (int(a), int(b), int(c))
            if ok(y, mo, d):
                return fmt(y, mo, d)
    # 25 Dec 2018 / 25-DEC-18
    for m in re.finditer(r"(?<!\d)(\d{1,2})[\s./-]*([A-Za-z]{3})[A-Za-z]*[\s.,/-]*(\d{2,4})(?!\d)", s):
        d, mo, y = m.groups()
        if mo.lower() in MONTHS and ok(year(y), MONTHS[mo.lower()], int(d)):
            return fmt(year(y), MONTHS[mo.lower()], int(d))
    # Ngày 12 tháng 3 năm 2021
    m = re.search(r"(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})", s, re.I)
    if m and ok(int(m.group(3)), int(m.group(2)), int(m.group(1))):
        return fmt(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return norm_text(s)


def parse_amount(s):
    """'12.500đ' -> 12500.0 ; 'RM 1,234.50' -> 1234.5 ; '9.00' -> 9.0. Không đọc được -> None."""
    if s is None:
        return None
    m = re.findall(r"\d[\d.,\s]*\d|\d", str(s))
    if not m:
        return None
    t = max(m, key=len).replace(" ", "")
    if "," in t and "." in t:
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        thou = "." if dec == "," else ","
        t = t.replace(thou, "").replace(dec, ".")
    else:
        sep = "," if "," in t else ("." if "." in t else None)
        if sep:
            groups = t.split(sep)
            # mọi nhóm sau dấu phân cách đều đúng 3 chữ số -> phân cách hàng nghìn
            if all(len(g) == 3 for g in groups[1:]):
                t = t.replace(sep, "")
            else:
                t = "".join(groups[:-1]) + "." + groups[-1]
    try:
        return round(float(t), 2)
    except ValueError:
        return None


def norm_total(s):
    v = parse_amount(s)
    return "" if v is None else f"{v:.2f}"


NORMALIZERS = {"seller": norm_text, "address": norm_text, "date": norm_date, "total": norm_total}
