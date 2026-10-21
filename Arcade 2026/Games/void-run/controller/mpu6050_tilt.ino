// MPU6050 tilt + button controller for Arduino Uno
// Works with serial_keyboard.py:  <KEY>1 = press and hold,  <KEY>0 = release
//   Tilt forward = S, left = D, back = W, right = A, button = SPACE

#include <Wire.h>
#include <math.h>

String axisKey(float angle, String current, String posKey, String negKey);
void updateKey(String &held, String next);
int16_t readWord();

const int MPU_ADDR   = 0x68;  // the sensor's address on the two-wire connection
const int BUTTON_PIN = 2;     // button goes between pin 2 and GND

const float TILT_ON  = 20.0;  // degrees of tilt needed to count as "tilted"
const float TILT_OFF = 12.0;  // must come back under this to count as "level" again

const unsigned long DEBOUNCE_MS = 50;  // ignores the tiny flickers a button makes when pressed

float roll  = 0;              // left/right tilt in degrees
float pitch = 0;              // forward/back tilt in degrees
String xKey = "";             // left/right key currently held ("" = none)
String yKey = "";             // forward/back key currently held ("" = none)

bool buttonPressed = false;   // the settled state of the button
bool lastReading = HIGH;      // the raw reading last time round
unsigned long lastChangeTime = 0;

void setup() {
  Serial.begin(9600);         // matches serial_keyboard.py's default speed
  Wire.begin();
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // pin reads HIGH normally, LOW when pressed

  // Wake the sensor up (it starts in sleep mode)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  if (Wire.endTransmission() != 0) {
    Serial.println("MPU6050 not found - check wiring");  // shows up as "ignored" in the script
  }
}

void loop() {
  checkTilt();
  checkButton();
  delay(5);
}

void checkTilt() {
  // Ask for the 6 bytes of accelerometer data (X, Y, Z)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6);

  int16_t ax = readWord();
  int16_t ay = readWord();
  int16_t az = readWord();

  // Each angle is worked out separately so tilting one way doesn't throw off the other
  float newRoll  = atan2(ay, sqrt((float)ax * ax + (float)az * az)) * 180.0 / PI;
  float newPitch = atan2(-ax, sqrt((float)ay * ay + (float)az * az)) * 180.0 / PI;

  // Smooth out shaky readings a little
  roll  = 0.8 * roll  + 0.2 * newRoll;
  pitch = 0.8 * pitch + 0.2 * newPitch;

  // Left/right and forward/back are handled on their own, so two keys can be held at once
  // (e.g. W and A together for a diagonal). Inverted mapping kept from before.
  updateKey(xKey, axisKey(roll,  xKey, "D", "A"));   // right tilt = A, left tilt = D
  updateKey(yKey, axisKey(pitch, yKey, "S", "W"));   // forward tilt = S, back tilt = W
}

// Decides which key (if any) one tilt direction should hold
String axisKey(float angle, String current, String posKey, String negKey) {
  if (angle >  TILT_ON) return posKey;
  if (angle < -TILT_ON) return negKey;
  if (fabs(angle) < TILT_OFF) return "";
  return current;   // in the in-between zone: keep whatever was held
}

// Sends release/press messages only when the key actually changes
void updateKey(String &held, String next) {
  if (next == held) return;
  if (held != "") Serial.println(held + "0");
  if (next != "") Serial.println(next + "1");
  held = next;
}

void checkButton() {
  bool reading = digitalRead(BUTTON_PIN);

  if (reading != lastReading) {
    lastChangeTime = millis();
    lastReading = reading;
  }

  // Only accept the change once it has stayed the same for 50 ms
  if (millis() - lastChangeTime > DEBOUNCE_MS) {
    bool pressedNow = (reading == LOW);
    if (pressedNow != buttonPressed) {
      buttonPressed = pressedNow;
      Serial.println(buttonPressed ? "SPACE1" : "SPACE0");
    }
  }
}

int16_t readWord() {
  int16_t high = Wire.read();
  int16_t low  = Wire.read();
  return (high << 8) | low;
}
