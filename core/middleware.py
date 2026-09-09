import logging
import time
import uuid

from core.logging import request_id_context

logger = logging.getLogger("http.requests")


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid.uuid4().hex
        token = request_id_context.set(request.request_id)
        started = time.monotonic()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request.request_id
            match = getattr(request, "resolver_match", None)
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "route": match.route if match else "unresolved",
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                },
            )
            return response
        finally:
            request_id_context.reset(token)
