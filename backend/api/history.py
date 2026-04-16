from fastapi import APIRouter
from lib.database import list_documents

router = APIRouter()


@router.get("/history")
async def history():
    docs = await list_documents(50)
    return docs
