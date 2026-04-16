"""
Local ASR microservice using Qwen3-ASR-0.6B model.

Setup:
  conda create -n qwen3-asr python=3.12 -y
  conda activate qwen3-asr
  pip install -r asr_service/requirements.txt

Download model first:
  pip install huggingface_hub
  hf download Qwen/Qwen3-ASR-0.6B --local-dir ./Qwen3-ASR-0.6B

Run:
  conda activate qwen3-asr
  cd <project_root>
  uvicorn asr_service.main:app --host 0.0.0.0 --port 8001
"""
import os
import time
import tempfile

import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qwen_asr import Qwen3ASRModel

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

MODEL_PATH = os.getenv("ASR_MODEL_PATH", "./Qwen3-ASR-0.6B")
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32

print(f"Loading Qwen3-ASR from {MODEL_PATH} on {DEVICE}...")
t0 = time.perf_counter()
model = Qwen3ASRModel.from_pretrained(
    MODEL_PATH,
    dtype=DTYPE,
    device_map=DEVICE,
    max_inference_batch_size=4,
    max_new_tokens=512,
)
print(f"Model loaded in {time.perf_counter() - t0:.2f}s")

app = FastAPI(title="Qwen3-ASR Local Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_PATH, "device": DEVICE}


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = "Vietnamese"):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data received")

    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        t0 = time.perf_counter()
        results = model.transcribe(audio=tmp_path, language=language)
        elapsed = time.perf_counter() - t0
        text = results[0].text if results else ""
        detected_lang = results[0].language if results else language
        return {"text": text, "language": detected_lang, "inference_time": round(elapsed, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
