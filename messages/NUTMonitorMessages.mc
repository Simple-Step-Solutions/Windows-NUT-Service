; NUTMonitorMessages.mc
; Message definitions for the UPS Monitor Service Windows event log source.
;
; Each message body is %1 — a pass-through that renders the insertion string
; supplied by the service at runtime. This gives us clean, readable messages
; in Event Viewer and PowerShell Get-WinEvent while preserving our custom
; event IDs for RMM alerting.
;
; Build pipeline: mc.exe → rc.exe → link.exe /DLL /NOENTRY → NUTMonitorMessages.dll
; See .github/workflows/build-message-dll.yml

MessageIdTypedef=DWORD

LanguageNames=(English=0x0409:MSG00001)

; ---------------------------------------------------------------
; Service Lifecycle (1000-1009)
; ---------------------------------------------------------------

MessageId=1001
SymbolicName=MSG_SERVICE_STARTED
Language=English
%1
.

MessageId=1002
SymbolicName=MSG_SERVICE_STOPPED
Language=English
%1
.

; ---------------------------------------------------------------
; Configuration (1010-1019)
; ---------------------------------------------------------------

MessageId=1010
SymbolicName=MSG_CONFIG_LOADED
Language=English
%1
.

MessageId=1011
SymbolicName=MSG_CONFIG_FAILED
Language=English
%1
.

; ---------------------------------------------------------------
; NUT Server Connection (1020-1029)
; ---------------------------------------------------------------

MessageId=1020
SymbolicName=MSG_NUT_CONNECTED
Language=English
%1
.

MessageId=1021
SymbolicName=MSG_NUT_CONNECT_FAILED
Language=English
%1
.

; ---------------------------------------------------------------
; UPS Monitoring (1030-1039)
; ---------------------------------------------------------------

MessageId=1030
SymbolicName=MSG_UPS_ON_BATTERY
Language=English
%1
.

MessageId=1031
SymbolicName=MSG_BATTERY_MODE_STARTED
Language=English
%1
.

MessageId=1032
SymbolicName=MSG_TIME_ON_BATTERY
Language=English
%1
.

MessageId=1033
SymbolicName=MSG_UPS_ONLINE
Language=English
%1
.

; ---------------------------------------------------------------
; Connection Errors (1040-1049)
; ---------------------------------------------------------------

MessageId=1040
SymbolicName=MSG_NUT_RECONNECT
Language=English
%1
.

MessageId=1041
SymbolicName=MSG_OS_ERROR
Language=English
%1
.

MessageId=1042
SymbolicName=MSG_MONITOR_ERROR
Language=English
%1
.

; ---------------------------------------------------------------
; Shutdown (1050-1059)
; ---------------------------------------------------------------

MessageId=1050
SymbolicName=MSG_SHUTDOWN_INITIATED
Language=English
%1
.

MessageId=1051
SymbolicName=MSG_SHUTDOWN_FAILED
Language=English
%1
.
