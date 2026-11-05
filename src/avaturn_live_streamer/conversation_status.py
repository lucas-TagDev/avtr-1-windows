"""Progress for the single local conversation, without credentials or transcript content."""
import time

LABELS = {
    "connecting": "Conectando áudio e vídeo…",
    "listening": "Ouvindo — pode falar",
    "hearing": "Ouvindo sua mensagem…",
    "thinking": "Pensando — o provedor de texto está processando sua fala…",
    "synthesizing": "Gerando áudio localmente com OmniVoice…",
    "buffering": "Preparando a fala e a animação do avatar…",
    "speaking": "Falando…",
    "ended": "Conversa encerrada",
    "error": "Falha no processamento",
}
_state = {"phase": "ended", "since": time.monotonic(), "detail": "", "transcript": []}
_last_audio = 0.0


def update(phase, detail=""):
    if phase != _state["phase"] or detail != _state["detail"]:
        _state.update(phase=phase, since=time.monotonic(), detail=detail)


def snapshot():
    return {"phase": _state["phase"], "label": LABELS[_state["phase"]],
            "detail": _state["detail"], "elapsed": round(time.monotonic() - _state["since"], 1),
            "vad": "Silero VAD 6.2.3 (CPU)", "transcript": list(_state["transcript"])}


def message(role, text):
    if text:
        _state["transcript"].append({"role": role, "text": text, "time": time.time()})
        _state["transcript"] = _state["transcript"][-40:]


def playback(has_voice):
    global _last_audio
    now = time.monotonic()
    if _state["phase"] not in ("listening", "buffering", "speaking"):
        return
    if has_voice:
        _last_audio = now
        update("speaking")
    elif _state["phase"] == "speaking" and now - _last_audio > 0.8:
        update("listening")
