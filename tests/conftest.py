from datetime import UTC, datetime, timedelta

import pytest

from e2x_hub_announcements.models import Announcement


@pytest.fixture
def make_announcement():
    """Build a valid announcement; override any field via keyword arguments."""

    def factory(**overrides) -> Announcement:
        fields = {
            "message": "<strong>Maintenance</strong> tonight.",
            "pages": ["spawn", "home"],
            "severity": "warning",
            "expires_at": datetime.now(UTC) + timedelta(days=1),
            "created_by": "admin",
        }
        return Announcement(**(fields | overrides))

    return factory
