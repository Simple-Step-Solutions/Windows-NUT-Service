### Config
- `nut_server`
  - `host`
    - The NUT server host.
    - Example: `localhost`
  - `port`
    - The NUT server port.
    - Example: `3493`
  - `user`
    - The NUT server username.
    - Example: `admin`
  - `password`
    - The NUT server password.
    - Example: `password123`
  - `ups_name`
    - The name of the UPS to be monitored.
    - Example: `ups`
- `monitor_type`
  - The monitor type for the service. Determines the criteria that trigger system shutdown.
  - Options:
    - `battery_percentage` - Shutdown initiated based on battery percentage (`shutdown_threshold` sets the percentage at which shutdown is triggered).
    - `time_on_battery` - Shutdown initiated based on the time the UPS has been on battery power (`shutdown_threshold` sets the duration in seconds before shutdown).
- `shutdown_threshold`
  - For `battery_percentage`: The percentage threshold before shutting the system down.
  - For `time_on_battery`: The duration in seconds on battery before the system shuts down.
  - Example for `battery_percentage`: `25`
  - Example for `time_on_battery`: `300`
- `shutdown_command`
  - The command to execute when the system triggers a shutdown.
  - Example: `shutdown /s /t 0`
- `failsafe_mode`
  - Determines how the system responds if the NUT server becomes unreachable.
  - Options:
    - `failsafe` - The system will initiate a shutdown if the NUT server is unreachable.
    - `faildeadly` - The system will continue attempting to reconnect without shutting down, even if the server is unreachable.

### Event ID Reference

The service uses the following Event IDs to log specific events to the Windows Event Log. The IDs are organized into ranges for easier management and future additions:

**Service Lifecycle (1000-1009):**
* **1001**: Information - Service started successfully.
* **1002**: Information - Service stopped successfully.

**Configuration (1010-1019):**
* **1010**: Information - Config loaded successfully from [path].
* **1011**: Error - Failed to load configuration: [error message].

**NUT Server Connection (1020-1029):**
* **1020**: Information - Connected to NUT server.
* **1021**: Error - Failed to connect to NUT server: [error message].

**UPS Monitoring (1030-1039):**
* **1030**: Information - UPS is on battery power.
* **1031**: Information - Battery mode started at [timestamp].
* **1032**: Information - Time on battery: [seconds] seconds.
* **1033**: Information - UPS returned to online power. Battery was on for [seconds] seconds.

**Connection Errors (1040-1049):**
* **1040**: Warning - Connection to NUT server was aborted. Attempting to reconnect on next cycle.
* **1041**: Error - An OS error occurred while monitoring UPS: [error message].
* **1042**: Error - Error monitoring UPS: [error message].

**Shutdown (1050-1059):**
* **1050**: Information - Initiating shutdown: [reason].