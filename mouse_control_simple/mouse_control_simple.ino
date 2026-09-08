#include <Mouse.h>

const int BUTTON_L = 2;
const int BUTTON_R = 3;
const int BUTTON_U = 4;
const int BUTTON_D = 5;
const int BUTTON_LC = 6;
const int BUTTON_RC = 7;

const int SPEED = 5;
const unsigned long RAPIDFIRE_INTERVAL = 100; // ms

unsigned long left_last_fire = 0;
unsigned long right_last_fire = 0;
bool leftWasDown = false;
bool rightWasDown = false;
bool rapidFire = false;
bool rapidFireToggled = true;

void setup() {
  pinMode(BUTTON_L, INPUT_PULLUP);
  pinMode(BUTTON_R, INPUT_PULLUP);
  pinMode(BUTTON_U, INPUT_PULLUP);
  pinMode(BUTTON_D, INPUT_PULLUP);
  pinMode(BUTTON_LC, INPUT_PULLUP);
  pinMode(BUTTON_RC, INPUT_PULLUP);
  Mouse.begin();
}

void loop() {
  bool l = digitalRead(BUTTON_L) == LOW;
  bool r = digitalRead(BUTTON_R) == LOW;
  bool u = digitalRead(BUTTON_U) == LOW;
  bool d = digitalRead(BUTTON_D) == LOW;
  bool lc = digitalRead(BUTTON_LC) == LOW;
  bool rc = digitalRead(BUTTON_RC) == LOW;

  int dx = 0;
  int dy = 0;

  if (l) dx -= SPEED;
  if (r) dx += SPEED;
  if (u) dy -= SPEED;
  if (d) dy += SPEED;

  if (dx != 0 || dy != 0) {
    Mouse.move(dx, dy, 0);
  }

  // Toggle rapidfire: all 4 directions pressed together
  bool allDirection = l && r && u && d;
  static bool prevAllDirection = false;
  if (allDirection && !prevAllDirection && rapidFireToggled) {
    rapidFire = !rapidFire;
    rapidFireToggled = false;
  } else if (!allDirection) {
    rapidFireToggled = true;
  }

  unsigned long now = millis();

  // Left mouse button
  if (rapidFire) {
    if (lc && (now - left_last_fire >= RAPIDFIRE_INTERVAL || !leftWasDown)) {
      Mouse.press(MOUSE_LEFT);
      delay(5);
      Mouse.release(MOUSE_LEFT);
      left_last_fire = now;
    }
  } else {
    if (lc && !leftWasDown) {
      Mouse.press(MOUSE_LEFT);
    } else if (!lc && leftWasDown) {
      Mouse.release(MOUSE_LEFT);
    }
  }
  leftWasDown = lc;

  // Right mouse button
  if (rapidFire) {
    if (rc && (now - right_last_fire >= RAPIDFIRE_INTERVAL || !rightWasDown)) {
      Mouse.press(MOUSE_RIGHT);
      delay(5);
      Mouse.release(MOUSE_RIGHT);
      right_last_fire = now;
    }
  } else {
    if (rc && !rightWasDown) {
      Mouse.press(MOUSE_RIGHT);
    } else if (!rc && rightWasDown) {
      Mouse.release(MOUSE_RIGHT);
    }
  }
  rightWasDown = rc;

  delay(10);
}
