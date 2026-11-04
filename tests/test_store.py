import json

import pytest
from pydantic import ValidationError

from e2x_hub_announcements import store


def test_missing_file_gives_empty_list(tmp_path):
    assert store.load(tmp_path / "announcements.json") == []


def test_round_trip(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    items = [make_announcement(), make_announcement(severity="info", pages=["login"])]
    store.save(path, items)
    assert store.load(path) == items


def test_times_are_stored_as_utc(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    store.save(path, [make_announcement()])
    [raw] = json.loads(path.read_text())
    assert raw["expires_at"].endswith("Z")
    assert raw["created_at"].endswith("Z")


def test_save_replaces_content_and_leaves_no_temp_file(tmp_path, make_announcement):
    path = tmp_path / "announcements.json"
    store.save(path, [make_announcement()])
    store.save(path, [])
    assert store.load(path) == []
    assert list(tmp_path.iterdir()) == [path]


def test_corrupt_file_raises(tmp_path):
    path = tmp_path / "announcements.json"
    path.write_text("{not json")
    with pytest.raises(ValidationError):
        store.load(path)
