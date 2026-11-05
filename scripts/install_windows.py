"""Bootstrap the three Windows environments; run with Python 3.12."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOICE = ROOT / "OmniVoice"
VOICE_REVISION = "08be0b4ccbac3e13e374e86fbfead4b4cac343e2"

def run(args, cwd=ROOT):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)

def environment(path):
    python = path / "Scripts/python.exe"
    if not python.exists():
        run([sys.executable, "-m", "venv", path])
    run([python, "-m", "ensurepip", "--upgrade"])
    run([python, "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"])
    return python

def main():
    if os.name != "nt" or sys.version_info[:2] != (3,12):
        raise SystemExit("Use Python 3.12 no Windows, sem WSL.")
    run(["git", "--version"])
    run(["nvidia-smi"])
    renderer = environment(ROOT / ".venv")
    streamer = environment(ROOT / ".venv-streamer")
    run([renderer, "-m", "pip", "install", "torch==2.7.1", "torchaudio==2.7.1", "--index-url", "https://download.pytorch.org/whl/cu128"])
    run([renderer, "-m", "pip", "install", "-r", ROOT / "requirements-windows.txt", "tensorrt-cu12==10.11.0.33", "onnx==1.23.2", "Pillow"])
    run([renderer, "-m", "pip", "install", "--no-deps", "-e", ROOT])
    run([streamer, "-m", "pip", "install", "-r", ROOT / "requirements-streamer-windows.txt", "python-dotenv"])
    run([streamer, "-m", "pip", "install", "--no-deps", "-e", ROOT])
    if not VOICE.exists():
        run(["git", "clone", "https://github.com/k2-fsa/OmniVoice.git", VOICE])
        run(["git", "checkout", VOICE_REVISION], cwd=VOICE)
    elif not (VOICE / "pyproject.toml").is_file():
        raise SystemExit("A pasta OmniVoice ja existe, mas nao contem o projeto. Escolha outra pasta para instalar.")
    voice = environment(VOICE / ".venv")
    run([voice, "-m", "pip", "install", "torch==2.7.1", "torchaudio==2.7.1", "--index-url", "https://download.pytorch.org/whl/cu128"])
    run([voice, "-m", "pip", "install", "-e", VOICE, "transformers==5.3.0", "fastapi", "uvicorn", "python-multipart"])
    print("Ambientes instalados. Faca login no Hugging Face e execute PREPARAR-MODELOS.cmd. Consulte WINDOWS.md.")

if __name__ == "__main__":
    main()
