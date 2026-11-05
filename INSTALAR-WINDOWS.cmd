@echo off
call "%~dp0ambiente-windows.cmd"
py -3.12 scripts\install_windows.py
if errorlevel 1 echo Falha na instalacao. Veja a mensagem acima e consulte WINDOWS.md.
pause
