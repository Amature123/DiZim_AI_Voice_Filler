from pydantic import BaseModel
from typing import Any, Optional


class TranscribeResponse(BaseModel):
    text: str


class ExtractRequest(BaseModel):
    text: str
    templateType: str = "hoa-don-gtgt"


class ExtractResponse(BaseModel):
    fields: dict[str, Any]
    templateType: str


class InvoicePublishRequest(BaseModel):
    invoice_data: dict[str, Any]
    viettel_mst: Optional[str] = None
    viettel_user: Optional[str] = None
    viettel_pass: Optional[str] = None


class InvoicePublishResponse(BaseModel):
    run_id: str
    invoice_data: dict[str, Any]
    viettel_response: Optional[dict[str, Any]] = None
    viettel_error: Optional[str] = None
    pdf_url: str


class DocumentRecord(BaseModel):
    id: str
    template_id: str
    audio_text: Optional[str] = None
    extracted: Optional[dict] = None
    output_path: Optional[str] = None
    created_at: str
