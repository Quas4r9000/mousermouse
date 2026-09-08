import serial
from pynput.mouse import Controller, Button

PORT = "COM8"
BAUD = 115200
SPEED = 5

mouse = Controller()
ser = serial.Serial(PORT, BAUD, timeout=0.05)

left_was_down = False
right_was_down = False

def parse_state(line):
    state = {}

    for item in line.split(","):
        key, value = item.split(":")
        state[key] = int(value)

    return state


while True:
    try:
        line = ser.readline().decode("utf-8").strip()

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

        # Left mouse button
        if state["LC"] and not left_was_down:
            mouse.press(Button.left)

        elif not state["LC"] and left_was_down:
            mouse.release(Button.left)

        # Right mouse button
        if state["RC"] and not right_was_down:
            mouse.press(Button.right)

        elif not state["RC"] and right_was_down:
            mouse.release(Button.right)

        left_was_down = state["LC"]
        right_was_down = state["RC"]

    except Exception as e:
        print("Error:", e)