# Dead Tape Gun

A two-player tape gun duel, or one player against the computer ("the Stranger") with `?solo=1` on the address, which the IEEE Arcade sets for you. Aim at your opponent, aim at yourself, feint, or spin, then pull the trigger. Player stats are saved in the browser.

## Keys

| Key | Action |
|---|---|
| W or Up | Aim at opponent |
| S or Down | Aim at self |
| X, Left, or Right | Lower the gun |
| Space or Enter (hold) | Trigger |
| F | Feint |
| R | Spin |
| M | Mute |

## Controller

ESP32 with an MPU6050 tilt sensor and a trigger switch on pin 18. It works as a Bluetooth keyboard called "DeadTape Gun", so pair it once in Windows Bluetooth settings. Needs ESP32 board package version 2.0.17. Sketch is in [controller/](controller/).

## Running it

Open `index.html` in Chrome or Edge.
