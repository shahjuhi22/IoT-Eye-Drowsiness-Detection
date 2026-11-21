@echo off
setlocal

:: Set title
title IoT Eye Monitoring and Drowsiness Detection System

:: Select Python interpreter: Use .venv if present, otherwise Python 3.11 or system python
set "RUN_PY=python"
if exist ".venv\Scripts\python.exe" (
    set "RUN_PY=.venv\Scripts\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "RUN_PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

:MENU
cls
echo ==============================================================================
echo   IoT SMART EYE MONITORING AND DROWSINESS DETECTION SYSTEM
echo ==============================================================================
echo   Interpreter: %RUN_PY%
echo ==============================================================================
echo.
echo   [0] Flash Firmware to ESP32 (One-Click Auto-Upload)
echo   [D] Install CP2102 Driver (If ESP32 COM Port Not Recognized)
echo   [1] Start Desktop Eye and Drowsiness Monitor (OpenCV Video + HUD)
echo   [2] Start Web Dashboard (Streamlit Control Panel and Live Charts)
echo   [3] Start Desktop Monitor in Pure Simulation Mode (No ESP32 Needed)
echo   [4] Run ESP32 Serial Protocol and Hardware Diagnostics
echo   [5] Run Camera and Computer Vision Diagnostics
echo   [6] Run Automated Unit Tests (pytest / unittest)
echo   [7] Open ESP32 Firmware in Arduino IDE
echo   [8] Run Complete Automated Setup (setup.bat)
echo   [9] Exit
echo.
echo ==============================================================================
set /p CHOICE="Choose an option [0-9 or D]: "

if /i "%CHOICE%"=="0" goto UPLOAD_FIRMWARE
if /i "%CHOICE%"=="D" goto INSTALL_DRIVER
if "%CHOICE%"=="1" goto RUN_MAIN
if "%CHOICE%"=="2" goto RUN_DASHBOARD
if "%CHOICE%"=="3" goto RUN_SIMULATION
if "%CHOICE%"=="4" goto RUN_SERIAL_TEST
if "%CHOICE%"=="5" goto RUN_CAMERA_TEST
if "%CHOICE%"=="6" goto RUN_UNIT_TESTS
if "%CHOICE%"=="7" goto OPEN_ARDUINO
if "%CHOICE%"=="8" goto RUN_SETUP
if "%CHOICE%"=="9" goto EXIT_PROG

echo.
echo [!] Invalid selection. Please choose an option from the menu.
timeout /t 2 >nul
goto MENU

:UPLOAD_FIRMWARE
cls
echo [INFO] Running ESP32 Automated Firmware Uploader...
call upload_firmware.bat
goto MENU

:INSTALL_DRIVER
cls
echo [INFO] Launching CP2102 Driver Installer...
call INSTALL_DRIVER.bat
goto MENU

:RUN_MAIN
cls
echo [STARTING] Desktop Eye and Drowsiness Monitor...
%RUN_PY% main.py
pause
goto MENU

:RUN_DASHBOARD
cls
echo [STARTING] Streamlit Web Dashboard...
if exist ".venv\Scripts\streamlit.exe" (
    .venv\Scripts\streamlit.exe run dashboard\dashboard.py
) else (
    %RUN_PY% -m streamlit run dashboard\dashboard.py
)
pause
goto MENU

:RUN_SIMULATION
cls
echo [STARTING] Desktop Monitor in Simulation Mode...
%RUN_PY% main.py --simulate
pause
goto MENU

:RUN_SERIAL_TEST
cls
echo [RUNNING] Serial and ESP32 Diagnostics...
%RUN_PY% test_serial.py
pause
goto MENU

:RUN_CAMERA_TEST
cls
echo [RUNNING] Camera and Vision Diagnostics...
%RUN_PY% test_camera.py
pause
goto MENU

:RUN_UNIT_TESTS
cls
echo [RUNNING] Automated Unit Tests...
%RUN_PY% -m unittest discover tests -v
pause
goto MENU

:OPEN_ARDUINO
cls
echo [INFO] Opening Arduino IDE with ESP32 Firmware...
if exist "%LOCALAPPDATA%\Programs\Arduino IDE\Arduino IDE.exe" (
    start "" "%LOCALAPPDATA%\Programs\Arduino IDE\Arduino IDE.exe" "esp32_firmware\eye_monitor_esp32\eye_monitor_esp32.ino"
) else (
    start esp32_firmware\eye_monitor_esp32\eye_monitor_esp32.ino
)
echo [DONE] Firmware opened in Arduino IDE.
pause
goto MENU

:RUN_SETUP
cls
call setup.bat
goto MENU

:EXIT_PROG
echo.
echo Goodbye!
timeout /t 1 >nul
exit /b 0
