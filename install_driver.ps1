# install_driver.ps1
$driverDir = Join-Path $PSScriptRoot "esp32_driver"
$installerExe = Join-Path $driverDir "CP210x_Installer.exe"
$infPath = Join-Path $driverDir "silabser.inf"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  Installing Silicon Labs CP210x Driver for ESP32" -ForegroundColor Cyan
Write-Host "  Driver folder: $driverDir" -ForegroundColor White
Write-Host "  Please click YES on the Windows UAC security prompt!" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan

# Run DPInst with WorkingDirectory and /PATH
if (Test-Path $installerExe) {
    Write-Host "[1/2] Running Driver Package Installer..." -ForegroundColor Yellow
    Start-Process -FilePath $installerExe -WorkingDirectory $driverDir -ArgumentList "/PATH `"$driverDir`"" -Verb RunAs -Wait
}

# Also run pnputil elevated directly to ensure driver store registration
Write-Host "[2/2] Staging and registering silabser.inf via pnputil..." -ForegroundColor Yellow
Start-Process -FilePath "pnputil.exe" -ArgumentList @("/add-driver", "$infPath", "/install") -Verb RunAs -Wait

Start-Sleep -Seconds 2

# Check for detected COM ports
Write-Host ""
Write-Host "Scanning for detected COM ports..." -ForegroundColor Green
$ports = [System.IO.Ports.SerialPort]::GetPortNames()
if ($ports) {
    Write-Host "SUCCESS! Found COM Port(s): $($ports -join ', ')" -ForegroundColor Green
} else {
    Write-Host "Driver installed! Unplug & re-plug your ESP32 USB-C cable once now to assign the COM port." -ForegroundColor Yellow
}
