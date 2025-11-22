"""Rule-based recommender for Dota 2 itemization."""
from __future__ import annotations

from typing import Dict, List, Set

HERO_TAGS: Dict[str, List[str]] = {
    "lion": ["heavy_magic_damage", "hard_disabler"],
    "shadow_fiend": ["heavy_magic_damage"],
    "axe": ["initiator", "high_armor_tank"],
    "phantom_lancer": ["illusion_hero"],
    "naga_siren": ["illusion_hero"],
}

TAG_COUNTER_ITEMS: Dict[str, List[str]] = {
    "heavy_magic_damage": ["black_king_bar", "pipe_of_insight"],
    "hard_disabler": ["black_king_bar", "manta_style", "linken_sphere"],
    "high_armor_tank": ["desolator", "silver_edge"],
    "initiator": ["linken_sphere", "black_king_bar"],
    "illusion_hero": ["battle_fury", "mjollnir", "shivas_guard"],
}

TAG_EXPLANATIONS: Dict[str, str] = {
    "heavy_magic_damage": "Против сильного магического урона полезен Black King Bar или Pipe of Insight.",
    "hard_disabler": "Дизейблы можно перекрыть Black King Bar, Manta Style или Linken Sphere.",
    "high_armor_tank": "Танков с высоким броней режут Desolator или Silver Edge.",
    "initiator": "Против инициаций хороши Linken Sphere или Black King Bar.",
    "illusion_hero": "Иллюзии удобно чистить с помощью Battle Fury, Mjollnir или Shiva's Guard.",
}


def _collect_enemy_tags(enemy_heroes: List[str]) -> Set[str]:
    tags: Set[str] = set()
    for hero in enemy_heroes:
        tags.update(HERO_TAGS.get(hero, []))
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
