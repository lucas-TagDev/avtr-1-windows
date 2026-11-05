@echo off
call "%~dp0ambiente-windows.cmd"
"%~dp0.venv-streamer\Scripts\python.exe" scripts\run_live_local.py
pause
