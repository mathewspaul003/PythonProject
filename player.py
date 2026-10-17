"""Player model and character-class configuration."""

from dataclasses import asdict, dataclass, field
from typing import Any


# One passive bonus unlocks at every five-level milestone, as required by the
# assignment. Bonuses become part of the hero's saved base stats.
PASSIVE_UNLOCKS: dict[int, dict[str, Any]] = {
    5: {"name": "Keen Edge", "bonuses": {"crit_chance": 0.02}, "description": "+2% critical chance"},
    10: {"name": "Iron Resolve", "bonuses": {"defense": 2}, "description": "+2 defense"},
    15: {"name": "Vitality", "bonuses": {"max_hp": 20}, "description": "+20 maximum HP"},
    20: {"name": "Arcane Reservoir", "bonuses": {"max_mana": 15}, "description": "+15 maximum mana"},
    25: {"name": "Sharpsight", "bonuses": {"crit_chance": 0.02}, "description": "+2% critical chance"},
    30: {"name": "Stone Skin", "bonuses": {"defense": 3}, "description": "+3 defense"},
    35: {"name": "Greater Vitality", "bonuses": {"max_hp": 25}, "description": "+25 maximum HP"},
    40: {"name": "Deep Reserve", "bonuses": {"max_mana": 20}, "description": "+20 maximum mana"},
    45: {"name": "Lethal Focus", "bonuses": {"crit_chance": 0.02}, "description": "+2% critical chance"},
    50: {"name": "Titan Guard", "bonuses": {"defense": 3}, "description": "+3 defense"},
    55: {"name": "Enduring Heart", "bonuses": {"max_hp": 25}, "description": "+25 maximum HP"},
    60: {"name": "Mana Well", "bonuses": {"max_mana": 20}, "description": "+20 maximum mana"},
    65: {"name": "Predator's Eye", "bonuses": {"crit_chance": 0.02}, "description": "+2% critical chance"},
    70: {"name": "Fortress Mind", "bonuses": {"defense": 4}, "description": "+4 defense"},
    75: {"name": "Giant's Heart", "bonuses": {"max_hp": 30}, "description": "+30 maximum HP"},
    80: {"name": "Infinite Wellspring", "bonuses": {"max_mana": 25}, "description": "+25 maximum mana"},
    85: {"name": "Deadeye", "bonuses": {"crit_chance": 0.03}, "description": "+3% critical chance"},
    90: {"name": "Adamant Guard", "bonuses": {"defense": 4}, "description": "+4 defense"},
    95: {"name": "Phoenix Heart", "bonuses": {"max_hp": 35}, "description": "+35 maximum HP"},
    100: {"name": "Demonbane", "bonuses": {"attack": 5, "defense": 3, "crit_chance": 0.05}, "description": "+5 attack, +3 defense, and +5% critical chance"},
}


CLASS_STATS: dict[str, dict[str, int | float]] = {
    "Warrior": {
        "max_hp": 150,
        "max_mana": 40,
        "attack": 18,
        "defense": 14,
        "crit_chance": 0.08,
        "crit_damage": 1.5,
    },
    "Mage": {
        "max_hp": 100,
        "max_mana": 120,
        "attack": 24,
        "defense": 6,
        "crit_chance": 0.12,
        "crit_damage": 1.7,
    },
    "Archer": {
        "max_hp": 115,
        "max_mana": 70,
        "attack": 17,
        "defense": 9,
        "crit_chance": 0.18,
        "crit_damage": 1.6,
    },
    "Assassin": {
        "max_hp": 90,
        "max_mana": 70,
        "attack": 23,
        "defense": 5,
        "crit_chance": 0.25,
        "crit_damage": 1.8,
    },
}


@dataclass
class Player:
    """Store all persistent player state in one object."""

    name: str
    character_class: str
    level: int = 1
    experience: int = 0
    hp: int = 0
    max_hp: int = 0
    mana: int = 0
    max_mana: int = 0
    attack: int = 0
    defense: int = 0
    crit_chance: float = 0.0
    crit_damage: float = 1.5
    gold: int = 100
    potions: dict[str, int] = field(
        default_factory=lambda: {"Small Health Potion": 2, "Small Mana Potion": 1}
    )
    inventory: list[dict[str, Any]] = field(default_factory=list)
    equipped_weapon: str | None = None
    equipped_armor: str | None = None
    bosses_defeated: list[str] = field(default_factory=list)
    enemies_defeated: int = 0
    total_play_time_seconds: int = 0
    equipment_version: int = 1
    unlocked_passives: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, character_class: str) -> "Player":
        """Create a player with the selected class's base stats."""
        if character_class not in CLASS_STATS:
            raise ValueError(f"Unknown character class: {character_class}")

        stats = CLASS_STATS[character_class]
        player = cls(
            name=name,
            character_class=character_class,
            hp=int(stats["max_hp"]),
            max_hp=int(stats["max_hp"]),
            mana=int(stats["max_mana"]),
            max_mana=int(stats["max_mana"]),
            attack=int(stats["attack"]),
            defense=int(stats["defense"]),
            crit_chance=float(stats["crit_chance"]),
            crit_damage=float(stats["crit_damage"]),
        )
        # Every new hero receives a modest starter weapon and armor set.
        from equipment import get_item

        starter_weapon = get_item("Wooden Sword")
        starter_armor = get_item("Traveler's Clothes")
        if starter_weapon:
            player.inventory.append(starter_weapon)
            player.equipped_weapon = starter_weapon["name"]
        if starter_armor:
            player.inventory.append(starter_armor)
            player.equipped_armor = starter_armor["name"]
        # Start fully restored against equipment-adjusted resource caps.
        player.hp = player.total_max_hp
        player.mana = player.total_max_mana
        return player

    @property
    def equipped_weapon_data(self) -> dict[str, Any] | None:
        """Get the equipped weapon's item record, if present in inventory."""
        from equipment import find_equipped_item

        return find_equipped_item(self, "weapon")

    @property
    def equipped_armor_data(self) -> dict[str, Any] | None:
        """Get the equipped armor's item record, if present in inventory."""
        from equipment import find_equipped_item

        return find_equipped_item(self, "armor")

    @property
    def weapon_damage_bonus(self) -> int:
        item = self.equipped_weapon_data
        return int(item.get("damage", 0)) if item else 0

    @property
    def weapon_critical_bonus(self) -> float:
        item = self.equipped_weapon_data
        return float(item.get("critical_bonus", 0.0)) if item else 0.0

    @property
    def armor_defense_bonus(self) -> int:
        item = self.equipped_armor_data
        return int(item.get("defense_bonus", 0)) if item else 0

    @property
    def armor_hp_bonus(self) -> int:
        item = self.equipped_armor_data
        return int(item.get("hp_bonus", 0)) if item else 0

    @property
    def armor_mana_bonus(self) -> int:
        item = self.equipped_armor_data
        return int(item.get("mana_bonus", 0)) if item else 0

    @property
    def critical_resistance(self) -> float:
        item = self.equipped_armor_data
        return float(item.get("critical_resistance", 0.0)) if item else 0.0

    @property
    def total_attack(self) -> int:
        return self.attack + self.weapon_damage_bonus

    @property
    def total_defense(self) -> int:
        return self.defense + self.armor_defense_bonus

    @property
    def total_max_hp(self) -> int:
        return self.max_hp + self.armor_hp_bonus

    @property
    def total_max_mana(self) -> int:
        return self.max_mana + self.armor_mana_bonus

    @property
    def total_crit_chance(self) -> float:
        return min(0.75, self.crit_chance + self.weapon_critical_bonus)

    def clamp_resources(self) -> None:
        """Keep current HP and mana within equipment-adjusted maximums."""
        self.hp = min(self.hp, self.total_max_hp)
        self.mana = min(self.mana, self.total_max_mana)

    def unlock_passive_for_level(self, level: int) -> dict[str, Any] | None:
        """Apply a five-level passive once and return its definition for display."""
        passive = PASSIVE_UNLOCKS.get(int(level))
        if passive is None or passive["name"] in self.unlocked_passives:
            return None

        for stat, amount in passive["bonuses"].items():
            if stat == "crit_chance":
                self.crit_chance = min(0.75, self.crit_chance + float(amount))
            else:
                setattr(self, stat, int(getattr(self, stat)) + int(amount))

        self.unlocked_passives.append(str(passive["name"]))
        self.clamp_resources()
        return passive

    def to_dict(self) -> dict[str, Any]:
        """Convert the player into JSON-serializable data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        """Rebuild a player from saved JSON data."""
        # Filter keys to known fields so old saves tolerate additional metadata.
        known_fields = cls.__dataclass_fields__.keys()
        clean_data = {key: value for key, value in data.items() if key in known_fields}
        needs_equipment_migration = "equipment_version" not in clean_data
        needs_passive_migration = "unlocked_passives" not in clean_data
        player = cls(**clean_data)

        # Older saves predate five-level passives. Grant milestones already reached
        # so the migration does not leave an established hero behind the new rules.
        if needs_passive_migration:
            for milestone in sorted(PASSIVE_UNLOCKS):
                if milestone <= player.level:
                    player.unlock_passive_for_level(milestone)

        # Saves created before Milestone 3 did not include starter equipment.
        # Migrate those saves once, while versioned saves retain their exact inventory.
        if needs_equipment_migration:
            from equipment import get_item

            has_weapon = any(
                isinstance(item, dict) and item.get("type") == "weapon"
                for item in player.inventory
            )
            has_armor = any(
                isinstance(item, dict) and item.get("type") == "armor"
                for item in player.inventory
            )
            if not player.equipped_weapon and not has_weapon:
                starter_weapon = get_item("Wooden Sword")
                if starter_weapon:
                    player.inventory.append(starter_weapon)
                    player.equipped_weapon = starter_weapon["name"]
            if not player.equipped_armor and not has_armor:
                starter_armor = get_item("Traveler's Clothes")
                if starter_armor:
                    player.inventory.append(starter_armor)
                    player.equipped_armor = starter_armor["name"]
            player.equipment_version = 1
        return player

    def display_stats(self) -> None:
        """Print a readable summary of the player's current stats."""
        print("\n" + "=" * 42)
        print(f" HERO: {self.name}  |  CLASS: {self.character_class.upper()}")
        print("=" * 42)
        print(f"Level: {self.level}    EXP: {self.experience}    Gold: {self.gold}")
        print(f"HP: {self.hp}/{self.total_max_hp}")
        print(f"Mana: {self.mana}/{self.total_max_mana}")
        print(f"Attack: {self.total_attack} (base {self.attack})    Defense: {self.total_defense} (base {self.defense})")
        print(f"Critical chance: {self.total_crit_chance:.0%}")
        print(f"Critical resistance: {self.critical_resistance:.0%}")
        print(f"Critical damage multiplier: x{self.crit_damage:.1f}")
        print("Passive bonuses:")
        if self.unlocked_passives:
            for passive_name in self.unlocked_passives:
                print(f"  - {passive_name}")
        else:
            print("  - None unlocked yet")
        print(f"Weapon: {self.equipped_weapon or 'None'}")
        print(f"Armor: {self.equipped_armor or 'None'}")
        print(f"Enemies defeated: {self.enemies_defeated}")
        print(f"Bosses defeated: {len(self.bosses_defeated)}")
        print("Potions:")
        if self.potions:
            for potion_name, quantity in self.potions.items():
                print(f"  - {potion_name}: {quantity}")
        else:
            print("  - None")
        print("=" * 42 + "\n")
