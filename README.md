# 👾 IEEE DAY GAME JAM: "You Are The Controller" 🎮

![IEEE](https://img.shields.io/badge/IEEE-Curtin%20Dubai-blue)
![Event](https://img.shields.io/badge/Event-Game%20Jam-red)
![Date](https://img.shields.io/badge/Date-Oct%208%202026-yellow)
![Teams](https://img.shields.io/badge/Teams-8%20teams%20of%20up%20to%204-green)
![Status](https://img.shields.io/badge/Status-Registration%20Open-brightgreen)
![Visitors](https://komarev.com/ghpvc/?username=IEEEcurtin&label=Repo%20Views&color=0e75b6&style=flat)

<img src="poster_animated (1).gif" alt="IEEE Day Game Jam poster" width="100%">

Welcome to the official repository for the **IEEE Day Game Jam**, hosted by the IEEE Curtin University Dubai Student Branch, with the Curtin Robotics Society (CuRoSo) as technical partner.

This repository is the single source of information for participants. It holds the setup guide, the Bluetooth library, the component guide (what each part does and how to use it), and everything teams need before and after the event.

## 📅 Event Details
* **Date:** Thursday 8 October 2026
* **Time:** 11:30 to 15:30 (Dubai time)
* **Venue:** Curtin University Dubai, Block 12, Room 12.2
* **Theme:** You Are The Controller
* **Format:** In person
* **Capacity:** 32 students: 8 teams of up to 4
* **Who can join:** Engineering, IT, and Cybersecurity students. The only requirement is staying for the full four hours. IEEE membership is not required.
* **Registration:** [https://tally.so/r/2E0GQ9](https://tally.so/r/2E0GQ9)
* **Registration closes:** 5 October 2026

## 🎯 How the Game Jam Works
**The game.** Each team programs its own game on a laptop, using any engine that can be uploaded to itch.io, such as Python (Pygame), Unity, or web (HTML and JavaScript). Web (HTML) games are the easiest to upload. Games are arcade style: fast-paced, competitive, and replayable, so players want to play again and challenge their friends.

**The controller.** Each team builds a physical controller for its game. An ESP32 (a small programmable circuit board with built-in Bluetooth) reads the controller's sensors and connects to the laptop over Bluetooth, acting like a wireless keyboard, so the game only needs to respond to key presses. Teams can also use the laptop's camera as their sensor instead. The body of the controller can be made from anything, such as cardboard, bottles, tape, and hot glue.

**What teams work on during the jam:**
* Programming the game
* Connecting the game to the controller
* Game art
* Building the controller and any arcade parts
* Anything else that fits in the time

## 🎓 Objectives
1. Give the branch and CuRoSo an activity that everyone can enjoy and socialise in.
2. Build technical skills across the branch's members.
3. Create projects that can be shown at exhibition events.
4. Serve as a test run for bigger future events, such as a version of this game jam for high school students.

## 🛠️ The Hardware Kit
All sensors and parts are laid out on a table at the front of the room. Teams take what they need, when they need it, instead of receiving a fixed kit.

**Sensors**
* **Gyro and accelerometer sensors:** Detect tilting, swinging, and shaking.
* **Piezo discs:** Detect stomps, taps, and knocks.
* **IR sensors:** Detect waving, blocking, and nearby movement.
* **Ultrasonic sensors:** Measure how far away a hand, body, or object is.
* **Sound sensors:** Detect shouts and claps.
* **Push buttons and limit switches:** Detect presses, or when a moving part hits a set point.

**Controller materials**
* **ESP32 boards:** The brain of each controller, reading sensors and sending inputs to the laptop over Bluetooth.
* **Jumper wires, resistors, and breadboards:** Connect sensors to the ESP32 without soldering.
* **Micro-USB cables:** Power and program the ESP32 from a laptop.
* **Cardboard, bottles, and paper:** Build the body of the controller and any arcade parts.
* **Tape and hot glue guns:** Hold the build together.
* **Scissors and box cutters:** Cut building materials to shape.

## 💻 The Tech Stack
* **Game engines:** Any engine that can be uploaded to itch.io, such as Python (Pygame), Unity, or web (HTML and JavaScript). Web (HTML) games are the easiest to upload.
* **Communication:** Bluetooth, with the ESP32 acting like a wireless keyboard. Teams can also use the laptop's camera as their sensor instead.
* **Laptops:** Participants bring their own laptops. Each team needs at least one laptop that can run the Arduino IDE (the free program used to load code onto the ESP32), preferably Windows with Bluetooth, and with permission to install software.

## 🚀 Before the Event
1. **Register:** Register through the Tally form by 5 October 2026, either as a team of up to 4 or solo. Solo participants are grouped into balanced teams based on skill levels.
2. **Join the WhatsApp group:** After registering, join the participant WhatsApp group, which is only for registered participants. Council members answer questions there.
3. **Install software:** Install the Arduino IDE, ESP32 Board Manager, and your preferred game engine.
4. **Plan your game:** Read the Inspiration Manual in the `/docs` folder and start brainstorming. Teams are encouraged to build their game before the day, so the jam itself can focus on the controller. However, teams are not required to make their games beforehand.

## 📅 Event Day Schedule

<table style="width: 100%; border-collapse: collapse; font-family: 'Courier New', monospace; font-size: 16px; color: #fff7d6; background-color: #101f4a; border: 4px solid #2c4390;">
  <thead>
    <tr style="background-color: #ff3d6e; color: #ffffff; font-family: 'Courier New', monospace; font-size: 13px;">
      <th style="padding: 12px; border: 3px solid #2c4390; text-align: left;">TIME</th>
      <th style="padding: 12px; border: 3px solid #2c4390; text-align: left;">SEGMENT</th>
      <th style="padding: 12px; border: 3px solid #2c4390; text-align: left;">WHAT HAPPENS</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 12px; border: 3px solid #2c4390; color: #ffd23f; white-space: nowrap;">11:30 - 12:00</td>
      <td style="padding: 12px; border: 3px solid #2c4390; color: #4cd04c; font-weight: bold;">Opening and info session</td>
      <td style="padding: 12px; border: 3px solid #2c4390;">Rules and safety briefing, components walkthrough, live sensor demos, and a showcase of possible projects, followed by Q&amp;A</td>
    </tr>
    <tr style="background-color: #0d1a3d;">
      <td style="padding: 12px; border: 3px solid #2c4390; color: #ffd23f; white-space: nowrap;">12:00 - 14:30</td>
      <td style="padding: 12px; border: 3px solid #2c4390; color: #4cd04c; font-weight: bold;">Game jam</td>
      <td style="padding: 12px; border: 3px solid #2c4390;">Teams collect components from the front table as needed, build and wire their controllers, program the ESP32, and connect it to their game</td>
    </tr>
    <tr>
      <td style="padding: 12px; border: 3px solid #2c4390; color: #ffd23f; white-space: nowrap;">14:30 - 15:00</td>
      <td style="padding: 12px; border: 3px solid #2c4390; color: #4cd04c; font-weight: bold;">Game exhibition</td>
      <td style="padding: 12px; border: 3px solid #2c4390;">Teams play each other's games and vote for the awards in a poll</td>
    </tr>
    <tr style="background-color: #0d1a3d;">
      <td style="padding: 12px; border: 3px solid #2c4390; color: #ffd23f; white-space: nowrap;">15:00 - 15:30</td>
      <td style="padding: 12px; border: 3px solid #2c4390; color: #4cd04c; font-weight: bold;">Awards and closing</td>
      <td style="padding: 12px; border: 3px solid #2c4390;">Winners announced on screen with team photos, then a group photo</td>
    </tr>
  </tbody>
</table>

## 🏆 Awards & Voting
Each participant votes for one team per award and cannot vote for their own team. The awards are:

* **Most Innovative:** The group that made us say "Wait… that's actually a good idea."
* **Most Brainrot Game:** The game that permanently damaged everyone's attention span.
* **Best Visuals & Aesthetics:** The game that looked suspiciously more professional than expected.
* **Most Chaotic Gameplay:** The game where nobody knew what was happening, including the developers.
* **Best Bug / Feature Award:** The team that proved sometimes the bug IS the game.
* **Most Addictive Game:** The game that turned "just one more round" into 45 minutes.
* **Most Unexpected Game:** The concept nobody asked for, but everyone enjoyed.
* **Best Overall Vibes:** The group that understood the assignment and brought immaculate vibes.

## 🎉 After the Event
* **Submission:** Teams submit their finished game and their controller's Arduino code to [itch.io](https://itch.io) (a free website for sharing independent games), where anyone can play them.
* **Certificates:** Every participant receives an official certificate of participation from the branch, using the name given at registration.

## ⚠️ Safety Rules
* **Scissors and box cutters:** Each team receives its own scissors and box cutters and must keep them in a safe spot at its table. They must never be left on the floor or lying around.
* **Protecting the venue:** Nothing may be taped, glued, or attached to the venue, including floors, walls, glass, tables, and chairs. Builds may only use disposable or recyclable materials. Teams are liable for any damage they cause to the venue.

Both rules are announced before the event starts and strictly enforced.

## 🤝 Code of Conduct
We are committed to providing a friendly, safe, and welcoming environment for all. Please be respectful to your fellow jammers, mentors, and organisers.

## 📞 Contact
**Email:** curtin.dubai.ieee@gmail.com

---
**Let the games begin!** 🕹️
