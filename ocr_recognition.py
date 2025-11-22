"""Template-matching based recognition for heroes and items."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Dict, List

import cv2
import numpy as np

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"
HERO_DIR = ASSETS_DIR / "heroes"
ITEM_DIR = ASSETS_DIR / "items"

HERO_THRESHOLD = 0.7
ITEM_THRESHOLD = 0.65

HERO_TEMPLATES: Dict[str, np.ndarray] = {}
ITEM_TEMPLATES: Dict[str, np.ndarray] = {}
_TEMPLATE_LOCK = Lock()
_hero_cell_cache: Dict[int, str] = {}
_hero_hash_cache: Dict[int, str] = {}
_item_cell_cache: Dict[int, str] = {}
_item_hash_cache: Dict[int, str] = {}


def _load_templates(directory: Path) -> Dict[str, np.ndarray]:
    templates: Dict[str, np.ndarray] = {}
    if not directory.exists():
        logger.warning("Assets directory missing: %s", directory)
        return templates
    for file in directory.iterdir():
        if file.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        img = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.warning("Failed to load template %s", file)
            continue
        templates[file.stem] = img
    return templates


def load_templates() -> None:
    """Load hero and item templates once and cache them globally."""
    with _TEMPLATE_LOCK:
        HERO_TEMPLATES.clear()
        HERO_TEMPLATES.update(_load_templates(HERO_DIR))
        ITEM_TEMPLATES.clear()
        ITEM_TEMPLATES.update(_load_templates(ITEM_DIR))
        _hero_cell_cache.clear()
        _hero_hash_cache.clear()
        _item_cell_cache.clear()
        _item_hash_cache.clear()
    logger.info(
        "Templates loaded: heroes=%d, items=%d", len(HERO_TEMPLATES), len(ITEM_TEMPLATES)
    )


@dataclass
class GridConfig:
    cols: int
    rows: int


HERO_GRID = GridConfig(cols=5, rows=1)
ITEM_GRID = GridConfig(cols=6, rows=5)


def _split_grid(image: np.ndarray, grid: GridConfig) -> List[np.ndarray]:
    cell_height = image.shape[0] // grid.rows
    cell_width = image.shape[1] // grid.cols
    cells: List[np.ndarray] = []
    for row in range(grid.rows):
        for col in range(grid.cols):
            y0 = row * cell_height
            x0 = col * cell_width
            cells.append(image[y0 : y0 + cell_height, x0 : x0 + cell_width])
    return cells


def _hash_cell(cell: np.ndarray) -> str:
    return hashlib.sha1(cell.tobytes()).hexdigest()


def _match_best(cell: np.ndarray, templates: Dict[str, np.ndarray], threshold: float) -> str:
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    best_label = ""
    best_score = 0.0
    for label, tmpl in templates.items():
        if gray.shape[0] < tmpl.shape[0] or gray.shape[1] < tmpl.shape[1]:
            continue
        res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val > best_score:
            best_score = max_val
            best_label = label
    return best_label if best_score >= threshold else ""


def _ensure_templates_loaded() -> None:
    if HERO_TEMPLATES and ITEM_TEMPLATES:
        return
    load_templates()


def detect_enemy_heroes(image: np.ndarray) -> List[str]:
    """Detect enemy heroes from the top bar capture."""
    _ensure_templates_loaded()
    heroes: List[str] = []
    for idx, cell in enumerate(_split_grid(image, HERO_GRID)):
        cell_hash = _hash_cell(cell)
        if _hero_hash_cache.get(idx) == cell_hash:
            label = _hero_cell_cache.get(idx, "")
        else:
            label = _match_best(cell, HERO_TEMPLATES, HERO_THRESHOLD)
            _hero_cell_cache[idx] = label
            _hero_hash_cache[idx] = cell_hash
        if label:
            heroes.append(label)
    logger.info("Recognized enemy heroes: %s", heroes)
    return heroes


def detect_enemy_items(image: np.ndarray, enemy_heroes: List[str]) -> Dict[str, List[str]]:
    """Detect item builds for each enemy hero from scoreboard capture."""
    _ensure_templates_loaded()
    if not enemy_heroes:
        return {}
    rows = min(len(enemy_heroes), ITEM_GRID.rows)
    cells = _split_grid(image, GridConfig(cols=ITEM_GRID.cols, rows=rows))
    hero_items: Dict[str, List[str]] = {hero: [] for hero in enemy_heroes[:rows]}

    for idx, hero in enumerate(enemy_heroes[:rows]):
        for col in range(ITEM_GRID.cols):
            cell_index = idx * ITEM_GRID.cols + col
            cell = cells[cell_index]
            cell_hash = _hash_cell(cell)
            if _item_hash_cache.get(cell_index) == cell_hash:
                label = _item_cell_cache.get(cell_index, "")
            else:
                label = _match_best(cell, ITEM_TEMPLATES, ITEM_THRESHOLD)
                _item_cell_cache[cell_index] = label
                _item_hash_cache[cell_index] = cell_hash
            if label:
                hero_items[hero].append(label)
    logger.info("Recognized enemy items: %s", hero_items)
    return hero_items


__all__ = ["detect_enemy_heroes", "detect_enemy_items", "load_templates"]
