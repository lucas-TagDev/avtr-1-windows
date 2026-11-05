"""Interactive destination selector and clean source deployment for Windows."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1]

def deploy(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    target = destination / 'avtr-1-windows'
    if target == source:
        return target
    if source in target.parents:
        raise ValueError('Escolha uma pasta fora da pasta de origem do instalador.')
    if target.exists() and any(target.iterdir()) and not (target / 'scripts/windows_installer.py').is_file():
        raise ValueError('A pasta avtr-1-windows ja existe e nao pertence a este instalador. Escolha outro destino.')
    manifest = json.loads((source / 'windows-install-files.json').read_text(encoding='utf-8'))
    for relative in manifest:
        path = Path(relative)
        original = (source / path).resolve()
        output = (target / path).resolve()
        if path.is_absolute() or source not in original.parents or target not in output.parents:
            raise ValueError('Caminho invalido no manifesto da instalacao.')
        if not original.is_file():
            raise ValueError('Arquivo ausente no pacote: ' + relative)
    target.mkdir(parents=True, exist_ok=True)
    for relative in manifest:
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, output)
    return target

def main():
    parser = argparse.ArgumentParser(description='Instalar AVTR-1 Windows no disco escolhido.')
    parser.add_argument('--destination', type=Path, help='Pasta que recebera avtr-1-windows e OmniVoice')
    args = parser.parse_args()
    if os.name != 'nt' or sys.version_info[:2] != (3,12):
        raise SystemExit('Instale Python 3.12 para Windows com o Python Launcher.')
    destination = args.destination
    if destination is None:
        import tkinter as tk
        from tkinter import filedialog
        window = tk.Tk()
        window.withdraw()
        window.attributes('-topmost', True)
        chosen = filedialog.askdirectory(parent=window, title='Escolha a pasta e o disco para instalar o AVTR-1', mustexist=True)
        window.destroy()
        if not chosen:
            print('Instalacao cancelada. Nenhum arquivo foi instalado.')
            return
        destination = Path(chosen)
    target = deploy(SOURCE, destination)
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', HF_HOME=str(target / '.cache/huggingface'), PIP_CACHE_DIR=str(target / '.cache/pip'))
    temporary = target / '.cache/tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    env['TEMP'] = env['TMP'] = str(temporary)
    print('Instalando em:', target, flush=True)
    subprocess.run([sys.executable, str(target / 'scripts/install_windows.py')], cwd=target, env=env, check=True)
    print('Instalacao concluida. Proximos passos: login no Hugging Face e PREPARAR-MODELOS.cmd em', target, flush=True)
    os.startfile(str(target))

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('Falha na instalacao:', error, file=sys.stderr)
        raise SystemExit(1)
