# Brainrot Mania

A two-player fighting game. Each player picks one of six fighters, and the first to win 2 rounds takes the match. Rounds last 60 seconds.

## Keys

| Player 1 | Player 2 | Action |
|---|---|---|
| A and D | Left and Right arrows | Move, and pick a fighter |
| W | Up arrow | Jump |
| F | K | Punch, and lock in your fighter |
| G | L | Kick |
| H | ; | Special |
| Hold away from your rival | Hold away from your rival | Block |

Esc quits.

## Controller

One Arduino Uno with two button pads (pins 2 to 5 for Player 1, 8 to 11 for Player 2). Blue moves left, black moves right, yellow jumps, and red punches. It connects by USB cable and sends lines like `W1` (pressed) and `W0` (released) at 9600 baud. The game reads it by itself, so `serial_keyboard.py` isn't needed. The pads have no kick or special buttons, so those are keyboard only. Sketch is in [controller/](controller/).

## Running it

Best played through the IEEE Arcade (`Start Arcade.bat` in the Arcade 2026 folder). To run it on its own, use Python 3.12 with `pygame` and `pyserial` and run `python game.py`. Plug the controller in first.
