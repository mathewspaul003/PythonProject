# Legends of the Forgotten Realm

**Legends of the Forgotten Realm** is a Python 3 command-line, turn-based RPG created for the Python major project assignment. Play as a Warrior, Mage, Archer, or Assassin, explore the realm, collect gear, defeat regional bosses, and challenge the Ancient Demon King at Level 100.

## Requirements

- Python 3.10 or newer
- No third-party packages are required

## Repository layout

All game modules are stored directly in the repository root, so you do not need a `game/` folder.

```text
Legends-of-the-Forgotten-Realm/
├── main.py
├── player.py
├── menus.py
├── battle.py
├── equipment.py
├── shop.py
├── loot.py
├── world.py
├── save_manager.py
├── README_LEGENDS.md
├── SUBMISSION_CHECKLIST.md
├── .gitignore
└── tests/
    ├── test_battle.py
    ├── test_equipment.py
    ├── test_loot.py
    ├── test_submission_readiness.py
    └── test_world.py
```

### Main modules

| File | Responsibility |
| --- | --- |
| `main.py` | Starts the game and opens the main menu. |
| `player.py` | Player character data, class stats, equipment-derived stats, and level-up passives. |
| `menus.py` | Main menu, character creation, adventure hub, Game Over menu, and World Map display. |
| `battle.py` | Turn-based combat, skills, enemy encounters, experience, level-ups, and boss fights. |
| `equipment.py` | Weapon, armor, potion, rarity, and material catalogues. |
| `shop.py` | Inventory operations and the village shop. |
| `loot.py` | Enemy loot drops and rarity-based item selection. |
| `world.py` | Regions, boss catalogue, and progression gates. |
| `save_manager.py` | JSON save/load and listing saved characters. |
| `tests/` | Automated tests for the game's core mechanics. |

## Run the game

1. Download or clone this repository.
2. Open the repository root in VS Code.
3. Open **Terminal → New Terminal**.
4. Run:

   ```bash
   python main.py
   ```

On systems where Python 3 is invoked as `python3`, use `python3 main.py` instead.

## Run automated tests

From the repository root, run:

```bash
python -m unittest discover -s tests -v
```

The test suite covers combat damage and skills, equipment and potions, save/load, level-up passives, Game Over recovery, loot drops, enemy and boss catalogues, boss gates, and progression through Level 100.

## Gameplay features

### Character creation and saves

- Four playable classes: Warrior, Mage, Archer, and Assassin, each with distinct starting stats and class skills.
- Player name, level, EXP, HP, mana, attack, defense, critical chance, gold, inventory, equipment, and progress tracking.
- JSON save/load, including migration for older saves that lack starter equipment.

### Combat and progression

- Turn-based combat options: Attack, Skills, Heal, Use Potion, Defend, Inventory, View Stats, and Run.
- Critical hits, armor critical resistance, stun, poison, temporary buffs, and evasion.
- Enemy stats and rewards scale with player level.
- 50 enemy archetypes across level ranges 1–100.
- Level-ups increase HP, mana, attack, and defense; every five levels unlock a passive bonus.
- Ten boss encounters at Levels 10, 20, ..., 100. Bosses have special attacks, critical hits, healing, and guaranteed Rare-or-better gear rewards.
- Boss gates prevent progression past a required level until the boss is defeated.
- Defeating the Ancient Demon King ends the game and awards the `Demon King's Sigil` quest item.

### Equipment, inventory, and shop

- 21 weapons across Common, Uncommon, Rare, Super Rare, Epic, Mythical, and Legendary tiers.
- 14 armor sets with defense, HP, mana, and critical-resistance bonuses.
- 15 potion types covering health, mana, mixed restoration, and temporary buffs.
- Buy eligible weapons, armor, and potions from the Village Shop; sell or drop eligible inventory items; equip and unequip gear.
- Equipment bonuses affect combat stats and maximum HP/mana.

### Loot and world

- Enemies award normal EXP and gold and can additionally drop equipment, potions, or regional materials.
- Rarity-weighted equipment/material selection follows the assignment's rarity weights, restricted to gear tiers appropriate to the player's level.
- Bosses guarantee a Rare-or-better weapon or armor reward.
- Regional materials include Slime Gel, Goblin Ear, Spider Silk, Ancient Bark, Scorpion Chitin, Cursed Sigil, Ember Core, Celestial Shard, and Demon Essence. Materials can be sold or dropped and persist in JSON saves.
- Nine regions are displayed in the World Map, leading toward the Demon Realm.
- The final victory screen summarizes character progress, boss/enemy defeats, collected weapons and rare items, play time, gold, and score.

## Controls

- **Main menu:** New Game, Continue, Instructions, Exit.
- **Adventure hub:** Explore, View Stats, Inventory & Equipment, Village Shop, World Map, Save Game, Return to Main Menu.
- **Combat:** Attack, Skills, Heal, Use Potion, Defend, Inventory, View Stats, Run.
- **Inventory:** Equip/unequip gear, drop eligible items, and sell eligible inventory items.
- **Village Shop:** Buy eligible weapons, armor, and potions or sell eligible items.

## Save files and Git

Game saves are created locally in the `saves/` directory. The included `.gitignore` excludes this directory and common Python temporary files, so personal save files and virtual environments should not be committed to GitHub.

## Assignment alignment

This project is designed to cover the assignment's major requirements: modular Python code, character creation, OOP-based player state, input validation, exception handling, JSON save/load, turn-based combat, skills, equipment, potions, shop, random loot, enemy and boss catalogues, level progression, and a final victory summary. The automated tests help validate key mechanics; manually play through the game before submitting it.
