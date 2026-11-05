"""Install in the directory containing this project's launcher, without relocation."""
import os
from pathlib import Path
import subprocess
import sys
from windows_prerequisites import check

ROOT = Path(__file__).resolve().parents[1]

def installation_environment(root):
    root = Path(root).resolve()
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               HF_HOME=str(root / '.cache/huggingface'),
               PIP_CACHE_DIR=str(root / '.cache/pip'),
               UV_CACHE_DIR=str(root / '.cache/uv'),
               AVTR1_LOCAL_STORAGE=str(root / 'artifacts'))
    temporary = root / '.cache/tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    env['TEMP'] = env['TMP'] = str(temporary)
    return env

def main():
    if os.name != 'nt' or sys.version_info[:2] != (3,12):
        raise SystemExit('Instale Python 3.12 para Windows com o Python Launcher.')
    if len(sys.argv) > 1:
        raise SystemExit('Coloque o projeto na pasta desejada e execute INSTALAR-WINDOWS.cmd nela. Nao ha selecao de destino.')
    if not check(ROOT):
        raise SystemExit('Corrija os itens FALTA e execute novamente. Nenhuma dependencia foi instalada.')
    print('Instalando nesta pasta:', ROOT, flush=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/install_windows.py')], cwd=ROOT,
                   env=installation_environment(ROOT), check=True)
    print('Concluido. Nesta mesma pasta, faca login no Hugging Face e execute PREPARAR-MODELOS.cmd.', flush=True)

if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        print('Falha na instalacao:', error, file=sys.stderr)
        raise SystemExit(1)
