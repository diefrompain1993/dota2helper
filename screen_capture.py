"""Screen capture helper around configured regions."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from paths import BASE_PATH

try:
    from mss import mss
except ImportError as exc:  # pragma: no cover - import guard
    raise RuntimeError("The 'mss' package is required for screen capture.") from exc

CONFIG_PATH = BASE_PATH / "config" / "regions.json"

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_regions() -> Dict[str, Dict[str, int]]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Region config not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        regions = json.load(f)
    return regions


def capture_region(region_name: str) -> Optional[np.ndarray]:
    """Capture a configured screen region using mss.

    Args:
        region_name: Name of the region defined in config/regions.json.

    Returns:
        numpy array in BGR order compatible with OpenCV.
    """
    regions = _load_regions()
    if region_name not in regions:
        logger.error("Region '%s' not found in regions.json", region_name)
        return None

    monitor = regions[region_name]
    if monitor.get("width", 0) <= 0 or monitor.get("height", 0) <= 0:
        logger.error("Invalid region size for '%s': %s", region_name, monitor)
        return None

    with mss() as sct:
        screenshot = sct.grab(monitor)
    img = np.array(screenshot)
    # mss returns BGRA; drop alpha channel for OpenCV compatibility
    if img.shape[2] == 4:
        img = img[:, :, :3]
    logger.debug("Captured region %s with shape %s", region_name, img.shape)
    return img


__all__ = ["capture_region"]
