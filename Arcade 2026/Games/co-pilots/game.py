# ================================================================
# CO-PILOTS - BEGINNER-FRIENDLY CODE GUIDE
# ================================================================
#
# HOW TO READ THIS FILE:
# Python runs this file from TOP to BOTTOM.
#
# The game is roughly divided into these parts:
#
# 1. IMPORTS
#    Loads libraries such as pygame, random, math, etc.
#
# 2. CONSTANTS / SETTINGS
#    Screen size, FPS, colors, difficulty settings, and other values
#    that we want to reuse throughout the game.
#
# 3. INPUT CLASSES
#    KeyboardInput reads keyboard controls.
#    SerialInput can read controls from the ESP32.
#
# 4. HELPER FUNCTIONS
#    Small reusable jobs such as drawing text and playing sounds.
#
# 5. GAME CLASS
#    This is the main part of the program.
#    It stores the game's variables and contains functions for:
#       - resetting a run
#       - creating obstacles
#       - updating movement/game logic
#       - detecting collisions
#       - drawing everything
#
# 6. MAIN GAME LOOP
#    Repeats about 60 times every second:
#       INPUT -> UPDATE -> DRAW
#
# IMPORTANT PYTHON IDEAS USED IN THIS PROJECT:
#
# self.variable
#     A variable belonging to the current Game object.
#     Example: self.score means "this game's score".
#
# def function_name(...):
#     Creates a function. A function is reusable code that performs a job.
#
# if / elif / else
#     Makes decisions.
#
# for
#     Repeats code for objects in a collection, such as every obstacle.
#
# dt
#     "Delta time" = how much time passed since the previous frame.
#     Multiplying movement by dt keeps movement similar on different PCs.
#
# random.uniform(a, b)
#     Gives a random decimal number between a and b.
#
# random.choice([...])
#     Randomly chooses one item from a list.
#
# ================================================================

"""CO-PILOTS - two-player arcade game.
Keyboard:  python game.py          (P1: arrows L/R, P2: W/S, boost: SPACE)
ESP32:     python game.py COM3     (or /dev/ttyUSB0). 'auto' finds it by listening on each USB port.
"""
import sys, math, random, threading, os
import pygame
# Arcade helpers (controller auto-detect, full screen, scores). The game still
# runs on its own if the arcade folder is missing.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "system", "pylib"))
try:
    import arcade_mode
except ImportError:
    arcade_mode = None
ARCADE = arcade_mode is not None and arcade_mode.ACTIVE
W, H, FPS = 960, 540, 60
CYAN, MAG, YEL, WHITE = (0, 240, 255), (255, 40, 200), (255, 230, 0), (240, 240, 255)
BG = (8, 4, 24)
HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")

# ------------------------------------------------
# EXTERNAL GAME AUDIO
# ------------------------------------------------
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")
BACKGROUND_FILE = os.path.join(SOUND_DIR, "background.mp3")
CRASH_FILE = os.path.join(SOUND_DIR, "crash.mpeg")
AFTER_CRASH_FILE = os.path.join(SOUND_DIR, "after_crash.mpeg")

# ---------- difficulty settings ----------
# ------------------------------------------------
# DIFFICULTY SYSTEM
# ------------------------------------------------
# A dictionary lets us store several settings under one difficulty name.
# Example:
# DIFFICULTIES["EASY"]["speed"] gives us EASY's starting speed.
#
# speed          = starting game speed
# gap_bonus      = extra space added to/subtracted from obstacle gaps
# spawn_distance = how far the game travels before making another obstacle
DIFFICULTIES = {
    "EASY":   {"speed": 150.0, "gap_bonus": 110, "spawn_distance": 360},
    "MEDIUM": {"speed": 240.0, "gap_bonus": 0,   "spawn_distance": 230},
    "HARD":   {"speed": 290.0, "gap_bonus": -35, "spawn_distance": 190},
}
DIFFICULTY_ORDER = ["EASY", "MEDIUM", "HARD"]

# ---------- inputs: both return (tilt -1..1, up, down, boost) ----------
# ------------------------------------------------
# KEYBOARD CONTROLS
# ------------------------------------------------
# This class converts keyboard buttons into simple values that Game.update()
# can understand. Keeping input separate makes ESP32 support easier.
class KeyboardInput:
    def poll(self):
        k = pygame.key.get_pressed()
        return float(k[pygame.K_RIGHT] - k[pygame.K_LEFT]), k[pygame.K_w], k[pygame.K_s], k[pygame.K_SPACE]
    def send(self, msg):
        pass
# ------------------------------------------------
# ESP32 / SERIAL CONTROLS
# ------------------------------------------------
# This class does the same job as KeyboardInput, but reads data sent through
# a serial/COM port by the physical controller.
class SerialInput:
    def __init__(self, port):
        import serial
        if isinstance(port, str):
            self.ser = serial.Serial(port, 115200, timeout=0.1)
        else:
            self.ser = port  # already opened by find_controller()
            self.ser.timeout = 0.1
        self.state = (0.0, 0, 0, 0)
        threading.Thread(target=self._read, daemon=True).start()
    def _read(self):
        while True:
            try:
                p = self.ser.readline().decode().strip().split(",")
                if len(p) == 4:
                    self.state = (max(-1, min(1, float(p[0]))), int(p[1]), int(p[2]), int(p[3]))
            except Exception:
                pass
    def poll(self):
        k = pygame.key.get_pressed()  # keyboard still works as a backup
        t, u, d, b = self.state
        return t, u or k[pygame.K_w], d or k[pygame.K_s], b or k[pygame.K_SPACE]
    def send(self, msg):
        try:
            self.ser.write((msg + "\n").encode())
        except Exception:
            pass
# Looks for the ESP32 on every USB port by listening for "tilt,up,down,boost" lines.
# Returns None if no controller answers, so the keyboard is used instead.
def find_controller():
    if arcade_mode is None:
        return None
    return arcade_mode.open_controller(115200, expect=r"^-?\d+(\.\d+)?,[01],[01],[01]$")
# ---------- helpers ----------
pygame.init()

# ------------------------------------------------
# PROJECTOR / FULLSCREEN DISPLAY
# ------------------------------------------------
# The GAME itself still thinks it is 960x540 (W x H).
# We draw everything onto "canvas" at that fixed size.
#
# At the very end of each frame, we scale that canvas to whatever
# window/projector size is being used. This means we do NOT have to
# rewrite all the positions, obstacle sizes, or UI coordinates.
fullscreen = False
if arcade_mode is not None:
    screen = arcade_mode.open_window((W, H), "CO-PILOTS", pygame.RESIZABLE)
else:
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("CO-PILOTS")
# Hidden Esc-hold exit and idle timeout, only used inside the arcade
session = arcade_mode.Session() if ARCADE else None
canvas = pygame.Surface((W, H))
fx = pygame.Surface((W, H), pygame.SRCALPHA)
clock = pygame.time.Clock()
fonts = {}
def text(surf, s, size, color, center, shadow=None):
    if size not in fonts:
        fonts[size] = pygame.font.SysFont("couriernew,consolas,monospace", size, bold=True)
    if shadow:
        r = fonts[size].render(s, True, shadow)
        surf.blit(r, r.get_rect(center=(center[0] + 4, center[1] + 4)))
    r = fonts[size].render(s, True, color)
    surf.blit(r, r.get_rect(center=center))
_glow = {}
def glow(color, r):
    if (color, r) not in _glow:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(6):
            pygame.draw.circle(s, (*color, 14), (r, r), r - i * r // 7)
        _glow[(color, r)] = s
    return _glow[(color, r)]
scan = pygame.Surface((W, H), pygame.SRCALPHA)
for y in range(0, H, 3):
    pygame.draw.line(scan, (0, 0, 0, 70), (0, y), (W, y))
stars = [[random.uniform(0, W), random.uniform(0, H), random.choice((0.2, 0.5, 1.0))] for _ in range(120)]
# ------------------------------------------------
# SAVED TEAM HIGH SCORE
# ------------------------------------------------
# highscore.txt is saved like this: TEAM NAME,8450
# The old number-only format is also supported.
best = 0
best_name = "NO TEAM YET"
try:
    saved = open(HS_FILE, encoding="utf-8").read().strip()
    if "," in saved:
        saved_name, saved_score = saved.split(",", 1)
        best_name = saved_name.strip() or "UNKNOWN TEAM"
        best = int(saved_score)
    elif saved:
        best = int(saved)
        best_name = "OLD RECORD"
except Exception:
    best = 0
    best_name = "NO TEAM YET"
# In the arcade the record to beat comes from the arcade leaderboard instead
if ARCADE:
    best_name, best = arcade_mode.best_entry() or ("NO RECORD YET", 0)
# ---------- sound (generated in code, no files needed) ----------
from array import array
try:
    SR = 22050
    pygame.mixer.init(SR, -16, 1)
except Exception:
    SR = None  # no audio device: the game still runs, just silent
def tone(freqs, dur, vol=0.25, noise=False, slide=0.0):
    n, ph, buf = int(SR * dur), 0.0, array("h")
    for i in range(n):
        ph += freqs[i * len(freqs) // n] * (1 + slide * i / n) / SR
        v = random.uniform(-1, 1) if noise else (1 if ph % 1 < 0.5 else -1)
        buf.append(int(v * vol * 32767 * (1 - i / n)))
    return pygame.mixer.Sound(buffer=buf.tobytes())
SFX = {}
if SR:
    SFX = {
        "start": tone([523, 659, 784, 1047], 0.35),          # rising arpeggio
        "boost": tone([400], 0.25, slide=1.5),               # whoosh up
        "pass": tone([880, 1175], 0.12, 0.2),                # coin-style blip
        "crash": tone([100], 0.7, 0.4, noise=True),          # explosion
    }
def sfx(name):
    if name in SFX:
        SFX[name].play()
# ---------- game ----------
# ================================================================
# MAIN GAME CLASS
# ================================================================
# Think of Game as the "brain" of CO-PILOTS.
# One Game object remembers the ship, score, obstacles, difficulty,
# combo, chaos event, particles, and current screen/state.
# ------------------------------------------------
# BACKGROUND + CRASH AUDIO
# ------------------------------------------------
# Background music loops while playing.
# Crash plays at impact.
# After-crash plays on the Game Over / score screen.
external_audio_ok = pygame.mixer.get_init() is not None
crash_sound = None
after_crash_sound = None

if external_audio_ok:
    try:
        crash_sound = pygame.mixer.Sound(CRASH_FILE)
        after_crash_sound = pygame.mixer.Sound(AFTER_CRASH_FILE)
        pygame.mixer.music.load(BACKGROUND_FILE)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
    except Exception as audio_error:
        print("External audio could not be loaded:", audio_error)
        external_audio_ok = False

class Game:
    def __init__(self, inp):
        self.inp, self.state, self.t = inp, "title", 0.0
        self.difficulty_index = 1
        self.difficulty = DIFFICULTY_ORDER[self.difficulty_index]
        self.select_cooldown = 0.0
        self.particles, self.shake, self.prev_boost, self.over_t = [], 0.0, 0, 0.0

        # Used only when a team breaks the high score.
        self.name_input = ""
        self.pending_high_score = 0

        # Crash audio sequence:
        # 1) crash.mpeg plays first
        # 2) after_crash.mpeg starts only AFTER crash.mpeg finishes
        self.after_crash_played = False
        self.waiting_for_after_crash = False
        self.post_crash_state = "over"

        self.reset()
    # ------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------
    # Called when a new run begins.
    # We put starting values here so restarting the game is easy:
    # just call self.reset().
    def reset(self):
        self.after_crash_played = False
        self.waiting_for_after_crash = False
        self.shake = 0.0

        # Stop all death/reaction audio and restore the background.
        # This keeps audio completely separate from retry/gameplay logic.
        if external_audio_ok:
            if crash_sound is not None:
                crash_sound.stop()
            if after_crash_sound is not None:
                after_crash_sound.stop()

            # If the music was paused by crash(), continue it.
            pygame.mixer.music.unpause()

        self.x, self.y = W / 2, H - 110
        self.walls, self.score, self.energy = [], 0.0, 100.0
        self.coins = []
        self.coins_collected = 0
        self.coin_streak = 0
        self.coin_spawn_timer = 2.0

        # COMBO SYSTEM:
        # Every obstacle passed safely increases the combo.
        # The multiplier rises every 3 passes and is capped at x5.
        self.combo = 0
        self.best_combo = 0
        self.speed, self.travel, self.boosting = DIFFICULTIES[self.difficulty]["speed"], 0.0, False
        self.last_gap, self.since, self.nxt = W / 2, 999, 0

        # --------------------------------------------------------
        # RANDOM CHAOS SYSTEM
        # --------------------------------------------------------
        # chaos_event tells us WHICH event is currently active.
        # None means there is currently no chaos event.
        self.chaos_event = None

        # chaos_t counts DOWN while an event is active.
        self.chaos_t = 0.0

        # next_chaos also counts down, but while NO event is active.
        # random.uniform makes the wait unpredictable.
        self.next_chaos = random.uniform(5.0, 8.0)

    # ------------------------------------------------------------
    # CREATE AN OBSTACLE
    # ------------------------------------------------------------
    # This function creates the next wall/beam.
    # self.nxt alternates the obstacle type so both players get turns.
    def spawn_wall(self):
        # SKILL ISSUE works by subtracting 45 pixels from the gap.
        # This is a Python "conditional expression":
        # use 45 if SKILL_ISSUE is active, otherwise use 0.
        chaos_gap_penalty = 45 if self.chaos_event == "SKILL_ISSUE" else 0

        # gw = gap width.
        # max(95, ...) prevents the opening from becoming smaller than 95 px.
        gw = max(95, 240 + DIFFICULTIES[self.difficulty]["gap_bonus"]
                 - self.score / 40 - chaos_gap_penalty)
        kind, self.nxt = self.nxt % 2, self.nxt + 1
        if kind == 0:  # CYAN wall falls from the top: P1 lines up the gap left/right
            gx = max(30, min(W - gw - 30, self.last_gap + random.uniform(-260, 260)))
            self.last_gap = gx
            self.walls.append({"k": "w", "y": -30.0, "gx": gx, "gw": gw, "done": False})
        else:  # MAGENTA beam flies in from the right: P2 lines up the gap up/down
            gh = max(130, gw - 60)
            self.walls.append({"k": "b", "x": W + 30.0, "gy": random.uniform(70, H - 30 - gh), "gh": gh, "done": False})
    def burst(self, x, y, n, colors, spd=300):
        for _ in range(n):
            a, s = random.uniform(0, 6.28), random.uniform(40, spd)
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(0.4, 1.0), random.choice(colors)])
    def crash(self):
        global best
        self.over_t = 0.0

        # --------------------------------------------------------
        # STAGE 1: CRASH MOMENT
        # --------------------------------------------------------
        # Freeze gameplay on the impact and let crash.mpeg have its
        # own moment before any Game Over / high-score writing appears.
        self.state = "crash"
        self.shake = 0.45
        self.burst(self.x, self.y, 90, (CYAN, MAG, YEL, WHITE), 500)
        self.inp.send("C")

        self.after_crash_played = False
        self.waiting_for_after_crash = True

        # Remember which screen should appear AFTER crash.mpeg finishes.
        # The arcade asks for names itself, so it always goes to Game Over.
        if int(self.score) > best and not ARCADE:
            self.pending_high_score = int(self.score)
            self.name_input = ""
            self.post_crash_state = "name_entry"
        else:
            self.post_crash_state = "over"

        if external_audio_ok:
            pygame.mixer.music.pause()
            if after_crash_sound is not None:
                after_crash_sound.stop()
            if crash_sound is not None:
                crash_sound.stop()
                crash_sound.play()
        else:
            sfx("crash")

    def handle_event(self, event):
        # pygame KEYDOWN events are perfect for typing names.
        global best, best_name

        if self.state != "name_entry" or event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_BACKSPACE:
            # [:-1] means everything except the final character.
            self.name_input = self.name_input[:-1]

        elif event.key == pygame.K_RETURN:
            # Enter saves the name, but only if something was typed.
            if self.name_input.strip():
                best_name = self.name_input.strip()[:16]
                best = self.pending_high_score

                # Save both values permanently.
                # Example: TEAM SIGMA,8450
                try:
                    with open(HS_FILE, "w", encoding="utf-8") as f:
                        f.write(f"{best_name},{best}")
                except Exception:
                    pass

                # after_crash may already be playing from the
                # NEW HIGH SCORE screen. Keep the flag True so the
                # Game Over screen does not start it a second time.
                self.state = "over"
                self.over_t = 0.0

        else:
            # event.unicode contains the character the user typed.
            # Limit names to 16 characters so they fit on screen.
            char = event.unicode
            if char and char.isprintable() and char != "," and len(self.name_input) < 16:
                self.name_input += char

    # ------------------------------------------------------------
    # UPDATE = GAME LOGIC
    # ------------------------------------------------------------
    # This runs every frame.
    # It reads controls, moves things, updates score/energy/chaos,
    # creates obstacles, and checks whether the ship crashes.
    #
    # dt = seconds since the previous frame.
    def update(self, dt):
        self.t += dt
        tilt, up, down, boost = self.inp.poll()
        pressed = boost and not self.prev_boost
        self.prev_boost = boost
        if session and (up or down or boost or abs(tilt) > 0.5):
            session.note_input()
        # Arcade: difficulty is fixed at MEDIUM so every score is comparable
        if ARCADE and self.state == "title" and pressed:
            self.reset()
            self.state = "play"
            sfx("start")
            return
        if self.state == "title" and pressed:
            self.state = "difficulty"
            self.select_cooldown = 0.20
            return
        if self.state == "difficulty":
            self.select_cooldown = max(0.0, self.select_cooldown - dt)
            if self.select_cooldown <= 0:
                if tilt < -0.5:
                    self.difficulty_index = max(0, self.difficulty_index - 1)
                    self.difficulty = DIFFICULTY_ORDER[self.difficulty_index]
                    self.select_cooldown = 0.20
                elif tilt > 0.5:
                    self.difficulty_index = min(2, self.difficulty_index + 1)
                    self.difficulty = DIFFICULTY_ORDER[self.difficulty_index]
                    self.select_cooldown = 0.20
            if pressed:
                self.reset()
                self.state = "play"
                sfx("start")
            return
        # ----------------------------------------------------
        # NEW HIGH SCORE NAME SCREEN
        # ----------------------------------------------------
        # ENTER saves the name through handle_event().
        # BOOST skips name entry and immediately starts another run.
        # This prevents the game from ever getting stuck here.
        # ----------------------------------------------------
        # STAGE 1: CRASH SCREEN
        # ----------------------------------------------------
        if self.state == "crash":
            # Keep a little impact shake at first, then let it fade.
            # No retry/name-entry controls are active yet.
            if external_audio_ok and crash_sound is not None:
                crash_finished = crash_sound.get_num_channels() == 0
            else:
                # Fallback if external audio failed: hold the crash
                # moment for about 1.2 seconds.
                crash_finished = self.over_t >= 1.2

            self.over_t += dt

            if crash_finished:
                self.shake = 0.0
                self.waiting_for_after_crash = False
                self.state = self.post_crash_state
                self.over_t = 0.0

                # ------------------------------------------------
                # STAGE 2: RESULT SCREEN + AFTER-CRASH SOUND
                # ------------------------------------------------
                if external_audio_ok and after_crash_sound is not None:
                    self.after_crash_played = True
                    after_crash_sound.play()

            return

        if self.state == "name_entry":
            # The score/name screen itself should NOT shake.
            self.shake = 0.0

            if pressed:
                if external_audio_ok:
                    if crash_sound is not None:
                        crash_sound.stop()
                    if after_crash_sound is not None:
                        after_crash_sound.stop()
                    pygame.mixer.music.unpause()

                self.reset()
                self.state = "play"
                sfx("start")

            return

        if self.state == "over":
            self.over_t += dt
            self.shake = 0.0

            # Arcade: one run per player, then back to the menu
            if ARCADE:
                if self.over_t >= arcade_mode.END_SCREEN_SECONDS:
                    arcade_mode.finish(int(self.score), "over", best_combo=self.best_combo)
                return

            # RETRY:
            # Boost works even if after_crash.mpeg is still playing.
            if pressed and self.over_t > 0.8:
                if external_audio_ok:
                    if crash_sound is not None:
                        crash_sound.stop()
                    if after_crash_sound is not None:
                        after_crash_sound.stop()
                    pygame.mixer.music.unpause()

                self.reset()
                self.state = "play"
                sfx("start")
                return
        if self.state == "play":
            # ----------------------------------------------------
            # RANDOM CHAOS TIMER
            # ----------------------------------------------------
            # There are two situations:
            #
            # A) An event IS active:
            #    subtract dt from chaos_t until it reaches zero.
            #
            # B) No event is active:
            #    subtract dt from next_chaos. When it reaches zero,
            #    random.choice() chooses one of our three events.
            if self.chaos_event is not None:
                self.chaos_t -= dt
                if self.chaos_t <= 0:
                    self.chaos_event = None
                    self.chaos_t = 0.0
                    self.next_chaos = random.uniform(8.0, 12.0)
            else:
                self.next_chaos -= dt
                if self.next_chaos <= 0:
                    # Add another chaos event later by putting its name
                    # in this list, then writing what that event actually
                    # changes elsewhere in update()/spawn_wall().
                    self.chaos_event = random.choice([
                        "MAX_VERSTAPPEN",
                        "SKILL_ISSUE",
                        "HYPER_BOOST",
                    ])
                    self.chaos_t = 5.0

            was = self.boosting

            # HYPER BOOST = automatic free boost for five seconds.
            if self.chaos_event == "HYPER_BOOST":
                self.boosting = True
                self.energy = min(100, self.energy + 15 * dt)
            else:
                self.boosting = bool(boost) and self.energy > 0
                self.energy = max(0, self.energy - 35 * dt) if self.boosting else min(100, self.energy + 15 * dt)

            if self.boosting and not was:
                self.inp.send("B"); sfx("boost")

            base_speed = DIFFICULTIES[self.difficulty]["speed"]
            self.speed = min(520, base_speed + self.score / 12)

            # MAX VERSTAPPEN = the entire world becomes 1.7x faster.
            chaos_speed = 1.7 if self.chaos_event == "MAX_VERSTAPPEN" else 1.0
            sp = self.speed * chaos_speed * (1.7 if self.boosting else 1)

            # Controls always stay normal.
            self.x = max(18, min(W - 18, self.x + tilt * 560 * dt))
            self.y = max(70, min(H - 30, self.y + (down - up) * 380 * dt))
            # Distance travelled this frame = speed * time.
            self.travel += sp * dt

            # The player slowly earns score just for surviving.
            # Boosting doubles this survival score.
            self.score += dt * 10 * (2 if self.boosting else 1)

            # "since" measures distance since the last obstacle spawned.
            self.since += sp * dt
            if self.since > DIFFICULTIES[self.difficulty]["spawn_distance"]:
                self.since = 0
                self.spawn_wall()
            # Collectible coins: spawn away from the edges and move down the screen.
            self.coin_spawn_timer -= dt
            if self.coin_spawn_timer <= 0:
                self.coins.append({"x": random.randint(90, W - 90), "y": -25.0})
                self.coin_spawn_timer = random.uniform(2.0, 3.5)
            for coin in self.coins[:]:
                coin["y"] += sp * 0.75 * dt
                if math.hypot(coin["x"] - self.x, coin["y"] - self.y) < 29:
                    self.coins.remove(coin)
                    self.coins_collected += 1
                    self.coin_streak += 1
                    self.score += 50 + min(100, (self.coin_streak - 1) * 10)
                    self.burst(coin["x"], coin["y"], 12, (YEL, WHITE), 160)
                    sfx("pass")
                elif coin["y"] > H + 25:
                    self.coins.remove(coin)
                    self.coin_streak = 0
            for w in self.walls:
                if w["k"] == "w":
                    w["y"] += sp * dt
                    hit = abs(w["y"] - self.y) < 24 and (self.x - 12 < w["gx"] or self.x + 12 > w["gx"] + w["gw"])
                    past = w["y"] > self.y + 20
                else:
                    w["x"] -= sp * 1.2 * dt
                    hit = abs(w["x"] - self.x) < 24 and (self.y - 12 < w["gy"] or self.y + 12 > w["gy"] + w["gh"])
                    past = w["x"] < self.x - 20
                if hit:
                    self.crash(); break
                if past and not w["done"]:
                    w["done"] = True

                    # One more successful obstacle = one more combo.
                    self.combo += 1
                    self.best_combo = max(self.best_combo, self.combo)

                    # x1 for combo 1-2, x2 for 3-5, x3 for 6-8,
                    # x4 for 9-11 and x5 from 12 onward.
                    multiplier = min(5, 1 + self.combo // 3)

                    # Boost still doubles the points just like before.
                    self.score += 100 * multiplier * (2 if self.boosting else 1)
                    sfx("pass")
            self.walls = [w for w in self.walls if w.get("y", 0) < H + 40 and w.get("x", 0) > -40]
            if self.state == "play":  # engine trail
                for _ in range(4 if self.boosting else 1):
                    self.particles.append([self.x + random.uniform(-6, 6), self.y + 14, random.uniform(-20, 20),
                                           sp * (0.6 if self.boosting else 0.3), 0.25 if self.boosting else 0.15,
                                           YEL if self.boosting else MAG])

        # world keeps moving for effects
        flow = self.speed * (1.7 if self.boosting else 1) if self.state == "play" else 80
        for s in stars:
            s[1] += flow * s[2] * dt * 0.5
            if s[1] > H: s[0], s[1] = random.uniform(0, W), 0
        for p in self.particles:
            p[0] += p[2] * dt; p[1] += p[3] * dt; p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        self.shake = max(0, self.shake - dt)
    # ------------------------------------------------------------
    # DRAW = WHAT THE PLAYER SEES
    # ------------------------------------------------------------
    # Game logic happens in update().
    # This function takes the current values and draws them on screen.
    def draw(self):
        canvas.fill(BG)
        fx.fill((0, 0, 0, 0))
        off = (self.travel if self.state == "play" else self.t * 80) % 60
        for i in range(-1, H // 60 + 2):  # neon grid
            pygame.draw.line(canvas, (30, 12, 60), (0, i * 60 + off), (W, i * 60 + off))
        for x in range(0, W, 80):
            pygame.draw.line(canvas, (24, 10, 50), (x, 0), (x, H))
        for s in stars:
            c = int(90 + 165 * s[2]); canvas.set_at((int(s[0]), int(s[1])), (c, c, 255))
            if s[2] == 1.0: pygame.draw.circle(canvas, (c, c, 255), (int(s[0]), int(s[1])), 1)
        for w in self.walls:
            if w["k"] == "w":
                col = CYAN
                rs = (pygame.Rect(0, w["y"] - 12, w["gx"], 24), pygame.Rect(w["gx"] + w["gw"], w["y"] - 12, W, 24))
            else:
                col = MAG
                rs = (pygame.Rect(w["x"] - 12, 0, 24, w["gy"]), pygame.Rect(w["x"] - 12, w["gy"] + w["gh"], 24, H))
            for r in rs:
                pygame.draw.rect(canvas, tuple(c // 6 for c in col), r)
                pygame.draw.rect(canvas, col, r, 3)
                pygame.draw.rect(fx, (*col, 50), r.inflate(10, 10), 8)
        # Gold coin with a bright center and small shine.
        for coin in self.coins:
            cx, cy = int(coin["x"]), int(coin["y"])
            pygame.draw.circle(canvas, (115, 65, 0), (cx, cy), 15)
            pygame.draw.circle(canvas, YEL, (cx, cy), 12)
            pygame.draw.circle(canvas, (255, 250, 165), (cx, cy), 8, 2)
            pygame.draw.circle(canvas, WHITE, (cx - 4, cy - 4), 2)
        for p in self.particles:
            a = max(0, min(1, p[4] * 2))
            pygame.draw.circle(canvas, tuple(int(c * a) for c in p[5]), (int(p[0]), int(p[1])), 3 if p[4] > 0.3 else 2)
        if self.state != "over":
            x, y = int(self.x), int(self.y)
            fx.blit(glow(YEL if self.boosting else CYAN, 46), (x - 46, y - 46))
            pts = [(x, y - 18), (x + 14, y + 14), (x, y + 7), (x - 14, y + 14)]
            pygame.draw.polygon(canvas, (10, 30, 50), pts)
            pygame.draw.polygon(canvas, WHITE if self.boosting else CYAN, pts, 3)
        canvas.blit(fx, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        # HUD
        text(canvas, f"SCORE {int(self.score):06d}", 26, WHITE, (170, 26))
        text(canvas, f"HIGH SCORE {best:06d}", 26, YEL, (W - 190, 26))
        pygame.draw.rect(canvas, WHITE, (W // 2 - 102, 14, 204, 18), 2)
        pygame.draw.rect(canvas, YEL if self.boosting else CYAN, (W // 2 - 99, 17, 198 * self.energy / 100, 12))
        text(canvas, "BOOST", 14, WHITE, (W // 2, 46))
        if self.state == "play":
            text(canvas, f"COINS {self.coins_collected}", 17, YEL, (W - 105, 67))

        # Show combo only after the player has passed at least one obstacle.
        if self.combo > 0:
            multiplier = min(5, 1 + self.combo // 3)
            text(canvas, f"COMBO {self.combo}  x{multiplier}", 18, YEL,
                 (W // 2, 94))
        if self.state == "play":
            text(canvas, self.difficulty, 14, WHITE, (W // 2, 68))
            text(canvas, f"HIGH SCORE: {best_name} - {best}", 15, YEL,
                 (W // 2, 118))
        text(canvas, "P1  TILT < >", 18, CYAN, (95, H - 18))
        text(canvas, "P2  UP / DOWN", 18, MAG, (W - 110, H - 18))

        if self.state == "play" and self.chaos_event is not None:
            chaos_names = {
                "MAX_VERSTAPPEN": "MAX VERSTAPPEN MODE!",
                "SKILL_ISSUE": "SKILL ISSUE!",
                "HYPER_BOOST": "HYPER BOOST!",
            }
            chaos_subtitles = {
                "MAX_VERSTAPPEN": "SPEED x1.7",
                "SKILL_ISSUE": "GAPS SHRINK",
                "HYPER_BOOST": "FREE BOOST",
            }
            text(canvas, chaos_names[self.chaos_event], 30, YEL,
                 (W // 2, 145), shadow=MAG)
            text(canvas,
                 f"{chaos_subtitles[self.chaos_event]}   {self.chaos_t:.1f}s",
                 19, WHITE, (W // 2, 178))

        if self.state == "title":
            text(canvas, "CO-PILOTS", 84, CYAN, (W // 2, 170), shadow=MAG)
            text(canvas, "TWO PLAYERS - ONE SHIP - ZERO CHILL", 22, WHITE, (W // 2, 235))
            text(canvas, f"HIGH SCORE: {best_name} - {best}", 20, YEL,
                 (W // 2, 270))
            text(canvas, "P1 steers LEFT/RIGHT: slip through CYAN walls", 22, CYAN, (W // 2, 315))
            text(canvas, "P2 flies UP/DOWN: slip through MAGENTA beams", 22, MAG, (W // 2, 345))
            if int(self.t * 2) % 2:
                text(canvas, "PRESS BOOST TO START", 34, YEL, (W // 2, 410))
        elif self.state == "difficulty":
            text(canvas, "SELECT DIFFICULTY", 48, WHITE, (W // 2, 145))
            names = ["EASY", "MEDIUM", "HARD"]
            colors = [CYAN, YEL, MAG]
            xs = [W // 2 - 250, W // 2, W // 2 + 250]
            for i, name in enumerate(names):
                selected = i == self.difficulty_index
                if selected:
                    pygame.draw.rect(canvas, colors[i],
                                     pygame.Rect(xs[i] - 105, 210, 210, 90), 3)
                text(canvas, name, 34 if selected else 27,
                     colors[i], (xs[i], 255))
            text(canvas, "P1 LEFT / RIGHT TO CHOOSE", 22, CYAN, (W // 2, 355))
            if int(self.t * 2) % 2:
                text(canvas, "PRESS BOOST TO START", 30, YEL, (W // 2, 410))
        elif self.state == "crash":
            # During the crash sound we deliberately show almost no writing.
            # This gives the impact + sound its own dramatic moment.
            text(canvas, "CRASH!", 72, MAG, (W // 2, 220), shadow=CYAN)

        elif self.state == "name_entry":
            text(canvas, "NEW HIGH SCORE!", 62, YEL, (W // 2, 155), shadow=MAG)
            text(canvas, f"SCORE {self.pending_high_score}", 32, WHITE, (W // 2, 225))
            text(canvas, "ENTER YOUR TEAM NAME", 24, CYAN, (W // 2, 290))

            # Flashing underscore = simple text cursor.
            shown_name = self.name_input if self.name_input else "TYPE HERE"
            cursor = "_" if int(self.t * 2) % 2 else ""
            text(canvas, f"> {shown_name}{cursor}", 34, WHITE, (W // 2, 345))

            text(canvas, "ENTER = SAVE HIGH SCORE", 22, MAG, (W // 2, 400))
            text(canvas, "BOOST = SKIP & RETRY", 22, YEL, (W // 2, 435))
            text(canvas, "BACKSPACE = DELETE   |   MAX 16 CHARACTERS",
                 15, WHITE, (W // 2, 470))

        elif self.state == "over":
            text(canvas, "GAME OVER", 80, MAG, (W // 2, 180), shadow=CYAN)
            text(canvas, f"SCORE {int(self.score)}", 34, WHITE, (W // 2, 255))
            text(canvas, f"HIGH SCORE: {best_name} - {best}", 22, CYAN,
                 (W // 2, 300))
            text(canvas, f"BEST COMBO {self.best_combo}", 22, YEL, (W // 2, 335))
            if self.over_t > 0.8 and int(self.t * 2) % 2 and not ARCADE:
                text(canvas, "PRESS BOOST TO RETRY", 30, YEL, (W // 2, 385))
        ox, oy = (random.randint(-8, 8), random.randint(-8, 8)) if self.shake > 0 else (0, 0)
        # First combine the game canvas + scanline effect at the
        # ORIGINAL 960x540 game resolution.
        frame = canvas.copy()
        frame.blit(scan, (0, 0))

        # Find the actual window/projector size.
        screen_w, screen_h = screen.get_size()

        # Scale without stretching the picture.
        # min(...) chooses the largest scale that fits BOTH dimensions.
        scale = min(screen_w / W, screen_h / H)
        scaled_w = max(1, int(W * scale))
        scaled_h = max(1, int(H * scale))
        scaled_frame = pygame.transform.smoothscale(frame, (scaled_w, scaled_h))

        # Center the image. On screens with a different aspect ratio,
        # the unused area simply becomes black bars.
        draw_x = (screen_w - scaled_w) // 2 + int(ox * scale)
        draw_y = (screen_h - scaled_h) // 2 + int(oy * scale)

        screen.fill((0, 0, 0))
        screen.blit(scaled_frame, (draw_x, draw_y))
        if session:
            session.draw_exit_hint(screen)
        pygame.display.flip()
# ================================================================
# STARTING THE PROGRAM
# ================================================================
# main() creates the input system and Game object, then runs the
# INPUT -> UPDATE -> DRAW loop until the player closes the window.
def main():
    global fullscreen, screen
    if ARCADE or (len(sys.argv) > 1 and sys.argv[1] == "auto"):
        ser = find_controller()
        inp = SerialInput(ser) if ser else KeyboardInput()
    else:
        inp = SerialInput(sys.argv[1]) if len(sys.argv) > 1 else KeyboardInput()
    g = Game(inp)
    while True:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        if session:
            reason = session.exit_reason()
            if reason:
                arcade_mode.finish(int(g.score) if g.state != "title" else None, reason)
        for e in pygame.event.get():
            if session:
                # Esc is held to leave (see arcade_mode) and the window stays full screen
                session.handle_event(e)
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_F11):
                    continue
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit()

            # F11 switches between a normal resizable window and
            # fullscreen. This is useful when connecting a projector.
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                fullscreen = not fullscreen

                if fullscreen:
                    # (0, 0) tells pygame to use the current display's
                    # full native resolution automatically.
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)

                # Do not pass F11 to the team-name typing system.
                continue

            # Needed for typing the winning team's name.
            g.handle_event(e)

        g.update(dt)
        g.draw()
if __name__ == "__main__":
    main()