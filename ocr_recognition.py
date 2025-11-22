"""Template-matching based recognition for heroes and items."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

ASSETS_DIR = Path(__file__).parent / "assets"
HERO_DIR = ASSETS_DIR / "heroes"
ITEM_DIR = ASSETS_DIR / "items"

HERO_THRESHOLD = 0.7
ITEM_THRESHOLD = 0.65


def _load_templates(directory: Path) -> Dict[str, np.ndarray]:
    templates: Dict[str, np.ndarray] = {}
    if not directory.exists():
        return templates
    for file in directory.iterdir():
        if file.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        img = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        templates[file.stem] = img
    return templates


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


_HERO_TEMPLATES = _load_templates(HERO_DIR)
_ITEM_TEMPLATES = _load_templates(ITEM_DIR)


def detect_enemy_heroes(image: np.ndarray) -> List[str]:
    """Detect enemy heroes from the top bar capture."""
    heroes: List[str] = []
    for cell in _split_grid(image, HERO_GRID):
        label = _match_best(cell, _HERO_TEMPLATES, HERO_THRESHOLD)
        if label:
            heroes.append(label)
    return heroes


def detect_enemy_items(image: np.ndarray, enemy_heroes: List[str]) -> Dict[str, List[str]]:
    """Detect item builds for each enemy hero from scoreboard capture."""
    if not enemy_heroes:
        return {}
    rows = min(len(enemy_heroes), ITEM_GRID.rows)
    cells = _split_grid(image, GridConfig(cols=ITEM_GRID.cols, rows=rows))
    hero_items: Dict[str, List[str]] = {hero: [] for hero in enemy_heroes[:rows]}

    for idx, hero in enumerate(enemy_heroes[:rows]):
        for col in range(ITEM_GRID.cols):
            cell = cells[idx * ITEM_GRID.cols + col]
            label = _match_best(cell, _ITEM_TEMPLATES, ITEM_THRESHOLD)
            if label:
                hero_items[hero].append(label)
    return hero_items


__all__ = ["detect_enemy_heroes", "detect_enemy_items"]
