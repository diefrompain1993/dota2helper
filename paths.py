"""Utilities for resolving runtime base paths (supports PyInstaller)."""
from __future__ import annotations

import sys
from pathlib import Path


def get_base_path() -> Path:
    """Return the directory where bundled assets/configs live.

    When frozen with PyInstaller, data files are unpacked into ``sys._MEIPASS``.
    Otherwise we use the repository root (the directory containing this file).
    """

    if getattr(sys, "frozen", False):  # pragma: no cover - runtime packaging branch
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent


BASE_PATH = get_base_path()


__all__ = ["BASE_PATH", "get_base_path"]
