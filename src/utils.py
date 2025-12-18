"""
Utility helpers and validation logic for a terminal Battleship game.

This module contains:
- Global game constants
- Coordinate conventions and conversions
- Ship and fleet validation helpers

No user input, file I/O, or random generation is implemented here.
"""


# =========================
# Constants
# =========================

BOARD_SIZE = 10

# Exact fleet definition (multiset of ship lengths)
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

# =========================
# Coordinate helpers
# =========================

def in_bounds(coord):
    """Return True if coordinate is within the board."""
    r, c = coord
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def coord_to_str(coord):
    """
    Convert (row, col) -> 'A1' style string.
    Row 0 -> A, Col 0 -> 1
    """
    r, c = coord
    return f"{chr(ord('A') + r)}{c + 1}"


def str_to_coord(s):
    """
    Convert 'A1' style string -> (row, col).
    """
    s = s.strip().upper()
    if len(s) < 2:
        raise ValueError(f"Invalid coordinate string: {s}")
    row_char = s[0]
    col_part = s[1:]

    r = ord(row_char) - ord('A')
    c = int(col_part) - 1
    return (r, c)


def coords_to_str(ship):
    """
    Convert a ship (list of coordinates) to CSV-friendly string.
    Example: [(0,0),(0,1),(0,2)] -> 'A1,A2,A3'
    """
    return ",".join(coord_to_str(c) for c in ship)


def str_to_coords(s):
    """
    Convert CSV-friendly ship string to list of coordinates.
    Example: 'A1,A2,A3' -> [(0,0),(0,1),(0,2)]
    """
    if not s.strip():
        return []
    return [str_to_coord(part) for part in s.split(",")]


# =========================
# Adjacency helpers
# =========================

def get_adjacent_and_diagonal_cells(coord):
    """
    Return all adjacent cells (8-directional) around coord,
    excluding the coord itself.
    """
    r, c = coord
    neighbors = []

    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))

    return neighbors


# =========================
# Ship validation helpers
# =========================

def _is_straight_and_consecutive(ship):
    """
    Check that a ship is either horizontal or vertical
    and consists of consecutive cells without gaps.
    """
    if len(ship) <= 1:
        return True

    rows = [r for r, _ in ship]
    cols = [c for _, c in ship]

    if len(set(rows)) == 1:
        # horizontal
        sorted_cols = sorted(cols)
        return sorted_cols == list(range(min(sorted_cols), max(sorted_cols) + 1))

    if len(set(cols)) == 1:
        # vertical
        sorted_rows = sorted(rows)
        return sorted_rows == list(range(min(sorted_rows), max(sorted_rows) + 1))

    return False


def ships_touch_or_overlap(ships):
    """
    Return True if any ships overlap or touch each other
    (including diagonally).
    """
    cell_to_ship = {}

    for idx, ship in enumerate(ships):
        for coord in ship:
            # Overlap check
            if coord in cell_to_ship:
                return True
            cell_to_ship[coord] = idx

    for coord, idx in cell_to_ship.items():
        for neighbor in get_adjacent_and_diagonal_cells(coord):
            if neighbor in cell_to_ship and cell_to_ship[neighbor] != idx:
                return True

    return False


def validate_ship_fleet(ships):
    """
    Validate a full fleet of ships.

    Checks:
    - All coordinates are in bounds
    - Ships are straight and consecutive
    - Fleet sizes match SHIP_SIZES exactly
    - Ships do not touch or overlap (8-direction adjacency)

    Returns:
        (True, None) if valid
        (False, error_message) otherwise
    """
    # Empty ships are not allowed
    if any(len(ship) == 0 for ship in ships):
        return False, "Empty ship detected"

    # Bounds check
    for ship in ships:
        for coord in ship:
            if not in_bounds(coord):
                return False, f"Coordinate out of bounds: {coord_to_str(coord)}"

    # Shape check
    for ship in ships:
        if not _is_straight_and_consecutive(ship):
            return False, f"Ship is not straight or consecutive: {coords_to_str(ship)}"

    # Fleet size check
    lengths = sorted(len(ship) for ship in ships)
    expected = sorted(SHIP_SIZES)
    if lengths != expected:
        return (
            False,
            f"Invalid fleet composition. Expected {expected}, got {lengths}",
        )

    # Touching / overlap check
    if ships_touch_or_overlap(ships):
        return False, "Ships overlap or touch each other"

    return True, None
