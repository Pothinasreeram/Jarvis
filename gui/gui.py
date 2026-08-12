import customtkinter as ctk
import threading
import random
import math
import pyaudio
import numpy as np
import os
import psutil
import time
from voice_engine.voice import (
    speak,
    speaking_status
)
from memory_layer.memory import load_memory
from program_finder import build_program_database
from system_layer.system_monitor import system_watchdog
from core.assistant import start_jarvis

# ---------------- PERFORMANCE SETTINGS ----------------

PERFORMANCE_MODE = True

BRAIN_DELAY = 180 if PERFORMANCE_MODE else 120
REACTOR_DELAY = 70 if PERFORMANCE_MODE else 40
GLOBE_DELAY = 80 if PERFORMANCE_MODE else 40
SPHERE_DELAY = 80 if PERFORMANCE_MODE else 40
RADAR_DELAY = 60 if PERFORMANCE_MODE else 30
WAVE_DELAY = 80 if PERFORMANCE_MODE else 50
PARTICLE_DELAY = 500

BRAIN_NODE_COUNT = 25
GLOBE_PARTICLE_COUNT = 40 if PERFORMANCE_MODE else 80
GLOBE_CONNECTION_COUNT = 20 if PERFORMANCE_MODE else 40
SPHERE_PARTICLE_COUNT = 60 if PERFORMANCE_MODE else 120
WAVE_PARTICLE_COUNT = 20 if PERFORMANCE_MODE else 40

is_speaking = False
if not os.path.exists("programs.json"):
    build_program_database()
# ---------------- GUI SETUP ----------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("JARVIS")
app.attributes("-fullscreen", True)
app.configure(fg_color="#05080f")
app.wm_attributes("-alpha", 0.97)

def exit_fullscreen(event=None):
    app.attributes("-fullscreen", False)

app.bind("<Escape>", exit_fullscreen)

thinking_active = False
# ---------------- AI BRAIN VISUALIZATION ----------------

brain_canvas = ctk.CTkCanvas(
    app,
    width=500,
    height=200,
    bg="#05080f",
    highlightthickness=0
)

brain_canvas.pack(pady=5)

nodes = []
connections = []

for _ in range(BRAIN_NODE_COUNT):

    x = random.randint(50,450)
    y = random.randint(30,170)

    node = brain_canvas.create_oval(
        x-3,y-3,x+3,y+3,
        fill="#00ffff",
        outline=""
    )

    nodes.append((node,x,y))

# create connections

for i in range(len(nodes)):
    for j in range(i+1,len(nodes)):

        x1,y1 = nodes[i][1],nodes[i][2]
        x2,y2 = nodes[j][1],nodes[j][2]

        dist = math.sqrt((x2-x1)**2+(y2-y1)**2)

        if dist < 120:

            line = brain_canvas.create_line(
                x1,y1,x2,y2,
                fill="#004444",
                width=1
            )

            connections.append(line)

brain_flash = 0

def animate_brain():

    global brain_flash

    brain_flash += 1

    for node,x,y in nodes:

        if thinking_active:

            glow = random.randint(150,255)
            color = f"#00{glow:02x}{glow:02x}"

        else:

            glow = 120 + int(40*math.sin(brain_flash/5))
            color = f"#00{glow:02x}{glow:02x}"

        brain_canvas.itemconfig(node,fill=color)

    app.after(BRAIN_DELAY, animate_brain)

animate_brain()
# ---------------- HEADER ----------------

header = ctk.CTkLabel(
    app,
    text="J.A.R.V.I.S",
    font=("Consolas", 28, "bold"),
    text_color="#00ffff"
)
header.pack(pady=10)

audio_level = 0
# ---------------- ARC REACTOR HUD ----------------

reactor_canvas = ctk.CTkCanvas(
    app,
    width=160,
    height=160,
    bg="#05080f",
    highlightthickness=0
)

reactor_canvas.pack(pady=10)

# outer ring
outer_ring = reactor_canvas.create_oval(
    10, 10, 150, 150,
    outline="#00ffff",
    width=3
)

# middle ring
middle_ring = reactor_canvas.create_oval(
    35, 35, 125, 125,
    outline="#0099ff",
    width=2
)

# glowing core
core = reactor_canvas.create_oval(
    65, 65, 95, 95,
    fill="#00ffff",
    outline=""
)

# ---------- REACTOR ENERGY ARMS ----------

reactor_lines = []

for i in range(0, 360, 60):

    angle = math.radians(i)

    x1 = 80 + 40 * math.cos(angle)
    y1 = 80 + 40 * math.sin(angle)

    x2 = 80 + 65 * math.cos(angle)
    y2 = 80 + 65 * math.sin(angle)

    line = reactor_canvas.create_line(
        x1, y1, x2, y2,
        fill="#00ffff",
        width=2
    )

    reactor_lines.append(line)
# ---------- HOLOGRAPHIC RINGS ----------

ring1 = reactor_canvas.create_oval(
    20,20,140,140,
    outline="#00ffff",
    width=1
)

ring2 = reactor_canvas.create_oval(
    45,45,115,115,
    outline="#0088ff",
    width=1
)

ring_rotation = 0
# -------- HOLOGRAPHIC GLOBE --------

globe_particles = []
globe_connections = []
globe_angle = 0
globe_center_x = 80
globe_center_y = 20
globe_radius = 40

# ---------- REACTOR ANIMATION ----------

reactor_angle = 0
pulse = 0
direction = 1
# -------- CREATE HOLOGRAPHIC GLOBE --------

for _ in range(GLOBE_PARTICLE_COUNT):

    theta = random.uniform(0, math.pi * 2)
    phi = random.uniform(0, math.pi)

    x = math.sin(phi) * math.cos(theta)
    y = math.sin(phi) * math.sin(theta)
    z = math.cos(phi)

    particle = reactor_canvas.create_oval(
        0,0,0,0,
        fill="#00ffff",
        outline=""
    )

    globe_particles.append([x,y,z,particle])


# create network connections
for _ in range(GLOBE_CONNECTION_COUNT):

    line = reactor_canvas.create_line(
        0,0,0,0,
        fill="#0088ff",
        width=1
    )

    globe_connections.append(line)

def animate_reactor():

    global pulse, direction, reactor_angle, ring_rotation

    pulse = min(audio_level/200,15)
    reactor_angle += 4

    if pulse > 12 or pulse < 0:
        direction *= -1

    # core pulse
    size = 65 - pulse/2
    reactor_canvas.coords(core, size, size, 160-size, 160-size)

    glow = min(255, int(200 + pulse*4))
    color = f"#00{glow:02x}{glow:02x}"

    reactor_canvas.itemconfig(core, fill=color)

    # rotate reactor arms
    for i, line in enumerate(reactor_lines):
        
        angle = math.radians(i*60 + reactor_angle)

        x1 = 80 + 40 * math.cos(angle)
        y1 = 80 + 40 * math.sin(angle)

        x2 = 80 + 65 * math.cos(angle)
        y2 = 80 + 65 * math.sin(angle)

        reactor_canvas.coords(line, x1, y1, x2, y2)
        # -------- ENERGY LIGHTNING --------

    if random.random() < 0.2:

        x1 = random.randint(60,100)
        y1 = random.randint(60,100)

        x2 = random.randint(40,120)
        y2 = random.randint(40,120)

        bolt = reactor_canvas.create_line(
            x1,y1,x2,y2,
            fill="#00ffff",
            width=1
        )

        app.after(80, lambda: reactor_canvas.delete(bolt))


    ring_rotation += 2

    offset = 10 * math.sin(math.radians(ring_rotation))

    reactor_canvas.coords(ring1,
                          20-offset,20-offset,
                          140+offset,140+offset)

    reactor_canvas.coords(ring2,
                          45+offset,45+offset,
                          115-offset,115-offset)
    app.after(REACTOR_DELAY, animate_reactor)
    

# ---------------- HOLOGRAPHIC AI SPHERE ----------------

sphere_particles = []

for _ in range(SPHERE_PARTICLE_COUNT):

    theta = random.uniform(0, math.pi*2)
    phi = random.uniform(0, math.pi)

    x = math.sin(phi) * math.cos(theta)
    y = math.sin(phi) * math.sin(theta)
    z = math.cos(phi)

    particle = reactor_canvas.create_oval(0,0,0,0,
                                          fill="#00ffff",
                                          outline="")

    sphere_particles.append([x,y,z,particle])

sphere_angle = 0
animate_reactor()
def animate_globe():

    global globe_angle

    globe_angle += 2

    projected = []

    for p in globe_particles:

        x,y,z,particle = p

        rx = x*math.cos(math.radians(globe_angle)) - z*math.sin(math.radians(globe_angle))
        rz = x*math.sin(math.radians(globe_angle)) + z*math.cos(math.radians(globe_angle))

        scale = 25/(rz+3)

        sx = globe_center_x + rx*scale*10
        sy = globe_center_y + y*scale*10

        reactor_canvas.coords(
            particle,
            sx-3,sy-3,
            sx+3,sy+3
        )

        projected.append((sx,sy))

    for line in globe_connections:

        p1 = random.choice(projected)
        p2 = random.choice(projected)

        reactor_canvas.coords(
            line,
            p1[0],p1[1],
            p2[0],p2[1]
        )

    app.after(40, animate_globe)
animate_globe()
def animate_ai_sphere():

    global sphere_angle

    radius = 90
    cx, cy = 80, 80

    sphere_angle += 0.03

    for p in sphere_particles:

        x, y, z, obj = p

        # rotate Y axis
        rx = x * math.cos(sphere_angle) - z * math.sin(sphere_angle)
        rz = x * math.sin(sphere_angle) + z * math.cos(sphere_angle)

        scale = 1 / (rz + 3)

        px = cx + rx * radius * scale
        py = cy + y * radius * scale

        size = 2 + 4 * scale

        reactor_canvas.coords(
            obj,
            px-size, py-size,
            px+size, py+size
        )

    app.after(SPHERE_DELAY, animate_ai_sphere)

animate_ai_sphere()
# ---------------- STATUS TEXT ----------------

status_label = ctk.CTkLabel(
    app,
    text="STATUS: IDLE",
    font=("Consolas", 12),
    text_color="#00ffff"
)
status_label.pack()

system_label = ctk.CTkLabel(
    app,
    text="CPU: 0% | RAM: 0% | Battery: N/A",
    font=("Consolas", 12),
    text_color="#00ffff"
)
system_label.pack()

def set_status(color):
    global current_color
    current_color = color

    if color == "yellow":
        status_label.configure(text="STATUS: LISTENING")

    elif color == "blue":
        status_label.configure(text="STATUS: PROCESSING")

    elif color == "green":
        status_label.configure(text="STATUS: SPEAKING")

    else:
        status_label.configure(text="STATUS: IDLE")
# ---------------- THINKING ANIMATION ----------------



def thinking_animation():

    dots = ["Thinking.", "Thinking..", "Thinking..."]
    i = 0

    def animate():
        nonlocal i

        if thinking_active:
            status_label.configure(text=dots[i % 3])
            i += 1
            app.after(400, animate)

    animate()

# ---------------- WAVEFORM VISUALIZER ----------------

# ---------------- WAVEFORM VISUALIZER ----------------
# ---------------- HUD CANVAS ----------------

hud_canvas = ctk.CTkCanvas(app,
                           width=600,
                           height=600,
                           bg="#05080f",
                           highlightthickness=0)
hud_canvas.pack(pady=20)
center_x = 300
center_y = 300

outer_ring = hud_canvas.create_oval(
    100, 100, 500, 500,
    outline="#00ffff",
    width=2
)

inner_ring = hud_canvas.create_oval(
    180, 180, 420, 420,
    outline="#0088ff",
    width=2
)
# -------- RADAR SWEEP --------

radar_line = hud_canvas.create_line(
    center_x, center_y,
    center_x, 100,
    fill="#00ffff",
    width=3
)

radar_angle = 0

def animate_radar():

    global radar_angle

    radar_angle += 3

    angle = math.radians(radar_angle)

    x = center_x + 200 * math.cos(angle)
    y = center_y + 200 * math.sin(angle)

    hud_canvas.coords(
        radar_line,
        center_x, center_y,
        x, y
    )

    app.after(RADAR_DELAY, animate_radar)

animate_radar()

ring_angle = 0

def animate_hud():
    global ring_angle

    ring_angle += 2

    hud_canvas.delete("scanner")

    for i in range(0, 360, 30):

        angle = math.radians(i + ring_angle)

        x1 = center_x + 200 * math.cos(angle)
        y1 = center_y + 200 * math.sin(angle)

        x2 = center_x + 240 * math.cos(angle)
        y2 = center_y + 240 * math.sin(angle)

        hud_canvas.create_line(
            x1, y1, x2, y2,
            fill="#00ffff",
            width=2,
            tags="scanner"
        )

    app.after(500, animate_hud)
animate_hud()

wave_canvas = ctk.CTkCanvas(
    app,
    width=900,
    height=120,
    bg="#05080f",
    highlightthickness=0
)
# ---------------- LIVE MICROPHONE ENGINE ----------------

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

audio_level = 0


def listen_microphone():
    global audio_level
    global thinking_active

    while True:
        try:
            if thinking_active:
                audio_level = 0
                time.sleep(0.05)
                continue

            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_level = np.abs(audio_data).mean()

            time.sleep(0.02)

        except:
            time.sleep(0.05)


# Run mic listener in background thread
mic_thread = threading.Thread(target=listen_microphone, daemon=True)
mic_thread.start()
wave_canvas.pack()

wave_bars = []
wave_positions = []

for i in range(70):
    x = 20 + i * 12
    bar = wave_canvas.create_line(x, 60, x, 60, fill="#00ffff", width=3)
    wave_bars.append(bar)
    wave_positions.append(x)  # store x safely


# ---------------- REAL VOICE WAVEFORM ----------------

def animate_wave():
    global audio_level

    if audio_level < 50:
        for i, bar in enumerate(wave_bars):
            x = wave_positions[i]
            wave_canvas.coords(bar, x, 60, x, 60)

        app.after(WAVE_DELAY, animate_wave)
        return

    normalized = min(audio_level / 3000, 1.0)

    for i, bar in enumerate(wave_bars):
        height = normalized * 60
        x = wave_positions[i]

        wave_canvas.coords(bar,
                           x, 60 - height,
                           x, 60 + height)

    app.after(WAVE_DELAY, animate_wave)

# ---------------- PARTICLE EFFECT ----------------

# ---------------- PARTICLE SYSTEM ----------------

particles = []

for _ in range(WAVE_PARTICLE_COUNT):
    x = random.randint(0, 900)
    y = random.randint(0, 120)
    size = random.randint(2, 4)

    dot = wave_canvas.create_oval(
        x, y, x + size, y + size,
        fill="#00ffff",
        outline=""
    )

    particles.append({
        "id": dot,
        "x": x,
        "y": y,
        "size": size,
        "speed": random.uniform(0.5, 2)
    })


def animate_particles():
    for p in particles:
        try:
            p["y"] -= p["speed"]

            if p["y"] < 0:
                p["y"] = 120
                p["x"] = random.randint(0, 900)

            x1 = float(p["x"])
            y1 = float(p["y"])
            x2 = float(p["x"] + p["size"])
            y2 = float(p["y"] + p["size"])

            wave_canvas.coords(p["id"], x1, y1, x2, y2)

        except Exception:
            pass

    app.after(PARTICLE_DELAY, animate_particles)
    app.after(WAVE_DELAY, animate_wave)




# ---------------- TEXT OUTPUT ----------------

textbox = ctk.CTkTextbox(
    app,
    width=900,
    height=250,
    font=("Consolas", 14),
    fg_color="#0a0f18",
    border_width=1,
    border_color="#00ffff"
)
textbox.pack(pady=10)
textbox.insert("end", "System initializing...\n\n")
textbox.configure(state="disabled")


def type_writer(text, index=0):
    if index < len(text):
        textbox.insert("end", text[index])
        textbox.see("end")
        app.after(8, type_writer, text, index+1)
    else:
        textbox.insert("end", "\n\n")
        textbox.configure(state="disabled")


def update_display(text):
    textbox.configure(state="normal")
    textbox.insert("end", "\nJARVIS: ")
    textbox.see("end")
    type_writer(text)


# ---------------- JARVIS CORE ----------------

memory = load_memory()
conversation_context = {
    "last_subject": None
}
WAKE_WORD = "jarvis"

last_subject = None
pending_action = None

def update_system_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "N/A"

    color = "#00ffff"
    if cpu > 80 or ram > 80:
        color = "#ff4444"

    system_label.configure(
        text=f"CPU: {cpu}% | RAM: {ram}% | Battery: {battery_percent}%",
        text_color=color
    )

    app.after(1000, update_system_stats)
update_system_stats()





# ---------------- BOOT SEQUENCE ----------------

def startup_sequence():
    messages = [
        "Initializing core systems...",
        "Loading neural architecture...",
        "Calibrating voice interface...",
        "System online."
    ]

    def run_sequence(index=0):
        if index < len(messages):
            update_display(messages[index])
            speak(messages[index])

            # 🔥 Wait for speech to fully finish before next
            def continue_after_speech():
                while speaking_status():
                    time.sleep(0.1)

                run_sequence(index + 1)

            threading.Thread(target=continue_after_speech, daemon=True).start()

        else:
            set_status("red")
            start_jarvis(
                app,
                set_status,
                update_display,
                thinking_animation
          )

    set_status("green")

    run_sequence()

animate_particles()
app.after(1000, startup_sequence)

app.mainloop()

