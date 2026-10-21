'use strict';
/* IEEE Arcade menu.
   Flow: menu -> how to play -> game -> score and name entry -> leaderboard -> back to that game's how to play.
   Each laptop acts as a station for one game. Esc on the how-to-play screen goes back to the full menu.
   Web games run in an iframe and report their score with postMessage({type:'arcade:over', score}).
   Python games are launched by server.py and report through /api/launch. */

const $ = id => document.getElementById(id);
const READ_MS = 3000;         // how long the rules stay up before a game can start
const IDLE_MS = 60000;        // nobody touches anything -> back to the menu
const ENTRY_IDLE_MS = 30000;  // name entry left alone -> save what is there
const BOARD_IDLE_MS = 10000;  // leaderboard shown this long after a game
const EXIT_HOLD_MS = 2000;    // helpers hold Esc this long to leave a game
const END_DELAY_MS = 1200;    // a short look at the game's own game-over screen (its input is frozen meanwhile)
const STATION_KEY = 'arcade-station'; // remembers which game this laptop is running
const NAME_LEN = 5;
const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ';
const SCREENS = ['menu', 'howto', 'play', 'result', 'tester'];

let games = [];
let sel = 0;
let screen = 'menu';
let current = null;        // game being played
let solo = false;          // playing the 1-player (versus computer) mode of a 2-player game
let readyAt = 0;           // when the how-to-play screen accepts a start
let ended = false;         // game already reported its result
let lastInput = Date.now();
let escDownAt = 0;
let pollTimer = null;
let resultMode = null;     // 'entry' or 'board'
let boardShownAt = 0;
let resultShownAt = 0;
let lastResult = null;
let name = [], pos = 0;

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function log(msg) {
  fetch('/api/log', { method: 'POST', body: JSON.stringify({ msg }) }).catch(() => {});
}
window.addEventListener('error', e => log(`menu error: ${e.message} at ${e.filename}:${e.lineno}`));

async function api(path, body) {
  const opts = body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  const r = await fetch(path, opts);
  return r.json();
}

let toastTimer = null;
function toast(text, ms = 3000) {
  const t = $('toast');
  t.textContent = text;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, ms);
}

function show(id) {
  for (const s of SCREENS) $(s).hidden = s !== id;
  screen = id;
  lastInput = Date.now();
}

/* ---------- sound: small arcade blips made in the browser ---------- */
let actx = null;
function beep(freq, dur = 0.07, type = 'square', vol = 0.05) {
  try {
    actx = actx || new (window.AudioContext || window.webkitAudioContext)();
    const o = actx.createOscillator(), g = actx.createGain(), t = actx.currentTime;
    o.type = type; o.frequency.value = freq;
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(actx.destination);
    o.start(t); o.stop(t + dur);
  } catch (e) {}
}
const sfx = {
  move: () => beep(660, 0.05),
  pick: () => { beep(880, 0.08); setTimeout(() => beep(1320, 0.1), 70); },
  back: () => beep(330, 0.08),
  save: () => [523, 659, 784, 1047].forEach((f, i) => setTimeout(() => beep(f, 0.1), i * 80)),
};

/* ---------- 1 or 2 players ---------- */
// A game's settings for the chosen mode: solo mode can override the goal, rules, controls, and scoring
const cfg = (g = current) => (solo && g.solo ? Object.assign({}, g, g.solo) : g);
// Solo and 2-player scores are kept on separate leaderboards
const boardId = (g = current, isSolo = solo) => g.id + (isSolo && g.solo ? '-solo' : '');

/* ---------- leaderboards ---------- */
function renderScores(ol, rows, label, limit, highlight) {
  if (!rows.length) { ol.innerHTML = '<li class="empty">NO SCORES YET. BE THE FIRST!</li>'; return; }
  ol.innerHTML = rows.slice(0, limit).map((r, i) =>
    `<li class="${i + 1 === highlight ? 'me' : ''}"><span class="rank">${i + 1}.</span><span class="name">${esc(r.name)}</span><span class="pts">${r.score} ${esc(label)}</span></li>`
  ).join('');
}

/* ---------- menu ---------- */
async function loadGames() {
  try {
    games = await (await fetch('games.json')).json();
  } catch (e) {
    log('could not load games.json: ' + e);
    toast('COULD NOT LOAD THE GAME LIST', 10000);
    return;
  }
  // Reopen the game this laptop was running before the arcade was restarted
  let station = null;
  try { station = games.find(g => g.id === localStorage.getItem(STATION_KEY)); } catch (e) {}
  if (station) openHowto(station);
  else toMenu();
}

function renderMenu() {
  $('grid').innerHTML = games.map((g, i) => `
    <div class="card${i === sel ? ' on' : ''}" style="--accent:${g.colour}">
      <h2>${esc(g.title)}</h2>
      <div class="meta"><span class="tag">${g.solo ? '1 OR 2 PLAYERS' : g.players === 1 ? '1 PLAYER' : `${g.players} PLAYERS`}</span></div>
      <div class="top" id="top-${g.id}">NO SCORES YET</div>
    </div>`).join('');
  for (const g of games) {
    // Games with a solo mode show the solo record, since that is the default
    const label = (g.solo ? g.solo.score : g.score).label;
    api('/api/scores/' + boardId(g, true)).then(rows => {
      const el = $('top-' + g.id);
      if (el && rows.length) el.innerHTML = `TOP &nbsp;<b>${esc(rows[0].name)}</b> &nbsp;${rows[0].score} ${esc(label)}`;
    }).catch(() => {});
  }
}

function moveSel(dx, dy) {
  const cols = getComputedStyle($('grid')).gridTemplateColumns.split(' ').length || 3;
  let next = sel + dx + dy * cols;
  if (next < 0 || next >= games.length) return;
  sel = next;
  document.querySelectorAll('.card').forEach((c, i) => c.classList.toggle('on', i === sel));
  sfx.move();
}

// The full menu with every game. Only reached on purpose (Esc on the how-to-play screen).
function toMenu(message) {
  stopGame();
  api('/api/usb', { active: true }).catch(() => {});
  try { localStorage.removeItem(STATION_KEY); } catch (e) {}
  show('menu');
  renderMenu();
  window.focus();
  if (message) toast(message);
}

// Where a station goes after a game: back to that game's how-to-play screen, ready for the next player
function toHome(message) {
  if (!current) return toMenu(message);
  stopGame();
  api('/api/usb', { active: true }).catch(() => {});
  openHowto(current, true);
  window.focus();
  if (message) toast(message);
}

/* ---------- how to play ---------- */
async function renderHowto() {
  const g = cfg();
  $('htTitle').textContent = g.title;
  $('htPlayers').textContent = current.solo ? '' : g.players === 1 ? '1 PLAYER' : `${g.players} PLAYERS`;
  $('htMode').hidden = !current.solo;
  $('modeSolo').classList.toggle('on', solo);
  $('modeDuo').classList.toggle('on', !solo);
  $('htGoal').textContent = g.goal;
  $('htRules').innerHTML = g.rules.map(r => `<li>${esc(r)}</li>`).join('');
  $('htControls').innerHTML = g.controls.map(([keys, what]) =>
    `<div class="control"><span class="keys">${keys.split(/\s+/).map(k => `<span class="key">${esc(k)}</span>`).join('')}</span><span>${esc(what)}</span></div>`
  ).join('');
  $('htController').textContent = g.controller;
  const id = boardId();
  try {
    const rows = await api('/api/scores/' + id);
    if (boardId() === id) renderScores($('htBoard'), rows, g.score.label, 5);
  } catch (e) {}
}

async function openHowto(g, keepMode) {
  current = g;
  sel = Math.max(0, games.indexOf(g));
  if (!keepMode) solo = !!g.solo; // solo is the default for games that have it
  try { localStorage.setItem(STATION_KEY, g.id); } catch (e) {}
  $('htBoard').innerHTML = '';
  renderHowto();
  show('howto');
  sfx.pick();

  // Rules stay up for a moment so players actually read them
  readyAt = Date.now() + READ_MS;
  const fill = $('readFill');
  fill.style.transition = 'none';
  fill.style.width = '0';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    fill.style.transition = `width ${READ_MS}ms linear`;
    fill.style.width = '100%';
  }));
  const startText = $('startText');
  startText.textContent = 'READ THE RULES';
  startText.classList.remove('go');
  setTimeout(() => {
    if (screen === 'howto' && current === g) {
      startText.textContent = 'PRESS ANY BUTTON TO START';
      startText.classList.add('go');
    }
  }, READ_MS);
}

/* ---------- playing ---------- */
function startGame() {
  const g = current;
  ended = false;
  show('play');
  sfx.pick();
  log('start ' + g.id);
  if (g.type === 'web') {
    $('pyWait').hidden = true;
    $('frame').hidden = false;
    const url = '/' + g.path.split('/').map(encodeURIComponent).join('/') + '?arcade=1' + (solo && g.solo ? '&solo=1' : '');
    // A game that reads its own USB controller needs the arcade to let go of the ports first
    if (g.ownsUsb) api('/api/usb', { active: false }).catch(() => {}).then(() => { if (screen === 'play') $('frame').src = url; });
    else $('frame').src = url;
  } else {
    $('frame').hidden = true;
    $('pyTitle').textContent = g.title;
    $('pyWait').hidden = false;
    api('/api/launch/' + g.id, {}).then(r => {
      if (r.error) { log('launch failed: ' + r.error); toHome('THAT GAME COULD NOT START'); return; }
      pollTimer = setInterval(pollPython, 500);
    }).catch(() => toHome('THAT GAME COULD NOT START'));
  }
}

async function pollPython() {
  let s;
  try { s = await api('/api/launch'); } catch (e) { return; }
  if (s.running || screen !== 'play') return;
  clearInterval(pollTimer);
  pollTimer = null;
  window.focus();
  const r = s.result || {};
  if (r.reason === 'crash') toHome('THE GAME CLOSED UNEXPECTEDLY');
  else if (r.reason !== 'over' || r.score == null) toHome();
  else showResult({ score: r.score });
}

function stopGame() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; api('/api/stop', {}).catch(() => {}); }
  const f = $('frame');
  if (f.getAttribute('src') && f.getAttribute('src') !== 'about:blank') f.src = 'about:blank';
}

// The game page is on the same server, so the menu can listen to its keys for Esc-hold and idle
$('frame').addEventListener('load', () => {
  const f = $('frame');
  if (screen !== 'play' || !f.contentWindow || f.contentWindow.location.href === 'about:blank') return;
  try {
    const w = f.contentWindow;
    w.addEventListener('keydown', e => onKey(e, true), true);
    w.addEventListener('keyup', e => onKeyUp(e), true);
    blockBrowserMouse(w);
    w.addEventListener('error', e => log(`${current.id} error: ${e.message} at line ${e.lineno}`));
    w.focus();
  } catch (e) {
    log('could not attach to game frame: ' + e);
  }
});

window.addEventListener('message', e => {
  const d = e.data;
  if (e.origin !== location.origin || !d || d.type !== 'arcade:over') return;
  if (screen !== 'play' || ended) return;
  // Freeze the game right away so nobody can start another round before the name screen
  ended = true;
  window.focus();
  log(`over ${current.id} ${JSON.stringify(d)}`);
  setTimeout(() => { if (screen === 'play') { stopGame(); showResult(d); } }, END_DELAY_MS);
});

/* ---------- results and name entry ---------- */
async function showResult(d) {
  const g = cfg();
  lastResult = d;
  const wins = g.score.mode === 'wins';
  const winner = d.winner != null ? (d.winnerName || `PLAYER ${d.winner + 1}`) : null;
  $('resHead').textContent = winner ? 'WINNER' : 'GAME OVER';
  $('resTitle').textContent = d.title || (winner ? `${winner} WINS!` : g.title);
  $('resScore').textContent = wins ? '' : d.score;
  $('resLabel').textContent = wins ? '' : g.score.label;
  $('resScore').parentElement.hidden = wins;
  $('entry').hidden = true;
  $('resBoard').hidden = true;
  resultMode = null;
  resultShownAt = Date.now();
  show('result');
  window.focus();

  let rows = [];
  try { rows = await api('/api/scores/' + boardId()); } catch (e) {}
  const score = Number(d.score) || 0;
  // Wins boards count every win. Losing to the computer (score 0) doesn't count.
  const qualifies = wins ? score > 0 : score > 0 && (rows.length < 10 || score > rows[9].score);
  if (qualifies) {
    $('entryPrompt').textContent = winner ? `${winner}, ENTER YOUR NAME`
      : wins ? 'ENTER YOUR NAME FOR THE BOARD'
      : g.players > 1 && !solo ? 'NEW HIGH SCORE! ENTER YOUR TEAM NAME' : 'NEW HIGH SCORE! ENTER YOUR NAME';
    startEntry();
  } else {
    showBoard(rows, null, score > 0 ? 'SO CLOSE! NOT IN THE TOP 10 THIS TIME' : 'LEADERBOARD');
  }
}

function startEntry() {
  name = ['A', ' ', ' ', ' ', ' '];
  pos = 0;
  resultMode = 'entry';
  $('entry').hidden = false;
  renderSlots();
  sfx.pick();
}

function renderSlots() {
  $('slots').innerHTML = name.map((c, i) => `<div class="slot${i === pos ? ' on' : ''}">${c === ' ' ? '_' : esc(c)}</div>`).join('');
}

function entryKey(e) {
  const k = e.key;
  if (k === 'ArrowUp' || k === 'ArrowDown') {
    const step = k === 'ArrowUp' ? 1 : -1;
    const i = CHARS.indexOf(name[pos]);
    name[pos] = name[pos] === ' ' && step > 0 ? 'A' : CHARS[(i + step + CHARS.length) % CHARS.length];
    sfx.move();
  } else if (k === 'ArrowRight' || k === ' ') {
    pos = Math.min(NAME_LEN - 1, pos + 1); sfx.move();
  } else if (k === 'ArrowLeft') {
    pos = Math.max(0, pos - 1); sfx.move();
  } else if (k === 'Backspace') {
    if (name[pos] === ' ' && pos > 0) pos--;
    name[pos] = ' '; sfx.back();
  } else if (k === 'Enter') {
    saveEntry(); return;
  } else if (/^[a-z0-9]$/i.test(k)) {
    name[pos] = k.toUpperCase();
    pos = Math.min(NAME_LEN - 1, pos + 1);
    sfx.move();
  } else return;
  renderSlots();
}

async function saveEntry() {
  if (resultMode !== 'entry') return;
  resultMode = 'saving';
  const entered = name.join('').trim() || 'ANON';
  try {
    const r = await api('/api/scores/' + boardId(), { name: entered, score: Number(lastResult.score) || 0 });
    if (r.error) throw new Error(r.error);
    sfx.save();
    $('entry').hidden = true;
    showBoard(r.rows, r.rank, r.rank && r.rank <= 10 ? `YOU ARE #${r.rank}!` : 'LEADERBOARD');
  } catch (e) {
    log('could not save score: ' + e);
    toHome('SCORE COULD NOT BE SAVED');
  }
}

function showBoard(rows, rank, title) {
  resultMode = 'board';
  boardShownAt = Date.now();
  lastInput = Date.now();
  $('resBoardTitle').textContent = title;
  renderScores($('resScores'), rows, cfg().score.label, 10, rank);
  $('resBoard').hidden = false;
}

/* ---------- controller test (F2) ---------- */
function testKey(e) {
  const label = e.key === ' ' ? 'SPACE' : e.key.length === 1 ? e.key.toUpperCase() : e.key.toUpperCase();
  $('testKey').textContent = label;
  const li = document.createElement('li');
  li.textContent = `${label}   (${e.code})`;
  $('testLog').prepend(li);
  while ($('testLog').children.length > 8) $('testLog').lastChild.remove();
  sfx.move();
}

/* ---------- keys ---------- */
let testerFromStation = false;
function openTester(fromStation) {
  testerFromStation = fromStation;
  show('tester');
  $('testKey').textContent = '-';
  $('testLog').innerHTML = '';
}

// Browser shortcuts a player could hit by accident (F1 opens Chrome Help, F12 developer tools,
// Ctrl+P print, Ctrl+F find, Ctrl and +/- zoom...). The arcade swallows them before Chrome acts.
// Alt+F4 and Alt+Tab still work, since Windows handles those itself.
const BROWSER_KEYS = ['F1', 'F3', 'F6', 'F7', 'F10', 'F11', 'F12', 'BrowserBack', 'BrowserForward', 'BrowserSearch', 'BrowserHome'];
function blockBrowserKeys(e) {
  const ctrlCombo = (e.ctrlKey || e.metaKey) && !['Control', 'Meta'].includes(e.key);
  const altArrow = e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'Home');
  if (BROWSER_KEYS.includes(e.key) || ctrlCombo || altArrow) {
    e.preventDefault();
    e.stopImmediatePropagation();
    return true;
  }
  return false;
}
// Right-click menus and Ctrl+scroll zoom, blocked the same way
function blockBrowserMouse(w) {
  w.addEventListener('contextmenu', e => e.preventDefault(), true);
  w.addEventListener('wheel', e => { if (e.ctrlKey) e.preventDefault(); }, { capture: true, passive: false });
}
blockBrowserMouse(window);

function onKey(e, fromFrame) {
  if (blockBrowserKeys(e)) return;
  lastInput = Date.now();
  if (e.key === 'Escape' && !escDownAt) escDownAt = Date.now();
  if (fromFrame) {
    // The game handles its own keys, except after it has ended: then nothing gets through
    if (ended) { e.preventDefault(); e.stopImmediatePropagation(); }
    return;
  }

  const k = e.key;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' ', 'Backspace', 'Tab', 'F2'].includes(k)) e.preventDefault();
  if (e.repeat && screen !== 'menu') return;

  if (screen === 'menu') {
    if (k === 'ArrowLeft' || k === 'a' || k === 'A') moveSel(-1, 0);
    else if (k === 'ArrowRight' || k === 'd' || k === 'D') moveSel(1, 0);
    else if (k === 'ArrowUp' || k === 'w' || k === 'W') moveSel(0, -1);
    else if (k === 'ArrowDown' || k === 's' || k === 'S') moveSel(0, 1);
    else if (k === 'Enter' || k === ' ') { if (games[sel]) openHowto(games[sel]); }
    else if (k === 'F2') openTester(false);
  } else if (screen === 'howto') {
    // Esc here is the only way from a game's station back to the full menu
    if (k === 'Escape' || k === 'Backspace') { sfx.back(); toMenu(); }
    else if (k === 'F2') openTester(true);
    else if (current.solo && (k === 'ArrowLeft' || k === 'ArrowRight')) { solo = !solo; sfx.move(); renderHowto(); }
    else if (Date.now() >= readyAt && !['Shift', 'Control', 'Alt', 'Meta'].includes(k)) startGame();
  } else if (screen === 'result') {
    // Ignore leftover button mashing from the game for a moment
    if (Date.now() - resultShownAt < 1200) return;
    if (resultMode === 'entry') entryKey(e);
    else if (resultMode === 'board' && Date.now() - boardShownAt > 1500 && k !== 'Escape') toHome();
  } else if (screen === 'tester') {
    if (k === 'F2') testerFromStation ? toHome() : toMenu();
    else testKey(e);
  }
}

function onKeyUp(e) {
  if (e.key === 'Escape') escDownAt = 0;
  if (ended && screen === 'play' && e.view !== window) { e.preventDefault(); e.stopImmediatePropagation(); }
}

// Capture phase, so the arcade sees every key first
window.addEventListener('keydown', e => onKey(e, false), true);
window.addEventListener('keyup', onKeyUp, true);
window.addEventListener('blur', () => { escDownAt = 0; });

/* ---------- USB controllers read by the server (Arduino key messages like W1 / W0) ---------- */
const USB_KEYS = {
  SPACE: [' ', 'Space'], ENTER: ['Enter', 'Enter'],
  LEFT: ['ArrowLeft', 'ArrowLeft'], RIGHT: ['ArrowRight', 'ArrowRight'],
  UP: ['ArrowUp', 'ArrowUp'], DOWN: ['ArrowDown', 'ArrowDown'],
};
function usbKey(name, down) {
  const [key, code] = USB_KEYS[name] || (/^[0-9]$/.test(name) ? [name, 'Digit' + name] : [name.toLowerCase(), 'Key' + name]);
  const inGame = screen === 'play' && current && current.type === 'web' && $('frame').contentWindow;
  const w = inGame ? $('frame').contentWindow : window;
  try {
    const target = w.document.activeElement || w.document.body;
    target.dispatchEvent(new w.KeyboardEvent(down ? 'keydown' : 'keyup', { key, code, bubbles: true, cancelable: true }));
  } catch (e) {}
}
function connectUsb() {
  const src = new EventSource('/api/keys');
  src.onmessage = e => {
    const d = JSON.parse(e.data);
    usbKey(d.key, d.down);
  };
  // EventSource reconnects by itself if the connection drops
}
connectUsb();

// Show helpers which USB controllers the arcade can see
setInterval(async () => {
  if (screen !== 'menu' && screen !== 'tester') return;
  try {
    const s = await api('/api/usb');
    const text = s.ports.length ? `USB ${s.ports.join(' ')}` : '';
    $('usbStatus').textContent = text;
    $('testUsb').textContent = s.ports.length ? `USB ports being read: ${s.ports.join(', ')}` : 'No USB controllers plugged in.';
  } catch (e) {}
}, 2000);

/* ---------- Esc-hold exit bar ---------- */
function tick() {
  const holding = escDownAt && screen === 'play';
  $('exitBar').hidden = !holding;
  if (holding) {
    const p = Math.min(1, (Date.now() - escDownAt) / EXIT_HOLD_MS);
    $('exitFill').style.width = (p * 100) + '%';
    if (p >= 1) {
      escDownAt = 0;
      log('helper closed ' + (current && current.id));
      toHome('GAME CLOSED');
    }
  }
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);

/* ---------- idle: back to the game's how-to-play screen when nobody is playing ---------- */
setInterval(() => {
  const idle = Date.now() - lastInput;
  if (screen === 'tester' && idle > IDLE_MS) testerFromStation ? toHome() : toMenu();
  else if (screen === 'play' && current && current.type === 'web' && !ended && idle > IDLE_MS) {
    log('idle, closing ' + current.id);
    toHome('NOBODY WAS PLAYING');
  } else if (screen === 'result' && resultMode === 'entry' && idle > ENTRY_IDLE_MS) saveEntry();
  else if (screen === 'result' && resultMode === 'board' && idle > BOARD_IDLE_MS) toHome();
}, 1000);

loadGames();
