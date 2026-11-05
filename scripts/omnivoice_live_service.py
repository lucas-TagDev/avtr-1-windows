"""Persistent local TTS worker for the original WebRTC streaming demo."""
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import io
import uuid
import json
import numpy as np
import soundfile as sf
import torch
from omnivoice import OmniVoice
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
VOICES = ROOT / "artifacts/voices"
VOICES.mkdir(parents=True, exist_ok=True)
model = None
prompts = {}
lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    global model
    snapshots = ROOT.parent / ".cache/huggingface/hub/models--openai--whisper-base/snapshots"
    asr = next((p for p in snapshots.glob("*") if (p / "model.safetensors").is_file()), None)
    model = OmniVoice.from_pretrained(str(ROOT.parent / "OmniVoice/models/OmniVoice"),
                                     device_map="cuda:0", dtype=torch.float16,
                                     asr_model_name=str(asr) if asr else "openai/whisper-base", asr_device="cpu", load_asr=True)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:7860", "http://127.0.0.1:7860"],
                   allow_methods=["POST"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"ready": model is not None}


@app.post("/reference")
async def reference(audio: UploadFile = File(...), transcript: str = Form("")):
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in (".wav", ".flac", ".ogg", ".mp3"):
        raise HTTPException(400, "Use WAV, FLAC, OGG ou MP3")
    data = await audio.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "Audio de referencia muito grande")
    voice_id = uuid.uuid4().hex
    path = VOICES / (voice_id + suffix)
    path.write_bytes(data)
    async with lock:
        prompts[voice_id] = await asyncio.to_thread(model.create_voice_clone_prompt,
                                                  ref_audio=str(path), ref_text=transcript.strip() or None)
    (VOICES / (voice_id + ".json")).write_text(json.dumps({"file": path.name, "transcript": transcript}), encoding="utf-8")
    return {"voice_id": voice_id}


@app.get('/voices')
def list_voices():
    result = []
    for path in VOICES.glob('*.json'):
        if len(path.stem) == 32 and all(c in '0123456789abcdef' for c in path.stem):
            result.append({'id': path.stem, 'name': path.stem[:8]})
    return {'voices': result}


@app.delete('/voices/{voice_id}')
async def delete_voice(voice_id: str):
    if len(voice_id) != 32 or any(c not in '0123456789abcdef' for c in voice_id):
        raise HTTPException(400, 'Voz invalida')
    root = VOICES.resolve()
    paths = [(root / (voice_id + suffix)).resolve() for suffix in ('.json', '.wav', '.mp3', '.ogg', '.flac')]
    if any(path.parent != root for path in paths):
        raise HTTPException(400, 'Caminho invalido')
    async with lock:
        if not any(path.is_file() for path in paths):
            raise HTTPException(404, 'Voz nao encontrada')
        prompts.pop(voice_id, None)
        for path in paths:
            path.unlink(missing_ok=True)
    return {'deleted': True}


@app.post("/speak")
async def speak(request: Request):
    body = await request.json()
    text = str(body.get("text", "")).strip()
    if not text or len(text) > 5000:
        raise HTTPException(400, "Texto ausente ou longo demais")
    voice = body.get("voice_id", "")
    if voice and voice not in prompts:
        if len(voice) != 32 or any(c not in "0123456789abcdef" for c in voice):
            raise HTTPException(400, "Voz invalida")
        metadata = VOICES / (voice + ".json")
        if not metadata.is_file():
            raise HTTPException(400, "Selecione novamente o audio da voz")
        saved = json.loads(metadata.read_text(encoding="utf-8"))
        async with lock:
            prompts[voice] = await asyncio.to_thread(model.create_voice_clone_prompt,
                ref_audio=str(VOICES / Path(saved["file"]).name), ref_text=saved["transcript"].strip() or None)
    kwargs = dict(text=text, language="Portuguese", num_step=16)
    if voice:
        kwargs["voice_clone_prompt"] = prompts[voice]
    async with lock:
        audio = await asyncio.to_thread(model.generate, **kwargs)
    pcm = (np.clip(audio[0], -1, 1) * 32767).astype("<i2").tobytes()
    return Response(pcm, media_type="application/octet-stream", headers={"X-Sample-Rate": "24000"})

@app.post("/transcribe")
async def transcribe(request: Request):
    import base64
    body = await request.json()
    raw = base64.b64decode(str(body.get("pcm", "")))
    if not raw or len(raw) > 4_000_000:
        raise HTTPException(400, "Audio invalido")
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    async with lock:
        text = await asyncio.to_thread(model.transcribe, (samples, 24000))
    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7863)
