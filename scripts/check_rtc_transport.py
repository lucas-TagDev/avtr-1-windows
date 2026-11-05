import asyncio
from aiortc import RTCPeerConnection, RTCConfiguration, AudioStreamTrack
from avaturn_live_streamer.localrtc.peer import LocalRTC
async def main():
 a=RTCPeerConnection(RTCConfiguration(iceServers=[]));b=RTCPeerConnection(RTCConfiguration(iceServers=[]));p=LocalRTC(b)
 a.addTrack(AudioStreamTrack());a.addTransceiver('video',direction='recvonly')
 try:
  await a.setLocalDescription(await a.createOffer());await b.setRemoteDescription(a.localDescription)
  await b.setLocalDescription(await b.createAnswer());await a.setRemoteDescription(b.localDescription)
  for i in range(8):
   await asyncio.sleep(1);print(i,a.connectionState,b.connectionState,flush=True)
  assert a.connectionState=='connected' and b.connectionState=='connected'
 finally:await a.close();await b.close()
asyncio.run(main())
