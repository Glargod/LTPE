/*
  LTPE_ESP32.ino — v6.0 locked scoring loop on ESP32
  Hardware scan (servo + LiDAR) -> score -> optional ritual nudge -> softmax pick.
  See HOWTO.md for wiring.
*/
#include <Wire.h>
#include <VL53L1X.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP32Servo.h>

static const int PIN_SERVO=13, PIN_BTN=33, PIN_BUZZ=25, PIN_LED_OK=26, PIN_LED_DE=27, PIN_LED_AN=14;
static const float LAMBDA=0.15f, SIGMA=0.40f, BETA=1.40f;
static const float W1=0.40f, W2=0.25f, W3=0.20f, W4=0.15f;
static const int STEP_DEG=15, NDIR=13, KMAX=5;
static const uint16_t DEAD_MM=180, ANOM_MM=2400;

Adafruit_SSD1306 display(128,64,&Wire,-1);
VL53L1X lidar;
Servo yaw;
int ritualCount=0;
uint32_t scanSteps=0;
bool useRitual=true;

struct Beam { int deg; uint16_t mm; float score; };
float urand(){ return (float)esp_random()/4294967295.0f; }

float scoreBeam(uint16_t mm, int openApprox){
  float distTerm=1.0f/(1.0f+(mm/400.0f));
  float A=(mm>400 && mm<1600)?0.8f:0.3f;
  float B=openApprox/4.0f;
  float H=(mm<DEAD_MM)?1.0f:0.0f;
  float eps=urand()*SIGMA;
  float goalish=1.0f-distTerm;
  return W1*goalish + W2*A + W3*B - W4*H + eps;
}

void ritualNudge(Beam* arr, int n, int m){
  float logm=logf(1.0f+(float)m);
  for(int i=0;i<n;i++){
    float factor=1.0f-LAMBDA*logm*((float)i/(float)max(n,1));
    if(factor<0.05f) factor=0.05f;
    arr[i].score*=factor;
  }
}

int softmaxPick(Beam* arr, int n){
  float w[NDIR]; float total=0;
  for(int i=0;i<n;i++){ w[i]=powf(fmaxf(arr[i].score,1e-6f), BETA); total+=w[i]; }
  float pick=urand()*total, acc=0;
  for(int i=0;i<n;i++){ acc+=w[i]; if(pick<=acc) return i; }
  return n-1;
}

void setup(){
  Serial.begin(115200);
  pinMode(PIN_BTN, INPUT_PULLUP);
  pinMode(PIN_BUZZ, OUTPUT);
  pinMode(PIN_LED_OK, OUTPUT);
  pinMode(PIN_LED_DE, OUTPUT);
  pinMode(PIN_LED_AN, OUTPUT);
  Wire.begin(21,22);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay(); display.setTextSize(1); display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0); display.println("LTPE v6.0 ESP32"); display.display();
  lidar.setTimeout(500);
  if(lidar.init()){ lidar.setDistanceMode(VL53L1X::Long); lidar.setMeasurementTimingBudget(33000); lidar.startContinuous(50); }
  yaw.setPeriodHertz(50); yaw.attach(PIN_SERVO,500,2400); yaw.write(90);
  randomSeed(esp_random());
}

void loop(){
  if(digitalRead(PIN_BTN)!=LOW){ delay(20); return; }
  delay(40);
  while(digitalRead(PIN_BTN)==LOW) delay(10);
  scanSteps++;
  Beam beams[NDIR]; int n=0, openApprox=0;
  for(int deg=0; deg<=180; deg+=STEP_DEG){
    yaw.write(deg); delay(120);
    uint16_t mm=lidar.read();
    if(lidar.timeoutOccurred()) mm=0;
    if(mm>DEAD_MM) openApprox++;
    beams[n].deg=deg; beams[n].mm=mm; n++;
  }
  for(int i=0;i<n;i++) beams[i].score=scoreBeam(beams[i].mm, openApprox);
  for(int i=0;i<n;i++) for(int j=i+1;j<n;j++) if(beams[j].score>beams[i].score){ Beam t=beams[i]; beams[i]=beams[j]; beams[j]=t; }
  int k=min(KMAX,n);
  bool complexFork=(openApprox>=4);
  if(useRitual && ((scanSteps%100)==0 || complexFork) && complexFork){
    ritualCount++; ritualNudge(beams,k,ritualCount);
  }
  int pick=softmaxPick(beams,k);
  Beam chosen=beams[pick];
  digitalWrite(PIN_LED_OK, chosen.mm>DEAD_MM);
  digitalWrite(PIN_LED_DE, chosen.mm<=DEAD_MM);
  digitalWrite(PIN_LED_AN, chosen.mm>=ANOM_MM);
  tone(PIN_BUZZ, chosen.mm>=ANOM_MM?1200:(chosen.mm<=DEAD_MM?220:600), 80);
  display.clearDisplay(); display.setCursor(0,0);
  display.printf("dirs %d  k %d\n", n, k);
  display.printf("pick %d deg\n", chosen.deg);
  display.printf("mm   %u\n", chosen.mm);
  display.printf("sc   %.2f\n", chosen.score);
  display.printf("rit  %d\n", ritualCount);
  display.display();
  Serial.printf("pick=%d deg mm=%u score=%.3f ritual=%d\n", chosen.deg, chosen.mm, chosen.score, ritualCount);
  yaw.write(chosen.deg);
}
