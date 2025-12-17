"""
Core gameplay state, CSV logging, and bot AI for the Battleship game.

This module defines:
- Internal game state
- Move application and sink handling
- CSV logging of turns
- A simple but intelligent bot AI (random → hunt → locked)

Board serialization format:
- Each board is a 10x10 grid flattened row-wise into a single string.
- Cell encoding:
    'U' = unknown
    'H' = hit
    'M' = miss
"""

import csv
import os
import random

from src.utils import (
    BOARD_SIZE,
    coords_to_str,
    get_adjacent_and_diagonal_cells,
    in_bounds,
)

# =========================
# Board cell constants
# =========================

UNKNOWN = "U"
HIT = "H"
MISS = "M"

# =========================
# Bot AI modes
# =========================

BOT_RANDOM = "RANDOM"
BOT_HUNT = "HUNT"
BOT_LOCKED = "LOCKED"


# =========================
# GameState
# =========================

class GameState:
    """
    Core game state container, including bot AI logic.
    """

    def __init__(
        self,
        player_ships,
        bot_ships,
    ):
        self.player_ships = player_ships
        self.bot_ships = bot_ships

        self.player_board = self._empty_board()  # player shots on bot
        self.bot_board = self._empty_board()     # bot shots on player

        self._player_hits = set()
        self._bot_hits = set()

        self.turn_number = 0

        # =========================
        # Bot AI state
        # =========================
        self.bot_mode = BOT_RANDOM
        self.bot_hit_chain = []      # consecutive hits on same ship
        self.bot_candidates = set()   # candidate cells to try next
        self.bot_tried = set()         # all bot shots taken

    # =========================
    # Construction
    # =========================

    @classmethod
    def from_fleets(
        cls,
        player_fleet,
        bot_fleet,
    ):
        """Create a GameState from player and bot fleets."""
        return cls(player_fleet, bot_fleet)

    @staticmethod
    def _empty_board():
        return [[UNKNOWN for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    # =========================
    # Player & bot move application
    # =========================

    def apply_player_move(self, coord):
        """Apply a player move against the bot's ships."""
        return self._apply_move(
            coord,
            self.bot_ships,
            self.player_board,
            self._player_hits,
        )

    def apply_bot_move(self, coord):
        """Apply a bot move against the player's ships."""
        return self._apply_move(
            coord,
            self.player_ships,
            self.bot_board,
            self._bot_hits,
        )

    def _apply_move(
        self,
        coord,
        target_ships,
        board,
        hit_set,
    ):
        """
        Core logic for applying a move to a board.
        """
        r, c = coord
        if board[r][c] != UNKNOWN:
            return ("miss", False)

        for ship in target_ships:
            if coord in ship:
                board[r][c] = HIT
                hit_set.add(coord)

                if self._is_ship_destroyed(ship, hit_set):
                    self._mark_surroundings_as_miss(ship, board)
                    return ("sink", True)

                return ("hit", False)

        board[r][c] = MISS
        return ("miss", False)

    # =========================
    # Ship helpers
    # =========================

    @staticmethod
    def _is_ship_destroyed(ship, hit_set):
        return all(coord in hit_set for coord in ship)

    def _mark_surroundings_as_miss(
        self,
        ship,
        board,
    ):
        for coord in ship:
            for adj in get_adjacent_and_diagonal_cells(coord):
                r, c = adj
                if board[r][c] == UNKNOWN:
                    board[r][c] = MISS

    # =========================
    # Bot AI logic
    # =========================

    def choose_bot_move(self):
        """
        Decide the bot's next move based on AI state.
        """
        if self.bot_mode == BOT_RANDOM:
            return self._choose_random_move()

        if self.bot_mode == BOT_HUNT:
            return self._choose_from_candidates()

        if self.bot_mode == BOT_LOCKED:
            return self._choose_locked_move()

        return self._choose_random_move()

    def bot_take_turn(self):
        """
        Bot chooses a move, applies it, and updates AI state.
        Returns (coord, result).
        """
        coord = self.choose_bot_move()
        self.bot_tried.add(coord)

        result, sunk = self.apply_bot_move(coord)

        if result == "hit":
            self._on_bot_hit(coord)
        elif result == "sink":
            self._on_bot_sink()
        else:
            self._on_bot_miss(coord)

        return coord, result

    # =========================
    # Bot AI state transitions
    # =========================

    def _on_bot_hit(self, coord):
        self.bot_hit_chain.append(coord)

        if len(self.bot_hit_chain) == 1:
            self.bot_mode = BOT_HUNT
            self._add_adjacent_candidates(coord)

        elif len(self.bot_hit_chain) >= 2:
            self.bot_mode = BOT_LOCKED
            self._lock_axis_and_expand_candidates()

    def _on_bot_miss(self, coord):
        self.bot_candidates.discard(coord)

        if self.bot_mode == BOT_LOCKED:
            # Remove dead-end direction, keep trying others
            self.bot_candidates.discard(coord)

    def _on_bot_sink(self):
        self.bot_mode = BOT_RANDOM
        self.bot_hit_chain.clear()
        self.bot_candidates.clear()

    # =========================
    # Bot AI helpers
    # =========================

    def _choose_random_move(self):
        """Pick a random untried cell."""
        all_cells = [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if (r, c) not in self.bot_tried
        ]
        return random.choice(all_cells)

    def _choose_from_candidates(self):
        """Choose next move from candidate cells."""
        valid = [
            c for c in self.bot_candidates
            if c not in self.bot_tried
        ]
        if not valid:
            self.bot_mode = BOT_RANDOM
            return self._choose_random_move()
        return random.choice(valid)

    def _choose_locked_move(self):
        """Choose next move along locked axis."""
        valid = [
            c for c in self.bot_candidates
            if c not in self.bot_tried
        ]
        if not valid:
            self.bot_mode = BOT_RANDOM
            return self._choose_random_move()
        return random.choice(valid)

    def _add_adjacent_candidates(self, coord):
        """Add orthogonal neighbors as candidates."""
        r, c = coord
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds((nr, nc)) and (nr, nc) not in self.bot_tried:
                self.bot_candidates.add((nr, nc))

    def _lock_axis_and_expand_candidates(self):
        """
        Lock orientation after second hit and expand candidates
        along that axis only.
        """
        if len(self.bot_hit_chain) < 2:
            return

        c1, c2 = self.bot_hit_chain[-2], self.bot_hit_chain[-1]
        r1, c1c = c1
        r2, c2c = c2

        self.bot_candidates.clear()

        if r1 == r2:
            # horizontal
            row = r1
            cols = sorted(c for _, c in self.bot_hit_chain)
            for nc in (cols[0] - 1, cols[-1] + 1):
                coord = (row, nc)
                if in_bounds(coord) and coord not in self.bot_tried:
                    self.bot_candidates.add(coord)
        else:
            # vertical
            col = c1c
            rows = sorted(r for r, _ in self.bot_hit_chain)
            for nr in (rows[0] - 1, rows[-1] + 1):
                coord = (nr, col)
                if in_bounds(coord) and coord not in self.bot_tried:
                    self.bot_candidates.add(coord)

    # =========================
    # Board serialization
    # =========================

    @staticmethod
    def serialize_board(board):
        return "".join(board[r][c] for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    @staticmethod
    def deserialize_board(s):
        board = GameState._empty_board()
        idx = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                board[r][c] = s[idx]
                idx += 1
        return board

    # =========================
    # CSV logging
    # =========================

    def log_turn(
        self,
        csv_path,
        player_move,
        player_result,
        bot_move,
        bot_result,
    ):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        file_exists = os.path.exists(csv_path)

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow([
                    "turn_number",
                    "player_move_coord",
                    "player_move_result",
                    "bot_move_coord",
                    "bot_move_result",
                    "player_board_serialized",
                    "bot_board_serialized",
                ])

            writer.writerow([
                self.turn_number,
                coords_to_str([player_move]),
                player_result,
                coords_to_str([bot_move]),
                bot_result,
                self.serialize_board(self.player_board),
                self.serialize_board(self.bot_board),
            ])

        self.turn_number += 1

    # =========================
    # Endgame checks
    # =========================

    def all_player_ships_sunk(self):
        return all(
            self._is_ship_destroyed(ship, self._bot_hits)
            for ship in self.player_ships
        )

    def all_bot_ships_sunk(self):
        return all(
            self._is_ship_destroyed(ship, self._player_hits)
            for ship in self.bot_ships
        )
