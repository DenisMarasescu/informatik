import time

from agentql import trail_logger

DOM_NETWORK_QUIET_THRESHOLD_SECONDS = 0.5


class PageActivityMonitor:
    """A class that monitors network activity and determines when a page has loaded."""

    def __init__(self):
        """Initialize the network monitor."""
        self._request_log = {}
        self._response_log = set()
        self._last_network_active_time = time.time()
        self._multi_request_found = False
        self._multi_request_url = ""
        self._page_loaded = False
        self._start_time = time.time()

    def track_network_request(self, request):
        """Track a request and record its timestamp into the _last_network_active_time.

        Parameters:
        ----------
        request (requests.PreparedRequest): The request to track."""
        self._last_network_active_time = time.time()
        # Start logging duplicate urls after the first 6 seconds
        if time.time() - self._start_time > 6:
            if request.url in self._request_log:
                self._multi_request_found = True
                self._multi_request_url = request.url
        self._request_log[request.url] = time.time()

    def track_network_response(self, response):
        """Track a response and mark it in the network log.

        Parameters:
        ----------
        response (requests.Response): The response to track."""
        self._last_network_active_time = time.time()
        if response.url in self._request_log:
            self._response_log.add(response.url)

    def track_load(self, _page):
        """Track whether the current page has loaded to make sure navigation is finished."""
        self._page_loaded = True

    def get_load_status(self):
        """Get the status of the page load.

        Returns:
        -------
        bool: True if the page has loaded, False otherwise."""
        return self._page_loaded

    def is_page_ready(self, last_active_dom_time=None) -> bool:
        """Check if the conditions for Page Ready state have been met

        Returns:
        -------
        bool: True if the conditions for Page Ready State have been met, False otherwise."""
        dom_is_quiet = False
        network_is_quiet = False

        # Check if DOM has changed
        if last_active_dom_time:
            last_active_dom_time = float(last_active_dom_time) / 1000
            if time.time() - last_active_dom_time > DOM_NETWORK_QUIET_THRESHOLD_SECONDS:
                dom_is_quiet = True

        # Check for inactivity
        missing_responses = []
        if time.time() - self._last_network_active_time > DOM_NETWORK_QUIET_THRESHOLD_SECONDS:
            # Check if all requests have been resolved
            for request in self._request_log:
                if request not in self._response_log:
                    missing_responses.append(request)

            # If not all requests have been resolved, check if 1.5 seconds have passed since the last request. If so, treat the request as resolved
            missing_responses_count = len(missing_responses)
            for missing_response in missing_responses:
                time_diff = time.time() - self._request_log[missing_response]
                if time_diff > 1.5:
                    missing_responses_count -= 1

            if missing_responses_count == 0:
                if dom_is_quiet:
                    trail_logger.add_event(
                        f"Page ready: No network and DOM activity for {DOM_NETWORK_QUIET_THRESHOLD_SECONDS} seconds."
                    )
                    return True
                network_is_quiet = True

        # If 6 seconds has passed, only check if the network is quiet or if multiple requests to the same destination are found
        if time.time() - self._start_time > 6:
            if network_is_quiet:
                trail_logger.add_event(
                    f"Page ready: No network activity for {DOM_NETWORK_QUIET_THRESHOLD_SECONDS} seconds."
                )
                return True
            if self._multi_request_found:
                trail_logger.add_event(
                    f"Page ready: Multiple outgoing requests to url {self._multi_request_url} are found."
                )
                return True

        return False

    def reset(self):
        """Reset the network monitor."""
        self._request_log = {}
        self._response_log = set()
        self._last_network_active_time = time.time()
        self._multi_request_found = False
        self._multi_request_url = ""
        self._start_time = time.time()
        self._page_loaded = False
