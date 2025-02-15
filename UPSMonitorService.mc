// UPSMonitorService.mc
//
// Define the facility code. You can choose a facility code; for custom applications, 0x100 is common.

//
// Define message IDs and their corresponding messages.
//

MessageIdTypedef=DWORD

severityNames=(
"INFORMATION"
"WARNING"
"ERROR"
)

// Messages
// Format: MessageId=Number
//
// Event ID 1000: Information - "Service started successfully."
// Event ID 1001: Error - "Failed to connect to NUT server: %1"
// Event ID 1002: Warning - "UPS is on battery power."
// Event ID 1003: Information - "Battery mode started at %1"
// Event ID 1004: Information - "Time on battery: %1 seconds"
// Event ID 1005: Information - "UPS returned to online power after %1 seconds."
// Event ID 1006: Error - "Failed to load configuration: %1"
// Event ID 1007: Error - "Failed to register event source: %1"
// Event ID 1008: Warning - "Initiating shutdown: %1"

//
// Message definitions
//

MessageId=1000
SymbolicName=UPSMonitorService_StartSuccess
Language=English
%1 SERVICE_STARTED_SUCCESSFULLY%

MessageId=1001
SymbolicName=UPSMonitorService_FailedConnect
Language=English
%1 FAILED_TO_CONNECT_TO_NUT_SERVER

MessageId=1002
SymbolicName=UPSMonitorService_ONBattery
Language=English
%1 UPS_IS_ON_BATTERY_POWER

MessageId=1003
SymbolicName=UPSMonitorService_BatteryModeStart
Language=English
%1 BATTERY_MODE_STARTED_AT__

MessageId=1004
SymbolicName=UPSMonitorService_TimeOnBattery
Language=English
%1 TIME_ON_BATTERY_SECONDS

MessageId=1005
SymbolicName=UPSMonitorService_ReturnedOnline
Language=English
%1 UPS_RETURNED_TO_ONLINE_POWER_AFTER_SECONDS

MessageId=1006
SymbolicName=UPSMonitorService_LoadConfigFail
Language=English
%1 FAILED_TO_LOAD_CONFIGURATION

MessageId=1007
SymbolicName=UPSMonitorService_RegisterSourceFail
Language=English
%1 FAILED_TO_REGISTER_EVENT_SOURCE

MessageId=1008
SymbolicName=UPSMonitorService_InitiateShutdown
Language=English
%1 INITIATING_SHUTDOWN: