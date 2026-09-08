import serial
import time
from pynput.mouse import Controller, Button

PORT = "/dev/cu.usbserial-A5069RR4"
BAUD = 115200
SPEED = 3
RAPIDFIRE_INTERVAL = 0.1

mouse = Controller()
ser = serial.Serial(PORT, BAUD, timeout=0.05)

left_was_down = False
right_was_down = False
left_last_fire = 0.0
right_last_fire = 0.0

def parse_state(line):
    state = {}

    for item in line.split(","):
        key, value = item.split(":")
        state[key] = int(value)

    return state


while True:
    try:
        line = ser.readline().decode("utf-8", errors="replace").strip()

        if not line:
            continue

        state = parse_state(line)

        dx = 0
        dy = 0

        if state["L"]:
            dx -= SPEED

        if state["R"]:
            dx += SPEED

        if state["U"]:
            dy -= SPEED

        if state["D"]:
            dy += SPEED

        if dx != 0 or dy != 0:
            mouse.move(dx, dy)

        # Left mouse button - rapid fire
        now = time.time()
        if state["LC"] and (now - left_last_fire >= RAPIDFIRE_INTERVAL or not left_was_down):
            mouse.press(Button.left)
            mouse.release(Button.left)
            left_last_fire = now

        left_was_down = state["LC"]

        # Right mouse button - rapid fire
        if state["RC"] and (now - right_last_fire >= RAPIDFIRE_INTERVAL or not right_was_down):
            mouse.press(Button.right)
            mouse.release(Button.right)
            right_last_fire = now

        right_was_down = state["RC"]

    except Exception as e:
        print("Error:", e)