"""
BRAINROT MANIA - 2D fighting game in pygame.

Setup:  pip install pygame
Run:    python brainrot_mania.py

P1: A/D move, W jump, F punch, G kick, H special   (hold back to block)
P2: LEFT/RIGHT move, UP jump, K punch, L kick, ;   (hold back to block)
Character select: browse with move keys, press punch (F / K) to lock in.
The button controller (an Arduino Uno sending W1 / W0 style lines at 9600) is read
directly by the game, so serial_keyboard.py is not needed.
"""
import array
import colorsys
import math
import os
import random
import sys

import pygame

# IEEE arcade helpers (full screen, controller, results). The game still runs on its own without them.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "system", "pylib"))
try:
    import arcade_mode
except ImportError:
    arcade_mode = None
ARCADE = arcade_mode is not None and arcade_mode.ACTIVE
MATCH_END_FRAMES = 6 * 60  # how long the winner screen shows in the arcade before it closes

W, H, FLOOR, FPS = 960, 540, 470, 60
ROUND_FRAMES = 60 * FPS
RATE = 22050
GOLD, DARK, SKIN = (255, 214, 10), (10, 10, 20), (241, 194, 125)
P_COL = [(0, 245, 212), (255, 46, 147)]

CHARS = [
    dict(name='Tung Tung Sahur', color=(198, 134, 66), hp=110, spd=3.2, dmg=8, sp='Bat Toss', type='proj',
         ps=9, spdmg=15, shape='bat', look='log', desc='Hurls his spinning bat'),
    dict(name='Sigmaman', color=(184, 192, 204), hp=100, spd=3.7, dmg=9, sp='Grindset Dash', type='dash',
         spdmg=17, look='sigma', desc='Charges through foes'),
    dict(name='The Rizzler', color=(255, 214, 10), hp=90, spd=4.2, dmg=7, sp='Rizz Beam', type='proj',
         ps=12, spdmg=13, shape='heart', look='rizz', desc='Fast heart missile'),
    dict(name='Grimace', color=(157, 78, 221), hp=135, spd=2.6, dmg=10, sp='Shake Slam', type='slam',
         spdmg=20, shape='wave', look='grimace', desc='Shockwave both ways'),
    dict(name='Ren Hayashi', color=(232, 232, 240), hp=105, spd=3.6, dmg=9, sp='Thunder Fist', type='dash',
         spdmg=18, look='ren', desc='Karate prodigy'),
    dict(name='Vex Ironclad', color=(193, 18, 31), hp=120, spd=3.0, dmg=10, sp='Inferno Wave', type='proj',
         ps=9, spdmg=16, shape='fire', look='vex', desc='Street brawler'),
]
CTRL = [
    dict(l=pygame.K_a, r=pygame.K_d, u=pygame.K_w, a=pygame.K_f, k=pygame.K_g, s=pygame.K_h),
    dict(l=pygame.K_LEFT, r=pygame.K_RIGHT, u=pygame.K_UP, a=pygame.K_k, k=pygame.K_l, s=pygame.K_SEMICOLON),
]
SEL = [dict(l=pygame.K_a, r=pygame.K_d, ok=pygame.K_f), dict(l=pygame.K_LEFT, r=pygame.K_RIGHT, ok=pygame.K_k)]
RAGE = ['L + RATIO + NO RIZZ + ZERO AURA', 'FANUM TAXED YOUR VICTORY', 'GO BACK TO OHIO',
        'SKILL ISSUE (CERTIFIED)', 'MOGGED IN 4K', 'NPC BEHAVIOR DETECTED', '-10000 AURA',
        'SIGMA? MORE LIKE BETA', 'TOUCH GRASS, THEN LOSE AGAIN']


# ============================== AUDIO (synthesised, no files) ==============================
def synth(dur, noise=0.0, lp=0.3, f0=0, f1=0, tone=0.0, square=False):
    """Decaying noise burst (one-pole low-pass) plus an optional sweeping tone."""
    n = int(RATE * dur)
    buf, y, ph = array.array('h'), 0.0, 0.0
    for i in range(n):
        t = i / n
        env = 1 - t
        v = 0.0
        if noise:
            y += lp * (random.uniform(-1, 1) - y)
            v += noise * y * env
        if tone and f0:
            ph += 2 * math.pi * f0 * (f1 / f0) ** t / RATE
            s = math.sin(ph)
            v += tone * (math.copysign(.5, s) if square else s) * env * env
        buf.append(int(max(-1, min(1, v)) * 32000))
    return pygame.mixer.Sound(buffer=buf.tobytes())


def load_sounds():
    return {
        'hit': synth(.09, 1.6, .35, 160, 50, .7), 'kick': synth(.16, 2.0, .5, 110, 35, .9),
        'heavy': synth(.22, 2.2, .45, 90, 28, 1.0), 'block': synth(.06, .6, .95, 900, 500, .2, True),
        'swing': synth(.12, 1.2, .15), 'kickswing': synth(.2, 1.6, .1),
        'jump': synth(.12, f0=250, f1=600, tone=.4), 'special': synth(.3, f0=300, f1=900, tone=.35, square=True),
        'pick': synth(.06, f0=700, f1=900, tone=.3, square=True), 'ko': synth(.7, 1.5, .1, 140, 30, 1.0),
        'bell': synth(.9, f0=1320, f1=1300, tone=.5), 'crowd': synth(1.2, 2.5, .2),
    }


# ============================== FIGHTER ==============================
class Fighter:
    def __init__(self, ci, side):
        self.c = CHARS[ci]
        self.x, self.y, self.vx, self.vy = (740 if side else 220), FLOOR, 0.0, 0.0
        self.w, self.h = 54, 96
        self.face = -1 if side else 1
        self.hp = self.c['hp']
        self.atk = self.stun = self.dash = self.flash = self.sp_cd = self.chain = self.chain_t = 0
        self.hit = self.dash_hit = self.air = self.kick = self.blk = False
        self.ha = self.hk = False  # held-state of punch/kick for fresh-press detection


def reach(f, o, r):
    """Does f's forward hitbox (length r) overlap o?"""
    x1 = f.x if f.face > 0 else f.x - r
    return x1 + r > o.x - o.w / 2 and x1 < o.x + o.w / 2 and abs(f.y - o.y) < f.h


# ============================== GAME ==============================
class Game:
    def __init__(self):
        try:
            pygame.mixer.init(RATE, -16, 1)
            self.sounds = load_sounds()
        except pygame.error:
            self.sounds = {}
        fam = 'impact,arialblack,verdana,arial'
        self.f_huge, self.f_big, self.f_mid, self.f_sm, self.f_xs = (pygame.font.SysFont(fam, s) for s in (84, 56, 30, 16, 12))
        self.canvas = pygame.Surface((W, H))
        self.beams = pygame.Surface((W, H), pygame.SRCALPHA)
        self.dark = pygame.Surface((W, 150), pygame.SRCALPHA)
        self.dark.fill((5, 3, 20, 100))
        self.crowd = sorted(({'x': (i % 74) * 13 + random.random() * 6, 'y': 186 + (i % 4) * 26 + random.random() * 6,
                              'c': tuple(int(v * 255) for v in colorsys.hls_to_rgb(random.random(), .14 + (i % 4) * .04, .45)),
                              'ph': random.random() * 6.3} for i in range(220)), key=lambda p: p['y'])
        self.bg_top, self.bg_bottom = self.build_bg()
        self.preview = [Fighter(i, 0) for i in range(len(CHARS))]
        self.frame = self.shake = 0
        self.sched = []
        self.reset_all()

    # ---------- helpers ----------
    def snd(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def note(self, freq, square=False):
        s = synth(.28, f0=freq, f1=freq * .98, tone=.5, square=square)
        s.play()

    def later(self, frames, fn):
        self.sched.append((self.frame + frames, fn))

    def say(self, text):
        self.banner = (text, self.frame)

    def spark(self, x, y, col, n):
        for _ in range(n):
            a, s = random.uniform(0, 6.283), random.uniform(1, 6)
            self.parts.append(dict(x=x, y=y, vx=math.cos(a) * s, vy=math.sin(a) * s - 1, g=.15,
                                   life=random.randint(25, 40), max=40, col=col, s=random.randint(2, 5)))

    # ---------- flow ----------
    def reset_all(self):
        self.state, self.state_t, self.banner = 'select', 0, None
        self.sel, self.locked = [0, 1], [False, False]
        self.F, self.P, self.parts, self.score, self.round = [], [], [], [0, 0], 1
        self.t, self.round_winner, self.winner, self.rage = ROUND_FRAMES, -1, 0, []

    def start_match(self):
        self.score, self.round = [0, 0], 1
        self.start_round()

    def start_round(self):
        self.F = [Fighter(self.sel[0], 0), Fighter(self.sel[1], 1)]
        self.P, self.parts, self.t = [], [], ROUND_FRAMES
        self.state, self.state_t = 'intro', 0
        self.say(f'ROUND {self.round}')
        self.snd('bell')

    def end_round(self):
        a, b = self.F[0].hp, self.F[1].hp
        self.round_winner = -1 if (a <= 0 and b <= 0) or a == b else (0 if a > b else 1)
        if self.round_winner >= 0:
            self.score[self.round_winner] += 1
        self.state, self.state_t = 'roundEnd', 0
        self.say('TIME!' if self.t <= 0 else 'K.O.!')
        self.snd('ko')
        self.later(6, lambda: self.snd('crowd'))

    def after_round(self):
        if max(self.score) >= 2:
            return self.end_match(0 if self.score[0] >= 2 else 1)
        if self.round_winner >= 0:
            self.round += 1
        self.start_round()

    def end_match(self, w):
        self.state, self.state_t, self.winner, self.banner = 'matchEnd', 0, w, None
        self.rage = random.sample(RAGE, 4)
        for i, f in enumerate([523, 659, 784, 1047, 784, 1047, 1319]):
            self.later(i * 8, lambda f=f: self.note(f))
        self.snd('crowd')
        self.later(54, lambda: self.snd('crowd'))
        for i, f in enumerate([300, 250, 200, 110]):
            self.later(70 + i * 17, lambda f=f: self.note(f, True))

    def select_key(self, key):
        for p, m in enumerate(SEL):
            if key == m['ok']:
                self.locked[p] = not self.locked[p]
                self.snd('pick')
            elif not self.locked[p] and key in (m['l'], m['r']):
                self.sel[p] = (self.sel[p] + (len(CHARS) - 1 if key == m['l'] else 1)) % len(CHARS)
                self.snd('pick')
        if all(self.locked):
            self.later(42, lambda: self.state == 'select' and all(self.locked) and self.start_match())

    # ---------- combat ----------
    def hurt(self, tg, face, dmg, kb, big, kick=False):
        if tg.hp <= 0:
            return
        blocked = tg.blk and not tg.air
        if blocked:
            dmg, kb, big = max(1, math.ceil(dmg * .2)), kb * .4, False
        tg.hp = max(0, tg.hp - dmg)
        tg.stun = 6 if blocked else (22 if big else 12)
        tg.flash, tg.dash = (0 if blocked else 10), 0
        tg.x += face * kb
        if big:
            tg.vy, tg.air = -8, True
        self.shake = 14 if big else 6
        self.spark(tg.x, tg.y - 55, (255, 255, 255) if blocked else tg.c['color'], 26 if big else 12)
        self.parts.append(dict(x=tg.x, y=tg.y - 115, vx=0, vy=-1.2, g=0, life=40, max=40, col=(255, 255, 255),
                               txt='BLOCK' if blocked else f'-{dmg}'))
        self.snd('block' if blocked else 'kick' if kick else 'heavy' if big else 'hit')

    def use_special(self, f):
        c, i = f.c, self.F.index(f)
        if c['type'] == 'dash':
            f.dash, f.dash_hit = 16, False
        elif c['type'] == 'proj':
            self.P.append(dict(x=f.x + f.face * 40, y=f.y - 60, vx=f.face * c['ps'], i=i, dmg=c['spdmg'],
                               shape=c['shape'], r=0, life=90, low=False))
        else:  # slam: two low shockwaves
            for d in (-1, 1):
                self.P.append(dict(x=f.x + d * 30, y=f.y - 18, vx=d * 6, i=i, dmg=c['spdmg'], shape=c['shape'],
                                   r=0, life=70, low=True))
            self.shake = 12
            self.spark(f.x, f.y, c['color'], 22)

    def step(self, f, o, ctrl, keys):
        """One fixed 1/60s tick for fighter f. ctrl=None means no input."""
        c = f.c
        down = (lambda n: bool(keys[ctrl[n]])) if ctrl else (lambda n: False)
        f.face = 1 if o.x >= f.x else -1  # always face the opponent
        f.sp_cd, f.flash, f.atk, f.vx = max(0, f.sp_cd - 1), max(0, f.flash - 1), max(0, f.atk - 1), 0
        pa, pk = down('a') and not f.ha, down('k') and not f.hk  # fresh presses only
        f.ha, f.hk = down('a'), down('k')
        if f.chain_t > 0:
            f.chain_t -= 1
        else:
            f.chain = 0
        if f.stun > 0:
            f.stun -= 1
        elif f.dash > 0:
            f.dash -= 1
            f.blk = False
            f.x += f.face * 12
            self.spark(f.x - f.face * 20, f.y - 45, c['color'], 2)
            if not f.dash_hit and reach(f, o, 60):
                f.dash_hit = True
                self.hurt(o, f.face, c['spdmg'], 30, True)
        else:
            m = int(down('r')) - int(down('l'))
            f.vx = m * c['spd'] * (.4 if f.atk else 1)
            f.blk = f.atk == 0 and not f.air and down('l' if f.face > 0 else 'r')  # hold back to block
            if down('u') and not f.air:
                f.vy, f.air = -15, True
                self.snd('jump')
            if not f.atk and (pa or pk):
                f.kick = not pa
                f.chain = min(f.chain + 1, 2) if (not f.kick and f.chain_t > 0) else 0  # punch, punch, finisher
                f.atk, f.hit, f.chain_t = (26 if f.kick else 18), False, 40
                self.snd('kickswing' if f.kick else 'swing')
            active = 10 <= f.atk <= 16 if f.kick else 7 <= f.atk <= 12
            if f.atk and active and not f.hit and reach(f, o, 95 if f.kick else 70):
                f.hit = True
                fin = (not f.kick) and f.chain == 2
                self.hurt(o, f.face, c['dmg'] + 5 if f.kick else c['dmg'] + f.chain * 2,
                          26 if f.kick else 30 if fin else 14, fin, f.kick)
            if down('s') and not f.sp_cd and not f.atk:
                f.sp_cd = 300
                self.snd('special')
                self.use_special(f)
        f.vy += .8
        f.y += f.vy
        f.x += f.vx
        if f.y >= FLOOR:
            f.y, f.vy, f.air = FLOOR, 0, False
        f.x = max(34, min(W - 34, f.x))

    def step_projectiles(self):
        keep = []
        for p in self.P:
            p['x'] += p['vx']
            p['r'] += .2
            p['life'] -= 1
            o = self.F[1 - p['i']]
            near = abs(p['x'] - o.x) < o.w / 2 + 16
            in_y = o.y > FLOOR - 50 if p['low'] else o.y - o.h - 10 < p['y'] < o.y + 10
            if near and in_y and o.hp > 0:
                self.hurt(o, 1 if p['vx'] > 0 else -1, p['dmg'], 22, True)
                continue
            if p['life'] > 0 and -40 < p['x'] < W + 40:
                keep.append(p)
        self.P = keep

    def separate(self):
        a, b = self.F
        if abs(a.x - b.x) < 44 and abs(a.y - b.y) < 60:
            d = -1 if a.x <= b.x else 1
            a.x += d * 1.8
            b.x -= d * 1.8

    def update(self, keys):
        self.frame += 1
        self.state_t += 1
        self.shake *= .85
        due = [s for s in self.sched if s[0] <= self.frame]
        self.sched = [s for s in self.sched if s[0] > self.frame]
        for _, fn in due:
            fn()
        if self.state == 'intro':
            if self.state_t == 80:
                self.say('FIGHT!')
                for i, f in enumerate([392, 523, 784]):
                    self.later(i * 5, lambda f=f: self.note(f, True))
            if self.state_t >= 120:
                self.state, self.banner = 'fight', None
        if self.state in ('fight', 'roundEnd'):
            live = self.state == 'fight'
            self.step(self.F[0], self.F[1], CTRL[0] if live else None, keys)
            self.step(self.F[1], self.F[0], CTRL[1] if live else None, keys)
            self.step_projectiles()
            self.separate()
            if live:
                self.t -= 1
                if self.F[0].hp <= 0 or self.F[1].hp <= 0 or self.t <= 0:
                    self.end_round()
            else:
                if self.state_t == 70:
                    self.say('DRAW! REPLAY' if self.round_winner < 0 else CHARS[self.sel[self.round_winner]]['name'] + ' takes it!')
                if self.state_t > 170:
                    self.after_round()
        if self.state == 'matchEnd':
            for i in range(3):
                self.parts.append(dict(x=random.uniform(0, W), y=-10, vx=random.uniform(-1, 1), vy=random.uniform(1, 3),
                                       g=.03, life=260, max=260, s=6,
                                       col=[GOLD, P_COL[0], P_COL[1], (255, 255, 255)][i % 4]))
            if self.state_t % 90 == 0:
                self.rage = random.sample(RAGE, 4)
        for p in self.parts:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += p['g']
            p['life'] -= 1
        self.parts = [p for p in self.parts if p['life'] > 0]

    # ============================== RENDER ==============================
    def build_bg(self):
        top = pygame.Surface((W, H))
        for y in range(H):
            k = y / H
            pygame.draw.line(top, (int(5 + 23 * k), int(3 + 5 * k), int(15 + 33 * k)), (0, y), (W, y))
        for y in range(56, 164):
            k = (y - 56) / 108
            pygame.draw.line(top, (int(43 - 33 * k), int(10 - 6 * k), int(94 - 62 * k)), (300, y), (660, y))
        pygame.draw.rect(top, GOLD, (300, 56, 360, 108), 4)
        bot = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(440, H):  # canvas mat
            k = (y - 440) / (H - 440)
            pygame.draw.line(bot, (int(47 - 33 * k), int(76 - 54 * k), int(192 - 112 * k)), (0, y), (W, y))
        for i in range(-10, 11):
            pygame.draw.line(bot, (80, 108, 210), (480 + i * 40, 440), (480 + i * 120, H))
        im = self.f_big.render('BRAINROT MANIA', True, (72, 100, 205))
        bot.blit(im, im.get_rect(center=(480, 502)))
        pygame.draw.line(bot, (255, 255, 255), (0, 440), (W, 440), 3)
        for x in (23, 911):  # ring posts
            pygame.draw.rect(bot, (26, 26, 36), (x, 296, 26, 146))
        for i, col in enumerate([(229, 7, 45), (244, 244, 244), (229, 7, 45)]):  # sagging ropes
            y0 = 398 - i * 42
            pts = [(40 + 880 * t / 24, y0 + 28 * (t / 24) * (1 - t / 24)) for t in range(25)]
            pygame.draw.lines(bot, col, False, pts, 6)
            for x in (26, 912):
                pygame.draw.rect(bot, (229, 7, 45), (x, y0 - 11, 22, 22))
        return top, bot

    def draw_arena(self, c):
        c.blit(self.bg_top, (0, 0))
        self.beams.fill((0, 0, 0, 0))
        for i in range(5):  # swinging spotlights
            x, a = 100 + i * 190, math.sin(self.frame * .02 + i * 1.3) * 70
            rgb = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(((i * 70 + self.frame * .5) % 360) / 360, .75, 1))
            pygame.draw.polygon(self.beams, rgb + (46,), [(x - 8, 0), (x + 8, 0), (x + a + 100, H * .85), (x + a - 100, H * .85)])
        c.blit(self.beams, (0, 0))
        k = .9 + .1 * math.sin(self.frame * .3)
        self.txt(c, 'BRAINROT', self.f_mid, (int(255 * k),) * 3, (480, 88))
        self.txt(c, 'MANIA', self.f_big, (int(255 * k), int(214 * k), 10), (480, 134))
        for i, p in enumerate(self.crowd):  # bobbing crowd and camera flashes
            y = p['y'] + math.sin(self.frame * .08 + p['ph']) * 3
            pygame.draw.rect(c, p['c'], (p['x'] - 8, y + 6, 16, 28))
            pygame.draw.circle(c, p['c'], (p['x'], y), 7)
            if (self.frame + i * 37) % 900 < 3:
                pygame.draw.circle(c, (255, 255, 255), (p['x'], y), 14)
        c.blit(self.dark, (0, 170))
        c.blit(self.bg_bottom, (0, 0))

    def txt(self, c, s, font, col, pos, anchor='center', outline=None):
        if outline:
            o = font.render(s, True, outline)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                c.blit(o, o.get_rect(**{anchor: (pos[0] + dx, pos[1] + dy)}))
        im = font.render(s, True, col)
        r = im.get_rect(**{anchor: pos})
        c.blit(im, r)
        return r

    def limb(self, c, p1, p2, w, col):
        for color, lw in ((DARK, w + 4), (col, w)):
            pygame.draw.line(c, color, p1, p2, lw)
            pygame.draw.circle(c, color, p1, lw // 2)
            pygame.draw.circle(c, color, p2, lw // 2)

    def draw_head(self, c, look, p, face):
        x, y = p
        ex = lambda dx: x + face * dx
        if look == 'log':
            pygame.draw.rect(c, (150, 95, 45), (x - 17, y - 22, 34, 44), border_radius=9)
            pygame.draw.rect(c, DARK, (x - 17, y - 22, 34, 44), 2, border_radius=9)
            pygame.draw.ellipse(c, (205, 150, 90), (x - 14, y - 26, 28, 12))
            for dx in (-5, 7):
                pygame.draw.circle(c, (255, 255, 255), (ex(dx), y - 4), 4)
                pygame.draw.circle(c, DARK, (ex(dx + 1), y - 4), 2)
            pygame.draw.line(c, DARK, (ex(-6), y + 10), (ex(8), y + 10), 3)
        elif look == 'grimace':
            pygame.draw.circle(c, (157, 78, 221), (x, y), 20)
            pygame.draw.circle(c, DARK, (x, y), 20, 2)
            for dx in (4, 12):
                pygame.draw.circle(c, (255, 255, 255), (ex(dx), y - 5), 3)
                pygame.draw.circle(c, DARK, (ex(dx + 1), y - 5), 1)
            pygame.draw.arc(c, DARK, (x - 8, y + 1, 16, 12), math.pi, 2 * math.pi, 2)
        else:
            pygame.draw.circle(c, (170, 172, 182) if look == 'sigma' else SKIN, (x, y), 17)
            pygame.draw.circle(c, DARK, (x, y), 17, 2)
            if look == 'sigma':
                pygame.draw.polygon(c, (10, 10, 10), [(ex(-3), y - 9), (ex(16), y - 9), (ex(16), y - 1), (ex(-3), y - 1)])
                pygame.draw.line(c, DARK, (ex(2), y + 9), (ex(12), y + 9), 2)
            else:
                pygame.draw.circle(c, (255, 255, 255), (ex(7), y - 4), 3)
                pygame.draw.circle(c, DARK, (ex(8), y - 4), 1)
            if look == 'ren':
                pts = [(-18, -2), (-16, -22), (-8, -13), (-2, -30), (5, -14), (14, -26), (18, -2)]
                pygame.draw.polygon(c, (17, 17, 17), [(ex(a), y + b) for a, b in pts])
                pygame.draw.line(c, (229, 7, 45), (x - 18, y - 10), (x + 18, y - 10), 5)
            elif look == 'vex':
                pygame.draw.polygon(c, (229, 7, 45), [(ex(-6), y - 8), (ex(-4), y - 32), (ex(8), y - 28), (ex(10), y - 8)])
                pygame.draw.line(c, DARK, (ex(3), y - 10), (ex(12), y - 7), 3)
            elif look == 'rizz':
                pygame.draw.polygon(c, (92, 58, 30), [(ex(-17), y - 4), (ex(-14), y - 20), (ex(4), y - 24), (ex(18), y - 14), (ex(10), y - 14)])
                pygame.draw.line(c, DARK, (ex(2), y + 9), (ex(12), y + 6), 2)

    def draw_fighter(self, c, f, tag=None):
        col = (255, 255, 255) if f.flash % 4 > 1 else f.c['color']
        a = -.14 if f.stun > 0 else 0  # lean back when hit
        ca, sa = math.cos(a), math.sin(a)

        def T(lx, ly):
            dy = ly + 26
            return (f.x + f.face * (lx * ca - dy * sa), f.y + lx * sa + dy * ca - 26)

        def poly(pts, color, outline=True):
            pts = [T(*p) for p in pts]
            pygame.draw.polygon(c, color, pts)
            if outline:
                pygame.draw.polygon(c, DARK, pts, 2)

        def shoe(p):
            pygame.draw.ellipse(c, DARK, (p[0] - 8 + f.face * 3, p[1] - 4, 20, 9))

        def fist(p):
            pygame.draw.circle(c, SKIN, p, 7)
            pygame.draw.circle(c, DARK, p, 7, 2)

        pygame.draw.ellipse(c, (8, 12, 50), (f.x - 32, f.y - 7, 64, 14))
        if tag is not None and not f.sp_cd:  # special ready aura
            k = .55 + .25 * math.sin(self.frame * .2)
            pygame.draw.ellipse(c, tuple(int(v * k) for v in f.c['color']), (f.x - 40, f.y - 104, 80, 112), 3)
        wk = 0 if f.air else math.sin(f.x * .15) * 6
        kicking, punching = f.kick and 8 < f.atk < 20, (not f.kick) and 4 < f.atk < 15
        self.limb(c, T(-8, -26), T(-12 - wk, -5), 13, col)
        shoe(T(-12 - wk, -3))
        if kicking:
            self.limb(c, T(8, -26), T(74, -48), 14, col)
            shoe(T(74, -48))
        else:
            self.limb(c, T(8, -26), T(12 + wk, -5), 13, col)
            shoe(T(12 + wk, -3))
        poly([(-13, -73), (13, -73), (21, -65), (21, -27), (13, -21), (-13, -21), (-21, -27), (-21, -65)], col)
        poly([(-14, -68), (0, -68), (0, -46), (-14, -46)], tuple(min(255, v + 45) for v in col), False)
        poly([(-21, -38), (21, -38), (19, -21), (-19, -21)], (17, 17, 17))
        poly([(-21, -42), (21, -42), (21, -36), (-21, -36)], GOLD)
        poly([(-6, -45), (6, -45), (6, -33), (-6, -33)], (255, 244, 168))
        fx, fy, rx, ry = 30, -66, 12, -74  # guard stance
        if f.blk:
            fx, fy, rx, ry = 28, -82, 18, -86
        if punching:
            fx, fy = 50 + f.chain * 8, -60
        self.limb(c, T(-12, -62), T(rx, ry), 12, col)
        fist(T(rx, ry))
        self.limb(c, T(14, -62), T(fx, fy), 12, col)
        fist(T(fx, fy))
        if f.dash:
            for k in range(1, 4):
                pygame.draw.circle(c, col, T(-20 * k, -48), max(4, 18 - k * 4))
        if f.blk:
            cx, cy = T(24, -48)
            s0 = -1.1 if f.face > 0 else math.pi - 1.1
            pygame.draw.arc(c, (255, 255, 255), (cx - 44, cy - 44, 88, 88), s0, s0 + 2.2, 4)
        self.draw_head(c, f.c['look'], T(0, -84), f.face)
        if tag is not None:
            self.txt(c, f'P{tag + 1}', self.f_xs, P_COL[tag], (f.x, f.y - 138))

    def draw_projectile(self, c, p):
        x, y, s = int(p['x']), int(p['y']), p['shape']
        if s == 'bat':
            dx, dy = math.cos(p['r'] * 2) * 22, math.sin(p['r'] * 2) * 22
            pygame.draw.line(c, DARK, (x - dx, y - dy), (x + dx, y + dy), 12)
            pygame.draw.line(c, (198, 134, 66), (x - dx, y - dy), (x + dx, y + dy), 8)
        elif s == 'heart':
            pygame.draw.circle(c, (255, 60, 140), (x - 8, y - 5), 10)
            pygame.draw.circle(c, (255, 60, 140), (x + 8, y - 5), 10)
            pygame.draw.polygon(c, (255, 60, 140), [(x - 17, y - 1), (x + 17, y - 1), (x, y + 18)])
        elif s == 'fire':
            r = 18 + int(math.sin(self.frame * .6) * 3)
            pygame.draw.circle(c, (229, 70, 20), (x, y), r)
            pygame.draw.circle(c, (255, 160, 20), (x, y), r - 6)
            pygame.draw.circle(c, (255, 240, 150), (x, y), r - 12)
        else:
            pygame.draw.ellipse(c, (157, 78, 221), (x - 28, y - 18, 56, 36))
            pygame.draw.ellipse(c, (220, 170, 255), (x - 18, y - 11, 36, 22))

    def draw_hud(self, c):
        for i, f in enumerate(self.F):
            x0 = 30 if i == 0 else W - 410
            pct = f.hp / f.c['hp']
            wf = 368 * pct
            if i == 0:
                bg = [(x0 + 12, 30), (x0 + 380, 30), (x0 + 368, 50), (x0, 50)]
                fill = [(x0 + 12, 30), (x0 + 12 + wf, 30), (x0 + wf, 50), (x0, 50)]
            else:
                bg = [(x0, 30), (x0 + 368, 30), (x0 + 380, 50), (x0 + 12, 50)]
                fill = [(x0 + 368 - wf, 30), (x0 + 368, 30), (x0 + 380, 50), (x0 + 380 - wf, 50)]
            pygame.draw.polygon(c, (32, 28, 64), bg)
            col = P_COL[i]
            if pct < .25:
                k = .5 + .5 * math.sin(self.frame * .4)
                col = tuple(int(v + (255 - v) * k * .6) for v in col)
            if pct > 0:
                pygame.draw.polygon(c, col, fill)
            pygame.draw.polygon(c, (60, 56, 110), bg, 2)
            self.txt(c, f"P{i + 1} {f.c['name']}", self.f_sm, P_COL[i], (x0 if i == 0 else x0 + 380, 18),
                     'midleft' if i == 0 else 'midright')
            for j in range(2):
                px = x0 + 10 + j * 20 if i == 0 else x0 + 370 - j * 20
                pygame.draw.circle(c, GOLD if self.score[i] > j else (141, 137, 184), (px, 66), 7, 0 if self.score[i] > j else 2)
        secs = max(0, math.ceil(self.t / FPS))
        hot = secs <= 10 and self.state == 'fight'
        self.txt(c, str(secs), self.f_big, (255, 59, 90) if hot else (255, 255, 255), (480, 34), outline=(0, 0, 0))

    def draw_banner(self, c):
        if not self.banner:
            return
        text, t0 = self.banner
        age = self.frame - t0
        w, h = self.f_huge.size(text)
        im = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
        for col, off in (((0, 0, 0), 8), (GOLD, 4), ((255, 255, 255), 0)):
            im.blit(self.f_huge.render(text, True, col), (off, off))
        im = pygame.transform.rotozoom(im, 0, 1 + max(0, 14 - age) * .1)
        im.set_alpha(min(255, 60 + age * 50))
        c.blit(im, im.get_rect(center=(480, 200)))

    def draw_select(self, c):
        for y in range(H):
            k = y / H
            pygame.draw.line(c, (int(90 - 80 * k), int(18 - 12 * k), int(48 - 20 * k)), (0, y), (W, y))
        self.txt(c, 'BRAINROT MANIA', self.f_big, GOLD, (480, 62), outline=(120, 40, 160))
        self.txt(c, 'Pick your fighter. Punch button (F / K) locks in. Match starts when both are ready.',
                 self.f_sm, (141, 137, 184), (480, 108))
        for i, ch in enumerate(CHARS):
            r = pygame.Rect(31 + i * 151, 135, 143, 300)
            p1, p2 = self.sel[0] == i, self.sel[1] == i
            border = GOLD if p1 and p2 else P_COL[0] if p1 else P_COL[1] if p2 else (45, 42, 85)
            lift = -6 if (p1 and self.locked[0]) or (p2 and self.locked[1]) else 0
            r.y += lift
            pygame.draw.rect(c, (18, 16, 42), r, border_radius=8)
            pygame.draw.rect(c, border, r, 4 if (p1 or p2) else 2, border_radius=8)
            pf = self.preview[i]
            pf.x, pf.y = r.centerx, r.y + 175
            pf.sp_cd = 0
            self.draw_fighter(c, pf)
            self.txt(c, ch['name'], self.f_xs, ch['color'], (r.centerx, r.y + 192))
            for j, (lab, v) in enumerate((('HP', ch['hp'] / 135), ('SPD', ch['spd'] / 4.2), ('PWR', ch['dmg'] / 10))):
                yy = r.y + 214 + j * 15
                self.txt(c, lab, self.f_xs, (141, 137, 184), (r.x + 8, yy), 'midleft')
                pygame.draw.rect(c, (27, 24, 56), (r.x + 38, yy - 3, 97, 7))
                pygame.draw.rect(c, GOLD, (r.x + 38, yy - 3, int(97 * v), 7))
            self.txt(c, ch['sp'], self.f_xs, GOLD, (r.centerx, r.y + 266))
            self.txt(c, ch['desc'], self.f_xs, (141, 137, 184), (r.centerx, r.y + 283))
            for p, on in ((0, p1), (1, p2)):
                if on:
                    label = f'P{p + 1}' + (' READY' if self.locked[p] else '')
                    tw = self.f_xs.size(label)[0] + 12
                    tr = pygame.Rect(r.x + 6 if p == 0 else r.right - 6 - tw, r.y - 11, tw, 20)
                    pygame.draw.rect(c, P_COL[p], tr, border_radius=3)
                    self.txt(c, label, self.f_xs, (0, 0, 0), tr.center)
        self.txt(c, 'P1  A/D browse, F lock in   |   P2  LEFT/RIGHT browse, K lock in', self.f_sm, (236, 235, 255), (480, 468))
        self.txt(c, 'Fight keys   P1: F punch, G kick, H special   |   P2: K punch, L kick, ; special   |   hold back to block',
                 self.f_xs, (141, 137, 184), (480, 494))

    def draw_end(self, c):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((5, 3, 15, 170))
        c.blit(ov, (0, 0))
        w, l = self.winner, 1 - self.winner
        cx, cy = 270, 200 + math.sin(self.frame * .1) * 10
        gold, dk = GOLD, (200, 150, 0)  # trophy
        pygame.draw.polygon(c, gold, [(cx - 55, cy - 60), (cx + 55, cy - 60), (cx + 34, cy), (cx - 34, cy)])
        pygame.draw.ellipse(c, (255, 240, 150), (cx - 55, cy - 70, 110, 22))
        pygame.draw.circle(c, gold, (cx - 58, cy - 34), 22, 7)
        pygame.draw.circle(c, gold, (cx + 58, cy - 34), 22, 7)
        pygame.draw.rect(c, dk, (cx - 10, cy, 20, 38))
        pygame.draw.rect(c, gold, (cx - 38, cy + 38, 76, 18), border_radius=4)
        self.txt(c, '1', self.f_big, dk, (cx, cy - 28))
        k = .5 + .5 * math.sin(self.frame * .15)
        shine = (255, int(200 + 55 * k), int(60 + 150 * k))
        self.txt(c, f"P{w + 1} {CHARS[self.sel[w]]['name']}", self.f_mid, shine, (cx, 330), outline=(90, 50, 0))
        self.txt(c, 'WINS THE MATCH!', self.f_mid, shine, (cx, 364), outline=(90, 50, 0))
        self.txt(c, f'{self.score[0]} - {self.score[1]}', self.f_sm, (236, 235, 255), (cx, 400))
        self.txt(c, f"P{l + 1} {CHARS[self.sel[l]]['name']}", self.f_mid, (255, 59, 59), (690, 100))
        for i, line in enumerate(self.rage):
            red = i % 2 == 0
            im = self.f_sm.render(line, True, (255, 255, 255) if red else (255, 59, 59))
            tile = pygame.Surface((im.get_width() + 22, im.get_height() + 14), pygame.SRCALPHA)
            tile.fill((229, 7, 45) if red else (17, 17, 17))
            pygame.draw.rect(tile, (255, 255, 255) if red else (255, 59, 59), tile.get_rect(), 2)
            tile.blit(im, (11, 7))
            tile = pygame.transform.rotate(tile, math.sin(self.frame * .35 + i * 1.7) * 3)
            c.blit(tile, tile.get_rect(center=(690 + math.sin(self.frame * .35 + i) * 3, 160 + i * 56)))
        self.button = pygame.Rect(0, 0, 240, 50)
        self.button.center = (480, 490)
        if ARCADE:  # the arcade takes over for names and the next match
            return
        pygame.draw.rect(c, GOLD, self.button, border_radius=6)
        self.txt(c, 'PLAY AGAIN', self.f_mid, (0, 0, 0), self.button.center)

    def draw(self, screen):
        c = self.canvas
        if self.state == 'select':
            self.draw_select(c)
        else:
            self.draw_arena(c)
            for f in self.F:
                self.draw_fighter(c, f, self.F.index(f))
            for p in self.P:
                self.draw_projectile(c, p)
        for p in self.parts:
            if 'txt' in p:
                im = self.f_mid.render(p['txt'], True, p['col'])
                im.set_alpha(int(255 * p['life'] / p['max']))
                c.blit(im, im.get_rect(center=(p['x'], p['y'])))
            else:
                s = max(1, int(p['s'] * min(1, p['life'] / 30)))
                pygame.draw.rect(c, p['col'], (p['x'], p['y'], s, s))
        if self.state not in ('select',):
            self.draw_hud(c)
            self.draw_banner(c)
        if self.state == 'matchEnd':
            self.draw_end(c)
        ox, oy = (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake)) if self.shake > .5 else (0, 0)
        screen.fill((0, 0, 0))
        screen.blit(c, (ox, oy))


# ============================== BUTTON CONTROLLER ==============================
class Controller:
    """Reads the Arduino's "<KEY>1" (pressed) / "<KEY>0" (released) lines and turns them into
    the same keys the keyboard uses, so the game itself does not care where a press came from."""

    NAMES = {'LEFT': pygame.K_LEFT, 'RIGHT': pygame.K_RIGHT, 'UP': pygame.K_UP, 'DOWN': pygame.K_DOWN,
             'SPACE': pygame.K_SPACE, 'ENTER': pygame.K_RETURN, ';': pygame.K_SEMICOLON,
             '': pygame.K_UP}  # the first sketch sent a blank name for player 2's jump

    def __init__(self):
        self.held = set()
        self.ser = arcade_mode.open_controller(9600) if arcade_mode else None

    def key_for(self, name):
        if name in self.NAMES:
            return self.NAMES[name]
        if len(name) == 1:
            try:
                return pygame.key.key_code(name.lower())
            except ValueError:
                return None
        return None

    def poll(self):
        """Read everything waiting. Presses are posted as normal key events (menus, idle timer)."""
        if not self.ser:
            return
        try:
            while self.ser.in_waiting > 0:
                line = arcade_mode.read_line(self.ser).upper()
                if not line or line[-1] not in '01':
                    continue
                key = self.key_for(line[:-1].strip())
                if key is None:
                    continue
                if line[-1] == '1' and key not in self.held:
                    self.held.add(key)
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode='', scancode=0))
                elif line[-1] == '0' and key in self.held:
                    self.held.discard(key)
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key, mod=0, unicode='', scancode=0))
        except Exception as e:  # unplugged mid-game: keep going on the keyboard
            arcade_mode.log('controller lost:', e)
            self.ser, self.held = None, set()


class Keys:
    """Keyboard state plus whatever the controller is holding."""

    def __init__(self, keyboard, held):
        self.keyboard, self.held = keyboard, held

    def __getitem__(self, k):
        return self.keyboard[k] or k in self.held


def main():
    pygame.init()
    if ARCADE:
        screen = arcade_mode.open_window((W, H), 'Brainrot Mania')
        session = arcade_mode.Session()
    else:
        screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption('Brainrot Mania')
    pad = Controller()
    game, clock = Game(), pygame.time.Clock()
    while True:
        pad.poll()
        for e in pygame.event.get():
            if ARCADE:
                session.handle_event(e)
                # Esc is held to leave (see arcade_mode), and the arcade decides when to play again
                if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    continue
                if e.type == pygame.KEYDOWN and game.state == 'matchEnd':
                    continue
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if game.state == 'select':
                    game.select_key(e.key)
                elif game.state == 'matchEnd' and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    game.reset_all()
            if e.type == pygame.MOUSEBUTTONDOWN and game.state == 'matchEnd' and game.button.collidepoint(e.pos):
                game.reset_all()
        if ARCADE:
            reason = session.exit_reason()
            if reason:
                arcade_mode.finish(None, reason)
            if game.state == 'matchEnd' and game.state_t >= MATCH_END_FRAMES:
                w = game.winner
                arcade_mode.finish(1, winner=w, winnerName=f'PLAYER {w + 1}',
                                   title=f"{CHARS[game.sel[w]]['name'].upper()} WINS!")
        game.update(Keys(pygame.key.get_pressed(), pad.held))
        game.draw(screen)
        if ARCADE:
            session.draw_exit_hint(screen)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
