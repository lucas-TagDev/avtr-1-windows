"""Start persistent local voice and the original continuously rendered WebRTC session."""
import os
import subprocess
import sys
import time
from pathlib import Path
import httpx
from windows_paths import voice_root

root = Path(__file__).resolve().parents[1]
for executable in (root / '.venv/Scripts/python.exe', voice_root() / '.venv/Scripts/python.exe'):
    if not executable.is_file():
        raise SystemExit('Instalacao incompleta. Execute INSTALAR-WINDOWS.cmd e consulte WINDOWS.md.')
env = os.environ.copy()
env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", HF_HOME=str(root / ".cache/huggingface"))
env.setdefault("AVTR1_ODE_STEPS", "3")
if not (root / "artifacts/silero-vad/silero_vad.onnx").is_file():
    subprocess.run([sys.executable, str(root / "scripts/download_silero_vad.py")], cwd=root, env=env, check=True)
voice = subprocess.Popen([str(voice_root() / ".venv/Scripts/python.exe"),
                          str(root / "scripts/omnivoice_live_service.py")], cwd=root, env=env)
stream = None
try:
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if voice.poll() is not None:
            raise RuntimeError("O servico de voz local encerrou durante a inicializacao")
        try:
            if httpx.get("http://127.0.0.1:7863/health", timeout=2).is_success:
                break
        except httpx.HTTPError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("O servico de voz nao iniciou em 180 segundos")
    stream = subprocess.Popen([sys.executable, str(root / "scripts/run_local_stream.py")], cwd=root, env=env)
    print("Abra http://localhost:7860 e selecione Gemini + voz local.", flush=True)
    while stream.poll() is None and voice.poll() is None:
        time.sleep(0.5)
finally:
    # Stop the process trees so that closing the launcher releases the GPU.
    for proc in (stream, voice):
        if proc is not None and proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
