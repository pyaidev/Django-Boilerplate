import pytest

from apps.notes.models import Note

pytestmark = pytest.mark.django_db


def test_anonymous_cannot_access_notes(api_client):
    assert api_client.get("/api/v1/notes/").status_code == 403


def test_create_ignores_forged_owner_and_records_history(authenticated_client, user, other_user):
    response = authenticated_client.post("/api/v1/notes/", {"title": "Private", "owner": other_user.pk})
    assert response.status_code == 201
    note = Note.objects.get(pk=response.data["id"])
    assert note.owner == user
    assert note.history.count() == 1
    assert note.history.first().history_user == user


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_other_users_note_is_inaccessible(authenticated_client, other_user, method):
    note = Note.objects.create(owner=other_user, title="Other user's secret")
    response = getattr(authenticated_client, method)(f"/api/v1/notes/{note.pk}/", {"title": "Changed"})
    assert response.status_code == 404
    note.refresh_from_db()
    assert note.title == "Other user's secret"


def test_list_search_and_filter_never_leak_other_users(authenticated_client, user, other_user):
    Note.objects.create(owner=user, title="Find me", is_archived=True)
    Note.objects.create(owner=user, title="Hidden by filter")
    Note.objects.create(owner=other_user, title="Find me", is_archived=True)
    response = authenticated_client.get("/api/v1/notes/?search=Find&is_archived=true")
    assert response.data["count"] == 1
    assert response.data["results"][0]["owner"] == user.pk


def test_pagination_caps_client_limit(authenticated_client, user):
    Note.objects.bulk_create([Note(owner=user, title=f"Note {i}") for i in range(105)])
    response = authenticated_client.get("/api/v1/notes/?limit=100000")
    assert response.data["count"] == 105
    assert len(response.data["results"]) == 100


def test_update_and_delete_have_history(authenticated_client, user):
    note = Note.objects.create(owner=user, title="Original")
    assert authenticated_client.patch(f"/api/v1/notes/{note.pk}/", {"title": "Edited"}).status_code == 200
    assert note.history.count() == 2
    assert authenticated_client.delete(f"/api/v1/notes/{note.pk}/").status_code == 204
    assert note.history.count() == 3
