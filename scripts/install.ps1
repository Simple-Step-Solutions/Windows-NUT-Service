$ErrorActionPreference = "Stop"

# GitHub repository for scripts
$RepoUrl = "https://raw.githubusercontent.com/Simple-Step-Solutions/Windows-NUT-Service/main/"
$ServiceScriptUrl = "${RepoUrl}windows_nut_service.py"
$ConfigFileUrl = "${RepoUrl}config.json"
$RequirementsUrl = "${RepoUrl}requirements.txt"

# Define paths
$PythonInstaller = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
$ScriptDir = "$env:ProgramFiles\Simple Step Solutions\NUTMonitor"
$ServiceScript = Join-Path $ScriptDir "windows_nut_service.py"
$ConfigFile = Join-Path $ScriptDir "config.json"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$PythonPath = "$env:ProgramFiles\Python313"

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

# Download the requirement file
Write-Event "Downloading requirements file..."
Invoke-WebRequest -Uri $RequirementsUrl -OutFile $RequirementsFile

# Install Python if not installed
if (-Not (Test-Path "$PythonPath\python.exe")) {
    Write-Event "Python not found. Downloading Python installer..."
    $PythonInstallerPath = Join-Path $env:TEMP "python-installer.exe"
    Invoke-WebRequest -Uri $PythonInstaller -OutFile $PythonInstallerPath

    Write-Event "Installing Python..."
    Start-Process -FilePath $PythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1" -Wait
    Remove-Item $PythonInstallerPath
}

# Install required Python packages
Write-Event "Installing required Python packages..."
$PipPath = Join-Path $PythonPath "Scripts\pip.exe"
& $PipPath install -r $RequirementsFile

# Since pynut is in beta currently, needs to be added separately
& $PipPath install -i https://test.pypi.org/simple/ pynutclient

# Using the service script, install the service
& "$PythonPath\python.exe" $ServiceScript install
& "$PythonPath\python.exe" $ServiceScript start

# Set the service to automatic start
Set-Service -Name UPSMonitorService -StartupType Automatic

# Clean up
Remove-Item $RequirementsFile

Write-Event "Installation complete. The UPS Monitor Service has been installed and started."
