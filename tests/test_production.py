import os
import re
import subprocess
import sys

import pytest


def production_env(**overrides):
    return {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "core.settings.production",
        "SECRET_KEY": "test-production-config-key-0123456789-abcdefghijklmnopqrstuvwxyz",
        "ALLOWED_HOSTS": "example.com,localhost,127.0.0.1",
        "DATABASE_URL": "postgresql://test:test@localhost/test",
        "REDIS_URL": "redis://localhost:6379/1",
        "RATE_LIMIT_REDIS_URL": "redis://localhost:6379/2",
        "PUBLIC_BASE_URL": "https://example.com",
        "SENTRY_DSN": "",
        "USE_S3": "0",
        **overrides,
    }


def test_production_deployment_checks_pass():
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        env=production_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    # Enabling these requires a deliberate domain-wide TLS/preload decision.
    warnings = set(re.findall(r"\((security\.W\d+|drf_spectacular\.W\d+)\)", result.stderr))
    assert warnings <= {"security.W005", "security.W021"}, result.stderr


def test_full_hsts_profile_passes_strict_deployment_checks():
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
        env=production_env(
            SECURE_HSTS_INCLUDE_SUBDOMAINS="1", SECURE_HSTS_PRELOAD="1", SECURE_HSTS_SECONDS="31536000"
        ),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "overrides",
    [
        {"SECRET_KEY": "short"},
        {"ALLOWED_HOSTS": "*"},
        {"DATABASE_URL": "sqlite:///:memory:"},
        {"REDIS_URL": ""},
        {"RATE_LIMIT_REDIS_URL": ""},
        {"PUBLIC_BASE_URL": "http://example.com"},
    ],
)
def test_production_refuses_unsafe_settings(overrides):
    result = subprocess.run(
        [sys.executable, "-c", "from django.conf import settings; print(settings.DEBUG)"],
        env=production_env(**overrides),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
