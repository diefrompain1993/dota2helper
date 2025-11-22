"""Lightweight Flask-based GSI receiver for Dota 2 state."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import Dict, List, Optional

from flask import Flask, jsonify, request


logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    hero: Optional[str] = None
    items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {"hero": self.hero, "items": list(self.items)}


class StateStore:
    def __init__(self) -> None:
        self._state = PlayerState()
        self._lock = Lock()

    def update(self, hero: Optional[str], items: Optional[List[str]]) -> None:
        with self._lock:
            if hero:
                self._state.hero = hero
            if items is not None:
                self._state.items = list(items)
            logger.info("Updated GSI state: hero=%s, items=%s", self._state.hero, self._state.items)

    def snapshot(self) -> PlayerState:
        with self._lock:
            return PlayerState(hero=self._state.hero, items=list(self._state.items))


_state_store = StateStore()


def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/gsi")
    def ingest_gsi():
        payload = request.get_json(force=True, silent=True) or {}
        logger.debug("Received GSI payload: %s", payload)

        # --- HERO PARSING ---
        hero_block = payload.get("hero") or {}
        raw_hero_id = hero_block.get("id") or hero_block.get("name") or ""
        hero = raw_hero_id.replace("npc_dota_hero_", "")

        # --- ITEM PARSING ---
        items_block = payload.get("items") or {}
        parsed_items = []
        for slot, item_data in items_block.items():
            if not isinstance(item_data, dict):
                continue
            name = item_data.get("name")
            if not name:
                continue
            if name.startswith("item_"):
                parsed_items.append(name.replace("item_", ""))

        _state_store.update(hero=hero, items=parsed_items)
        return jsonify({"status": "ok", "hero": hero, "items": parsed_items}), 200

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


def get_my_state() -> Dict[str, object]:
    """Return current player state for consumption by the orchestrator/UI."""
    return _state_store.snapshot().to_dict()


def run_server(host: str = "0.0.0.0", port: int = 4000) -> Thread:
    """Run the Flask GSI server in a background thread."""
    app = create_app()
    thread = Thread(
        target=app.run,
        kwargs={"host": host, "port": port, "use_reloader": False},
        daemon=True,
    )
    thread.start()
    logger.info("GSI server started on %s:%s", host, port)
    return thread


if __name__ == "__main__":
    run_server()
