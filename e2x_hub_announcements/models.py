"""Announcement data model.

Messages are sanitized and times normalized to UTC during validation, so every
announcement that exists as a model instance is safe to store and render.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

import nh3
from pydantic import AwareDatetime, BaseModel, Field, field_validator

ALLOWED_TAGS = {"a", "strong", "em", "p", "br", "ul", "ol", "li", "code"}
ALLOWED_ATTRIBUTES = {"a": {"href"}}


class Page(StrEnum):
    """Hub pages an announcement can target (stock ``announcement_<page>`` variables)."""

    spawn = "spawn"
    login = "login"
    home = "home"
    logout = "logout"


class Severity(StrEnum):
    """Banner severity, mapped to a Bootstrap alert class when rendering."""

    info = "info"
    warning = "warning"
    alert = "alert"


def sanitize(html: str) -> str:
    """Strip everything from ``html`` except the allow-listed tags and attributes."""
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)


class AnnouncementCreate(BaseModel):
    """The fields an admin provides when creating an announcement."""

    message: str = Field(min_length=1)
    pages: list[Page] = Field(min_length=1)
    severity: Severity
    expires_at: AwareDatetime

    @field_validator("message")
    @classmethod
    def _sanitize_message(cls, value: str) -> str:
        cleaned = sanitize(value).strip()
        if not cleaned:
            raise ValueError("message is empty after sanitizing")
        return cleaned

    @field_validator("expires_at")
    @classmethod
    def _to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class Announcement(AnnouncementCreate):
    """A stored announcement."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str

    def is_active(self, now: datetime | None = None) -> bool:
        """Whether the announcement has not yet expired."""
        return self.expires_at > (now or datetime.now(UTC))
