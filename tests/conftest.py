import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.fixture(autouse=True)
def isolated_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="alice", email="alice@example.com", password="SafePassword-493!abc"
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="bob", email="bob@example.com", password="SafePassword-493!abc")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
