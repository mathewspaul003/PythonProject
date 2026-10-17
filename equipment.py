"""Weapon, armor, and potion catalogs used by inventory and shop systems."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

RARITY_MULTIPLIERS: dict[str, float] = {
    "Common": 1.0,
    "Uncommon": 1.1,
    "Rare": 1.3,
    "Super Rare": 1.5,
    "Epic": 1.8,
    "Mythical": 2.2,
    "Legendary": 2.8,
}

RARITY_CRITICAL_BONUSES: dict[str, float] = {
    "Common": 0.00,
    "Uncommon": 0.02,
    "Rare": 0.05,
    "Super Rare": 0.08,
    "Epic": 0.12,
    "Mythical": 0.18,
    "Legendary": 0.25,
}

RARITY_ORDER = tuple(RARITY_MULTIPLIERS)

# name, rarity, base damage, price, required level
_WEAPON_DEFINITIONS = (
    ("Wooden Sword", "Common", 4, 50, 1),
    ("Rusty Axe", "Common", 5, 55, 1),
    ("Training Bow", "Common", 4, 60, 1),
    ("Iron Dagger", "Uncommon", 7, 150, 5),
    ("Reinforced Spear", "Uncommon", 7, 165, 5),
    ("Oak Staff", "Uncommon", 8, 170, 5),
    ("Steel Sword", "Rare", 10, 420, 10),
    ("Long Bow", "Rare", 10, 440, 10),
    ("Battle Mage Staff", "Rare", 11, 460, 10),
    ("Crystal Blade", "Super Rare", 14, 950, 20),
    ("Shadow Dagger", "Super Rare", 13, 975, 20),
    ("Lightning Bow", "Super Rare", 14, 1000, 20),
    ("Flame Sword", "Epic", 18, 2200, 30),
    ("Ice Spear", "Epic", 18, 2350, 30),
    ("Thunder Hammer", "Epic", 20, 2500, 30),
    ("Phoenix Blade", "Mythical", 22, 5500, 50),
    ("Demon Slayer", "Mythical", 24, 6000, 50),
    ("Celestial Staff", "Mythical", 22, 5800, 50),
    ("Dragon King's Sword", "Legendary", 25, 13000, 75),
    ("Blade of Eternity", "Legendary", 28, 14500, 75),
    ("Bow of the Gods", "Legendary", 26, 14000, 75),
)

WEAPONS: list[dict[str, Any]] = []
for name, rank, base_damage, price, required_level in _WEAPON_DEFINITIONS:
    WEAPONS.append(
        {
            "type": "weapon",
            "name": name,
            "rank": rank,
            "base_damage": base_damage,
            "damage_multiplier": RARITY_MULTIPLIERS[rank],
            "damage": max(1, round(base_damage * RARITY_MULTIPLIERS[rank])),
            "critical_bonus": RARITY_CRITICAL_BONUSES[rank],
            "price": price,
            "required_level": required_level,
        }
    )

# name, rarity, defense, bonus HP, bonus mana, critical resistance, price, level
_ARMOR_DEFINITIONS = (
    ("Traveler's Clothes", "Common", 2, 10, 0, 0.00, 60, 1),
    ("Padded Leather", "Common", 3, 5, 0, 0.01, 75, 1),
    ("Scout Garb", "Uncommon", 4, 15, 5, 0.02, 190, 5),
    ("Iron Vest", "Uncommon", 5, 20, 0, 0.03, 220, 5),
    ("Knight Armor", "Rare", 8, 35, 0, 0.05, 520, 10),
    ("Ranger's Mantle", "Rare", 6, 20, 15, 0.06, 540, 10),
    ("Crystal Armor", "Super Rare", 10, 55, 15, 0.08, 1200, 20),
    ("Shadowweave", "Super Rare", 8, 30, 30, 0.10, 1250, 20),
    ("Dragon Scale", "Epic", 14, 90, 10, 0.12, 2700, 30),
    ("Arcane Robes", "Epic", 10, 45, 45, 0.14, 2850, 30),
    ("Phoenix Plate", "Mythical", 19, 130, 25, 0.18, 6200, 50),
    ("Demonforged Armor", "Mythical", 21, 100, 10, 0.20, 6600, 50),
    ("Celestial Aegis", "Legendary", 27, 200, 50, 0.25, 15000, 75),
    ("Armor of Eternity", "Legendary", 30, 175, 35, 0.30, 16500, 75),
)

ARMOR: list[dict[str, Any]] = []
for name, rank, defense_bonus, hp_bonus, mana_bonus, crit_resistance, price, required_level in _ARMOR_DEFINITIONS:
    ARMOR.append(
        {
            "type": "armor",
            "name": name,
            "rank": rank,
            "defense_bonus": defense_bonus,
            "hp_bonus": hp_bonus,
            "mana_bonus": mana_bonus,
            "critical_resistance": crit_resistance,
            "price": price,
            "required_level": required_level,
        }
    )

# Materials are collected from regional enemies. They can be sold or dropped;
# their rarity and level requirements make loot improve as the hero progresses.
_MATERIAL_DEFINITIONS = (
    # name, rank, sale price, minimum level, maximum level
    ("Slime Gel", "Common", 8, 1, 10),
    ("Goblin Ear", "Common", 9, 1, 10),
    ("Wolf Pelt", "Common", 10, 1, 10),
    ("Spider Silk", "Uncommon", 15, 5, 20),
    ("Troll Hide", "Uncommon", 18, 11, 20),
    ("Ancient Bark", "Rare", 28, 10, 30),
    ("Scorpion Chitin", "Super Rare", 45, 20, 40),
    ("Cursed Sigil", "Epic", 70, 30, 50),
    ("Ember Core", "Mythical", 120, 50, 70),
    ("Celestial Shard", "Legendary", 200, 75, 90),
    ("Demon Essence", "Legendary", 250, 90, 100),
)

MATERIALS: list[dict[str, Any]] = [
    {
        "type": "material",
        "name": name,
        "rank": rank,
        "price": price,
        "required_level": required_level,
        "min_level": required_level,
        "max_level": max_level,
        "description": f"A {rank.lower()} crafting material found in dangerous regions.",
    }
    for name, rank, price, required_level, max_level in _MATERIAL_DEFINITIONS
]

# A final quest keepsake is recorded after the last boss. It is not sold by the
# shop and is included in the inventory for the end-game summary.
QUEST_ITEMS: list[dict[str, Any]] = [
    {
        "type": "quest",
        "name": "Demon King's Sigil",
        "rank": "Legendary",
        "price": 0,
        "required_level": 100,
        "description": "Proof that the Ancient Demon King has been defeated.",
    }
]

# Potion data is shared by the shop and battle module. Full-restoration items
# use flags rather than fixed amounts so they scale correctly with the hero.
POTION_CATALOG: list[dict[str, Any]] = [
    {"type": "potion", "name": "Small Health Potion", "category": "health", "hp_restore": 50, "price": 20, "description": "Restore up to 50 HP."},
    {"type": "potion", "name": "Medium Health Potion", "category": "health", "hp_restore": 100, "price": 45, "description": "Restore up to 100 HP."},
    {"type": "potion", "name": "Large Health Potion", "category": "health", "hp_restore": 250, "price": 90, "description": "Restore up to 250 HP."},
    {"type": "potion", "name": "Giant Health Potion", "category": "health", "hp_restore": 500, "price": 160, "description": "Restore up to 500 HP."},
    {"type": "potion", "name": "Ultimate Health Potion", "category": "health", "full_hp": True, "price": 300, "description": "Restore all HP."},
    {"type": "potion", "name": "Small Mana Potion", "category": "mana", "mana_restore": 30, "price": 20, "description": "Restore up to 30 mana."},
    {"type": "potion", "name": "Medium Mana Potion", "category": "mana", "mana_restore": 75, "price": 45, "description": "Restore up to 75 mana."},
    {"type": "potion", "name": "Large Mana Potion", "category": "mana", "mana_restore": 150, "price": 90, "description": "Restore up to 150 mana."},
    {"type": "potion", "name": "Giant Mana Potion", "category": "mana", "mana_restore": 300, "price": 160, "description": "Restore up to 300 mana."},
    {"type": "potion", "name": "Ultimate Mana Potion", "category": "mana", "full_mana": True, "price": 300, "description": "Restore all mana."},
    {"type": "potion", "name": "Rejuvenation Potion", "category": "mixed", "hp_restore": 100, "mana_restore": 50, "price": 100, "description": "Restore up to 100 HP and 50 mana."},
    {"type": "potion", "name": "Greater Rejuvenation Potion", "category": "mixed", "hp_restore": 250, "mana_restore": 125, "price": 220, "description": "Restore up to 250 HP and 125 mana."},
    {"type": "potion", "name": "Strength Potion", "category": "buff", "attack_buff": 1.25, "duration": 3, "price": 80, "description": "Increase attack by 25% for 3 turns."},
    {"type": "potion", "name": "Guardian Tonic", "category": "buff", "defense_buff": 1.5, "duration": 3, "price": 80, "description": "Increase armor defense by 50% for 3 turns."},
    {"type": "potion", "name": "Precision Elixir", "category": "buff", "crit_buff": 0.15, "duration": 3, "price": 100, "description": "Increase critical chance by 15% for 3 turns."},
]


def get_item(name: str) -> dict[str, Any] | None:
    """Return a copy of a catalog item by exact name."""
    for item in [*WEAPONS, *ARMOR, *POTION_CATALOG, *MATERIALS, *QUEST_ITEMS]:
        if item["name"] == name:
            return deepcopy(item)
    return None


def find_equipped_item(player: Any, item_type: str) -> dict[str, Any] | None:
    """Find the player's currently equipped weapon or armor record."""
    equipped_name = getattr(player, f"equipped_{item_type}", None)
    if not equipped_name:
        return None
    for item in getattr(player, "inventory", []):
        if isinstance(item, dict) and item.get("type") == item_type and item.get("name") == equipped_name:
            return item
    return None


def get_potion(name: str) -> dict[str, Any] | None:
    """Return a copy of potion metadata by its name."""
    for potion in POTION_CATALOG:
        if potion["name"] == name:
            return deepcopy(potion)
    return None
