# Arduino Uno → MacBook Keyboard Setup

Basically, this setup lets the Arduino UNO send keyboard commands to the MacBook through Python.

> Arduino UNO → USB → Python → MacBook keyboard

---

## 1. Download Python

Download the latest macOS installer from:

[https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/)

Install it normally.

---

## 2. Download Arduino IDE

Download the latest Arduino IDE for macOS:

[https://support.arduino.cc/hc/en-us/articles/360019833020-Download-and-install-Arduino-IDE](https://support.arduino.cc/hc/en-us/articles/360019833020-Download-and-install-Arduino-IDE)

### If using an Apple chip

For M1/M2/M3/etc. Macs, make sure you download the version that says:

`arm64`

**NOT:**

`64bit`

- `arm64` → Apple Silicon
    
- `64bit` → Intel
    

---

## 3. Open Arduino IDE

Open Arduino IDE after installing it.

If the UNO is plugged in, the IDE might download/set up a bunch of stuff automatically, so don't worry if it does.

If it asks you to install the **xcrun Command Line Developer Tools**, click **Install**.

These are needed for compiling the Arduino code.

---

## 4. Test the Arduino

Plug in the Arduino UNO and upload this test code:

```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println("HELLO");
  delay(1000);
}
```

Open the **Serial Monitor** and set the baud rate to:

`9600`

You should see:

```text
HELLO
HELLO
HELLO
HELLO
```

every second.

If this works, the Arduino + IDE are good.

---

## 5. Check Python

Open **Terminal** and run:

```bash
python3 --version
```

You should get a Python version number.

---

## 6. Download the Python libraries

In Terminal, run:

```bash
python3 -m pip install pyserial pynput
```

These are the two libraries needed by `serial_keyboard.py`.

- `pyserial` → lets Python communicate with the Arduino
    
- `pynput` → lets Python control the Mac keyboard
    

---

## 7. Put `serial_keyboard.py` somewhere easy to find

Have the `serial_keyboard.py` file downloaded and put it somewhere easy to find.

The **Desktop** is probably easiest.

For example:

```text
Desktop/
└── serial_keyboard.py
```

---

## 8. Navigate to the file using Terminal

If the file is on the Desktop:

```bash
cd ~/Desktop
```

Then:

```bash
ls
```

Check that you can see:

```text
serial_keyboard.py
```

If it's there, you're good.

> If you put it somewhere else, `cd` to that folder instead.

---

## 9. Test that the Python file works

Run:

```bash
python3 serial_keyboard.py --list-keys
```

It should show something like:

```text
Single characters: any letter, digit or symbol...
Named keys: ...
Also accepted: ...
```

If you get this, the Python file is working.

---

## 10. Allow keyboard control on macOS

macOS might block Python from controlling the keyboard.

Go to:

**System Settings → Privacy & Security → Accessibility**

Then:

1. Allow changes if needed.
    
2. Find **Terminal**.
    
3. Turn it **ON**.
    

If Terminal isn't there:

**+ → Applications → Utilities → Terminal**

Then add it and turn it on.

---

## 11. Plug in the Arduino UNO

Plug the UNO into the MacBook.

In Arduino IDE, check:

**Tools → Board**

Make sure the board is:

**Arduino Uno**

Then check:

**Tools → Port**

Select the port belonging to the UNO.

It will probably look something like:

```text
/dev/cu.usbmodemXXXX
```

> **Important:** Close the Arduino Serial Monitor before running the Python file. Python needs to use the Arduino's serial connection.

---

## 12. Run the serial keyboard

Go back to Terminal.

Make sure you're still in the folder containing `serial_keyboard.py`.

Run:

```bash
python3 serial_keyboard.py
```

You should see something like:

```text
Connected to /dev/cu.usbmodemXXXX.
Click on the game window to play.
Press Ctrl+C here to stop.
```

At this point, the Arduino can send commands such as:

```text
W1
W0
A1
A0
SPACE1
SPACE0
```

The Python program turns these into actual keyboard presses.

### Example

```text
W1 → press/hold W
W0 → release W
```

---

## 13. Stopping the program

To stop the Python program:

**Control + C**

Not:

**Command + C**

So:

```text
⌃ Control + C
```

The program should stop and release any keys that were being held.

---

# Quick Setup Summary

```text
1. Install Python
        ↓
2. Install Arduino IDE
        ↓
3. Plug in UNO
        ↓
4. Test Arduino with HELLO code
        ↓
5. Check Python with python3 --version
        ↓
6. Install pyserial + pynput
        ↓
7. Put serial_keyboard.py somewhere easy to find
        ↓
8. Navigate to it with cd
        ↓
9. Test with --list-keys
        ↓
10. Give Terminal Accessibility permission
        ↓
11. Select Arduino Uno + correct port
        ↓
12. Run python3 serial_keyboard.py
        ↓
13. Arduino commands → Mac keyboard
```

---

## Important

The Arduino messages need to be sent as **one complete command per line**:

```text
W1
W0
```

**NOT:**

```text
W
1
```

Otherwise Python will ignore them.
