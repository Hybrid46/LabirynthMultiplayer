# Labyrinth Multiplayer 🏰

![Labyrinth Multiplayer screenshot](LabirynthMultiplayer.png)

A tiny, dependency-free **LAN multiplayer maze game** written in pure Python.
One machine runs the server, everyone else connects with the client — race
through a randomly generated labyrinth and be the first to reach the exit.

![Labyrinth Multiplayer screenshot](LabirynthMultiplayer.png)

---

## ✨ Features

- 🎲 **Randomly generated maze** every time the server starts (recursive backtracker)
- 👥 **LAN multiplayer** — no internet, no accounts, no matchmaking
- ⚡ **Zero dependencies** — just the Python standard library
- 🎨 **Colored terminal rendering** with a unique symbol & color per player
- 🏆 **First to the exit wins** — the server locks further moves and announces the winner
- 🧵 **Thread-safe** — one thread per client, one global lock, full-state broadcast after each move

---

## 📦 Requirements

- Python **3.8+** (nothing else — no `pip install` needed)
- All players on the **same local network** (Wi-Fi or Ethernet)
- A terminal that supports ANSI colors
  - ✅ Windows Terminal, PowerShell 7+, macOS Terminal, Linux terminals
  - ⚠️ Old `cmd.exe` may render colors oddly — use Windows Terminal instead

---

## 🚀 Quick Start

### 1. Start the server (one machine only)

```bash
python server.py
```

You'll see something like:

====================================================
  LABYRINTH SERVER
  Address : 192.168.1.10:5555
  Maze    : 31 x 15   exit at (29, 13)
  Connect : python client.py 192.168.1.10
  Ctrl+C to stop.
====================================================

💡 On the first run, Windows/macOS may ask to allow incoming connections.
Say yes, or other machines can't reach port 5555.

2. Connect from each player's machine

```bash
python client.py 192.168.1.10
```

Use the IP that your server printed — not the one in this example.

That's it. The maze appears and you're playing.

🎮 Controls
Key	Action
W	Move up
A	Move left
S	Move down
D	Move right
Q	Quit

You're shown as a bold colored letter. Other players show up in their own colors.

🧪 Try It Solo First

You can test the whole thing on a single machine before inviting friends:

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py 127.0.0.1

# Terminal 3 (optional) — a second fake player
python client.py 127.0.0.1
```

🖼️ How It Looks

```bash
╔══════════════════════════════════════════╗
║  You are 'B'   Players online: 3         ║
║                                          ║
║  #############################           ║
║  #A....#.......#.............#           ║
║  #.###.#.#####.#.###########.#           ║
║  #.#...#.....#.#.#.........#.#           ║
║  #.#.#######.#.#.#.#######.#.#           ║
║  #...#.......#...#.#.....#...#           ║
║  #.#.#.#########.#.#.###.#.#.#           ║
║  #.#.#...........#.#.#...#.#.#           ║
║  #.#.###############.#.###.#.#           ║
║  #B..#...........#...#...#...#           ║
║  #.#####.#######.#.###.#.###.#           ║
║  #.....#.....#...#...#.#...#.#           ║
║  #.###.#.###.#.###.#.#.#.#.#.#           ║
║  #...#...#...#...#...#...#..E#           ║
║  #############################           ║
║                                          ║
║  Move: W A S D     Quit: Q               ║
╚══════════════════════════════════════════╝

   # = wall        . = floor        E = exit
   A, B, C… = players (your own letter is bold)
   ```

   📁 Files
File	Purpose
server.py	Generates the maze, listens on port 5555, tracks players, enforces the win condition
client.py	Connects to the server, renders the maze, sends your keypresses

⚙️ Configuration

A few constants at the top of server.py are worth tweaking:
Constant	Default	Notes
PORT	5555	Change if it clashes with something else on your LAN
W, H	31, 15	Maze size. Keep both odd or the generator may misbehave
SYMBOLS	A–Z 0–9	Player symbols, assigned in join order

If you change PORT, update the matching value in client.py too.
🛠️ How It Works (Short Version)

    The server generates a maze using a recursive backtracker.

    Each connecting client gets a thread, a spawn cell, and a symbol (A, B, …).

    Every keypress is sent as a single character over TCP.

    The server validates the move (in bounds? not a wall? game not over?), updates
    the player's position, and broadcasts the full game state to everyone.

    Reaching cell (W-2, H-2) sets the winner, and further moves are ignored.

Simple, synchronous, and fast enough for a LAN game with a handful of players.
❓ Troubleshooting

Could not connect to <ip>:5555

    Double-check you're using the IP the server printed.

    Make sure both machines are on the same Wi-Fi/Ethernet network.

    Allow Python through your firewall (both on the server machine).

Colors look wrong / garbled

    Use Windows Terminal, PowerShell 7+, or any modern terminal.

python not found

    Try python3 instead (common on macOS/Linux).

Client hangs on "Waiting for maze..."

    The server isn't reachable. Same firewall/IP checks as above.

📜 License

MIT — do whatever you want with it.
🙌 Contributing

This is a tiny hobby project. If you want to add features (spectator mode,
timed rounds, chat, a scoring system), feel free to open a PR or fork it.