"""Unit tests for validate_and_calculate (no network calls)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.viettel import validate_and_calculate

def test_single_item_calculation():
    data = {
        "itemInfo": [
            {"quantity": 2, "unitPrice": 15_000_000, "taxPercentage": 8}
        ]
    }
    result = validate_and_calculate(data)
    item = result["itemInfo"][0]
    assert item["itemTotalAmountWithoutTax"] == 30_000_000
    assert item["taxAmount"] == 2_400_000
    assert item["itemTotalAmountWithTax"] == 32_400_000
    assert result["summarizeInfo"]["totalAmountWithTax"] == 32_400_000

def test_default_tax_percentage():
    data = {"itemInfo": [{"quantity": 1, "unitPrice": 10_000_000}]}
    result = validate_and_calculate(data)
    assert result["itemInfo"][0]["taxPercentage"] == 8.0

def test_number_to_vietnamese():
    from lib.viettel import _number_to_vietnamese
    assert _number_to_vietnamese(0) == "Không đồng"
    result = _number_to_vietnamese(32_400_000)
    assert "ba mươi" in result.lower() or "mười" in result.lower()
    assert result.endswith("đồng")
