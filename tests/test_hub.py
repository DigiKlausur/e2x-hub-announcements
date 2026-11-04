from traitlets.config import Config

from e2x_hub_announcements import store
from e2x_hub_announcements._data import JUPYTERHUB_TEMPLATE_PATH
from e2x_hub_announcements.hub import configure_announcements

PAGES = ("spawn", "login", "home", "logout")


def resolve(value, initial):
    """On a fresh Config, traitlets records changes lazily; resolve them like the hub does."""
    return value.get_value(initial) if hasattr(value, "get_value") else value


def configured(store_path, c=None) -> Config:
    c = c or Config()
    configure_announcements(c, store_path=str(store_path))
    return c


def template_vars(store_path, c=None) -> dict:
    return resolve(configured(store_path, c).JupyterHub.template_vars, {})


def test_registers_a_callable_per_page(tmp_path):
    tv = template_vars(tmp_path / "announcements.json")
    assert {f"announcement_{p}" for p in PAGES} <= tv.keys()
    assert all(callable(tv[f"announcement_{p}"]) for p in PAGES)


def test_keeps_existing_template_vars(tmp_path):
    c = Config()
    c.JupyterHub.template_vars = {"username_label": "Username"}
    assert template_vars(tmp_path / "announcements.json", c)["username_label"] == "Username"


def test_callable_renders_from_store(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    store.save(path, [make_announcement(message="Hello", pages=["spawn"])])
    tv = template_vars(path)
    assert "Hello" in tv["announcement_spawn"](None)
    assert tv["announcement_login"](None) is None


def test_store_is_read_on_every_call(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    announcement_spawn = template_vars(path)["announcement_spawn"]
    assert announcement_spawn(None) is None
    store.save(path, [make_announcement(message="New", pages=["spawn"])])
    assert "New" in announcement_spawn(None)


def test_missing_store_gives_none(tmp_path):
    assert template_vars(tmp_path / "missing.json")["announcement_spawn"](None) is None


def test_corrupt_store_gives_none(tmp_path):
    path = tmp_path / "announcements.json"
    path.write_text("{not json")
    assert template_vars(path)["announcement_spawn"](None) is None


def test_template_dir_is_first(tmp_path):
    c = configured(tmp_path / "announcements.json")
    assert resolve(c.JupyterHub.template_paths, [])[0] == JUPYTERHUB_TEMPLATE_PATH


def test_keeps_existing_template_paths(tmp_path):
    c = Config()
    c.JupyterHub.template_paths = ["/other/templates"]
    configured(tmp_path / "announcements.json", c)
    assert c.JupyterHub.template_paths == [JUPYTERHUB_TEMPLATE_PATH, "/other/templates"]
