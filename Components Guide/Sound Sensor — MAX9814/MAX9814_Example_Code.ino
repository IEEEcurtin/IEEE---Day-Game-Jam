const int SOUND = 34;

void setup() {
  Serial.begin(115200);
}

void loop() {
  Serial.println(analogRead(SOUND));
  delay(20);
}
