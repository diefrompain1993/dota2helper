"""Entry point orchestrating GSI, capture, recognition, and UI."""
from __future__ import annotations

import logging
from typing import Dict, List

from gsi_server import get_my_state, run_server
from ocr_recognition import detect_enemy_heroes, detect_enemy_items
from recommender import get_recommendations
from screen_capture import capture_region
from ui import DotaAssistantUI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self) -> None:
        self.cached_data: Dict[str, object] = {
            "my_hero": None,
            "my_items": [],
            "enemy_heroes": [],
            "enemy_items": {},
            "recommended_items": [],
            "explanations": [],
        }

    def _capture_and_detect(self) -> None:
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

        self.cached_data["enemy_heroes"] = enemy_heroes
        self.cached_data["enemy_items"] = enemy_items

    def build_snapshot(self) -> Dict[str, object]:
        my_state = get_my_state()
        my_hero = my_state.get("hero") or ""
        my_items: List[str] = my_state.get("items") or []

        self.cached_data["my_hero"] = my_hero
        self.cached_data["my_items"] = my_items

        self._capture_and_detect()

        recos = get_recommendations(
            my_hero=my_hero,
            my_items=my_items,
            enemy_heroes=self.cached_data["enemy_heroes"],
            enemy_items=self.cached_data["enemy_items"],
        )
        self.cached_data["recommended_items"] = recos["recommended_items"]
        self.cached_data["explanations"] = recos["explanations"]

        logger.info(
            "Snapshot: hero=%s, my_items=%s, enemies=%s, recos=%s",
            my_hero,
            my_items,
            self.cached_data["enemy_heroes"],
            self.cached_data["recommended_items"],
        )
        return dict(self.cached_data)


def main() -> None:
    run_server()
    orchestrator = Orchestrator()
    ui = DotaAssistantUI(data_provider=orchestrator.build_snapshot)
    ui.run()


if __name__ == "__main__":
    main()
