# Windows NUT Service

A Windows service that monitors a [Network UPS Tools (NUT)](https://networkupstools.org/) server and initiates a graceful system shutdown when configured thresholds are met — protecting your machine from unexpected power loss.

## Overview

This is useful when your Windows machine is protected by a UPS managed by a NUT server running elsewhere (e.g., a Synology NAS, Linux box, or Raspberry Pi). The service polls the NUT server on a configurable interval and shuts down Windows when the UPS has been on battery too long or the battery charge drops below a set threshold.

## Requirements

- Windows 10/11 or Windows Server 2016+
- A running NUT server reachable over the network
- Python 3.13 (installed automatically by the install script)

## Installation

Run the following in an **elevated (Administrator) PowerShell** prompt:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
irm https://raw.githubusercontent.com/Simple-Step-Solutions/Windows-NUT-Service/main/scripts/install.ps1 | iex
```

The script will:
1. Install Python 3.13 if not already present at `%ProgramFiles%\Python313`
2. Install required Python packages (`pywin32`, `pynutclient`)
3. Copy the service files to `%ProgramFiles%\Simple Step Solutions\NUTMonitor`
4. Drop a `config.json` template into that directory
5. Register and start the `UPSMonitorService` Windows service

**After installation, edit `config.json` before the service can function correctly** — the template contains placeholder values.

## Configuration

Edit `%ProgramFiles%\Simple Step Solutions\NUTMonitor\config.json`:

```json
{
    "nut_server": {
        "host": "192.168.1.10",
        "port": 3493,
        "user": "upsmon",
        "password": "secret",
        "ups_name": "ups"
    },
    "monitor_type": "time_on_battery",
    "shutdown_threshold": 300,
    "shutdown_command": "shutdown /s /t 0",
    "failsafe_mode": "failsafe"
}
```

### Options

| Key | Description |
|-----|-------------|
| `nut_server.host` | Hostname or IP of your NUT server |
| `nut_server.port` | NUT server port (default: `3493`) |
| `nut_server.user` | NUT username |
| `nut_server.password` | NUT password |
| `nut_server.ups_name` | Name of the UPS as configured in NUT (default: `ups`) |
| `monitor_type` | `battery_percentage` or `time_on_battery` |
| `shutdown_threshold` | For `battery_percentage`: charge % to trigger shutdown. For `time_on_battery`: seconds on battery before shutdown. |
| `shutdown_command` | Command to run when shutting down (default: `shutdown /s /t 0`) |
| `failsafe_mode` | `failsafe` — shut down if NUT server is unreachable. `faildeadly` — keep running and keep retrying. |

After editing the config, restart the service:

```powershell
Restart-Service UPSMonitorService
```

## Updating

Run in an elevated PowerShell prompt:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
irm https://raw.githubusercontent.com/Simple-Step-Solutions/Windows-NUT-Service/main/scripts/update.ps1 | iex
```

This stops the service, downloads the latest service script, updates Python packages, and restarts the service. Your `config.json` is preserved.

## Uninstalling

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
irm https://raw.githubusercontent.com/Simple-Step-Solutions/Windows-NUT-Service/main/scripts/uninstall.ps1 | iex
```

To keep your config when uninstalling:

```powershell
$env:keepSettings = "true"
# then run the uninstall script above
```

To keep Python installed:

```powershell
$env:keepPython = "true"
```

## Logs

The service writes a rotating log file to:

```
%ProgramFiles%\Simple Step Solutions\NUTMonitor\NUT Service.log
```

Max size is 20 MB with one backup file kept.

Events are also written to the **Windows Application Event Log** under the source `UPSMonitorService`.

## Event ID Reference

| Range | Category |
|-------|----------|
| 1000–1009 | Service lifecycle |
| 1010–1019 | Configuration |
| 1020–1029 | NUT server connection |
| 1030–1039 | UPS monitoring |
| 1040–1049 | Connection errors |
| 1050–1059 | Shutdown |

| ID | Level | Message |
|----|-------|---------|
| 1001 | Info | Service started |
| 1002 | Info | Service stopped |
| 1010 | Info | Config loaded successfully |
| 1011 | Error | Failed to load configuration |
| 1020 | Info | Connected to NUT server |
| 1021 | Error | Failed to connect to NUT server |
| 1030 | Info | UPS is on battery power |
| 1031 | Info | Battery mode started |
| 1032 | Info | Time on battery (seconds) |
| 1033 | Info | UPS returned to online power |
| 1040 | Warning | NUT server connection aborted, will retry |
| 1041 | Error | OS error during UPS monitoring |
| 1042 | Error | General error during UPS monitoring |
| 1050 | Info | Initiating shutdown |
| 1051 | Error | Shutdown command failed |
