"""Turn-based Gemini + local OmniVoice + local AVTR-1, without WebRTC deadlines."""
import asyncio
import base64
import json
import os
import re
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
from windows_paths import voice_root
OMNI = voice_root()
OUTPUT = ROOT / "artifacts/conversations"
OUTPUT.mkdir(parents=True, exist_ok=True)
app = FastAPI()
app.mount("/media", StaticFiles(directory=OUTPUT), name="media")
jobs = {}
gpu_lock = asyncio.Lock()
tasks = set()


@app.get("/")
def index():
    return RedirectResponse("http://localhost:7860", status_code=307)


@app.get("/offline")
def offline():
    return FileResponse(ROOT / "scripts/gemini_local_ui.html")


@app.get("/options")
def options():
    folder = ROOT / "artifacts/main/avatars_artifacts"
    return {"avatars": sorted(p.stem for p in (folder / "reference_frames").glob("*.png")),
            "backgrounds": sorted(p.stem for p in (folder / "backgrounds").glob("*.png"))}


@app.get("/portrait/{avatar}")
def portrait(avatar: str):
    if avatar not in options()["avatars"]:
        raise HTTPException(404, "Avatar nao encontrado")
    return FileResponse(ROOT / f"artifacts/main/avatars_artifacts/reference_frames/{avatar}.png")


@app.get("/idle/{avatar}")
def idle(avatar: str):
    if avatar not in options()["avatars"]:
        raise HTTPException(404, "Avatar nao encontrado")
    path = ROOT / f"artifacts/idle/{avatar}.mp4"
    if not path.is_file():
        raise HTTPException(404, "Animacao de espera indisponivel")
    return FileResponse(path)


@app.get("/jobs/{job_id}")
def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Conversa nao encontrada")
    return jobs[job_id]


async def process(command, folder, logname):
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               HF_HOME=str(ROOT / ".cache/huggingface"))
    with (folder / logname).open("wb") as log:
        child = await asyncio.create_subprocess_exec(*map(str, command), cwd=ROOT,
                                                    env=env, stdout=log, stderr=log)
        try:
            code = await asyncio.wait_for(child.wait(), timeout=3600)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            child.kill()
            await child.wait()
            raise
    if code:
        raise RuntimeError(f"Falha na etapa {logname}. Consulte artifacts/conversations/{folder.name}/{logname}.")


async def run_job(job_id, data, key, history, audio):
    state = jobs[job_id]
    folder = OUTPUT / job_id
    try:
        if not data["test"]:
            state["stage"] = "Aguardando resposta do Gemini"
            parts = [{"text": data["message"] or "Responda ao que eu disse no audio."}]
            if audio:
                source = folder / "microphone.webm"
                source.write_bytes(audio[0])
                wav = folder / "microphone.wav"
                ffmpeg = next((ROOT / ".venv/Lib/site-packages/imageio_ffmpeg/binaries").glob("*.exe"))
                await process([ffmpeg, "-y", "-i", source, "-ac", "1", "-ar", "16000", wav],
                              folder, "microphone.log")
                parts.append({"inlineData": {"mimeType": "audio/wav",
                              "data": base64.b64encode(wav.read_bytes()).decode()}})
            payload = {"contents": history + [{"role": "user", "parts": parts}],
                       "systemInstruction": {"parts": [{"text": data["prompt"]}]},
                       "generationConfig": {"maxOutputTokens": 2048}}
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{data['model']}:generateContent",
                    headers={"x-goog-api-key": key}, json=payload)
            if response.is_error:
                message = response.json().get("error", {}).get("message", "Falha na API")
                raise RuntimeError(f"Gemini ({response.status_code}): {message}".replace(key, "[chave]"))
            candidates = response.json().get("candidates", [])
            text = "".join(p.get("text", "") for p in
                           (candidates[0].get("content", {}).get("parts", []) if candidates else [])
                           if not p.get("thought"))
            if not text.strip():
                raise RuntimeError("O Gemini nao retornou texto. Verifique o modelo e a mensagem.")
        else:
            text = data["message"]
        state["text"] = text
        async with gpu_lock:
            state["stage"] = "Gerando voz local com OmniVoice"
            tts = {"text": text, "reference": data["reference"],
                   "reference_text": data["reference_text"], "output": str(folder / "voice.wav")}
            spec = folder / "tts.json"
            spec.write_text(json.dumps(tts, ensure_ascii=False), encoding="utf-8")
            await process([OMNI / ".venv/Scripts/python.exe", ROOT / "scripts/omnivoice_synthesize.py", spec],
                          folder, "voice.log")
            state["audio"] = f"/media/{job_id}/voice.wav"
            if data["video"]:
                state["stage"] = "Animando o avatar localmente; esta etapa pode levar varios minutos"
                await process([ROOT / ".venv/Scripts/python.exe", ROOT / "scripts/generate_offline.py",
                               "--speech", folder / "voice.wav", "--avatar", data["avatar"],
                               "--bg", data["background"], "--out", folder / "avatar.mp4"],
                              folder, "avatar.log")
                state["video"] = f"/media/{job_id}/avatar.mp4"
        state.update(stage="Pronto", done=True)
    except Exception as exc:
        state.update(stage="Falha", error=str(exc), done=True)


@app.post("/reply")
async def reply(request: Request):
    form = await request.form()
    test = form.get("test") == "true"
    key = str(form.get("key", "")).strip()
    message = str(form.get("message", "")).strip()
    if not test and not key:
        raise HTTPException(400, "Informe a chave Gemini na interface.")
    if test and not message:
        raise HTTPException(400, "Digite o texto para testar a voz local.")
    model = str(form.get("model", "gemini-3.8-flash")).removeprefix("models/")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise HTTPException(400, "Nome de modelo invalido")
    try:
        history = json.loads(str(form.get("history", "[]")))
        assert isinstance(history, list)
    except (ValueError, AssertionError):
        raise HTTPException(400, "Historico invalido")
    if any(not j["done"] for j in jobs.values()):
        raise HTTPException(409, "Aguarde a geracao atual terminar.")
    job_id = uuid.uuid4().hex
    folder = OUTPUT / job_id
    folder.mkdir()
    reference = form.get("reference")
    reference_path = ""
    transcript = str(form.get("reference_text", "")).strip()
    if reference and getattr(reference, "filename", ""):
        if not transcript:
            raise HTTPException(400, "Escreva a transcricao exata do audio de referencia.")
        suffix = Path(reference.filename).suffix.lower()
        if suffix not in (".wav", ".mp3", ".flac", ".ogg"):
            raise HTTPException(400, "Use WAV, MP3, FLAC ou OGG para a voz.")
        blob = await reference.read(20 * 1024 * 1024 + 1)
        if len(blob) > 20 * 1024 * 1024:
            raise HTTPException(400, "O audio de referencia deve ter ate 20 MB.")
        target = folder / ("reference" + suffix)
        target.write_bytes(blob)
        reference_path = str(target)
    audio = None
    recording = form.get("recording")
    if recording and getattr(recording, "filename", ""):
        blob = await recording.read(15 * 1024 * 1024 + 1)
        if len(blob) > 15 * 1024 * 1024:
            raise HTTPException(400, "Grave uma mensagem mais curta.")
        audio = (blob, "audio/webm")
    elif not message:
        raise HTTPException(400, "Digite ou grave uma mensagem.")
    opts = options()
    avatar, background = str(form.get("avatar", "maria")), str(form.get("background", "plain_white"))
    if avatar not in opts["avatars"] or background not in opts["backgrounds"]:
        raise HTTPException(400, "Avatar ou fundo invalido")
    data = dict(test=test, message=message, model=model, reference=reference_path,
                reference_text=transcript, avatar=avatar, background=background,
                video=form.get("video") == "true",
                prompt=str(form.get("prompt", "Responda em portugues, em ate duas frases curtas, sem markdown.")))
    jobs[job_id] = {"stage": "Preparando", "done": False}
    task = asyncio.create_task(run_job(job_id, data, key, history[-12:], audio))
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"id": job_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7862)
