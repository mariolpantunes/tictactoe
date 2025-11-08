# Tic-Tac-Toe

A classic Tic-Tac-Toe game implemented in Python using **Pygame**.

This project's main purpose is to demonstrate modern network programming by implementing a real-time, 2-player remote mode using `asyncio` streams. All game modes are accessible via an in-game GUI, with no command-line arguments required.

This game implements several modes:

1.  **Local Play vs. Human:** Classic 1v1 on the same screen.
2.  **Local Play vs. AI:** Challenge a simple bot powered by a MinMax agent.
3.  **Networked Play (Asyncio):** Host or join a remote game to play against a friend over TCP.

-----

## Setup and Dependencies

This project is built with Python 3 and Pygame. All Python dependencies should be installed in a virtual environment.

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install dependencies:**
    ```bash
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

-----

## How to Play

Simply run the main script to start the game. The main menu will appear, allowing you to choose your mode.

```bash
python main.py
```

### 1. Local Mode

1.  Click **Local Play**.
2.  Choose **1 Player** (to play against the AI) or **2 Players** (for a hot-seat game).

### 2. Host a Network Game (Player X)

1.  Click **Host Game**.
2.  Enter a port to listen on (e.g., `8888`) and press **Enter**.
3.  The game will show a "Waiting..." screen.
4.  Tell the other player your IP address and the port you chose.

### 3. Join a Network Game (Player O)

1.  Click **Join Game**.
2.  Enter the host's IP address (e.g., `192.168.1.10`) and press **Enter**.
3.  Enter the host's port (e.g., `8888`) and press **Enter**.
4.  The game will connect, and the match will begin.

-----

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Copyright

See the `COPYRIGHT` file for details.