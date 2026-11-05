"""Download OmniVoice and Whisper into the layout used by the launcher."""
from pathlib import Path
from huggingface_hub import snapshot_download
root = Path(__file__).resolve().parents[1]
snapshot_download("k2-fsa/OmniVoice", local_dir=root / "OmniVoice/models/OmniVoice")
snapshot_download("openai/whisper-base", cache_dir=root / ".cache/huggingface/hub")
print("Modelos de voz e transcricao baixados.")
