# IoT-Based Smart Eye Monitoring and Drowsiness Detection System

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-FaceMesh-orange.svg)](https://developers.google.com/mediapipe)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32%20DevKit-red.svg)](https://www.espressif.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An end-to-end edge Internet of Things (IoT) project designed for driver alertness monitoring and fatigue prevention. The system combines real-time facial landmark analysis via computer vision with ambient environmental telemetry from an ESP32 microcontroller node equipped with a **DHT22** temperature/humidity sensor, a **PIR** motion sensor, and an **active buzzer** alarm.

---

## Table of Contents
1. [Project Introduction](#1-project-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Objectives](#3-objectives)
4. [Components Required](#4-components-required)
5. [Software Requirements](#5-software-requirements)
6. [System Architecture](#6-system-architecture)
7. [How Eye Detection Works](#7-how-eye-detection-works)
8. [Eye Aspect Ratio (EAR) Mathematical Formulation](#8-eye-aspect-ratio-ear-mathematical-formulation)
9. [How the DHT22 Sensor Works](#9-how-the-dht22-sensor-works)
10. [How the PIR Motion Sensor Works](#10-how-the-pir-motion-sensor-works)
11. [ESP32 Serial Communication Protocol](#11-esp32-serial-communication-protocol)
12. [Hardware Wiring Diagram & Pin Assignment](#12-hardware-wiring-diagram--pin-assignment)
13. [Installation Steps (Windows 11)](#13-installation-steps-windows-11)
14. [ESP32 Firmware Upload Guide (Arduino IDE)](#14-esp32-firmware-upload-guide-arduino-ide)
15. [Python Execution Steps](#15-python-execution-steps)
16. [Expected Output & Hotkeys](#16-expected-output--hotkeys)
17. [Troubleshooting Guide](#17-troubleshooting-guide)
18. [Project Limitations](#18-project-limitations)
19. [Future Enhancements](#19-future-enhancements)

---

## 1. Project Introduction

Driver drowsiness and micro-sleep episodes are leading contributors to highway road accidents worldwide. Prolonged driving without breaks, lack of adequate ventilation, and high cabin temperature induce physiological fatigue, causing drivers to close their eyes for critical seconds without realizing it.

This project delivers a **hybrid Edge IoT solution**:
- **Computer Vision Tier**: A host machine (laptop/PC) utilizes an onboard or USB webcam to detect faces, track eyelids, and compute Eye Aspect Ratio (EAR) in real-time.
- **Microcontroller Tier**: A normal ESP32 development board (USB-C) continuously samples cabin temperature and relative humidity via a **DHT22** sensor and tracks driver motion using a **PIR** sensor.
- **Closed-Loop Actuation**: When continuous eye closure exceeds **1.75 seconds**, the laptop signals the ESP32 via USB Serial to trigger an immediate, high-priority **audible buzzer alarm** and visual LED strobe, waking the driver.

---

## 2. Problem Statement

Commercial automotive driver monitoring systems (DMS) are expensive, proprietary, and inaccessible to students and aftermarket retrofitters. Existing hobbyist projects often rely solely on basic thresholding or assume a specialized camera-equipped microcontroller (such as an ESP32-CAM) with low frame rates and inadequate computational power.

There is a need for a practical, low-cost mini project architecture that offloads heavy computer vision algorithms to an edge computer (laptop) while relying on a standard ESP32 development board for multi-sensor environmental acquisition and low-latency hardware actuation.

---

## 3. Objectives

- **Real-Time Facial Landmark Tracking**: Accurately isolate left and right eye contours from 30 FPS video frames using MediaPipe Face Mesh.
- **Mathematical EAR Estimation**: Implement the landmark-based Eye Aspect Ratio to distinguish between spontaneous natural blinks and hazardous micro-sleeps.
- **Timestamp-Based State Machine**: Rely on high-precision wall-clock timestamps (`time.perf_counter`) rather than assumed frame rates to eliminate timing drift under varying CPU loads.
- **Environmental Telemetry**: Monitor cabin temperature and humidity with a DHT22 sensor to identify environmental conditions (e.g. $T > 35^\circ\text{C}$ or stuffy air) that trigger drowsiness.
- **Motion Verification**: Utilize a PIR sensor to detect driver stillness or restlessness.
- **Robust Serial Bridge**: Implement a non-blocking full-duplex protocol over USB UART with automatic COM port discovery and seamless software simulation fallback.
- **Interactive Visualizations**: Provide both an OpenCV Heads-Up Display (HUD) overlay and a Streamlit web control panel with real-time trend analytics.

---

## 4. Components Required

### Hardware Available & Used
| S.No. | Component | Specification / Notes |
|---|---|---|
| 1 | **ESP32 Dev Module** | 30-pin / 38-pin NodeMCU-32S with USB-C connector (Dual Core 240MHz, 3.3V logic) |
| 2 | **DHT22 Sensor** | AM2302 digital temperature & humidity sensor (3-pin module or 4-pin bare) |
| 3 | **PIR Motion Sensor** | HC-SR501 passive infrared motion detector (5V VIN, 3.3V digital output) |
| 4 | **Active Buzzer** | 3.3V - 5V continuous tone piezoceramic buzzer |
| 5 | **Status LED** | 5mm Red or Yellow LED (Visual warning strobe) |
| 6 | **Current-Limiting Resistor** | 220$\Omega$ to 330$\Omega$ (0.25W) for LED; 1k$\Omega$ for optional buzzer transistor |
| 7 | **Pull-up Resistor** | 10k$\Omega$ (Required only if using a bare 4-pin DHT22 without onboard pull-up) |
| 8 | **Solderless Breadboard** | Standard 400-point or 830-point half-size breadboard |
| 9 | **Jumper Wires** | Male-to-Male (M-M) and Male-to-Female (M-F) DuPont wires |
| 10 | **USB-C Cable** | Data + Power synchronization cable connecting ESP32 to laptop |
| 11 | **Webcam** | Laptop integrated HD webcam or external USB camera |

> **Note regarding ESP32 vs ESP32-CAM**:  
> The ESP32 board used here is a standard general-purpose ESP32 development board, **not** an ESP32-CAM. Therefore, camera processing executes entirely on the laptop, and the ESP32 acts as the sensor hub and alarm actuator via USB serial communication.

---

## 5. Software Requirements

- **Operating System**: Windows 10 / Windows 11 (64-bit)
- **Python**: Python 3.11 (Recommended for native MediaPipe wheel compatibility)
- **Arduino IDE**: Version 2.0 or higher
- **Arduino Libraries**:
  - `DHT sensor library` by Adafruit (v1.4.6+)
  - `Adafruit Unified Sensor` by Adafruit (v1.1.14+)
  - ESP32 Board Core by Espressif (`esp32` v2.0.14+)
- **Python Dependencies**:
  - `opencv-python>=4.8.0`
  - `mediapipe>=0.10.14`
  - `pyserial>=3.5`
  - `streamlit>=1.30.0`
  - `numpy>=1.24.0`
  - `matplotlib>=3.7.0`
  - `pandas>=2.0.0`
  - `scipy>=1.11.0`

---

## 6. System Architecture

The project is structured into three decoupled layers:

```
[ Laptop Webcam ] ──> [ OpenCV Frame Capture ] ──> [ MediaPipe Face Mesh ]
                                                           │
                                                           ▼
                                               [ EAR Mathematical Engine ]
                                                           │
                                                           ▼
                                               [ Drowsiness State Machine ]
                                               (Normal / Warning / Drowsy)
                                                           │
                                                           ▼
[ Streamlit Dashboard / HUD ] <────────────── [ Alert Manager ]
                                                           │
                                                           │ USB Serial (115200 Baud)
                                                           ▼
                                                [ ESP32 Microcontroller ]
                                               ┌───────────┼───────────┐
                                               ▼           ▼           ▼
                                            [DHT22]      [PIR]     [Buzzer & LED]
```

Visual diagram:  
See `diagrams/system_architecture.png` and `diagrams/project_flowchart.png`.

---

## 7. How Eye Detection Works

1. **Face Mesh Extraction**: The input video frame ($640 \times 480$ pixels) is converted from BGR to RGB and passed to MediaPipe Face Mesh, generating 468 3D facial coordinate landmarks.
2. **Eye Contour Isolation**: The system isolates the 6 canonical landmarks describing the aperture of each eye:
   - **Left Eye Indices**: $P_1=33, P_2=160, P_3=158, P_4=133, P_5=153, P_6=144$
   - **Right Eye Indices**: $P_1=362, P_2=385, P_3=387, P_4=263, P_5=373, P_6=380$
3. **EAR Computation**: The vertical eyelid distances are compared against the horizontal width of the eye.
4. **State Machine Evaluation**:
   - $\text{EAR} \ge \text{Threshold}$ ($0.22$): Eyes are **OPEN** (Green).
   - $\text{EAR} < \text{Threshold}$ for $0.08\text{s} \le \Delta t \le 0.40\text{s}$: Natural **BLINK** registered; blink counter increments.
   - $\text{EAR} < \text{Threshold}$ for $\Delta t \ge 1.00\text{s}$: **WARNING** displayed on screen (Orange).
   - $\text{EAR} < \text{Threshold}$ for $\Delta t \ge 1.75\text{s}$: **DROWSINESS ALARM** triggered (Red); buzzer sounds.

---

## 8. Eye Aspect Ratio (EAR) Mathematical Formulation

Introduced by Tereza Soukupová and Jan Čech (2016), the Eye Aspect Ratio (EAR) provides a scalar metric measuring eye openness that is invariant to uniform scaling and in-plane head rotation:

$$\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \cdot \|p_1 - p_4\|}$$

Where:
- $p_1$ and $p_4$ are the 2D Cartesian coordinates of the outer and inner eye corners (lateral and medial canthi).
- $p_2, p_6$ and $p_3, p_5$ are vertical pairs of coordinates located along the upper and lower eyelid boundaries.
- $\|\cdot\|$ denotes the L2 Euclidean norm:
  $$\|p_a - p_b\| = \sqrt{(x_a - x_b)^2 + (y_a - y_b)^2}$$

### Why EAR is Scale-Invariant:
As a driver moves closer to or further from the camera, all distances expand or contract proportionally. Because the vertical distances in the numerator are divided by the horizontal length $\|p_1 - p_4\|$ in the denominator, the distance factor cancels out, keeping the EAR value remarkably constant.

- **Typical Open Eye EAR**: $0.26 \sim 0.38$
- **Typical Closed Eye EAR**: $0.05 \sim 0.18$

---

## 9. How the DHT22 Sensor Works

The DHT22 (AM2302) is a digital composite sensor containing:
1. A **capacitive humidity sensor**: A moisture-holding dielectric polymer film sandwiched between two electrodes. As relative humidity changes, the dielectric constant and capacitance vary proportionally.
2. An **NTC thermistor**: A negative temperature coefficient ceramic resistor whose electrical resistance decreases predictably as temperature increases.
3. An internal 8-bit microcontroller that computes analog-to-digital conversion, applies factory calibration coefficients, and transmits a single-wire digital signal.

**Measurement Specifications**:
- Temperature Range: $-40^\circ\text{C}$ to $+80^\circ\text{C}$ ($\pm 0.5^\circ\text{C}$ accuracy)
- Humidity Range: $0\%$ to $100\%$ RH ($\pm 2\%$ accuracy)
- Sampling Rate: Max $0.5\text{ Hz}$ (Requires at least $2.0\text{ seconds}$ between reads).

---

## 10. How the PIR Motion Sensor Works

The HC-SR501 Passive Infrared (PIR) sensor detects shifts in ambient thermal radiation:
1. **Pyroelectric Element**: Contains two radiation-sensitive crystalline slots. In idle conditions, both slots receive equal ambient thermal infrared ($\sim 10\,\mu\text{m}$).
2. **Differential Detection**: When a warm human body moves across the detection zone, one half intercepts the radiation first, creating a positive differential pulse $\Delta V$, followed by a negative differential pulse as the body leaves.
3. **Fresnel Lens**: Splits the field of view into discrete conical beam sectors, maximizing sensitivity to lateral motion.
4. **Output Voltage**: Powered by $5\text{V}$ VIN (required by onboard 3.3V LDO regulator), but the digital `OUT` signal pin produces **$3.3\text{V}$ logic levels**, making it directly safe for ESP32 GPIO pins!

---

## 11. ESP32 Serial Communication Protocol

- **Physical Layer**: USB-UART Bridge (Silicon Labs CP2102 / WCH CH340 / FTDI)
- **Baud Rate**: `115200` bps
- **Data Format**: 8 Data bits, No Parity, 1 Stop bit (8-N-1)

### Packet Formats

#### 1. Sensor Telemetry (ESP32 $\to$ Laptop)
Sent every 2.0 seconds (non-blocking):
```text
SENSOR,<temperature_celsius>,<humidity_percent>,<pir_state>
```
*Examples*:
- `SENSOR,26.4,58.2,1` (Valid read: $26.4^\circ\text{C}$, $58.2\%$ humidity, motion detected)
- `SENSOR,NAN,NAN,0` (Fault tolerant: DHT22 disconnected, motion 0)

#### 2. Actuator Commands (Laptop $\to$ ESP32)
Sent **strictly on state transitions** (never spamming frames):
- `BUZZER:ON\n` $\implies$ Enables active buzzer and warning LED.
- `BUZZER:OFF\n` $\implies$ Disables active buzzer and LED.
- `PING\n` $\implies$ ESP32 responds with `PONG\n`.

---

## 12. Hardware Wiring Diagram & Pin Assignment

### Connection Pinout Table
| Peripheral Module | Module Pin | ESP32 GPIO | Electrical Specification / Wire Color |
|---|---|---|---|
| **DHT22 Sensor** | VCC | **3.3V** | Red Wire (Power) |
| **DHT22 Sensor** | DATA | **GPIO 4** | Green Wire (Pull-up with 10k$\Omega$ to 3.3V if bare sensor) |
| **DHT22 Sensor** | GND | **GND** | Grey/Black Wire (Common Ground) |
| **PIR (HC-SR501)** | VCC | **VIN (5V)** | Orange Wire (Requires 5V input to feed onboard LDO) |
| **PIR (HC-SR501)** | OUT | **GPIO 27** | Yellow Wire ($3.3\text{V}$ TTL Output Logic) |
| **PIR (HC-SR501)** | GND | **GND** | Grey/Black Wire (Common Ground) |
| **Active Buzzer** | Signal (+) | **GPIO 26** | Cyan Wire (Direct 3-pin module or via 2N2222 transistor) |
| **Active Buzzer** | GND (-) | **GND** | Grey/Black Wire (Common Ground) |
| **Alert LED** | Anode (+) | **GPIO 25** | Purple Wire (Through 220$\Omega$ - 330$\Omega$ resistor) |
| **Alert LED** | Cathode (-) | **GND** | Grey/Black Wire (Common Ground) |

> [!IMPORTANT]
> **Electrical Safety Rules**:
> 1. Never connect a $5\text{V}$ output signal directly to an ESP32 GPIO. The HC-SR501 output is confirmed $3.3\text{V}$ logic despite receiving $5\text{V}$ VIN.
> 2. All modules must share a **common ground** (GND rail on the breadboard connected to ESP32 GND).
> 3. If using a bare active buzzer drawing $>12\text{mA}$, drive it via an NPN transistor (2N2222 or BC547) with a $1\text{k}\Omega$ base resistor from GPIO 26. If using a standard 3-pin buzzer sensor module with onboard transistor, wire directly to GPIO 26.

Refer to the visual schematic in `diagrams/esp32_wiring.png`.

---

## 13. Installation Steps (Windows 11)

### Quick Automated Installation
1. Open this project directory in Windows Explorer:
   ```cmd
   cd "c:\Users\shahj\OneDrive\Desktop\ml\iot project"
   ```
2. Double-click `setup.bat` or run in terminal:
   ```cmd
   setup.bat
   ```
   The script automatically detects Python 3.11, initializes the `.venv`, installs dependencies, and runs hardware diagnostics.

---

## 14. ESP32 Firmware Upload Guide (Arduino IDE)

1. Connect your ESP32 board to your laptop using a **USB Type-C data cable**.
2. Launch **Arduino IDE**.
3. In Arduino IDE, navigate to **File $\to$ Open...** and select:
   `iot project/esp32_firmware/eye_monitor_esp32.ino`
4. If ESP32 board support is not yet installed:
   - Go to **File $\to$ Preferences**, add to *Additional Boards Manager URLs*:
     ```text
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to **Tools $\to$ Board $\to$ Boards Manager**, search for `esp32` by Espressif and click **Install**.
5. Install required libraries:
   - Go to **Sketch $\to$ Include Library $\to$ Manage Libraries...**
   - Search for `DHT sensor library` by Adafruit $\to$ Install (select "Install All Dependencies" to include `Adafruit Unified Sensor`).
6. Select Board and Port:
   - **Tools $\to$ Board $\to$ esp32 $\to$ ESP32 Dev Module**
   - **Tools $\to$ Port $\to$ COMx** (Select the COM port corresponding to your USB-UART bridge, e.g., COM3, COM4).
7. Click the **Upload** button ($\rightarrow$).
   *(If upload hangs on "Connecting......._____", press and hold the `BOOT` button on your ESP32 until flashing starts).*
8. Open **Serial Monitor** at `115200 baud` to verify startup confirmation. Close Serial Monitor before starting the Python app.

---

## 15. Python Execution Steps

Launch via the menu:
```cmd
run.bat
```

Or execute commands directly:

### Option A: Desktop Monitor (OpenCV Live HUD)
```cmd
python main.py
```
*Run with explicit COM port*:
```cmd
python main.py --port COM3
```
*Run in Simulation Mode (No hardware connected)*:
```cmd
python main.py --simulate
```

### Option B: Interactive Web Dashboard (Streamlit)
```cmd
streamlit run dashboard/dashboard.py
```

### Option C: Run Diagnostics
```cmd
python test_serial.py
python test_camera.py
python -m unittest discover tests -v
```

---

## 16. Expected Output & Hotkeys

### Interactive Hotkeys in OpenCV Window:
- `Q` or `ESC`: Exit cleanly and turn off buzzer.
- `C`: Recalibrate baseline open-eye EAR to adjust for user eye geometry.
- `S`: Toggle between physical serial connection and software simulation mode.
- `B`: Test manual buzzer trigger (sound on/off).
- `R`: Reset blink counter and alert metrics.
- `H`: Print hotkey guide to console.

### Expected Telemetry Logging:
Snapshots are continuously appended to `data/logs/eye_monitoring_log.csv` and events are logged to `data/logs/system_events.log`.

---

## 17. Troubleshooting Guide

| Issue | Root Cause | Solution |
|---|---|---|
| `Cannot open camera index 0` | Webcam in use by Teams, Zoom, or browser | Close other camera apps; try `python main.py --camera 1`. |
| `pyserial: could not open port COMx` | Port open in Arduino Serial Monitor | Close Arduino IDE Serial Monitor before running Python. |
| `DHT22 returns SENSOR,NAN,NAN` | Loose DATA pin or missing pull-up | Check GPIO 4 connection; add 10k$\Omega$ resistor between 3.3V and DATA. |
| `Buzzer does not sound` | Inverted polarity or insufficient current | Ensure buzzer (+) connects to GPIO 26/3.3V; test via Option B (`test_serial.py`). |
| `High false positive drowsiness` | Threshold too high for smaller eyes | Press `C` to recalibrate or pass `--threshold 0.19`. |
| `MediaPipe import error on Python 3.13` | Wheels not built for 3.13 | Use installed Python 3.11 (`setup.bat` automatically handles this). |

---

## 18. Project Limitations

1. **Illumination Sensitivity**: Standard RGB webcams struggle in total darkness. In a commercial vehicle, an active Near-Infrared (NIR) camera with IR illuminators is required.
2. **Extreme Head Poses**: If the driver turns their head $>60^\circ$ away from the camera, 2D facial landmarks lose precision.
3. **Eyewear Obstruction**: Thick tinted sunglasses prevent optical detection of pupil and eyelid landmarks.

---

## 19. Future Enhancements

- **Yawn Detection**: Add Mouth Aspect Ratio (MAR) to detect early-stage fatigue before eye closure occurs.
- **Head Nodding Detection**: Integrate 3D SolvePnP head pose estimation (Pitch, Yaw, Roll) to recognize sudden head drops.
- **NIR Night Vision Camera**: Replace standard webcam with an infrared USB camera module for nighttime driving.
- **Cloud Fleet Telemetry**: Publish telemetry via MQTT to AWS IoT Core or ThingsBoard for centralized transport fleet monitoring.
