from unittest.mock import patch

import pytest
from django.db import OperationalError


def test_liveness_is_independent_of_database(api_client):
    assert api_client.get("/health/live/").json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_checks_database_and_cache(api_client):
    assert api_client.get("/health/ready/").status_code == 200


def test_readiness_hides_database_failure_details(api_client):
    with patch("apps.common.views.connection.cursor", side_effect=OperationalError("private-host")):
        response = api_client.get("/health/ready/")
    assert response.status_code == 503
    assert "private-host" not in response.content.decode()


def test_request_id_is_generated_and_returned(api_client):
    response = api_client.get("/health/live/", HTTP_X_REQUEST_ID="untrusted-value")
    assert len(response["X-Request-ID"]) == 32
    assert response["X-Request-ID"] != "untrusted-value"


def test_metrics_are_not_exposed_on_public_app_port(api_client):
    assert api_client.get("/metrics").status_code == 404


def test_schema_is_valid_openapi3(api_client):
    response = api_client.get("/api/schema/?format=json")
    assert response.status_code == 200
    assert response.data["openapi"].startswith("3.")
    assert "/api/v1/notes/" in response.data["paths"]
