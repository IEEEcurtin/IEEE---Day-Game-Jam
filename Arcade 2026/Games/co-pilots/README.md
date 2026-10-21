# Co-Pilots

A two-player co-op flying game. One player steers, the other handles up and down, and you share a boost. The best team score is saved with a team name.

## Keys

| Key | Action |
|---|---|
| Left and Right arrows | Player 1 steers |
| W and S | Player 2 up and down |
| Space | Boost |
| F11 | Fullscreen |
| Esc | Quit |

## Controller

Connects by USB cable and sends lines of `tilt,up,down,boost` at 115200 baud (tilt from -1 to 1, the rest 0 or 1). Keyboard keeps working alongside it. The controller sketch is still to be added.

## Running it

Best played through the IEEE Arcade (`Start Arcade.bat` in the Arcade 2026 folder), which finds the controller by itself. To run it on its own, use Python with `pygame` and `pyserial` and run `python game.py` for keyboard only, `python game.py auto` to find the controller, or `python game.py COM3` with the controller's port.
