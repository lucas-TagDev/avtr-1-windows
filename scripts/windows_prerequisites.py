"""Read-only prerequisite diagnostics, before downloading/installing dependencies."""
import ctypes
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=20)
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)

def check(root=ROOT):
    checks=[]
    def add(name, ok, detail, required=True):
        checks.append((name, bool(ok), detail, required))
    add('Windows 64 bits', os.name=='nt' and platform.machine().lower() in ('amd64','x86_64') and ctypes.sizeof(ctypes.c_void_p)==8, platform.platform())
    add('Python 3.12', sys.version_info[:2]==(3,12), sys.version.split()[0]+' - '+sys.executable)
    ok, text=command(['git','--version'])
    add('Git',ok,text if ok else 'Instale Git para Windows: https://git-scm.com/download/win')
    smi=shutil.which('nvidia-smi')
    if not smi:
        candidate=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/nvidia-smi.exe'
        smi=str(candidate) if candidate.is_file() else None
    ok, text=command([smi,'--query-gpu=name,memory.total,driver_version','--format=csv,noheader']) if smi else (False,'')
    add('GPU NVIDIA e driver',ok,text if ok else 'Instale/atualize o driver NVIDIA; GPU CUDA e necessaria.')
    supported, header=command([smi]) if smi else (False,'')
    match=re.search(r'CUDA(?: UMD)? Version:\s*(\d+)\.(\d+)',header)
    compatible=bool(match and tuple(map(int,match.groups())) >= (12,8))
    add('Driver com suporte CUDA 12.8+',supported and compatible, 'CUDA '+'.'.join(match.groups()) if match else 'Nao foi possivel confirmar suporte. Atualize o driver NVIDIA.')
    vc=False
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
                vc=winreg.QueryValueEx(key,'Installed')[0]==1
        except OSError:
            pass
    add('Visual C++ Redistributable x64',vc,'Instalado' if vc else 'Instale: https://aka.ms/vs/17/release/vc_redist.x64.exe')
    try:
        with tempfile.TemporaryFile(dir=root):
            pass
        writable=True
    except OSError:
        writable=False
    add('Permissao de escrita na pasta',writable,str(root))
    try:
        free=shutil.disk_usage(root).free/(1024**3)
        add('Espaco livre (aviso)',free>=50,f'{free:.1f} GB livres. Reserve espaco para modelos e tres ambientes; 50 GB e uma margem de planejamento, nao um requisito medido.',False)
    except OSError:
        add('Espaco livre (aviso)',False,'Nao foi possivel consultar.',False)
    for name,ok,detail,required in checks:
        print(f"[{'OK' if ok else 'FALTA' if required else 'AVISO'}] {name}: {detail}",flush=True)
    return all(ok for _,ok,_,required in checks if required)

if __name__=='__main__':
    raise SystemExit(0 if check() else 1)
