# ESP32 Bluetooth Keyboard Setup Guide

IEEE Curtin Student Branch · Game Jam

This guide turns an ESP32 board into a wireless keyboard. When set up, pressing a button on the board types a key on your laptop, just like a normal Bluetooth keyboard. You can then connect sensors to it and use them to control any game.

## What you need

- An ESP32 board (the regular ESP32 used with the **ESP32 Dev Module** setting).
- A USB cable that carries **data**. Many cheap cables only charge, and your computer won't detect the board with those.
- A laptop with Bluetooth and Arduino IDE installed (the free app from arduino.cc).
- An internet connection for the downloads in Steps 1 to 3.

> **Important:** this guide uses **older, specific versions** of two downloads: ESP32 add-on version **2.0.17** and keyboard library version **0.3.2-beta**. Newer versions don't work together and cause errors. Follow the version numbers exactly.

## Step 1: Tell Arduino IDE where to find ESP32 boards

- Open Arduino IDE.
- Go to **File → Preferences** (on a Mac: **Arduino IDE → Settings**).
- Find the box labelled **Additional boards manager URLs** and paste this link into it:

```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

- Click **OK**.

## Step 2: Install the ESP32 add-on (version 2.0.17)

- Click the **Boards Manager** icon on the left sidebar (the second icon, which looks like a circuit board).
- Type **esp32** in the search box.
- Find **esp32 by Espressif Systems**. In its version dropdown, choose **2.0.17**, then click **Install**.
- This is a large download and may take several minutes. Wait until it shows "2.0.17 installed".

> **Do not click UPDATE.** After installing, Arduino IDE will show an **UPDATE** button and may pop up messages saying updates are available. Ignore them. Updating to version 3 or later breaks the keyboard library.

## Step 3: Install the Bluetooth keyboard library (version 0.3.2-beta)

- In your web browser, open this page:

```
https://github.com/T-vK/ESP32-BLE-Keyboard/releases
```

- Find the release named **ESP32-BLE-Keyboard v0.3.2-beta**. Under its **Assets**, download the **.zip** file. **Don't unzip it.**
- Use this exact version. Older versions (such as 0.3.0) stop typing on Windows after the board restarts.
- Back in Arduino IDE, go to **Sketch → Include Library → Add .ZIP Library**, and select the file you downloaded.
- A message at the bottom should confirm the library was installed.

## Step 4: Connect the board and choose the right settings

- Plug the ESP32 into your laptop with the data cable.
- Go to **Tools → Board → esp32** and choose **ESP32 Dev Module**.
- Go to **Tools → Port** and select the port that appeared when you plugged in the board. On Windows it looks like **COM** followed by a number (for example, **COM4**). The top bar should then show **ESP32 Dev Module** with that port underneath.
- **If no port appears**, see "No port shows up" in the troubleshooting section.

## Step 5: Upload the test code

This code turns the board's built-in **BOOT** button into the spacebar, so you can test it without wiring anything.

- Delete everything in the Arduino IDE editor window and paste in this code:

```cpp
#include <BleKeyboard.h>

BleKeyboard bleKeyboard("Team1");   // change the name for each team
const int buttonPin = 0;            // BOOT button on the board
bool wasPressed = false;

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  bleKeyboard.begin();
}

void loop() {
  if (bleKeyboard.isConnected()) {
    bool pressed = (digitalRead(buttonPin) == LOW);
    if (pressed && !wasPressed) bleKeyboard.press(' ');
    if (!pressed && wasPressed) bleKeyboard.release(' ');
    wasPressed = pressed;
  }
  delay(10);
}
```

- Change **"Team1"** to your own team name, so your board doesn't get mixed up with other teams' boards.
- Click the **Upload** button (the right-pointing arrow at the top left).
- If it gets stuck on **"Connecting......"**, press and hold the **BOOT** button on the board until the upload starts, then let go.
- The upload has worked when the bottom panel says **"Hard resetting via RTS pin"**. Then press the board's **EN** or **RST** button once to make sure the new code starts running.

## Step 6: Pair it with your laptop and test

- **Windows:** open **Settings → Bluetooth & devices → Add device → Bluetooth**, and select your team name.
- **Mac:** open **System Settings → Bluetooth**, and click **Connect** next to your team name.
- Open Google Chrome and type `chrome://dino` into the address bar.
- Press the **BOOT** button on the board. **If the dinosaur jumps, everything is working.**

## Using your own button or sensor

To use an external button, connect one leg to a free pin (for example, **pin 4**) and the other leg to **GND** (the ground pin). Then change `buttonPin = 0` to `buttonPin = 4` in the code and upload again.

To send a different key, replace `' '` in both the **press** and **release** lines. Some useful keys:

| Key | What to write in the code |
|---|---|
| Letter or number | `'a'`, `'w'`, `'1'` (in single quotes) |
| Arrow keys | `KEY_UP_ARROW`, `KEY_DOWN_ARROW`, `KEY_LEFT_ARROW`, `KEY_RIGHT_ARROW` |
| Enter | `KEY_RETURN` |
| Escape | `KEY_ESC` |

> **Wiring rule:** the ESP32 runs on 3.3 volts. **Power every sensor from the 3V3 pin**, not the 5V or VIN pin. This keeps the sensor's signal at a safe level for the board.
>
> **Piezo discs:** a hard hit can create a voltage spike. Connect a **1 MΩ resistor** across the piezo's two wires and a **10 kΩ resistor** between the piezo and the ESP32 pin. CuRoSo will provide these resistors.

## Troubleshooting

| Problem | What to do |
|---|---|
| No port shows up in Tools → Port | Try a different USB cable, as yours may be charge-only. If that doesn't help, look at the small chip next to the USB port. If it says **CH340**, install the CH340 driver. If it says **CP2102**, install the CP210x driver. Then unplug and replug the board. |
| Red error text when uploading, mentioning "std::string" or "String" | The wrong ESP32 add-on version is installed. Go back to Step 2 and install version **2.0.17**. |
| "Library ESP32 BLE Keyboard is already installed, but with a different version" | Close Arduino IDE. Check **File → Preferences → Sketchbook location**, open that folder, go into **libraries**, and delete the old ESP32_BLE_Keyboard folder. Then install the .zip again. |
| Upload stuck on "Connecting......" | Hold the **BOOT** button on the board while it's connecting, then release it once the upload starts. |
| Team name doesn't appear in the Bluetooth list | Press the **EN** or **RST** button on the board, then close and reopen the Add device window. On Windows 11, also go to **Settings → Bluetooth & devices → Devices** and set **Bluetooth devices discovery** to **Advanced**. |
| Paired before, but it won't reconnect | Check you installed library version **0.3.2-beta**. If so, remove the device from your laptop's Bluetooth list, press **EN**/**RST** on the board, and pair it again. |
| Paired, but pressing the button does nothing | Click inside the game window first so it's active. Check that **buttonPin** is set to **0** for the BOOT button, or to the pin your own button is wired to. |
