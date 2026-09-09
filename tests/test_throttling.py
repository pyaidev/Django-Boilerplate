import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from redis import ConnectionError

from core.throttling import client_ip, increment_counter


def rates(settings, **overrides):
    config = dict(settings.REST_FRAMEWORK)
    config["DEFAULT_THROTTLE_RATES"] = {**config["DEFAULT_THROTTLE_RATES"], **overrides}
    settings.REST_FRAMEWORK = config


def test_anonymous_limit_is_shared_between_clients(api_client, settings):
    rates(settings, anon="2/minute")
    from rest_framework.test import APIClient

    assert api_client.get("/api/v1/auth/csrf/").status_code == 200
    assert APIClient().get("/api/v1/auth/csrf/").status_code == 200
    response = api_client.get("/api/v1/auth/csrf/")
    assert response.status_code == 429
    assert 1 <= int(response["Retry-After"]) <= 60
    assert response.data["error"]["code"] == "throttled"


@pytest.mark.django_db
def test_login_has_separate_limit(api_client, settings):
    rates(settings, login="2/minute")
    for _ in range(2):
        assert (
            api_client.post("/api/v1/auth/login/", {"username": "missing", "password": "bad"}).status_code
            == 403
        )
    assert (
        api_client.post("/api/v1/auth/login/", {"username": "missing", "password": "bad"}).status_code == 429
    )
    assert api_client.get("/api/v1/auth/csrf/").status_code == 200


@pytest.mark.django_db
def test_user_limit_follows_user_across_ips(authenticated_client, settings):
    rates(settings, user="1/minute")
    assert authenticated_client.get("/api/v1/auth/me/", REMOTE_ADDR="192.0.2.1").status_code == 200
    assert authenticated_client.get("/api/v1/auth/me/", REMOTE_ADDR="192.0.2.2").status_code == 429


def test_untrusted_forwarded_ip_cannot_bypass_limit(api_client, settings):
    rates(settings, anon="1/minute")
    assert api_client.get("/api/v1/auth/csrf/", HTTP_X_REAL_IP="192.0.2.1").status_code == 200
    assert api_client.get("/api/v1/auth/csrf/", HTTP_X_REAL_IP="192.0.2.2").status_code == 429


def test_only_explicit_proxy_peer_is_trusted(settings):
    settings.TRUSTED_PROXY_IPS = ["192.0.2.10"]
    request = RequestFactory().get("/", REMOTE_ADDR="192.0.2.10", HTTP_X_REAL_IP="198.51.100.4")
    assert client_ip(request) == "198.51.100.4"
    request.META["HTTP_X_REAL_IP"] = "malformed"
    assert client_ip(request) == "192.0.2.10"


def test_redis_failure_does_not_disable_limits(api_client, settings):
    settings.RATE_LIMIT_REDIS_URL = "redis://localhost:6379/15"
    with patch("core.throttling.redis_client") as client:
        client.return_value.eval.side_effect = ConnectionError("unavailable")
        response = api_client.get("/api/v1/auth/csrf/")
    assert response.status_code == 503
    assert response.data["error"]["code"] == "rate_limit_unavailable"


@pytest.mark.redis
def test_real_redis_counter_is_atomic_and_expires(settings):
    url = os.getenv("TEST_REDIS_URL")
    if not url:
        pytest.skip("TEST_REDIS_URL is required for the Redis integration test")
    settings.RATE_LIMIT_REDIS_URL = url
    key = f"boilerplate:test:{uuid.uuid4().hex}"
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: increment_counter(key, 1), range(50)))
    assert sorted(count for count, _ in results) == list(range(1, 51))
    assert sum(count <= 5 for count, _ in results) == 5
    time.sleep(1.1)
    assert increment_counter(key, 1)[0] == 1
