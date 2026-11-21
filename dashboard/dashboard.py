"""
dashboard.py — Interactive Streamlit Dashboard for IoT Eye Monitoring
=====================================================================
A modern, web-based control panel and monitoring dashboard for the
IoT-Based Smart Eye Monitoring & Drowsiness Detection System.

Features:
  - Live video stream display with facial mesh and eye contour annotations
  - Real-time KPI indicator cards (Eye Status, EAR, Drowsiness, Blinks, Alarm)
  - ESP32 hardware telemetry gauges (Temperature, Humidity, PIR Motion)
  - Historical trend charts (EAR variations, Environmental telemetry)
  - Dedicated Simulation Mode when hardware/camera is not connected
  - Educational reference tab with mathematical EAR formulas and wiring guide
"""

import sys
import os
import time
from pathlib import Path
import numpy as np
import cv2
import pandas as pd
import streamlit as st

# Ensure project root is available for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.ear_calculator import calculate_ear, calculate_eyes_ear
from src.eye_detector import EyeDetector
from src.drowsiness_detector import DrowsinessDetector, DrowsinessState
from src.serial_communication import ESP32SerialBridge
from src.sensor_manager import SensorManager
from src.alert_manager import AlertManager


# -----------------------------------------------------------------------------
# Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IoT Smart Eye & Drowsiness Monitor",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .status-badge-green {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-badge-red {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-badge-orange {
        background-color: #FEF08A;
        color: #854D0E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-card {
        border-radius: 8px;
        padding: 16px;
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Global / Cached Session State Initialization
# -----------------------------------------------------------------------------
if "sensor_mgr" not in st.session_state:
    st.session_state.sensor_mgr = SensorManager(history_maxlen=60)

if "serial_bridge" not in st.session_state:
    st.session_state.serial_bridge = ESP32SerialBridge(
        port=config.SERIAL_PORT,
        on_telemetry_received=st.session_state.sensor_mgr.update_from_dict
    )
    st.session_state.serial_bridge.connect()
    st.session_state.serial_bridge.start()

if "alert_mgr" not in st.session_state:
    st.session_state.alert_mgr = AlertManager(serial_bridge=st.session_state.serial_bridge)

if "eye_detector" not in st.session_state:
    st.session_state.eye_detector = EyeDetector()

if "drowsiness_detector" not in st.session_state:
    st.session_state.drowsiness_detector = DrowsinessDetector(
        ear_threshold=config.DEFAULT_EAR_THRESHOLD,
        warning_duration=config.WARNING_DURATION_SEC,
        drowsy_duration=config.DROWSY_DURATION_SEC,
        calibration_enabled=False  # Use manual or direct slider in dashboard
    )

if "ear_history" not in st.session_state:
    st.session_state.ear_history = []


# -----------------------------------------------------------------------------
# Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/visible.png", width=64)
    st.title("System Controls")

    # Operating Mode
    op_mode = st.radio(
        "Operating Mode",
        ["Live Webcam + IoT Telemetry", "Pure Simulation Mode"],
        index=0
    )

    st.markdown("---")
    st.subheader("Threshold Adjustments")

    ear_slider = st.slider(
        "EAR Closure Threshold",
        min_value=0.15,
        max_value=0.35,
        value=float(config.DEFAULT_EAR_THRESHOLD),
        step=0.01,
        help="Eyes with EAR below this value are considered CLOSED."
    )
    st.session_state.drowsiness_detector.effective_ear_threshold = ear_slider

    drowsy_slider = st.slider(
        "Drowsy Alarm Duration (s)",
        min_value=0.8,
        max_value=3.5,
        value=float(config.DROWSY_DURATION_SEC),
        step=0.1,
        help="Continuous eye closure duration required to trigger buzzer alert."
    )
    st.session_state.drowsiness_detector.drowsy_duration = drowsy_slider

    st.markdown("---")
    st.subheader("Hardware & Actuator Test")

    # Test Buzzer Button
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🔔 Buzzer ON", use_container_width=True):
            st.session_state.serial_bridge.send_command("BUZZER:ON")
            st.session_state.alert_mgr.log_event("Manual dashboard Buzzer ON triggered.")
    with col_b2:
        if st.button("🔕 Buzzer OFF", use_container_width=True):
            st.session_state.serial_bridge.send_command("BUZZER:OFF")
            st.session_state.alert_mgr.log_event("Manual dashboard Buzzer OFF triggered.")

    if st.button("🔄 Reset Blink Counter", use_container_width=True):
        st.session_state.drowsiness_detector.blink_count = 0
        st.session_state.drowsiness_detector.drowsy_event_count = 0
        st.success("Counters reset.")

    st.markdown("---")
    # Port info
    avail_ports = ESP32SerialBridge.list_available_ports()
    st.caption(f"Detected Ports: {', '.join(avail_ports) if avail_ports else 'None'}")
    is_conn = st.session_state.serial_bridge.is_connected
    is_sim = st.session_state.serial_bridge.simulation_mode

    if is_conn:
        st.success(f"ESP32 Connected: {st.session_state.serial_bridge.serial_conn.port}")
    elif is_sim:
        st.info("Simulation Mode Active")
    else:
        st.warning("ESP32 Offline")


# -----------------------------------------------------------------------------
# Main Dashboard UI Layout
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">IoT Eye Monitoring & Drowsiness Detection System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Edge Computer Vision (EAR) paired with ESP32 Environmental & Motion Telemetry</div>', unsafe_allow_html=True)

# Tabs
tab_monitor, tab_charts, tab_docs = st.tabs(["📊 Live Monitoring", "📈 Real-Time Charts", "📘 Project Guide & Architecture"])

# -----------------------------------------------------------------------------
# TAB 1: Live Monitoring
# -----------------------------------------------------------------------------
with tab_monitor:
    # Top KPI Metrics Row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    metric_eye_status = kpi1.empty()
    metric_drowsy_status = kpi2.empty()
    metric_ear = kpi3.empty()
    metric_blinks = kpi4.empty()
    metric_closure_time = kpi5.empty()

    st.markdown("---")

    # Main Grid: Video Stream on Left, Environmental Telemetry on Right
    col_video, col_sensors = st.columns([1.5, 1])

    with col_sensors:
        st.subheader("ESP32 IoT Sensor Telemetry")

        sensor_temp_box = st.empty()
        sensor_hum_box = st.empty()
        sensor_pir_box = st.empty()
        sensor_buzzer_box = st.empty()

        st.markdown("##### Environmental Comfort Check")
        env_advice_box = st.empty()

    with col_video:
        st.subheader("Live Camera Stream & Face Mesh")
        video_placeholder = st.empty()
        camera_ctrl_cols = st.columns([1, 1])
        start_stream = camera_ctrl_cols[0].checkbox("Start Camera Feed", value=False)
        sim_stream = camera_ctrl_cols[1].checkbox("Simulate Eye Feed (No Cam)", value=False)


    # Simulation frame generator for demonstration when no camera is present
    def generate_demo_frame(eye_state: str, ear_val: float) -> np.ndarray:
        img = np.zeros((360, 480, 3), dtype=np.uint8)
        img[:] = (30, 30, 30)

        # Draw simulated face outline
        cv2.ellipse(img, (240, 180), (120, 150), 0, 0, 360, (180, 180, 180), 2)

        # Eye centers
        left_center = (190, 160)
        right_center = (290, 160)

        if eye_state == "OPEN":
            eye_color = (0, 220, 0)
            cv2.ellipse(img, left_center, (28, 14), 0, 0, 360, eye_color, 2)
            cv2.circle(img, left_center, 6, (0, 220, 0), -1)
            cv2.ellipse(img, right_center, (28, 14), 0, 0, 360, eye_color, 2)
            cv2.circle(img, right_center, 6, (0, 220, 0), -1)
        else:
            eye_color = (0, 0, 255)
            cv2.line(img, (162, 160), (218, 160), eye_color, 3)
            cv2.line(img, (262, 160), (318, 160), eye_color, 3)

        cv2.putText(img, f"DEMO SIMULATION | EAR: {ear_val:.2f}", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return img


    # Live Feed Execution Loop
    if start_stream and op_mode == "Live Webcam + IoT Telemetry":
        cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        stop_button = st.button("Stop Monitoring")

        while cap.isOpened() and not stop_button:
            ret, frame = cap.read()
            if not ret or frame is None:
                video_placeholder.warning("Waiting for camera frame...")
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)

            # Vision pipeline
            det = st.session_state.eye_detector.process_frame(frame)
            drowsy = st.session_state.drowsiness_detector.update(
                face_detected=det["face_detected"],
                left_ear=det["left_ear"],
                right_ear=det["right_ear"]
            )

            # Telemetry & Alert coordination
            summary = st.session_state.sensor_mgr.get_summary()
            st.session_state.alert_mgr.process_alert(drowsy, summary)

            # Record EAR history
            st.session_state.ear_history.append(drowsy["avg_ear"])
            if len(st.session_state.ear_history) > 60:
                st.session_state.ear_history.pop(0)

            # Render HUD on video
            annotated = st.session_state.eye_detector.render_overlay(
                frame=frame,
                detection_res=det,
                drowsiness_res=drowsy,
                sensor_data=summary,
                fps=25.0
            )

            # Update Streamlit UI components
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            video_placeholder.image(annotated_rgb, channels="RGB", use_container_width=True)

            # Update KPIs
            o_status = drowsy["overall_status"]
            state_str = drowsy["state"]
            metric_eye_status.metric("Eye State", o_status)
            metric_drowsy_status.metric("System State", state_str)
            metric_ear.metric("Avg EAR", f"{drowsy['avg_ear']:.3f}", delta=f"{drowsy['avg_ear'] - ear_slider:.2f}")
            metric_blinks.metric("Blink Count", drowsy["blink_count"])
            metric_closure_time.metric("Closure Duration", f"{drowsy['closure_duration']:.2f}s")

            # Update Sensor display
            temp_val = summary.get("temperature")
            hum_val = summary.get("humidity")
            pir_val = summary.get("pir_state", 0)
            buzz_val = summary.get("buzzer_on", False)

            sensor_temp_box.metric("Cabin Temperature", f"{temp_val:.1f} °C" if temp_val is not None else "Waiting...")
            sensor_hum_box.metric("Relative Humidity", f"{hum_val:.1f} %" if hum_val is not None else "Waiting...")
            sensor_pir_box.metric("PIR Motion", "Motion Detected 🏃" if pir_val == 1 else "Stationary / Clear")
            sensor_buzzer_box.metric("Active Buzzer", "🚨 ALARM ON" if buzz_val else "Silent (OFF)")

            time.sleep(0.03)

        cap.release()

    elif sim_stream or op_mode == "Pure Simulation Mode":
        # Interactive demonstration simulation mode without camera
        sim_closed = st.checkbox("Simulate Eye Closure (Hold to test Drowsiness Alarm)", value=False)
        sim_ear = 0.14 if sim_closed else 0.31

        drowsy = st.session_state.drowsiness_detector.update(
            face_detected=True,
            left_ear=sim_ear,
            right_ear=sim_ear
        )
        summary = st.session_state.sensor_mgr.get_summary()
        st.session_state.alert_mgr.process_alert(drowsy, summary)

        demo_img = generate_demo_frame("CLOSED" if sim_closed else "OPEN", sim_ear)
        video_placeholder.image(demo_img, channels="BGR", use_container_width=True)

        metric_eye_status.metric("Eye State", drowsy["overall_status"])
        metric_drowsy_status.metric("System State", drowsy["state"])
        metric_ear.metric("Avg EAR", f"{sim_ear:.3f}")
        metric_blinks.metric("Blink Count", drowsy["blink_count"])
        metric_closure_time.metric("Closure Duration", f"{drowsy['closure_duration']:.2f}s")

        temp_val = summary.get("temperature")
        hum_val = summary.get("humidity")
        pir_val = summary.get("pir_state", 0)
        buzz_val = summary.get("buzzer_on", False)

        sensor_temp_box.metric("Cabin Temperature", f"{temp_val:.1f} °C" if temp_val is not None else "26.5 °C")
        sensor_hum_box.metric("Relative Humidity", f"{hum_val:.1f} %" if hum_val is not None else "54.2 %")
        sensor_pir_box.metric("PIR Motion", "Motion Detected 🏃" if pir_val == 1 else "Stationary")
        sensor_buzzer_box.metric("Active Buzzer", "🚨 ALARM ON" if buzz_val else "Silent (OFF)")
    else:
        video_placeholder.info("Check 'Start Camera Feed' above to begin real-time eye tracking, or 'Simulate Eye Feed' for an instant demonstration.")


# -----------------------------------------------------------------------------
# TAB 2: Real-Time Charts & Historical Analytics
# -----------------------------------------------------------------------------
with tab_charts:
    st.subheader("Telemetry & Performance Trends")

    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        st.markdown("#### Eye Aspect Ratio (EAR) vs Time")
        if len(st.session_state.ear_history) > 2:
            ear_df = pd.DataFrame({
                "EAR": st.session_state.ear_history,
                "Threshold": [ear_slider] * len(st.session_state.ear_history)
            })
            st.line_chart(ear_df)
        else:
            # Generate sample trend for visual presentation
            dummy_t = np.linspace(0, 10, 50)
            dummy_ear = 0.30 + 0.03 * np.sin(dummy_t)
            dummy_ear[20:25] = 0.15  # blink
            st.line_chart(pd.DataFrame({"EAR": dummy_ear, "Threshold": [0.22]*50}))

    with chart_c2:
        st.markdown("#### Environmental Temperature & Humidity Trend")
        series = st.session_state.sensor_mgr.get_history_series()
        if len(series["time"]) > 2:
            env_df = pd.DataFrame({
                "Temperature (°C)": series["temperature"],
                "Humidity (%)": series["humidity"]
            })
            st.line_chart(env_df)
        else:
            st.info("Run the live camera feed or simulation mode to stream environmental telemetry.")


# -----------------------------------------------------------------------------
# TAB 3: Project Architecture & Faculty Viva Reference
# -----------------------------------------------------------------------------
with tab_docs:
    st.subheader("System Architecture & Viva Guide")

    st.markdown("""
    ### 1. Mathematical Formulation: Eye Aspect Ratio (EAR)
    The system utilizes the landmark geometry established by Soukupová and Čech:

    $$\\text{EAR} = \\frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \\cdot ||p_1 - p_4||}$$

    - **$p_1, p_4$**: Lateral and medial eye canthi (horizontal extent).
    - **$p_2, p_6$ and $p_3, p_5$**: Complementary vertical eyelid landmark coordinates.
    - **Scale Invariance**: Normalization by horizontal eye width ensures that the EAR is invariant
      to camera distance and facial scale.

    ### 2. Hardware Wiring Configuration (ESP32 Dev Board)
    | Component | ESP32 GPIO | Electrical Specification & Wiring Note |
    |---|---|---|
    | **DHT22 DATA** | **GPIO 4** | 3.3V logic. (10k pull-up required if bare sensor) |
    | **PIR OUT** | **GPIO 27** | 3.3V logic output from HC-SR501 |
    | **Active Buzzer** | **GPIO 26** | Controlled via NPN transistor driver / module |
    | **Warning LED** | **GPIO 25** | In series with 220Ω - 330Ω current-limiting resistor |
    | **Power & Ground** | **3.3V / 5V / GND** | Common ground across all modules |

    ### 3. USB Serial Telemetry Protocol
    - **Baud Rate**: 115200 bps
    - **ESP32 Telemetry**: `SENSOR,<temperature_c>,<humidity_pct>,<pir_state>\\n`
    - **Actuator Commands**: `BUZZER:ON\\n` and `BUZZER:OFF\\n` (Sent strictly upon state transition)
    """)
