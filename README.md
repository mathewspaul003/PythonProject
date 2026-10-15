# Tic-Tac-Toe Game (Python)

## Project overview
A console-based Tic-Tac-Toe game built with Python 3. It supports:
- **Player vs Player:** Player 1 uses `X` and Player 2 uses `O`.
- **Player vs Computer:** The human uses `X`; the computer uses `O` and chooses a random available cell.

## Requirements
- Python 3.x
- No external libraries required. The computer opponent uses Python's built-in `random` module.

## How to run
1. Keep `README_TicTacToe_Updated.md` and your `tic_tac_toe.py` file in your project folder.
2. Open a terminal or command prompt in that folder.
3. Run:

   ```bash
   python tic_tac_toe.py
   ```

   On some systems, use `python3 tic_tac_toe.py` instead.

## How to play
1. Choose a mode from the main menu:
   - `1` for Player vs Player
   - `2` for Player vs Computer
   - `3` to exit
2. Enter a cell number from 1 to 9 when prompted. Positions are arranged left to right, top to bottom:

   ```text
   1 | 2 | 3
   --+---+---
   4 | 5 | 6
   --+---+---
   7 | 8 | 9
   ```

   The numbers indicate positions only; the game board itself can display blank cells.
3. The first player to make three marks in a row, column, or diagonal wins.
4. If all nine cells are filled without a winner, the round is a draw.
5. After a round, enter `y` to play another round or `n` to return to the main menu.

## Features
- 3x3 console board
- Player vs Player mode
- Player vs Computer mode with random computer moves
- Input validation for empty, non-numeric, out-of-range, and occupied-cell choices
- Win detection for rows, columns, and diagonals
- Draw detection
- Play-again option
- Functions and comments for readability

## Python concepts demonstrated
Variables, lists, functions, `while` and `for` loops, conditional statements, string methods, exception handling, and basic input validation.
