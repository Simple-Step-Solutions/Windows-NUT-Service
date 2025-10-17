$ErrorActionPreference = "Stop"

# GitHub repository for scripts
$RepoUrl = "https://raw.githubusercontent.com/Simple-Step-Solutions/Windows-NUT-Service/main/"
$ServiceScriptUrl = "${RepoUrl}windows_nut_service.py"
$RequirementsUrl = "${RepoUrl}requirements.txt"

# Define paths
$ScriptDir = "$env:ProgramFiles\Simple Step Solutions\NUTMonitor"
$ServiceScript = Join-Path $ScriptDir "windows_nut_service.py"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$PythonPath = "$env:ProgramFiles\Python313"
$ServiceName = "UPSMonitorService"

# Function to log events
function Write-Event {
    param (
        [string]$Message
    )
    Write-Host $Message
}

# Check if the service exists
if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Write-Event "Stopping the UPS Monitor Service..."
    Stop-Service -Name $ServiceName
    
    Write-Event "Uninstalling the old service..."
    & "$PythonPath\python.exe" $ServiceScript remove
} else {
    Write-Event "Service not found. It may not be installed."
}


# Download the latest Python service script
Write-Event "Downloading latest service script..."
Invoke-WebRequest -Uri $ServiceScriptUrl -OutFile $ServiceScript

# Download the latest requirement file
Write-Event "Downloading latest requirements file..."
Invoke-WebRequest -Uri $RequirementsUrl -OutFile $RequirementsFile

# Install/update required Python packages
Write-Event "Updating required Python packages..."
$PipPath = Join-Path $PythonPath "Scripts\pip.exe"
& $PipPath install --upgrade -r $RequirementsFile

# Since pynut is in beta currently, needs to be added separately
& $PipPath install --upgrade -i https://test.pypi.org/simple/ pynutclient

# Using the new service script, install the service
Write-Event "Installing the new service..."
& "$PythonPath\python.exe" $ServiceScript install

# Set the service to automatic start
Set-Service -Name $ServiceName -StartupType Automatic

# Start the service
Write-Event "Starting the UPS Monitor Service..."
Start-Service -Name $ServiceName

# Clean up
Remove-Item $RequirementsFile

Write-Event "Update complete. The UPS Monitor Service has been updated and started."
