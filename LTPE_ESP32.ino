/*
 * LTPE – ESP32 Prototype with IMU Elevation & 3D Coordinates
 * Robert @BobTheFixer73 – March 2026
 *
 * Now includes:
 * - MPU-6050 IMU for pitch (elevation) bias & 3D coord calculation
 * - Relative (x,y,z) positions for each visible point
 * - Tilt servo only for final pointing (not scanning)
 */

#include <Wire.h>
#include <VL53L1X.h>
#include <Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MPU6050_tockn.h>

// ────────────────────────────────────────────────
//  PINS
// ────────────────────────────────────────────────
#define YAW_SERVO_PIN    13
#define TILT_SERVO_PIN   12
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
//  LTPE State with 3D coords
// ────────────────────────────────────────────────
struct Exif {
  int     yaw_deg;      // horizontal 0–180
  float   pitch_deg;    // vertical from IMU
  uint16_t dist_mm;
  uint8_t pri;
  uint8_t anomaly;
  bool    tried;

  // 3D relative position (cm)
  float   x;            // forward
  float   y;            // right/left
  float   z;            // up/down
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
  Serial.println("\nLTPE ESP32 with IMU Elevation & 3D Coords");

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

  // I2C
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
  tiltServo.write(90);

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
//  SCAN + DECIDE + 3D COORDS
// ────────────────────────────────────────────────
void scanAndDecide() {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Scanning...");
  display.display();

  vis_count = 0;

  for (int yaw = 0; yaw <= 180; yaw += 15) {
    yawServo.write(yaw);
    delay(120);

    // Read current pitch from IMU
    mpu6050.update();
    float pitch_deg = mpu6050.getAngleY();  // pitch in degrees

    // Tilt servo to match current interest or neutral
    int tilt_target = constrain(map(pitch_deg, -60, 60, 0, 180), 0, 180);
    tiltServo.write(tilt_target);
    delay(80);

    lidar.startRanging();
    while (!lidar.dataReady()) delay(1);
    uint16_t dist_mm = lidar.readRange();
    lidar.stopRanging();

    if (dist_mm < 4000 && dist_mm > 20) {
      uint8_t pri = calcPri(dist_mm, yaw, pitch_deg);
      uint8_t ano = calcAnomaly(dist_mm, yaw);

      // Compute 3D relative position (simple spherical to cartesian)
      float dist_m = dist_mm / 1000.0;
      float yaw_rad = radians(yaw - 90);      // center = 0° forward
      float pitch_rad = radians(pitch_deg);

      float x = dist_m * cos(pitch_rad) * cos(yaw_rad);   // forward
      float y = dist_m * cos(pitch_rad) * sin(yaw_rad);   // left/right
      float z = dist_m * sin(pitch_rad);                  // up/down

      if (vis_count < 12) {
        visible[vis_count] = {yaw, tilt_target, dist_mm, pri, ano, false};
        visible[vis_count].x = x * 100;  // cm
        visible[vis_count].y = y * 100;
        visible[vis_count].z = z * 100;
        vis_count++;
      }
    }
  }

  yawServo.write(90);
  tiltServo.write(90);

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
  display.print(target.tilt_angle - 90);
  display.println("°");

  display.setCursor(0,40);
  display.print("Pos: ");
  display.print((int)target.x); display.print(",");
  display.print((int)target.y); display.print(",");
  display.print((int)target.z); display.println(" cm");

  if (target.anomaly >= 3) {
    display.println("Anomaly!");
    digitalWrite(LED_ANOMALY, HIGH);
    tone(BUZZER_PIN, 1800, 400);
  } else if (target.pri >= 10) {
    digitalWrite(LED_GOOD, HIGH);
    tone(BUZZER_PIN, 1200, 300);
  }

  display.display();
  delay(5000);

  digitalWrite(LED_GOOD, LOW);
  digitalWrite(LED_ANOMALY, LOW);

  last_yaw_angle = target.yaw_angle;
  target.tried = true;

  // Point toward target
  yawServo.write(target.yaw_angle);
  tiltServo.write(target.tilt_angle);
  delay(2000);
}

// ────────────────────────────────────────────────
//  PRIORITY with ELEVATION
// ────────────────────────────────────────────────
uint8_t calcPri(uint16_t dist_mm, int yaw, float pitch_deg) {
  uint8_t p = 8;
  if (dist_mm < 1000) p += 5;
  if (dist_mm > 3000) p -= 4;

  // Elevation bias
  if (pitch_deg > 10)  p += 5;   // upward = strong exit cue
  if (pitch_deg < -20) p -= 6;   // steep down = danger

  if (yaw >= 60 && yaw <= 120) p += 2;

  if (yaw == last_yaw_angle) p = max(0, p - 4);

  return constrain(p, 0, 15);
}

// ────────────────────────────────────────────────
//  ANOMALY
// ────────────────────────────────────────────────
uint8_t calcAnomaly(uint16_t dist_mm, int yaw) {
  uint8_t a = 0;
  if (dist_mm < 400 && dist_mm > 50) a += 3;
  if (dist_mm > 3500) a += 2;
  return a;
}

// ────────────────────────────────────────────────
//  Probabilistic Pick
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
