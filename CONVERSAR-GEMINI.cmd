@echo off
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%~dp0..\.cache\huggingface"
echo Abra http://localhost:7862 no navegador.
"%~dp0..\OmniVoice\.venv\Scripts\python.exe" scripts\gemini_local_app.py
pause
