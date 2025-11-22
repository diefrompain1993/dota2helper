"""Screen capture helper around configured regions."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

import numpy as np
from mss import mss

CONFIG_PATH = Path(__file__).parent / "config" / "regions.json"


@lru_cache(maxsize=1)
def _load_regions() -> Dict[str, Dict[str, int]]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Region config not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        regions = json.load(f)
    return regions


def capture_region(region_name: str) -> np.ndarray:
    """Capture a configured screen region using mss.

    Args:
        region_name: Name of the region defined in config/regions.json.

    Returns:
        numpy array in BGR order compatible with OpenCV.
    """
    regions = _load_regions()
    if region_name not in regions:
        raise KeyError(f"Region '{region_name}' not defined in regions.json")

    monitor = regions[region_name]
    with mss() as sct:
        screenshot = sct.grab(monitor)
    img = np.array(screenshot)
    # mss returns BGRA; drop alpha channel for OpenCV compatibility
    if img.shape[2] == 4:
        img = img[:, :, :3]
    return img


__all__ = ["capture_region"]
