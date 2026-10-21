# Flappy Tungs

A two-player race. Stomp a foot pedal to flap, angel against devil, through the same obstacles. First to win 3 rounds wins the match.

There is also a solo mode where the computer flies the devil. Add `?solo=1` to the address, or pick 1 PLAYER in the IEEE Arcade.

## How to play

- Each player types their name. Player 1 is the angel on the left, and Player 2 is the devil on the right.
- Click Start game. Each player stomps once to ready up, then a 3-2-1 countdown starts.
- Each stomp makes your character jump. Gravity pulls you down between stomps, so keep a steady rhythm.
- Avoid the spikes, the ceiling, and the ground. Touching anything ends your run and freezes your lane.
- The round ends when both players are out. Whoever passed more spike gaps wins the round. In a tie, whoever lasted longer wins.
- After the match, Pedal 1 plays again with the same names and Pedal 2 changes the names.
- The Leaderboard button shows the best distances ever flown.

## Keys

| Key | Action |
|---|---|
| A | Player 1 flap |
| L | Player 2 flap |

## Controller

Two piezo disc foot pedals on an ESP32. It can work two ways.

- **Bluetooth keyboard.** The sketch in [controller/](controller/) makes the ESP32 a keyboard called "Stomp Pedals" that sends A and L. Pair it once in Windows Bluetooth settings.
- **USB cable.** Close the Arduino Serial Monitor, open the game in Chrome or Edge, click Connect pedals (USB), and choose the ESP32's port. The game expects `P1 stomp` / `P2 stomp` or `Piezo 1 Knock` / `Piezo 2 Knock` at 115200 baud. No sketch for this mode was submitted.

## Tips

- Stomp quickly and lightly. Lift your foot fully between stomps.
- A steady rhythm matters more than speed.

## Running it

Open `index.html` in Chrome or Edge.
