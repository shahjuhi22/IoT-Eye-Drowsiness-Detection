@echo off
setlocal
cd /d "%~dp0"
title Upload Firmware to ESP32

set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

%PY_CMD% upload_firmware.py
pause
