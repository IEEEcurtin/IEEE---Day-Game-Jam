# Don't Press That! (Bomb Defusal)

A fake bomb panel. The screen tells you what to press, like PRESS RED, PRESS KEYPAD 7, or a sequence such as RED, then BLUE, then GREEN. Some lines are tricks, and some tell you to press nothing at all.

## How to play

- You have 3 lives and 2 levels (35 seconds, then 25 seconds).
- A wrong press or running out of time costs a life.
- Finish level 2 to win.
- The menu is clicked with the mouse.

## Keys

| Key | Action |
|---|---|
| R, B, G | Red, blue, and green buttons |
| 0 to 9 | Keypad numbers |
| A, V, C, D | Keypad A, B, C, D (V stands in for B because B is blue) |
| S | Keypad * |
| H | Keypad # |
| Enter | Play again |
| Esc | Quit |

## Controller

ESP32 with a 4x4 keypad and three colour buttons on pins 27, 26, and 25. It connects by USB cable and sends `KEY_x`, `RED`, `BLUE`, and `GREEN` at 115200 baud. The game finds it on any USB port by itself, so plug it in before starting. Sketch is in [controller/](controller/).

## Running it

Best played through the IEEE Arcade (`Start Arcade.bat` in the Arcade 2026 folder). To run it on its own, use Python with `pygame` and `pyserial` and run `python game.py`.
