"""Entry point for Legends of the Forgotten Realm."""

from menus import main_menu


def main() -> None:
    """Start the game and keep returning to the main menu until exit."""
    while True:
        choice = main_menu()

        if choice == "1":
            from menus import create_new_player, player_hub

            player = create_new_player()
            if player is not None and player_hub(player) == "exit":
                print("\nThank you for visiting Eldoria. Farewell, adventurer!")
                break
        elif choice == "2":
            from menus import continue_game, player_hub

            player = continue_game()
            if player is not None and player_hub(player) == "exit":
                print("\nThank you for visiting Eldoria. Farewell, adventurer!")
                break
        elif choice == "3":
            print_instructions()
        elif choice == "4":
            print("\nThank you for visiting Eldoria. Farewell, adventurer!")
            break
        else:
            print("Please choose a valid option (1-4).")


def print_instructions() -> None:
    """Show basic instructions for the current development milestone."""
    print(
        "\nHOW TO PLAY\n"
        "-----------\n"
        "1. Create a character and choose a class.\n"
        "2. Choose Explore in the adventure hub to start a battle.\n"
        "3. Use Attack, class Skills, Heal, Potions, or Defend strategically.\n"
        "4. Visit Inventory & Equipment to equip, unequip, drop, or sell eligible items.\n"
        "5. Buy equipment and 15 potion types at the Village Shop.\n"
        "6. Use the World Map to view regions and boss gates.\n"
        "7. Defeat enemies to earn gold, EXP, and a chance at bonus loot.\n"
        "8. Loot may include weapons, armor, potions, and regional materials.\n"
        "9. Higher-level enemies have better loot chances; rarity follows the project drop table.\n"
        "10. Every 5 levels unlocks a passive bonus; every 10 levels, defeat the boss to progress.\n"
        "11. Bosses use special attacks, can critically hit, may heal, and grant Rare-or-better gear.\n"
        "12. Save your game from the adventure hub.\n\n"
        "Healing costs 15 mana and restores up to 30% of maximum HP.\n"
        "Gear adds weapon damage, defense, HP, mana, critical chance, and critical resistance.\n"
        "Buff potions last for three completed combat turns.\n"
        "Materials can be sold or dropped; the final quest sigil cannot be sold or dropped.\n"
        "There are 50 enemy types and 10 boss encounters up to Level 100.\n"
        "After defeat, choose Retry, Load Save, or Exit from the Game Over menu.\n"
    )


if __name__ == "__main__":
    main()
