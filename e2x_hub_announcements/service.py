"""FastAPI app for managing announcements, run as a JupyterHub managed service.

Run with ``uvicorn e2x_hub_announcements.service:app``. Access is limited to
users with ``access:services!service=announcements``.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from jupyterhub.utils import url_path_join
from jupyterhub_fastapi_adapter import (
    AuthenticationRequired,
    User,
    authentication_required_handler,
    oauth_callback,
    require_authenticated_user,
)
from pydantic import BaseModel

from . import store
from .__about__ import __version__
from ._data import SERVICE_TEMPLATE_PATH
from .hub_page import STOCK_TEMPLATE_PATH, hub_page_context
from .models import ALLOWED_TAGS, Announcement, AnnouncementCreate, Page, Severity
from .render import render_banner
from .settings import ServiceSettings

# ── Config ────────────────────────────────────────────────────────────
settings = ServiceSettings()
service_prefix = settings.service_prefix.rstrip("/")
api_prefix = f"{service_prefix}/api"

CurrentUser = Annotated[User, Depends(require_authenticated_user)]

# ── Jinja2 environment for the admin UI ──────────────────────────────
# Our templates first, then JupyterHub's stock ones, so pages can extend "page.html".
jinja_env = Environment(
    loader=ChoiceLoader(
        [FileSystemLoader(SERVICE_TEMPLATE_PATH), FileSystemLoader(STOCK_TEMPLATE_PATH)]
    ),
    autoescape=True,
)

# ── FastAPI application ──────────────────────────────────────────────
app = FastAPI(
    title="E2X Hub Announcements API",
    version=__version__,
    openapi_url=f"{service_prefix}/openapi.json",
    docs_url=f"{service_prefix}/docs",
    redoc_url=None,
)

app.exception_handler(AuthenticationRequired)(authentication_required_handler)
app.get(url_path_join(service_prefix, "oauth_callback"))(oauth_callback)


class Preview(BaseModel):
    html: str


def _find(announcements: list[Announcement], announcement_id: str) -> Announcement:
    for announcement in announcements:
        if announcement.id == announcement_id:
            return announcement
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Announcement not found")


# ── API ──────────────────────────────────────────────────────────────
# All endpoints are `async def` on purpose. FastAPI runs plain `def` endpoints in a
# thread pool, where two requests could interleave their load → change → save of the
# store and lose an update. `async def` endpoints without `await` run one at a time
# on the event loop; the store is small, so blocking it briefly is fine.


@app.get(f"{api_prefix}/announcements")
async def list_announcements(user: CurrentUser) -> list[Announcement]:
    """All announcements, active and expired, newest first."""
    announcements = store.load(settings.store_path)
    return sorted(announcements, key=lambda a: a.created_at, reverse=True)


@app.post(f"{api_prefix}/announcements", status_code=status.HTTP_201_CREATED)
async def create_announcement(data: AnnouncementCreate, user: CurrentUser) -> Announcement:
    if data.expires_at <= datetime.now(UTC):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "expires_at is in the past")
    announcement = Announcement(**data.model_dump(), created_by=user.username)
    announcements = store.load(settings.store_path)
    announcements.append(announcement)
    store.save(settings.store_path, announcements)
    return announcement


@app.post(f"{api_prefix}/announcements/{{announcement_id}}/end")
async def end_announcement(announcement_id: str, user: CurrentUser) -> Announcement:
    """Expire an announcement now. Already expired ones are left unchanged."""
    announcements = store.load(settings.store_path)
    announcement = _find(announcements, announcement_id)
    now = datetime.now(UTC)
    if announcement.is_active(now):
        announcement.expires_at = now
        store.save(settings.store_path, announcements)
    return announcement


@app.delete(
    f"{api_prefix}/announcements/{{announcement_id}}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_announcement(announcement_id: str, user: CurrentUser) -> None:
    announcements = store.load(settings.store_path)
    announcements.remove(_find(announcements, announcement_id))
    store.save(settings.store_path, announcements)


@app.post(f"{api_prefix}/preview")
async def preview(data: AnnouncementCreate, user: CurrentUser) -> Preview:
    """Render the banner exactly as the hub will, without saving it."""
    return Preview(html=render_banner(data))


# ── Admin UI ─────────────────────────────────────────────────────────
# Shown next to each page checkbox, so admins know where a banner will appear.
PAGE_DESCRIPTIONS = {
    Page.spawn: "Where users choose and start their server.",
    Page.home: "The hub's home page, where users start, stop or open their server.",
    Page.login: "The login page. Visible to everyone, even before logging in.",
    Page.logout: "The page shown right after logging out.",
}


def admin_ui_context(user: User) -> dict:
    """Template variables for index.j2: the hub's page variables plus our own."""
    return hub_page_context(user, settings.hub_base_url) | {
        "api_url": api_prefix,
        "pages": list(Page),
        "page_descriptions": PAGE_DESCRIPTIONS,
        "severities": list(Severity),
        "allowed_tags": sorted(ALLOWED_TAGS),
    }


@app.get(f"{service_prefix}/", include_in_schema=False, response_class=HTMLResponse)
async def admin_ui(user: CurrentUser) -> HTMLResponse:
    """The admin page: form, preview and list, talking to the API above."""
    html = jinja_env.get_template("index.j2").render(admin_ui_context(user))
    return HTMLResponse(content=html)
