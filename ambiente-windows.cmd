@echo off
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"
set "AVTR1_LOCAL_STORAGE=%~dp0artifacts"
set "HF_HOME=%~dp0.cache\huggingface"
set "PATH=%~dp0.venv\Lib\site-packages\torch\lib;%~dp0.venv\Lib\site-packages\tensorrt_libs;%~dp0.venv\Lib\site-packages\nvidia\cuda_runtime\bin;%PATH%"

set "PIP_CACHE_DIR=%~dp0.cache\pip"
set "UV_CACHE_DIR=%~dp0.cache\uv"
if not exist "%~dp0.cache\tmp" mkdir "%~dp0.cache\tmp"
set "TEMP=%~dp0.cache\tmp"
set "TMP=%~dp0.cache\tmp"
