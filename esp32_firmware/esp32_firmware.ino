/*
 * ==============================================================================
 * IoT-Based Smart Eye Monitoring and Drowsiness Detection System
 * ESP32 Sensor Telemetry & Alarm Actuation Firmware
 * ==============================================================================
 * Target Board: ESP32 Dev Module / NodeMCU-32S (USB-C)
 * Baud Rate:    115200
 * 
 * Sensors:
 *   - DHT22 (Temperature & Humidity) on GPIO 4
 *   - PIR Motion Sensor on GPIO 27
 * 
 * Actuators:
 *   - Active Buzzer on GPIO 26 (Direct or Transistor-driven)
 *   - Status / Warning LED on GPIO 25 (with 220-330 ohm resistor)
 * 
 * Serial Protocol:
 *   - ESP32 -> Laptop: SENSOR,<temp_c>,<humidity_pct>,<pir_state>
 *     Example: SENSOR,26.4,58.2,1
 *   - Laptop -> ESP32: BUZZER:ON
 *   - Laptop -> ESP32: BUZZER:OFF
 *   - Laptop -> ESP32: PING  (Replies: PONG)
 * 
 * Note: Non-blocking execution using millis(). No delay() in loop!
 * ==============================================================================
 */

#include "DHT.h"

// ------------------------------------------------------------------------------
// Pin Definitions (ESP32 GPIO numbers, NOT Arduino Uno pins!)
// ------------------------------------------------------------------------------
#define DHTPIN        4      // GPIO 4 for DHT22 Data line
#define PIRPIN        27     // GPIO 27 for PIR Motion Sensor digital output
#define BUZZER_PIN    26     // GPIO 26 for Active Buzzer signal
#define LED_PIN       25     // GPIO 25 for Alert / Status LED

// ------------------------------------------------------------------------------
// Sensor & Timing Constants
// ------------------------------------------------------------------------------
#define DHTTYPE       DHT22  // DHT 22 (AM2302, AM2321)

// DHT22 requires at least 2000ms between physical read cycles
const unsigned long SENSOR_PUBLISH_INTERVAL_MS = 2000;
unsigned long lastSensorPublishTime = 0;

// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE);

// System state tracking
bool buzzerActive = false;
int lastPirState = -1;
String inputCommandBuffer = "";

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial && millis() < 2000) {
    // Wait briefly for serial port to open
  }

  // Configure GPIO directions
  pinMode(PIRPIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // Ensure actuators start in OFF state
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  // Initialize DHT22
  dht.begin();

  // Startup visual / audible confirmation (quick double beep & blink)
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
    delay(70);
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    delay(70);
  }

  Serial.println();
  Serial.println("=================================================");
  Serial.println("[ESP32] Smart Eye Monitoring & Drowsiness Node");
  Serial.println("[ESP32] Firmware Initialized Successfully");
  Serial.println("[ESP32] Baud Rate: 115200 | DHT22: GPIO4 | PIR: GPIO27");
  Serial.println("[ESP32] Actuators: Buzzer: GPIO26 | LED: GPIO25");
  Serial.println("=================================================");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Process incoming commands from Python via USB Serial (Immediate response)
  handleSerialInput();

  // 2. Read sensors and publish telemetry packet at non-blocking intervals
  if (currentMillis - lastSensorPublishTime >= SENSOR_PUBLISH_INTERVAL_MS) {
    lastSensorPublishTime = currentMillis;
    publishSensorData();
  }
}

/**
 * Reads incoming characters from serial, buffers into line, and parses commands.
 */
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
      // Buffer incoming character (prevent buffer overflow)
      if (inputCommandBuffer.length() < 64) {
        inputCommandBuffer += inChar;
      }
    }
  }
}

/**
 * Executes recognized commands sent by Python application.
 */
void processCommand(const String& cmd) {
  if (cmd.equalsIgnoreCase("BUZZER:ON")) {
    setAlarm(true);
    Serial.println("[ACK] BUZZER_STATE:ON");
  } else if (cmd.equalsIgnoreCase("BUZZER:OFF")) {
    setAlarm(false);
    Serial.println("[ACK] BUZZER_STATE:OFF");
  } else if (cmd.equalsIgnoreCase("PING")) {
    Serial.println("PONG");
  } else if (cmd.equalsIgnoreCase("STATUS")) {
    Serial.print("[STATUS] Buzzer:");
    Serial.print(buzzerActive ? "ON" : "OFF");
    Serial.print(" PIR:");
    Serial.println(digitalRead(PIRPIN));
  } else {
    Serial.print("[ERR] UNKNOWN_COMMAND: ");
    Serial.println(cmd);
  }
}

/**
 * Activates or deactivates the buzzer and visual warning LED.
 */
void setAlarm(bool enable) {
  buzzerActive = enable;
  if (enable) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
  }
}

/**
 * Reads DHT22 and PIR, validates values, and outputs CSV formatted telemetry:
 * "SENSOR,<temp>,<hum>,<pir>"
 */
void publishSensorData() {
  // Read humidity (%) and temperature (Celsius)
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Read PIR digital motion state (0 = No motion, 1 = Motion detected)
  int pirState = digitalRead(PIRPIN);

  // Format and publish telemetry string
  // If sensor read fails (NaN), output "NAN" so Python parser handles gracefully
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
