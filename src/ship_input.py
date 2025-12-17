"""
User input handling for placing player ships.

This module is responsible for:
- Prompting the user to enter ship coordinates
- Parsing and validating the input using src.utils
- Saving a valid fleet to CSV

No game logic or bot logic is implemented here.
"""

import csv
import os

from src.utils import (
    SHIP_SIZES,
    validate_ship_fleet,
    str_to_coords,
    coords_to_str,
)


# =========================
# Input helpers
# =========================

def _prompt_ship(size, index, total):
    """
    Prompt the user to enter coordinates for a single ship.

    Input format:
        A1 A2 A3   (space-separated coordinates)

    Returns a Ship (list of Coord).
    """
    while True:
        if total > 1:
            prompt = f"Enter coordinates for ship of size {size} ({index + 1} of {total}): "
        else:
            prompt = f"Enter coordinates for ship of size {size}: "

        raw = input(prompt).strip()

        try:
            parts = raw.split()
            ship = []
            for part in parts:
                ship.extend(str_to_coords(part))
        except Exception:
            print("Invalid format. Use space-separated coordinates like: A1 A2 A3")
            continue

        if len(ship) != size:
            print(f"Expected exactly {size} coordinates, got {len(ship)}.")
            continue

        return ship


def _collect_fleet():
    """
    Prompt the user to enter all ships according to SHIP_SIZES.
    Returns a list of Ship objects (not yet globally validated).
    """
    ships = []

    size_counts = {}
    for size in SHIP_SIZES:
        size_counts[size] = size_counts.get(size, 0) + 1

    for size, count in sorted(size_counts.items(), reverse=True):
        for i in range(count):
            ship = _prompt_ship(size, i, count)
            ships.append(ship)

    return ships


# =========================
# CSV helpers
# =========================

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

def get_and_save_player_ships(
    csv_path="data/player_ships.csv",
):
    """
    Prompt the user to place all ships, validate the fleet,
    save it to CSV, and return the list of ships.
    """
    while True:
        print("\nPlace your ships on a 10x10 board.")
        print("Coordinates format: A1 A2 A3 (space-separated)\n")

        ships = _collect_fleet()

        valid, error = validate_ship_fleet(ships)
        if not valid:
            print(f"\nFleet validation failed: {error}")
            print("Please re-enter all ships.\n")
            continue

        _save_ships_to_csv(ships, csv_path)
        print(f"\nShips saved successfully to {csv_path}\n")
        return ships
