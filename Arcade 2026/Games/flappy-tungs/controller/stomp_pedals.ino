#include <BleKeyboard.h>
BleKeyboard kb("Stomp Pedals");

const int PIN1 = 34, PIN2 = 35;   // piezo inputs (ADC pins)
const int THRESH = 600;           // raise if it misfires, lower if it misses
const int COOLDOWN = 120;         // ms between triggers
unsigned long last1 = 0, last2 = 0;

void setup() { kb.begin(); }

void loop() {
  if (!kb.isConnected()) return;
  unsigned long now = millis();
  if (analogRead(PIN1) > THRESH && now - last1 > COOLDOWN) { kb.write('a'); last1 = now; }
  if (analogRead(PIN2) > THRESH && now - last2 > COOLDOWN) { kb.write('l'); last2 = now; }
}