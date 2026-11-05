"""Isolated local TTS worker; exits before AVTR-1 starts to release GPU memory."""
import json
import sys
from pathlib import Path

import soundfile as sf
import torch
from omnivoice import OmniVoice
from windows_paths import voice_model

job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
model = OmniVoice.from_pretrained(
    str(voice_model()),
    device_map="cuda:0", dtype=torch.float16,
)
kwargs = {"text": job["text"], "language": "Portuguese", "num_step": 16}
if job.get("reference"):
    kwargs.update(ref_audio=job["reference"], ref_text=job["reference_text"])
audio = model.generate(**kwargs)
sf.write(job["output"], audio[0], model.sampling_rate)
print("Audio saved:", job["output"])
