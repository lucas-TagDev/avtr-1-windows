from pathlib import Path
import httpx,io
from PIL import Image
c=httpx.Client(base_url='http://localhost:7860',timeout=90)
p=Path('artifacts/main/avatars_artifacts/reference_frames/maria.png')
r=c.post('/custom-avatars',data={'name':'Exemplo de template (Maria)'},files={'photo':('maria.png',p.read_bytes(),'image/png')})
print('UPLOAD',r.status_code,r.text);r.raise_for_status();avatar=r.json()['id']
Path('custom-avatar-test-id.tmp').write_text(avatar)
a=c.get('/avatars').json();assert avatar in a['avatars'];assert a['avatar_names'][avatar]=='Exemplo de template (Maria)'
print('LIBRARY',len(a['custom_avatars']),'template; PREVIEW',c.get('/avatar-preview/'+avatar).status_code)
b=io.BytesIO();Image.new('RGB',(512,512),(255,255,255)).save(b,'PNG')
r=c.post('/custom-avatars',data={'name':'Sem rosto'},files={'photo':('blank.png',b.getvalue(),'image/png')})
print('NO FACE',r.status_code,r.text);assert r.status_code==400
assert len(c.get('/avatars').json()['custom_avatars'])==len(a['custom_avatars'])
# Exercise the new avatar through the actual renderer with a live chunk.
c=httpx.Client(base_url='http://localhost:8000',timeout=30)
files={k:('audio.pcm',b'\0'*(6400 if 'current' in k else 6560)) for k in ['current_chunk','future_chunk','current_chunk_listen','future_chunk_listen']}
r=c.post('/process-audio-v3',params={'avatar_id':avatar,'bg_id':'plain_white','pixel_format':'yuv_i420'},files=files)
r.raise_for_status();n=int(r.headers['X-State-Length-Bytes']);assert len(r.content)-n==5*int(r.headers['X-Frame-Length-Bytes'])
print('PERSONALIZED AVATAR RENDERED',r.headers['X-Num-Frames'],'frames')
