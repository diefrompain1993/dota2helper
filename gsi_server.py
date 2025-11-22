"""Lightweight Flask-based GSI receiver for Dota 2 state."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import Dict, List, Optional

from flask import Flask, jsonify, request


logging.basicConfig(level=logging.INFO)
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
        hero = payload.get("hero") or payload.get("my_hero")
        items = payload.get("items") or payload.get("my_items")
        if items is not None and not isinstance(items, list):
            return jsonify({"error": "items must be a list"}), 400
        _state_store.update(hero=hero, items=items)
        return jsonify({"status": "ok", "hero": hero, "items": items}), 200

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
    thread = Thread(target=app.run, kwargs={"host": host, "port": port}, daemon=True)
    thread.start()
    logger.info("GSI server started on %s:%s", host, port)
    return thread


if __name__ == "__main__":
    run_server()
