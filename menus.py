"""Command-line menus for the first development milestone."""

import json
import time

from player import CLASS_STATS, Player
from save_manager import list_saves, load_player, save_player
from shop import inventory_menu, shop_menu
from world import BOSSES, REGIONS, next_boss, region_for_level


def main_menu() -> str:
    print("\n" + "=" * 54)
    print("       LEGENDS OF THE FORGOTTEN REALM")
    print("=" * 54)
    print("1. New Game")
    print("2. Continue")
    print("3. Instructions")
    print("4. Exit")
    return input("Choose an option: ").strip()


def game_over_menu() -> str:
    """Show recovery options after the hero falls in battle."""
    print("\n" + "=" * 34)
    print("             GAME OVER")
    print("=" * 34)
    print("1. Retry (restore your hero and try again)")
    print("2. Load Save")
    print("3. Exit")
    while True:
        choice = input("Choose an option: ").strip()
        if choice in {"1", "2", "3"}:
            return choice
        print("Please choose 1 (Retry), 2 (Load Save), or 3 (Exit).")


def create_new_player() -> Player | None:
    print("\nCHARACTER CREATION\n------------------")
    while True:
        name = input("Enter your hero's name: ").strip()
        if name:
            break
        print("Name cannot be empty. Please try again.")

    class_names = list(CLASS_STATS)
    print("\nChoose your class:")
    for index, class_name in enumerate(class_names, start=1):
        print(f"{index}. {class_name}")

    while True:
        choice = input("Class (1-4): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(class_names):
            character_class = class_names[int(choice) - 1]
            break
        print("Please enter a number from 1 to 4.")

    player = Player.create(name, character_class)
    print(f"\nWelcome, {player.name} the {player.character_class}!")
    print("Your journey through Eldoria begins now.")
    return player


def continue_game() -> Player | None:
    saves = list_saves()
    if not saves:
        print("\nNo saved games found. Start a New Game first.")
        return None

    print("\nAVAILABLE SAVES\n---------------")
    for index, path in enumerate(saves, start=1):
        print(f"{index}. {path.stem}")
    print("0. Cancel")

    while True:
        choice = input("Choose a save to load: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(saves):
            try:
                player = load_player(saves[int(choice) - 1])
                print(f"\nWelcome back, {player.name}!")
                return player
            except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
                print(f"Could not load that save: {error}")
                return None
        print(f"Please enter a number from 1 to {len(saves)}, or 0 to cancel.")


def show_world_map(player: Player) -> None:
    """Display the region route and each boss gate's current status."""
    current_region = region_for_level(player.level)
    upcoming_boss = next_boss(player)
    print("\n" + "=" * 58)
    print("                       WORLD MAP")
    print("=" * 58)
    print("Village (safe hub) -> Forest -> Cave -> Desert -> Ruins -> Castle")
    print("                 -> Volcano -> Frozen Mountain -> Sky Temple -> Demon Realm")
    print(f"\nCurrent region: {current_region['name']} (Level {player.level})")
    print(current_region["description"])
    print("\nREGION PROGRESSION")
    for region in REGIONS:
        is_open = player.level >= int(region["min_level"])
        if region["min_level"] <= player.level <= region["max_level"]:
            status = "CURRENT"
        elif is_open:
            status = "UNLOCKED"
        else:
            boss_gate = int(region["min_level"]) - 1
            boss_name = next((boss["name"] for boss in BOSSES if boss["level"] == boss_gate), None)
            status = f"LOCKED — defeat {boss_name}" if boss_name else f"LOCKED — reach Level {region['min_level']}"
        print(f"  {region['name']:<18} Levels {region['min_level']:>2}-{region['max_level']:<3} {status}")

    print("\nBOSS GATES")
    defeated = set(player.bosses_defeated)
    for boss in BOSSES:
        if boss["name"] in defeated:
            status = "DEFEATED"
        elif player.level >= boss["level"]:
            status = "CHALLENGE READY — choose Explore"
        else:
            status = f"Reach Level {boss['level']}"
        print(f"  Level {boss['level']:>3}: {boss['name']:<22} {status}")
    if upcoming_boss:
        print(f"\nNext boss: {upcoming_boss['name']} at Level {upcoming_boss['level']}.")
    else:
        print("\nAll bosses defeated. Eldoria is safe!")
    print("=" * 58)


def player_hub(player: Player) -> str | None:
    """Adventure hub for exploring, managing gear, shopping, and saving."""
    session_started_at = time.monotonic()
    player._session_started_at = session_started_at
    while True:
        region = region_for_level(player.level)
        print(f"\n--- {player.name}'s Adventure ---")
        print(f"Region: {region['name']} | Level {player.level} | HP {player.hp}/{player.total_max_hp} | Gold {player.gold}")
        print("1. Explore (find an enemy or challenge a boss)")
        print("2. View Stats")
        print("3. Inventory & Equipment")
        print("4. Village Shop")
        print("5. World Map")
        print("6. Save Game")
        print("7. Return to Main Menu")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            from battle import battle

            result = battle(player)
            if result == "defeat":
                # Keep the last save untouched. Recovery is explicit after defeat.
                while True:
                    game_over_choice = game_over_menu()
                    if game_over_choice == "1":
                        player.total_play_time_seconds += max(0, int(time.monotonic() - session_started_at))
                        player.hp = player.total_max_hp
                        player.mana = player.total_max_mana
                        session_started_at = time.monotonic()
                        player._session_started_at = session_started_at
                        print("Your hero has recovered. Prepare for another attempt!")
                        break
                    if game_over_choice == "2":
                        loaded_player = continue_game()
                        if loaded_player is None:
                            # Stay on the Game Over menu if loading was cancelled or failed.
                            continue
                        player = loaded_player
                        session_started_at = time.monotonic()
                        player._session_started_at = session_started_at
                        break
                    return "exit"
            elif result == "final_victory":
                # The final victory screen already saves its own summary.
                return "victory"
        elif choice == "2":
            player.display_stats()
        elif choice == "3":
            inventory_menu(player)
        elif choice == "4":
            shop_menu(player)
        elif choice == "5":
            show_world_map(player)
        elif choice == "6":
            try:
                player.total_play_time_seconds += max(0, int(time.monotonic() - session_started_at))
                session_started_at = time.monotonic()
                player._session_started_at = session_started_at
                path = save_player(player)
                print(f"Game saved successfully: {path.name}")
            except OSError as error:
                print(f"Could not save the game: {error}")
        elif choice == "7":
            return
        else:
            print("Please choose a valid option (1-7).")

