"""
Bot ship generation for the Battleship game.

This module randomly generates a valid fleet for the bot,
validates it using src.utils, and saves it to CSV.
"""

import csv
import os
import random

from src.utils import (
    BOARD_SIZE,
    SHIP_SIZES,
    validate_ship_fleet,
    coords_to_str,
)


# =========================
# Internal helpers
# =========================

def _random_ship(size):
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


def _save_ships_to_csv(ships, csv_path):
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
    csv_path="data/bot_ships.csv",
):
    """
    Generate a valid random fleet for the bot, save it to CSV,
    and return the list of ships.
    """
    while True:
        ships = []

        for size in SHIP_SIZES:
            ships.append(_random_ship(size))

        valid, _ = validate_ship_fleet(ships)
        if not valid:
            continue

        _save_ships_to_csv(ships, csv_path)
        return ships
