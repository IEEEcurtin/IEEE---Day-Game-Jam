#!/usr/bin/env python3
"""
Serial-to-keyboard bridge for Arduino controllers.

Message format (one per line, sent by the Arduino):
    <KEY>1   press and hold the key    e.g. W1, SPACE1, UP1
    <KEY>0   release the key           e.g. W0, SPACE0, UP0

KEY can be any single letter, digit or symbol (W, A, 1, /), or a named key.
See all named keys with:  python serial_keyboard.py --list-keys
"""

import argparse
import importlib.util
import sys
import time

INSTALL_HINT = "Install the libraries with:  python -m pip install pyserial pynput"

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("Missing library 'pyserial'.\n" + INSTALL_HINT)

try:
    from pynput.keyboard import Controller, Key
except Exception as error:
    if importlib.util.find_spec("pynput") is None:
        sys.exit("Missing library 'pynput'.\n" + INSTALL_HINT)
    sys.exit(f"Could not take control of the keyboard: {error}\n"
             "On Linux, log in with an 'X11' / 'Xorg' session instead of Wayland.")

# USB chip makers found on Arduino Unos and common clones
KNOWN_BOARDS = {
    0x2341: "Arduino",
    0x2A03: "Arduino",
    0x1A86: "CH340 clone",
    0x0403: "FTDI clone",
    0x10C4: "CP210x clone",
}

# Extra spellings people are likely to use
ALIASES = {
    "escape": "esc", "return": "enter", "control": "ctrl", "spacebar": "space",
    "del": "delete", "back": "backspace", "arrowup": "up", "arrowdown": "down",
    "arrowleft": "left", "arrowright": "right", "lshift": "shift_l",
    "rshift": "shift_r", "lctrl": "ctrl_l", "rctrl": "ctrl_r",
}


def resolve_key(name):
    """Turn a key name like 'W' or 'SPACE' into something pynput can press."""
    if len(name) == 1:
        return name.lower()
    lowered = name.lower()
    return Key.__members__.get(ALIASES.get(lowered, lowered))


def parse_line(text):
    """'W1' -> ('W', key, True). Returns None if the line isn't valid."""
    if len(text) < 2 or text[-1] not in "01":
        return None
    name = text[:-1].strip().upper()
    if not name:
        return None
    return name, resolve_key(name), text[-1] == "1"


def find_boards():
    ports = list(list_ports.comports())
    boards = [p for p in ports if p.vid in KNOWN_BOARDS]
    return boards, ports


def choose_port():
    """Wait until an Arduino is plugged in, then return its port name."""
    shown_waiting = False
    while True:
        boards, ports = find_boards()
        if len(boards) == 1:
            return boards[0].device
        if len(boards) > 1:
            print("More than one board found:")
            for i, p in enumerate(boards, 1):
                print(f"  {i}. {p.device}  ({KNOWN_BOARDS[p.vid]})")
            choice = input("Type the number of the one to use: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(boards):
                return boards[int(choice) - 1].device
            continue
        if not shown_waiting:
            print("Waiting for an Arduino to be plugged in...")
            if ports:
                print("  (Not recognised automatically? Run again with --port "
                      "and one of these: " + ", ".join(p.device for p in ports) + ")")
            shown_waiting = True
        time.sleep(1)


def connection_hint(error):
    message = str(error).lower()
    if "permission" in message and sys.platform.startswith("linux"):
        return ("Linux blocked access to the port. Run:  sudo usermod -aG dialout $USER  "
                "then log out and back in.")
    if "denied" in message or "busy" in message or "permission" in message:
        return "Another program is using the board. Close the Arduino Serial Monitor."
    return "Check the cable, or unplug and replug the board."


def run(port_arg, baud):
    keyboard = Controller()
    held = {}

    def release_all():
        for key in held.values():
            try:
                keyboard.release(key)
            except Exception:
                pass
        held.clear()

    while True:
        port = port_arg or choose_port()
        try:
            with serial.Serial(port, baud, timeout=0.1) as board:
                print(f"Connected to {port}. Click on the game window to play. "
                      "Press Ctrl+C here to stop.")
                while True:
                    raw = board.readline()
                    if not raw:
                        continue
                    text = raw.decode("ascii", errors="ignore").strip()
                    if not text:
                        continue

                    parsed = parse_line(text)
                    if parsed is None:
                        print(f"  ignored '{text}' (expected something like W1 or W0)")
                        continue
                    name, key, pressed = parsed
                    if key is None:
                        print(f"  unknown key '{name}' (see --list-keys)")
                        continue

                    if pressed and name not in held:
                        keyboard.press(key)
                        held[name] = key
                    elif not pressed:
                        keyboard.release(held.pop(name, key))
                    print(f"  {name} {'down' if pressed else 'up'}")
        except serial.SerialException as error:
            release_all()
            print(f"Lost connection to {port}. {connection_hint(error)}")
            time.sleep(2)
        except KeyboardInterrupt:
            release_all()
            print("\nStopped.")
            return


def main():
    parser = argparse.ArgumentParser(description="Turn Arduino serial messages into key presses.")
    parser.add_argument("--port", help="board port, e.g. COM3 or /dev/ttyACM0 (found automatically if left out)")
    parser.add_argument("--baud", type=int, default=9600, help="must match Serial.begin() (default 9600)")
    parser.add_argument("--list-keys", action="store_true", help="show all named keys and exit")
    args = parser.parse_args()

    if args.list_keys:
        print("Single characters: any letter, digit or symbol, e.g. W, A, 1, /")
        print("Named keys:", ", ".join(sorted(k.upper() for k in Key.__members__)))
        print("Also accepted:", ", ".join(sorted(a.upper() for a in ALIASES)))
        return

    run(args.port, args.baud)


if __name__ == "__main__":
    main()
