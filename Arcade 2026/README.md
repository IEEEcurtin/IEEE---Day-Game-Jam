# 🕹️ IEEE Arcade 2026

The games made at the IEEE Day Game Jam (8 October 2026), playable from one full-screen arcade menu. First shown at Pinktober 2026.

Every game has a short how-to-play screen, a leaderboard saved on the laptop, and arcade-style name entry. Every game works on the keyboard alone, so a broken controller never stops play.

## Setting up a laptop (Windows)
1. Download the repository (green **Code** button on the main page, then **Download ZIP**). Right-click the ZIP and choose **Extract All**, or clone it with git.
2. Open the **Arcade 2026** folder and double-click **`Start Arcade.bat`**.
3. The first time, it downloads its own copy of Python (about 60 MB), so the laptop needs internet once. Nothing gets installed system-wide. After that the arcade runs completely offline.

The arcade opens full screen in Chrome, or in Edge if Chrome isn't installed.

To update a laptop later, download a fresh ZIP the same way. Leaderboards are kept separately on each laptop, so updating never wipes them.

## Running it on the day
Each laptop runs as a station for one game. Pick the game once, and after every player the arcade returns to that game's how-to-play screen, ready for the next person. It also remembers the game if the arcade is restarted.

* **Choose a game** with the arrow keys, then press Enter.
* **Choose 1 or 2 players** with the left and right arrows on the how-to-play screen, for games that have both.
* **Leave a game early** by holding Esc for 2 seconds. This is for helpers, so players can't quit by accident.
* **Switch to a different game** by pressing Esc on the how-to-play screen. That opens the full menu.
* **Test a controller** by pressing F2 on the menu or the how-to-play screen. Every key the controller sends shows up on screen.
* **Close the arcade** with Alt+F4.
* A game left alone for 60 seconds goes back to its how-to-play screen by itself.

Bluetooth controllers need pairing once per laptop in Windows Bluetooth settings. USB controllers just plug in, since the arcade finds them by itself. If anything goes wrong, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## What's in this folder

| Folder | What it holds |
|---|---|
| [`Games/`](Games/) | One folder per game, each with the game, its controller code, and a README |
| [`system/`](system/) | The arcade itself (menu, local server, one-time setup) |

Each game also runs on its own. Open its `index.html` in Chrome or Edge, or see the game's README for the two Python games.
