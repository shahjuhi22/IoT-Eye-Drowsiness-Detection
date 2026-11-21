@echo off
setlocal
cd /d "%~dp0"
title Install ESP32 CP2102 Driver

powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install_driver.ps1"

echo.
echo ==============================================================================
echo If you saw the Windows UAC prompt and clicked YES, the driver is installed!
echo If your ESP32 COM port is not visible yet, simply UNPLUG and RE-PLUG the USB cable.
echo ==============================================================================
echo.
pause
