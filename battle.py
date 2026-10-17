"""Turn-based combat, class skills, enemies, and battle rewards."""

from __future__ import annotations

import random
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from player import Player
from equipment import ARMOR, WEAPONS, get_item, get_potion
from loot import award_enemy_loot
from world import pending_boss, region_for_level


@dataclass
class Enemy:
    """An enemy instance with scaled stats and optional boss abilities."""

    name: str
    level: int
    max_hp: int
    hp: int
    attack: int
    defense: int
    experience_reward: int
    gold_reward: int
    is_boss: bool = False
    stunned_turns: int = 0
    poisoned_turns: int = 0
    turn_count: int = 0
    critical_chance: float = 0.05
    special_attacks: tuple[tuple[str, float], ...] = ()
    boss_heal_percent: float = 0.0
    boss_heals_used: int = 0


# Fifty enemy types, grouped into level ranges. The first three ranges also
# preserve the enemy families suggested in the assignment brief.
_ENEMY_ROWS: tuple[tuple[str, int, int, int, int, int, int, int], ...] = (
    # Name, minimum level, maximum level, HP, attack, defense, EXP, gold
    ("Slime", 1, 10, 38, 8, 2, 35, 10),
    ("Goblin", 1, 10, 46, 10, 3, 40, 14),
    ("Wolf", 1, 10, 52, 12, 2, 42, 15),
    ("Zombie", 1, 10, 56, 11, 4, 45, 16),
    ("Skeleton", 1, 10, 58, 12, 5, 48, 18),
    ("Orc", 11, 20, 95, 22, 8, 90, 35),
    ("Bandit", 11, 20, 82, 24, 5, 88, 38),
    ("Troll", 11, 20, 125, 25, 12, 105, 42),
    ("Dark Archer", 11, 20, 78, 27, 4, 100, 40),
    ("Giant Spider", 11, 20, 88, 23, 7, 98, 39),
    ("Vampire", 21, 30, 160, 35, 12, 150, 65),
    ("Werewolf", 21, 30, 175, 38, 10, 160, 70),
    ("Necromancer", 21, 30, 145, 42, 8, 170, 75),
    ("Ice Golem", 21, 30, 220, 34, 19, 175, 72),
    ("Fire Demon", 21, 30, 190, 44, 13, 185, 80),
    ("Sand Scorpion", 21, 30, 175, 40, 13, 180, 78),
    ("Mummy", 21, 30, 185, 37, 16, 178, 76),
    ("Dust Wraith", 21, 30, 155, 45, 9, 188, 82),
    ("Dune Stalker", 21, 30, 170, 43, 12, 190, 84),
    ("Sand Golem", 21, 30, 245, 39, 21, 200, 90),
    ("Wraith", 31, 40, 250, 48, 17, 230, 105),
    ("Cursed Knight", 31, 40, 300, 47, 25, 240, 110),
    ("Bone Priest", 31, 40, 235, 53, 14, 245, 112),
    ("Ruin Golem", 31, 40, 340, 45, 29, 250, 115),
    ("Stone Guardian", 31, 40, 320, 49, 27, 255, 118),
    ("Vampire Knight", 41, 50, 365, 60, 26, 300, 140),
    ("Gargoyle", 41, 50, 390, 57, 30, 305, 145),
    ("Royal Guard", 41, 50, 350, 63, 32, 310, 150),
    ("Blood Mage", 41, 50, 315, 68, 21, 315, 155),
    ("Banshee", 41, 50, 325, 66, 20, 320, 158),
    ("Magma Beast", 51, 60, 440, 76, 31, 365, 180),
    ("Ember Drake", 51, 60, 420, 82, 29, 375, 188),
    ("Ashen Warlock", 51, 60, 385, 88, 24, 380, 192),
    ("Lava Serpent", 51, 60, 455, 79, 33, 385, 195),
    ("Infernal Brute", 51, 60, 490, 75, 38, 390, 200),
    ("Frost Wolf", 61, 70, 510, 92, 35, 430, 220),
    ("Ice Revenant", 61, 70, 485, 97, 32, 438, 225),
    ("Snow Troll", 61, 70, 600, 90, 42, 440, 230),
    ("Glacier Witch", 61, 70, 470, 102, 28, 445, 235),
    ("Yeti", 61, 70, 620, 94, 45, 455, 240),
    ("Storm Harpy", 71, 80, 585, 110, 39, 490, 260),
    ("Thunder Sentinel", 71, 80, 670, 106, 48, 500, 270),
    ("Cloud Serpent", 71, 80, 610, 116, 40, 505, 275),
    ("Celestial Adept", 71, 80, 560, 121, 35, 515, 280),
    ("Sky Reaver", 71, 80, 650, 114, 44, 520, 285),
    ("Hellhound", 81, 100, 720, 132, 47, 560, 315),
    ("Doomguard", 81, 100, 820, 126, 58, 570, 325),
    ("Abyssal Reaper", 81, 100, 700, 141, 42, 585, 335),
    ("Soul Eater", 81, 100, 750, 137, 45, 590, 340),
    ("Void Stalker", 81, 100, 735, 145, 43, 600, 350),
)

ENEMY_ARCHETYPES: tuple[dict[str, int | str], ...] = tuple(
    {
        "name": name,
        "min_level": min_level,
        "max_level": max_level,
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "exp": exp,
        "gold": gold,
    }
    for name, min_level, max_level, hp, attack, defense, exp, gold in _ENEMY_ROWS
)

# Every class has four skills. Effects are interpreted by use_skill().
SKILLS: dict[str, list[dict[str, Any]]] = {
    "Warrior": [
        {"name": "Slash", "mana": 5, "damage": 1.45, "description": "A powerful weapon strike."},
        {"name": "Shield Bash", "mana": 8, "damage": 0.9, "stun": 1, "description": "Damage and stun the enemy for one turn."},
        {"name": "Rage", "mana": 10, "buff": 1.5, "buff_turns": 3, "description": "Increase attack by 50% for three attacks."},
        {"name": "Earthquake", "mana": 20, "damage": 2.3, "description": "Deal massive area-shaking damage."},
    ],
    "Mage": [
        {"name": "Fireball", "mana": 8, "damage": 1.5, "description": "Launch a ball of fire."},
        {"name": "Ice Blast", "mana": 12, "damage": 1.25, "stun": 1, "description": "Blast the enemy with ice and freeze it briefly."},
        {"name": "Thunder Strike", "mana": 18, "damage": 1.9, "description": "Strike the enemy with lightning."},
        {"name": "Meteor", "mana": 30, "damage": 2.7, "description": "Call down a devastating meteor."},
    ],
    "Archer": [
        {"name": "Multi Shot", "mana": 8, "damage": 0.65, "hits": 3, "description": "Fire three arrows in quick succession."},
        {"name": "Poison Arrow", "mana": 10, "damage": 1.0, "poison": 3, "description": "Poison the enemy for three turns."},
        {"name": "Explosive Arrow", "mana": 16, "damage": 1.8, "description": "Deal explosive damage."},
        {"name": "Sniper Shot", "mana": 22, "damage": 2.4, "description": "Fire a precise, high-damage shot."},
    ],
    "Assassin": [
        {"name": "Backstab", "mana": 6, "damage": 1.6, "description": "Strike a vulnerable point."},
        {"name": "Smoke Bomb", "mana": 8, "evade": 1, "description": "Avoid the enemy's next attack."},
        {"name": "Shadow Strike", "mana": 16, "damage": 2.1, "description": "Attack from the shadows."},
        {"name": "Instant Kill", "mana": 25, "damage": 1.4, "instant_kill_chance": 0.05, "description": "A risky strike with a 5% instant-kill chance."},
    ],
}


def calculate_damage(
    attack: float,
    defense: int,
    multiplier: float = 1.0,
    critical: bool = False,
    critical_multiplier: float = 1.5,
) -> int:
    """Calculate damage using the assignment formula, never dealing less than 1."""
    damage = max(1, int(attack * multiplier) - defense)
    if critical:
        damage = max(1, int(damage * critical_multiplier))
    return damage


def create_enemy(player_level: int) -> Enemy:
    """Create a normal enemy from the hero's level band and scale its stats."""
    level = max(1, min(100, int(player_level)))
    eligible = [enemy for enemy in ENEMY_ARCHETYPES
                if int(enemy["min_level"]) <= level <= int(enemy["max_level"])]
    archetype = random.choice(eligible or list(ENEMY_ARCHETYPES))
    level_delta = level - 1
    hp = int(archetype["hp"]) + level_delta * 8
    attack = int(archetype["attack"]) + level_delta * 2
    defense = int(archetype["defense"]) + level_delta // 4
    return Enemy(
        name=str(archetype["name"]),
        level=level,
        max_hp=hp,
        hp=hp,
        attack=attack,
        defense=defense,
        experience_reward=int(archetype["exp"]) + level_delta * 12,
        gold_reward=random.randint(int(archetype["gold"]), int(archetype["gold"]) + 10)
        + level_delta * 3,
    )


def create_boss(player_level: int, definition: dict[str, Any]) -> Enemy:
    """Create a boss with two special attacks, critical hits, and healing."""
    level = max(int(definition["level"]), min(100, int(player_level)))
    hp = 280 + level * 23
    return Enemy(
        name=str(definition["name"]),
        level=level,
        max_hp=hp,
        hp=hp,
        attack=20 + level * 3,
        defense=5 + int(level * 0.4),
        experience_reward=experience_to_next_level(min(level, 99)) + 150,
        gold_reward=150 + level * 25,
        is_boss=True,
        critical_chance=0.12,
        special_attacks=tuple(definition["special_attacks"]),
        boss_heal_percent=float(definition.get("heal_percent", 0.10)),
    )


def create_encounter(player: Player) -> Enemy:
    """Force a boss when its level gate is reached; otherwise spawn a normal enemy."""
    boss = pending_boss(player)
    if boss is not None:
        return create_boss(player.level, boss)
    return create_enemy(player.level)


def experience_to_next_level(level: int) -> int:
    """Return the total EXP needed to advance from this level."""
    return 100 + level * 25


def award_experience(player: Player, amount: int) -> None:
    """Grant EXP and grow stats without crossing an undefeated boss gate."""
    player.experience += amount
    print(f"You gained {amount} EXP.")

    while player.level < 100 and player.experience >= experience_to_next_level(player.level):
        # Reaching a boss level is allowed, but crossing it is blocked until victory.
        waiting_boss = pending_boss(player)
        if waiting_boss is not None:
            print(f"Level progression is sealed. Defeat {waiting_boss['name']} before advancing!")
            break
        player.experience -= experience_to_next_level(player.level)
        player.level += 1
        player.max_hp += 15
        player.max_mana += 10
        player.attack += 3
        player.defense += 2
        if player.level % 3 == 0:
            player.crit_chance = min(0.60, player.crit_chance + 0.01)
        passive = player.unlock_passive_for_level(player.level) if player.level % 5 == 0 else None
        player.hp = player.total_max_hp
        player.mana = player.total_max_mana
        print("\n" + "*" * 46)
        print(f"LEVEL UP! {player.name} reached Level {player.level}!")
        print("+15 Max HP | +10 Max Mana | +3 Attack | +2 Defense")
        if player.level % 3 == 0:
            print("+1% Critical Chance")
        if passive is not None:
            print(f"PASSIVE UNLOCKED: {passive['name']} — {passive['description']}")
        print("HP and mana have been fully restored.")
        print("*" * 46)


def _show_enemy(enemy: Enemy) -> None:
    print("\n" + "=" * 52)
    if enemy.is_boss:
        print(f"BOSS CHALLENGE: {enemy.name} — Level {enemy.level}")
        print("This boss guards the level gate. Prepare for powerful attacks and healing!")
    else:
        region = region_for_level(enemy.level)
        print(f"Region: {region['name']} | A wild {enemy.name} appears! (Level {enemy.level})")
    print(f"Enemy HP: {enemy.hp}/{enemy.max_hp} | ATK: {enemy.attack} | DEF: {enemy.defense}")
    print("=" * 52)


def _show_battle_menu(player: Player, enemy: Enemy) -> None:
    print(f"\nYOUR TURN  |  HP {player.hp}/{player.total_max_hp}  |  MP {player.mana}/{player.total_max_mana}")
    print(f"{enemy.name}: {enemy.hp}/{enemy.max_hp} HP")
    print("1. Attack")
    print("2. Skills")
    print("3. Heal")
    print("4. Use Potion")
    print("5. Defend")
    print("6. Inventory")
    print("7. View Stats")
    print("8. Run")


def _roll_player_damage(
    player: Player,
    enemy: Enemy,
    multiplier: float,
    attack_buff: float,
) -> tuple[int, bool]:
    critical_chance = min(
        0.75,
        player.total_crit_chance + float(getattr(player, "_battle_crit_bonus", 0.0)),
    )
    is_critical = random.random() < critical_chance
    damage = calculate_damage(
        attack=player.total_attack * attack_buff * float(getattr(player, "_battle_attack_bonus", 1.0)),
        defense=enemy.defense,
        multiplier=multiplier,
        critical=is_critical,
        critical_multiplier=player.crit_damage,
    )
    enemy.hp = max(0, enemy.hp - damage)
    if is_critical:
        print("\nCRITICAL HIT!")
    print(f"You dealt {damage} damage to {enemy.name}.")
    print(f"{enemy.name} HP: {enemy.hp}/{enemy.max_hp}")
    return damage, is_critical


def _attack(player: Player, enemy: Enemy, attack_buff: float) -> None:
    _roll_player_damage(player, enemy, multiplier=1.0, attack_buff=attack_buff)


def _choose_skill(player: Player) -> dict[str, Any] | None:
    skills = SKILLS.get(player.character_class, [])
    print("\nCLASS SKILLS")
    for index, skill in enumerate(skills, start=1):
        print(f"{index}. {skill['name']} — {skill['mana']} mana | {skill['description']}")
    print("0. Back")

    while True:
        choice = input("Choose a skill: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(skills):
            return skills[int(choice) - 1]
        print(f"Please enter a number from 1 to {len(skills)}, or 0 to go back.")


def _use_skill(
    player: Player,
    enemy: Enemy,
    skill: dict[str, Any],
    battle_state: dict[str, Any],
) -> bool:
    """Use a class skill. Return False if it cannot be used this turn."""
    mana_cost = int(skill["mana"])
    if player.mana < mana_cost:
        print(f"Not enough mana for {skill['name']} (requires {mana_cost}).")
        return False

    player.mana -= mana_cost
    print(f"\n{player.name} uses {skill['name']}! (-{mana_cost} mana)")

    instant_kill_chance = float(skill.get("instant_kill_chance", 0.0))
    if instant_kill_chance and random.random() < instant_kill_chance:
        enemy.hp = 0
        print(f"A perfect strike! {enemy.name} was defeated instantly!")
        return True

    if "damage" in skill:
        hits = int(skill.get("hits", 1))
        for hit_number in range(hits):
            if enemy.hp <= 0:
                break
            if hits > 1:
                print(f"Hit {hit_number + 1}/{hits}:")
            _roll_player_damage(
                player,
                enemy,
                multiplier=float(skill["damage"]),
                attack_buff=float(battle_state["attack_buff"]),
            )

    stun_turns = int(skill.get("stun", 0))
    if stun_turns and enemy.hp > 0:
        enemy.stunned_turns = max(enemy.stunned_turns, stun_turns)
        print(f"{enemy.name} is stunned and will miss its next turn!")

    poison_turns = int(skill.get("poison", 0))
    if poison_turns and enemy.hp > 0:
        enemy.poisoned_turns = max(enemy.poisoned_turns, poison_turns)
        print(f"{enemy.name} is poisoned for {poison_turns} turns!")

    buff_multiplier = float(skill.get("buff", 1.0))
    if buff_multiplier > 1.0:
        battle_state["attack_buff"] = buff_multiplier
        battle_state["attack_buff_attacks"] = int(skill.get("buff_turns", 0))
        print(f"Your attack is increased by {int((buff_multiplier - 1) * 100)}% for "
              f"{battle_state['attack_buff_attacks']} attacks.")

    evade_turns = int(skill.get("evade", 0))
    if evade_turns:
        battle_state["evade_charges"] = evade_turns
        print("Smoke surrounds you. The next enemy attack will miss!")

    return True


def _show_inventory(player: Player) -> None:
    print("\nINVENTORY")
    print("---------")
    print(f"Equipped weapon: {player.equipped_weapon or 'None'} (+{player.weapon_damage_bonus} attack)")
    print(f"Equipped armor: {player.equipped_armor or 'None'} (+{player.armor_defense_bonus} defense)")
    print(f"Effective attack: {player.total_attack} | Effective defense: {player.total_defense}")
    if player.potions:
        for name, quantity in player.potions.items():
            print(f"{name}: {quantity}")
    else:
        print("No potions.")
    if player.inventory:
        print("Other items:")
        for item in player.inventory:
            if isinstance(item, dict):
                print(f"- {item.get('name', 'Unknown item')}")
            else:
                print(f"- {item}")
    else:
        print("No other items yet.")


def _use_potion(player: Player, battle_state: dict[str, Any] | None = None) -> bool:
    """Use a catalog potion, applying healing, mixed restoration, or a 3-turn buff."""
    available = [(name, qty) for name, qty in player.potions.items() if qty > 0]
    if not available:
        print("You have no potions.")
        return False

    if battle_state is None:
        battle_state = {}
    print("\nPOTIONS")
    for index, (name, quantity) in enumerate(available, start=1):
        potion = get_potion(name)
        description = potion.get("description", "") if potion else "Unknown potion type"
        print(f"{index}. {name} x{quantity} — {description}")
    print("0. Back")

    while True:
        choice = input("Choose a potion: ").strip()
        if choice == "0":
            return False
        if choice.isdigit() and 1 <= int(choice) <= len(available):
            potion_name, _quantity = available[int(choice) - 1]
            potion = get_potion(potion_name)
            if potion is None:
                # Old saves or manually edited files may contain unsupported potion names.
                print("This potion is not in the current catalog and cannot be used.")
                return False

            category = potion.get("category")
            effect_applied = False
            if category in {"health", "mixed"}:
                if potion.get("full_hp"):
                    restored_hp = max(0, player.total_max_hp - player.hp)
                else:
                    restored_hp = min(
                        int(potion.get("hp_restore", 0)),
                        max(0, player.total_max_hp - player.hp),
                    )
                player.hp += restored_hp
                if restored_hp:
                    print(f"You restored {restored_hp} HP.")
                    effect_applied = True

            if category in {"mana", "mixed"}:
                if potion.get("full_mana"):
                    restored_mana = max(0, player.total_max_mana - player.mana)
                else:
                    restored_mana = min(
                        int(potion.get("mana_restore", 0)),
                        max(0, player.total_max_mana - player.mana),
                    )
                player.mana += restored_mana
                if restored_mana:
                    print(f"You restored {restored_mana} mana.")
                    effect_applied = True

            if category == "buff":
                duration = int(potion.get("duration", 3))
                if "attack_buff" in potion:
                    battle_state["potion_attack_buff"] = float(potion["attack_buff"])
                    battle_state["potion_attack_turns"] = duration
                    battle_state.setdefault("buffs_applied_this_turn", set()).add("potion_attack_turns")
                    print(f"Attack increased for {duration} turns.")
                if "defense_buff" in potion:
                    battle_state["potion_defense_buff"] = float(potion["defense_buff"])
                    battle_state["potion_defense_turns"] = duration
                    battle_state.setdefault("buffs_applied_this_turn", set()).add("potion_defense_turns")
                    print(f"Defense increased for {duration} turns.")
                if "crit_buff" in potion:
                    battle_state["potion_crit_buff"] = float(potion["crit_buff"])
                    battle_state["potion_crit_turns"] = duration
                    battle_state.setdefault("buffs_applied_this_turn", set()).add("potion_crit_turns")
                    print(f"Critical chance increased for {duration} turns.")
                effect_applied = True

            if not effect_applied:
                print("Your HP and mana are already full. The potion was not consumed.")
                return False

            player.potions[potion_name] -= 1
            if player.potions[potion_name] <= 0:
                del player.potions[potion_name]
            return True
        print(f"Please enter a number from 1 to {len(available)}, or 0 to go back.")


def _advance_potion_buffs(battle_state: dict[str, Any]) -> None:
    """Advance existing potion timers, preserving the full duration of new buffs."""
    applied_this_turn = battle_state.get("buffs_applied_this_turn", set())
    for buff_key, turns_key, default_value in (
        ("potion_attack_buff", "potion_attack_turns", 1.0),
        ("potion_defense_buff", "potion_defense_turns", 1.0),
        ("potion_crit_buff", "potion_crit_turns", 0.0),
    ):
        if battle_state.get(turns_key, 0) > 0 and turns_key not in applied_this_turn:
            battle_state[turns_key] -= 1
            if battle_state[turns_key] == 0:
                battle_state[buff_key] = default_value
                label = buff_key.replace("potion_", "").replace("_buff", "")
                print(f"The {label} potion effect has worn off.")


def _enemy_turn(player: Player, enemy: Enemy, battle_state: dict[str, Any]) -> None:
    if enemy.hp <= 0:
        return

    enemy.turn_count += 1
    if enemy.poisoned_turns > 0:
        poison_damage = max(3, int(enemy.max_hp * 0.05))
        enemy.hp = max(0, enemy.hp - poison_damage)
        enemy.poisoned_turns -= 1
        print(f"Poison deals {poison_damage} damage to {enemy.name}.")
        if enemy.hp <= 0:
            print(f"{enemy.name} succumbed to poison!")
            return

    if enemy.stunned_turns > 0:
        enemy.stunned_turns -= 1
        print(f"{enemy.name} is stunned and cannot attack!")
        return

    if battle_state["evade_charges"] > 0:
        battle_state["evade_charges"] -= 1
        print(f"You evade {enemy.name}'s attack with your smoke bomb!")
        return

    # Bosses alternate between two special moves every third enemy turn.
    special_move: tuple[str, float] | None = None
    if enemy.is_boss and enemy.special_attacks and enemy.turn_count % 3 == 0:
        special_index = (enemy.turn_count // 3 - 1) % len(enemy.special_attacks)
        special_move = enemy.special_attacks[special_index]

    if enemy.is_boss and special_move is None and enemy.hp <= int(enemy.max_hp * 0.45):
        if enemy.boss_heals_used < 2 and random.random() < 0.25:
            restored = min(int(enemy.max_hp * enemy.boss_heal_percent), enemy.max_hp - enemy.hp)
            if restored > 0:
                enemy.hp += restored
                enemy.boss_heals_used += 1
                print(f"{enemy.name} uses dark regeneration and restores {restored} HP! ({enemy.hp}/{enemy.max_hp})")
                return

    defense_multiplier = float(battle_state.get("potion_defense_buff", 1.0))
    effective_defense = int(player.total_defense * defense_multiplier)
    multiplier = special_move[1] if special_move else 1.0
    incoming = max(1, int(enemy.attack * multiplier) - effective_defense)

    critical_chance = max(0.0, enemy.critical_chance - player.critical_resistance)
    if random.random() < critical_chance:
        incoming = max(1, int(incoming * 1.5))
        print(f"\n{enemy.name} lands a CRITICAL HIT!")

    defending = bool(battle_state["defending"])
    if defending:
        incoming = max(1, int(incoming * 0.5))
        print("Your defense stance reduces the incoming damage by about 50%.")

    if special_move:
        print(f"\n{enemy.name} unleashes {special_move[0]}!")
    else:
        print(f"{enemy.name} attacks!")
    player.hp = max(0, player.hp - incoming)
    print(f"{enemy.name} deals {incoming} damage.")
    print(f"Your HP: {player.hp}/{player.total_max_hp}")


def _award_boss_reward(player: Player, enemy: Enemy) -> None:
    """Give each defeated boss a guaranteed Rare-or-better gear reward."""
    from equipment import RARITY_ORDER

    rare_ranks = set(RARITY_ORDER[RARITY_ORDER.index("Rare"):])
    eligible = [
        item for item in [*WEAPONS, *ARMOR]
        if item.get("rank") in rare_ranks
        and int(item.get("required_level", 1)) <= min(100, player.level)
    ]
    if not eligible:
        eligible = [item for item in [*WEAPONS, *ARMOR] if item.get("rank") in rare_ranks]
    owned_names = {item.get("name") for item in player.inventory if isinstance(item, dict)}
    not_owned = [item for item in eligible if item["name"] not in owned_names]
    reward = deepcopy(random.choice(not_owned or eligible))
    player.inventory.append(reward)
    print(f"GUARANTEED BOSS REWARD: {reward['rank']} {reward['name']} added to your inventory!")


def _show_victory_summary(player: Player) -> None:
    """Print the end-game summary after the Ancient Demon King is defeated."""
    started = getattr(player, "_session_started_at", None)
    if started is not None:
        player.total_play_time_seconds += max(0, int(time.monotonic() - started))
        player._session_started_at = time.monotonic()
    elapsed = int(getattr(player, "total_play_time_seconds", 0))
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    weapons = [item for item in player.inventory if isinstance(item, dict) and item.get("type") == "weapon"]
    rare_items = [item for item in player.inventory if isinstance(item, dict) and item.get("rank") in {"Rare", "Super Rare", "Epic", "Mythical", "Legendary"}]
    score = player.level * 100 + player.enemies_defeated * 10 + len(player.bosses_defeated) * 250 + player.gold + len(rare_items) * 150
    print("\n" + "=" * 54)
    print("              ELDORIA HAS BEEN SAVED!")
    print("          ANCIENT DEMON KING DEFEATED")
    print("=" * 54)
    print(f"Hero: {player.name} the {player.character_class}")
    print(f"Final level: {player.level}")
    print(f"Total gold: {player.gold}")
    print(f"Bosses defeated: {len(player.bosses_defeated)}/10")
    print(f"Enemies defeated: {player.enemies_defeated}")
    print(f"Weapons collected: {len(weapons)}")
    print(f"Rare-or-better items found: {len(rare_items)}")
    print(f"Total play time: {hours:02}:{minutes:02}:{seconds:02}")
    print(f"Final score: {score}")
    print("The people of Eldoria will remember your name!")
    print("=" * 54)
    try:
        from save_manager import save_player
        saved_path = save_player(player)
        print(f"Victory progress saved to {saved_path.name}.")
    except OSError as error:
        print(f"Warning: could not auto-save victory progress: {error}")


def battle(player: Player) -> str:
    """Run one complete encounter. Return victory, defeat, or escaped."""
    enemy = create_encounter(player)
    _show_enemy(enemy)
    battle_state: dict[str, Any] = {
        "defending": False,
        "attack_buff": 1.0,
        "attack_buff_attacks": 0,
        "evade_charges": 0,
        "potion_attack_buff": 1.0,
        "potion_attack_turns": 0,
        "potion_defense_buff": 1.0,
        "potion_defense_turns": 0,
        "potion_crit_buff": 0.0,
        "potion_crit_turns": 0,
        "crit_buff": 0.0,
    }

    while player.hp > 0 and enemy.hp > 0:
        battle_state["buffs_applied_this_turn"] = set()
        battle_state["crit_buff"] = float(battle_state.get("potion_crit_buff", 0.0))
        player._battle_crit_bonus = battle_state["crit_buff"]
        player._battle_attack_bonus = float(battle_state.get("potion_attack_buff", 1.0))
        _show_battle_menu(player, enemy)
        choice = input("Choose your action (1-8): ").strip()
        completed_turn = False
        escaped = False

        if choice == "1":
            _attack(player, enemy, float(battle_state["attack_buff"]))
            completed_turn = True
        elif choice == "2":
            skill = _choose_skill(player)
            if skill is not None:
                completed_turn = _use_skill(player, enemy, skill, battle_state)
        elif choice == "3":
            heal_cost = 15
            if player.hp >= player.total_max_hp:
                print("Your HP is already full.")
            elif player.mana < heal_cost:
                print(f"Not enough mana to heal (requires {heal_cost}).")
            else:
                player.mana -= heal_cost
                restored = min(max(20, int(player.total_max_hp * 0.30)), player.total_max_hp - player.hp)
                player.hp += restored
                print(f"You spend {heal_cost} mana and restore {restored} HP.")
                completed_turn = True
        elif choice == "4":
            completed_turn = _use_potion(player, battle_state)
        elif choice == "5":
            battle_state["defending"] = True
            print("You brace yourself. The next incoming attack will deal 50% less damage.")
            completed_turn = True
        elif choice == "6":
            _show_inventory(player)
        elif choice == "7":
            player.display_stats()
        elif choice == "8":
            if random.random() < 0.55:
                print("You escaped safely from the encounter.")
                return "escaped"
            print("You failed to escape!")
            completed_turn = True
        else:
            print("Please choose a valid option from 1 to 8.")

        if not completed_turn:
            continue

        # Buff duration counts successful attacks/skills, not menu browsing.
        if choice == "1" or (choice == "2" and skill is not None and "damage" in skill):
            if battle_state["attack_buff_attacks"] > 0:
                battle_state["attack_buff_attacks"] -= 1
                if battle_state["attack_buff_attacks"] == 0:
                    battle_state["attack_buff"] = 1.0
                    print("Your attack buff has worn off.")

        if enemy.hp > 0:
            _enemy_turn(player, enemy, battle_state)
        battle_state["defending"] = False

        # Buffs used this turn retain their full duration for the next turns.
        _advance_potion_buffs(battle_state)

    if player.hp <= 0:
        print("\n" + "=" * 46)
        print("GAME OVER — you have been defeated.")
        print("Your last saved game is still available from the main menu.")
        print("=" * 46)
        return "defeat"

    print("\n" + "=" * 52)
    print(f"VICTORY! You defeated the {enemy.name}!")
    print(f"You found {enemy.gold_reward} gold.")
    player.gold += enemy.gold_reward
    player.enemies_defeated += 1
    if enemy.is_boss:
        if enemy.name not in player.bosses_defeated:
            player.bosses_defeated.append(enemy.name)
        print(f"BOSS DEFEATED: {enemy.name}")
        print("A region gate has opened!")
        _award_boss_reward(player, enemy)
        if enemy.name == "Ancient Demon King" and not any(
            isinstance(item, dict) and item.get("name") == "Demon King's Sigil"
            for item in player.inventory
        ):
            sigil = get_item("Demon King's Sigil")
            if sigil is not None:
                player.inventory.append(sigil)
                print("QUEST ITEM: Demon King's Sigil added to your inventory.")
    award_enemy_loot(player, enemy)
    award_experience(player, enemy.experience_reward)
    print("=" * 52)

    if enemy.name == "Ancient Demon King" and enemy.is_boss:
        _show_victory_summary(player)
        return "final_victory"
    if enemy.is_boss:
        print("World progress updated. Check the World Map to see the next region.")
    return "victory"
