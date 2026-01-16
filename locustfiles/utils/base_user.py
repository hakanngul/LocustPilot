import os
from locust import FastHttpUser, events, between

try:
    from locust.contrib.fasthttp import FastResponse
except ImportError:
    FastResponse = None

from locustfiles.utils.log_utils import log_test_summary

TARGET_HOST = os.getenv("LOCUST_TARGET_HOST", "https://localhost:8080")


class BaseLocustUser(FastHttpUser):
    """
    Base class for all Locust load tests.
    Provides common FastHttpUser configurations and response validation.
    """

    # Tells Locust not to run this class directly as a test
    abstract = True

    # Default wait_time (subclasses can override this)
    wait_time = between(1, 5)

    # FastHttpUser optimizations
    connection_timeout = 5.0
    network_timeout = 10.0
    max_retries = 0
    host = TARGET_HOST

    def validate_response(
        self, response: FastResponse, expected_status: int = 200, check_text: str = None
    ):
        """
        Validate HTTP response and mark as success/failure.
        MUST be used within a 'with client.request(..., catch_response=True) as response:' block.

        Args:
            response: Locust response object
            expected_status: Expected HTTP status code (default: 200)
            check_text: Optional string to search within response body
        """
        # 1. Status Code Check
        if response.status_code != expected_status:
            # Adding a short preview from response body in error cases is helpful.
            error_preview = response.text[:200] if response.text else "No content"
            response.failure(
                f"FAIL: Expected {expected_status}, got {response.status_code}. Body: {error_preview}"
            )
            return  # Exit if there's an error

        # 2. (Optional) Content Check
        if check_text and check_text not in response.text:
            response.failure(f"FAIL: Text '{check_text}' not found in response.")
            return

        # If everything is fine
        response.success()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Global test stop listener for all tests."""
    # Only print report if requests were made (to avoid log clutter in empty runs)
    if environment.stats.total.num_requests > 0:
        try:
            log_test_summary(environment)
        except Exception as e:
            environment.events.log.fire(f"Summary logging failed: {e}")
