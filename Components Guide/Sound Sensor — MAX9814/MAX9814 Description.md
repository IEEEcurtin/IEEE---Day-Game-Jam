### 1. What is it?
Detects **sounds such as claps, shouts and loud noises**.

### 2. Preferred component
**MAX9814 microphone amplifier**

### 3. Game Jam uses
- Shout → shield/attack
- Clap → activate something
- Loud noise → trigger an event
- Similar to the shout mechanic in *Rage Quit Simulator*

> The poster uses the **laptop microphone** for Rage Quit Simulator. The MAX9814 would allow a physical microphone connected to the ESP32.

### 4. Wiring

| MAX9814 | ESP32 |
|---|---|
| VDD | 3V3 |
| GND | GND |
| OUT | GPIO 34 |

### 5. Useful link
- [MAX9814 Guide](https://learn.adafruit.com/adafruit-agc-electret-microphone-amplifier-max9814)
