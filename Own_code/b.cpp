#include "BluetoothSerial.h"
#include <ESP32Servo.h>

BluetoothSerial SerialBT;
Servo myServo;

int servoPin = 13;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_SERVO");
  myServo.attach(servoPin);
  myServo.write(0);
  Serial.println("Bluetooth ready. Pair with ESP32_SERVO");
}

void loop() {
  if (SerialBT.available()) {
    char cmd = SerialBT.read();

    if (cmd == 'O') {
      myServo.write(15);
      SerialBT.println("Servo Opened");
    }
    else if (cmd == 'C') {
      myServo.write(0);
      SerialBT.println("Servo Closed");
    }
  }
}


