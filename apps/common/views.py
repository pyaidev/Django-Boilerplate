import logging

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from core.throttling import redis_client

logger = logging.getLogger(__name__)


@require_GET
def live(request):
    return JsonResponse({"status": "ok"})


@require_GET
def ready(request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = True
    except Exception:
        logger.exception("Database readiness failed")
        checks["database"] = False
    try:
        cache.set("boilerplate:readiness", "ok", 10)
        checks["cache"] = cache.get("boilerplate:readiness") == "ok"
        if settings.RATE_LIMIT_REDIS_URL:
            checks["rate_limit"] = bool(redis_client(settings.RATE_LIMIT_REDIS_URL).ping())
    except Exception:
        logger.exception("Redis readiness failed")
        checks["cache"] = False
    healthy = all(checks.values())
    return JsonResponse({"status": "ok" if healthy else "unavailable"}, status=200 if healthy else 503)
