/*
  DEAD TAPE - cardboard gun controller
  ESP32 + MPU6050 + one limit switch, acting as a Bluetooth keyboard.

  What it sends to the game:
    W      gun pointed away from you (at the other player)
    S      gun turned around toward yourself
    X      gun lowered (pointing at the floor)
    SPACE  held while the trigger switch is pressed, released when let go
    F      sharp upward jerk = fake shot (taunt)
    R      quick twisting shake = spin the cylinder

  Aim keys are only sent when the aim CHANGES. The game remembers the last one.

  WIRING
    MPU6050 VCC -> 3V3      MPU6050 GND -> GND
    MPU6050 SDA -> GPIO 21  MPU6050 SCL -> GPIO 22
    Trigger limit switch: one leg -> GPIO 18, other leg -> GND  (uses the internal pull-up)
    Onboard LED (GPIO 2) lights when the laptop is connected.

  MOUNTING (important)
    Glue the MPU6050 flat inside the gun body, chip facing up,
    with the X arrow printed on the board pointing toward the muzzle.
    If you mount it differently, change the AXIS settings below.

  LIBRARY
    "ESP32 BLE Keyboard" by T-vK: download the ZIP from
    https://github.com/T-vK/ESP32-BLE-Keyboard and use Sketch > Include Library > Add .ZIP Library.
    If it fails to compile with errors about std::string / String, go to
    Tools > Board > Boards Manager, and install esp32 by Espressif version 2.0.17.

  FIRST RUN
    1. Set DEBUG to true, upload, open Serial Monitor at 115200.
    2. Keep the gun STILL on the table for 2 seconds while it calibrates (LED blinks).
    3. Move the gun and watch pitch / yaw / rates. Adjust the thresholds if needed.
    4. Set DEBUG back to false, upload, then pair "DeadTape Gun" in the laptop's Bluetooth settings.
*/

#include <Wire.h>
#include <BleKeyboard.h>

BleKeyboard kb("DeadTape Gun", "IEEE Game Jam", 100);

// ---------- pins ----------
const int PIN_TRIGGER = 18;
const int PIN_LED     = 2;
const int MPU_ADDR    = 0x68;

// ---------- axis settings (change if the sensor is mounted differently) ----------
// Which sensor axis points along the barrel toward the muzzle, and its sign.
// 0 = X, 1 = Y, 2 = Z
const int   BARREL_AXIS = 0;   const float BARREL_SIGN = 1.0;
const int   UP_AXIS     = 2;   const float UP_SIGN     = 1.0;
const int   SIDE_AXIS   = 1;   // the remaining axis

// ---------- tuning ----------
const float LOWER_PITCH   = -45.0;  // barrel this far below horizontal = lowered (X)
const float RAISE_PITCH   = -30.0;  // barrel back above this = raised again
const float SELF_YAW      = 110.0;  // turned this far from the start direction = pointing at yourself (S)
const float BACK_YAW      =  70.0;  // turned back under this = pointing at them again (W)
const float YAW_DEADBAND  =   2.0;  // ignore tiny rotations (deg/s) so yaw does not drift
const float JERK_DPS      = 380.0;  // barrel flick upward faster than this = fake shot (F)
const float SHAKE_DPS     = 280.0;  // twist faster than this counts as one shake swing
const int   SHAKE_SWINGS  =   4;    // swings needed (within SHAKE_WINDOW) to spin (R)
const unsigned long SHAKE_WINDOW = 800;
const unsigned long JERK_COOLDOWN  = 1200;
const unsigned long SHAKE_COOLDOWN = 2000;
const unsigned long DEBOUNCE_MS    = 20;

const bool DEBUG = false;   // true = print sensor values to Serial Monitor, no keys sent

// ---------- state ----------
float gyroBias[3] = {0, 0, 0};
float acc[3], gyr[3];         // g and deg/s, in sensor axes
float yaw = 0;                // degrees turned since the gun was raised
char  aim = 'x';              // 'w', 's' or 'x'
bool  trigDown = false, trigRaw = false;
unsigned long trigChangedAt = 0, lastJerk = 0, lastShake = 0, shakeStart = 0;
int   shakeSwings = 0, lastShakeSign = 0;
unsigned long lastMicros = 0, lastPrint = 0;
bool  wasConnected = false;

// ---------- MPU6050 ----------
void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR); Wire.write(reg); Wire.write(val); Wire.endTransmission();
}
bool mpuRead() {
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, 14) != 14) return false;
  int16_t r[7];
  for (int i = 0; i < 7; i++) r[i] = (Wire.read() << 8) | Wire.read();
  for (int i = 0; i < 3; i++) acc[i] = r[i] / 4096.0;                       // +-8 g
  for (int i = 0; i < 3; i++) gyr[i] = r[i + 4] / 16.4 - gyroBias[i];       // +-2000 deg/s
  return true;
}
void calibrateGyro() {
  float sum[3] = {0, 0, 0}; int n = 0;
  for (int i = 0; i < 400; i++) {
    float saved[3] = {gyroBias[0], gyroBias[1], gyroBias[2]};
    gyroBias[0] = gyroBias[1] = gyroBias[2] = 0;
    if (mpuRead()) { for (int k = 0; k < 3; k++) sum[k] += gyr[k]; n++; }
    gyroBias[0] = saved[0]; gyroBias[1] = saved[1]; gyroBias[2] = saved[2];
    digitalWrite(PIN_LED, (i / 25) % 2);
    delay(5);
  }
  if (n) for (int k = 0; k < 3; k++) gyroBias[k] = sum[k] / n;
  digitalWrite(PIN_LED, LOW);
}

// ---------- keys ----------
void tap(char c) {
  if (DEBUG) { Serial.printf(">> key %c\n", c); return; }
  if (kb.isConnected()) kb.write(c);
}
void setAim(char a) {
  if (aim == a) return;
  aim = a;
  tap(a);
}

void setup() {
  pinMode(PIN_TRIGGER, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(400000);
  mpuWrite(0x6B, 0x00);   // wake up
  mpuWrite(0x1A, 0x03);   // low-pass filter ~44 Hz
  mpuWrite(0x1B, 0x18);   // gyro +-2000 deg/s
  mpuWrite(0x1C, 0x10);   // accel +-8 g
  delay(100);
  if (!mpuRead()) Serial.println("MPU6050 not found - check SDA/SCL wiring");
  Serial.println("Calibrating, keep the gun still...");
  calibrateGyro();
  Serial.println("Ready.");
  if (!DEBUG) kb.begin();
  lastMicros = micros();
}

void loop() {
  // connection LED; release everything if the laptop drops
  bool conn = !DEBUG && kb.isConnected();
  digitalWrite(PIN_LED, conn ? HIGH : LOW);
  if (wasConnected && !conn) { trigDown = false; aim = 'x'; }
  wasConnected = conn;

  unsigned long now = millis();
  float dt = (micros() - lastMicros) / 1e6; lastMicros = micros();
  if (dt > 0.05) dt = 0.05;

  // ---------- trigger (debounced) ----------
  bool raw = digitalRead(PIN_TRIGGER) == LOW;
  if (raw != trigRaw) { trigRaw = raw; trigChangedAt = now; }
  if (now - trigChangedAt > DEBOUNCE_MS && trigRaw != trigDown) {
    trigDown = trigRaw;
    if (DEBUG) Serial.println(trigDown ? ">> SPACE down" : ">> SPACE up");
    else if (conn) { if (trigDown) kb.press(' '); else kb.release(' '); }
  }

  if (!mpuRead()) { delay(5); return; }

  // ---------- orientation ----------
  float barrel = acc[BARREL_AXIS] * BARREL_SIGN;
  float up     = acc[UP_AXIS] * UP_SIGN;
  float side   = acc[SIDE_AXIS];
  float pitch  = atan2(barrel, sqrt(up * up + side * side)) * 57.2958;   // + = muzzle up
  float yawRate   = gyr[UP_AXIS] * UP_SIGN;      // turning left/right
  float pitchRate = -gyr[SIDE_AXIS];             // muzzle flicking up (flip sign if jerks don't register)
  float rollRate  = gyr[BARREL_AXIS] * BARREL_SIGN;  // twisting

  // ---------- aim: lowered / at them / at yourself ----------
  if (pitch < LOWER_PITCH) {
    yaw = 0;                           // re-zero while lowered: raising it = pointing at them
    setAim('x');
  } else {
    if (aim == 'x' && pitch > RAISE_PITCH) { yaw = 0; setAim('w'); }
    if (aim != 'x') {
      if (fabs(yawRate) > YAW_DEADBAND) yaw += yawRate * dt;
      if (aim == 'w' && fabs(yaw) > SELF_YAW) setAim('s');
      else if (aim == 's' && fabs(yaw) < BACK_YAW) setAim('w');
    }
  }

  // ---------- shake to spin (fast back-and-forth twisting) ----------
  if (fabs(rollRate) > SHAKE_DPS) {
    int sgn = rollRate > 0 ? 1 : -1;
    if (sgn != lastShakeSign) {
      if (shakeSwings == 0 || now - shakeStart > SHAKE_WINDOW) { shakeSwings = 0; shakeStart = now; }
      shakeSwings++; lastShakeSign = sgn;
    }
  }
  bool shaking = shakeSwings >= 2 && now - shakeStart < SHAKE_WINDOW;
  if (shakeSwings >= SHAKE_SWINGS && now - shakeStart < SHAKE_WINDOW && now - lastShake > SHAKE_COOLDOWN) {
    tap('r'); lastShake = now; shakeSwings = 0;
  }

  // ---------- fake shot: a sharp upward flick without pulling the trigger ----------
  if (!trigDown && !shaking && aim != 'x' && pitchRate > JERK_DPS && now - lastJerk > JERK_COOLDOWN && now - lastShake > 500) {
    tap('f'); lastJerk = now;
  }

  // ---------- debug output ----------
  if (DEBUG && now - lastPrint > 100) {
    lastPrint = now;
    Serial.printf("pitch %6.1f  yaw %7.1f  aim %c | yawRate %7.1f  pitchRate %7.1f  rollRate %7.1f | trig %d\n",
                  pitch, yaw, aim, yawRate, pitchRate, rollRate, trigDown);
  }
  delay(4);   // ~200 readings a second
}
