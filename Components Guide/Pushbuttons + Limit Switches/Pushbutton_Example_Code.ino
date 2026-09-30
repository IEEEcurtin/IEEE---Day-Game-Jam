const int BUTTON = 27;

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON, INPUT_PULLUP);
}

void loop() {
  int buttonState = digitalRead(BUTTON);

  if (buttonState == LOW) {
    Serial.println("PRESSED");
  } else {
    Serial.println("NOT PRESSED");
  }

  delay(50);
}
