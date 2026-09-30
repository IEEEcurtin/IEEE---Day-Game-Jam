### 1. What is it?
Measures the **distance between the sensor and an object**.

### 2. Preferred component
**HC-SR04**

### 3. Game Jam uses
- Hand gets closer → attack
- Detect nearby objects
- Distance-based movement
- Gesture controller

### 4. Wiring

| HC-SR04 | ESP32 |
|---|---|
| VCC | 5V / VIN |
| GND | GND |
| TRIG | GPIO 5 |
| ECHO | GPIO 18 through voltage divider |

**Voltage divider for ECHO:**

```text
HC-SR04 ECHO
      |
     10kΩ
      |
      +------ GPIO 18
      |
     10kΩ
      |
     GND
```

### 5. Useful link
- [HC-SR04 Guide](https://learn.adafruit.com/ultrasonic-sonar-distance-sensors)
