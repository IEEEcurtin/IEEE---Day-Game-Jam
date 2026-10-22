// ONE Arduino Uno, TWO controllers: { pin, key }
struct Btn { int pin; const char* key; };
Btn buttons[] = {
  // ---- Controller 1 (Player 1) - breadboard 1 ----
  {2, "A"},       // BLUE   - move left
  {3, "D"},       // BLACK  - move right
  {4, "W"},       // YELLOW - jump
  {5, "F"},       // RED    - select fighter & punch
  // ---- Controller 2 (Player 2) - breadboard 2 ----
  {8, "LEFT"},    // BLUE   - move left
  {9, "RIGHT"},   // BLACK  - move right
  {10, "UP"},     // YELLOW - jump
  {11, "K"},      // RED    - select fighter & punch
};

const int N = sizeof(buttons) / sizeof(buttons[0]);
bool state[N];
unsigned long lastChange[N];

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < N; i++) pinMode(buttons[i].pin, INPUT_PULLUP);
}

void loop() {
  for (int i = 0; i < N; i++) {
    bool down = digitalRead(buttons[i].pin) == LOW;
    if (down != state[i] && millis() - lastChange[i] > 30) {
      state[i] = down;
      lastChange[i] = millis();
      Serial.print(buttons[i].key);
      Serial.println(down ? "1" : "0");
    }
  }
}