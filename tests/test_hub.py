from traitlets.config import Config

from e2x_hub_announcements import store
from e2x_hub_announcements.hub import configure_announcements

PAGES = ("spawn", "login", "home", "logout")


def configured(store_path, c=None) -> dict:
    """Run configure_announcements and return the resulting template_vars dict."""
    c = c or Config()
    configure_announcements(c, store_path=str(store_path))
    value = c.JupyterHub.template_vars
    # On a fresh Config, traitlets records `update` lazily and merges it at hub startup.
    return value.get_value({}) if hasattr(value, "get_value") else value


def test_registers_a_callable_per_page(tmp_path):
    template_vars = configured(tmp_path / "announcements.json")
    assert {f"announcement_{p}" for p in PAGES} <= template_vars.keys()
    assert all(callable(template_vars[f"announcement_{p}"]) for p in PAGES)


def test_keeps_existing_template_vars(tmp_path):
    c = Config()
    c.JupyterHub.template_vars = {"username_label": "Username"}
    template_vars = configured(tmp_path / "announcements.json", c)
    assert template_vars["username_label"] == "Username"


def test_callable_renders_from_store(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    store.save(path, [make_announcement(message="Hello", pages=["spawn"])])
    template_vars = configured(path)
    assert "Hello" in template_vars["announcement_spawn"](None)
    assert template_vars["announcement_login"](None) is None


def test_store_is_read_on_every_call(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    announcement_spawn = configured(path)["announcement_spawn"]
    assert announcement_spawn(None) is None
    store.save(path, [make_announcement(message="New", pages=["spawn"])])
    assert "New" in announcement_spawn(None)


def test_missing_store_gives_none(tmp_path):
    assert configured(tmp_path / "missing.json")["announcement_spawn"](None) is None


def test_corrupt_store_gives_none(tmp_path):
    path = tmp_path / "announcements.json"
    path.write_text("{not json")
    assert configured(path)["announcement_spawn"](None) is None
