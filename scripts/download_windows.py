import json, urllib.request, concurrent.futures, shutil, os
from huggingface_hub import get_token
from pathlib import Path
base=Path(__file__).resolve().parents[1]/'artifacts'/'main'
def get(url):
    with urllib.request.urlopen(url, timeout=90) as r: return json.load(r)
files=[]
for x in get('https://huggingface.co/api/models/avaturn-live/avtr-1/tree/main?recursive=true'):
    if x['type']=='file' and not x['path'].endswith(('.engine','.so')) and x['path'].startswith(('avatars_artifacts/','build_artifacts/','renderer_runtime_artifacts/')):
        files.append(('avaturn-live/avtr-1',x['path'],x['path'],x['size']))
names=['appearance_extractor','motion_extractor','landmark106','landmark203','insightface_det','blaze_face','face_mesh','decoder','warp_network','warp_network_ori','stitch_network']
for x in get('https://huggingface.co/api/models/digital-avatar/ditto-talkinghead/tree/main/ditto_onnx'):
    name=Path(x['path']).stem
    if name in names:
        folder='renderer_runtime_artifacts' if name in names[:7] else 'build_artifacts'
        files.append(('digital-avatar/ditto-talkinghead',x['path'],f'{folder}/{name}.onnx',x['size']))
def download(item):
    repo,src,dst,size=item
    out=base/dst
    if out.exists() and out.stat().st_size==size: return
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(out.suffix+'.partial')
    token=get_token() or ''
    req=urllib.request.Request(f'https://huggingface.co/{repo}/resolve/main/{src}',headers={'Authorization':f'Bearer {token}'})
    with urllib.request.urlopen(req,timeout=120) as response, tmp.open('wb') as target:
        shutil.copyfileobj(response,target)
    if tmp.stat().st_size!=size: raise RuntimeError(f'Invalid size {dst}')
    tmp.replace(out)
    print('OK',dst,flush=True)
print('Download total GB:',sum(x[3] for x in files)/1e9,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(download,files))
print('DOWNLOAD COMPLETE',flush=True)
