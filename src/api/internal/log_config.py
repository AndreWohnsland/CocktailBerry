import copy
import logging

from uvicorn.config import LOGGING_CONFIG


class EndpointFilter(logging.Filter):
    """Filter to exclude specific endpoints from access logs."""

    def __init__(self, excluded_endpoints: list[str] | None = None) -> None:
        super().__init__()
        self.excluded_endpoints = excluded_endpoints or []

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(endpoint in message for endpoint in self.excluded_endpoints)


log_config = copy.deepcopy(LOGGING_CONFIG)

log_config["formatters"]["default"]["fmt"] = "%(asctime)s | %(levelprefix)s | %(message)s"
log_config["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
log_config["formatters"]["access"]["fmt"] = (
    '%(asctime)s | %(levelprefix)s | %(client_addr)s - "%(request_line)s" %(status_code)s'
)
log_config["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

# Add filter to exclude specific endpoints from access logs
log_config["filters"] = {
    "endpoint_filter": {
        "()": EndpointFilter,
        "excluded_endpoints": ["GET /api/info"],
    }
}
log_config["handlers"]["access"]["filters"] = ["endpoint_filter"]
