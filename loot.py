"""Level-aware enemy loot tables and item rewards."""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

from equipment import ARMOR, MATERIALS, POTION_CATALOG, RARITY_ORDER, WEAPONS
from player import Player

# These percentages match the major-project assignment. For a loot roll, a
# rarity is selected using these weights, limited to tiers unlocked at the
# player's level so early enemies cannot drop unusable end-game equipment.
LOOT_RARITY_CHANCES: dict[str, float] = {
    "Common": 50.0,
    "Uncommon": 25.0,
    "Rare": 15.0,
    "Super Rare": 6.0,
    "Epic": 3.0,
    "Mythical": 0.9,
    "Legendary": 0.1,
}

# Ordinary enemies have a level-scaled chance of bonus loot. Bosses already
# guarantee a Rare-or-better gear reward and get a higher chance of extra loot.
BASE_ENEMY_LOOT_CHANCE = 0.35
ENEMY_LOOT_CHANCE_PER_LEVEL = 0.004
MAX_ENEMY_LOOT_CHANCE = 0.75
BOSS_BONUS_LOOT_CHANCE = 0.85


def enemy_loot_chance(level: int, is_boss: bool = False) -> float:
    """Return the bonus-loot probability, increasing as enemies get stronger."""
    if is_boss:
        return BOSS_BONUS_LOOT_CHANCE
    safe_level = max(1, min(100, int(level)))
    return min(
        MAX_ENEMY_LOOT_CHANCE,
        BASE_ENEMY_LOOT_CHANCE + safe_level * ENEMY_LOOT_CHANCE_PER_LEVEL,
    )


def roll_loot_rarity(level: int) -> str:
    """Roll a rarity tier using assignment weights, bounded by level unlocks."""
    safe_level = max(1, min(100, int(level)))
    eligible_rarities = [
        rarity
        for rarity in RARITY_ORDER
        if any(
            item.get("rank") == rarity
            and int(item.get("required_level", 1)) <= safe_level
            for item in [*WEAPONS, *ARMOR, *MATERIALS]
        )
    ]
    if not eligible_rarities:
        return "Common"
    weights = [LOOT_RARITY_CHANCES[rarity] for rarity in eligible_rarities]
    return str(random.choices(eligible_rarities, weights=weights, k=1)[0])


def _add_material(player: Player, level: int, rarity: str) -> dict[str, Any]:
    """Add one level-appropriate material and return the inventory record."""
    eligible = [
        item for item in MATERIALS
        if item.get("rank") == rarity
        and int(item.get("min_level", 1)) <= level <= int(item.get("max_level", 100))
        and int(item.get("required_level", 1)) <= player.level
    ]
    if not eligible:
        eligible = [
            item for item in MATERIALS
            if int(item.get("min_level", 1)) <= level <= int(item.get("max_level", 100))
            and int(item.get("required_level", 1)) <= player.level
        ]
    if not eligible:
        eligible = [MATERIALS[0]]
    material = deepcopy(random.choice(eligible))
    player.inventory.append(material)
    print(f"BONUS LOOT: {material['rank']} {material['name']} added to your inventory.")
    return material


def _add_potion(player: Player) -> str:
    """Add a potion appropriate for the hero's current stage."""
    # Price is used as a simple progression gate so ultimate potions are not
    # showered on low-level players before they have reached harder regions.
    max_price = 20 + player.level * 5
    eligible = [potion for potion in POTION_CATALOG if int(potion["price"]) <= max_price]
    if not eligible:
        eligible = [POTION_CATALOG[0]]
    potion = random.choice(eligible)
    name = str(potion["name"])
    player.potions[name] = player.potions.get(name, 0) + 1
    print(f"BONUS LOOT: You found 1 x {name}.")
    return name


def _add_gear(player: Player, rarity: str) -> dict[str, Any]:
    """Add a weapon or armor piece of the rolled rarity, unlocked at this level."""
    eligible = [
        item for item in [*WEAPONS, *ARMOR]
        if item.get("rank") == rarity
        and int(item.get("required_level", 1)) <= player.level
    ]
    if not eligible:
        # Safety fallback for customized catalogs or legacy data.
        eligible = [
            item for item in [*WEAPONS, *ARMOR]
            if int(item.get("required_level", 1)) <= player.level
        ]
    if not eligible:
        return _add_material(player, player.level, "Common")

    owned_names = {
        str(item.get("name")) for item in player.inventory if isinstance(item, dict)
    }
    unowned = [item for item in eligible if item["name"] not in owned_names]
    reward = deepcopy(random.choice(unowned or eligible))
    player.inventory.append(reward)
    print(f"BONUS LOOT: {reward['rank']} {reward['name']} added to your inventory.")
    return reward


def award_enemy_loot(player: Player, enemy: Any) -> dict[str, Any] | str | None:
    """Roll optional loot after a victory and grant an eligible reward.

    Gold and EXP are awarded by the battle loop independently. Normal enemies
    can drop gear, potions, or materials. Bosses have a higher extra-drop rate;
    their guaranteed Rare-or-better gear is granted by the boss reward system,
    so their bonus reward is a potion or a material instead of a second gear roll.
    """
    chance = enemy_loot_chance(int(enemy.level), bool(getattr(enemy, "is_boss", False)))
    if random.random() >= chance:
        print("No additional loot this time.")
        return None

    if bool(getattr(enemy, "is_boss", False)):
        category = str(random.choices(["potion", "material"], weights=[45, 55], k=1)[0])
    else:
        category = str(random.choices(["gear", "potion", "material"], weights=[50, 30, 20], k=1)[0])

    if category == "potion":
        return _add_potion(player)

    rarity = roll_loot_rarity(int(enemy.level))
    if category == "material":
        return _add_material(player, int(enemy.level), rarity)
    return _add_gear(player, rarity)
