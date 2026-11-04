import os
from datetime import UTC, datetime, timedelta

import pytest

from e2x_hub_announcements.models import Announcement

# jupyterhub_fastapi_adapter reads these when it is imported, so they must be set
# before any test imports e2x_hub_announcements.service.
os.environ.setdefault("JUPYTERHUB_API_URL", "http://hub.invalid/hub/api")
os.environ.setdefault("JUPYTERHUB_API_TOKEN", "test-token")
os.environ.setdefault("JUPYTERHUB_SERVICE_PREFIX", "/services/announcements/")


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
