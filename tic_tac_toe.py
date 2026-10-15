import random
def computer_move(board):
    empty_cells = [
        index for index in range(9)
        if board[index] == " "
    ]
    if empty_cells:
        position = random.choice(empty_cells)
        board[position] = "O"
        print(f"Computer chooses cell {position + 1}.")
def display_board(board):
    print()
    print(f" {board[0]} | {board[1]} | {board[2]} ")
    print("---+---+---")
    print(f" {board[3]} | {board[4]} | {board[5]} ")
    print("---+---+---")
    print(f" {board[6]} | {board[7]} | {board[8]} ")
    print()
def check_winner(board, mark):
    winning_combinations = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    ]
    for first, second, third in winning_combinations:
        if board[first] == board[second] == board[third] == mark:
            return True
    return False
def get_move(board, player_name, mark):
    while True:
        choice = input(
            f"{player_name} ({mark}), choose a cell (1-9): "
        ).strip()
        if not choice:
            print("Input cannot be empty. Please enter a number from 1 to 9.")
            continue
        try:
            position = int(choice)
        except ValueError:
            print("Invalid input. Please enter a whole number from 1 to 9.")
            continue
        if position < 1 or position > 9:
            print("Out of range. Choose a cell from 1 to 9.")
            continue
        index = position - 1
        if board[index] in ("X", "O"):
            print("That cell is already occupied. Choose another cell.")
            continue
        return index
def play_round():
    board = [" " for _ in range(9)]
    players = [("Player 1", "X"), ("Player 2", "O")]
    turn = 0
    print("\nWelcome to Tic-Tac-Toe!")
    print("Choose a cell by entering its number:")
    display_board(board)
    while True:
        player_name, mark = players[turn]
        index = get_move(board, player_name, mark)
        board[index] = mark
        display_board(board)
        if check_winner(board, mark):
            print(f"{player_name} ({mark}) wins!")
            return mark
        if all(cell in ("X", "O") for cell in board):
            print("It's a draw!")
            return None
        turn = 1 - turn
def play_computer_round():
    board = [" " for _ in range(9)]
    print("\nYou are X, and the computer is O.")
    display_board(board)
    while True:
        index = get_move(board, "Player", "X")
        board[index] = "X"
        display_board(board)
        if check_winner(board, "X"):
            print("Congratulations! You win!")
            return
        if all(cell != " " for cell in board):
            print("It's a draw!")
            return
        print("Computer's turn...")
        computer_move(board)
        display_board(board)
        if check_winner(board, "O"):
            print("Computer wins! Better luck next time.")
            return
        if all(cell != " " for cell in board):
            print("It's a draw!")
            return
def ask_play_again():
    while True:
        answer = input("Would you like to play again? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter 'y' for yes or 'n' for no.")
def choose_game_mode():
    while True:
        print("\n===== TIC-TAC-TOE =====")
        print("1. Player vs Player")
        print("2. Player vs Computer")
        print("3. Exit")
        choice = input("Choose a mode (1-3): ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Invalid choice! Please enter 1, 2, or 3.")
def main():
    while True:
        mode = choose_game_mode()
        if mode == "1":
            while True:
                play_round()
                if not ask_play_again():
                    break
        elif mode == "2":
            while True:
                play_computer_round()
                if not ask_play_again():
                    break
        elif mode == "3":
            print("Thanks for playing Tic-Tac-Toe. Goodbye!")
            break
if __name__ == "__main__":
    main()
