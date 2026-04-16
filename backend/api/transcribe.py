import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from models import TranscribeResponse

router = APIRouter()

LOCAL_ASR_URL = "http://localhost:8001/transcribe"


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)):
    """
    Forward audio to Phú's local Qwen3-ASR-0.6B service (port 8001).
    Requires asr_service to be running. Falls back gracefully if unavailable.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                LOCAL_ASR_URL,
                files={"audio": (audio.filename or "audio.wav", audio_bytes, audio.content_type or "audio/wav")},
            )
        if resp.status_code == 200:
            return TranscribeResponse(text=resp.json()["text"])
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Local ASR service không khả dụng. Chạy asr_service trước hoặc dùng Web Speech API.",
        )
