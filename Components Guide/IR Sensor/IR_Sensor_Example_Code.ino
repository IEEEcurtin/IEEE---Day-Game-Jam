const int IR = 27;

void setup() {
  Serial.begin(115200);
  pinMode(IR, INPUT);
}

void loop() {
  Serial.println(digitalRead(IR));
  delay(100);
}
