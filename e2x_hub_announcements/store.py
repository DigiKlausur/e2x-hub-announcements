"""JSON file store for announcements.

The service writes the file; the hub reads it on every page render. Writes go to
a temp file that is then moved over the store with ``os.replace``, so a reader
sees either the old or the new file, never a half-written one.
"""

import contextlib
import os
import tempfile
from pathlib import Path

from pydantic import TypeAdapter

from .models import Announcement

_announcements = TypeAdapter(list[Announcement])


def load(path: str | Path) -> list[Announcement]:
    """Read all announcements. A missing file means no announcements.

    A corrupt file raises ``pydantic.ValidationError`` rather than returning an
    empty list, so the service never overwrites history it couldn't read.
    """
    try:
        data = Path(path).read_bytes()
    except FileNotFoundError:
        return []
    return _announcements.validate_json(data)


def save(path: str | Path, announcements: list[Announcement]) -> None:
    """Atomically replace the store with ``announcements``."""
    path = Path(path)
    # Same directory as the target: os.replace is only atomic within one filesystem.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(_announcements.dump_json(announcements, indent=2))
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise
