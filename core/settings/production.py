from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("development-"):  # noqa: F405
    raise ImproperlyConfigured("Production requires a random SECRET_KEY of at least 50 characters.")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("Production requires explicit ALLOWED_HOSTS.")
if "postgresql" not in DATABASES["default"]["ENGINE"]:  # noqa: F405
    raise ImproperlyConfigured("Production requires a PostgreSQL DATABASE_URL.")
if not REDIS_URL or not RATE_LIMIT_REDIS_URL:  # noqa: F405
    raise ImproperlyConfigured("Production requires Redis for cache and distributed rate limits.")
if not PUBLIC_BASE_URL.startswith("https://"):  # noqa: F405
    raise ImproperlyConfigured("Production requires an HTTPS PUBLIC_BASE_URL.")
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^health/live/$", r"^health/ready/$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)  # noqa: F405
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)  # noqa: F405
# The proxy must strip client-supplied X-Forwarded-Proto before enabling this.
if env.bool("TRUST_PROXY_HTTPS", default=False):  # noqa: F405
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SENTRY_DSN = env.str("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=False,
        environment=env.str("SENTRY_ENVIRONMENT", default="production"),  # noqa: F405
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),  # noqa: F405
    )
