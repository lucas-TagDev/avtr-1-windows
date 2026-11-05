"""Boundary regression tests plus real CPU inference on local synthetic speech."""
import sys
from pathlib import Path
import unittest
import wave
import numpy as np
import soxr
from avaturn_live_streamer.speech.silero_turns import SileroTurnDetector


class Probabilities:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self, audio):
        assert audio.shape == (512,)
        return next(self.values, 0.0)


def feed_all(detector, pcm, chunk_bytes=960):
    events = []
    for pos in range(0, len(pcm), chunk_bytes):
        events.extend(detector.feed(pcm[pos:pos+chunk_bytes]))
    return events


class Boundaries(unittest.TestCase):
    def test_silence_and_brief_noise_do_not_open_turn(self):
        detector = SileroTurnDetector(probability=Probabilities([0]*5+[.9]*2+[0]*40))
        self.assertEqual(feed_all(detector, b"\0"*768*2*60), [])

    def test_turn_preserves_preroll_and_waits_for_silence(self):
        detector = SileroTurnDetector(probability=Probabilities([0]*4+[.9]*8+[0]*40))
        pcm = np.full(768*60, 1234, dtype="<i2").tobytes()
        events = feed_all(detector, pcm)
        self.assertEqual([e.kind for e in events], ["start", "end"])
        self.assertEqual(events[1].pcm, pcm[:len(events[1].pcm)])
        self.assertGreaterEqual(len(events[1].pcm), (8+21)*768*2)

    def test_short_pause_does_not_split_a_turn(self):
        detector = SileroTurnDetector(probability=Probabilities([.9]*8+[0]*10+[.9]*8+[0]*40))
        events = feed_all(detector, b"\0"*768*2*80, chunk_bytes=202)
        self.assertEqual([e.kind for e in events], ["start", "end"])

    def test_long_speech_is_bounded(self):
        detector = SileroTurnDetector(probability=Probabilities([.9]*100+[0]*40), max_turn_seconds=1)
        events = feed_all(detector, b"\0"*768*2*150)
        ends = [e for e in events if e.kind == "end"]
        self.assertGreaterEqual(len(ends), 3)
        self.assertTrue(all(len(e.pcm) <= 32*768*2 for e in ends))

    def test_real_silero_detects_speech_and_ignores_silence(self):
        root = Path(__file__).resolve().parents[1]
        reference = root / "artifacts/conversations/af1d0a661dc6466c9ce831d33a434061/voice.wav"
        with wave.open(str(reference), "rb") as audio:
            samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype="<i2")
            rate = audio.getframerate()
        if rate != 24000:
            samples = soxr.resample(samples, rate, 24000).astype("<i2")
        pcm = b"\0"*24000 + samples.tobytes() + b"\0"*96000
        detector = SileroTurnDetector()
        events = feed_all(detector, pcm)
        self.assertIn("start", [e.kind for e in events])
        self.assertIn("end", [e.kind for e in events])
        silence = SileroTurnDetector()
        self.assertEqual(feed_all(silence, b"\0"*96000), [])
        print("Real Silero speech boundaries:", [e.kind for e in events])


if __name__ == "__main__":
    unittest.main(verbosity=2)
