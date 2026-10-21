"""Shared helpers that let the Python games run inside the IEEE arcade.

The arcade launcher sets ARCADE_RESULT to a file path. When it is set, a game
runs one round full screen, then writes its score to that file and exits.
Without it, every helper falls back to normal standalone behaviour.
"""
import json
import os
import re
import sys
import time

import pygame

RESULT_PATH = os.environ.get("ARCADE_RESULT")
ACTIVE = bool(RESULT_PATH)
LOG_PATH = os.environ.get("ARCADE_LOG")

IDLE_SECONDS = 60       # nobody touches anything for this long -> back to the menu
QUIT_HOLD_SECONDS = 2   # helpers hold Esc this long to leave a game
END_SCREEN_SECONDS = 2.5  # how long a game-over screen stays up before the name screen

# USB-serial chips used by ESP32 and Arduino boards
KNOWN_USB_VIDS = {
    0x10C4: "CP210x", 0x1A86: "CH340", 0x0403: "FTDI",
    0x303A: "Espressif", 0x2341: "Arduino", 0x2A03: "Arduino",
}


def log(*parts):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(p) for p in parts)
    # In the arcade, printed output already goes to the arcade log
    print(line, flush=True)


def open_window(size, caption, flags=0):
    """Full screen (scaled, keeps the game's own resolution) in the arcade, normal window otherwise."""
    pygame.display.set_caption(caption)
    if ACTIVE:
        screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.SCALED)
        pygame.mouse.set_visible(False)
        bring_to_front()
        return screen
    return pygame.display.set_mode(size, flags)


def bring_to_front():
    """Windows only lets the active app hand over focus, so tap Alt first (a standard workaround)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get("window")
        if not hwnd:
            return
        user32 = ctypes.windll.user32
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
    except Exception as e:
        log("bring_to_front failed:", e)


def open_controller(baud, expect=None, listen_seconds=2.5):
    """Find a USB controller without knowing its COM port.

    Tries every USB serial device (ESP32 / Arduino chips first). If `expect` is a
    regex, the port whose messages match it wins. Otherwise the first USB serial
    device is used. Returns an open serial.Serial, or None for keyboard only.
    """
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        log("pyserial missing, keyboard only")
        return None

    # Bluetooth and virtual COM ports have no USB vendor ID and can hang when opened
    ports = [p for p in list_ports.comports() if p.vid is not None]
    ports.sort(key=lambda p: 0 if p.vid in KNOWN_USB_VIDS else 1)
    if not ports:
        log("no USB controller found, keyboard only")
        return None

    pattern = re.compile(expect) if expect else None
    fallback = None
    for p in ports:
        try:
            ser = serial.Serial(p.device, baud, timeout=0.05)
        except Exception as e:
            log("could not open", p.device, e)
            continue
        if pattern is None:
            log("controller on", p.device, p.description)
            return ser
        # ESP32 boards reboot when the port opens, so give them a moment to start talking
        deadline = time.time() + listen_seconds
        while time.time() < deadline:
            try:
                line = ser.readline().decode(errors="ignore").strip()
            except Exception:
                break
            if line and pattern.search(line):
                log("controller on", p.device, p.description)
                if fallback:
                    fallback.close()
                return ser
        if fallback is None and p.vid in KNOWN_USB_VIDS:
            fallback = ser
        else:
            ser.close()
    if fallback:
        log("controller probably on", fallback.port, "(no messages yet)")
    else:
        log("no matching controller, keyboard only")
    return fallback


class Session:
    """Tracks the hidden Esc-hold exit and the idle timeout. Does nothing outside the arcade."""

    def __init__(self):
        self.last_input = time.time()
        self.esc_down_at = None

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
            self.last_input = time.time()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.esc_down_at = time.time()
        elif event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            self.esc_down_at = None

    def note_input(self):
        self.last_input = time.time()

    def exit_reason(self):
        """'quit' or 'idle' when the game should close, otherwise None."""
        if not ACTIVE:
            return None
        now = time.time()
        if self.esc_down_at and now - self.esc_down_at >= QUIT_HOLD_SECONDS:
            return "quit"
        if now - self.last_input >= IDLE_SECONDS:
            return "idle"
        return None

    def draw_exit_hint(self, surface):
        """Small bar that fills while Esc is held, so helpers know it is working."""
        if not ACTIVE or not self.esc_down_at:
            return
        held = min(1.0, (time.time() - self.esc_down_at) / QUIT_HOLD_SECONDS)
        w, h = surface.get_size()
        bar = pygame.Rect(w // 2 - 150, h - 40, 300, 16)
        pygame.draw.rect(surface, (0, 0, 0), bar.inflate(8, 8))
        pygame.draw.rect(surface, (0, 98, 155), (bar.x, bar.y, int(bar.w * held), bar.h))
        pygame.draw.rect(surface, (255, 255, 255), bar, 2)


def finish(score=None, reason="over", **extra):
    """Tell the arcade how the round went, then close the game."""
    if ACTIVE:
        data = {"score": score, "reason": reason}
        data.update(extra)
        try:
            with open(RESULT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError as e:
            log("could not write result:", e)
        log("finished:", data)
    pygame.quit()
    sys.exit(0)


def best_entry():
    """Top arcade leaderboard entry as (name, score), so games can show the record to beat."""
    raw = os.environ.get("ARCADE_BEST", "")
    if "," in raw:
        name, score = raw.rsplit(",", 1)
        try:
            return name, int(score)
        except ValueError:
            pass
    return None
