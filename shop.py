"""Inventory management and village shop menus."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from equipment import ARMOR, POTION_CATALOG, WEAPONS, get_potion
from player import Player


def _read_number(prompt: str, minimum: int, maximum: int) -> int | None:
    """Read a bounded integer; return None if the player cancels with 0."""
    while True:
        value = input(prompt).strip()
        if value == "0":
            return None
        if value.isdigit() and minimum <= int(value) <= maximum:
            return int(value)
        print(f"Enter a number from {minimum} to {maximum}, or 0 to cancel.")


def _item_label(item: dict[str, Any]) -> str:
    if item.get("type") == "weapon":
        return (
            f"{item['name']} [{item['rank']}] — +{item['damage']} attack, "
            f"+{float(item.get('critical_bonus', 0)):.0%} crit"
        )
    if item.get("type") == "armor":
        return (
            f"{item['name']} [{item['rank']}] — +{item['defense_bonus']} DEF, "
            f"+{item['hp_bonus']} HP, +{item['mana_bonus']} mana"
        )
    return str(item.get("name", "Unknown item"))


def inventory_menu(player: Player) -> None:
    """Inspect, equip, unequip, or drop inventory items."""
    while True:
        print("\nINVENTORY & EQUIPMENT")
        print("=" * 64)
        print(f"Weapon: {player.equipped_weapon or 'None'} (+{player.weapon_damage_bonus} attack)")
        print(f"Armor: {player.equipped_armor or 'None'} (+{player.armor_defense_bonus} defense)")
        print(f"Effective attack: {player.total_attack} | Effective defense: {player.total_defense}")
        print("\nGear:")
        gear = [item for item in player.inventory if isinstance(item, dict) and item.get("type") in {"weapon", "armor"}]
        if not gear:
            print("  No weapons or armor in your inventory.")
        else:
            for item in gear:
                equipped = item.get("name") in {player.equipped_weapon, player.equipped_armor}
                marker = " [EQUIPPED]" if equipped else ""
                print(f"  - {_item_label(item)}{marker}")
        print("\nMaterials & quest items:")
        other_items = [
            item for item in player.inventory
            if isinstance(item, dict) and item.get("type") in {"material", "quest"}
        ]
        if other_items:
            for item in other_items:
                rank = f" [{item['rank']}]" if item.get("rank") else ""
                print(f"  - {item.get('name', 'Unknown item')}{rank}")
        else:
            print("  None")
        print("\nPotions:")
        if player.potions:
            for name, quantity in sorted(player.potions.items()):
                print(f"  - {name} x{quantity}")
        else:
            print("  None")
        print("\n1. Equip weapon")
        print("2. Equip armor")
        print("3. Unequip weapon")
        print("4. Unequip armor")
        print("5. Drop an item (unequipped gear, material, or potion)")
        print("6. Sell items")
        print("0. Back")
        choice = input("Choose an action: ").strip()

        if choice == "1":
            _equip_from_inventory(player, "weapon")
        elif choice == "2":
            _equip_from_inventory(player, "armor")
        elif choice == "3":
            if not player.equipped_weapon:
                print("No weapon is currently equipped.")
            else:
                player.equipped_weapon = None
                player.clamp_resources()
                print("Weapon unequipped.")
        elif choice == "4":
            if not player.equipped_armor:
                print("No armor is currently equipped.")
            else:
                player.equipped_armor = None
                player.clamp_resources()
                print("Armor unequipped.")
        elif choice == "5":
            _drop_item(player)
        elif choice == "6":
            sell_menu(player)
        elif choice == "0":
            return
        else:
            print("Choose a valid option from 0 to 6.")


def _equip_from_inventory(player: Player, item_type: str) -> None:
    eligible = [
        item for item in player.inventory
        if isinstance(item, dict)
        and item.get("type") == item_type
        and int(item.get("required_level", 1)) <= player.level
    ]
    label = "weapon" if item_type == "weapon" else "armor"
    if not eligible:
        print(f"You have no {label} you can equip at your current level.")
        return

    print(f"\nCHOOSE {label.upper()}")
    for index, item in enumerate(eligible, start=1):
        print(f"{index}. {_item_label(item)} (requires level {item.get('required_level', 1)})")
    print("0. Cancel")
    choice = _read_number("Select item: ", 1, len(eligible))
    if choice is None:
        return

    selected = eligible[choice - 1]
    setattr(player, f"equipped_{item_type}", selected["name"])
    player.clamp_resources()
    print(f"Equipped {selected['name']}.")


def _drop_item(player: Player) -> None:
    """Drop unequipped gear or a potion from the player's inventory."""
    droppable: list[tuple[str, dict[str, Any] | None, str | None, int]] = []
    for item in player.inventory:
        if not isinstance(item, dict) or item.get("type") not in {"weapon", "armor", "material"}:
            continue
        if item.get("name") in {player.equipped_weapon, player.equipped_armor}:
            continue
        droppable.append((str(item.get("name", "Unknown item")), item, None, 1))
    for name, quantity in sorted(player.potions.items()):
        if quantity > 0:
            droppable.append((f"{name} (x{quantity})", None, name, quantity))

    if not droppable:
        print("You have no items to drop. Equipped gear must be unequipped first.")
        return
    print("\nDROP ITEM (this cannot be undone)")
    for index, (label, item, _potion_name, quantity) in enumerate(droppable, start=1):
        if item is not None:
            print(f"{index}. {_item_label(item)}")
        else:
            print(f"{index}. {label}")
    print("0. Cancel")
    choice = _read_number("Select item: ", 1, len(droppable))
    if choice is None:
        return
    label, item, potion_name, quantity = droppable[choice - 1]
    if item is not None:
        player.inventory.remove(item)
        print(f"Dropped {item.get('name', 'item')}.")
    elif potion_name:
        try:
            quantity_text = input(f"How many {potion_name} (1-{quantity})? ").strip()
            if not quantity_text.isdigit() or not 1 <= int(quantity_text) <= quantity:
                print("Invalid quantity; nothing dropped.")
                return
            drop_quantity = int(quantity_text)
        except (ValueError, EOFError):
            print("Invalid quantity; nothing dropped.")
            return
        player.potions[potion_name] -= drop_quantity
        if player.potions[potion_name] <= 0:
            del player.potions[potion_name]
        print(f"Dropped {drop_quantity} x {potion_name}.")


def shop_menu(player: Player) -> None:
    """Open the village shop with buying and selling options."""
    while True:
        print("\nVILLAGE SHOP")
        print("=" * 40)
        print(f"Gold: {player.gold}")
        print("1. Buy weapons")
        print("2. Buy armor")
        print("3. Buy potions")
        print("4. Sell items")
        print("0. Leave shop")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            _buy_gear(player, WEAPONS, "WEAPONS")
        elif choice == "2":
            _buy_gear(player, ARMOR, "ARMOR")
        elif choice == "3":
            _buy_potions(player)
        elif choice == "4":
            sell_menu(player)
        elif choice == "0":
            print("You leave the village shop.")
            return
        else:
            print("Choose a valid option from 0 to 4.")


def _buy_gear(player: Player, catalog: list[dict[str, Any]], heading: str) -> None:
    print(f"\n{heading}")
    print("-" * 76)
    owned_names = {
        item.get("name") for item in player.inventory
        if isinstance(item, dict) and item.get("type") in {"weapon", "armor"}
    }
    for index, item in enumerate(catalog, start=1):
        locked = player.level < int(item["required_level"])
        status = f"LOCKED: level {item['required_level']}" if locked else "Available"
        if item["name"] in owned_names:
            status = "Already owned"
        print(f"{index:2}. {_item_label(item)} | {item['price']} gold | {status}")
    print("0. Cancel")
    choice = _read_number("Choose an item to buy: ", 1, len(catalog))
    if choice is None:
        return

    selected = catalog[choice - 1]
    if player.level < int(selected["required_level"]):
        print(f"You need to reach level {selected['required_level']} to buy that item.")
        return
    if selected["name"] in owned_names:
        print("You already own this item.")
        return
    if player.gold < int(selected["price"]):
        print(f"Not enough gold. You need {selected['price']} gold.")
        return

    player.gold -= int(selected["price"])
    player.inventory.append(deepcopy(selected))
    print(f"Purchased {selected['name']}! Use Inventory & Equipment to equip it.")


def _buy_potions(player: Player) -> None:
    print("\nPOTIONS")
    for index, potion in enumerate(POTION_CATALOG, start=1):
        print(f"{index:2}. {potion['name']} — {potion['price']} gold | {potion['description']}")
    print("0. Cancel")
    choice = _read_number("Choose a potion: ", 1, len(POTION_CATALOG))
    if choice is None:
        return

    potion = POTION_CATALOG[choice - 1]
    try:
        quantity_text = input("Quantity to buy: ").strip()
        if not quantity_text.isdigit() or int(quantity_text) < 1:
            print("Quantity must be a positive whole number.")
            return
        quantity = int(quantity_text)
    except (ValueError, EOFError):
        print("Invalid quantity.")
        return

    total_cost = int(potion["price"]) * quantity
    if player.gold < total_cost:
        affordable = player.gold // int(potion["price"])
        print(f"Not enough gold. You can afford at most {affordable} at this price.")
        return

    player.gold -= total_cost
    name = str(potion["name"])
    player.potions[name] = player.potions.get(name, 0) + quantity
    print(f"Purchased {quantity} x {name} for {total_cost} gold.")


def sell_menu(player: Player) -> None:
    """Sell unequipped gear or potions for half of their listed purchase price."""
    candidates: list[tuple[str, dict[str, Any] | None, str | None, int]] = []
    for item in player.inventory:
        if not isinstance(item, dict) or item.get("type") not in {"weapon", "armor", "material"}:
            continue
        if item.get("name") in {player.equipped_weapon, player.equipped_armor}:
            continue
        original_price = int(item.get("price", 0))
        candidates.append((str(item.get("name", "Unknown item")), item, None, max(1, original_price // 2)))

    for name, quantity in player.potions.items():
        if quantity <= 0:
            continue
        potion = get_potion(name)
        if potion:
            candidates.append((f"{name} (x{quantity})", None, name, max(1, int(potion["price"]) // 2)))

    if not candidates:
        print("You have nothing eligible to sell. Equipped gear cannot be sold.")
        return

    print("\nSELL ITEMS (receive 50% of listed price)")
    for index, (label, _item, _potion_name, sell_price) in enumerate(candidates, start=1):
        print(f"{index}. {label} — {sell_price} gold each")
    print("0. Cancel")
    choice = _read_number("Choose an item to sell: ", 1, len(candidates))
    if choice is None:
        return

    label, item, potion_name, sell_price = candidates[choice - 1]
    if item is not None:
        player.inventory.remove(item)
        print(f"Sold {item['name']} for {sell_price} gold.")
    elif potion_name:
        try:
            quantity_text = input(f"How many {potion_name} (1-{player.potions[potion_name]})? ").strip()
            if not quantity_text.isdigit() or not 1 <= int(quantity_text) <= player.potions[potion_name]:
                print("Invalid quantity; no items sold.")
                return
            quantity = int(quantity_text)
        except (KeyError, ValueError, EOFError):
            print("Invalid quantity; no items sold.")
            return
        player.potions[potion_name] -= quantity
        if player.potions[potion_name] <= 0:
            del player.potions[potion_name]
        sell_price *= quantity
        print(f"Sold {quantity} x {potion_name} for {sell_price} gold.")
    player.gold += sell_price
