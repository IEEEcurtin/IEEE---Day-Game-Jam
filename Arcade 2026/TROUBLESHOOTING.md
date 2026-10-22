# Arcade troubleshooting

Every game can be played on the keyboard. If a controller misbehaves, keep playing on the keyboard and sort the controller out between players.

## Starting the arcade

| What happens | What to do |
|---|---|
| "Setup could not finish" | The first start needs internet to download Python. Connect to Wi-Fi and run `Start Arcade.bat` again. |
| A blue Windows box says "Windows protected your PC" | Click **More info**, then **Run anyway**. It appears because the file came from the internet. |
| Nothing opens, or the window flashes and closes | Run `Start Arcade.bat` again. If it still fails, open the arcade log (see the end of this page) and look at the last lines. |
| `Start Arcade.bat` was opened from inside the ZIP | Right-click the ZIP, choose **Extract All**, then run `Start Arcade.bat` from the extracted folder. |
| The arcade opens in a normal browser window | Neither Chrome nor Edge was found. It still works. Press F11 for full screen. |
| You need the arcade in a window, for example to test | Run `system/Start Arcade (windowed).bat`. |

## During play

| What happens | What to do |
|---|---|
| A player is stuck in a game | Hold **Esc** for 2 seconds. A bar fills up, then it goes back to the game's how-to-play screen. |
| The laptop needs to run a different game | On the how-to-play screen press **Esc** to open the full menu, then pick the game. |
| Keys do nothing in a game | Click once on the game with the mouse so it has focus, then try again. |
| Bomb Defusal, Co-Pilots, or Brainrot Mania opened but can't be seen | Press **Alt+Tab** and pick the game window. |
| Bomb Defusal, Co-Pilots, or Brainrot Mania won't close | Hold **Esc** for 2 seconds in the game. If that fails, hold Esc on the arcade's "running in its own window" screen. |
| A Chrome page (Help, settings, a new tab) is covering the arcade | Press **Ctrl+W** to close it. The arcade is still running underneath. Don't use Alt+F4, which can close the arcade itself. |
| The arcade froze | Press **Alt+F4**, then run `Start Arcade.bat` again. Leaderboards are saved after every game, so nothing is lost. |
| Sound is missing | Check the laptop volume, and that the laptop isn't on mute. |

## Controllers

| What happens | What to do |
|---|---|
| Not sure if a controller is working | On the menu or a how-to-play screen, press **F2**. Every key the controller sends appears on screen. Press F2 again to go back. |
| A Bluetooth controller (Dead Tape Gun, Flappy Tungs pedals) does nothing | Open Windows Bluetooth settings and check it is paired and connected. If it was paired to another laptop, remove it there first, then pair it here. |
| A USB controller (tilt stick, tap pads) does nothing | Unplug it and plug it back in, then wait 3 seconds. The bottom of the menu shows "USB COM..." when the arcade can see it. Close the Arduino Serial Monitor if it is open. |
| The Bomb Defusal panel, Co-Pilots controller, or Brainrot Mania buttons do nothing | Plug it in **before** starting the game, since the game looks for it as it opens. |
| Flappy Tungs USB pedals do nothing | Those pedals connect inside the game. The first time on a laptop, click **Connect pedals (USB)** at the bottom with the mouse and pick the pedals. After that they reconnect by themselves. |
| Void Run steering feels backwards with the tilt stick | On the Void Run start screen, tick the two **Invert** boxes with the mouse. The laptop remembers this. Untick them for keyboard players. |
| A controller presses keys by itself | Unplug it. Play on the keyboard until it can be checked. |

## Where the arcade keeps its files

Everything the arcade saves on a laptop is in one folder. To open it, click the File Explorer address bar, type `%LOCALAPPDATA%\IEEEArcade` and press Enter.

| Folder or file | What it is |
|---|---|
| `scores` | The leaderboards, one file per game |
| `arcade.log` | Every game started, every score, and every error, with times |
| `python` | The arcade's private copy of Python |
| `browser-profile` | The arcade's own browser settings |

These stay put when you download a newer copy of the repo, so updating never wipes the leaderboards.

## Leaderboards

* Each laptop keeps its own leaderboards.
* To clear a leaderboard, close the arcade and delete that game's file from `scores`. Delete the whole `scores` folder to clear everything.
* To copy leaderboards to another laptop, copy the `scores` folder across while both arcades are closed.
* If the arcade ever breaks after an update, delete the `python` folder and run `Start Arcade.bat` with internet. It downloads a fresh copy.

## After the event

Send `arcade.log` along with any bug report.
