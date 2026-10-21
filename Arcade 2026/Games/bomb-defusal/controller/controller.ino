#include <Keypad.h>

// =====================================================
// 4x4 KEYPAD SETUP
// =====================================================

const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

// Keypad rows
byte rowPins[ROWS] = {
  14,
  12,
  13,
  15
};

// Keypad columns
byte colPins[COLS] = {
  2,
  4,
  18,
  5
};

Keypad keypad = Keypad(
  makeKeymap(keys),
  rowPins,
  colPins,
  ROWS,
  COLS
);


// =====================================================
// COLOUR BUTTONS
// =====================================================

const int RED_PIN = 27;
const int BLUE_PIN = 26;
const int GREEN_PIN = 25;


// =====================================================
// SETUP
// =====================================================

void setup() {

  // Start Serial communication
  Serial.begin(115200);

  // Colour buttons use internal pull-up resistors
  pinMode(RED_PIN, INPUT_PULLUP);
  pinMode(BLUE_PIN, INPUT_PULLUP);
  pinMode(GREEN_PIN, INPUT_PULLUP);

}


// =====================================================
// MAIN LOOP
// =====================================================

void loop() {

  // ---------------------------------------------------
  // CHECK KEYPAD
  // ---------------------------------------------------

  char key = keypad.getKey();

  if (key) {

    Serial.print("KEY_");
    Serial.println(key);

  }


  // ---------------------------------------------------
  // CHECK RED BUTTON
  // ---------------------------------------------------

  if (digitalRead(RED_PIN) == LOW) {

    Serial.println("RED");

    delay(180);

  }


  // ---------------------------------------------------
  // CHECK BLUE BUTTON
  // ---------------------------------------------------

  if (digitalRead(BLUE_PIN) == LOW) {

    Serial.println("BLUE");

    delay(180);

  }


  // ---------------------------------------------------
  // CHECK GREEN BUTTON
  // ---------------------------------------------------

  if (digitalRead(GREEN_PIN) == LOW) {

    Serial.println("GREEN");

    delay(180);

  }

}
