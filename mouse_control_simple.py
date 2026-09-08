import serial
import time
import ctypes
from ctypes import c_void_p, c_int, c_double, c_uint64, CDLL
import os
from ctypes.util import find_library

# Load CoreGraphics
cg_path = find_library("CoreGraphics")
cg = ctypes.CDLL(cg_path)

# Load CoreFoundation
cf_path = find_library("CoreFoundation")
cf = ctypes.CDLL(cf_path)

kCGEventLeftMouseDown = 1
kCGEventLeftMouseUp = 2
kCGEventRightMouseDown = 3
kCGEventRightMouseUp = 4
kCGHIDEventScrollWheel = 22

kCGMouseEventDeltaX = 0
kCGMouseEventDeltaY = 1

kCGWindowListOptionOnScreenOnly = 1
kCGWindowLevelBelow = -1

# Define function signatures
cf.CFRelease.argtypes = [ctypes.c_void_p]
cf.CFRelease.restype = None

cg.CGEventCreate.argtypes = [ctypes.c_void_p]
cg.CGEventCreate.restype = ctypes.c_void_p

cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double, ctypes.c_double]
cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p

cg.CGEventPost.argtypes = [ctypes.c_int, ctypes.c_void_p]
cg.CGEventPost.restype = None

cg.CGEventSetIntegerValueField.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint64]
cg.CGEventSetIntegerValueField.restype = None

cg.CGEventSetDoubleValueField.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
cg.CGEventSetDoubleValueField.restype = None

kCGHIDEventTap = 0
kCGUEventSuppressionSuspended = 31

PORT = "/dev/cu.usbserial-A5069RR4"
BAUD = 115200
SPEED = 5
RAPIDFIRE = False
RAPIDFIRE_INTERVAL = 0.1
RAPIDFIRE_TOGGLED = True

ser = serial.Serial(PORT, BAUD, timeout=0.05)

def send_mouse_move(dx, dy):
    event = cg.CGEventCreateMouseEvent(None, 0, 0, 0)
    cg.CGEventSetDoubleValueField(event, kCGMouseEventDeltaX, ctypes.c_double(dx))
    cg.CGEventSetDoubleValueField(event, kCGMouseEventDeltaY, ctypes.c_double(dy))
    cg.CGEventPost(kCGHIDEventTap, event)
    cf.CFRelease(event)

def send_left_down():
    event = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, 0, 0)
    cg.CGEventPost(kCGHIDEventTap, event)
    cf.CFRelease(event)

def send_left_up():
    event = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, 0, 0)
    cg.CGEventPost(kCGHIDEventTap, event)
    cf.CFRelease(event)

def send_right_down():
    event = cg.CGEventCreateMouseEvent(None, kCGEventRightMouseDown, 0, 0)
    cg.CGEventPost(kCGHIDEventTap, event)
    cf.CFRelease(event)

def send_right_up():
    event = cg.CGEventCreateMouseEvent(None, kCGEventRightMouseUp, 0, 0)
    cg.CGEventPost(kCGHIDEventTap, event)
    cf.CFRelease(event)

left_was_down = False
right_was_down = False
left_last_fire = 0.0
right_last_fire = 0.0
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
            send_mouse_move(dx, dy)

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
            if state.get("LC") and (now - left_last_fire >= RAPIDFIRE_INTERVAL or not left_was_down):
                send_left_down()
                send_left_up()
                left_last_fire = now
        else:
            if state.get("LC") and not left_was_down:
                send_left_down()
            elif not state.get("LC") and left_was_down:
                send_left_up()

        left_was_down = state.get("LC")

        # Right mouse button
        if RAPIDFIRE:
            now = time.time()
            if state.get("RC") and (now - right_last_fire >= RAPIDFIRE_INTERVAL or not right_was_down):
                send_right_down()
                send_right_up()
                right_last_fire = now
        else:
            if state.get("RC") and not right_was_down:
                send_right_down()
            elif not state.get("RC") and right_was_down:
                send_right_up()

        right_was_down = state.get("RC")

        prev_state = dict(state)

    except Exception as e:
        print("Error:", e)
