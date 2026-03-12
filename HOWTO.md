# LTPE ESP32 Prototype – HOWTO

This is a simple hardware implementation of the **LTPE** (Line-of-Sight Priority-Guided Escape) algorithm on ESP32.

It scans forward with a servo-swept LiDAR, computes priorities + anomaly bonuses, makes probabilistic decisions, and gives feedback via OLED, buzzer, and LEDs.

## Hardware Needed

| Component             | Recommendation / Notes                     | Approx Cost |
|-----------------------|--------------------------------------------|-------------|
| ESP32 board           | DevKit, NodeMCU, WROOM, etc.               | $6–12       |
| LiDAR                 | VL53L1X (Pololu/SparkFun) or VL53L0X       | $5–15       |
| Micro servo           | SG90 or similar (for yaw/horizontal scan)  | $2–5        |
| 0.96" OLED            | SSD1306 I²C (128×64)                       | $4–7        |
| Buzzer                | Active or passive piezo                    | $1          |
| 3 LEDs                | Good (green), Dead-end (red), Anomaly (blue) + 220 Ω resistors | $1 |
| Push button           | Momentary with internal pull-up            | $1          |
| Jumper wires & breadboard | —                                          | —           |

**Optional future add-ons**:
- MPU-6050 IMU for elevation bias
- Second servo for tilt (elevation pointing)
- TFmini-S or Garmin LIDAR-Lite for longer range

## Wiring

| Component         | ESP32 Pin(s)       | Notes                              |
|-------------------|--------------------|------------------------------------|
| LiDAR VCC         | 3.3V               | (or 5V if your model requires)     |
| LiDAR GND         | GND                |                                    |
| LiDAR SDA         | 21                 | I²C data                           |
| LiDAR SCL         | 22                 | I²C clock                          |
| Yaw Servo signal  | 13                 | PWM                                |
| Yaw Servo power   | 5V / 3.3V          | Use external supply if high torque |
| Button            | 33                 | INPUT_PULLUP (other side to GND)   |
| Buzzer +          | 25                 | Other side to GND                  |
| LED Good          | 26                 | + 220 Ω resistor to GND            |
| LED Dead-end      | 27                 | + 220 Ω resistor to GND            |
| LED Anomaly       | 14                 | + 220 Ω resistor to GND            |
| OLED SDA/SCL      | 21 / 22            | Same I²C bus as LiDAR              |

## Required Libraries

Install via Arduino IDE → **Library Manager**:

- `VL53L1X` by Pololu (or `Adafruit_VL53L0X` if using VL53L0X)
- `Adafruit_SSD1306` + `Adafruit_GFX`
- `Servo` (built-in)

## Upload & Run

1. Open Arduino IDE
2. Select board: **ESP32 Dev Module** (or your variant)
3. Select port
4. Paste the code from `LTPE_ESP32.ino` (or download from repo)
5. Upload
6. Open Serial Monitor (115200 baud) for debug output
7. Press the button → watch OLED for scan results + decision
8. Listen to buzzer and observe LEDs for feedback

## What to Expect

- **Press button** → servo sweeps 0–180° in 15° steps (\~2–3 seconds)
- **LiDAR** measures distance in each direction
- **Priority (0–15)** + **anomaly bonus (0–5)** computed
- **Decision** made probabilistically (weighted + 10% random)
- **OLED** shows: number of directions, chosen direction + distance
- **Buzzer/LEDs** signal: good path, dead-end, or anomaly ("butler" exit)

## Troubleshooting

| Issue                          | Possible Fix                                                                 |
|--------------------------------|------------------------------------------------------------------------------|
| OLED blank                     | Check I²C address (0x3C or 0x3D), wiring, power                              |
| LiDAR no reading               | Verify I²C pins, power (3.3V), library match, XSHUT pin if used              |
| Servo jitter / no movement     | Add 100–470 µF capacitor across servo power; check PWM pin                   |
| No buzzer sound                | Test polarity; passive piezo needs `tone()`; active piezo just HIGH/LOW      |
| Random choices repeat          | `randomSeed(esp_random())` should fix; if not, use `analogRead(0) + millis()`|
| Button not responding          | Confirm INPUT_PULLUP, wiring (button between pin & GND)                      |

## Future Ideas

- Add MPU-6050 IMU → elevation bias (upward = higher pri)
- Second servo → active tilt pointing toward best direction
- WiFi logging → send scan data to phone/browser
- Dynamic obstacle watchdog → continuous forward check
- Spiral scan pattern → more efficient coverage
- Motor control → physically turn robot toward chosen direction

Enjoy hacking!  
Questions, PRs, or photos of your build → open an issue or ping @BobTheFixer73 on X.

🐜🪐🕯️✨
