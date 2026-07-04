"""Study logger - desktop widget for any subjects (sister of ca_countdown_widget.pyw).

Pick a subject, run a stopwatch (start / pause / end), every ended session is
appended to study_log.jsonl. The lower panel shows TODAY's time per subject as
bars (+ 7-day sparkline); click the panel header to flip to a 14-day heatmap.
First launch pops a setup window: type your own subjects (any stream) -
saved to subjects.json next to this script.

Plain tkinter, no browser engine. Pins itself to the desktop layer (behind all
apps, in front of the wallpaper). Interact with it when the desktop is visible
(Win+D), same as the countdown widget.

Run silently (normal use):   pythonw study_logger_widget.pyw
Run with console (debug):    python study_logger_widget.pyw
Re-open the setup popup:     python study_logger_widget.pyw --setup
Preview as normal window:    python study_logger_widget.pyw --preview
Move it:                     double-click a blank spot -> border turns red ->
                             drag anywhere -> double-click again to lock.
                             Position is remembered in widget_state.json.
Quit:                        right-click the widget (a running session is
                             ended and saved first - nothing is lost).

Crash safety: while a session runs, progress is checkpointed to
active_session.json every 30 s. If the PC dies mid-session, the next launch
recovers the time up to the last checkpoint into the log.
"""

import os
import sys
import json
import ctypes
import datetime as dt
import tkinter as tk
import tkinter.font as tkfont

# ---------------- config ----------------
# defaults only - real subjects live in subjects.json, created by the
# first-run setup popup (re-open it anytime:  python study_logger_widget.pyw --setup)
TITLE = 'STUDY LOG'
SUBJECTS = [                      # (full name, chip label, log key)
    ('Advanced Accounting',    'ACC',  'Adv Acc'),
    ('Corporate & Other Laws', 'LAW',  'Law'),
    ('Taxation',               'TAX',  'Tax'),
    ('Cost & Mgmt Accounting', 'COST', 'Costing'),
    ('Auditing & Ethics',      'AUD',  'Audit'),
    ('FM & SM',                'FMSM', 'FM-SM'),
]
MAX_SUBJECTS = 8
HEAT_DAYS   = 14        # columns in the heatmap view
SPARK_DAYS  = 7         # bars in the sparkline under the TODAY view
MIN_SESSION = 30        # sessions shorter than this (seconds) are discarded
CHECKPOINT  = 30        # seconds between crash-safety checkpoints

TRANSPARENT = True      # colorkey transparency, same as the countdown widget
BG    = '#010101'       # root bg = transparency key (click-through)
CARD  = '#000000'       # widget body - solid, clickable, invisible on black wallpaper
FG    = '#f2f2f2'
DIM   = '#8a8a8a'
FAINT = '#4a4a4a'
RED   = '#e63946'
BAR_W, ROW_H = 150, 22          # today-view bar canvas geometry
CELL, CELL_GAP = 15, 3          # heatmap cell size / spacing

# subject identity colours - deep jewel tones (user hates pastels), NO
# reds/oranges (those always mean urgency). Text = urgency, graphics =
# identity. Assigned to subjects by position (1st subject = 1st hue...).
PALETTE = ['#2b5f96',   # deep steel blue
           '#17806e',   # deep teal
           '#9c7f26',   # dark gold
           '#3e7d35',   # deep green
           '#6b46a3',   # deep violet
           '#1f8fa8',   # deep cyan
           '#4f5aa8',   # indigo
           '#6e8a2f']   # olive
SUBJ_HUE = {key: PALETTE[i] for i, (_, _, key) in enumerate(SUBJECTS)}

# urgency colours: a subject is judged against the average subject's time in
# a window (board labels: last 14 days / strength strip: all-time / TODAY's
# hour numbers: today). Same fractions everywhere:
URG_RED    = '#e63946'   # under 2/3 of the average - needs the most work
URG_ORANGE = '#c96342'   # under 90% of the average - falling behind
URG_BRIGHT = '#f2f2f2'   # over 4/3 of the average - ahead, can ease off
URG_RED_FRAC, URG_ORANGE_FRAC, URG_AHEAD_FRAC = 2 / 3, 0.9, 4 / 3
MIN_DATA   = 2 * 3600    # judge a window only after this much time is in it

FONT_UI  = 'Segoe UI'
FONT_BIG = 'Anton'              # loaded from anton.ttf next to this script
FONT_BIG_FALLBACK = 'Segoe UI Black'
BIG_FAMILY = FONT_BIG_FALLBACK  # resolved in main() by load_anton()
SZ_LABEL, SZ_CHIP, SZ_BIG, SZ_BTN, SZ_ROW, SZ_SUB = -15, -14, -52, -15, -14, -12
BIG_H, BIG_BASE = 50, 3         # stopwatch canvas height / baseline inset
                                # (47px above baseline; digit ink rises 45px,
                                # was exactly 45 = zero margin -> scale
                                # rounding could clip round digit tops)

DIR    = os.path.dirname(os.path.abspath(__file__))
LOG    = os.path.join(DIR, 'study_log.jsonl')
STATE  = os.path.join(DIR, 'widget_state.json')
ACTIVE = os.path.join(DIR, 'active_session.json')
CONFIG = os.path.join(DIR, 'subjects.json')     # written by the setup popup
DEFAULT_POS = (1480, 130)       # first-run position (physical px from top-left)
                                # top-right - clear of desktop icons (left side)
                                # and the countdown widget (bottom-right)
# -----------------------------------------

PREVIEW = '--preview' in sys.argv

# ---------------- win32 plumbing (same as countdown widget) ----------------
u32 = ctypes.windll.user32
u32.FindWindowW.restype = ctypes.c_void_p
u32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
u32.FindWindowExW.restype = ctypes.c_void_p
u32.FindWindowExW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p]
u32.SetParent.restype = ctypes.c_void_p
u32.SetParent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
u32.GetParent.restype = ctypes.c_void_p
u32.GetParent.argtypes = [ctypes.c_void_p]
u32.IsWindow.argtypes = [ctypes.c_void_p]
u32.SendMessageTimeoutW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p,
                                    ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
                                    ctypes.POINTER(ctypes.c_ulong)]
u32.RedrawWindow.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_uint]
u32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
_ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)

def single_instance():
    ctypes.windll.kernel32.CreateMutexW(None, False, 'Study_Logger_Widget_Mutex')
    if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
        sys.exit(0)

def get_hwnd(root):
    root.update_idletasks()
    return u32.GetParent(root.winfo_id()) or root.winfo_id()

def load_anton():
    path = os.path.join(DIR, 'anton.ttf')
    FR_PRIVATE = 0x10
    if os.path.exists(path) and ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0):
        return FONT_BIG
    print('anton.ttf not loaded - falling back to', FONT_BIG_FALLBACK, flush=True)
    return FONT_BIG_FALLBACK

# ---------------- subjects config + first-run setup popup ----------------
def load_config():
    try:
        # utf-8-sig: tolerate the BOM that Notepad/PowerShell like to add
        with open(CONFIG, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

def save_config(cfg):
    with open(CONFIG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

def apply_config(cfg):
    """Install subjects.json contents into the module globals."""
    global TITLE, SUBJECTS, SUBJ_HUE
    TITLE = (cfg.get('title') or TITLE).strip() or TITLE
    trip = [(s['name'], s['chip'], s.get('key', s['chip']))
            for s in cfg.get('subjects') or []
            if s.get('name') and s.get('chip')][:MAX_SUBJECTS]
    if len(trip) >= 2:
        SUBJECTS = trip
    SUBJ_HUE = {key: PALETTE[i % len(PALETTE)]
                for i, (_, _, key) in enumerate(SUBJECTS)}

def parse_subject_rows(rows, title):
    """(name, chip) pairs from the popup -> config dict, or an error string."""
    subs, chips = [], set()
    for name, chip in rows:
        name, chip = name.strip(), chip.strip().upper()[:6]
        if not name and not chip:
            continue
        if not name or not chip:
            return 'every subject needs BOTH a full name and a chip'
        if chip in chips:
            return f'chip "{chip}" is used twice - chips must be unique'
        chips.add(chip)
        subs.append({'name': name, 'chip': chip})
    if not 2 <= len(subs) <= MAX_SUBJECTS:
        return f'enter 2-{MAX_SUBJECTS} subjects'
    return {'title': (title.strip() or 'STUDY LOG').upper(), 'subjects': subs}

def run_setup(prev=None):
    """First-run popup: name your own subjects - works for any stream.
    Returns the new config dict, or None if the window is just closed."""
    BGD, FGD, GREY, ENT = '#0b0b0b', '#f2f2f2', '#8a8a8a', '#181818'
    win = tk.Tk()
    win.title('Study Logger - setup')
    win.configure(bg=BGD, padx=20, pady=16)
    win.attributes('-topmost', True)

    def entry(r, c, width, text=''):
        e = tk.Entry(win, bg=ENT, fg=FGD, insertbackground=FGD, relief='flat',
                     font=(FONT_UI, 11), width=width)
        e.insert(0, text)
        e.grid(row=r, column=c, sticky='w', pady=3, ipady=3)
        return e

    tk.Label(win, text='SET UP YOUR STUDY LOG', bg=BGD, fg=FGD,
             font=(FONT_UI, 14, 'bold')).grid(row=0, column=0, columnspan=2,
                                              sticky='w', pady=(0, 10))
    tk.Label(win, text='widget title', bg=BGD, fg=GREY,
             font=(FONT_UI, 10)).grid(row=1, column=0, sticky='w')
    prev_subs = (prev or {}).get('subjects') or \
        [{'name': n, 'chip': c} for n, c, _ in SUBJECTS]
    title_e = entry(1, 1, 24, (prev or {}).get('title', TITLE))
    tk.Label(win, text='your subjects (2-8) - full name + short chip label,\n'
                       'leave rows blank to skip', justify='left',
             bg=BGD, fg=GREY, font=(FONT_UI, 10)).grid(
        row=2, column=0, columnspan=2, sticky='w', pady=(12, 4))
    rows = []
    for i in range(MAX_SUBJECTS):
        pre = prev_subs[i] if i < len(prev_subs) else {'name': '', 'chip': ''}
        rows.append((entry(3 + i, 0, 30, pre['name']),
                     entry(3 + i, 1, 10, pre['chip'])))
    err = tk.Label(win, text='', bg=BGD, fg='#e63946', font=(FONT_UI, 10))
    err.grid(row=3 + MAX_SUBJECTS, column=0, columnspan=2, sticky='w')
    out = {}

    def ok():
        got = parse_subject_rows([(n.get(), ch.get()) for n, ch in rows],
                                 title_e.get())
        if isinstance(got, str):
            err.config(text=got)
            return
        out.update(got)
        win.destroy()

    tk.Button(win, text='SAVE  &  LAUNCH', command=ok, bg='#e63946',
              fg='white', relief='flat', font=(FONT_UI, 11, 'bold'),
              padx=16, pady=4).grid(row=4 + MAX_SUBJECTS, column=0,
                                    columnspan=2, sticky='w', pady=(10, 0))
    win.mainloop()
    return out or None

# ---------------- log storage ----------------
def append_session(subject_key, started, ended, seconds, recovered=False):
    rec = {'subject': subject_key, 'date': started.strftime('%Y-%m-%d'),
           'start': started.isoformat(timespec='seconds'),
           'end': ended.isoformat(timespec='seconds'), 'sec': int(seconds)}
    if recovered:
        rec['recovered'] = True
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + '\n')

def load_totals():
    """{date str: {subject key: seconds}} from the whole log."""
    totals = {}
    if not os.path.exists(LOG):
        return totals
    with open(LOG, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                totals.setdefault(rec['date'], {})
                totals[rec['date']][rec['subject']] = \
                    totals[rec['date']].get(rec['subject'], 0) + rec['sec']
            except (json.JSONDecodeError, KeyError):
                print('skipping bad log line:', line[:80], flush=True)
    return totals

def recover_crashed_session():
    """If active_session.json survived a crash, bank its checkpointed time."""
    if not os.path.exists(ACTIVE):
        return
    try:
        with open(ACTIVE, encoding='utf-8') as f:
            a = json.load(f)
        started = dt.datetime.fromisoformat(a['started'])
        checkpt = dt.datetime.fromisoformat(a['checkpoint'])
        if a['sec'] >= MIN_SESSION:
            append_session(a['subject'], started, checkpt, a['sec'], recovered=True)
            print(f"recovered crashed session: {a['subject']} {a['sec']}s", flush=True)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print('could not recover active session:', e, flush=True)
    os.remove(ACTIVE)

def load_state():
    try:
        with open(STATE, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def save_state(st):
    with open(STATE, 'w', encoding='utf-8') as f:
        json.dump(st, f)

def tint(colour, f):
    """colour dimmed to fraction f (0..1) - heat shading within one hue."""
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return f'#{int(r * f):02x}{int(g * f):02x}{int(b * f):02x}'

def lift(colour, f):
    """colour blended toward white by fraction f (0..1) - highlights."""
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return (f'#{int(r + (255 - r) * f):02x}{int(g + (255 - g) * f):02x}'
            f'{int(b + (255 - b) * f):02x}')

def heat_shade(colour, f):
    """heat-cell fill for intensity f (0..1): dark hue -> full hue -> glows
    toward white at the top so the strongest cells pop on black."""
    if f <= 0.7:
        return tint(colour, 0.35 + 0.65 * (f / 0.7))
    return lift(colour, (f - 0.7) / 0.3 * 0.35)

def fmt_hm(sec):
    h, m = int(sec) // 3600, int(sec) % 3600 // 60
    if h:
        return f'{h}h {m:02d}m'
    return f'{m}m' if m else '-'

# ---------------- UI ----------------
class Widget:
    def __init__(self, root):
        self.root = root
        root.overrideredirect(True)
        root.configure(bg=BG)
        if TRANSPARENT and not PREVIEW:
            try:
                root.attributes('-transparentcolor', BG)
            except tk.TclError:
                pass

        self.state = load_state()
        self.scale = min(2.0, max(0.6, float(self.state.get('scale', 1.0))))
        sc = self.scale
        self.f_label = tkfont.Font(family=FONT_UI, size=int(SZ_LABEL * sc))
        self.f_chip  = tkfont.Font(family=FONT_UI, size=int(SZ_CHIP * sc), weight='bold')
        self.f_big   = tkfont.Font(family=BIG_FAMILY, size=int(SZ_BIG * sc))
        self.f_btn   = tkfont.Font(family=FONT_UI, size=int(SZ_BTN * sc), weight='bold')
        self.f_row   = tkfont.Font(family=FONT_UI, size=int(SZ_ROW * sc))
        self.f_row_b = tkfont.Font(family=FONT_UI, size=int(SZ_ROW * sc), weight='bold')
        self.f_sub   = tkfont.Font(family=FONT_UI, size=int(SZ_SUB * sc))

        # ---- state ---- (self.state/self.scale loaded above, before fonts)
        self.view = self.state.get('view', 'today')     # 'today' | 'heat'
        self.subject = None            # selected log key
        self.sw = 'idle'               # 'idle' | 'run' | 'pause'
        self.accum = 0.0               # banked seconds (across pauses)
        self.run_from = None           # wallclock of current run segment
        self.started = None            # first start of this session
        self.last_ckpt = 0.0
        self.move_mode = False
        self._resize = None
        self.totals = load_totals()

        # ---- layout ----
        self.card = tk.Frame(root, bg=CARD, padx=self.S(16), pady=self.S(13),
                             highlightthickness=1, highlightbackground=CARD)
        self.card.pack()
        c = self.card

        self.title = tk.Label(c, bg=CARD, fg=DIM, font=self.f_label,
                              text=' '.join(TITLE))
        self.title.pack(anchor='w')

        self.chips_fr = tk.Frame(c, bg=CARD)
        self.chips_fr.pack(anchor='w', pady=(9, 2))
        self.chips = {}
        for full, chip, key in SUBJECTS:
            lb = tk.Label(self.chips_fr, bg=CARD, fg=SUBJ_HUE[key],
                          font=self.f_chip, text=chip, cursor='hand2')
            lb.pack(side='left', padx=(0, 13))
            lb.bind('<Button-1>', lambda e, k=key: self.pick(k))
            self.chips[key] = lb

        self.bigcv = tk.Canvas(c, bg=CARD, height=self.S(BIG_H), width=10,
                               highlightthickness=0, bd=0)
        self.bigcv.pack(anchor='w', pady=(4, 2))

        self.btn_fr = tk.Frame(c, bg=CARD)
        self.btn_fr.pack(anchor='w', pady=(2, 4))
        self.btns = {}
        for name, txt in (('start', '▶ START'), ('pause', '⏸ PAUSE'),
                          ('end', '■ END')):
            b = tk.Label(self.btn_fr, bg=CARD, fg=FAINT, font=self.f_btn,
                         text=txt, cursor='hand2')
            b.pack(side='left', padx=(0, 22))
            b.bind('<Button-1>', lambda e, n=name: self.press(n))
            self.btns[name] = b

        self.hint = tk.Label(c, bg=CARD, fg=FAINT, font=self.f_sub,
                             text='pick a subject')
        self.hint.pack(anchor='w')

        tk.Frame(c, bg='#1e1e1e', height=1).pack(fill='x', pady=(9, 8))

        self.head = tk.Label(c, bg=CARD, fg=DIM, font=self.f_label,
                             cursor='hand2')
        self.head.pack(anchor='w')
        self.head.bind('<Button-1>', self.toggle_view)

        self.board = tk.Canvas(c, bg=CARD, highlightthickness=0, bd=0)
        self.board.pack(anchor='w', pady=(6, 0))

        tk.Frame(c, bg='#1e1e1e', height=1).pack(fill='x', pady=(9, 8))
        self.strc = tk.Canvas(c, bg=CARD, highlightthickness=0, bd=0)
        self.strc.pack(anchor='w')

        # ---- bindings: drag mode + quit ----
        for w in (c, self.title, self.bigcv, self.hint):
            w.bind('<Double-Button-1>', self.toggle_move)
        root.bind('<Button-3>', self.quit)
        root.bind('<ButtonPress-1>', self.drag_press)
        root.bind('<B1-Motion>', self.drag_motion)

        self.hwnd = None
        self.desktop = None
        self.render_stopwatch()
        self.render_board()
        self.tick()

    # ---------------- uniform scaling ----------------
    def S(self, v):
        """scale a base pixel value (corner-drag resize, no elongation)."""
        return max(1, int(round(v * self.scale)))

    def apply_scale(self):
        sc = self.scale
        for f, base in ((self.f_label, SZ_LABEL), (self.f_chip, SZ_CHIP),
                        (self.f_big, SZ_BIG), (self.f_btn, SZ_BTN),
                        (self.f_row, SZ_ROW), (self.f_row_b, SZ_ROW),
                        (self.f_sub, SZ_SUB)):
            f.config(size=int(base * sc))
        self.card.config(padx=self.S(16), pady=self.S(13))
        self.bigcv.config(height=self.S(BIG_H))
        self.render_stopwatch()
        self.render_board()

    # ---------------- stopwatch ----------------
    def elapsed(self):
        e = self.accum
        if self.sw == 'run':
            e += (dt.datetime.now() - self.run_from).total_seconds()
        return e

    def pick(self, key):
        if self.sw != 'idle':
            self.hint.config(text='end the session before switching', fg=RED)
            return
        self.subject = key
        for k, lb in self.chips.items():
            lb.config(fg=lift(SUBJ_HUE[k], 0.45) if k == key else SUBJ_HUE[k])
        self.hint.config(text=f'{key} selected - hit start', fg=DIM)
        self.paint_buttons()

    def press(self, name):
        now = dt.datetime.now()
        if name == 'start':
            if self.subject is None:
                self.hint.config(text='pick a subject first', fg=RED)
                return
            if self.sw == 'idle':
                self.started, self.accum = now, 0.0
                self.sw, self.run_from = 'run', now
                self.hint.config(text=f'logging {self.subject}...', fg=DIM)
            elif self.sw == 'pause':
                self.sw, self.run_from = 'run', now
                self.hint.config(text=f'resumed {self.subject}', fg=DIM)
        elif name == 'pause' and self.sw == 'run':
            self.accum += (now - self.run_from).total_seconds()
            self.sw = 'pause'
            self.hint.config(text='paused', fg=DIM)
            self.checkpoint()
        elif name == 'end' and self.sw in ('run', 'pause'):
            self.end_session(now)
        self.paint_buttons()
        self.render_stopwatch()

    def end_session(self, now):
        sec = self.elapsed()
        if sec >= MIN_SESSION:
            append_session(self.subject, self.started, now, sec)
            d = self.started.strftime('%Y-%m-%d')
            self.totals.setdefault(d, {})
            self.totals[d][self.subject] = self.totals[d].get(self.subject, 0) + int(sec)
            self.hint.config(text=f'saved {fmt_hm(sec)} to {self.subject}', fg=DIM)
        else:
            self.hint.config(text=f'under {MIN_SESSION}s - not logged', fg=FAINT)
        if os.path.exists(ACTIVE):
            os.remove(ACTIVE)
        self.sw, self.accum, self.run_from, self.started = 'idle', 0.0, None, None
        self.render_board()

    def checkpoint(self):
        with open(ACTIVE, 'w', encoding='utf-8') as f:
            json.dump({'subject': self.subject,
                       'started': self.started.isoformat(timespec='seconds'),
                       'checkpoint': dt.datetime.now().isoformat(timespec='seconds'),
                       'sec': int(self.elapsed())}, f)

    def paint_buttons(self):
        can = {'start': self.subject is not None and self.sw != 'run',
               'pause': self.sw == 'run',
               'end':   self.sw in ('run', 'pause')}
        for n, b in self.btns.items():
            b.config(fg=FG if can[n] else FAINT)
        self.btns['start'].config(text='▶ RESUME' if self.sw == 'pause'
                                  else '▶ START')

    def render_stopwatch(self):
        cv = self.bigcv
        cv.delete('all')
        e = int(self.elapsed())
        txt = f'{e // 3600:02d}:{e % 3600 // 60:02d}:{e % 60:02d}'
        # big white digits like the countdown - dull grey idle killed the look
        colour = DIM if self.sw == 'pause' else FG
        y = self.S(BIG_H - BIG_BASE) + self.f_big.metrics('descent')
        cv.create_text(0, y, text=txt, font=self.f_big, fill=colour, anchor='sw')
        w = self.f_big.measure(txt)
        if self.sw == 'run':          # red pulse dot
            cv.create_oval(w + self.S(12), self.S(10), w + self.S(22),
                           self.S(20), fill=RED, outline='')
            w += self.S(30)
        cv.config(width=max(w, 10))

    # ---------------- overview board ----------------
    def toggle_view(self, _=None):
        self.view = 'heat' if self.view == 'today' else 'today'
        self.state['view'] = self.view
        save_state(self.state)
        self.render_board()

    def day_total(self, dstr, key=None):
        d = self.totals.get(dstr, {})
        base = d.get(key, 0) if key else sum(d.values())
        # fold the live session in so the board is honest mid-session
        if self.sw != 'idle' and self.started and \
                self.started.strftime('%Y-%m-%d') == dstr and \
                (key is None or key == self.subject):
            base += int(self.elapsed())
        return base

    def urgency_tiers(self, totals_by_key):
        """{subject: seconds} -> {subject: colour} by the 2/3-of-average rule."""
        total = sum(totals_by_key.values())
        if total < MIN_DATA:                 # too little data to judge
            return {k: DIM for k in totals_by_key}
        mean = total / len(totals_by_key)
        return {k: URG_RED if v < URG_RED_FRAC * mean
                else URG_ORANGE if v < URG_ORANGE_FRAC * mean
                else URG_BRIGHT if v > URG_AHEAD_FRAC * mean
                else DIM
                for k, v in totals_by_key.items()}

    def urgency_colours(self):
        """Board labels: tiers over the last 14 days (current pattern)."""
        today = dt.date.today()
        days = [(today - dt.timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(HEAT_DAYS)]
        return self.urgency_tiers(
            {key: sum(self.day_total(d, key) for d in days)
             for _, _, key in SUBJECTS})

    def render_board(self):
        if self.view == 'today':
            self.render_today()
        else:
            self.render_heat()
        self.render_strength()

    def render_today(self):
        today = dt.date.today()
        self.head.config(text='T O D A Y  · ' +
                         today.strftime('%a %d %b').upper() + '   ⇄')
        bd = self.board
        bd.delete('all')
        dstr = today.strftime('%Y-%m-%d')
        vals = [(key, self.day_total(dstr, key)) for _, _, key in SUBJECTS]
        mx = max(max(v for _, v in vals), 3600)      # scale floor: 1 h
        urg = self.urgency_colours()
        # today's redline: once 2h+ is logged today, a subject under 2/3 of
        # today's per-subject average gets its hours number in red
        day_tot = sum(v for _, v in vals)
        redline = URG_RED_FRAC * day_tot / len(vals) if day_tot >= MIN_DATA else 0
        s = self.S
        name_w, bar_w, row_h = s(62), s(BAR_W), s(ROW_H)
        y = 0
        for key, v in vals:
            cy = y + row_h // 2
            bd.create_text(0, cy, text=key.upper(), font=self.f_row,
                           fill=urg[key], anchor='w')
            bw = int(bar_w * v / mx)
            bd.create_rectangle(name_w, cy - s(5), name_w + bar_w, cy + s(5),
                                fill='#161616', outline='')
            if bw > 0:
                bd.create_rectangle(name_w, cy - s(5), name_w + max(bw, 2),
                                    cy + s(5), fill=SUBJ_HUE[key], outline='')
            bd.create_text(name_w + bar_w + s(10), cy,
                           text=fmt_hm(v) if v else '0',
                           font=self.f_row_b if v else self.f_row,
                           fill=RED if (not v or v < redline) else FG,
                           anchor='w')
            y += row_h
        # total + 7-day sparkline
        y += s(8)
        tot = self.day_total(dstr)
        bd.create_text(0, y + s(8), text='TOTAL  ' + (fmt_hm(tot) if tot else '0'),
                       font=self.f_row_b, fill=FG, anchor='w')
        days = [today - dt.timedelta(days=i) for i in range(SPARK_DAYS - 1, -1, -1)]
        dtot = [self.day_total(d.strftime('%Y-%m-%d')) for d in days]
        smx = max(max(dtot), 1)
        sx, sw, sh = name_w + bar_w - SPARK_DAYS * s(12), s(8), s(16)
        for i, v in enumerate(dtot):
            h = max(int(sh * v / smx), 1 if v else 1)
            x0 = sx + i * s(12)
            bd.create_rectangle(x0, y + s(16) - h, x0 + sw, y + s(16),
                                fill=RED if i == SPARK_DAYS - 1 else FAINT,
                                outline='')
        bd.config(width=name_w + bar_w + s(62), height=y + s(22))
        self.place_sized()

    def render_heat(self):
        today = dt.date.today()
        self.head.config(text=f'L A S T  {HEAT_DAYS}  D A Y S   ⇄')
        bd = self.board
        bd.delete('all')
        days = [today - dt.timedelta(days=i) for i in range(HEAT_DAYS - 1, -1, -1)]
        s = self.S
        name_w, cell = s(62), s(CELL)
        step = cell + s(CELL_GAP)
        # column labels: day-of-month, Mondays + today emphasized
        for i, d in enumerate(days):
            x = name_w + i * step + cell // 2
            is_today = d == today
            bd.create_text(x, s(6), text=str(d.day), font=self.f_sub,
                           fill=RED if is_today else
                           (DIM if d.weekday() == 0 else FAINT), anchor='n')
        y0 = s(24)
        mx = max((self.day_total(d.strftime('%Y-%m-%d'), key)
                  for d in days for _, _, key in SUBJECTS), default=0)
        mx = max(mx, 1)
        urg = self.urgency_colours()
        for r, (_, _, key) in enumerate(SUBJECTS):
            y = y0 + r * step
            bd.create_text(0, y + cell // 2, text=key.upper(),
                           font=self.f_row, fill=urg[key], anchor='w')
            row_tot = 0
            for i, d in enumerate(days):
                v = self.day_total(d.strftime('%Y-%m-%d'), key)
                row_tot += v
                x = name_w + i * step
                if v <= 0:
                    fill = '#101010'
                else:   # brightness within the subject's own hue
                    fill = heat_shade(SUBJ_HUE[key], v / mx)
                bd.create_rectangle(x, y, x + cell, y + cell,
                                    fill=fill, outline='')
                if d == today:
                    bd.create_rectangle(x, y, x + cell, y + cell,
                                        outline=RED)
            bd.create_text(name_w + HEAT_DAYS * step + s(8), y + cell // 2,
                           text=fmt_hm(row_tot) if row_tot else '-',
                           font=self.f_row, fill=FG if row_tot else FAINT,
                           anchor='w')
        w = name_w + HEAT_DAYS * step + s(80)
        h = y0 + len(SUBJECTS) * step + 2
        bd.config(width=w, height=h)
        self.place_sized()

    def render_strength(self):
        """Always-visible strip: per subject, an all-time heat cell (shade =
        total hours vs the strongest subject) + total hours + days studied."""
        cv = self.strc
        cv.delete('all')
        today = dt.date.today().strftime('%Y-%m-%d')
        live = int(self.elapsed()) if self.sw != 'idle' else 0
        stats = {}
        for _, _, key in SUBJECTS:
            sec = sum(d.get(key, 0) for d in self.totals.values())
            days = sum(1 for d in self.totals.values() if d.get(key, 0) > 0)
            if live and key == self.subject:
                sec += live
                if not self.totals.get(today, {}).get(key, 0):
                    days += 1
            stats[key] = (sec, days)
        mx = max((sec for sec, _ in stats.values()), default=0) or 1
        # strength strip judges ALL-TIME balance (user's 2/3-of-average rule)
        urg = self.urgency_tiers({k: sec for k, (sec, _) in stats.items()})
        s = self.S
        colw, cw, ch = s(44), s(36), s(16)
        cv.create_text(0, 0, text='S T R E N G T H  · ALL TIME',
                       font=self.f_sub, fill=FAINT, anchor='nw')
        y0 = s(20)
        for i, (_, chip, key) in enumerate(SUBJECTS):
            x = i * colw
            sec, days = stats[key]
            cv.create_text(x + cw // 2, y0, text=chip, font=self.f_sub,
                           fill=urg[key], anchor='n')
            cy = y0 + s(16)
            shade = '#101010' if not sec else \
                heat_shade(SUBJ_HUE[key], sec / mx)
            cv.create_rectangle(x, cy, x + cw, cy + ch, fill=shade,
                                outline=URG_RED if urg[key] == URG_RED else '')
            htxt = f'{sec // 3600}h' if sec >= 3600 else \
                   (f'{sec // 60}m' if sec >= 60 else '-')
            cv.create_text(x + cw // 2, cy + ch + s(4), text=htxt,
                           font=self.f_sub, fill=FG if sec else FAINT, anchor='n')
            cv.create_text(x + cw // 2, cy + ch + s(18),
                           text=f'{days}d' if days else '-',
                           font=self.f_sub, fill=DIM if days else FAINT, anchor='n')
        cv.config(width=max(len(SUBJECTS) * colw - (colw - cw),
                            self.f_sub.measure('S T R E N G T H  · ALL TIME') + 4),
                  height=y0 + s(16) + ch + s(34))
        self.place_sized()

    # ---------------- move / place ----------------
    def toggle_move(self, _=None):
        self.move_mode = not self.move_mode
        self.card.config(highlightbackground=RED if self.move_mode else CARD)
        self.hint.config(text='drag body to move · corner to resize - '
                              'double-click to lock' if self.move_mode
                         else 'position locked',
                         fg=RED if self.move_mode else FAINT)

    def drag_press(self, e):
        self._drag = (e.x_root, e.y_root,
                      self.root.winfo_x(), self.root.winfo_y())
        self._resize = None
        if not self.move_mode:
            return
        # grab within 22px of a corner = uniform resize (anchored so the
        # whole widget scales; never elongates one axis)
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        m = max(22, self.S(22))
        for cx, cy, ox, oy in ((wx, wy, wx + w, wy + h),
                               (wx + w, wy, wx, wy + h),
                               (wx, wy + h, wx + w, wy),
                               (wx + w, wy + h, wx, wy)):
            if abs(e.x_root - cx) <= m and abs(e.y_root - cy) <= m:
                d0 = ((cx - ox) ** 2 + (cy - oy) ** 2) ** 0.5
                self._resize = (ox, oy, d0, self.scale)
                break

    def drag_motion(self, e):
        if not self.move_mode:
            return
        if self._resize:   # corner drag: scale fonts + layout uniformly
            ox, oy, d0, s0 = self._resize
            d = ((e.x_root - ox) ** 2 + (e.y_root - oy) ** 2) ** 0.5
            target = min(2.0, max(0.6, s0 * d / d0))
            if abs(target - self.scale) >= 0.04:   # 4% steps, stays light
                self.scale = target
                self.state['scale'] = round(target, 3)
                self.apply_scale()
                save_state(self.state)
            return
        x0, y0, wx, wy = self._drag
        nx, ny = wx + e.x_root - x0, wy + e.y_root - y0
        self.root.geometry(f'+{nx}+{ny}')
        self.state['pos'] = [nx, ny]
        save_state(self.state)

    def place_sized(self):
        self.root.update_idletasks()
        x, y = self.state.get('pos', DEFAULT_POS)
        self.root.geometry(f'+{x}+{y}')

    def pin(self):
        if self.hwnd is None:
            self.hwnd = get_hwnd(self.root)
        if self.desktop is None or not u32.IsWindow(self.desktop):
            # parent into Progman itself, NOT the wallpaper WorkerW: the
            # icons layer (SHELLDLL_DefView) sits above the WorkerW and eats
            # every mouse click, so a WorkerW-hosted widget can never be
            # interactive. As a Progman child raised above the icons layer
            # the widget still lives behind all apps but receives clicks.
            self.desktop = u32.FindWindowW('Progman', None)
            if self.desktop:
                u32.SetParent(self.hwnd, self.desktop)
                self.place_sized()
                self.jiggle()
                print(f'pinned hwnd={self.hwnd:#x} into Progman '
                      f'{self.desktop:#x}', flush=True)
            else:
                print('Progman not found - widget stays as a plain window',
                      flush=True)
        if self.desktop:
            # keep it above the icons layer (re-asserted every 30 s)
            u32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0,
                             0x1 | 0x2 | 0x10)   # NOSIZE|NOMOVE|NOACTIVATE, to HWND_TOP
        self.root.after(30000, self.pin)

    def jiggle(self):
        # a window reparented into the wallpaper WorkerW never repaints until
        # its SIZE changes once - repaints/moves/RedrawWindow don't cut it.
        # Bump the card padding 1px and back: two real resizes via tk's own
        # auto-sizing, so the window keeps resizing itself to content later.
        self.card.config(pady=self.S(13) + 1)
        self.root.after(150, lambda: self.card.config(pady=self.S(13)))

    def quit(self, _=None):
        if self.sw in ('run', 'pause'):
            self.end_session(dt.datetime.now())
        self.root.destroy()

    # ---------------- 1-second tick ----------------
    def tick(self):
        # repaint every second even when idle - windows parented into the
        # wallpaper WorkerW stop showing unless they keep painting (the
        # countdown widget repaints each second too, which is why it shows)
        self.render_stopwatch()
        if self.sw == 'run':
            e = self.elapsed()
            if e - self.last_ckpt >= CHECKPOINT:
                self.last_ckpt = e
                self.checkpoint()
            if int(e) % 60 == 0:          # keep bars honest mid-session
                self.render_board()
        self.root.after(1000, self.tick)


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    # first run (no subjects.json) or --setup: pop the subject editor.
    # Runs BEFORE the single-instance check so --setup works while the
    # widget is up - save, then hit the "Restart CA Widgets" shortcut.
    cfg = load_config()
    if cfg is None or '--setup' in sys.argv:
        cfg = run_setup(cfg) or cfg or \
            {'title': TITLE, 'subjects': [{'name': n, 'chip': c, 'key': k}
                                          for n, c, k in SUBJECTS]}
        save_config(cfg)
    apply_config(cfg)
    if not PREVIEW:
        single_instance()
    recover_crashed_session()
    global BIG_FAMILY
    BIG_FAMILY = load_anton()
    root = tk.Tk()
    root.title('Study Logger Widget' + (' Preview' if PREVIEW else ''))
    app = Widget(root)
    app.place_sized()
    root.update()
    if PREVIEW:
        root.attributes('-topmost', True)
        shot = [sys.argv[i + 1] for i, a in enumerate(sys.argv)
                if a == '--shot' and i + 1 < len(sys.argv)]
        if shot:
            def snap():
                from PIL import ImageGrab
                x, y = root.winfo_rootx(), root.winfo_rooty()
                w, h = root.winfo_width(), root.winfo_height()
                ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True).save(shot[0])
                print('shot saved:', shot[0], flush=True)
                root.destroy()
            root.after(1500, snap)
    else:
        app.pin()
    print('study logger running - right-click to quit', flush=True)
    root.mainloop()


if __name__ == '__main__':
    main()
