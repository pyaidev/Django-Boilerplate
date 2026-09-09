from .base import *  # noqa: F403

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405
SECRET_KEY = SECRET_KEY or "development-only-key-do-not-use-in-production-0123456789"  # noqa: F405
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)  # noqa: F405
SPECTACULAR_SETTINGS["SERVE_PERMISSIONS"] = ["rest_framework.permissions.AllowAny"]  # noqa: F405
STORAGES["staticfiles"] = {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"}  # noqa: F405
