"""Rule-based recommender for Dota 2 itemization."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"
HERO_TAGS_PATH = CONFIG_DIR / "hero_tags.json"
TAG_COUNTER_PATH = CONFIG_DIR / "tag_counter_items.json"


def _load_json(path: Path) -> Dict[str, List[str]]:
    if not path.exists():
        logger.warning("Config not found: %s", path)
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


HERO_TAGS: Dict[str, List[str]] = _load_json(HERO_TAGS_PATH)
TAG_COUNTER_ITEMS: Dict[str, List[str]] = _load_json(TAG_COUNTER_PATH)
logger.info(
    "Loaded hero tags (%d entries) and counter rules (%d tags)",
    len(HERO_TAGS),
    len(TAG_COUNTER_ITEMS),
)

TAG_EXPLANATIONS: Dict[str, str] = {
    "heavy_magic_damage": "Против сильного магического урона полезен Black King Bar, Hood или Pipe of Insight.",
    "hard_disabler": "Дизейблы можно перекрыть Black King Bar, Manta Style или Linken Sphere.",
    "high_armor_tank": "Танков с высокой броней режут Desolator или Silver Edge.",
    "initiator": "Против инициаций хороши Linken Sphere или Black King Bar.",
    "illusion_hero": "Иллюзии удобно чистить с помощью Battle Fury, Maelstrom, Mjollnir или Shiva's Guard.",
    "illusionist": "Иллюзии удобно чистить с помощью Battle Fury, Maelstrom, Mjollnir или Shiva's Guard.",
    "magic_damage": "Много магии — берём BKB, Hood, Pipe или Eternal Shroud.",
    "physical_damage": "Против физ-урона помогают Ghost Scepter, Crimson Guard или Shiva's Guard.",
    "mobile": "Подвижных героев ловят Orchid, Bloodthorn, Hex, Gleipnir или Abyssal.",
    "healer": "Хил режут Spirit Vessel и Shiva's Guard.",
}


def _collect_enemy_tags(enemy_heroes: List[str]) -> Set[str]:
    tags: Set[str] = set()
    for hero in enemy_heroes:
        hero_tags = HERO_TAGS.get(hero, [])
        if not hero_tags:
            logger.debug("Hero %s has no tag mapping; using placeholder", hero)
        tags.update(hero_tags)
    return tags


def _aggregate_items(tags: Set[str], owned_items: List[str]) -> List[str]:
    recommendations: List[str] = []
    seen: Set[str] = set(owned_items)
    for tag in tags:
        for item in TAG_COUNTER_ITEMS.get(tag, []):
            if item not in seen:
                recommendations.append(item)
                seen.add(item)
    return recommendations


def _build_explanations(tags: Set[str], items: List[str]) -> List[str]:
    explanations: List[str] = []
    for tag in tags:
        text = TAG_EXPLANATIONS.get(tag)
        if not text:
            continue
        matched = [item for item in TAG_COUNTER_ITEMS.get(tag, []) if item in items]
        if matched:
            explanations.append(f"{', '.join(matched)} — {text}")
    return explanations


def get_recommendations(
    my_hero: str, my_items: List[str], enemy_heroes: List[str], enemy_items: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Return recommended items and explanations."""
    enemy_tags = _collect_enemy_tags(enemy_heroes)
    recommended_items = _aggregate_items(enemy_tags, owned_items=my_items)
    explanations = _build_explanations(enemy_tags, recommended_items)
    logger.info(
        "Recommendations built: hero=%s, enemy_tags=%s, recommended=%s",
        my_hero,
        sorted(enemy_tags),
        recommended_items,
    )
    return {
        "recommended_items": recommended_items,
        "explanations": explanations,
        "context": {
            "my_hero": my_hero,
            "enemy_heroes": enemy_heroes,
            "enemy_items": enemy_items,
        },
    }


__all__ = ["get_recommendations"]
