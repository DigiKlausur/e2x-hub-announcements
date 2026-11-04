from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment, StrictUndefined
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


def test_admin_ui_renders(client):
    response = client.get("/services/announcements/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert f'const API = "{API}";' in html
    assert 'href="/hub/static/css/style.min.css"' in html
    for page in ("spawn", "login", "home", "logout"):
        assert f'id="page-{page}"' in html
    # The hub navbar from JupyterHub's page.html
    assert 'href="/hub/home"' in html
    assert 'href="/hub/admin"' in html
    assert '<span class="me-1">admin</span>' in html


def test_admin_ui_hides_admin_link_for_non_admins():
    context = service.admin_ui_context(User(username="potato", admin=False))
    html = service.jinja_env.get_template("index.j2").render(context)
    assert 'href="/hub/home"' in html
    assert 'href="/hub/admin"' not in html


def test_admin_ui_provides_every_variable_hub_page_html_needs():
    # Renders against the installed JupyterHub templates and fails on any missing
    # variable, so a JupyterHub upgrade that needs a new one breaks this test, not the page.
    strict = Environment(
        loader=service.jinja_env.loader, autoescape=True, undefined=StrictUndefined
    )
    strict.get_template("index.j2").render(service.admin_ui_context(User(username="admin")))
