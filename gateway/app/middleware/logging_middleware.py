import json
import logging
import sys
import time
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("gateway.access")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured JSON logging middleware.
    Outputs log entries with: timestamp, method, path, status_code,
    duration_ms, correlation_id, user_id.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        status_code = 500

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            raise
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            correlation_id = getattr(request.state, "correlation_id", None)
            user_id = getattr(request.state, "user_id", None)

            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
                "user_id": user_id,
            }
            logger.info(json.dumps(log_entry))
