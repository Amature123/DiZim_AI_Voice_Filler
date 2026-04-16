import asyncio
import json
from lib.database import init_db, get_template
from lib.prompts import DEFAULT_PROMPTS
import aiosqlite
from lib.database import DB_PATH

TEMPLATES = [
    {
        "id": "hoa-don-gtgt",
        "name": "Hóa đơn GTGT (Viettel S-Invoice)",
        "fields": json.dumps({
            "buyerInfo": {
                "buyerNotGetInvoice": 0,
                "buyerName": "", "buyerCode": "", "buyerLegalName": "",
                "buyerTaxCode": "", "buyerAddressLine": "",
                "buyerPhoneNumber": "", "buyerEmail": "",
                "buyerBankName": "", "buyerBankAccount": "",
                "buyerIdType": "", "buyerIdNo": "",
            },
            "generalInvoiceInfo": {
                "paymentMethodName": "TM/CK",
                "currencyCode": "VND",
                "exchangeRate": 1,
            },
            "itemInfo": [
                {
                    "lineNumber": 1, "itemCode": "", "itemName": "",
                    "unitName": "", "unitPrice": 0, "quantity": 0,
                    "itemTotalAmountWithoutTax": 0, "taxPercentage": 8,
                    "taxAmount": 0, "itemTotalAmountWithTax": 0,
                }
            ],
        }),
        "docx_path": "",
        "prompt": DEFAULT_PROMPTS["hoa-don-gtgt"],
    },
]


async def seed():
    await init_db()
    for t in TEMPLATES:
        existing = await get_template(t["id"])
        if existing is None:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO templates (id, name, fields, docx_path, prompt) VALUES (?, ?, ?, ?, ?)",
                    (t["id"], t["name"], t["fields"], t["docx_path"], t["prompt"]),
                )
                await db.commit()
            print(f"Seeded template: {t['id']}")
        else:
            # Update prompt in case it changed
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE templates SET prompt = ?, name = ? WHERE id = ?",
                    (t["prompt"], t["name"], t["id"]),
                )
                await db.commit()
            print(f"Updated template: {t['id']}")


if __name__ == "__main__":
    asyncio.run(seed())
