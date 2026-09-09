import hashlib
import ipaddress
import math
import time
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache
from redis import Redis, RedisError
from rest_framework.exceptions import APIException
from rest_framework.settings import api_settings
from rest_framework.throttling import BaseThrottle

# Count and expiry are changed atomically, including across Gunicorn workers.
COUNTER_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('PEXPIRE', KEYS[1], ARGV[1]) end
return {count, redis.call('PTTL', KEYS[1])}
"""


class RateLimitUnavailable(APIException):
    status_code = 503
    default_detail = "Request limiting is temporarily unavailable. Try again shortly."
    default_code = "rate_limit_unavailable"


def client_ip(request):
    peer = request.META.get("REMOTE_ADDR", "127.0.0.1")
    # Trust exactly one sanitized header from an explicitly trusted direct peer.
    if peer in settings.TRUSTED_PROXY_IPS:
        forwarded = request.META.get("HTTP_X_REAL_IP", "")
        try:
            return str(ipaddress.ip_address(forwarded))
        except ValueError:
            pass
    return peer


@lru_cache(maxsize=4)
def redis_client(url):
    return Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)


def increment_counter(key, duration):
    if settings.RATE_LIMIT_REDIS_URL:
        try:
            count, ttl_ms = redis_client(settings.RATE_LIMIT_REDIS_URL).eval(
                COUNTER_SCRIPT,
                1,
                key,
                duration * 1000,
            )
            return int(count), max(1, math.ceil(ttl_ms / 1000))
        except RedisError as exc:
            raise RateLimitUnavailable() from exc
    # Development/tests only; production settings require Redis.
    expires_key = key + ":expires"
    if cache.add(key, 1, duration):
        cache.set(expires_key, time.time() + duration, duration)
        return 1, duration
    try:
        count = cache.incr(key)
    except ValueError:
        return increment_counter(key, duration)
    return count, max(1, math.ceil(cache.get(expires_key, time.time() + duration) - time.time()))


class FixedWindowThrottle(BaseThrottle):
    def scope_and_identity(self, request, view):
        raise NotImplementedError

    def allow_request(self, request, view):
        scope, identity = self.scope_and_identity(request, view)
        if scope is None:
            return True
        rate = api_settings.DEFAULT_THROTTLE_RATES[scope]
        limit, period = rate.split("/")
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
        digest = hashlib.sha256(identity.encode()).hexdigest()
        count, self.retry_after = increment_counter(f"boilerplate:throttle:{scope}:{digest}", duration)
        return count <= int(limit)

    def wait(self):
        return self.retry_after


class APIRateThrottle(FixedWindowThrottle):
    def scope_and_identity(self, request, view):
        if request.user and request.user.is_authenticated:
            return "user", f"user:{request.user.pk}"
        return "anon", f"ip:{client_ip(request)}"


class EndpointRateThrottle(FixedWindowThrottle):
    def scope_and_identity(self, request, view):
        return getattr(view, "throttle_scope", None), f"ip:{client_ip(request)}"
