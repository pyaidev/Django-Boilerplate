import logging

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request_id = getattr(context.get("request"), "request_id", "-")
    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        return Response(
            {
                "error": {
                    "code": "server_error",
                    "message": "An unexpected error occurred.",
                    "details": {},
                    "request_id": request_id,
                }
            },
            status=500,
        )
    details = response.data
    message = (
        details.get("detail", "Request validation failed.")
        if isinstance(details, dict)
        else "Request failed."
    )
    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "request_error"),
            "message": str(message),
            "details": details,
            "request_id": request_id,
        }
    }
    return response


def axes_lockout_response(request, *args, **kwargs):
    response = JsonResponse(
        {
            "error": {
                "code": "login_locked",
                "message": "Too many failed login attempts. Try again later.",
                "details": {},
                "request_id": getattr(request, "request_id", "-"),
            }
        },
        status=429,
    )
    response["Retry-After"] = "900"
    return response


def csrf_failure(request, reason=""):
    return JsonResponse(
        {
            "error": {
                "code": "csrf_failed",
                "message": "CSRF verification failed.",
                "details": {},
                "request_id": getattr(request, "request_id", "-"),
            }
        },
        status=403,
    )
