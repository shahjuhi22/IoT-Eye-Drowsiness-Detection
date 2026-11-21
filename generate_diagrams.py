"""
generate_diagrams.py — Programmatic Visual Diagram Generator
=============================================================
Generates professional, high-resolution PNG architectural and wiring diagrams:
  1. diagrams/esp32_wiring.png
  2. diagrams/system_architecture.png
  3. diagrams/project_flowchart.png
"""

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

DIAGRAMS_DIR = Path(__file__).resolve().parent / "diagrams"
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)


def create_esp32_wiring_diagram():
    """Generates a detailed, color-coded breadboard wiring schematic."""
    fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor("#0F172A")  # Dark theme slate background

    # Title Banner
    ax.text(8, 10.4, "ESP32 SMART EYE MONITORING & DROWSINESS SYSTEM",
            fontsize=18, fontweight="bold", color="#F8FAFC", ha="center")
    ax.text(8, 10.0, "Hardware Schematic & Pin Interconnection Diagram (USB-C ESP32 DevKit)",
            fontsize=12, color="#94A3B8", ha="center")

    # Breadboard Base Graphic
    bb = patches.FancyBboxPatch((0.8, 0.8), 14.4, 8.8, boxstyle="round,pad=0.2",
                                facecolor="#1E293B", edgecolor="#334155", linewidth=2)
    ax.add_patch(bb)

    # -------------------------------------------------------------------------
    # 1. ESP32 NodeMCU Dev Board (Center-Left)
    # -------------------------------------------------------------------------
    esp_box = patches.FancyBboxPatch((5.8, 2.5), 3.8, 5.8, boxstyle="round,pad=0.15",
                                     facecolor="#18181B", edgecolor="#3B82F6", linewidth=2.5)
    ax.add_patch(esp_box)
    ax.text(7.7, 7.8, "ESP32 DEVKIT V1", fontsize=12, fontweight="bold", color="#60A5FA", ha="center")
    ax.text(7.7, 7.45, "(USB-C 30-Pin Module)", fontsize=9, color="#94A3B8", ha="center")

    # Microcontroller SoC Chip
    soc = patches.Rectangle((6.7, 4.4), 2.0, 2.5, facecolor="#27272A", edgecolor="#52525B", linewidth=1.5)
    ax.add_patch(soc)
    ax.text(7.7, 5.65, "ESP-WROOM-32\nWiFi + BLE + Dual Core", fontsize=8, color="#A1A1AA", ha="center")

    # USB-C Port
    usb = patches.Rectangle((7.1, 2.2), 1.2, 0.5, facecolor="#71717A", edgecolor="#D4D4D8", linewidth=1.2)
    ax.add_patch(usb)
    ax.text(7.7, 2.45, "USB-C", fontsize=7.5, fontweight="bold", color="#18181B", ha="center", va="center")
    ax.text(7.7, 1.8, "To Laptop USB Port\n(115200 Baud Serial)", fontsize=8.5, color="#38BDF8", ha="center")

    # ESP32 Key Pins Labeled
    pins = [
        ("3V3", 6.0, 7.0, "#EF4444"),
        ("GND", 6.0, 6.4, "#94A3B8"),
        ("GPIO 4", 6.0, 5.8, "#22C55E"),
        ("VIN (5V)", 6.0, 3.2, "#F97316"),
        ("GPIO 25", 9.4, 6.4, "#A855F7"),
        ("GPIO 26", 9.4, 5.8, "#38BDF8"),
        ("GPIO 27", 9.4, 5.2, "#EAB308"),
        ("GND", 9.4, 3.2, "#94A3B8"),
    ]
    for label, px, py, col in pins:
        p_circ = patches.Circle((px, py), 0.12, facecolor=col, edgecolor="#FFFFFF", linewidth=1)
        ax.add_patch(p_circ)
        ha_align = "right" if px < 7.7 else "left"
        offset = -0.25 if px < 7.7 else 0.25
        ax.text(px + offset, py, label, fontsize=8.5, fontweight="bold", color=col, ha=ha_align, va="center")

    # -------------------------------------------------------------------------
    # 2. DHT22 Temperature & Humidity Sensor (Top Left)
    # -------------------------------------------------------------------------
    dht_box = patches.FancyBboxPatch((1.4, 6.0), 3.2, 3.0, boxstyle="round,pad=0.1",
                                     facecolor="#1E3A8A", edgecolor="#3B82F6", linewidth=2)
    ax.add_patch(dht_box)
    ax.text(3.0, 8.5, "DHT22 SENSOR", fontsize=11, fontweight="bold", color="#93C5FD", ha="center")
    ax.text(3.0, 8.1, "(Temp & Humidity)", fontsize=8.5, color="#BFDBFE", ha="center")

    # Sensor grill icon
    grill = patches.Rectangle((2.3, 6.8), 1.4, 1.0, facecolor="#172554", edgecolor="#60A5FA", linewidth=1)
    ax.add_patch(grill)
    ax.text(3.0, 7.3, "AM2302\nGrill", fontsize=7.5, color="#93C5FD", ha="center")

    dht_pins = [("VCC", 2.0, 6.2), ("DATA", 3.0, 6.2), ("GND", 4.0, 6.2)]
    for lbl, px, py in dht_pins:
        ax.add_patch(patches.Circle((px, py), 0.08, facecolor="#E2E8F0"))
        ax.text(px, py - 0.25, lbl, fontsize=7.5, color="#E2E8F0", ha="center")

    # -------------------------------------------------------------------------
    # 3. PIR Motion Sensor (HC-SR501) (Bottom Left)
    # -------------------------------------------------------------------------
    pir_box = patches.FancyBboxPatch((1.4, 2.0), 3.2, 3.2, boxstyle="round,pad=0.1",
                                     facecolor="#064E3B", edgecolor="#10B981", linewidth=2)
    ax.add_patch(pir_box)
    ax.text(3.0, 4.7, "PIR MOTION SENSOR", fontsize=10.5, fontweight="bold", color="#6EE7B7", ha="center")
    ax.text(3.0, 4.35, "(HC-SR501 Module)", fontsize=8.5, color="#A7F3D0", ha="center")

    # Fresnel dome
    dome = patches.Circle((3.0, 3.4), 0.7, facecolor="#022C22", edgecolor="#34D399", linewidth=1.5)
    ax.add_patch(dome)
    ax.text(3.0, 3.4, "Fresnel\nLens", fontsize=7.5, color="#6EE7B7", ha="center", va="center")

    pir_pins = [("VCC (5V)", 2.0, 2.2), ("OUT", 3.0, 2.2), ("GND", 4.0, 2.2)]
    for lbl, px, py in pir_pins:
        ax.add_patch(patches.Circle((px, py), 0.08, facecolor="#E2E8F0"))
        ax.text(px, py - 0.25, lbl, fontsize=7.5, color="#E2E8F0", ha="center")

    # -------------------------------------------------------------------------
    # 4. Active Buzzer Alarm Circuit (Top Right)
    # -------------------------------------------------------------------------
    buzzer_box = patches.FancyBboxPatch((11.0, 6.0), 3.8, 3.2, boxstyle="round,pad=0.1",
                                        facecolor="#7F1D1D", edgecolor="#EF4444", linewidth=2)
    ax.add_patch(buzzer_box)
    ax.text(12.9, 8.8, "ACTIVE BUZZER MODULE", fontsize=11, fontweight="bold", color="#FCA5A5", ha="center")
    ax.text(12.9, 8.45, "(Audio Drowsy Alarm)", fontsize=8.5, color="#FECACA", ha="center")

    # Buzzer transducer circle
    transducer = patches.Circle((12.9, 7.5), 0.65, facecolor="#450A0A", edgecolor="#F87171", linewidth=1.5)
    ax.add_patch(transducer)
    ax.text(12.9, 7.5, "BUZZER\nSOUND", fontsize=7.5, color="#FCA5A5", ha="center", va="center")

    # Explicit 3-Pin / 2-Pin connections on Buzzer
    buz_pins = [("SIGNAL (I/O)", 11.4, 6.3), ("VCC (3.3V)", 12.9, 6.3), ("GND (-)", 14.2, 6.3)]
    for lbl, px, py in buz_pins:
        ax.add_patch(patches.Circle((px, py), 0.08, facecolor="#E2E8F0"))
        ax.text(px, py - 0.22, lbl, fontsize=7.0, color="#E2E8F0", ha="center")

    # -------------------------------------------------------------------------
    # 5. External Alert LED (Bottom Right)
    # -------------------------------------------------------------------------
    led_box = patches.FancyBboxPatch((11.0, 1.8), 3.8, 3.4, boxstyle="round,pad=0.1",
                                     facecolor="#581C87", edgecolor="#A855F7", linewidth=2)
    ax.add_patch(led_box)
    ax.text(12.9, 4.8, "ALERT STATUS LED", fontsize=11, fontweight="bold", color="#D8B4FE", ha="center")
    ax.text(12.9, 4.45, "(Visual Warning Beacon)", fontsize=8.5, color="#E9D5FF", ha="center")

    led_sym = patches.Circle((12.9, 3.5), 0.45, facecolor="#7E22CE", edgecolor="#C084FC", linewidth=1.5)
    ax.add_patch(led_sym)
    ax.text(12.9, 3.5, "LED", fontsize=8.5, fontweight="bold", color="#F3E8FF", ha="center", va="center")

    # 220 ohm Resistor note
    res_rect = patches.Rectangle((12.1, 2.5), 1.6, 0.4, facecolor="#3B0764", edgecolor="#E9D5FF", linewidth=1)
    ax.add_patch(res_rect)
    ax.text(12.9, 2.7, "220Ω Resistor", fontsize=7.5, color="#E9D5FF", ha="center", va="center")

    led_pins = [("ANODE (+)", 12.1, 2.0), ("CATHODE (-)", 13.7, 2.0)]
    for lbl, px, py in led_pins:
        ax.add_patch(patches.Circle((px, py), 0.08, facecolor="#E2E8F0"))
        ax.text(px, py - 0.22, lbl, fontsize=7.0, color="#E2E8F0", ha="center")

    # -------------------------------------------------------------------------
    # 6. Connecting Wires (Curved spline paths with explicit colors)
    # -------------------------------------------------------------------------
    # DHT22 DATA (GPIO 4) -> Green Wire
    ax.annotate("", xy=(6.0, 5.8), xytext=(3.0, 6.2),
                arrowprops=dict(arrowstyle="-|>", color="#22C55E", lw=2.5,
                                connectionstyle="arc3,rad=-0.15"))
    ax.text(4.2, 6.1, "DATA (GPIO 4)", color="#22C55E", fontsize=8, fontweight="bold")

    # DHT22 VCC (3.3V) -> Red Wire
    ax.annotate("", xy=(6.0, 7.0), xytext=(2.0, 6.2),
                arrowprops=dict(arrowstyle="-|>", color="#EF4444", lw=2,
                                connectionstyle="arc3,rad=-0.2"))

    # DHT22 GND -> Black/Grey Wire
    ax.annotate("", xy=(6.0, 6.4), xytext=(4.0, 6.2),
                arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=2,
                                connectionstyle="arc3,rad=0.1"))

    # PIR OUT (GPIO 27) -> Yellow Wire
    ax.annotate("", xy=(9.4, 5.2), xytext=(3.0, 2.2),
                arrowprops=dict(arrowstyle="-|>", color="#EAB308", lw=2.5,
                                connectionstyle="arc3,rad=0.25"))
    ax.text(4.8, 3.4, "PIR OUT -> GPIO 27", color="#EAB308", fontsize=8, fontweight="bold")

    # PIR VCC (5V VIN) -> Orange Wire
    ax.annotate("", xy=(6.0, 3.2), xytext=(2.0, 2.2),
                arrowprops=dict(arrowstyle="-|>", color="#F97316", lw=2,
                                connectionstyle="arc3,rad=0.15"))

    # PIR GND -> Black/Grey Wire
    ax.annotate("", xy=(6.0, 6.4), xytext=(4.0, 2.2),
                arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=2,
                                connectionstyle="arc3,rad=-0.1"))

    # Buzzer Signal (GPIO 26) -> Cyan Wire
    ax.annotate("", xy=(11.4, 6.3), xytext=(9.4, 5.8),
                arrowprops=dict(arrowstyle="-|>", color="#38BDF8", lw=2.5,
                                connectionstyle="arc3,rad=0.12"))
    ax.text(9.9, 6.4, "GPIO 26 -> SIGNAL", color="#38BDF8", fontsize=8, fontweight="bold")

    # Buzzer GND (-) -> Grey Wire to ESP32 GND
    ax.annotate("", xy=(9.4, 3.2), xytext=(14.2, 6.3),
                arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=2.2,
                                connectionstyle="arc3,rad=0.25"))
    ax.text(12.4, 5.2, "Buzzer GND -> ESP32 GND", color="#94A3B8", fontsize=7.5, fontweight="bold")

    # Buzzer VCC (3.3V) -> Red Wire to 3.3V Rail (if 3-pin module)
    ax.annotate("", xy=(6.0, 7.0), xytext=(12.9, 6.3),
                arrowprops=dict(arrowstyle="-|>", color="#EF4444", lw=1.8,
                                connectionstyle="arc3,rad=-0.15"))

    # LED Anode (+) -> Purple Wire from GPIO 25 through resistor
    ax.annotate("", xy=(12.1, 2.0), xytext=(9.4, 6.4),
                arrowprops=dict(arrowstyle="-|>", color="#C084FC", lw=2.5,
                                connectionstyle="arc3,rad=-0.2"))
    ax.text(9.9, 4.4, "GPIO 25 -> LED (+)", color="#C084FC", fontsize=8, fontweight="bold")

    # LED Cathode (-) -> Grey Wire to ESP32 GND
    ax.annotate("", xy=(9.4, 3.2), xytext=(13.7, 2.0),
                arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=2.0,
                                connectionstyle="arc3,rad=0.15"))
    ax.text(11.2, 2.4, "LED (-) -> GND", color="#94A3B8", fontsize=7.5)

    # Wire Color Legend Table at Bottom
    leg_box = patches.FancyBboxPatch((1.2, 0.4), 13.6, 0.65, boxstyle="round,pad=0.08",
                                     facecolor="#1E293B", edgecolor="#475569", linewidth=1.2)
    ax.add_patch(leg_box)
    legend_text = (
        "WIRE LEGEND:  "
        "■ Red: 3.3V Power  |  "
        "■ Orange: 5V VIN  |  "
        "■ Grey: Common Ground  |  "
        "■ Green: DHT22 Data (GPIO 4)  |  "
        "■ Yellow: PIR Out (GPIO 27)  |  "
        "■ Cyan: Buzzer (GPIO 26)  |  "
        "■ Purple: LED (GPIO 25)"
    )
    ax.text(8.0, 0.72, legend_text, fontsize=8.5, color="#E2E8F0", ha="center", va="center")

    plt.tight_layout()
    output_path = DIAGRAMS_DIR / "esp32_wiring.png"
    try:
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        print(f"[SUCCESS] Generated: {output_path}")
    except Exception as e:
        alt_path = DIAGRAMS_DIR / "esp32_wiring_detailed.png"
        plt.savefig(alt_path, dpi=200, bbox_inches="tight")
        print(f"[SUCCESS] File was locked by viewer. Saved updated diagram to: {alt_path}")
    plt.close()


def create_system_architecture_diagram():
    """Generates a high-level layered system architecture diagram."""
    fig, ax = plt.subplots(figsize=(15, 9), dpi=200)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor("#0F172A")

    # Title
    ax.text(7.5, 8.4, "IoT SMART EYE MONITORING & DROWSINESS SYSTEM",
            fontsize=17, fontweight="bold", color="#F8FAFC", ha="center")
    ax.text(7.5, 8.0, "Three-Tier Edge Architecture: Laptop Computer Vision, USB-Serial Bridge, ESP32 Sensor Node",
            fontsize=11, color="#94A3B8", ha="center")

    # Layer 1: Edge Computer Vision (Laptop)
    cv_layer = patches.FancyBboxPatch((0.8, 4.6), 6.5, 3.0, boxstyle="round,pad=0.15",
                                      facecolor="#1E293B", edgecolor="#38BDF8", linewidth=2)
    ax.add_patch(cv_layer)
    ax.text(4.05, 7.25, "TIER 1: EDGE COMPUTER VISION (LAPTOP)", fontsize=11, fontweight="bold", color="#38BDF8", ha="center")

    blocks_cv = [
        ("Webcam Capture\n(OpenCV VideoCapture)", 1.2, 5.0, 2.5, 1.8),
        ("MediaPipe Face Mesh\n(468 Facial Landmarks)", 4.2, 6.0, 2.8, 0.85),
        ("EAR Mathematical Engine\nSoukupová & Čech (2016)", 4.2, 4.9, 2.8, 0.85),
    ]
    for b_title, bx, by, bw, bh in blocks_cv:
        p = patches.FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.08",
                                   facecolor="#0F172A", edgecolor="#60A5FA", linewidth=1.2)
        ax.add_patch(p)
        ax.text(bx + bw/2, by + bh/2, b_title, fontsize=8.5, color="#E2E8F0", ha="center", va="center")

    # Layer 2: Real-Time Drowsiness State Machine & Control (Laptop)
    ctrl_layer = patches.FancyBboxPatch((7.7, 4.6), 6.5, 3.0, boxstyle="round,pad=0.15",
                                        facecolor="#1E293B", edgecolor="#A855F7", linewidth=2)
    ax.add_patch(ctrl_layer)
    ax.text(10.95, 7.25, "TIER 2: DROWSINESS STATE MACHINE & ACTUATION", fontsize=11, fontweight="bold", color="#C084FC", ha="center")

    blocks_ctrl = [
        ("State Machine\n(Normal / Warning / Drowsy)", 8.1, 5.0, 2.7, 1.8),
        ("Alert Manager & Debounce\n(Cooldown / State Transition)", 11.2, 6.0, 2.7, 0.85),
        ("Logging Engine\n(CSV Telemetry & Logs)", 11.2, 4.9, 2.7, 0.85),
    ]
    for b_title, bx, by, bw, bh in blocks_ctrl:
        p = patches.FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.08",
                                   facecolor="#0F172A", edgecolor="#C084FC", linewidth=1.2)
        ax.add_patch(p)
        ax.text(bx + bw/2, by + bh/2, b_title, fontsize=8.5, color="#E2E8F0", ha="center", va="center")

    # Bridge Banner: USB Serial Communication
    bridge = patches.FancyBboxPatch((2.5, 3.4), 10.0, 0.75, boxstyle="round,pad=0.1",
                                    facecolor="#064E3B", edgecolor="#10B981", linewidth=2)
    ax.add_patch(bridge)
    ax.text(7.5, 3.77, "FULL-DUPLEX USB SERIAL BRIDGE (115200 BAUD)\nESP32 -> Laptop: 'SENSOR,temp,hum,pir'  |  Laptop -> ESP32: 'BUZZER:ON' / 'BUZZER:OFF'",
            fontsize=9.5, fontweight="bold", color="#6EE7B7", ha="center", va="center")

    # Layer 3: ESP32 Hardware & Physical Sensors (Bottom)
    hw_layer = patches.FancyBboxPatch((0.8, 0.6), 13.4, 2.4, boxstyle="round,pad=0.15",
                                      facecolor="#1E293B", edgecolor="#F59E0B", linewidth=2)
    ax.add_patch(hw_layer)
    ax.text(7.5, 2.65, "TIER 3: PHYSICAL EMBEDDED NODE (ESP32 MICROCONTROLLER)", fontsize=11, fontweight="bold", color="#FBBF24", ha="center")

    blocks_hw = [
        ("ESP32 DevKit V1\n(Dual Core 240MHz)", 1.2, 0.9, 2.5, 1.4, "#D97706"),
        ("DHT22 Sensor (GPIO 4)\nTemp & Humidity Sensing", 4.1, 0.9, 2.7, 1.4, "#0284C7"),
        ("PIR Motion (GPIO 27)\nDriver Activity Detection", 7.2, 0.9, 2.7, 1.4, "#16A34A"),
        ("Active Buzzer (GPIO 26)\nAudible Alert Actuator", 10.3, 0.9, 1.8, 1.4, "#DC2626"),
        ("Warning LED (GPIO 25)\nVisual Strobe", 12.3, 0.9, 1.6, 1.4, "#9333EA"),
    ]
    for b_title, bx, by, bw, bh, b_col in blocks_hw:
        p = patches.FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.08",
                                   facecolor="#0F172A", edgecolor=b_col, linewidth=1.5)
        ax.add_patch(p)
        ax.text(bx + bw/2, by + bh/2, b_title, fontsize=8, color="#E2E8F0", ha="center", va="center")

    # Arrows between tiers
    ax.annotate("", xy=(7.7, 5.9), xytext=(7.1, 5.9),
                arrowprops=dict(arrowstyle="-|>", color="#38BDF8", lw=2.5))
    ax.annotate("", xy=(7.5, 3.4), xytext=(7.5, 4.6),
                arrowprops=dict(arrowstyle="<|-|>", color="#10B981", lw=2.5))
    ax.annotate("", xy=(7.5, 3.0), xytext=(7.5, 3.4),
                arrowprops=dict(arrowstyle="-|>", color="#10B981", lw=2.5))

    plt.tight_layout()
    output_path = DIAGRAMS_DIR / "system_architecture.png"
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[SUCCESS] Generated: {output_path}")


def create_project_flowchart():
    """Generates a complete decision and execution flowchart."""
    fig, ax = plt.subplots(figsize=(15, 11), dpi=200)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor("#0F172A")

    ax.text(7.5, 10.4, "EXECUTION FLOWCHART & DECISION LOGIC",
            fontsize=17, fontweight="bold", color="#F8FAFC", ha="center")
    ax.text(7.5, 10.0, "Real-Time Frame Acquisition, EAR Computation, Blink Filtering, and Alarm Actuation",
            fontsize=11, color="#94A3B8", ha="center")

    flow_nodes = [
        ("Start: Initialize Camera,\nESP32 Serial & Models", 7.5, 9.1, 3.6, 0.8, "#3B82F6"),
        ("Capture Video Frame\n& Flip Mirror", 7.5, 7.9, 3.2, 0.7, "#0284C7"),
        ("Face Detected in Frame?", 7.5, 6.7, 3.4, 0.8, "#F59E0B"),
        ("Extract 6-point Left & Right\nEye Landmarks (MediaPipe)", 4.0, 5.5, 3.4, 0.8, "#10B981"),
        ("Face Absent:\nAccumulate Absence Timer", 11.0, 5.5, 3.4, 0.8, "#64748B"),
        ("Calculate Left, Right & Avg EAR:\nEAR = (||p2-p6|| + ||p3-p5||) / (2||p1-p4||)", 4.0, 4.3, 4.2, 0.8, "#10B981"),
        ("Is Avg EAR < Threshold\n(e.g., 0.22)?", 4.0, 3.0, 3.4, 0.8, "#F59E0B"),
        ("Eyes OPEN: Accumulate Blink\nif closure was 0.08s - 0.40s.\nReset Timer & Send BUZZER:OFF", 1.5, 1.4, 3.6, 1.0, "#22C55E"),
        ("Eyes CLOSED: Accumulate\nClosure Duration\n(t = t_now - t_start)", 7.0, 3.0, 3.2, 0.8, "#EF4444"),
        ("Duration >= 1.75s?", 11.5, 3.0, 2.5, 0.7, "#DC2626"),
        ("Trigger Drowsiness Alarm:\nSend 'BUZZER:ON' via Serial,\nFlash Red HUD, Log Event", 11.5, 1.4, 3.6, 1.0, "#991B1B"),
    ]

    for text, cx, cy, w, h, col in flow_nodes:
        bx = cx - w / 2
        by = cy - h / 2
        p = patches.FancyBboxPatch((bx, by), w, h, boxstyle="round,pad=0.1",
                                   facecolor="#1E293B", edgecolor=col, linewidth=2)
        ax.add_patch(p)
        ax.text(cx, cy, text, fontsize=8.2, fontweight="bold", color="#F8FAFC", ha="center", va="center")

    # Connectors
    arrows = [
        ((7.5, 8.7), (7.5, 8.25)),   # Start -> Capture
        ((7.5, 7.55), (7.5, 7.1)),   # Capture -> Face?
        ((6.2, 6.7), (4.5, 5.9)),    # Face? -> Yes (MediaPipe)
        ((8.8, 6.7), (10.5, 5.9)),   # Face? -> No (Absent)
        ((4.0, 5.1), (4.0, 4.7)),    # MediaPipe -> EAR
        ((4.0, 3.9), (4.0, 3.4)),    # EAR -> EAR < thresh?
        ((2.8, 2.6), (2.0, 1.9)),    # EAR < thresh? -> No (OPEN)
        ((5.7, 3.0), (5.4, 3.0)),    # EAR < thresh? -> Yes (CLOSED)
        ((8.6, 3.0), (10.25, 3.0)),  # Closed -> Dur >= 1.75s?
        ((11.5, 2.65), (11.5, 1.9)), # Dur >= 1.75s? -> Yes (Alarm)
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=2))

    ax.text(5.2, 6.5, "YES", fontsize=8.5, fontweight="bold", color="#10B981")
    ax.text(9.5, 6.5, "NO", fontsize=8.5, fontweight="bold", color="#F87171")
    ax.text(2.1, 2.6, "NO (OPEN)", fontsize=8, fontweight="bold", color="#22C55E")
    ax.text(5.5, 3.15, "YES (CLOSED)", fontsize=8, fontweight="bold", color="#F87171")
    ax.text(9.5, 3.15, ">= 1.75s", fontsize=8, fontweight="bold", color="#EF4444")

    # Loop back arrow from bottom to Capture Frame
    ax.annotate("", xy=(7.5, 7.7), xytext=(1.5, 0.7),
                arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=1.5,
                                connectionstyle="arc3,rad=-0.4"))
    ax.text(0.7, 4.0, "Next Video Frame", fontsize=8, color="#94A3B8", rotation=90)

    plt.tight_layout()
    output_path = DIAGRAMS_DIR / "project_flowchart.png"
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[SUCCESS] Generated: {output_path}")


if __name__ == "__main__":
    create_esp32_wiring_diagram()
    create_system_architecture_diagram()
    create_project_flowchart()
