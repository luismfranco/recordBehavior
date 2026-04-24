// Run on Teensy 4.0
// https://www.pjrc.com/store/teensy40.html
// IMU --> SparkFun Micro 6DoF IMU Breakout - BMI270
// https://www.sparkfun.com/sparkfun-micro-6dof-imu-breakout-bmi270-qwiic.html
// Adapter --> Flexible Qwiic Cable - Breadboard Jumper (4-pin)
// https://www.sparkfun.com/flexible-qwiic-cable-breadboard-jumper-4-pin.html
//
// IMU adapter cable connections:
//      Blue wire --> Teensy SDA (pin 18)
//      Yellow wire --> Teensy SCL (pin 19)
//      Red wire --> Teensy 3V power
//      Black wire --> Teensy GND
//
// Uses SparkFun BMI270 library:
// https://github.com/sparkfun/SparkFun_BMI270_Arduino_Library
// 
// Adapted for Teensy 4.0 by Luis M. Franco, April 2026
// (Based on orinal code by Dylan Martins written in August 2025)

// Install these libraries on Arduino IDE before uploading this code to Teensy 4.0
// Wire
// SparkFun_BMI270_Arduino_Library

#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"

BMI270 imu;

uint8_t i2cAddress = BMI2_I2C_PRIM_ADDR;

void setup() {

    // Serial.begin(115200);
    Serial.println("BMI270 Example 1 - Basic Readings I2C");

    Wire.begin();

    // Check if sensor is connected and initialize
    while(imu.beginI2C(i2cAddress) != BMI2_OK) {
        Serial.println("Error: BMI270 not connected, check wiring and I2C address!");
        delay(1000);
    }

    Serial.println("BMI270 connected");

}

void loop() {

    imu.getSensorData();

    // Acceleration in g's
    Serial.print(imu.data.accelX, 3);
    Serial.print(",");
    Serial.print(imu.data.accelY, 3);
    Serial.print(",");
    Serial.print(imu.data.accelZ, 3);
    Serial.print(",");

    // Rotation in deg/sec
    Serial.print(imu.data.gyroX, 3);
    Serial.print(",");
    Serial.print(imu.data.gyroY, 3);
    Serial.print(",");
    Serial.println(imu.data.gyroZ, 3);

}