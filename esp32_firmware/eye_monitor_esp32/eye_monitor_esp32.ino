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
 * ALARM BEHAVIOR:
 *   1. Drowsiness Detection (Eyes Closed):
 *      - Buzzer sounds (ACTIVE)
 *      - LED BLINKS rapidly (120ms warning strobe)
 *   2. Normal State (Eyes Open):
 *      - Buzzer is SILENT
 *      - LED is OFF
 *   3. Telemetry:
 *      - Sends "SENSOR,<temp>,<hum>,<pir>" every 2 seconds
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
#define BUZZER_ACTIVE_LOW true

// ------------------------------------------------------------------------------
// Sensor & Timing Constants
// ------------------------------------------------------------------------------
#define DHTTYPE       DHT22  // DHT 22 (AM2302, AM2321)

const unsigned long SENSOR_PUBLISH_INTERVAL_MS = 2000;
unsigned long lastSensorPublishTime = 0;

// LED Blinking Timing during Alarm
const unsigned long LED_BLINK_INTERVAL_MS = 120; // Fast emergency strobe
unsigned long lastLedToggleTime = 0;
bool ledCurrentState = false;

DHT dht(DHTPIN, DHTTYPE);

bool serialAlarmActive = false;
String inputCommandBuffer = "";

void updateActuators(bool alarmOn) {
  if (alarmOn) {
    // Buzzer sounds continuously during drowsiness
    digitalWrite(BUZZER_PIN, BUZZER_ACTIVE_LOW ? LOW : HIGH);

    // LED BLINKS rapidly (Warning Strobe)
    unsigned long now = millis();
    if (now - lastLedToggleTime >= LED_BLINK_INTERVAL_MS) {
      lastLedToggleTime = now;
      ledCurrentState = !ledCurrentState;
      digitalWrite(LED_PIN, ledCurrentState ? HIGH : LOW);
    }
  } else {
    // Alarm OFF: Silence buzzer and turn LED OFF
    digitalWrite(BUZZER_PIN, BUZZER_ACTIVE_LOW ? HIGH : LOW);
    digitalWrite(LED_PIN, LOW);
    ledCurrentState = false;
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIRPIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // Initial state: Everything OFF
  updateActuators(false);

  // Initialize DHT22
  dht.begin();

  // Startup confirmation: 2 short beeps & LED flashes on boot
  for (int i = 0; i < 2; i++) {
    digitalWrite(BUZZER_PIN, BUZZER_ACTIVE_LOW ? LOW : HIGH);
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, BUZZER_ACTIVE_LOW ? HIGH : LOW);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  Serial.println();
  Serial.println("=================================================");
  Serial.println("[ESP32] Smart Eye Monitoring & Drowsiness Node");
  Serial.println("[ESP32] Buzzer: GPIO 26 | LED: GPIO 25 (Blinking)");
  Serial.println("[ESP32] PIR: GPIO 27 | DHT22: GPIO 4");
  Serial.println("=================================================");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Process incoming commands from Python via USB Serial
  handleSerialInput();

  // 2. Read physical PIR motion sensor
  int pirState = digitalRead(PIRPIN);

  // 3. Update Actuators based on Drowsiness Alarm from Python
  updateActuators(serialAlarmActive);

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
    Serial.println("[ACK] BUZZER_STATE:ON");
  } else if (cmd.equalsIgnoreCase("BUZZER:OFF")) {
    serialAlarmActive = false;
    updateActuators(false);
    Serial.println("[ACK] BUZZER_STATE:OFF");
  } else if (cmd.equalsIgnoreCase("PING")) {
    Serial.println("PONG");
  } else if (cmd.equalsIgnoreCase("STATUS")) {
    Serial.print("[STATUS] Alarm:");
    Serial.print(serialAlarmActive ? "ON" : "OFF");
    Serial.println();
  }
}

void publishSensorData(int pirState) {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  String packet = "SENSOR,";

  if (isnan(temperature)) {
    packet += "NAN,";
  } else {
    packet += String(temperature, 1) + ",";
  }

  if (isnan(humidity)) {
    packet += "NAN,";
  } else {
    packet += String(humidity, 1) + ",";
  }

  packet += String(pirState);

  Serial.println(packet);
}
