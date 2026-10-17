"""World regions, level gates, and boss definitions for Eldoria."""

from __future__ import annotations

from typing import Any

REGIONS: tuple[dict[str, Any], ...] = (
    {"name": "Forest", "min_level": 1, "max_level": 10, "description": "Overgrown trails and goblin camps."},
    {"name": "Cave", "min_level": 11, "max_level": 20, "description": "Dark tunnels, spiders, and ancient stone."},
    {"name": "Desert", "min_level": 21, "max_level": 30, "description": "Scorching sands and restless spirits."},
    {"name": "Ruins", "min_level": 31, "max_level": 40, "description": "Forgotten temples and cursed guardians."},
    {"name": "Castle", "min_level": 41, "max_level": 50, "description": "Fortified halls and vampire courts."},
    {"name": "Volcano", "min_level": 51, "max_level": 60, "description": "Lava rivers and fire-forged beasts."},
    {"name": "Frozen Mountain", "min_level": 61, "max_level": 70, "description": "Blizzards, ice spirits, and giants."},
    {"name": "Sky Temple", "min_level": 71, "max_level": 80, "description": "Storms and ancient celestial sentinels."},
    {"name": "Demon Realm", "min_level": 81, "max_level": 100, "description": "The final frontier before the Demon King."},
)

# Each boss has two distinct special attacks and a healing ability. Bosses spawn
# when the player reaches the listed level and block progress until defeated.
BOSSES: tuple[dict[str, Any], ...] = (
    {"level": 10, "name": "Goblin King", "region": "Forest", "special_attacks": (("King's Cleave", 1.65), ("Goblin King's Fury", 1.9)), "heal_percent": 0.10},
    {"level": 20, "name": "Forest Guardian", "region": "Cave", "special_attacks": (("Ancient Roots", 1.65), ("Verdant Shockwave", 1.9)), "heal_percent": 0.10},
    {"level": 30, "name": "Ancient Golem", "region": "Desert", "special_attacks": (("Earthshatter", 1.7), ("Titanic Fist", 2.0)), "heal_percent": 0.10},
    {"level": 40, "name": "Vampire Lord", "region": "Ruins", "special_attacks": (("Blood Moon", 1.7), ("Crimson Drain", 1.95)), "heal_percent": 0.12},
    {"level": 50, "name": "Dragon Rider", "region": "Castle", "special_attacks": (("Dragonfire Dive", 1.75), ("Rider's Onslaught", 2.0)), "heal_percent": 0.10},
    {"level": 60, "name": "Demon General", "region": "Volcano", "special_attacks": (("Infernal Rupture", 1.75), ("Hellblade Storm", 2.05)), "heal_percent": 0.12},
    {"level": 70, "name": "Ice Titan", "region": "Frozen Mountain", "special_attacks": (("Glacial Cataclysm", 1.8), ("Frozen Colossus Slam", 2.05)), "heal_percent": 0.10},
    {"level": 80, "name": "Shadow Emperor", "region": "Sky Temple", "special_attacks": (("Eclipse Nova", 1.8), ("Nightfall Decree", 2.1)), "heal_percent": 0.12},
    {"level": 90, "name": "Celestial Dragon", "region": "Demon Realm", "special_attacks": (("Celestial Judgment", 1.85), ("Starfire Cataclysm", 2.1)), "heal_percent": 0.10},
    {"level": 100, "name": "Ancient Demon King", "region": "Demon Realm", "special_attacks": (("Doom of Eldoria", 1.9), ("World-Ender", 2.2)), "heal_percent": 0.15},
)

BOSS_BY_LEVEL: dict[int, dict[str, Any]] = {boss["level"]: boss for boss in BOSSES}
BOSS_BY_NAME: dict[str, dict[str, Any]] = {boss["name"]: boss for boss in BOSSES}


def region_for_level(level: int) -> dict[str, Any]:
    """Return the region appropriate for a hero level, clamped to 1–100."""
    safe_level = max(1, min(100, int(level)))
    for region in REGIONS:
        if region["min_level"] <= safe_level <= region["max_level"]:
            return region
    return REGIONS[-1]


def pending_boss(player: Any) -> dict[str, Any] | None:
    """Return the earliest undefeated boss whose gate the player has reached."""
    defeated = set(getattr(player, "bosses_defeated", []))
    for boss in BOSSES:
        if boss["level"] <= int(player.level) and boss["name"] not in defeated:
            return boss
    return None


def next_boss(player: Any) -> dict[str, Any] | None:
    """Return the next undefeated boss, even if its level has not been reached."""
    defeated = set(getattr(player, "bosses_defeated", []))
    return next((boss for boss in BOSSES if boss["name"] not in defeated), None)


def boss_defeated(player: Any, boss_name: str) -> bool:
    """Check persistent boss progress by boss name."""
    return boss_name in getattr(player, "bosses_defeated", [])
