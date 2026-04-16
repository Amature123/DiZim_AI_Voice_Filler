import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models import InvoicePublishRequest, InvoicePublishResponse
from lib.viettel import validate_and_calculate, send_to_viettel
from lib.invoice_pdf import generate_pdf
from lib.database import create_document

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/invoice/publish", response_model=InvoicePublishResponse)
async def publish_invoice(req: InvoicePublishRequest):
    """
    Validate invoice data, publish to Viettel S-Invoice, generate PDF.
    Viettel credentials: request body > .env fallback.
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: validate & recalculate
    try:
        invoice_data = validate_and_calculate(req.invoice_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation failed: {e}")

    # Step 2: send to Viettel
    viettel_response = None
    viettel_error = None
    try:
        viettel_response = send_to_viettel(
            invoice_data,
            mst=req.viettel_mst or None,
            user=req.viettel_user or None,
            pass_=req.viettel_pass or None,
        )
    except Exception as e:
        viettel_error = str(e)

    # Step 3: generate PDF regardless of Viettel outcome
    pdf_path = str(run_dir / "invoice.pdf")
    try:
        generate_pdf(invoice_data, pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Step 4: save to DB
    doc_id = run_id
    await create_document({
        "id": doc_id,
        "template_id": "hoa-don-gtgt",
        "audio_text": None,
        "extracted": str(invoice_data),
        "output_path": pdf_path,
    })

    return InvoicePublishResponse(
        run_id=run_id,
        invoice_data=invoice_data,
        viettel_response=viettel_response,
        viettel_error=viettel_error,
        pdf_url=f"/api/invoice/pdf/{run_id}",
    )


@router.get("/invoice/pdf/{run_id}")
async def download_pdf(run_id: str):
    """Download generated invoice PDF."""
    if ".." in run_id or "/" in run_id or "\\" in run_id:
        raise HTTPException(status_code=400, detail="Invalid run_id")
    pdf_path = OUTPUT_DIR / run_id / "invoice.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"invoice_{run_id}.pdf",
    )
