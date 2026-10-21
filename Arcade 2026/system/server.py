"""IEEE Arcade local server.

Serves the arcade menu and games to a full-screen browser on this laptop only,
keeps the leaderboards, launches the Python games, and writes a log.
Closing the arcade browser window stops it.

Leaderboards, the log, and the browser profile live in %LOCALAPPDATA%\\IEEEArcade,
so they survive downloading a newer copy of the repo.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ARCADE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ARCADE_DIR)
DATA = os.path.join(os.environ["LOCALAPPDATA"], "IEEEArcade") if os.environ.get("LOCALAPPDATA") else os.path.join(ARCADE_DIR, "data")
SCORES = os.path.join(DATA, "scores")
LOG_PATH = os.path.join(DATA, "arcade.log")
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/system/"
NAME_RE = re.compile(r"^[A-Z0-9 ]{1,5}$")
KEEP_SCORES = 100

os.makedirs(SCORES, exist_ok=True)
lock = threading.Lock()


def log(*parts):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(p) for p in parts)
    print(line, flush=True)
    with lock:
        try:
            if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1_000_000:
                os.replace(LOG_PATH, LOG_PATH + ".old")
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass


def load_games():
    with open(os.path.join(ARCADE_DIR, "games.json"), encoding="utf-8") as f:
        return {g["id"]: g for g in json.load(f)}


GAMES = load_games()


# ---------- leaderboards ----------

def board_score(board_id):
    """Score settings for a leaderboard. Games with a solo mode also have an '<id>-solo' board."""
    if board_id in GAMES:
        return GAMES[board_id]["score"]
    base = board_id[:-len("-solo")] if board_id.endswith("-solo") else None
    if base in GAMES and "solo" in GAMES[base]:
        return GAMES[base]["solo"]["score"]
    return None

def score_file(game_id):
    return os.path.join(SCORES, game_id + ".json")


def read_scores(game_id):
    try:
        with open(score_file(game_id), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def write_scores(game_id, rows):
    # Write to a temp file first so a power cut can never leave a half-written leaderboard
    path = score_file(game_id)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)
    os.replace(path + ".tmp", path)


def add_score(game_id, name, score):
    mode = board_score(game_id)["mode"]
    with lock:
        rows = read_scores(game_id)
        if mode == "wins":
            # One row per name, counting match wins
            row = next((r for r in rows if r["name"] == name), None)
            if row:
                row["score"] += 1
                row["at"] = time.time()
            else:
                row = {"name": name, "score": 1, "at": time.time()}
                rows.append(row)
        else:
            row = {"name": name, "score": int(score), "at": time.time()}
            rows.append(row)
        # Highest first, earlier entry wins a tie
        rows.sort(key=lambda r: (-r["score"], r["at"]))
        rows = rows[:KEEP_SCORES]
        write_scores(game_id, rows)
        rank = rows.index(row) + 1 if row in rows else None
    log("score", game_id, name, row["score"], "rank", rank)
    return rank, rows


# ---------- Python games ----------

class Launcher:
    def __init__(self):
        self.proc = None
        self.game_id = None
        self.result_path = None
        self.result = None

    def start(self, game_id):
        self.stop()
        bridge.set_active(False)  # the game reads its own controller
        game = GAMES[game_id]
        script = os.path.join(ROOT, game["path"])
        fd, self.result_path = tempfile.mkstemp(prefix="arcade-", suffix=".json")
        os.close(fd)
        os.remove(self.result_path)
        top = read_scores(game_id)[:1]
        env = dict(os.environ,
                   ARCADE_RESULT=self.result_path,
                   ARCADE_LOG=LOG_PATH,
                   ARCADE_BEST=f"{top[0]['name']},{top[0]['score']}" if top else "",
                   PYGAME_HIDE_SUPPORT_PROMPT="1")
        out = open(LOG_PATH, "a", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, script], cwd=os.path.dirname(script), env=env,
                                     stdout=out, stderr=subprocess.STDOUT)
        out.close()
        self.game_id, self.result = game_id, None
        log("launched", game_id, "pid", self.proc.pid)

    def status(self):
        if self.proc is None:
            return {"running": False, "result": self.result}
        code = self.proc.poll()
        if code is None:
            return {"running": True, "result": None}
        try:
            with open(self.result_path, encoding="utf-8") as f:
                self.result = json.load(f)
            os.remove(self.result_path)
        except (OSError, ValueError):
            self.result = {"score": None, "reason": "crash"}
            log("game", self.game_id, "closed without a result, exit code", code)
        self.proc = None
        bridge.set_active(True)
        return {"running": False, "result": self.result}

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            log("stopped", self.game_id)
        self.proc = None


launcher = Launcher()


# ---------- USB controllers that send key messages ----------

class Bridge:
    """Reads Arduino controllers that send lines like W1 / W0 (press / release, 9600 baud)
    and passes them to the browser as key presses, replacing serial_keyboard.py.

    Every USB serial port is watched. Lines that aren't key messages (for example an
    ESP32 talking at a different speed) are ignored. Ports are let go while a game
    that reads its own controller is running.
    """
    LINE = re.compile(r"^([A-Z0-9]|SPACE|LEFT|RIGHT|UP|DOWN|ENTER)([01])$")

    def __init__(self):
        self.active = True
        self.ports = {}          # device -> open serial port
        self.buffers = {}        # device -> partial line
        self.held = {}           # device -> keys currently held
        self.failed = {}         # device -> time of last failed open
        self.listeners = []      # queues of browser connections
        self.lock = threading.Lock()

    def emit(self, key, down, device):
        event = {"key": key, "down": down, "port": device}
        with self.lock:
            for q in self.listeners:
                q.append(event)

    def status(self):
        return {"active": self.active, "ports": sorted(self.ports)}

    def set_active(self, active):
        if active != self.active:
            self.active = active
            log("usb controllers", "watching" if active else "released for game")
        if not active:
            # Wait until the ports are really closed so the game can open them
            end = time.time() + 1.5
            while self.ports and time.time() < end:
                time.sleep(0.05)

    def release(self, device):
        for key in self.held.pop(device, set()):
            self.emit(key, False, device)
        ser = self.ports.pop(device, None)
        self.buffers.pop(device, None)
        if ser:
            try:
                ser.close()
            except Exception:
                pass

    def scan(self):
        from serial.tools import list_ports
        import serial
        present = {p.device for p in list_ports.comports() if p.vid is not None}
        for dev in list(self.ports):
            if dev not in present:
                log("usb controller unplugged", dev)
                self.release(dev)
        for dev in present - set(self.ports):
            if time.time() - self.failed.get(dev, 0) < 10:
                continue
            try:
                ser = serial.Serial()
                ser.port, ser.baudrate, ser.timeout = dev, 9600, 0
                # Opening without the reset signal, so a Bluetooth controller powered by USB stays connected
                ser.dtr = ser.rts = False
                ser.open()
                self.ports[dev], self.buffers[dev], self.held[dev] = ser, "", set()
                log("usb controller found", dev)
            except Exception as e:
                self.failed[dev] = time.time()
                log("could not open", dev, e)

    def read(self):
        for dev, ser in list(self.ports.items()):
            try:
                data = ser.read(ser.in_waiting or 1)
            except Exception as e:
                log("usb controller lost", dev, e)
                self.release(dev)
                continue
            if not data:
                continue
            text = self.buffers[dev] + data.decode("ascii", errors="replace")
            *lines, self.buffers[dev] = text.split("\n")
            self.buffers[dev] = self.buffers[dev][-64:]
            for line in lines:
                m = self.LINE.match(line.strip().upper())
                if not m:
                    continue
                key, down = m.group(1), m.group(2) == "1"
                held = self.held[dev]
                if down and key in held or not down and key not in held:
                    continue
                (held.add if down else held.discard)(key)
                self.emit(key, down, dev)

    def run(self):
        try:
            import serial  # noqa: F401
        except ImportError:
            log("pyserial missing, USB key controllers disabled")
            return
        last_scan = 0
        while True:
            if not self.active:
                for dev in list(self.ports):
                    self.release(dev)
                time.sleep(0.2)
                continue
            if time.time() - last_scan > 2:
                self.scan()
                last_scan = time.time()
            self.read()
            time.sleep(0.005)


bridge = Bridge()


# ---------- HTTP ----------

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        pass  # keep the log for things that matter

    def end_headers(self):
        # Always serve the latest files after an update
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/system/")
            self.end_headers()
        elif path.startswith("/api/scores/"):
            game_id = path.rsplit("/", 1)[1]
            if not board_score(game_id):
                return self.send_json({"error": "unknown game"}, 404)
            self.send_json(read_scores(game_id)[:10])
        elif path == "/api/launch":
            self.send_json(launcher.status())
        elif path == "/api/usb":
            self.send_json(bridge.status())
        elif path == "/api/keys":
            self.stream_keys()
        elif path.startswith("/api/"):
            self.send_json({"error": "not found"}, 404)
        else:
            super().do_GET()

    def stream_keys(self):
        """Server-sent events: pushes USB controller key presses to the menu as they happen."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        queue = []
        with bridge.lock:
            bridge.listeners.append(queue)
        try:
            last_ping = time.time()
            while True:
                if queue:
                    with bridge.lock:
                        events, queue[:] = list(queue), []
                    for ev in events:
                        self.wfile.write(f"data: {json.dumps(ev)}\n\n".encode())
                    self.wfile.flush()
                elif time.time() - last_ping > 10:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    last_ping = time.time()
                time.sleep(0.005)
        except OSError:
            pass  # browser closed the connection
        finally:
            with bridge.lock:
                bridge.listeners.remove(queue)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = self.read_json()
        if path.startswith("/api/scores/"):
            game_id = path.rsplit("/", 1)[1]
            name = str(body.get("name", "")).upper()
            score = body.get("score")
            if not board_score(game_id) or not NAME_RE.match(name) or not isinstance(score, (int, float)):
                return self.send_json({"error": "bad score"}, 400)
            rank, rows = add_score(game_id, name.rstrip() or "?", score)
            self.send_json({"rank": rank, "rows": rows[:10]})
        elif path.startswith("/api/launch/"):
            game_id = path.rsplit("/", 1)[1]
            if GAMES.get(game_id, {}).get("type") != "python":
                return self.send_json({"error": "not a python game"}, 400)
            try:
                launcher.start(game_id)
            except Exception as e:
                log("launch failed", game_id, e)
                return self.send_json({"error": str(e)}, 500)
            self.send_json({"ok": True})
        elif path == "/api/stop":
            launcher.stop()
            self.send_json({"ok": True})
        elif path == "/api/usb":
            bridge.set_active(bool(body.get("active")))
            self.send_json(bridge.status())
        elif path == "/api/test-key" and "--debug" in sys.argv:
            bridge.emit(str(body.get("key")), bool(body.get("down")), "TEST")
            self.send_json({"ok": True})
        elif path == "/api/log":
            log("browser:", str(body.get("msg", ""))[:500])
            self.send_json({"ok": True})
        else:
            self.send_json({"error": "not found"}, 404)


# ---------- browser ----------

def find_browser():
    """Chrome first (best for USB controllers later), then Edge, which every Windows laptop has."""
    candidates = []
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidates.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
    for base in (os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES")):
        if base:
            candidates.append(os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
    for c in candidates:
        if os.path.exists(c):
            return c
    return shutil.which("chrome") or shutil.which("msedge")


def open_browser(windowed):
    exe = find_browser()
    if not exe:
        log("no Chrome or Edge found, opening the default browser")
        webbrowser.open(URL)
        return None
    profile = os.path.join(DATA, "browser-profile")
    args = [exe, f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
            "--autoplay-policy=no-user-gesture-required", "--disable-session-crashed-bubble",
            "--disable-features=Translate", "--overscroll-history-navigation=0", "--disable-pinch"]
    args += [f"--app={URL}", "--start-maximized"] if windowed else ["--kiosk", URL]
    log("opening", os.path.basename(exe), "windowed" if windowed else "full screen")
    return subprocess.Popen(args)


def main():
    windowed = "--windowed" in sys.argv
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # Already running (for example the window was closed but the server kept going)
        log("arcade already running, opening it again")
        open_browser(windowed)
        return
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=bridge.run, daemon=True).start()
    log("arcade started from", ROOT, "python", sys.version.split()[0], "data in", DATA)
    browser = None if "--no-browser" in sys.argv else open_browser(windowed)
    try:
        if browser is not None:
            browser.wait()
            log("browser closed, arcade stopping")
        else:
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        launcher.stop()
        server.shutdown()


if __name__ == "__main__":
    main()
