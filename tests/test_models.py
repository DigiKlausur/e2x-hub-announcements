from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError


def test_allowed_tags_are_kept(make_announcement):
    html = "<p><strong>a</strong> <em>b</em> <code>c</code></p><ul><li>d</li></ul>"
    assert make_announcement(message=html).message == html


def test_script_is_removed(make_announcement):
    a = make_announcement(message="<script>alert(1)</script>Hello")
    assert a.message == "Hello"


def test_disallowed_attributes_are_removed(make_announcement):
    a = make_announcement(message='<p onclick="evil()">Hi</p>')
    assert a.message == "<p>Hi</p>"


def test_link_href_is_kept(make_announcement):
    a = make_announcement(message='<a href="https://example.org">docs</a>')
    assert 'href="https://example.org"' in a.message


def test_message_empty_after_sanitizing_is_rejected(make_announcement):
    with pytest.raises(ValidationError):
        make_announcement(message="<script>alert(1)</script>")


def test_empty_pages_are_rejected(make_announcement):
    with pytest.raises(ValidationError):
        make_announcement(pages=[])


def test_naive_expiry_is_rejected(make_announcement):
    with pytest.raises(ValidationError):
        make_announcement(expires_at=datetime(2026, 11, 18, 12, 0))


def test_expiry_is_converted_to_utc(make_announcement):
    berlin = datetime(2026, 11, 18, 12, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    a = make_announcement(expires_at=berlin)
    assert a.expires_at == datetime(2026, 11, 18, 11, 0, tzinfo=UTC)
    assert a.expires_at.utcoffset() == timedelta(0)


def test_is_active(make_announcement):
    now = datetime.now(UTC)
    a = make_announcement(expires_at=now + timedelta(minutes=1))
    assert a.is_active(now)
    assert not a.is_active(now + timedelta(minutes=2))
