"""JSON save/load helpers."""

import json
import re
from pathlib import Path
from typing import Any

from player import Player

PROJECT_ROOT = Path(__file__).resolve().parent
SAVE_DIR = PROJECT_ROOT / "saves"


def _filename_for(name: str) -> str:
    """Make a safe, predictable JSON filename from a player name."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).strip("_")
    return f"{slug or 'hero'}.json"


def save_player(player: Player) -> Path:
    """Save player data and return the save-file path."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = SAVE_DIR / _filename_for(player.name)
    with path.open("w", encoding="utf-8") as save_file:
        json.dump(player.to_dict(), save_file, indent=4)
    return path


def list_saves() -> list[Path]:
    """Return all available save files, sorted by filename."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(SAVE_DIR.glob("*.json"), key=lambda path: path.name.lower())


def load_player(path: Path) -> Player:
    """Load a player from a JSON save file."""
    # Only permit loading files that are directly inside our save directory.
    resolved_path = path.resolve()
    resolved_dir = SAVE_DIR.resolve()
    if resolved_path.parent != resolved_dir or resolved_path.suffix.lower() != ".json":
        raise ValueError("Invalid save-file path.")

    with resolved_path.open("r", encoding="utf-8") as save_file:
        data: Any = json.load(save_file)

    if not isinstance(data, dict):
        raise ValueError("Save file has an invalid format.")
    return Player.from_dict(data)
