import os,asyncio,time
from pathlib import Path
os.environ['RENDERERS__RENDERERS__AVTRN_1__MODE']='single'
os.environ['RENDERERS__RENDERERS__AVTRN_1__LB_OR_INSTANCE_URL']='http://127.0.0.1:8000'
from aiortc import RTCPeerConnection,RTCConfiguration,RTCBundlePolicy,AudioStreamTrack
from avaturn_live_streamer.localrtc.peer import LocalRTC
from avaturn_live_streamer.local_stream_cli import _run_session
from avaturn_live_streamer.conversation_engines.configs import GeminiLocalConversationEngineConfig
from avaturn_live_streamer.events import Shutdown
async def local_idle(bus,clocks):
 async with bus.subscribe(Shutdown) as sub:
  bus.ready();await sub.get_next()
async def main():
 cfg=RTCConfiguration(iceServers=[],bundlePolicy=RTCBundlePolicy.MAX_BUNDLE)
 client=RTCPeerConnection(cfg);server=RTCPeerConnection(cfg);peer=LocalRTC(server);received=[];video_ready=asyncio.Future();audio_task=None;session=None
 client.addTrack(AudioStreamTrack());client.addTransceiver('video',direction='recvonly')
 @client.on('track')
 def track(t):
  if t.kind=='video':video_ready.set_result(t)
  else:
   async def consume():
    while True:await t.recv()
   nonlocal audio_task
   audio_task=asyncio.create_task(consume())
 try:
  await client.setLocalDescription(await client.createOffer());await server.setRemoteDescription(client.localDescription)
  await server.setLocalDescription(await server.createAnswer());await client.setRemoteDescription(server.localDescription)
  session=asyncio.create_task(_run_session(built_engine=(GeminiLocalConversationEngineConfig(),local_idle),peer=peer,avatar='maria',background='plain_white',idle_timeout=30,max_duration=30))
  video=await asyncio.wait_for(video_ready,10)
  for i in range(65):
   frame=await asyncio.wait_for(video.recv(),20);received.append(time.perf_counter())
   if i==30:
    a=frame.to_ndarray(format='rgb24');Path('avatar-live-validated.ppm').write_bytes(f'P6\n{a.shape[1]} {a.shape[0]}\n255\n'.encode()+a.tobytes())
  print('REAL WEBRTC FRAMES:',len(received),'FPS:',(len(received)-1)/(received[-1]-received[0]),'CONNECTED:',client.connectionState,flush=True)
 finally:
  await client.close();await server.close()
  if audio_task:audio_task.cancel()
  if session:session.cancel();await asyncio.gather(session,return_exceptions=True)
asyncio.run(main())
