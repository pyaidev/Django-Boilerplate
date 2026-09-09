import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def csrf(client):
    return client.get("/api/v1/auth/csrf/").json()["csrfToken"]


def test_register_hashes_password_and_rejects_privilege_escalation(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "newuser",
            "email": "NEW@example.com",
            "password": "Difficult-Pass-394!",
            "is_staff": True,
            "is_superuser": True,
        },
        format="json",
    )
    assert response.status_code == 201
    assert "password" not in response.data
    created = User.objects.get(username="newuser")
    assert created.email == "new@example.com"
    assert created.check_password("Difficult-Pass-394!")
    assert not created.is_staff and not created.is_superuser


def test_registration_rejects_weak_password(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "newuser",
            "email": "new@example.com",
            "password": "12345678",
        },
    )
    assert response.status_code == 400
    assert "password" in response.data["error"]["details"]


def test_registration_rejects_case_insensitive_duplicate_email(api_client, user):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "newuser",
            "email": "ALICE@EXAMPLE.COM",
            "password": "Difficult-Pass-394!",
        },
    )
    assert response.status_code == 400


def test_session_login_logout_and_csrf(user):
    client = APIClient(enforce_csrf_checks=True)
    credentials = {"username": user.username, "password": "SafePassword-493!abc"}
    assert client.post("/api/v1/auth/login/", credentials).status_code == 403
    response = client.post("/api/v1/auth/login/", credentials, HTTP_X_CSRFTOKEN=csrf(client))
    assert response.status_code == 200
    assert client.get("/api/v1/auth/me/").data["id"] == user.pk
    assert client.post("/api/v1/auth/logout/").status_code == 403
    assert client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=csrf(client)).status_code == 204
    assert client.get("/api/v1/auth/me/").status_code == 403


def test_register_requires_csrf():
    client = APIClient(enforce_csrf_checks=True)
    assert client.post("/api/v1/auth/register/", {}).status_code == 403


def test_inactive_user_cannot_login(api_client, user):
    user.is_active = False
    user.save()
    response = api_client.post(
        "/api/v1/auth/login/",
        {
            "username": user.username,
            "password": "SafePassword-493!abc",
        },
    )
    assert response.status_code == 403


def test_me_cannot_change_email_or_permissions(authenticated_client, user):
    response = authenticated_client.patch(
        "/api/v1/auth/me/",
        {
            "first_name": "Alice",
            "email": "changed@example.com",
            "is_staff": True,
        },
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Alice"
    assert user.email == "alice@example.com"
    assert not user.is_staff


def test_password_reset_response_does_not_reveal_account(api_client, user):
    known = api_client.post("/api/v1/auth/password-reset/", {"email": user.email})
    unknown = api_client.post("/api/v1/auth/password-reset/", {"email": "unknown@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.data == unknown.data
    assert len(mail.outbox) == 1


def test_password_reset_token_is_single_use(api_client, user):
    api_client.post("/api/v1/auth/password-reset/", {"email": user.email})
    uid, token = re.search(r"/accounts/reset/([^/]+)/([^/]+)/", mail.outbox[0].body).groups()
    payload = {"uid": uid, "token": token, "password": "Updated-Pass-472!safe"}
    response = api_client.post("/api/v1/auth/password-reset/confirm/", payload)
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(payload["password"])
    assert api_client.post("/api/v1/auth/password-reset/confirm/", payload).status_code == 400


def test_password_reset_rejects_forged_token(api_client, user):
    response = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "uid": "MQ",
            "token": "invalid",
            "password": "Updated-Pass-472!safe",
        },
    )
    assert response.status_code == 400


def test_browser_reset_form_and_success_page(api_client, user):
    api_client.post("/api/v1/auth/password-reset/", {"email": user.email})
    uid, token = re.search(r"/accounts/reset/([^/]+)/([^/]+)/", mail.outbox[0].body).groups()
    response = api_client.get(f"/accounts/reset/{uid}/{token}/", follow=True)
    assert response.status_code == 200
    response = api_client.post(
        f"/accounts/reset/{uid}/set-password/",
        {
            "new_password1": "Updated-Pass-472!safe",
            "new_password2": "Updated-Pass-472!safe",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert b"Password updated" in response.content


def test_axes_locks_repeated_failures(api_client, user, settings):
    settings.AXES_ENABLED = True
    settings.AXES_FAILURE_LIMIT = 2
    bad = {"username": user.username, "password": "incorrect"}
    assert api_client.post("/api/v1/auth/login/", bad).status_code == 403
    assert api_client.post("/api/v1/auth/login/", bad).status_code == 429
    response = api_client.post(
        "/api/v1/auth/login/",
        {
            "username": user.username,
            "password": "SafePassword-493!abc",
        },
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "login_locked"
