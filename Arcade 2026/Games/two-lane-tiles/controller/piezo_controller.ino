// Two piezo discs as LEFT and RIGHT buttons.
// Wiring for each disc:
//   red wire   -> its analog pin (A0 or A1)
//   black wire -> GND
//   1 megaohm resistor between the analog pin and GND (drains leftover charge so readings settle)

const int   PINS[] = {A0, A1};
const char* KEYS[] = {"LEFT", "RIGHT"};

const int THRESHOLD = 800;             // 0-1023. Raise if it triggers by itself, lower if soft hits are missed.
const unsigned long HOLD_MS = 30;      // how long each hit holds the key down
const unsigned long COOLDOWN_MS = 80;  // ignore the disc's leftover vibration after a hit

// true = show raw readings in Tools > Serial Plotter, for picking THRESHOLD.
// Set back to false before running the Python script.
const bool SHOW_LEVELS = false;

const int COUNT = sizeof(PINS) / sizeof(PINS[0]);
bool held[COUNT];
unsigned long hitTime[COUNT];

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < COUNT; i++) {
    held[i] = false;
    hitTime[i] = 0;
  }
}

void loop() {
  unsigned long now = millis();

  for (int i = 0; i < COUNT; i++) {
    int level = analogRead(PINS[i]);

    if (SHOW_LEVELS) {
      Serial.print(KEYS[i]);
      Serial.print(":");
      Serial.print(level);
      Serial.print(i < COUNT - 1 ? " " : "\n");
      continue;
    }

    // A hit: press the key
    if (!held[i] && level > THRESHOLD && now - hitTime[i] > COOLDOWN_MS) {
      held[i] = true;
      hitTime[i] = now;
      Serial.print(KEYS[i]);
      Serial.println("1");
    }

    // Release the key shortly after the hit
    if (held[i] && now - hitTime[i] >= HOLD_MS) {
      held[i] = false;
      Serial.print(KEYS[i]);
      Serial.println("0");
    }
  }

  if (SHOW_LEVELS) delay(5);
}
