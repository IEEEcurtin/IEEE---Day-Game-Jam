# Two-Lane Tiles

Tiles fall in two lanes. Hit the lane with the next tile. A wrong lane or a missed tile ends the run, and it speeds up as your score climbs. Has a light and dark theme.

## Keys

| Key | Action |
|---|---|
| Left arrow | Left lane |
| Right arrow | Right lane |

Clicking or tapping each half of the screen also works.

## Controller

Two piezo disc tap pads on an Arduino Uno (A0 and A1, each with a 1 megaohm resistor). It connects by USB cable at 9600 baud. The IEEE Arcade reads it by itself. Outside the arcade it needs `serial_keyboard.py` (in Pre-Event Files). It sends `LEFT1`/`LEFT0` and `RIGHT1`/`RIGHT0`. THRESHOLD is set to 800. Sketch is in [controller/](controller/) and is the same one Chop Chop uses.

## Running it

Open `index.html` in Chrome or Edge.
