import copy

from uvicorn.config import LOGGING_CONFIG

log_config = copy.deepcopy(LOGGING_CONFIG)
log_config["formatters"]["default"]["fmt"] = "%(asctime)s %(levelprefix)s - %(message)s"
log_config["formatters"]["access"]["fmt"] = (
    '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
)
