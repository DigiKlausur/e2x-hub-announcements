from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jupyterhub_fastapi_adapter import User, require_authenticated_user

from e2x_hub_announcements import service
from e2x_hub_announcements.models import AnnouncementCreate
from e2x_hub_announcements.render import render_banner

API = "/services/announcements/api"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A client logged in as 'admin', with the store in a temp dir."""
    monkeypatch.setattr(service.settings, "store_path", str(tmp_path / "announcements.json"))
    service.app.dependency_overrides[require_authenticated_user] = lambda: User(
        username="admin", admin=True
    )
    yield TestClient(service.app)
    service.app.dependency_overrides.clear()


def payload(**overrides) -> dict:
    fields = {
        "message": "<strong>Maintenance</strong> tonight.",
        "pages": ["spawn", "login"],
        "severity": "warning",
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }
    return fields | overrides


def create(client, **overrides) -> dict:
    response = client.post(f"{API}/announcements", json=payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_list(client):
    created = create(client)
    assert created["created_by"] == "admin"
    assert client.get(f"{API}/announcements").json() == [created]


def test_create_sanitizes_message(client):
    created = create(client, message="<script>alert(1)</script>Hi")
    assert created["message"] == "Hi"


def test_create_rejects_past_expiry(client):
    past = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    response = client.post(f"{API}/announcements", json=payload(expires_at=past))
    assert response.status_code == 422


def test_create_rejects_expiry_without_timezone(client):
    response = client.post(f"{API}/announcements", json=payload(expires_at="2099-01-01T12:00:00"))
    assert response.status_code == 422


def test_list_is_newest_first(client):
    first = create(client, message="first")
    second = create(client, message="second")
    ids = [a["id"] for a in client.get(f"{API}/announcements").json()]
    assert ids == [second["id"], first["id"]]


def test_end_expires_announcement(client):
    created = create(client)
    response = client.post(f"{API}/announcements/{created['id']}/end")
    assert response.status_code == 200
    ended_at = datetime.fromisoformat(response.json()["expires_at"])
    assert ended_at <= datetime.now(UTC)
    [stored] = client.get(f"{API}/announcements").json()
    assert stored["expires_at"] == response.json()["expires_at"]


def test_end_unknown_gives_404(client):
    assert client.post(f"{API}/announcements/nope/end").status_code == 404


def test_delete_removes_announcement(client):
    created = create(client)
    assert client.delete(f"{API}/announcements/{created['id']}").status_code == 204
    assert client.get(f"{API}/announcements").json() == []


def test_delete_unknown_gives_404(client):
    assert client.delete(f"{API}/announcements/nope").status_code == 404


def test_preview_matches_hub_render_and_does_not_save(client):
    data = payload(severity="alert")
    response = client.post(f"{API}/preview", json=data)
    assert response.status_code == 200
    assert response.json()["html"] == render_banner(AnnouncementCreate(**data))
    assert client.get(f"{API}/announcements").json() == []
