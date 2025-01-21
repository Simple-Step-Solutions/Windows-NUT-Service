import json
import os
import time
import win32event
import win32service
import win32serviceutil
from PyNUTClient import PyNUTClient
from win32evtlogutil import ReportEvent

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

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r") as file:
                return json.load(file)
        except Exception as e:
            self.log_event(f"Failed to load configuration: {e}", event_id=1006, event_type=win32event.EVENTLOG_ERROR_TYPE)
            raise

    def log_event(self, message, event_id=1000, event_type=win32event.EVENTLOG_INFORMATION_TYPE):
        ReportEvent(self._svc_name_, event_id, eventType=event_type, strings=[message])

    def connect_to_nut(self):
        try:
            self.nut_client = PyNUTClient(
                host=self.config["nut_server"].get("host", "localhost"),
                port=self.config["nut_server"].get("port", 3493),
                username=self.config["nut_server"].get("user"),
                password=self.config["nut_server"].get("password")
            )
            self.log_event("Connected to NUT server.", event_id=1000)
        except Exception as e:
            self.log_event(f"Failed to connect to NUT server: {e}", event_id=1001, event_type=win32event.EVENTLOG_ERROR_TYPE)

    def monitor_ups(self):
        if not self.nut_client:
            self.connect_to_nut()
            if not self.nut_client:
                time.sleep(5)  # Retry connection every 5 seconds
                return

        try:
            ups_data = self.nut_client.list_vars(self.config["nut_server"].get("ups_name", "ups"))
            on_battery = ups_data.get("status", "").lower().startswith("ob")
            battery_level = int(ups_data.get("battery.charge", 100))

            if on_battery:
                self.log_event("UPS is on battery power.", event_id=1002)
                if self.config["monitor_type"] == "battery_percentage" and battery_level <= self.config["threshold"]:
                    self.initiate_shutdown("Battery level critical.")
                elif self.config["monitor_type"] == "time_on_battery":
                    self.log_event("Monitoring time on battery.", event_id=1003)
                    time.sleep(self.config["shutdown_delay"])
                    self.initiate_shutdown("Time on battery exceeded threshold.")

        except Exception as e:
            self.log_event(f"Error monitoring UPS: {e}", event_id=1004, event_type=win32event.EVENTLOG_ERROR_TYPE)

    def initiate_shutdown(self, reason):
        self.log_event(f"Initiating shutdown: {reason}", event_id=1005)
        shutdown_command = self.config.get("shutdown_command", "shutdown /s /t 0")
        os.system(shutdown_command)

    def SvcDoRun(self):
        self.log_event("Service started.", event_id=1000)
        while self.running:
            self.monitor_ups()
            time.sleep(5)  # Prevent high CPU usage

    def SvcStop(self):
        self.running = False
        win32event.SetEvent(self.stop_event)
        self.log_event("Service stopped.", event_id=1000)

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(UPSMonitorService)
