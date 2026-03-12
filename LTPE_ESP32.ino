/*
 * LTPE – ESP32 Prototype with IMU Elevation Bias + Tilt Servo
 * Robert @BobTheFixer73 – March 2026
 *
 * Hardware additions:
 * - MPU-6050 IMU (pitch for elevation bias)
 * - Second servo on pin 12 for LiDAR tilt (elevation pointing)
 *
 * Behavior changes:
 * - Reads pitch from IMU → biases pri (upward = good, downward = bad)
 * - When high-pri or anomalous direction chosen → tilts LiDAR to that elevation
 * - Keeps yaw sweep for horizontal scan
 */

#include <Wire.h>
#include <VL53L1X.h>              // Pololu VL53L1X
#include <Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MPU6050_tockn.h>        // MPU6050 library (install via Library Manager)

// ────────────────────────────────────────────────
//  PINS
// ────────────────────────────────────────────────
#define YAW_SERVO_PIN    13       // horizontal pan
#define TILT_SERVO_PIN   12       // vertical tilt
#define BUTTON_PIN       33
#define BUZZER_PIN       25
#define LED_GOOD         26
#define LED_DEAD         27
#define LED_ANOMALY      14

// ────────────────────────────────────────────────
//  DISPLAY
// ────────────────────────────────────────────────
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ────────────────────────────────────────────────
//  SENSORS
// ────────────────────────────────────────────────
VL53L1X lidar;
MPU6050_tockn mpu6050(Wire);
Servo yawServo;
Servo tiltServo;

// ────────────────────────────────────────────────
//  LTPE State
// ────────────────────────────────────────────────
struct Exif {
  int     yaw_angle;    // 0–180° horizontal
  int     tilt_angle;   // –45° to +45° vertical (servo mapped)
  uint16_t dist_mm;
  uint8_t pri;
  uint8_t anomaly;
  bool    tried;
};

Exif visible[12];
uint8_t vis_count = 0;

int last_yaw_angle = -1;

// ────────────────────────────────────────────────
//  SETUP
// ────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\nLTPE ESP32 with IMU & Tilt Servo");

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_GOOD, OUTPUT);
  pinMode(LED_DEAD, OUTPUT);
  pinMode(LED_ANOMALY, OUTPUT);

  // OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 failed"));
    for(;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("LTPE Starting...");
  display.display();

  // I2C sensors
  Wire.begin();

  // IMU
  mpu6050.begin();
  mpu6050.calcGyroOffsets(true);  // calibrate on flat surface

  // LiDAR
  if (!lidar.init()) {
    Serial.println("VL53L1X failed");
    while(1);
  }
  lidar.setTimeout(500);
  lidar.setDistanceMode(VL53L1X::Long);
  lidar.setMeasurementTimingBudget(50000);

  // Servos
  yawServo.attach(YAW_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  yawServo.write(90);
  tiltServo.write(90);  // neutral / level

  randomSeed(esp_random());

  delay(2000);
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Ready – Press BTN");
  display.display();
}

// ────────────────────────────────────────────────
//  MAIN LOOP
// ────────────────────────────────────────────────
void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    delay(50);
    while (digitalRead(BUTTON_PIN) == LOW);
    scanAndDecide();
  }
}

// ────────────────────────────────────────────────
//  SCAN + DECIDE
// ────────────────────────────────────────────────
void scanAndDecide() {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Scanning...");
  display.display();

  vis_count = 0;

  // Horizontal yaw sweep (0–180°)
  for (int yaw = 0; yaw <= 180; yaw += 15) {
    yawServo.write(yaw);
    delay(120);

    // Read IMU pitch for elevation bias
    mpu6050.update();
    float pitch_deg = mpu6050.getAngleY();  // pitch in degrees

    // Tilt servo to current "interest" level (simple heuristic)
    int tilt_target = map(pitch_deg, -90, 90, 0, 180);  // rough mapping
    tiltServo.write(tilt_target);

    delay(80);  // settle

    lidar.startRanging();
    while (!lidar.dataReady()) delay(1);
    uint16_t dist_mm = lidar.readRange();
    lidar.stopRanging();

    if (dist_mm < 4000 && dist_mm > 20) {
      uint8_t pri = calcPri(dist_mm, yaw, pitch_deg);
      uint8_t ano = calcAnomaly(dist_mm, yaw);

      if (vis_count < 12) {
        visible[vis_count++] = {yaw, tilt_target, dist_mm, pri, ano, false};
      }
    }
  }

  yawServo.write(90);
  tiltServo.write(90);  // reset to level

  if (vis_count == 0) {
    display.clearDisplay();
    display.println("No path!");
    tone(BUZZER_PIN, 300, 1200);
    digitalWrite(LED_DEAD, HIGH);
    delay(2500);
    digitalWrite(LED_DEAD, LOW);
    return;
  }

  display.clearDisplay();
  display.setCursor(0,0);
  display.print("Found ");
  display.print(vis_count);
  display.println(" dirs");

  int idx = pickNext();
  Exif &target = visible[idx];

  display.setCursor(0,16);
  display.print("Go ");
  display.print(target.dist_mm / 10);
  display.print("cm @ yaw ");
  display.print(target.yaw_angle);
  display.print("° tilt ");
  display.print(target.tilt_angle - 90);  // relative to level
  display.println("°");

  if (target.anomaly >= 3) {
    display.println("Anomaly – check!");
    digitalWrite(LED_ANOMALY, HIGH);
    tone(BUZZER_PIN, 1800, 400);
  } else if (target.pri >= 10) {
    digitalWrite(LED_GOOD, HIGH);
    tone(BUZZER_PIN, 1200, 300);
  }

  display.display();
  delay(4000);

  digitalWrite(LED_GOOD, LOW);
  digitalWrite(LED_ANOMALY, LOW);

  last_angle = target.yaw_angle;
  target.tried = true;

  // Physically point gimbal toward target
  yawServo.write(target.yaw_angle);
  tiltServo.write(target.tilt_angle);
  delay(1500);  // hold position briefly
}

// ────────────────────────────────────────────────
//  PRIORITY with ELEVATION BIAS
// ────────────────────────────────────────────────
uint8_t calcPri(uint16_t dist_mm, int yaw, float pitch_deg) {
  uint8_t p = 8;
  if (dist_mm < 1000) p += 5;
  if (dist_mm > 3000) p -= 4;

  // Elevation bonus/penalty
  if (pitch_deg > 10)  p += 5;   // upward = strong exit cue
  if (pitch_deg < -20) p -= 6;   // steep down = danger

  if (yaw >= 60 && yaw <= 120) p += 2;  // forward bias

  if (yaw == last_angle) p = max(0, p - 4);  // avoid immediate revisit

  return constrain(p, 0, 15);
}

// ────────────────────────────────────────────────
//  ANOMALY (unchanged)
// ────────────────────────────────────────────────
uint8_t calcAnomaly(uint16_t dist_mm, int yaw) {
  uint8_t a = 0;
  if (dist_mm < 400 && dist_mm > 50) a += 3;
  if (dist_mm > 3500) a += 2;
  return a;
}

// ────────────────────────────────────────────────
//  Probabilistic Pick (unchanged)
// ────────────────────────────────────────────────
int pickNext() {
  if (random(100) < 10 && vis_count > 0) {
    return random(vis_count);
  }

  int best = 0;
  int best_score = -1;

  for (int i = 0; i < vis_count; i++) {
    if (visible[i].tried) continue;
    int score = visible[i].pri + visible[i].anomaly * 2;
    if (score > best_score) {
      best_score = score;
      best = i;
    }
  }

  return best;
}
