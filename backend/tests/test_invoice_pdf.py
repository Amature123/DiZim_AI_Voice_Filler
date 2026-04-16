"""Smoke test: generate_pdf produces a non-empty PDF file."""
import os, tempfile, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.invoice_pdf import generate_pdf
from lib.viettel import validate_and_calculate

SAMPLE_DATA = {
    "buyerInfo": {"buyerName": "Test User", "buyerLegalName": "Công ty Test"},
    "generalInvoiceInfo": {"paymentMethodName": "TM/CK", "currencyCode": "VND"},
    "itemInfo": [{"itemName": "Laptop", "unitName": "Cái", "quantity": 2, "unitPrice": 15_000_000, "taxPercentage": 8}],
}

def test_generate_pdf_creates_file():
    data = validate_and_calculate(SAMPLE_DATA)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = f.name
    try:
        generate_pdf(data, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000  # non-trivial PDF
    finally:
        os.unlink(path)
