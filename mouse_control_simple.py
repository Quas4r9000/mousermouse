import serial
import time
from pynput.mouse import Controller, Button

PORT = "/dev/cu.usbserial-A5069RR4"
BAUD = 115200
SPEED = 3
RAPIDFIRE = True
RAPIDFIRE_INTERVAL = 0.2

mouse = Controller()
ser = serial.Serial(PORT, BAUD, timeout=0.05)

left_was_down = False
right_was_down = False
left_last_fire = 0.0
right_last_fire = 0.0

def parse_state(line):
    state = {}

    for item in line.split(","):
        parts = item.split(":")
        if len(parts) != 2:
            continue
        key, value = parts
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

        if state.get("L"):
            dx -= SPEED

        if state.get("R"):
            dx += SPEED

        if state.get("U"):
            dy -= SPEED

        if state.get("D"):
            dy += SPEED

        if dx != 0 or dy != 0:
            mouse.move(dx, dy)

        # Left mouse button
        if RAPIDFIRE:
            now = time.time()
            if state.get("LC") and (now - left_last_fire >= RAPIDFIRE_INTERVAL or not left_was_down):
                mouse.press(Button.left)
                mouse.release(Button.left)
                left_last_fire = now
        else:
            if state.get("LC") and not left_was_down:
                mouse.press(Button.left)
            elif not state.get("LC") and left_was_down:
                mouse.release(Button.left)

        left_was_down = state.get("LC")

        # Right mouse button
        if RAPIDFIRE:
            if state.get("RC") and (now - right_last_fire >= RAPIDFIRE_INTERVAL or not right_was_down):
                mouse.press(Button.right)
                mouse.release(Button.right)
                right_last_fire = now
        else:
            if state.get("RC") and not right_was_down:
                mouse.press(Button.right)
            elif not state.get("RC") and right_was_down:
                mouse.release(Button.right)

        right_was_down = state.get("RC")

    except Exception as e:
        print("Error:", e)