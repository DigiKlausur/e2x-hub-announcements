from datetime import UTC, datetime, timedelta

import pytest

from e2x_hub_announcements.models import AnnouncementCreate, Page
from e2x_hub_announcements.render import render_banner, render_page

NOW = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("severity", "css"),
    [("info", "alert-info"), ("warning", "alert-warning"), ("alert", "alert-danger")],
)
def test_banner_uses_severity_class(make_announcement, severity, css):
    html = render_banner(make_announcement(severity=severity, message="Hi"))
    assert html == (
        f'<div class="container text-center announcement alert {css}" role="alert">Hi</div>'
    )


def test_banner_renders_unsaved_announcement():
    # The service preview renders announcements that are not stored yet.
    draft = AnnouncementCreate(
        message="Draft", pages=["login"], severity="info", expires_at=NOW + timedelta(days=1)
    )
    assert "Draft" in render_banner(draft)


def test_no_announcements_gives_none():
    assert render_page([], Page.spawn, NOW) is None


def test_only_targeted_page_is_shown(make_announcement):
    a = make_announcement(pages=["login"], expires_at=NOW + timedelta(days=1))
    assert render_page([a], Page.login, NOW) is not None
    assert render_page([a], Page.spawn, NOW) is None


def test_expired_announcement_is_hidden(make_announcement):
    a = make_announcement(pages=["spawn"], expires_at=NOW - timedelta(seconds=1))
    assert render_page([a], Page.spawn, NOW) is None


def test_most_severe_first_then_newest(make_announcement):
    expires = NOW + timedelta(days=1)
    old_info = make_announcement(
        message="MSG1", severity="info", expires_at=expires, created_at=NOW - timedelta(2)
    )
    new_info = make_announcement(
        message="MSG2", severity="info", expires_at=expires, created_at=NOW - timedelta(1)
    )
    alert = make_announcement(
        message="MSG3", severity="alert", expires_at=expires, created_at=NOW - timedelta(3)
    )
    html = render_page([old_info, new_info, alert], Page.spawn, NOW)
    # Expected: alert (MSG3), then the newer info (MSG2), then the older info (MSG1).
    order = [html.index(m) for m in ("MSG3", "MSG2", "MSG1")]
    assert order == sorted(order)
