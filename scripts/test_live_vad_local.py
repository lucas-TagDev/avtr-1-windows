import asyncio
from types import SimpleNamespace
from avaturn_live_streamer.conversation_engines.gemini_local import GeminiLocalEngine
from avaturn_live_streamer.event_bus import EventBus
from avaturn_live_streamer.events import UserSpeechReceived,Shutdown
from avaturn_live_streamer.speech.speech_buffer import SpeechBuffer
import numpy as np
class Probe(GeminiLocalEngine):
 async def respond(self,bus,pcm):
  await received.put(pcm)
async def main():
 global received
 received=asyncio.Queue();bus=EventBus();engine=Probe(SimpleNamespace())
 worker=asyncio.create_task(engine.run(bus.clone(),None));bus.ready()
 import wave
 from pathlib import Path
 with wave.open(str(Path(__file__).resolve().parents[1]/'artifacts/conversations/af1d0a661dc6466c9ce831d33a434061/voice.wav'),'rb') as wav:
  speech=wav.readframes(wav.getnframes())
 pcm=b'\0'*24000+speech+b'\0'*96000
 for offset in range(0,len(pcm),960):
  await bus.publish(UserSpeechReceived(buffer=SpeechBuffer.from_bytes(pcm[offset:offset+960],24000)))
 detected=await asyncio.wait_for(received.get(),2)
 assert len(detected)>=len(speech),len(detected)
 await bus.publish(Shutdown());await asyncio.wait_for(worker,2)
 print('Silero microphone-to-response dispatch and shutdown OK')
asyncio.run(main())
