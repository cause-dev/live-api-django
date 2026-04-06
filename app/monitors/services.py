import requests
from django.utils import timezone
from .models import MonitorLog


class MonitorService:
    def __init__(self, monitor):
        self.monitor = monitor
        self.expected_code = monitor.expected_status_code
        self.url = monitor.url
        self.timeout = 10
        self.headers = {
            "User-Agent": "ApiVigil/1.0 (https://apivigil.com)",
        }
        # Variables
        self.is_online = False
        self.status_code = None
        self.response_time = None
        self.error_message = None

    def run_check(self):
        """
        The main entry point. Pings the site, creates a log, and updates the model.
        """
        try:
            response = self._perform_request("HEAD")
            if response.status_code in [404, 405]:
                response = self._perform_request("GET")

            self.status_code = response.status_code
            self.response_time = response.elapsed.total_seconds()
            self.is_online = self.status_code == self.expected_code

        except Exception as e:
            self.is_online = False
            self.error_message = str(e)[:1000]

        self._create_log_entry()

        return self._update_monitor_model()

    def _perform_request(self, method):
        """Internal helper to execute the HTTP call."""
        if method == "HEAD":
            return requests.head(
                self.url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
        return requests.get(
            self.url, headers=self.headers, timeout=self.timeout, stream=True
        )

    def _update_monitor_model(self):
        """Updates the Django model instance with the check results."""
        self.monitor.is_online = self.is_online
        self.monitor.last_checked = timezone.now()
        self.monitor.save()
        return self.monitor

    def _create_log_entry(self):
        """Saves a snapshot of this check to the MonitorLog table."""
        MonitorLog.objects.create(
            monitor=self.monitor,
            status_code=self.status_code,
            latency=self.response_time,
            is_online=self.is_online,
            error_message=self.error_message,
        )
