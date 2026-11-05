"""Install official Silero ONNX assets without adding PyTorch to the streamer."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

VERSION = "6.2.3"
target = Path(__file__).resolve().parents[1] / "artifacts/silero-vad"
with urllib.request.urlopen(f"https://pypi.org/pypi/silero-vad/{VERSION}/json", timeout=60) as response:
    release = json.load(response)
wheel = next(item for item in release["urls"] if item["packagetype"] == "bdist_wheel")
with urllib.request.urlopen(wheel["url"], timeout=120) as response:
    data = response.read()
if hashlib.sha256(data).hexdigest() != wheel["digests"]["sha256"]:
    raise RuntimeError("Silero wheel checksum mismatch")
target.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    assets = {"silero_vad/data/silero_vad.onnx": "silero_vad.onnx",
              f"silero_vad-{VERSION}.dist-info/licenses/LICENSE": "LICENSE"}
    for source, name in assets.items():
        pending = target / (name + ".tmp")
        pending.write_bytes(archive.read(source))
        pending.replace(target / name)
(target / "VERSION").write_text(f"silero-vad {VERSION}; official PyPI wheel; snakers4/silero-vad")
print("Silero VAD installed:", target)
