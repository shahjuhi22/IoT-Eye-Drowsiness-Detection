/*
 * ==============================================================================
 * IoT-Based Smart Eye Monitoring and Drowsiness Detection System
 * ESP32 Sensor Telemetry & Alarm Actuation Firmware
 * ==============================================================================
 * Target Board: ESP32 Dev Module / NodeMCU-32S (USB-C)
 * Baud Rate:    115200
 * 
 * Pins:
 *   - DHT22 (Temperature & Humidity) on GPIO 4
 *   - PIR Motion Sensor on GPIO 27
 *   - Active Buzzer on GPIO 26
 *   - Status / Warning LED on GPIO 25
 * 
 * HARDCODED BUZZER FEATURES:
 *   1. Startup audible self-test: 3 distinct beeps on boot.
 *   2. Hardware Trigger: Buzzer & LED automatically sound/flash whenever PIR detects motion!
 *   3. Software Command: Buzzer & LED sound when Python sends "BUZZER:ON" (drowsiness alarm).
 * ==============================================================================
 */

#include "DHT.h"

// ------------------------------------------------------------------------------
// Pin Definitions (ESP32 GPIO numbers)
// ------------------------------------------------------------------------------
#define DHTPIN        4      // GPIO 4 for DHT22 Data line
#define PIRPIN        27     // GPIO 27 for PIR Motion Sensor digital output
#define BUZZER_PIN    26     // GPIO 26 for Active Buzzer signal
#define LED_PIN       25     // GPIO 25 for Alert / Status LED

// Set to true if using an inverted / Active-LOW buzzer module (KY-012)
#define BUZZER_ACTIVE_LOW false

// ------------------------------------------------------------------------------
// Sensor & Timing Constants
// ------------------------------------------------------------------------------
#define DHTTYPE       DHT22  // DHT 22 (AM2302, AM2321)

const unsigned long SENSOR_PUBLISH_INTERVAL_MS = 2000;
unsigned long lastSensorPublishTime = 0;

DHT dht(DHTPIN, DHTTYPE);

bool serialAlarmActive = false;
String inputCommandBuffer = "";

void setHardwareAlarm(bool enable) {
  if (enable) {
    digitalWrite(BUZZER_PIN, BUZZER_ACTIVE_LOW ? LOW : HIGH);
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, BUZZER_ACTIVE_LOW ? HIGH : LOW);
    digitalWrite(LED_PIN, LOW);
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIRPIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // Initial OFF state
  setHardwareAlarm(false);

  // Initialize DHT22
  dht.begin();

  // HARDCODED STARTUP TEST: 3 loud, clear confirmation beeps on boot
  for (int i = 0; i < 3; i++) {
    setHardwareAlarm(true);
    delay(120);
    setHardwareAlarm(false);
    delay(100);
  }

  Serial.println();
  Serial.println("=================================================");
  Serial.println("[ESP32] Smart Eye Monitoring & Drowsiness Node");
  Serial.println("[ESP32] Hardcoded Buzzer & LED Test Initialized");
  Serial.println("[ESP32] Buzzer: GPIO 26 | LED: GPIO 25 | PIR: GPIO 27");
  Serial.println("=================================================");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Process incoming commands from Python via USB Serial
  handleSerialInput();

  // 2. Read physical PIR motion sensor
  int pirState = digitalRead(PIRPIN);

  // 3. HARDCODED BUZZER ACTIVATION LOGIC:
  //    Buzzer turns ON if:
  //    - Python sent a Drowsiness Alarm ("BUZZER:ON"), OR
  //    - PIR sensor detects motion (hardware fallback)
  if (serialAlarmActive || pirState == HIGH) {
    setHardwareAlarm(true);
  } else {
    setHardwareAlarm(false);
  }

  // 4. Publish telemetry packet every 2 seconds
  if (currentMillis - lastSensorPublishTime >= SENSOR_PUBLISH_INTERVAL_MS) {
    lastSensorPublishTime = currentMillis;
    publishSensorData(pirState);
  }
}

void handleSerialInput() {
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();

    if (inChar == '\n' || inChar == '\r') {
      inputCommandBuffer.trim();
      if (inputCommandBuffer.length() > 0) {
        processCommand(inputCommandBuffer);
      }
      inputCommandBuffer = "";
    } else {
      if (inputCommandBuffer.length() < 64) {
        inputCommandBuffer += inChar;
      }
    }
  }
}

void processCommand(const String& cmd) {
  if (cmd.equalsIgnoreCase("BUZZER:ON")) {
    serialAlarmActive = true;
    setHardwareAlarm(true);
    Serial.println("[ACK] BUZZER_STATE:ON");
  } else if (cmd.equalsIgnoreCase("BUZZER:OFF")) {
    serialAlarmActive = false;
    setHardwareAlarm(false);
    Serial.println("[ACK] BUZZER_STATE:OFF");
  } else if (cmd.equalsIgnoreCase("PING")) {
    Serial.println("PONG");
  } else if (cmd.equalsIgnoreCase("STATUS")) {
    Serial.print("[STATUS] Alarm:");
    Serial.print(serialAlarmActive ? "ON" : "OFF");
    Serial.print(" PIR:");
    Serial.println(digitalRead(PIRPIN));
  } else {
    Serial.print("[ERR] UNKNOWN_COMMAND: ");
    Serial.println(cmd);
  }
}

void publishSensorData(int pirState) {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  Serial.print("SENSOR,");

  if (isnan(temperature)) {
    Serial.print("NAN,");
  } else {
    Serial.print(temperature, 1);
    Serial.print(",");
  }

  if (isnan(humidity)) {
    Serial.print("NAN,");
  } else {
    Serial.print(humidity, 1);
    Serial.print(",");
  }

  Serial.println(pirState);
}
