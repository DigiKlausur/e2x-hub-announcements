"""Render announcements to banner HTML.

Used by both the hub integration and the service preview, so admins see exactly
what users will see.
"""

from collections.abc import Iterable
from datetime import UTC, datetime

from .models import Announcement, AnnouncementCreate, Page, Severity

ALERT_CLASSES = {
    Severity.info: "alert-info",
    Severity.warning: "alert-warning",
    Severity.alert: "alert-danger",
}

# Lower comes first: the most severe banner is shown on top.
_SEVERITY_ORDER = {Severity.alert: 0, Severity.warning: 1, Severity.info: 2}


def render_banner(announcement: AnnouncementCreate) -> str:
    """Render one announcement. Its message is already sanitized by the model."""
    css = f"container text-center announcement alert {ALERT_CLASSES[announcement.severity]}"
    return f'<div class="{css}" role="alert">{announcement.message}</div>'


def render_page(
    announcements: Iterable[Announcement], page: Page, now: datetime | None = None
) -> str | None:
    """Render all active announcements for ``page``, most severe (then newest) first.

    Returns ``None`` when there is nothing to show, which the stock JupyterHub
    templates treat as "no announcement".
    """
    now = now or datetime.now(UTC)
    visible = [a for a in announcements if page in a.pages and a.is_active(now)]
    if not visible:
        return None
    visible.sort(key=lambda a: (_SEVERITY_ORDER[a.severity], -a.created_at.timestamp()))
    return "\n".join(render_banner(a) for a in visible)
