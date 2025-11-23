"""Tkinter-based UI to display game state and recommendations."""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List


logger = logging.getLogger(__name__)

def _list_to_lines(items: List[str]) -> str:
    return "\n".join(items) if items else "—"


def _enemy_items_to_lines(enemy_items: Dict[str, List[str]]) -> str:
    lines = []
    for hero, items in enemy_items.items():
        lines.append(f"{hero}: {', '.join(items) if items else '—'}")
    return "\n".join(lines) if lines else "—"


class DotaAssistantUI:
    def __init__(self, data_provider: Callable[[], Dict[str, object]], refresh_ms: int = 1500) -> None:
        self.data_provider = data_provider
        self.refresh_ms = refresh_ms

        self.root = tk.Tk()
        self.root.title("Dota 2 Item Helper")
        self._build_widgets()
        self._schedule_refresh()

    def _build_widgets(self) -> None:
        padding = {"padx": 10, "pady": 5, "sticky": "w"}
        self.hero_var = tk.StringVar()
        self.my_items_var = tk.StringVar()
        self.enemies_var = tk.StringVar()
        self.enemy_items_var = tk.StringVar()
        self.reco_var = tk.StringVar()
        self.expl_var = tk.StringVar()

        ttk.Label(self.root, text="Мой герой:").grid(row=0, column=0, **padding)
        ttk.Label(self.root, textvariable=self.hero_var).grid(row=0, column=1, **padding)

        ttk.Label(self.root, text="Мои предметы:").grid(row=1, column=0, **padding)
        ttk.Label(self.root, textvariable=self.my_items_var).grid(row=1, column=1, **padding)

        ttk.Label(self.root, text="Вражеские герои:").grid(row=2, column=0, **padding)
        ttk.Label(self.root, textvariable=self.enemies_var, justify=tk.LEFT).grid(row=2, column=1, **padding)

        ttk.Label(self.root, text="Вражеские предметы:").grid(row=3, column=0, **padding)
        ttk.Label(self.root, textvariable=self.enemy_items_var, justify=tk.LEFT).grid(row=3, column=1, **padding)

        ttk.Label(self.root, text="Рекомендуемые предметы:").grid(row=4, column=0, **padding)
        ttk.Label(self.root, textvariable=self.reco_var, justify=tk.LEFT).grid(row=4, column=1, **padding)

        ttk.Label(self.root, text="Пояснения:").grid(row=5, column=0, **padding)
        ttk.Label(self.root, textvariable=self.expl_var, justify=tk.LEFT).grid(row=5, column=1, **padding)

    def _schedule_refresh(self) -> None:
        self.root.after(self.refresh_ms, self._refresh)

    def _refresh(self) -> None:
        data = self.data_provider()
        self.hero_var.set(data.get("my_hero") or "—")
        self.my_items_var.set(", ".join(data.get("my_items", [])) if data.get("my_items") else "—")
        enemies = data.get("enemy_heroes", [])
        self.enemies_var.set(", ".join(enemies) if enemies else "—")
        self.enemy_items_var.set(_enemy_items_to_lines(data.get("enemy_items", {})))
        self.reco_var.set(_list_to_lines(data.get("recommended_items", [])))
        self.expl_var.set(_list_to_lines(data.get("explanations", [])))
        logger.debug("UI refreshed with snapshot")
        self._schedule_refresh()

    def run(self) -> None:
        self.root.mainloop()


__all__ = ["DotaAssistantUI"]
