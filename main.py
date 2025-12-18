"""
Entry point for the terminal Battleship game.

This script:
- Sets up required directories
- Collects player ship placements
- Generates bot ship placements
- Initializes the game state
- Runs the main gameplay loop
- Logs all turns to data/game_state.csv

If data/game_state.csv already exists, it will be overwritten.
"""

import os
import sys

from src.ship_input import get_and_save_player_ships
from src.bot_generation import generate_and_save_bot_ships
from src.gameplay import GameState
from src.utils import str_to_coords, coord_to_str


DATA_DIR = "data"
OUTPUTS_DIR = "outputs"
GAME_STATE_CSV = os.path.join(DATA_DIR, "game_state.csv")


# =========================
# Helper functions
# =========================

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def truncate_game_state_csv():
    """
    Overwrite existing game_state.csv at game start
    to ensure a clean log for each new game.
    """
    if os.path.exists(GAME_STATE_CSV):
        with open(GAME_STATE_CSV, "w", encoding="utf-8"):
            pass


def prompt_player_move(game):
    """
    Prompt the player for a move and return a Coord.
    Expected format: A1. Checks if the move was already tried.
    """
    from src.gameplay import UNKNOWN
    while True:
        raw = input("Enter your move (e.g. A1): ").strip()
        try:
            coords = str_to_coords(raw)
            if len(coords) != 1:
                raise ValueError
            
            coord = coords[0]
            r, c = coord
            
            if game.player_board[r][c] != UNKNOWN:
                print(f"You already fired at {raw}. Try another coordinate.")
                continue
                
            return coord
        except Exception:
            print("Invalid coordinate. Please use format like A1.")


def print_boards(game):
    """
    Print the current state of both boards.
    """
    print("\nYour shots on the bot's board:")
    _print_board(game.player_board)

    print("\nBot's shots on your board:")
    _print_board(game.bot_board)


def _print_board(board):
    header = "  " + " ".join(str(i + 1) for i in range(len(board)))
    print(header)
    for i, row in enumerate(board):
        line = chr(ord("A") + i) + " " + " ".join(row)
        print(line)


# =========================
# Main game loop
# =========================

def main():
    ensure_directories()
    truncate_game_state_csv()

    print("=== Battleship ===\n")

    try:
        # Ship placement
        player_ships = get_and_save_player_ships()
        bot_ships = generate_and_save_bot_ships()

        # Initialize game state
        game = GameState.from_fleets(player_ships, bot_ships)

        print("\nGame start!\n")

        current_turn = "player"

        # Gameplay loop
        while True:
            print_boards(game)

            if current_turn == "player":
                print("\n--- YOUR TURN ---")
                player_coord = prompt_player_move(game)
                player_result, _ = game.apply_player_move(player_coord)
                
                print(f"\nYou shoot at {coord_to_str(player_coord)} -> {player_result.upper()}")

                # Log turn (using dummy bot info if it's player's streak)
                game.log_turn(GAME_STATE_CSV, player_coord, player_result, (0,0), "n/a")

                if game.all_bot_ships_sunk():
                    print_boards(game)
                    print("\nYou win! All bot ships are sunk.")
                    break

                if player_result == "miss":
                    current_turn = "bot"
            else:
                print("\n--- BOT'S TURN ---")
                bot_coord, bot_result = game.bot_take_turn()
                print(f"Bot shoots at {coord_to_str(bot_coord)} -> {bot_result.upper()}")

                # Log turn (using dummy player info if it's bot's streak)
                game.log_turn(GAME_STATE_CSV, (0,0), "n/a", bot_coord, bot_result)

                if game.all_player_ships_sunk():
                    print("\nYou lose! All your ships are sunk.")
                    break

                if bot_result == "miss":
                    current_turn = "player"

        print(f"\nGame data saved in '{DATA_DIR}/'.")

    except KeyboardInterrupt:
        print("\n\nGame interrupted. Exiting gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
