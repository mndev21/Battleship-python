"""
Bot ship generation for the Battleship game.

This module randomly generates a valid fleet for the bot,
validates it using src.utils, and saves it to CSV.
"""

from __future__ import annotations

import csv
import os
import random
from typing import List

from src.utils import (
    BOARD_SIZE,
    SHIP_SIZES,
    Ship,
    Coord,
    validate_ship_fleet,
    coords_to_str,
)


# =========================
# Internal helpers
# =========================

def _random_ship(size: int) -> Ship:
    """
    Generate a random straight ship of given size within board bounds.
    Does not check for overlap or touching with other ships.
    """
    orientation = random.choice(("H", "V"))

    if orientation == "H":
        row = random.randrange(BOARD_SIZE)
        col_start = random.randrange(BOARD_SIZE - size + 1)
        return [(row, col_start + i) for i in range(size)]
    else:
        col = random.randrange(BOARD_SIZE)
        row_start = random.randrange(BOARD_SIZE - size + 1)
        return [(row_start + i, col) for i in range(size)]


def _save_ships_to_csv(ships: List[Ship], csv_path: str) -> None:
    """
    Save ships to CSV file.
    One row per ship: ship_id, size, coordinates
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ship_id", "size", "coordinates"])

        for ship_id, ship in enumerate(ships):
            writer.writerow([
                ship_id,
                len(ship),
                coords_to_str(ship),
            ])


# =========================
# Public API
# =========================

def generate_and_save_bot_ships(
    csv_path: str = "data/bot_ships.csv",
) -> List[Ship]:
    """
    Generate a valid random fleet for the bot, save it to CSV,
    and return the list of ships.
    """
    while True:
        ships: List[Ship] = []

        for size in SHIP_SIZES:
            ships.append(_random_ship(size))

        valid, _ = validate_ship_fleet(ships)
        if not valid:
            continue

        _save_ships_to_csv(ships, csv_path)
        return ships
