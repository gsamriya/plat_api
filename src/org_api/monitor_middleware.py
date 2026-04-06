from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from ichec_monitor import CustomRequestCounter, RequestCounterConfig

# Create a custom request counter via ichec_monitor with labels
request_counter = CustomRequestCounter(
            RequestCounterConfig(
                name="http_requests_total_ichec_api",
                description="Total HTTP requests",
                label_names=["method", "endpoint"]
            )
        )

class MonitoringMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Increment the counter with label values
        request_counter.inc(method="GET", endpoint="/status")
        # Increment the counter with label values
        request_counter.inc(method="POST", endpoint="/data")
        response = await call_next(request)

        return response