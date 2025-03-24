import json
import os
import time
import win32event
import win32evtlog
import win32service
import win32serviceutil
import logging
from PyNUTClient.PyNUT import PyNUTClient
from win32evtlogutil import ReportEvent
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
        self.battery_start_time = None  # Initialize battery start time

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
        ReportEvent(self._svc_name_, event_id, eventType=event_type, strings=[message])
        if event_type == win32evtlog.EVENTLOG_INFORMATION_TYPE:
            logger.info(message)
        elif event_type == win32evtlog.EVENTLOG_ERROR_TYPE:
            logger.error(message)
        elif event_type == win32evtlog.EVENTLOG_WARNING_TYPE:
            logger.warning(message)

    def connect_to_nut(self):
        try:
            self.nut_client = PyNUTClient(
                host=self.config["nut_server"].get("host", "localhost"),
                port=self.config["nut_server"].get("port", 3493),
                login=self.config["nut_server"].get("user", "ups"),
                password=self.config["nut_server"].get("password", "password")
            )
            self.log_event("Connected to NUT server.", event_id=1020)
        except Exception as e:
            self.log_event(f"Failed to connect to NUT server: {e}", event_id=1021, event_type=win32evtlog.EVENTLOG_ERROR_TYPE)

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
                    self.battery_start_time = None  # Reset the timer

        except OSError as e:
            if e.errno == 10053:
                self.log_event("Connection to NUT server was aborted. Attempting to reconnect on next cycle.", event_id=1040, event_type=win32evtlog.EVENTLOG_WARNING_TYPE)
                self.nut_client = None # Force a reconnect on the next cycle
            else:
                self.log_event(f"An OS error occurred while monitoring UPS: {e}", event_id=1041, event_type=win32evtlog.EVENTLOG_ERROR_TYPE)
        except Exception as e:
            self.log_event(f"Error monitoring UPS: {e}", event_id=1042, event_type=win32evtlog.EVENTLOG_ERROR_TYPE)

    def initiate_shutdown(self, reason):
        self.log_event(f"Initiating shutdown: {reason}", event_id=1050)
        shutdown_command = self.config.get("shutdown_command", "shutdown /s /t 0")
        os.system(shutdown_command)

    def SvcDoRun(self):
        self.log_event("Service started.", event_id=1001)
        while self.running:
            self.monitor_ups()
            time.sleep(5)  # Prevent high CPU usage

    def SvcStop(self):
        self.running = False
        win32event.SetEvent(self.stop_event)
        self.log_event("Service stopped.", event_id=1002)

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(UPSMonitorService)