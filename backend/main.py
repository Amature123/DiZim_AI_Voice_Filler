import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api import transcribe, extract, invoice, history
from lib.database import init_db
from seed import seed

app = FastAPI(title="DiZim AI — Viettel Invoice Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.include_router(transcribe.router, prefix="/api")
app.include_router(extract.router,    prefix="/api")
app.include_router(invoice.router,    prefix="/api")
app.include_router(history.router,    prefix="/api")


@app.on_event("startup")
async def startup():
    await init_db()
    await seed()


@app.get("/")
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "ok", "service": "DiZim AI — Viettel Invoice Assistant"}
