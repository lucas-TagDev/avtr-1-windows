@echo off
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo [FALTA] Python 3.12 ou Python Launcher.
  echo Instale Python 3.12 x64 com o Launcher: https://www.python.org/downloads/windows/
  echo Marque a opcao do Python Launcher no instalador.
  pause
  exit /b 1
)
py -3.12 "%~dp0scripts\windows_prerequisites.py" %*
if errorlevel 1 echo Verifique as mensagens acima e consulte WINDOWS.md.
pause
