$ErrorActionPreference = "Stop"

# Define paths
$ScriptDir = "$env:ProgramFiles\Simple Step Solutions\NUTMonitor"
$PythonPath = "$env:ProgramFiles\Python313"
$ServiceName = "UPSMonitorService"

# Function to log events
function Write-Event {
    param (
        [string]$Message
    )
    Write-Host $Message
}

# Stop and remove the service
Write-Event "Stopping and removing the UPS Monitor Service..."
try {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Stop-Service -Name $ServiceName
        & "$PythonPath\python.exe" (Join-Path $ScriptDir "windows_nut_service.py") remove
        Write-Event "Service stopped and removed."
    } else {
        Write-Event "Service not found, skipping."
    }
} catch {
    Write-Event "An error occurred while stopping or removing the service: $_"
}


# Remove the installation directory
if ($env:keepSettings -ne "true") {
    Write-Event "Removing installation directory..."
    if (Test-Path $ScriptDir) {
        Remove-Item -Path $ScriptDir -Recurse -Force
        Write-Event "Installation directory removed."
    } else {
        Write-Event "Installation directory not found, skipping."
    }
} else {
    Write-Event "KEEP_SETTINGS is true, preserving config.json."
    # Remove all files except config.json
    Get-ChildItem -Path $ScriptDir -Exclude "config.json" | Remove-Item -Recurse -Force
}


# Uninstall Python if the switch is set
if ($env:keepPython -ne "true") {
    Write-Event "Uninstalling Python..."
    $pythonInstallerPath = Join-Path $env:TEMP "python-installer.exe"
    $pythonInstallerUrl = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"

    Write-Event "Downloading Python installer to perform uninstall..."
    Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $pythonInstallerPath

    Write-Event "Running Python uninstaller..."
    Start-Process -FilePath $pythonInstallerPath -ArgumentList "/uninstall /quiet" -Wait

    Remove-Item $pythonInstallerPath
    Write-Event "Python uninstallation complete."
} else {
    Write-Event "keepPython is set to true, skipping Python uninstallation."
}

Write-Event "Uninstallation complete."