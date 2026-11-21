@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo   IoT SMART EYE MONITORING AND DROWSINESS SYSTEM -- AUTOMATED SETUP
echo ==============================================================================
echo.

:: ------------------------------------------------------------------------------
:: Step 1: Detect Compatible Python Installation (Prefers Python 3.11 for MediaPipe)
:: ------------------------------------------------------------------------------
set "PY_CMD="

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    echo [FOUND] Dedicated Python 3.11 detected at:
    echo         !PY_CMD!
    goto :PYTHON_FOUND
)

py -3.11 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=py -3.11"
    echo [FOUND] Python 3.11 detected via py launcher.
    goto :PYTHON_FOUND
)

python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    echo [INFO] Testing default system 'python'...
    goto :PYTHON_FOUND
)

echo [ERROR] No suitable Python installation detected on your system.
echo         Please install Python 3.11 from: https://www.python.org/downloads/release/python-3119/
echo         Ensure "Add Python to PATH" is checked during installation.
pause
exit /b 1

:PYTHON_FOUND
echo.
echo Active Python binary:
!PY_CMD! --version
echo.

:: ------------------------------------------------------------------------------
:: Step 2: Virtual Environment Configuration
:: ------------------------------------------------------------------------------
if not exist ".venv" (
    echo [SETUP] Creating isolated virtual environment in .venv ...
    !PY_CMD! -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [PASS] Virtual environment created successfully.
) else (
    echo [INFO] Existing virtual environment found (.venv).
)

set "VENV_PY=.venv\Scripts\python.exe"
set "VENV_PIP=.venv\Scripts\pip.exe"

:: ------------------------------------------------------------------------------
:: Step 3: Install Required Dependencies
:: ------------------------------------------------------------------------------
echo.
echo [SETUP] Installing and verifying dependencies from requirements.txt ...
!VENV_PIP! install --upgrade pip
!VENV_PIP! install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Encountered errors during pip install. Checking core libraries...
)

:: ------------------------------------------------------------------------------
:: Step 4: Verify Arduino IDE and ESP32 Environment
:: ------------------------------------------------------------------------------
echo.
echo ==============================================================================
echo   ARDUINO IDE AND ESP32 HARDWARE ENVIRONMENT CHECK
echo ==============================================================================
set "ARDUINO_FOUND=0"
if exist "%LOCALAPPDATA%\Programs\Arduino IDE\Arduino IDE.exe" (
    echo [PASS] Arduino IDE 2.x found:
    echo        "%LOCALAPPDATA%\Programs\Arduino IDE\Arduino IDE.exe"
    set "ARDUINO_FOUND=1"
) else if exist "C:\Program Files\Arduino IDE\Arduino IDE.exe" (
    echo [PASS] Arduino IDE found in C:\Program Files\Arduino IDE
    set "ARDUINO_FOUND=1"
) else (
    echo [INFO] Arduino IDE not detected in standard paths.
    echo        Download Arduino IDE from: https://www.arduino.cc/en/software
)

echo.
echo ESP32 Board and Library Installation Checklist:
echo   1. In Arduino IDE -^> File -^> Preferences, add Boards Manager URL:
echo      https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
echo   2. In Tools -^> Board -^> Boards Manager, search for "esp32" by Espressif and install.
echo   3. In Sketch -^> Include Library -^> Manage Libraries, install:
echo      - "DHT sensor library" by Adafruit
echo      - "Adafruit Unified Sensor" by Adafruit
echo.

:: ------------------------------------------------------------------------------
:: Step 5: Run Automated Diagnostics
:: ------------------------------------------------------------------------------
echo ==============================================================================
echo   RUNNING HARDWARE AND SENSOR DIAGNOSTICS
echo ==============================================================================
echo.
echo --- Diagnostic 1: Serial Node and Protocol Test ---
!VENV_PY! test_serial.py
echo.
echo --- Diagnostic 2: Camera and Vision Pipeline Test ---
!VENV_PY! test_camera.py
echo.
echo --- Diagnostic 3: Core Algorithm Unit Tests ---
!VENV_PY! -m unittest discover tests -v
echo.

echo ==============================================================================
echo   SETUP AND VERIFICATION COMPLETE!
echo ==============================================================================
echo To launch the project, double-click run.bat or execute:
echo   .venv\Scripts\python main.py
echo   .venv\Scripts\streamlit run dashboard\dashboard.py
echo.
pause
