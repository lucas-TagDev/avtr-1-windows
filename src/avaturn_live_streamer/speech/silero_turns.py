"""Streaming Silero VAD (official 6.2.3 ONNX) on CPU, with 24 kHz turn audio.

ONNX recurrent state/context follow snakers4/silero-vad's MIT OnnxWrapper.
The original PCM is retained for Gemini; resampling is only for classification.
"""
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
import onnxruntime as ort
import soxr


@dataclass(frozen=True)
class VadEvent:
    kind: str
    pcm: bytes = b""


class SileroProbability:
    def __init__(self, model_path: Path):
        options = ort.SessionOptions()
        options.inter_op_num_threads = options.intra_op_num_threads = 1
        self.session = ort.InferenceSession(str(model_path), sess_options=options,
                                            providers=["CPUExecutionProvider"])
        self.state = np.zeros((2, 1, 128), dtype=np.float32)
        self.context = np.zeros((1, 64), dtype=np.float32)

    def __call__(self, frame):
        audio = np.concatenate((self.context, frame.reshape(1, 512)), axis=1)
        probability, self.state = self.session.run(None, {
            "input": audio, "state": self.state, "sr": np.array(16000, dtype=np.int64),
        })
        self.context = audio[:, -64:].copy()
        return float(probability.reshape(-1)[0])


class SileroTurnDetector:
    """Accept arbitrary 24 kHz mono s16 chunks; emit start/end/discard events."""
    frame_seconds = 512 / 16000
    frame_bytes = 768 * 2

    def __init__(self, probability=None, threshold=0.5, silence_ms=650,
                 preroll_ms=200, minimum_speech_ms=160, max_turn_seconds=25):
        if not 0.15 < threshold <= 1 or silence_ms < 32 or max_turn_seconds < 1:
            raise ValueError("Invalid Silero VAD configuration")
        path = Path(__file__).resolve().parents[3] / "artifacts/silero-vad/silero_vad.onnx"
        self.probability = probability if probability is not None else SileroProbability(path)
        self.threshold = threshold
        self.end_threshold = threshold - 0.15
        self.silence_frames = math.ceil(silence_ms / 32)
        self.minimum_frames = math.ceil(minimum_speech_ms / 32)
        self.max_frames = math.ceil(max_turn_seconds / self.frame_seconds)
        self.preroll = deque(maxlen=max(3, math.ceil(preroll_ms / 32)))
        self.resampler = soxr.ResampleStream(24000, 16000, 1, dtype="float32", quality="HQ")
        self.pending_audio = bytearray()
        self.pending_vad = np.empty(0, dtype=np.float32)
        self.frames = []
        self.active = False
        self.candidate = self.quiet = self.voiced = 0
        self.last_probability = 0.0

    def feed(self, pcm: bytes) -> list[VadEvent]:
        if len(pcm) % 2:
            raise ValueError("PCM must contain complete int16 samples")
        if not pcm:
            return []
        self.pending_audio.extend(pcm)
        samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        resampled = self.resampler.resample_chunk(samples)
        self.pending_vad = np.concatenate((self.pending_vad, resampled))
        events = []
        while len(self.pending_vad) >= 512 and len(self.pending_audio) >= self.frame_bytes:
            window = self.pending_vad[:512]
            self.pending_vad = self.pending_vad[512:]
            original = bytes(self.pending_audio[:self.frame_bytes])
            del self.pending_audio[:self.frame_bytes]
            p = self.probability(window)
            self.last_probability = p
            if not self.active:
                self.preroll.append(original)
                self.candidate = self.candidate + 1 if p >= self.threshold else 0
                if self.candidate >= 3:
                    self.active = True
                    self.frames = list(self.preroll)
                    self.preroll.clear()
                    self.voiced = self.candidate
                    self.quiet = 0
                    events.append(VadEvent("start"))
                continue
            self.frames.append(original)
            if p >= self.threshold:
                self.voiced += 1
                self.quiet = 0
            elif p < self.end_threshold:
                self.quiet += 1
            else:
                self.quiet = 0
            if self.quiet >= self.silence_frames or len(self.frames) >= self.max_frames:
                if self.voiced >= self.minimum_frames:
                    events.append(VadEvent("end", b"".join(self.frames)))
                else:
                    events.append(VadEvent("discard"))
                self.active = False
                self.frames = []
                self.candidate = self.quiet = self.voiced = 0
        return events
