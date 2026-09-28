#!/usr/bin/env python3
"""
Text-based multiplayer labyrinth -- CLIENT.

Run on each player's machine:
    python client.py <server-ip>
e.g.
    python client.py 192.168.1.10

Controls:  W A S D  to move,  Q  to quit.
"""

import json
import os
import socket
import sys
import threading

PORT = 5555

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

PLAYER_COLORS = [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE]

running = True
state = {"maze": [], "players": {}, "exit": [0, 0], "winner": None}
my_id = None
my_sym = "?"


def clear_screen():
    # Clear screen + move cursor to top-left
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def color_for(sym):
    # Map symbol letter -> stable color by its index in the alphabet
    idx = (ord(sym) - ord("A")) % len(PLAYER_COLORS) if sym.isalpha() else 0
    return PLAYER_COLORS[idx]


def render():
    clear_screen()
    maze = state["maze"]
    players = state["players"]
    exit_pos = tuple(state["exit"])
    winner = state["winner"]

    # Build a lookup of (x,y) -> symbol so we can overlay players onto the maze
    overlay = {}
    for pid, (x, y, sym) in players.items():
        overlay[(x, y)] = (sym, pid)

    print(f"{BOLD}=== LABYRINTH ==={RESET}   "
          f"You are {BOLD}{color_for(my_sym)}{my_sym}{RESET}   "
          f"Players online: {len(players)}")
    print()

    for y, row in enumerate(maze):
        line = []
        for x, ch in enumerate(row):
            if (x, y) in overlay:
                sym, pid = overlay[(x, y)]
                col = color_for(sym)
                if pid == str(my_id):
                    line.append(f"{BOLD}{col}{sym}{RESET}")   # you: bold
                else:
                    line.append(f"{col}{sym}{RESET}")
            elif (x, y) == exit_pos:
                line.append(f"{BOLD}{GREEN}E{RESET}")
            elif ch == "#":
                line.append(f"{DIM}#{RESET}")
            else:
                line.append(".")
        print("".join(line))

    print()
    if winner is not None:
        win_pid, win_sym = winner
        who = "YOU" if win_pid == my_id else f"Player {win_sym}"
        print(f"{BOLD}{GREEN}🏆  {who} reached the exit!  🏆{RESET}")
    else:
        print(f"{BOLD}Move:{RESET} W A S D     {BOLD}Quit:{RESET} Q")
        print(f"{DIM}Legend: # wall   . floor   E exit{RESET}")


def recv_loop(sock):
    global running, state, my_id, my_sym
    buf = b""
    try:
        while running:
            data = sock.recv(4096)
            if not data:
                print("\nDisconnected from server.")
                running = False
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line.decode())
                except json.JSONDecodeError:
                    continue

                t = msg.get("type")
                if t == "init":
                    my_id = msg["id"]
                    my_sym = msg["sym"]
                    state["maze"] = msg["maze"]
                    state["exit"] = msg["exit"]
                    state["winner"] = msg.get("winner")
                    render()
                elif t == "state":
                    state["players"] = msg["players"]
                    state["winner"] = msg["winner"]
                    render()
                elif t == "error":
                    print("Server error:", msg.get("msg"))
                    running = False
    except OSError:
        pass
    finally:
        running = False


def input_loop(sock):
    global running
    try:
        while running:
            key = sys.stdin.readline()
            if not key:
                break
            k = key.strip().lower()
            if k == "q":
                running = False
                break
            if k in ("w", "a", "s", "d"):
                try:
                    sock.sendall((k + "\n").encode())
                except OSError:
                    running = False
                    break
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        running = False


def main():
    global running
    if len(sys.argv) < 2:
        print("Usage: python client.py <server-ip>")
        print("Example: python client.py 192.168.1.10")
        sys.exit(1)

    host = sys.argv[1]
    try:
        sock = socket.create_connection((host, PORT), timeout=10)
    except OSError as e:
        print(f"Could not connect to {host}:{PORT}  ({e})")
        sys.exit(1)
    sock.settimeout(None)

    print(f"Connected to {host}:{PORT}.  Waiting for maze...")

    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    try:
        input_loop(sock)
    finally:
        running = False
        try:
            sock.close()
        except OSError:
            pass
        clear_screen()
        print("Thanks for playing!")


if __name__ == "__main__":
    main()