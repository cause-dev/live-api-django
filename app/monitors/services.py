import requests
from django.utils import timezone
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException


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
        The main entry point. Pings the site and updates the results.
        """
        try:
            response = self._perform_request("HEAD")
            if response.status_code in [404, 405]:
                response = self._perform_request("GET")

            self.status_code = response.status_code
            self.response_time = response.elapsed.total_seconds()
            self.is_online = self.status_code == self.expected_code
        except Timeout:
            self.error_message = "Timeout"
        except ConnectionError:
            self.error_message = "DNS/Connection Error"
        except RequestException:
            self.error_message = "Request Failed"

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
