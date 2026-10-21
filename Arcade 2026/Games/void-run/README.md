# Void Run

A 3D space flyer. Your ship flies forward on its own. Steer around rocks and hold fire to shoot drones. Your hull bar drops when you hit things. The menu has toggles to invert up/down and left/right.

## Keys

| Key | Action |
|---|---|
| WASD or arrows | Steer |
| Space (hold) | Fire, also starts and restarts |

## Controller

A tilt stick made from an Arduino Uno, an MPU6050 tilt sensor, and a button on pin 2. It connects by USB cable at 9600 baud. The IEEE Arcade reads it by itself. Outside the arcade it needs `serial_keyboard.py` (in Pre-Event Files) to turn its messages into key presses. The directions are deliberately flipped (forward sends S, left sends D), which is what the invert toggles are for. Sketch is in [controller/](controller/).

## Running it

Open `index.html` in Chrome or Edge. Everything it needs, including three.js and the font, is in `assets/`, so it runs offline.
