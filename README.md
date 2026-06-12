# Intelligent Othello Player

An intelligent Python implementation of the classic two-player board game Othello (Reversi). This project features a fully playable Tkinter graphical user interface (GUI) and an AI opponent powered by the Mini-Max heuristic search algorithm with alpha-beta pruning.

# Overview
This application allows users to play Othello in three distinct modes: Human vs. AI, Human vs. Human, and AI vs. AI. The game engine enforces all standard Othello rules, computes valid moves and disk flips, and detects end-game conditions. The core of the project is an adversarial AI agent capable of evaluating board states and making strategic decisions in real-time.

# Key Features
Mini-Max Search Algorithm: The AI determines optimal moves by recursively evaluating the game tree to a specified search depth to maximize its score while minimizing the opponent's potential.

Alpha-Beta Pruning: Optimizes the Mini-Max algorithm by eliminating branches that cannot possibly influence the final decision. Alpha-Beta pruning significantly improves search efficiency in game trees by reducing the number of nodes evaluated, which allows the algorithm to search deeper within the same timeframe (Schaeffer & Plaat, 1996).

Custom Heuristic Evaluation: The AI utilizes a multi-factor evaluation function to score board states. It combines a positional weight matrix (heavily favoring corners), mobility tracking (the number of valid moves available), and coin parity (the raw piece count).

Adjustable Difficulty: Users can dynamically adjust the AI's search depth (from 1 to 8) to scale the difficulty and computation time.

Interactive Debug Mode: A toggleable debug interface reveals the AI's underlying thought process, displaying the sequence of evaluated top-level moves, the heuristic value of each sequence, and the total number of game states examined per move.

Tkinter GUI: A clean, event-driven graphical interface that handles board rendering, move highlighting, scorekeeping, and dynamic settings configuration.

# Installation and Execution
Ensure you have Python 3.x installed on your system.

Clone this repository to your local machine.

Execute the main script to launch the application:

python othello_gui.py
