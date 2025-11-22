"""Entry point orchestrating GSI, capture, recognition, and UI."""
from __future__ import annotations

import logging
import threading
import time
from typing import Dict, List

import ocr_recognition
from gsi_server import get_my_state, run_server
from logging_config import setup_logging
from ocr_recognition import detect_enemy_heroes, detect_enemy_items, load_templates
from recommender import get_recommendations
from screen_capture import capture_region
from setup_manager import initialize_application
from ui import DotaAssistantUI

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, refresh_interval: float = 0.75) -> None:
        self.refresh_interval = refresh_interval
        self.cached_data: Dict[str, object] = {
            "my_hero": None,
            "my_items": [],
            "enemy_heroes": [],
            "enemy_items": {},
            "recommended_items": [],
            "explanations": [],
        }
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def _capture_and_detect(self) -> None:
        enemy_heroes: List[str]
        enemy_items: Dict[str, List[str]]
        try:
            top_bar = capture_region("top_bar_enemies")
            enemy_heroes = detect_enemy_heroes(top_bar)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to detect enemy heroes: %s", exc)
            enemy_heroes = []

        try:
            scoreboard = capture_region("scoreboard_items")
            enemy_items = detect_enemy_items(scoreboard, enemy_heroes)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to detect enemy items: %s", exc)
            enemy_items = {}

        with self._lock:
            self.cached_data["enemy_heroes"] = enemy_heroes
            self.cached_data["enemy_items"] = enemy_items

    def refresh_once(self) -> None:
        my_state = get_my_state()
        my_hero = my_state.get("hero") or ""
        my_items: List[str] = my_state.get("items") or []

        with self._lock:
            self.cached_data["my_hero"] = my_hero
            self.cached_data["my_items"] = my_items

        self._capture_and_detect()

        recos = get_recommendations(
            my_hero=my_hero,
            my_items=my_items,
            enemy_heroes=self.cached_data["enemy_heroes"],
            enemy_items=self.cached_data["enemy_items"],
        )
        with self._lock:
            self.cached_data["recommended_items"] = recos["recommended_items"]
            self.cached_data["explanations"] = recos["explanations"]

        logger.info(
            "Snapshot: hero=%s, my_items=%s, enemies=%s, recos=%s",
            my_hero,
            my_items,
            self.cached_data["enemy_heroes"],
            self.cached_data["recommended_items"],
        )

    def run_loop(self) -> None:
        while not self._stop.is_set():
            start = time.time()
            self.refresh_once()
            elapsed = time.time() - start
            sleep_for = max(self.refresh_interval - elapsed, 0.05)
            logger.debug("Loop completed in %.3fs; sleeping %.3fs", elapsed, sleep_for)
            self._stop.wait(timeout=sleep_for)

    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.run_loop, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        self._stop.set()

    def build_snapshot(self) -> Dict[str, object]:
        with self._lock:
            return dict(self.cached_data)


def main() -> None:
    setup_logging()
    initialize_application()
    load_templates()
    if not (ocr_recognition.HERO_TEMPLATES and ocr_recognition.ITEM_TEMPLATES):
        logger.warning(
            "Templates are missing; ensure assets/heroes and assets/items contain all icons"
        )
    run_server()
    orchestrator = Orchestrator()
    orchestrator.start()
    ui = DotaAssistantUI(data_provider=orchestrator.build_snapshot, refresh_ms=int(orchestrator.refresh_interval * 1000))
    ui.run()


if __name__ == "__main__":
    main()
