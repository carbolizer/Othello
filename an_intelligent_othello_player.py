"""
Name: Carl A. Coleman Jr
Date: 11/29/2025
Assignment: CSC 475 - An Intelligent Othello Player
Description: This program implements the game of Othello (Reversi) with a
GUI and an AI opponent using the Mini-Max search algorithm with
alpha-beta pruning. It allows for human vs. AI, AI vs. AI, or
human vs. human play.
"""

import copy
import math
import sys
import time
import tkinter as tk
from tkinter import messagebox, Toplevel, Scale, Checkbutton, BooleanVar, IntVar

# --- Global Constants ---

# Using numbers for pieces is easier than strings
EMPTY = 0
BLACK = 1
WHITE = 2

# This is a handy trick for Othello. Instead of writing 8 different
# functions to check for flips (up, down, left, right, diagonals),
# we can just loop through this list of (row_delta, col_delta) tuples.
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),  # Above
    (0, -1), (0, 1),             # Sides
    (1, -1), (1, 0), (1, 1)      # Below
]

# This is our heuristic weight matrix.
# I learned about this from Othello strategy guides.
# Squares are weighted based on their strategic value.
# Corners (like [0][0]) are the best, so they have a high value.
# Squares next to corners (like [0][1]) are dangerous because they
# can let the opponent take the corner, so they have a very low value.
# Reference: https://courses.cs.washington.edu/courses/cse573/04au/Project/mini1/RUSSIA/Final_Paper.pdf
POSITIONAL_WEIGHTS = [
    [120, -20, 20,  5,  5, 20, -20, 120],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [ 20,  -5, 15,  3,  3, 15,  -5,  20],
    [  5,  -5,  3,  3,  3,  3,  -5,   5],
    [  5,  -5,  3,  3,  3,  3,  -5,   5],
    [ 20,  -5, 15,  3,  3, 15,  -5,  20],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [120, -20, 20,  5,  5, 20, -20, 120]
]

# --- Game Logic Class ---

class OthelloGame:
    """
    This is the main class for the Othello game LOGIC.
    It holds the board state and game rules, but NO GUI code.
    It's structured similarly to my NeuralNetwork class,
    where one class holds all the main logic.
    """

    def __init__(self):
        """
        Constructor to initialize the game state.
        """
        self.board_size = 8
        # We'll represent the board as a list of lists.
        self.board = self.create_board()
        self.current_player = BLACK  # Black always moves first

        # AI settings
        # Search depth should be easily adjustable.
        self.search_depth = 4  # Default depth
        # Ability to easily switch on/off alpha-beta pruning.
        self.alpha_beta_pruning = True
        # Debug mode to show move values.
        self.debug_mode = False
        # To count states for the report.
        self.states_examined = 0
        # To store debug info for the GUI
        self.debug_info = ""

    def create_board(self):
        """
        Initializes the 8x8 board with the 4 starting pieces.
        """
        board = [[EMPTY for _ in range(self.board_size)] for _ in range(self.board_size)]
        # Standard Othello starting position
        board[3][3] = WHITE
        board[3][4] = BLACK
        board[4][3] = BLACK
        board[4][4] = WHITE
        return board

    def get_score(self):
        """
        Counts the pieces for each player.
        """
        black_score = 0
        white_score = 0
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board[r][c] == BLACK:
                    black_score += 1
                elif self.board[r][c] == WHITE:
                    white_score += 1
        return black_score, white_score

    def get_tiles_to_flip(self, row, col, player):
        """
        This is the core game logic.
        Given a move (row, col) by a player, it finds all the
        opponent's pieces that would be flipped.
        It returns a list of (r, c) tuples to be flipped.
        If the move is invalid, it returns an empty list.
        """
        # Can't place a piece on an occupied square
        if not self.is_on_board(row, col) or self.board[row][col] != EMPTY:
            return []

        opponent = self.get_opponent(player)
        tiles_to_flip = []

        # We check all 8 directions from the placed piece
        for dr, dc in DIRECTIONS:
            r, c = row + dr, col + dc
            tiles_in_this_direction = []

            # Keep moving in one direction as long as we're on the board
            # and seeing the opponent's pieces.
            while self.is_on_board(r, c) and self.board[r][c] == opponent:
                tiles_in_this_direction.append((r, c))
                r += dr
                c += dc

            # If we moved off the board OR hit an empty square, this
            # direction is invalid.
            # But if we hit one of our OWN pieces, it's a valid "sandwich"
            # and we add all the pieces we passed over to the main flip list.
            if self.is_on_board(r, c) and self.board[r][c] == player:
                tiles_to_flip.extend(tiles_in_this_direction)

        return tiles_to_flip

    def is_valid_move(self, row, col, player):
        """
        A move is valid if it flips at least one opponent piece.
        """
        return bool(self.get_tiles_to_flip(row, col, player))

    def make_move(self, row, col, player):
        """
        Places a piece on the board and flips the appropriate tiles.
        Returns True if the move was successful, False otherwise.
        """
        tiles_to_flip = self.get_tiles_to_flip(row, col, player)
        if not tiles_to_flip:
            # This check is important for rejecting illegal moves
            return False

        # Make the move
        self.board[row][col] = player
        for r, c in tiles_to_flip:
            self.board[r][c] = player

        return True

    def get_valid_moves(self, player):
        """
        Gets a list of all valid moves (as (r, c) tuples) for the given player.
        """
        valid_moves = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.is_valid_move(r, c, player):
                    valid_moves.append((r, c))
        return valid_moves

    def is_game_over(self):
        """
        The game is over if neither player has a valid move.
        """
        has_black_moves = bool(self.get_valid_moves(BLACK))
        has_white_moves = bool(self.get_valid_moves(WHITE))
        return not has_black_moves and not has_white_moves

    def get_winner_message(self):
        """
        Called at the end of the game to declare the winner.
        """
        black_score, white_score = self.get_score()
        if black_score > white_score:
            return f"Black (X) wins: {black_score} to {white_score}"
        elif white_score > black_score:
            return f"White (O) wins: {white_score} to {black_score}"
        else:
            return f"It's a draw: {black_score} to {black_score}"

    # --- Helper Functions ---

    def get_opponent(self, player):
        """Simple helper to get the other player."""
        return WHITE if player == BLACK else BLACK

    def is_on_board(self, r, c):
        """Checks if a square is within the 8x8 grid."""
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def switch_player(self):
        """Switches the current player."""
        self.current_player = self.get_opponent(self.current_player)

    # --- AI Mini-Max ---

    def heuristic_evaluate(self, board_state, player):
        """
        This heuristic combines three factors:
        1. Positional Score: Using our POSITIONAL_WEIGHTS matrix.
        2. Mobility: How many moves does each player have?
        3. Coin Parity (Raw Score): Who has more pieces?
        """
        opponent = self.get_opponent(player)

        # 1. Positional Score
        player_pos_score = 0
        opp_pos_score = 0
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] == player:
                    player_pos_score += POSITIONAL_WEIGHTS[r][c]
                elif board_state[r][c] == opponent:
                    opp_pos_score += POSITIONAL_WEIGHTS[r][c]

        positional_score = player_pos_score - opp_pos_score

        # 2. Mobility Score
        # We need to get moves based on the *board_state* passed in,
        # not the main game board.  

        # This feels clunky, but it's the simplest way to re-use
        # the get_valid_moves logic on a hypothetical board state.
        temp_game = OthelloGame()
        temp_game.board = board_state

        player_moves = len(temp_game.get_valid_moves(player))
        opp_moves = len(temp_game.get_valid_moves(opponent))

        mobility_score = 0
        if (player_moves + opp_moves) != 0:
            mobility_score = 100 * (player_moves - opp_moves) / (player_moves + opp_moves)

        # 3. Coin Parity (Raw Score)
        player_coins = 0
        opp_coins = 0
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] == player:
                    player_coins += 1
                elif board_state[r][c] == opponent:
                    opp_coins += 1

        coin_parity = 0
        if (player_coins + opp_coins) != 0:
            coin_parity = 100 * (player_coins - opp_coins) / (player_coins + opp_coins)

        # Combine the scores with weights
        # The weights are a bit of trial and error.
        # Positional score is generally the most important.
        final_score = (10 * positional_score) + (2 * mobility_score) + (1 * coin_parity)

        return final_score


    def get_ai_move(self):
        """
        This is the main entry point for the AI.
        It sets up the minimax call and handles debug output.
        """
        self.states_examined = 0  # Reset counter for each move
        self.debug_info = "" # Reset debug info

        # We want to find the move that leads to the best score.
        best_move = None
        best_score = -math.inf

        # Alpha-beta pruning setup
        alpha = -math.inf
        beta = math.inf

        # For debug mode, we store all top-level move scores
        debug_move_scores = []

        valid_moves = self.get_valid_moves(self.current_player)

        # If no moves, just return None
        if not valid_moves:
            return None

        # Iterate through all possible first moves
        for move in valid_moves:
            r, c = move

            # We need a deep copy of the board to simulate the move
            # This is critical! My Neural Network backprop had a similar
            # idea where you can't mess up the original data.
            board_copy = copy.deepcopy(self.board)

            # Simulate the move on the copy
            # We can re-use the make_move logic.
            temp_game = OthelloGame()
            temp_game.board = board_copy
            temp_game.make_move(r, c, self.current_player)

            # Now, call minimax on the *opponent's* turn (minimizing player)
            # The depth is reduced by 1 because we've made one move.
            score = self.minimax(
                board_state=temp_game.board,
                player=self.get_opponent(self.current_player),
                depth=self.search_depth - 1,
                is_maximizing_player=False, # Opponent's turn, so they minimize
                alpha=alpha,
                beta=beta
            )

            if self.debug_mode:
                move_str = f"{chr(ord('a') + c)}{r+1}"
                debug_move_scores.append((move_str, score))

            if score > best_score:
                best_score = score
                best_move = move

            # Alpha update for the *maximizing* (top-level) player
            alpha = max(alpha, best_score)

        # After the loop, build the debug info string if requested
        if self.debug_mode:
            info_lines = []
            info_lines.append(f"AI is '{'X' if self.current_player == BLACK else 'O'}' (Maximizing)")
            info_lines.append(f"Search Depth: {self.search_depth}")
            info_lines.append(f"Alpha-Beta: {'ON' if self.alpha_beta_pruning else 'OFF'}")
            info_lines.append("Scores for top-level moves:")
            # Sort by score for readability
            debug_move_scores.sort(key=lambda x: x[1], reverse=True)
            for move_str, score in debug_move_scores:
                info_lines.append(f"  Move: {move_str} -> Value: {score:.2f}")

            self.debug_info = "\n".join(info_lines)
            self.debug_mode = False # Reset debug mode after one move

        return best_move


    def minimax(self, board_state, player, depth, is_maximizing_player, alpha, beta):
        """
        This is the heart of the AI.
        Implements the Mini-Max algorithm with Alpha-Beta Pruning.
        """
        # [20 pts] Properly implements the Mini-Max algorithm
        # [20 pts] Properly implements alpha-beta pruning

        self.states_examined += 1

        # We need a temporary game object to use our helper functions
        # This is much cleaner than passing the 'player' all the way down
        temp_game = OthelloGame()
        temp_game.board = board_state
        opponent = self.get_opponent(player)

        # Base Case: If we've reached max depth or the game is over
        if depth == 0 or temp_game.is_game_over():
            # The heuristic is always evaluated from the perspective of the
            # *original* player who started the get_ai_move() call.
            # In our setup, that's self.current_player.
            return self.heuristic_evaluate(board_state, self.current_player)

        # Get moves for the 'player' whose turn it is at this node
        valid_moves = temp_game.get_valid_moves(player)

        # If this player has no moves, we must pass the turn
        if not valid_moves:
            # We recurse, but switch the 'is_maximizing_player' flag
            # and pass to the opponent. Depth stays the same (or -1?).
            # This is a "pass" node.
            return self.minimax(
                board_state,
                opponent,
                depth - 1, # Still consume depth
                not is_maximizing_player,
                alpha,
                beta
            )

        if is_maximizing_player:
            best_value = -math.inf
            for move in valid_moves:
                r, c = move

                # Create the new board state by simulating the move
                board_copy = copy.deepcopy(board_state)
                temp_game_move = OthelloGame()
                temp_game_move.board = board_copy
                temp_game_move.make_move(r, c, player)

                # Recursive call for the *opponent* (minimizing player)
                value = self.minimax(
                    temp_game_move.board,
                    opponent,
                    depth - 1,
                    False, # Now it's the minimizer's turn
                    alpha,
                    beta
                )

                best_value = max(best_value, value)
                alpha = max(alpha, best_value)

                # This is the alpha-beta pruning step
                if self.alpha_beta_pruning and beta <= alpha:
                    break  # Beta cut-off

            return best_value

        else: # Minimizing player
            best_value = math.inf
            for move in valid_moves:
                r, c = move

                # Create the new board state by simulating the move
                board_copy = copy.deepcopy(board_state)
                temp_game_move = OthelloGame()
                temp_game_move.board = board_copy
                temp_game_move.make_move(r, c, player)

                # Recursive call for the *opponent* (maximizing player)
                value = self.minimax(
                    temp_game_move.board,
                    opponent,
                    depth - 1,
                    True, # Now it's the maximizer's turn
                    alpha,
                    beta
                )

                best_value = min(best_value, value)
                beta = min(best_value, best_value)

                # This is the alpha-beta pruning step
                if self.alpha_beta_pruning and beta <= alpha:
                    break  # Alpha cut-off

            return best_value

# --- GUI Application Class ---

class OthelloGUI:
    """
    This class manages the entire Tkinter GUI.
    It contains an instance of the OthelloGame logic class.
    This is just like how my main() in the Neural Network
    assignment controlled the NeuralNetwork object.
    """

    def __init__(self, root):
        """
        Constructor for the GUI application.
        'root' is the main Tkinter window.
        """
        self.root = root
        self.root.title("Othello AI (CSC 475)")
        self.root.resizable(False, False)

        self.game = OthelloGame()

        self.cell_size = 60
        board_dim = self.game.board_size * self.cell_size

        # 'player_control' stores who is playing which color.
        # 0 = AI, 1 = Human
        self.player_control = {BLACK: 1, WHITE: 0} # Default: Human (Black) vs AI (White)

        # --- Create GUI Frames ---
        # This helps organize the layout

        # Main frame holds the board
        main_frame = tk.Frame(root, bg='white')
        main_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # Info panel holds scores, turn, and status
        info_panel = tk.Frame(root, bg='lightgray')
        info_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # --- Main Game Board (Canvas) ---
        self.canvas = tk.Canvas(main_frame, width=board_dim, height=board_dim, bg='green')
        self.canvas.pack()
        # Bind the click event to our handler function
        self.canvas.bind("<Button-1>", self.on_board_click)

        # --- Info Panel Widgets ---
        self.score_label = tk.Label(info_panel, text="Score", font=("Arial", 16, "bold"), bg='lightgray')
        self.score_label.pack(pady=(10, 0))

        self.black_score_label = tk.Label(info_panel, text="Black (X): 2", font=("Arial", 14), bg='lightgray')
        self.black_score_label.pack(pady=5)

        self.white_score_label = tk.Label(info_panel, text="White (O): 2", font=("Arial", 14), bg='lightgray')
        self.white_score_label.pack(pady=5)

        self.turn_label = tk.Label(info_panel, text="Turn: Black (X)", font=("Arial", 14, "bold"), bg='lightgray')
        self.turn_label.pack(pady=(20, 10))

        self.status_label = tk.Label(info_panel, text="Game in progress...", font=("Arial", 12, "italic"), bg='lightgray', wraplength=180)
        self.status_label.pack(pady=10, fill=tk.X)

        # --- Control Buttons ---
        button_frame = tk.Frame(info_panel, bg='lightgray')
        button_frame.pack(pady=10, fill=tk.X)

        self.new_game_button = tk.Button(button_frame, text="New Game", command=self.new_game)
        self.new_game_button.pack(fill=tk.X, padx=10, pady=5)

        self.settings_button = tk.Button(button_frame, text="Settings", command=self.open_settings)
        self.settings_button.pack(fill=tk.X, padx=10, pady=5)

        self.ai_move_button = tk.Button(button_frame, text="AI Move for Me", command=self.ai_move_for_human)
        self.ai_move_button.pack(fill=tk.X, padx=10, pady=5)

        # --- Debug Info Area ---
        self.debug_text = tk.Label(info_panel, text="", font=("Courier", 9), bg='lightgray', justify=tk.LEFT, relief="sunken", anchor="nw")
        self.debug_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Initial draw and start the game
        self.update_gui()

    def new_game(self):
        """
        Resets the game to the initial state.
        """
        self.game = OthelloGame()
        # Restore settings from the GUI controls (if they exist)
        # This is a bit complex, so for now just reset to default AI settings
        self.status_label.config(text="New game started.")
        self.debug_text.config(text="")
        self.update_gui()
        self.check_for_ai_move() # Start the game loop

    def update_gui(self):
        """
        Redraws the entire board and updates all labels.
        This is the main refresh function.
        """
        self.draw_board()
        self.update_status_labels()

    def draw_board(self):
        """
        Draws the grid and all the pieces on the canvas.
        """
        self.canvas.delete("all") # Clear the board
        size = self.cell_size

        # Draw grid lines
        for i in range(self.game.board_size + 1):
            self.canvas.create_line(i * size, 0, i * size, self.game.board_size * size, fill='black')
            self.canvas.create_line(0, i * size, self.game.board_size * size, i * size, fill='black')

        # Draw pieces
        for r in range(self.game.board_size):
            for c in range(self.game.board_size):
                piece = self.game.board[r][c]
                if piece != EMPTY:
                    color = "black" if piece == BLACK else "white"
                    # Add a small padding
                    pad = 5
                    self.canvas.create_oval(c * size + pad, r * size + pad,
                                            (c + 1) * size - pad, (r + 1) * size - pad,
                                            fill=color, outline='black')

        # Highlight valid moves for the current human player
        if self.player_control[self.game.current_player] == 1: # If human's turn
            valid_moves = self.game.get_valid_moves(self.game.current_player)
            for r, c in valid_moves:
                pad = size * 0.3
                self.canvas.create_oval(c * size + pad, r * size + pad,
                                        (c + 1) * size - pad, (r + 1) * size - pad,
                                        fill='gray', outline='darkgray', stipple='gray50')

    def update_status_labels(self):
        """
        Updates the score and turn labels.
        """
        black_score, white_score = self.game.get_score()
        self.black_score_label.config(text=f"Black (X): {black_score}")
        self.white_score_label.config(text=f"White (O): {white_score}")

        turn_str = "Black (X)" if self.game.current_player == BLACK else "White (O)"
        self.turn_label.config(text=f"Turn: {turn_str}")

        if self.game.is_game_over():
            self.status_label.config(text=f"Game Over!\n{self.game.get_winner_message()}")
            self.turn_label.config(text="Game Over")

        # Show/hide the "AI Move for Me" button
        if self.player_control[self.game.current_player] == 1: # Human turn
            self.ai_move_button.config(state=tk.NORMAL)
        else: # AI turn
            self.ai_move_button.config(state=tk.DISABLED)

    def on_board_click(self, event):
        """
        This is the main event handler for human moves.
        """
        # Do nothing if it's not a human's turn
        if self.player_control[self.game.current_player] == 0:
            return

        # Calculate which row and col was clicked
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if not self.game.is_on_board(row, col):
            return

        # Try to make the move
        if self.game.make_move(row, col, self.game.current_player):
            self.status_label.config(text="Move successful.")
            self.debug_text.config(text="") # Clear debug on human move
            self.game.switch_player()
            self.update_gui()

            # This is the new event-driven game loop.
            # After a human move, we call this to check for passes or AI moves.
            self.run_game_loop()
        else:
            self.status_label.config(text="Invalid move. Try again.")

    def run_game_loop(self):
        """
        This function replaces the old procedural game loop.
        It checks for game over, handles passes, and triggers AI moves.
        """
        if self.game.is_game_over():
            self.update_gui()
            return

        # Check for valid moves
        valid_moves = self.game.get_valid_moves(self.game.current_player)

        if not valid_moves:
            # No valid moves, so pass the turn
            player_str = "Black (X)" if self.game.current_player == BLACK else "White (O)"
            self.status_label.config(text=f"{player_str} has no moves.\nPassing turn.")
            self.game.switch_player()
            self.update_gui()

            # We need to run the loop again for the *next* player
            # Use root.after to give the GUI time to update
            self.root.after(1000, self.run_game_loop)
            return

        # If we're here, there are valid moves. Check if it's an AI's turn.
        if self.player_control[self.game.current_player] == 0:
            # It's an AI's turn.
            self.trigger_ai_move()

    def check_for_ai_move(self):
        """
        A helper to start the game loop, checking if the first move is by an AI.
        """
        self.run_game_loop()

    def trigger_ai_move(self):
        """
        Schedules the AI to make a move after a short delay.
        This prevents the GUI from freezing while the AI is "thinking".
        """
        player_str = "Black (X)" if self.game.current_player == BLACK else "White (O)"
        self.status_label.config(text=f"AI ({player_str}) is thinking...")

        # The 'after' method runs 'run_ai_move' after 50ms,
        # giving the GUI time to update the "thinking..." message.
        self.root.after(50, self.run_ai_move)

    def run_ai_move(self):
        """
        This is where the AI logic is actually called.
        """
        move = self.game.get_ai_move()

        if self.game.debug_info:
            self.debug_text.config(text=self.game.debug_info)
        else:
            self.debug_text.config(text=f"AI examined {self.game.states_examined} states.")

        if move:
            self.game.make_move(move[0], move[1], self.game.current_player)
            move_str = f"{chr(ord('a') + move[1])}{move[0]+1}"
            player_str = "Black (X)" if self.game.current_player == BLACK else "White (O)"
            self.status_label.config(text=f"AI ({player_str}) played {move_str}.")
        else:
            # This should not happen if get_valid_moves check passed, but good to have
            self.status_label.config(text="AI has no moves.")

        self.game.switch_player()
        self.update_gui()

        # Continue the game loop
        self.root.after(100, self.run_game_loop)

    def ai_move_for_human(self):
        """
        Handler for the "AI Move for Me" button.
        """
        if self.player_control[self.game.current_player] == 0:
            return # Should be disabled, but a good check

        self.status_label.config(text="AI is thinking for you...")
        # We can just re-use the AI logic.
        # This is a bit of a cheat, as we're temporarily
        # setting the *game's* debug flag, but it works.
        self.game.debug_mode = True # Always show debug for this
        self.root.after(50, self.run_ai_move_for_human)

    def run_ai_move_for_human(self):
        """
        The actual logic for the "AI Move for Me" button.
        This is separate so the GUI can update.
        """
        move = self.game.get_ai_move()

        if self.game.debug_info:
            self.debug_text.config(text=self.game.debug_info)
        else:
            self.debug_text.config(text=f"AI examined {self.game.states_examined} states.")

        if move:
            self.game.make_move(move[0], move[1], self.game.current_player)
            move_str = f"{chr(ord('a') + move[1])}{move[0]+1}"
            self.status_label.config(text=f"AI suggests {move_str} for you.")
        else:
            self.status_label.config(text="AI finds no moves for you.")

        self.game.switch_player()
        self.update_gui()

        # Continue the game loop
        self.root.after(100, self.run_game_loop)


    def open_settings(self):
        """
        Creates the pop-up settings window.
        This is just like the old CLI settings menu.
        """
        self.settings_window = Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.grab_set() # Modal window

        # --- Game Mode ---
        mode_frame = tk.Frame(self.settings_window, relief="groove", borderwidth=2)
        mode_frame.pack(padx=10, pady=10, fill="x")
        tk.Label(mode_frame, text="Player Settings", font=("Arial", 12, "bold")).pack()

        self.p1_var = IntVar(value=self.player_control[BLACK])
        self.p2_var = IntVar(value=self.player_control[WHITE])

        tk.Checkbutton(mode_frame, text="Black (X) is Human", variable=self.p1_var, onvalue=1, offvalue=0).pack(anchor="w")
        tk.Checkbutton(mode_frame, text="White (O) is Human", variable=self.p2_var, onvalue=1, offvalue=0).pack(anchor="w")

        # --- AI Settings ---
        ai_frame = tk.Frame(self.settings_window, relief="groove", borderwidth=2)
        ai_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(ai_frame, text="AI Settings", font=("Arial", 12, "bold")).pack()

        # AI Search Depth
        tk.Label(ai_frame, text="AI Search Depth").pack()
        self.depth_var = IntVar(value=self.game.search_depth)
        Scale(ai_frame, from_=1, to=8, orient=tk.HORIZONTAL, variable=self.depth_var).pack(fill="x")

        # Alpha-Beta Pruning
        self.pruning_var = BooleanVar(value=self.game.alpha_beta_pruning)
        Checkbutton(ai_frame, text="Use Alpha-Beta Pruning", variable=self.pruning_var).pack(anchor="w")

        # Debug Mode
        self.debug_var = BooleanVar(value=self.game.debug_mode)
        Checkbutton(ai_frame, text="Debug Mode (for next AI move)", variable=self.debug_var).pack(anchor="w")

        # --- Apply Button ---
        apply_button = tk.Button(self.settings_window, text="Apply and Close", command=self.apply_settings)
        apply_button.pack(padx=10, pady=10)

    def apply_settings(self):
        """
        Called when the settings window is closed.
        It saves the settings to the game object.
        """
        self.player_control[BLACK] = self.p1_var.get()
        self.player_control[WHITE] = self.p2_var.get()

        self.game.search_depth = self.depth_var.get()
        self.game.alpha_beta_pruning = self.pruning_var.get()
        self.game.debug_mode = self.debug_var.get()

        self.settings_window.destroy()

        self.status_label.config(text="Settings updated.")

        # If we applied settings, check if an AI move is needed now
        self.check_for_ai_move()


if __name__ == "__main__":
    """
    Standard Python entry point for a Tkinter application.
    """
    root = tk.Tk()
    app = OthelloGUI(root)

    # This is a small hack to make sure the AI
    # moves first if it's set to AI vs AI or AI (Black)
    root.after(100, app.check_for_ai_move)

    root.mainloop()