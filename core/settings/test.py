from .development import *  # noqa: F403

DEBUG = False
AXES_ENABLED = False
SECRET_KEY = "test-only-secret-key-0123456789-abcdefghijklmnopqrstuvwxyz"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": env.db("TEST_DATABASE_URL", default="sqlite:///:memory:")}  # noqa: F405
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
RATE_LIMIT_REDIS_URL = ""
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
WHITENOISE_AUTOREFRESH = True
