#include<Servo.h>
#include <SerialCommand.h>
#include <LiquidCrystal_I2C.h>
LiquidCrystal_I2C lcd(0x27, 16, 2);

//Pin
#define startBtn  A0
#define BTAI 11
#define BOM 6
#define NHA 5

//Parameter Robot
#define a4  13
#define d1  13
#define a2  16
#define a3  16

//Velocity conveyolt
#define Vo  4.9 //cm/s

//define servo name
Servo SV1;
Servo SV2;
Servo SV3;
Servo SV4;
int GOC1 = 90;
int GOC2 = 90;
int GOC3 = 90;
int GOC4 = 90;
int G;
//StartBtnState
int buttonState = 0;
int lastButtonState = 0;

float A[5];
float newPy;
float t, t1, t2, t3;
float th1, th2, th3, th4;
unsigned long tb;
const float des[3][4] = {{7, -21, -3, 0}, {0, -20, -3, 0}, { -7, -20, -3, 0}};
int C[3] = {0, 0, 0};
int anglePlus[3] = {25, 0, -18};

SerialCommand sc;

//---------------------------------------------------------------------------------

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  lcd.clear();

  pinMode(startBtn, INPUT_PULLUP);
  pinMode(BTAI, OUTPUT);
  analogWrite(BTAI, 100);
  pinMode(BOM, OUTPUT);
  pinMode(NHA, OUTPUT);
  SV2.attach(9);
  SV3.attach(8);

  SV1.attach(10);
  SV4.attach(7);

  sc.addCommand("obj", Obj);
  sc.addCommand("h", Home);
  sc.setDefaultHandler(unrecognized);
}

//---------------------------------------------------------------------------------

void loop() {
  sc.readSerial();
  wait();
  checkBtnState();
  display();
}

void display() {
  String color;
  lcd.setCursor(0, 1); lcd.print("R:");
  lcd.setCursor(2, 1); lcd.print(C[2]);
  lcd.setCursor(5, 1); lcd.print("G:");
  lcd.setCursor(7, 1); lcd.print(C[1]);
  lcd.setCursor(10, 1); lcd.print("B:");
  lcd.setCursor(12, 1); lcd.print(C[0]);

  lcd.setCursor(0, 0); lcd.print(A[0]);
  lcd.setCursor(5, 0); lcd.print("-");
  lcd.setCursor(6, 0); lcd.print(A[1]);
  lcd.setCursor(11, 0); lcd.print("-");
  lcd.setCursor(12, 0); lcd.print(A[3]);
  if (A[4] == 0) {
    color = "B";
  } else if (A[4] == 1) {
    color = "G";
  } else if (A[4] == 2) {
    color = "R";
  };
  lcd.setCursor(15, 0); lcd.print(color);
}
void checkBtnState() {
  buttonState = digitalRead(startBtn);
  if (buttonState != lastButtonState) {
    if (buttonState == 0) {
      Serial.println(4);
    } else {
      Serial.println(5);
    }
    delay(50);
  }
  lastButtonState = buttonState;
}

void Obj() {
  updateData();
  tb = millis();
  moving();
}

void updateData() {
  char *arg;
  for (int i = 0; i < 5; i++) {
    arg = sc.next();
    if (arg == NULL) break;
    A[i] = atof(arg);
  }
}

void moving() {
  Invert(A[0], A[1], A[2], A[3]);
  G = SV1.read();
  t1 = (abs(th1 - SV1.read()) * 170 / 60) + (abs(th1 - SV1.read()) * 12);
  t2 = (abs(th2 - SV2.read()) * 170 / 60) + (abs(th2 - SV2.read()) * 12);
  t3 = (abs(th3 - SV3.read()) * 170 / 60) + (abs(th3 - SV3.read()) * 12);
  t = round(t1 + t2 + t3);
  newPy = t * Vo;
  newPy = A[1] - newPy / 1000;
  Invert(A[0], newPy, A[2] + 4, A[3]);
  MOVE();
}

void Invert(float Px, float Py, float Pz, float Or) {
  th1 = atan2(Py, Px);
  float Pz1 = Pz - d1 + a4;
  th3 = acos((sq(Px) + sq(Py) + sq(Pz1) - sq(a2) - sq(a3)) / (2 * a2 * a3));
  th2 = asin(Pz1 / (sqrt(sq(Px) + sq(Py) + sq(Pz1)))) + atan2(a3 * sin(abs(th3)), a2 + a3 * cos(th3));
  th1 *= 180 / PI;  th2 *= 180 / PI;
  th3 *= 180 / PI;
  th1 = round(90 + th1 + 20);
  th2 = round(180 - th2 - 10);
  th3 = round(th3 - 40);
  if (Or > 90) {
    th4 = (180 - Or) + 90 - 10;
  } else {
    th4 = (90 - Or) - 20;
  }
}

void MOVE() {
  CTAY3(th3, 12);
  CTAY1(th1, 12);
  CTAY2(th2, 12);
}

void wait() {
  int c = A[4];
  c = constrain(c, 0, 2);
  if (t && (millis() - tb > t )) {
    Invert(A[0], newPy, A[2], A[3]);
    MOVE();
    digitalWrite(BOM, 1);
    CTAY2(80, 10);
    SV4.write(th4 + anglePlus[c]);
    int meo = G - SV1.read();
    Invert(des[c][0], des[c][1], des[c][2], des[c][3]);
    MOVE();
    digitalWrite(BOM, 0);
    digitalWrite(NHA, 1);
    delay(30);
    digitalWrite(NHA, 0);
    Invert(des[c][0], des[c][1]+2, des[c][2] + 10, des[c][3]);
    CTAY2(th2, 12);
    CTAY1(th1, 12);
    CTAY3(th3, 12);
    t = 0;
    SV4.write(90);
    Serial.println(4);
    Serial.println(c);
    C[c]++;
  }
}
void Home() {
  th1 = 110;
  th2 = 80;
  th3 = 100;
  SV4.write(90);
  CTAY2(th2, 10);
  CTAY3(th3, 10);
  CTAY1(th1, 10);
}
void CTAY1(int goc, int dly) {
  if (goc > GOC1) {
    for (GOC1; GOC1 < goc; GOC1++) {
      SV1.write(GOC1); delay(dly);
    }
  }
  if (goc < GOC1) {
    for (GOC1; GOC1 > goc; GOC1--) {
      SV1.write(GOC1); delay(dly);
    }
  }
}

void CTAY2(int goc, int dly) {
  if (goc > GOC2) {
    for (GOC2; GOC2 < goc; GOC2++) {
      SV2.write(GOC2); delay(dly);
    }
  }
  if (goc < GOC2) {
    for (GOC2; GOC2 > goc; GOC2--) {
      SV2.write(GOC2); delay(dly);
    }
  }
}

void CTAY3(int goc, int dly) {
  if (goc > GOC3) {
    for (GOC3; GOC3 < goc; GOC3++) {
      SV3.write(GOC3); delay(dly);
    }
  }
  if (goc < GOC3) {
    for (GOC3; GOC3 > goc; GOC3--) {
      SV3.write(GOC3); delay(dly);
    }
  }
}

void unrecognized() {
  Serial.println("Ready");
  return;
}
