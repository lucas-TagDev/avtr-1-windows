"""Gemini audio understanding and local OmniVoice feeding the original streaming bus."""
import asyncio
import base64
import io
import uuid
import wave
import base64
import httpx
from avaturn_live_streamer.events import (
    UserSpeechReceived, Shutdown, DiscardAvatarSpeechBuffer,
    SegmentGenerationStarted, SegmentChunkGenerated, SegmentGenerationCompleted,
)
from avaturn_live_streamer.management.types import SegmentId
from avaturn_live_streamer.speech.speech_buffer import SpeechBuffer
from avaturn_live_streamer.conversation_status import update, message
from avaturn_live_streamer.speech.silero_turns import SileroTurnDetector


class GeminiLocalEngine:
    def __init__(self, options):
        self.options = options
        self.history = []
        self.response = None

    async def respond(self, bus, pcm):
        segment = None
        try:
            provider_name = "Gemini" if self.options.text_provider == "gemini" else (self.options.text_endpoint or "LLM OpenAI-compatible")
            update("thinking", f"{provider_name} está processando sua fala…")
            output = io.BytesIO()
            with wave.open(output, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(24000)
                wav.writeframes(pcm)
            async with httpx.AsyncClient(timeout=45) as transcriber:
                if self.options.transcription_provider == "openai":
                    tr = await transcriber.post("https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.options.transcription_api_key}"},
                        files={"file": ("speech.wav", output.getvalue(), "audio/wav")},
                        data={"model": "whisper-1"})
                else:
                    tr = await transcriber.post("http://127.0.0.1:7863/transcribe",
                        json={"pcm": base64.b64encode(pcm).decode()})
                tr.raise_for_status()
                spoken_text = tr.json().get("text", "").strip() or "[fala do microfone]"
            message("user", spoken_text)
            user = {"role": "user", "parts": [{"inlineData": {
                "mimeType": "audio/wav", "data": base64.b64encode(output.getvalue()).decode()}}]}
            async with httpx.AsyncClient(timeout=90) as client:
                if self.options.text_provider == "openai-compatible":
                    endpoint = self.options.text_endpoint.rstrip("/") + "/chat/completions"
                    r = await client.post(endpoint, headers={"Authorization": f"Bearer {self.options.text_api_key}"},
                        json={"model": self.options.model, "messages":[{"role":"system","content":self.options.prompt},{"role":"user","content":spoken_text}], "stream":False})
                else:
                    r = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{self.options.model}:generateContent",
                        headers={"x-goog-api-key": self.options.api_key}, json={"contents": self.history[-8:] + [user], "systemInstruction": {"parts": [{"text": self.options.prompt}]}, "generationConfig": {"maxOutputTokens": 2048}})
                if r.is_error:
                    raise RuntimeError("Gemini: " + r.json().get("error", {}).get("message", str(r.status_code)))
                if self.options.text_provider == "openai-compatible":
                    text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    candidates = r.json().get("candidates", [])
                    text = "".join(p.get("text", "") for p in (candidates[0].get("content", {}).get("parts", []) if candidates else []) if not p.get("thought"))
                if not text.strip():
                    raise RuntimeError("Gemini retornou uma resposta vazia")
                message("avatar", text)
                update("synthesizing")
                r = await client.post("http://127.0.0.1:7863/speak",
                                      json={"text": text, "voice_id": self.options.voice_id})
                r.raise_for_status()
            self.history.extend([user, {"role": "model", "parts": [{"text": text}]}])
            self.history = self.history[-8:]
            segment = SegmentId("gemini-local-" + uuid.uuid4().hex)
            update("buffering")
            await bus.publish(SegmentGenerationStarted(segment_id=segment))
            for offset in range(0, len(r.content), 4800):
                await bus.publish(SegmentChunkGenerated(segment_id=segment,
                                  buffer=SpeechBuffer.from_bytes(r.content[offset:offset+4800], 24000)))
            await bus.publish(SegmentGenerationCompleted(segment_id=segment))
            segment = None
        except Exception as exc:
            update("error", str(exc).replace(self.options.api_key, "[chave]"))
            raise
        finally:
            if segment:
                await bus.publish(SegmentGenerationCompleted(segment_id=segment))

    async def run(self, bus, clocks):
        vad = SileroTurnDetector()
        async with bus.subscribe(UserSpeechReceived, Shutdown) as sub, asyncio.TaskGroup() as tg:
            bus.ready()
            update("listening")
            try:
                async for event in sub:
                    if isinstance(event, Shutdown):
                        return
                    pcm = event.buffer.resample(24000).to_bytes()
                    for turn in vad.feed(pcm):
                        if turn.kind == "start":
                            if self.response and not self.response.done():
                                self.response.cancel()
                            await bus.publish(DiscardAvatarSpeechBuffer())
                            update("hearing")
                        elif turn.kind == "end":
                            self.response = tg.create_task(self.respond(bus, turn.pcm))
                        elif turn.kind == "discard" and (self.response is None or self.response.done()):
                            update("listening")
            finally:
                if self.response:
                    self.response.cancel()
