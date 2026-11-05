@echo off
call "%~dp0ambiente-windows.cmd"
"%~dp0.venv\Scripts\python.exe" scripts\download_windows.py
if errorlevel 1 goto falha
for %%S in (prepare_warp_windows.py build_avtr1_engines.py build_hubert_engine.py prepare_warp_cuda.py build_warp_cuda_trt.py prepare_warp_b5.py build_warp_b5.py) do (
  "%~dp0.venv\Scripts\python.exe" scripts\%%S
  if errorlevel 1 goto falha
)
"%~dp0.venv\Scripts\python.exe" scripts\build_renderer_engines.py decoder modnet stitch
if errorlevel 1 goto falha
"%~dp0.venv-streamer\Scripts\python.exe" scripts\download_silero_vad.py
if errorlevel 1 goto falha
"%~dp0..\OmniVoice\.venv\Scripts\python.exe" scripts\download_voice_models.py
if errorlevel 1 goto falha
echo Modelos preparados. Abra CONVERSAR-AO-VIVO.cmd.
goto fim
:falha
echo Falha ao preparar modelos. Verifique a mensagem acima. Consulte WINDOWS.md.
:fim
pause
