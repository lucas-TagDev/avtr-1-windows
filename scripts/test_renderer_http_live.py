import httpx,time
c=httpx.Client(timeout=10)
state=None;elapsed=[]
for i in range(8):
 files={name:('audio.pcm',b'\0'*(6400 if 'current' in name else 6560)) for name in ['current_chunk','future_chunk','current_chunk_listen','future_chunk_listen']}
 if state:files['state']=('state.safetensors',state)
 t=time.perf_counter()
 r=c.post('http://127.0.0.1:8000/process-audio-v3',params={'avatar_id':'maria','bg_id':'plain_white','pixel_format':'yuv_i420'},files=files)
 r.raise_for_status();sec=time.perf_counter()-t
 n=int(r.headers['X-State-Length-Bytes']);state=r.content[:n]
 frames=(len(r.content)-n)//int(r.headers['X-Frame-Length-Bytes'])
 assert frames==5,(frames,len(r.content),r.headers)
 print('HTTP STREAM',i,'frames',frames,'ms',round(sec*1000,1),flush=True)
 if i>1:elapsed.append(sec)
print('HTTP renderer FPS:',5/(sum(elapsed)/len(elapsed)),flush=True)
