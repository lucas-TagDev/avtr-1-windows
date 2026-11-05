@echo off
call "%~dp0ambiente-windows.cmd"
"%~dp0.venv\Scripts\python.exe" scripts\generate_offline.py --speech example\speaker_1.ogg --avatar maria --bg plain_white --out resultado.mp4 %*
pause
