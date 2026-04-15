import json
import os
import subprocess
import time
import win32event
import win32evtlog
import win32service
import win32serviceutil
import win32evtlogutil
import logging
from PyNUTClient.PyNUT import PyNUTClient
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("NUT Service")
logger.setLevel(logging.DEBUG)

fh = RotatingFileHandler(os.path.join(os.path.dirname(__file__), f"NUT Service.log"), maxBytes=20000000, backupCount=1)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)

# TODO - Implement failsafe/deadly mode
# TODO - Implement battery tests
class UPSMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "UPSMonitorService"
    _svc_display_name_ = "UPS Monitor Service"
    _svc_description_ = "Monitors a NUT server for UPS status and initiates shutdown when configured thresholds are met."

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.config = self.load_config()
        self.nut_client = None
        self.running = True
        self.battery_start_time = None
        self.shutdown_initiated = False
        self.next_reconnect_attempt = None  # Cooldown timer for reconnect attempts

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
            self.log_event(f"Config loaded successfully from {config_path}", event_id=1010)
            return config
        except Exception as e:
            self.log_event(f"Failed to load configuration: {e}", event_id=1011, event_type=win32evtlog.EVENTLOG_ERROR_TYPE)
            raise

    def log_event(self, message, event_id=1000, event_type=win32evtlog.EVENTLOG_INFORMATION_TYPE):
        win32evtlogutil.ReportEvent(self._svc_name_, event_id, eventType=event_type, strings=[message])
        if event_type == win32evtlog.EVENTLOG_INFORMATION_TYPE:
            logger.info(message)
        elif event_type == win32evtlog.EVENTLOG_ERROR_TYPE:
            logger.error(message)
        elif event_type == win32evtlog.EVENTLOG_WARNING_TYPE:
            logger.warning(message)
        else:
            logger.debug(message)

    def connect_to_nut(self):
        # Enforce reconnect cooldown to avoid hammering an unreachable server
        if self.next_reconnect_attempt and datetime.now() < self.next_reconnect_attempt:
            return
        try:
            self.nut_client = PyNUTClient(
                host=self.config["nut_server"].get("host", "localhost"),
                port=self.config["nut_server"].get("port", 3493),
                login=self.config["nut_server"].get("user", "ups"),
                password=self.config["nut_server"].get("password", "password")
            )
            self.next_reconnect_attempt = None
            self.log_event("Connected to NUT server.", event_id=1020)
        except Exception as e:
            self.next_reconnect_attempt = datetime.now() + timedelta(seconds=30)
            self.log_event(f"Failed to connect to NUT server: {e}. Will retry in 30 seconds.", event_id=1021, event_type=win32evtlog.EVENTLOG_WARNING_TYPE)

    def monitor_ups(self):
        # Check if the NUT client is active, if not try to connect
        if not self.nut_client:
            self.connect_to_nut()
            if not self.nut_client:
                # Return and try again
                # TODO - Implement warnings if unable to connect repeatedly
                return

        try:
            # Get the UPS data
            ups_data = self.nut_client.GetUPSVars(self.config["nut_server"].get("ups_name", "ups"))
            # Convert byte strings to regular strings
            ups_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in ups_data.items()}
            logger.info(f"UPS data: {ups_data}")
            # Get line/battery status
            on_battery = ups_data.get("ups.status", "OL").lower().startswith("ob")
            # Get battery level
            battery_level = int(ups_data.get("battery.charge", "100"))

            # Get current time
            current_time = datetime.now()

            # Check if on battery
            if on_battery:
                self.log_event("UPS is on battery power.", event_id=1030)
                if self.shutdown_initiated:
                    # Already kicked off a shutdown — stop hammering the command
                    return
                # Check the configured mode
                if self.config["monitor_type"] == "battery_percentage":
                    # Check if battery level is lower than threshold
                    if battery_level <= self.config["shutdown_threshold"]:
                        self.initiate_shutdown("Battery level critical.")
                elif self.config["monitor_type"] == "time_on_battery":
                    # Check if the battery start time is set
                    if self.battery_start_time is None:
                        self.battery_start_time = current_time
                        self.log_event(f"Battery mode started at {self.battery_start_time}", event_id=1031)
                    else:
                        # Check if the time since entering battery mode has exceeded the threshold
                        elapsed_time = (current_time - self.battery_start_time).total_seconds()
                        self.log_event(f"Time on battery: {elapsed_time} seconds", event_id=1032)
                        if elapsed_time >= self.config["shutdown_threshold"]:
                            self.initiate_shutdown("Time on battery exceeded threshold.")
            else:
                # Check if battery start time is set
                if self.battery_start_time is not None:
                    self.log_event(f"UPS returned to online power. Battery was on for {(current_time - self.battery_start_time).total_seconds()} seconds.", event_id=1033)
                    self.battery_start_time = None
                    self.shutdown_initiated = False  # Reset so shutdown can trigger again next time

        except OSError as e:
            self.nut_client = None  # Connection is broken — force reconnect on next cycle
            self.next_reconnect_attempt = datetime.now() + timedelta(seconds=30)
            self.log_event(f"Network error communicating with NUT server (errno {e.errno}): {e}. Will reconnect in 30 seconds.", event_id=1040, event_type=win32evtlog.EVENTLOG_WARNING_TYPE)
        except Exception as e:
            self.nut_client = None  # Unknown error — treat connection as broken
            self.next_reconnect_attempt = datetime.now() + timedelta(seconds=30)
            self.log_event(f"Error monitoring UPS: {e}. Will reconnect in 30 seconds.", event_id=1042, event_type=win32evtlog.EVENTLOG_ERROR_TYPE)

    def initiate_shutdown(self, reason):
        self.shutdown_initiated = True
        self.log_event(f"Initiating shutdown: {reason}", event_id=1050)
        shutdown_command = self.config.get("shutdown_command", "shutdown /s /t 0")
        result = subprocess.run(shutdown_command, shell=True)
        if result.returncode != 0:
            self.log_event(f"Shutdown command failed with exit code {result.returncode}: {shutdown_command}", event_id=1051, event_type=win32evtlog.EVENTLOG_ERROR_TYPE)

    def _register_event_source(self):
        """Register the event source with our compiled message DLL.

        pywin32's service installer registers the source pointing to python.exe,
        which has no Win32 message resources, causing blank Message fields in
        PowerShell Get-WinEvent and Event Viewer. We re-register here at startup
        to point to NUTMonitorMessages.dll (built by the GitHub Actions workflow
        and deployed alongside this script), which contains a %1 pass-through
        template for every event ID we use.

        Falls back to EventCreate.exe if the DLL isn't present — messages will
        still be non-empty (Windows includes the insertion strings in the
        "description not found" text) but will have an ugly preamble.
        """
        dll_path = os.path.join(os.path.dirname(__file__), "NUTMonitorMessages.dll")
        if not os.path.exists(dll_path):
            logger.warning("NUTMonitorMessages.dll not found — falling back to EventCreate.exe for event source registration. Messages will display with a 'description not found' prefix.")
            dll_path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "EventCreate.exe")
        try:
            win32evtlogutil.AddSourceToRegistry(self._svc_name_, msgDLL=dll_path, eventLogType="Application")
        except Exception as e:
            logger.warning(f"Could not register event source: {e}")

    def SvcDoRun(self):
        self._register_event_source()
        self.log_event("Service started.", event_id=1001)
        while self.running:
            self.monitor_ups()
            # Block for up to 5 seconds or until the stop event is signaled,
            # whichever comes first. This lets SvcStop wake us up immediately
            # instead of waiting out a full sleep cycle.
            win32event.WaitForSingleObject(self.stop_event, 5000)

    def SvcStop(self):
        # Tell the SCM we received the stop request and are working on it.
        # Without this, the SCM assumes the service is hung and fails the stop.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.stop_event)
        self.log_event("Service stopped.", event_id=1002)

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(UPSMonitorService)