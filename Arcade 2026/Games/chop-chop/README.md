# Chop Chop

Chop the tree from the left or right and avoid branches on your side. Each round lasts 30 seconds, and your score is the total number of chops.

## Keys

| Key | Action |
|---|---|
| P (or left arrow) | Chop left |
| Q (or right arrow) | Chop right |

Clicking or tapping each half of the screen also works.

## Controller

Two piezo disc tap pads on an Arduino Uno. It connects by USB cable at 9600 baud. The IEEE Arcade reads it by itself. Outside the arcade it needs `serial_keyboard.py` (in Pre-Event Files). Sketch is in [controller/](controller/) and is the same one Two-Lane Tiles uses.

## Running it

Open `index.html` in Chrome or Edge.
