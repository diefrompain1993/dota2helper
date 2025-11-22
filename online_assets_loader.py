"""Download heroes/items metadata and icons from OpenDota/Valve CDN automatically."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from paths import BASE_PATH

logger = logging.getLogger(__name__)

ROOT = BASE_PATH
ASSETS_DIR = ROOT / "assets"
HERO_DIR = ASSETS_DIR / "heroes"
ITEM_DIR = ASSETS_DIR / "items"
DATA_DIR = ROOT / "data"

HEROES_URL = "https://api.opendota.com/api/heroes"
ITEMS_URL = "https://api.opendota.com/api/constants/items"
HERO_ICON_URL = "http://cdn.dota2.com/apps/dota2/images/heroes/{name}_icon.png"
ITEM_ICON_URL = "http://cdn.dota2.com/apps/dota2/images/items/{name}_lg.png"


def _ensure_directories() -> None:
    HERO_DIR.mkdir(parents=True, exist_ok=True)
    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _fetch_json(url: str):
    logger.debug("Fetching JSON from %s", url)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:  # nosec: B310
            return json.load(response)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed fetching JSON from %s: %s", url, exc)
        return None


def download_image(url: str, path: Path) -> bool:
    """Download a single image to the given path."""
    try:
        logger.debug("Downloading %s -> %s", url, path)
        with urllib.request.urlopen(url) as response:  # nosec: B310
            data = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return True
    except urllib.error.URLError as exc:  # pragma: no cover - network guard
        logger.warning("Failed to download %s: %s", url, exc)
        return False


def _hero_name(hero_entry: Dict[str, object]) -> str:
    raw_name = str(hero_entry.get("name", ""))
    return raw_name.replace("npc_dota_hero_", "")


def download_heroes() -> Tuple[List[Dict[str, object]], int]:
    """Download heroes.json and all hero icons."""
    _ensure_directories()
    heroes: List[Dict[str, object]] = _fetch_json(HEROES_URL)
    if not heroes:
        logger.warning("Heroes metadata could not be fetched. Using existing local files.")
        return [], 0
    (DATA_DIR / "heroes.json").write_text(
        json.dumps(heroes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    downloaded = 0
    for hero in heroes:
        name = _hero_name(hero)
        if not name:
            continue
        dest = HERO_DIR / f"{name}.png"
        if dest.exists():
            continue
        url = HERO_ICON_URL.format(name=name)
        if download_image(url, dest):
            downloaded += 1
    logger.info("Heroes fetched: %d total, %d icons downloaded", len(heroes), downloaded)
    return heroes, downloaded


def _item_image_url(name: str, entry: Dict[str, object]) -> str:
    img = entry.get("img")
    if isinstance(img, str) and img:
        if img.startswith("http"):
            return img
        if img.startswith("/"):
            return urllib.parse.urljoin("http://cdn.dota2.com", img)
    return ITEM_ICON_URL.format(name=name)


def download_items() -> Tuple[Dict[str, object], int]:
    """Download items.json and all item icons."""
    _ensure_directories()
    items: Dict[str, object] = _fetch_json(ITEMS_URL)
    if not items:
        logger.warning("Items metadata could not be fetched. Using existing local files.")
        return {}, 0
    (DATA_DIR / "items.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    downloaded = 0
    for name, entry in items.items():
        dest = ITEM_DIR / f"{name}.png"
        if dest.exists():
            continue
        url = _item_image_url(name, entry if isinstance(entry, dict) else {})
        if download_image(url, dest):
            downloaded += 1
    logger.info("Items fetched: %d total, %d icons downloaded", len(items), downloaded)
    return items, downloaded


def _load_local_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _download_missing_images(entries: Iterable[Tuple[str, Path, str]]) -> int:
    downloaded = 0
    for url, dest, label in entries:
        if dest.exists():
            continue
        if download_image(url, dest):
            downloaded += 1
            logger.debug("Downloaded missing %s -> %s", label, dest)
    return downloaded


def update_assets() -> None:
    """Ensure metadata and icons for heroes/items are present, downloading as needed."""
    _ensure_directories()

    heroes_path = DATA_DIR / "heroes.json"
    items_path = DATA_DIR / "items.json"

    heroes = _load_local_json(heroes_path)
    if heroes is None:
        heroes, fresh_downloads = download_heroes()
    else:
        fresh_downloads = 0
    missing_hero_jobs = []
    if heroes:
        for hero in heroes:
            name = _hero_name(hero)
            if not name:
                continue
            dest = HERO_DIR / f"{name}.png"
            if not dest.exists():
                url = HERO_ICON_URL.format(name=name)
                missing_hero_jobs.append((url, dest, name))
    if missing_hero_jobs:
        fresh_downloads += _download_missing_images(
            (url, dest, label) for url, dest, label in missing_hero_jobs
        )

    items = _load_local_json(items_path)
    if items is None:
        items, item_downloads = download_items()
    else:
        item_downloads = 0
    missing_item_jobs = []
    if isinstance(items, dict):
        for name, entry in items.items():
            dest = ITEM_DIR / f"{name}.png"
            if not dest.exists():
                url = _item_image_url(name, entry if isinstance(entry, dict) else {})
                missing_item_jobs.append((url, dest, name))
    if missing_item_jobs:
        item_downloads += _download_missing_images(
            (url, dest, label) for url, dest, label in missing_item_jobs
        )

    # Cleanup stray icons no longer present in metadata
    hero_valid = {(_hero_name(hero)) for hero in heroes} if heroes else set()
    for fname in HERO_DIR.glob("*.png"):
        label = fname.stem
        if hero_valid and label not in hero_valid:
            try:
                fname.unlink()
                logger.debug("Removed stale hero icon %s", fname)
            except OSError as exc:  # pragma: no cover - filesystem errors
                logger.warning("Failed to remove stale hero icon %s: %s", fname, exc)

    item_valid = set(items.keys()) if isinstance(items, dict) else set()
    for fname in ITEM_DIR.glob("*.png"):
        label = fname.stem
        if item_valid and label not in item_valid:
            try:
                fname.unlink()
                logger.debug("Removed stale item icon %s", fname)
            except OSError as exc:  # pragma: no cover
                logger.warning("Failed to remove stale item icon %s: %s", fname, exc)

    logger.info(
        "Assets ready: heroes=%d (missing downloaded=%d), items=%d (missing downloaded=%d)",
        len(heroes) if heroes else 0,
        fresh_downloads,
        len(items) if isinstance(items, dict) else 0,
        item_downloads,
    )


__all__ = [
    "update_assets",
    "download_heroes",
    "download_items",
    "download_image",
]
