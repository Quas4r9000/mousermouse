import serial
import time
import ctypes
from ctypes import c_void_p, c_int, c_double, c_uint64, c_ubyte, Structure, pointer, CDLL
from ctypes.util import find_library

# Load frameworks
cg = CDLL(find_library("CoreGraphics"))
cf = CDLL(find_library("CoreFoundation"))

# CoreFoundation
cf.CFRelease.argtypes = [c_void_p]
cf.CFRelease.restype = None

# CoreGraphics types
class CGPoint(Structure):
    _fields_ = [("x", c_double), ("y", c_double)]

# Function signatures
cg.CGEventCreateMouseEvent.argtypes = [c_void_p, c_int, c_double, c_double]
cg.CGEventCreateMouseEvent.restype = c_void_p

cg.CGEventPost.argtypes = [c_int, c_void_p]
cg.CGEventPost.restype = None

cg.CGEventSetIntegerValueField.argtypes = [c_void_p, c_uint64, c_uint64]
cg.CGEventSetIntegerValueField.restype = None

cg.CGEventSetDoubleValueField.argtypes = [c_void_p, c_uint64, c_double]
cg.CGEventSetDoubleValueField.restype = None

# Constants
kCGEventLeftMouseDown = 1
kCGEventLeftMouseUp = 2
kCGEventRightMouseDown = 3
kCGEventRightMouseUp = 4
kCGHIDEventTap = 0

PORT = "/dev/cu.usbserial-A5069RR4"
BAUD = 115200
SPEED = 5
RAPIDFIRE = False
RAPIDFIRE_INTERVAL = 100  # ms
RAPIDFIRE_TOGGLED = True

ser = serial.Serial(PORT, BAUD, timeout=0.05)

def send_move(dx, dy):
    try:
        event = cg.CGEventCreateMouseEvent(None, 0, 0, 0)
        if event:
            cg.CGEventSetDoubleValueField(event, 1, c_double(dx))  # kCGMouseEventDeltaX
            cg.CGEventSetDoubleValueField(event, 2, c_double(dy))  # kCGMouseEventDeltaY
            cg.CGEventPost(kCGHIDEventTap, event)
            cf.CFRelease(event)
    except Exception:
        pass

def send_click(btn_down):
    try:
        evt_type = kCGEventLeftMouseDown if btn_down else kCGEventLeftMouseUp
        event = cg.CGEventCreateMouseEvent(None, evt_type, 0, 0)
        if event:
            cg.CGEventPost(kCGHIDEventTap, event)
            cf.CFRelease(event)
    except Exception:
        pass

def send_right_click(btn_down):
    try:
        evt_type = kCGEventRightMouseDown if btn_down else kCGEventRightMouseUp
        event = cg.CGEventCreateMouseEvent(None, evt_type, 0, 0)
        if event:
            cg.CGEventPost(kCGHIDEventTap, event)
            cf.CFRelease(event)
    except Exception:
        pass

left_was_down = False
right_was_down = False
left_last_fire = 0
right_last_fire = 0
prev_state = {}

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
            send_move(dx, dy)

        # Toggle rapidfire when all 4 directions pressed together
        all_directions = state.get("L") and state.get("R") and state.get("U") and state.get("D")
        prev_all_directions = (
            prev_state.get("L") and prev_state.get("R") and
            prev_state.get("U") and prev_state.get("D")
        ) if prev_state else False
        if all_directions and not prev_all_directions and RAPIDFIRE_TOGGLED:
            RAPIDFIRE = not RAPIDFIRE
            print(f"Rapidfire: {'ON' if RAPIDFIRE else 'OFF'}")
            RAPIDFIRE_TOGGLED = False
        elif not all_directions:
            RAPIDFIRE_TOGGLED = True

        # Left mouse button
        if RAPIDFIRE:
            now = time.time()
            if state.get("LC") and (now - left_last_fire >= RAPIDFIRE_INTERVAL / 1000 or not left_was_down):
                send_click(True)
                time.sleep(0.005)
                send_click(False)
                left_last_fire = now
        else:
            if state.get("LC") and not left_was_down:
                send_click(True)
            elif not state.get("LC") and left_was_down:
                send_click(False)

        left_was_down = state.get("LC")

        # Right mouse button
        if RAPIDFIRE:
            now = time.time()
            if state.get("RC") and (now - right_last_fire >= RAPIDFIRE_INTERVAL / 1000 or not right_was_down):
                send_right_click(True)
                time.sleep(0.005)
                send_right_click(False)
                right_last_fire = now
        else:
            if state.get("RC") and not right_was_down:
                send_right_click(True)
            elif not state.get("RC") and right_was_down:
                send_right_click(False)

        right_was_down = state.get("RC")

        prev_state = dict(state)

    except Exception as e:
        print("Error:", e)
