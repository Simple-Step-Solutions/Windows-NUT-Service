$ErrorActionPreference = "Stop"

# GitHub repository for scripts
$RepoUrl = "https://raw.githubusercontent.com/username/repo/branch/"
$ServiceScriptUrl = "${RepoUrl}windows_nut_service.py"
$ConfigFileUrl = "${RepoUrl}config.json"

# Define paths
$PythonInstaller = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
$ScriptDir = "$env:ProgramFiles\SimpleStepSolutions\NUTMonitor"
$ServiceScript = Join-Path $ScriptDir "windows_nut_service.py"
$ConfigFile = Join-Path $ScriptDir "config.json"
$PythonPath = "C:\Python313"

# Function to log events
function Write-Event {
    param (
        [string]$Message
    )
    Write-Host $Message
}

# Create service directory if it doesn't exist
if (-Not (Test-Path $ScriptDir)) {
    New-Item -Path $ScriptDir -ItemType Directory
}

# Download the Python service script
Write-Event "Downloading service script..."
Invoke-WebRequest -Uri $ServiceScriptUrl -OutFile $ServiceScript

# Download the configuration file
Write-Event "Downloading configuration file..."
Invoke-WebRequest -Uri $ConfigFileUrl -OutFile $ConfigFile

# Install Python if not installed
if (-Not (Test-Path "$PythonPath\python.exe")) {
    Write-Event "Python not found. Downloading Python installer..."
    $PythonInstallerPath = Join-Path $env:TEMP "python-installer.exe"
    Invoke-WebRequest -Uri $PythonInstaller -OutFile $PythonInstallerPath

    Write-Event "Installing Python..."
    Start-Process -FilePath $PythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 TargetDir=$PythonPath" -Wait
    Remove-Item $PythonInstallerPath
}

# Install required Python packages
Write-Event "Installing required Python packages..."
$PipPath = Join-Path $PythonPath "Scripts\pip.exe"
& $PipPath install pywin32 PyNUTClient

# Generate service registration script
$RegisterServiceScript = @"
import win32serviceutil
from windows_nut_service import UPSMonitorService

if __name__ == '__main__':
    win32serviceutil.InstallService(
        UPSMonitorService._svc_name_,
        UPSMonitorService._svc_display_name_,
        UPSMonitorService._svc_description_
    )
    win32serviceutil.StartService(UPSMonitorService._svc_name_)
"@

$RegisterServicePath = Join-Path $ScriptDir "register_service.py"
Set-Content -Path $RegisterServicePath -Value $RegisterServiceScript

# Register the service
Write-Event "Registering the UPS Monitor service..."
& "$PythonPath\python.exe" $RegisterServicePath

# Clean up
Remove-Item $RegisterServicePath

Write-Event "Installation complete. The UPS Monitor Service has been installed and started."
