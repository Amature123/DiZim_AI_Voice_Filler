"""
Viettel S-Invoice — validation + API integration.
Ported from Hiệp's pipeline.py (detect llm/).
"""
import os
import uuid
import requests
from requests.auth import HTTPBasicAuth

# ── CONFIG (env-first, sensible defaults) ──────────────────────────
VIETTEL_MST = os.getenv("VIETTEL_MST", "")
VIETTEL_USER = os.getenv("VIETTEL_USER", "")
VIETTEL_PASS = os.getenv("VIETTEL_PASS", "")
VIETTEL_API_BASE = os.getenv("VIETTEL_API_BASE", "https://api-vinvoice.viettel.vn")
VIETTEL_INVOICE_SERIES = os.getenv("VIETTEL_INVOICE_SERIES", "C25TYY")
VIETTEL_TEMPLATE_CODE = os.getenv("VIETTEL_TEMPLATE_CODE", "1/001")


def validate_and_calculate(data: dict) -> dict:
    """
    Tính lại toàn bộ số liệu từ itemInfo — không tin LLM làm toán.
    Thêm summarizeInfo và taxBreakdowns vào data rồi trả về.
    """
    items = data.get("itemInfo", [])
    total_before = 0
    total_tax = 0
    total_after = 0
    tax_groups: dict[float, dict] = {}

    for idx, item in enumerate(items):
        qty = float(item.get("quantity") or 0)
        price = float(item.get("unitPrice") or 0)
        tax_pct = float(item.get("taxPercentage") or 8)

        amount = round(qty * price)
        tax = round(amount * tax_pct / 100)
        total = amount + tax

        item["selection"] = idx + 1
        item["quantity"] = qty
        item["unitPrice"] = price
        item["itemTotalAmountWithoutTax"] = amount
        item["taxPercentage"] = tax_pct
        item["taxAmount"] = tax
        item["itemTotalAmountWithTax"] = total

        total_before += amount
        total_tax += tax
        total_after += total

        tax_groups.setdefault(tax_pct, {"taxableAmount": 0, "taxAmount": 0})
        tax_groups[tax_pct]["taxableAmount"] += amount
        tax_groups[tax_pct]["taxAmount"] += tax

    data["summarizeInfo"] = {
        "sumOfTotalLineAmountWithoutTax": total_before,
        "totalAmountWithoutTax": total_before,
        "totalTaxAmount": total_tax,
        "totalAmountWithTax": total_after,
        "totalAmountWithTaxInWords": _number_to_vietnamese(int(total_after)),
        "discountAmount": 0,
    }
    data["taxBreakdowns"] = [
        {"taxPercentage": pct, **vals}
        for pct, vals in sorted(tax_groups.items())
    ]
    return data


def send_to_viettel(
    payload: dict,
    mst: str | None = None,
    user: str | None = None,
    pass_: str | None = None,
) -> dict:
    """
    Gửi invoice payload lên Viettel S-Invoice API để phát hành hóa đơn.
    Credentials ưu tiên: tham số > biến môi trường.
    """
    _mst = mst or VIETTEL_MST
    _user = user or VIETTEL_USER
    _pass = pass_ or VIETTEL_PASS

    if not _user or not _pass:
        raise ValueError("Chưa cấu hình VIETTEL_USER / VIETTEL_PASS")

    # Bổ sung các trường bắt buộc của Viettel mà LLM không sinh ra
    info = payload.setdefault("generalInvoiceInfo", {})
    info.setdefault("invoiceType", "1")
    info.setdefault("templateCode", VIETTEL_TEMPLATE_CODE)
    info.setdefault("invoiceSeries", VIETTEL_INVOICE_SERIES)
    info.setdefault("adjustmentType", "1")
    info.setdefault("paymentStatus", True)
    info.setdefault("cusGetInvoiceRight", True)
    info.setdefault("transactionUuid", uuid.uuid4().hex)

    buyer = payload.setdefault("buyerInfo", {})
    buyer.setdefault("buyerNotGetInvoice", 0)

    if "payments" not in payload:
        method = info.get("paymentMethodName", "TM/CK")
        payload["payments"] = [{"paymentMethodName": method}]

    url = (
        f"{VIETTEL_API_BASE}/services/einvoiceapplication/api/"
        f"InvoiceAPI/InvoiceWS/createInvoice/{_mst}"
    )
    resp = requests.post(
        url,
        auth=HTTPBasicAuth(_user, _pass),
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )

    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 401:
        raise PermissionError(
            f"Viettel xác thực thất bại (401). Kiểm tra lại VIETTEL_USER/VIETTEL_PASS. "
            f"Response: {resp.text[:300]}"
        )
    raise RuntimeError(f"Viettel API lỗi {resp.status_code}: {resp.text[:500]}")


# ── HELPERS ────────────────────────────────────────────────────────

def _number_to_vietnamese(n: int) -> str:
    """Chuyển số nguyên thành chữ tiếng Việt. VD: 32400000 → 'Ba mươi...'"""
    if n == 0:
        return "Không đồng"

    don_vi = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def doc_ba(so, co_hang_truoc=False):
        tram = so // 100
        chuc = (so % 100) // 10
        dv = so % 10
        s = ""
        if tram > 0:
            s += don_vi[tram] + " trăm"
        elif co_hang_truoc and (chuc > 0 or dv > 0):
            s += "không trăm"
        if chuc == 0:
            if dv > 0:
                if s:
                    s += " lẻ"
                s += " " + don_vi[dv]
        elif chuc == 1:
            s += " mười"
            if dv == 5:
                s += " lăm"
            elif dv > 0:
                s += " " + don_vi[dv]
        else:
            s += " " + don_vi[chuc] + " mươi"
            if dv == 1:
                s += " mốt"
            elif dv == 4:
                s += " tư"
            elif dv == 5:
                s += " lăm"
            elif dv > 0:
                s += " " + don_vi[dv]
        return s.strip()

    hang = ["", "nghìn", "triệu", "tỷ"]
    nhom = []
    temp = n
    while temp > 0:
        nhom.insert(0, temp % 1000)
        temp //= 1000

    parts = []
    total_groups = len(nhom)
    for i, g in enumerate(nhom):
        if g == 0 and total_groups > 1:
            continue
        bac = total_groups - 1 - i
        t = doc_ba(g, i > 0)
        if bac > 0:
            t += " " + hang[min(bac, len(hang) - 1)]
        if t.strip():
            parts.append(t)

    result = " ".join(parts) + " đồng"
    return result[0].upper() + result[1:]
