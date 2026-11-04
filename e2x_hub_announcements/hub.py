"""JupyterHub integration, used from ``jupyterhub_config.py`` / ``hub.extraConfig``.

Example::

    from e2x_hub_announcements.hub import configure_announcements
    configure_announcements(c, store_path="/srv/jupyterhub/announcements.json")
"""

import logging
from collections.abc import Callable

from . import store
from ._data import JUPYTERHUB_TEMPLATE_PATH
from .models import Page
from .render import render_page

DEFAULT_STORE_PATH = "/srv/jupyterhub/announcements.json"

# The hub's own logger, so errors show up in the normal hub log output.
log = logging.getLogger("JupyterHub")


def _announcement_for(page: Page, store_path: str) -> Callable[[object], str | None]:
    """Build the ``template_vars`` callable for one page.

    JupyterHub calls it with the current user (``None`` on the login page) on
    every render. Any error yields ``None``: announcements must never stop the
    hub from rendering a page.
    """

    def announcement(user=None) -> str | None:
        try:
            return render_page(store.load(store_path), page)
        except Exception:
            log.exception("Could not render %s announcements from %s", page, store_path)
            return None

    return announcement


def configure_announcements(c, store_path: str = DEFAULT_STORE_PATH) -> None:
    """Register ``announcement_<page>`` template variables for every page.

    Uses ``update`` so existing ``template_vars`` (e.g. ``username_label``) are kept.

    Also puts the package's ``page.html`` override first in ``template_paths`` so
    banners render with their severity colour. Config that runs later must add to
    ``template_paths`` (``append`` / ``+=``), not assign it, or the override is lost.
    """
    c.JupyterHub.template_vars.update(
        {f"announcement_{page}": _announcement_for(page, store_path) for page in Page}
    )
    c.JupyterHub.template_paths.insert(0, JUPYTERHUB_TEMPLATE_PATH)
