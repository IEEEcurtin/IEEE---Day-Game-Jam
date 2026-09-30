### 1. What is it?
Detects **tilting, movement, rotation and shaking**.

### 2. Preferred component
**MPU6050**

### 3. Game Jam uses
- Tilt controller → *Tilt Tank Tussle*
- Shake → *Rage Quit Simulator*
- Hold still → *Steady Hand Sam*
- Swing → *Cardboard Ninja*

### 4. Wiring

| MPU6050 | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### 5. Useful links
- [ESP32 Setup Guide](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [ESP32 DevKit Pinout](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)
