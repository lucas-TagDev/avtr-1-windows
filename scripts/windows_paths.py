"""Project-local paths; retain read compatibility with installations made before this layout."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def voice_root():
    local = ROOT / 'OmniVoice'
    if local.exists():
        return local
    # Existing virtual environments contain absolute paths and cannot simply be moved.
    legacy = ROOT.parent / 'OmniVoice'
    return legacy if (legacy / '.venv/Scripts/python.exe').is_file() else local

def whisper_cache():
    local = ROOT / '.cache/huggingface/hub'
    if (local / 'models--openai--whisper-base/snapshots').exists():
        return local
    legacy = ROOT.parent / '.cache/huggingface/hub'
    return legacy if (legacy / 'models--openai--whisper-base/snapshots').exists() else local
