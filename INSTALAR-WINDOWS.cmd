@echo off
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3.12 "%~dp0scripts\windows_installer.py" %*
if errorlevel 1 echo Falha na instalacao. Instale Python 3.12, Git e consulte WINDOWS.md.
pause
