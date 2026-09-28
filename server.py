#!/usr/bin/env python3
"""
Text-based multiplayer labyrinth -- SERVER.
Run this on one machine, then connect with client.py from any machine
on the same LAN.

Controls in game:  W A S D  (Q quits the client)
"""

import json
import random
import socket
import threading

HOST = "0.0.0.0"
PORT = 5555

W, H = 31, 15                       # maze size -- keep both ODD
SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
DIRS = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}

lock = threading.Lock()
players = {}                        # pid -> {"x","y","sym","sock","addr"}
next_id = 0
winner = None                       # (pid, sym) once somebody escapes
maze = []


# ----------------------------------------------------------------- maze
def generate_maze(w, h):
    """Recursive-backtracker maze. 1 = wall, 0 = floor."""
    grid = [[1] * w for _ in range(h)]
    grid[1][1] = 0
    stack = [(1, 1)]
    while stack:
        x, y = stack[-1]
        opts = []
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            nx, ny = x + dx, y + dy
            if 0 < nx < w - 1 and 0 < ny < h - 1 and grid[ny][nx] == 1:
                opts.append((nx, ny, dx, dy))
        if opts:
            nx, ny, dx, dy = random.choice(opts)
            grid[y + dy // 2][x + dx // 2] = 0   # knock down the wall between
            grid[ny][nx] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    return grid


def pick_spawn():
    cells = [(x, y) for y in range(H) for x in range(W) if maze[y][x] == 0]
    random.shuffle(cells)
    taken = {(p["x"], p["y"]) for p in players.values()}
    goal = (W - 2, H - 2)
    for c in cells:
        if c not in taken and c != goal:
            return c
    return None


# ----------------------------------------------------------------- net
def send(conn, obj):
    try:
        conn.sendall((json.dumps(obj) + "\n").encode())
    except OSError:
        pass


def broadcast():
    with lock:
        state = {
            "type": "state",
            "players": {str(pid): [p["x"], p["y"], p["sym"]]
                        for pid, p in players.items()},
            "winner": winner,
        }
        targets = [p["sock"] for p in players.values()]
    msg = (json.dumps(state) + "\n").encode()
    for s in targets:
        try:
            s.sendall(msg)
        except OSError:
            pass


def do_move(pid, cmd):
    global winner
    if cmd not in DIRS:
        return
    with lock:
        if pid not in players or winner is not None:
            return
        p = players[pid]
        dx, dy = DIRS[cmd]
        nx, ny = p["x"] + dx, p["y"] + dy
        if not (0 <= nx < W and 0 <= ny < H) or maze[ny][nx] == 1:
            return
        p["x"], p["y"] = nx, ny
        if (nx, ny) == (W - 2, H - 2):
            winner = (pid, p["sym"])
    broadcast()


# ----------------------------------------------------------------- client thread
def handle_client(conn, addr):
    global next_id
    pid = None
    sym = "?"
    try:
        with lock:
            spawn = pick_spawn()
            if spawn is None:
                send(conn, {"type": "error", "msg": "No free spawn point."})
                return
            pid = next_id
            next_id += 1
            sym = SYMBOLS[pid % len(SYMBOLS)]
            players[pid] = {"x": spawn[0], "y": spawn[1], "sym": sym,
                            "sock": conn, "addr": addr}
            init = {
                "type": "init",
                "id": pid,
                "sym": sym,
                "width": W,
                "height": H,
                "maze": ["".join("#" if c else "." for c in row) for row in maze],
                "exit": [W - 2, H - 2],
                "winner": winner,
            }
        send(conn, init)
        print(f"[+] {addr[0]}:{addr[1]} joined as '{sym}'")
        broadcast()

        buf = b""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                cmd = line.decode(errors="ignore").strip().lower()
                if cmd:
                    do_move(pid, cmd)
    except OSError:
        pass
    finally:
        with lock:
            if pid in players:
                sym = players[pid]["sym"]
                del players[pid]
        print(f"[-] {addr[0]}:{addr[1]} left ('{sym}')")
        broadcast()
        try:
            conn.close()
        except OSError:
            pass


# ----------------------------------------------------------------- main
def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    global maze
    maze = generate_maze(W, H)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(8)

    print("=" * 52)
    print("  LABYRINTH SERVER")
    print(f"  Address : {local_ip()}:{PORT}")
    print(f"  Maze    : {W} x {H}   exit at ({W - 2}, {H - 2})")
    print("  Connect : python client.py " + local_ip())
    print("  Ctrl+C to stop.")
    print("=" * 52)

    try:
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client,
                             args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        srv.close()


if __name__ == "__main__":
    main()