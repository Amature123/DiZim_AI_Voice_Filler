"""
Tạo file PDF hóa đơn GTGT bằng fpdf2.
Ported from Hiệp's pipeline.py (detect llm/).
"""
from pathlib import Path
from datetime import datetime
from fpdf import FPDF


def _find_fonts() -> tuple[str | None, str | None]:
    """Tìm font regular + bold hỗ trợ tiếng Việt trên hệ thống."""
    candidates = [
        ("C:/Windows/Fonts/arial.ttf",    "C:/Windows/Fonts/arialbd.ttf"),
        ("C:/Windows/Fonts/tahoma.ttf",   "C:/Windows/Fonts/tahomabd.ttf"),
        ("C:/Windows/Fonts/times.ttf",    "C:/Windows/Fonts/timesbd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists():
            bold_path = bold if Path(bold).exists() else regular
            return regular, bold_path
    return None, None


def _fmt(amount) -> str:
    """15000000 → '15.000.000'"""
    return f"{int(amount):,}".replace(",", ".")


def generate_pdf(data: dict, output_path: str) -> str:
    """Tạo file PDF hóa đơn GTGT từ dữ liệu JSON đã validate."""
    info = data.get("generalInvoiceInfo", {})
    buyer = data.get("buyerInfo", {})
    items = data.get("itemInfo", [])
    summary = data.get("summarizeInfo", {})

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    reg_path, bold_path = _find_fonts()
    if reg_path:
        pdf.add_font("VN", "",  reg_path)
        pdf.add_font("VN", "B", bold_path)
        fn = "VN"
    else:
        fn = "Helvetica"

    now = datetime.now()

    # ── HEADER ────────────────────────────────────────────
    pdf.set_font(fn, "B", 18)
    pdf.cell(0, 12,
             txt="HÓA ĐƠN GIÁ TRỊ GIA TĂNG" if fn != "Helvetica" else "HOA DON GIA TRI GIA TANG",
             new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font(fn, "", 10)
    pdf.cell(0, 6,
             txt="(BẢN NHÁP / DRAFT)" if fn != "Helvetica" else "(BAN NHAP / DRAFT)",
             new_x="LMARGIN", new_y="NEXT", align="C")

    date_str = (f"Ngày {now.day} tháng {now.month} năm {now.year}"
                if fn != "Helvetica"
                else f"Ngay {now.day} thang {now.month} nam {now.year}")
    pdf.cell(0, 6, txt=date_str, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # ── THÔNG TIN NGƯỜI MUA ────────────────────────────────
    pdf.set_font(fn, "B", 12)
    pdf.cell(0, 8,
             txt="THÔNG TIN NGƯỜI MUA" if fn != "Helvetica" else "THONG TIN NGUOI MUA",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fn, "", 11)

    fields = [
        ("Tên người mua" if fn != "Helvetica" else "Ten nguoi mua",  buyer.get("buyerName", "")),
        ("Tên đơn vị"    if fn != "Helvetica" else "Ten don vi",     buyer.get("buyerLegalName", "")),
        ("Mã số thuế"    if fn != "Helvetica" else "Ma so thue",     buyer.get("buyerTaxCode", "")),
        ("Địa chỉ"       if fn != "Helvetica" else "Dia chi",        buyer.get("buyerAddressLine", "")),
        ("Điện thoại"    if fn != "Helvetica" else "Dien thoai",     buyer.get("buyerPhoneNumber", "")),
        ("Email",                                                      buyer.get("buyerEmail", "")),
        ("Hình thức TT"  if fn != "Helvetica" else "Hinh thuc TT",  info.get("paymentMethodName", "TM/CK")),
        ("Loại tiền"     if fn != "Helvetica" else "Loai tien",      info.get("currencyCode", "VND")),
    ]
    for label, val in fields:
        if val:
            pdf.cell(45, 7, txt=f"{label}:")
            pdf.cell(0, 7, txt=str(val), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── BẢNG HÀNG HÓA ─────────────────────────────────────
    col_w = [12, 68, 18, 18, 37, 37]
    headers = (["STT", "Tên hàng hóa/dịch vụ", "ĐVT", "SL", "Đơn giá", "Thành tiền"]
               if fn != "Helvetica"
               else ["STT", "Ten hang hoa/dich vu", "DVT", "SL", "Don gia", "Thanh tien"])

    pdf.set_font(fn, "B", 9)
    for i, hdr in enumerate(headers):
        pdf.cell(col_w[i], 8, txt=hdr, border=1, align="C")
    pdf.ln()

    pdf.set_font(fn, "", 9)
    for item in items:
        pdf.cell(col_w[0], 8, txt=str(item.get("selection", "")), border=1, align="C")
        pdf.cell(col_w[1], 8, txt=str(item.get("itemName", ""))[:40], border=1)
        pdf.cell(col_w[2], 8, txt=str(item.get("unitName", "")), border=1, align="C")
        pdf.cell(col_w[3], 8, txt=str(int(item.get("quantity", 0))), border=1, align="C")
        pdf.cell(col_w[4], 8, txt=_fmt(item.get("unitPrice", 0)), border=1, align="R")
        pdf.cell(col_w[5], 8, txt=_fmt(item.get("itemTotalAmountWithoutTax", 0)), border=1, align="R")
        pdf.ln()
    pdf.ln(4)

    # ── TỔNG CỘNG ──────────────────────────────────────────
    lbl_w, val_w = 120, 70
    pdf.set_font(fn, "", 11)

    pdf.cell(lbl_w, 7, txt="Cộng tiền hàng chưa thuế:" if fn != "Helvetica" else "Cong tien hang chua thue:", align="R")
    pdf.cell(val_w, 7, txt=_fmt(summary.get("totalAmountWithoutTax", 0)), align="R", new_x="LMARGIN", new_y="NEXT")

    for tb in data.get("taxBreakdowns", []):
        pct = int(tb.get("taxPercentage", 0))
        lbl = f"Thuế GTGT ({pct}%):" if fn != "Helvetica" else f"Thue GTGT ({pct}%):"
        pdf.cell(lbl_w, 7, txt=lbl, align="R")
        pdf.cell(val_w, 7, txt=_fmt(tb.get("taxAmount", 0)), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(fn, "B", 12)
    pdf.cell(lbl_w, 9, txt="Tổng tiền thanh toán:" if fn != "Helvetica" else "Tong tien thanh toan:", align="R")
    pdf.cell(val_w, 9, txt=f'{_fmt(summary.get("totalAmountWithTax", 0))} VND',
             align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font(fn, "", 10)
    words = summary.get("totalAmountWithTaxInWords", "")
    lbl_words = "Số tiền viết bằng chữ: " if fn != "Helvetica" else "So tien viet bang chu: "
    pdf.cell(0, 7, txt=f"{lbl_words}{words}", new_x="LMARGIN", new_y="NEXT")

    # ── CHÂN TRANG ─────────────────────────────────────────
    pdf.ln(14)
    pdf.set_font(fn, "B", 10)
    half = 95
    if fn != "Helvetica":
        pdf.cell(half, 7, txt="NGƯỜI MUA HÀNG", align="C")
        pdf.cell(half, 7, txt="NGƯỜI BÁN HÀNG", align="C")
        pdf.ln()
        pdf.set_font(fn, "", 9)
        pdf.cell(half, 6, txt="(Ký, ghi rõ họ tên)", align="C")
        pdf.cell(half, 6, txt="(Ký, đóng dấu, ghi rõ họ tên)", align="C")
    else:
        pdf.cell(half, 7, txt="NGUOI MUA HANG", align="C")
        pdf.cell(half, 7, txt="NGUOI BAN HANG", align="C")
        pdf.ln()
        pdf.set_font(fn, "", 9)
        pdf.cell(half, 6, txt="(Ky, ghi ro ho ten)", align="C")
        pdf.cell(half, 6, txt="(Ky, dong dau, ghi ro ho ten)", align="C")

    pdf.output(output_path)
    return output_path
