### 1. What is it? 
Detects **knocks, taps, hits and vibrations**. 
### 2. Preferred component 
**Raw piezo disc** 
### 3. Game Jam uses 
- Stomp → *Lava Floor Jump* 
- Drum hit → *Drum Hero* - Tap → Trigger an action 
- Slam controller → *Rage Quit Simulator* 
### 4. Wiring 

| Piezo         | ESP32            |
| ------------- | ---------------- |
| One side      | GPIO 34          |
| Other side    | GND              |
| 1 MΩ resistor | Across the piezo |

### 5. Useful link

- [Arduino Knock Example](https://docs.arduino.cc/built-in-examples/sensors/Knock/)
