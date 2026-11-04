"""Let service pages extend JupyterHub's stock ``page.html``.

The service runs in the hub pod, so JupyterHub's templates are installed. Our
pages ``{% extends "page.html" %}`` to get the real hub navbar and styles. That
template expects variables the hub normally provides; ``hub_page_context``
supplies them.

Checked against JupyterHub 5.4. If an upgrade needs a new variable,
``tests/test_service.py`` fails, because it renders with ``StrictUndefined``.
"""

import json
import os
from types import SimpleNamespace

from jupyterhub._data import DATA_FILES_PATH as JUPYTERHUB_DATA_FILES_PATH
from jupyterhub.utils import url_path_join
from jupyterhub_fastapi_adapter import User

STOCK_TEMPLATE_PATH = os.path.join(JUPYTERHUB_DATA_FILES_PATH, "templates")


def hub_page_context(user: User, hub_base_url: str) -> dict:
    """Template variables for rendering a page that extends the stock ``page.html``."""
    hub_prefix = url_path_join(hub_base_url, "hub/")

    def static_url(path: str, include_version: bool = True) -> str:
        # The hub serves its static files; the browser loads them from there.
        return url_path_join(hub_prefix, "static", path)

    return {
        "base_url": hub_prefix,
        "prefix": hub_base_url,
        "static_url": static_url,
        "version_hash": "",
        "logo_url": "",
        "login_url": url_path_join(hub_prefix, "login"),
        "logout_url": url_path_join(hub_prefix, "logout"),
        "user": SimpleNamespace(
            name=user.username, json_escaped_name=json.dumps(user.username)[1:-1]
        ),
        "admin_access": user.admin,
        # Only decides whether the navbar shows the Admin link. The adapter's User
        # has no scopes, so approximate: hub admins have admin-ui.
        "parsed_scopes": {"admin-ui"} if user.admin else set(),
        # The user's service list isn't available here, so no Services dropdown.
        "services": [],
        # Skip page.html's check of user.spawner.options_form.
        "no_spawner_check": True,
        # Only used by the hub's own JavaScript, which this page doesn't call.
        "xsrf_token": "",
        "announcement": None,
    }
