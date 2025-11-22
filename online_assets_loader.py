"""Fetch a single bundled archive of hero/item assets instead of per-icon CDN requests."""
from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import requests

from paths import BASE_PATH

logger = logging.getLogger(__name__)

# Paths
ROOT = BASE_PATH
ASSETS_DIR = ROOT / "assets"
HERO_DIR = ASSETS_DIR / "heroes"
ITEM_DIR = ASSETS_DIR / "items"

# Remote bundle that contains the full heroes/items icon set.
ASSET_BUNDLE_URL = (
    "https://raw.githubusercontent.com/diefrompain1993/dota2helper-assets/main/dota_assets.zip"
)
BUNDLE_FILENAME = "dota_assets.zip"
BUNDLE_TIMEOUT = 30


def _ensure_directories() -> None:
    HERO_DIR.mkdir(parents=True, exist_ok=True)
    ITEM_DIR.mkdir(parents=True, exist_ok=True)


def _dir_missing_or_empty(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        return next(path.iterdir(), None) is None
    except OSError as exc:  # pragma: no cover - filesystem error guard
        logger.warning("Failed to inspect directory %s: %s", path, exc)
        return True


def _download_bundle(dest: Path) -> bool:
    """Download the zipped asset bundle to ``dest``."""

    logger.info("Downloading asset bundle from %s", ASSET_BUNDLE_URL)
    try:
        resp = requests.get(ASSET_BUNDLE_URL, timeout=BUNDLE_TIMEOUT)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        logger.info("Asset bundle downloaded to %s", dest)
        return True
    except Exception as exc:  # noqa: BLE001 - network/IO guard
        logger.error("Failed to download asset bundle: %s", exc)
        return False


def _extract_bundle(zip_path: Path, target_root: Path) -> bool:
    logger.info("Extracting asset bundle from %s", zip_path)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target_root)
        logger.info("Asset bundle extracted into %s", target_root)
        return True
    except Exception as exc:  # noqa: BLE001 - extraction guard
        logger.error("Failed to extract asset bundle %s: %s", zip_path, exc)
        return False


def update_assets() -> None:
    """Ensure hero/item icons exist locally by downloading a single bundle if needed."""

    _ensure_directories()
    heroes_missing = _dir_missing_or_empty(HERO_DIR)
    items_missing = _dir_missing_or_empty(ITEM_DIR)

    if not (heroes_missing or items_missing):
        logger.info("Assets already present; skipping bundle download")
        return

    bundle_path = ROOT / BUNDLE_FILENAME

    if bundle_path.exists():
        try:
            bundle_path.unlink()
        except OSError:
            logger.warning("Could not remove existing bundle at %s; reusing it", bundle_path)

    if not _download_bundle(bundle_path):
        logger.warning("Proceeding without refreshing assets because bundle download failed")
        return

    if not _extract_bundle(bundle_path, ROOT):
        logger.warning("Proceeding without refreshed assets because extraction failed")
    else:
        logger.info("Assets loaded from local bundle successfully")

    try:
        bundle_path.unlink()
    except OSError:
        logger.debug("Temporary bundle file %s could not be removed", bundle_path)


__all__ = ["update_assets"]
