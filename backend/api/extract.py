from fastapi import APIRouter, HTTPException
from models import ExtractRequest, ExtractResponse
from lib.dashscope import extract_fields
from lib.database import get_template
from lib.prompts import DEFAULT_PROMPTS

router = APIRouter()


@router.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest):
    template = await get_template(req.templateType)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {req.templateType}")

    system_prompt = template["prompt"]

    try:
        fields = extract_fields(req.text, system_prompt)
        return ExtractResponse(fields=fields, templateType=req.templateType)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
