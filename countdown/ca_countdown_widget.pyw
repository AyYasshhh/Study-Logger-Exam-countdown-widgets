"""Exam countdown - lightweight desktop widget for any exam schedule.

Plain tkinter, no browser engine. Pins itself to the desktop layer (behind all
apps, in front of the wallpaper) bottom-right, and ticks once per second.
First launch pops a setup window: your exam title, dates, papers and times -
saved to countdown_config.json next to this script.

Run silently (normal use):   pythonw ca_countdown_widget.pyw
Run with console (debug):    python ca_countdown_widget.pyw
Re-open the setup popup:     python ca_countdown_widget.pyw --setup
Preview a future state:      python ca_countdown_widget.pyw --now 2026-09-05T10:00
Preview as normal window:    python ca_countdown_widget.pyw --preview   (topmost,
                             solid bg, no desktop pinning, no single-instance lock)
Quit:                        right-click the widget text (or kill pythonw.exe)

States:
  before the first paper -> live d/h/m/s till it + schedule strip
  during the exam window -> next paper name + live countdown + schedule strip
  after the last paper   -> DONE.
"""

import os
import sys
import json
import ctypes
import datetime as dt
import tkinter as tk
import tkinter.font as tkfont

# ---------------- config ----------------
OFF_RIGHT   = 70        # px gap from right edge of screen
OFF_BOTTOM  = 100       # px gap from bottom edge
TRANSPARENT = True      # True = only the text floats over the wallpaper
BG    = '#010101'       # background (and transparency key when TRANSPARENT)
FG    = '#f2f2f2'
DIM   = '#8a8a8a'
FAINT = '#4a4a4a'
RED   = '#e63946'
FONT_UI  = 'Segoe UI'
FONT_BIG = 'Anton'            # loaded from anton.ttf next to this script
FONT_BIG_FALLBACK = 'Segoe UI Black'
BIG_FAMILY = FONT_BIG_FALLBACK        # resolved in main() by load_anton()
# negative sizes = pixels (DPI-stable). HTML wallpaper used ~110px Anton digits.
SZ_LABEL, SZ_PAPER, SZ_BIG, SZ_UNIT, SZ_SUB, SZ_STRIP = -20, -24, -88, -46, -20, -13
UNIT_RAISE = 0                # extra px above the digit baseline for D/H/M/S
BIG_H    = 82                 # digit row height — crops Anton's empty cell
                              # headroom but keeps 78px above the baseline:
                              # round digits (0/6/8/9) overshoot to 76px and
                              # lost their curved tops at the old 78 total
BIG_BASE = 4                  # px the digit baseline sits above the row bottom
GAP_UNIT, GAP_GROUP = 4, 20   # px number→unit and unit→next-number gaps

# digit colour by time left to the current target (checked top to bottom)
HEAT = [
    (1,  '#d90429'),          # <= 24 hours: deep red
    (7,  '#ff6a3d'),          # <= 7 days:   reddish orange
    (15, '#ffa028'),          # <= 15 days:  orange
]                             # else FG (white)

def heat_color(ms):
    days_left = ms.total_seconds() / 86400
    for limit, colour in HEAT:
        if days_left <= limit:
            return colour
    return FG

# defaults only - your real exams live in countdown_config.json, created by
# the first-run setup popup (re-open anytime:  python ca_countdown_widget.pyw --setup)
TITLE  = 'CA INTER · SEPT 2026'   # letterspaced header line
TILL   = 'CA Inter'               # short name in "till <this> — first paper..."
WINDOW = '2–5 PM'                 # exam-hours text shown in the sub line
LEAVE_H, LEAVE_M = 13, 30         # leave-home time the countdown targets
EXAMS = [                         # (date, full name, chip, hue)
    ('2026-09-01', 'Advanced Accounting',     'ACC',  '#2b5f96'),
    ('2026-09-03', 'Corporate & Other Laws',  'LAW',  '#17806e'),
    ('2026-09-06', 'Taxation',                'TAX',  '#9c7f26'),
    ('2026-09-08', 'Cost & Mgmt Accounting',  'COST', '#3e7d35'),
    ('2026-09-10', 'Auditing & Ethics',       'AUD',  '#6b46a3'),
    ('2026-09-12', 'FM & SM',                 'FMSM', '#1f8fa8'),
]
MAX_PAPERS = 8
# deep jewel palette shared with the study logger - hues are assigned to
# papers by date order (1st paper = 1st hue...). No reds/oranges: those
# always mean urgency here.
PALETTE = ['#2b5f96', '#17806e', '#9c7f26', '#3e7d35',
           '#6b46a3', '#1f8fa8', '#4f5aa8', '#6e8a2f']

def lift(colour, f):
    """colour blended toward white by fraction f (0..1) - highlights."""
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return (f'#{int(r + (255 - r) * f):02x}{int(g + (255 - g) * f):02x}'
            f'{int(b + (255 - b) * f):02x}')
# -----------------------------------------

DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(DIR, 'countdown_config.json')   # written by the popup

def target(dstr):
    y, m, d = map(int, dstr.split('-'))
    return dt.datetime(y, m, d, LEAVE_H, LEAVE_M)

FIRST = dt.datetime(2026, 9, 1)
LAST  = target(EXAMS[-1][0])

# ---------------- exams config + first-run setup popup ----------------
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

def default_config():
    return {'title': TITLE, 'till': TILL, 'leave': f'{LEAVE_H}:{LEAVE_M:02d}',
            'window': WINDOW,
            'papers': [{'date': d, 'name': n, 'chip': c}
                       for d, n, c, _ in EXAMS]}

def apply_config(cfg):
    """Install countdown_config.json contents into the module globals."""
    global TITLE, TILL, WINDOW, LEAVE_H, LEAVE_M, EXAMS, FIRST, LAST
    TITLE = (cfg.get('title') or TITLE).strip() or TITLE
    TILL = (cfg.get('till') or TILL).strip() or TILL
    WINDOW = (cfg.get('window') or WINDOW).strip() or WINDOW
    try:
        LEAVE_H, LEAVE_M = map(int, cfg.get('leave', '').split(':'))
    except ValueError:
        pass
    papers = sorted((p for p in cfg.get('papers') or []
                     if p.get('date') and p.get('name') and p.get('chip')),
                    key=lambda p: p['date'])[:MAX_PAPERS]
    if papers:
        EXAMS = [(p['date'], p['name'], p['chip'], PALETTE[i % len(PALETTE)])
                 for i, p in enumerate(papers)]
        y, m, d = map(int, EXAMS[0][0].split('-'))
        FIRST = dt.datetime(y, m, d)
        LAST = target(EXAMS[-1][0])

def parse_paper_rows(rows, title, till, leave, window):
    """Popup rows -> config dict, or an error string."""
    try:
        h, mi = map(int, leave.strip().split(':'))
        assert 0 <= h <= 23 and 0 <= mi <= 59
    except (ValueError, AssertionError):
        return 'leave time must be HH:MM (24h), e.g. 13:30'
    papers, chips = [], set()
    for date, name, chip in rows:
        date, name = date.strip(), name.strip()
        chip = chip.strip().upper()[:6]
        if not date and not name and not chip:
            continue
        if not (date and name and chip):
            return 'every paper needs date + name + chip'
        try:
            dt.date.fromisoformat(date)
        except ValueError:
            return f'bad date "{date}" - use YYYY-MM-DD'
        if chip in chips:
            return f'chip "{chip}" is used twice - chips must be unique'
        chips.add(chip)
        papers.append({'date': date, 'name': name, 'chip': chip})
    if not 1 <= len(papers) <= MAX_PAPERS:
        return f'enter 1-{MAX_PAPERS} papers'
    return {'title': (title.strip() or TITLE).upper(),
            'till': till.strip() or TILL,
            'leave': f'{h}:{mi:02d}', 'window': window.strip() or WINDOW,
            'papers': papers}

def run_setup(prev=None):
    """First-run popup: your own exam name, dates and papers - any stream.
    Returns the new config dict, or None if the window is just closed."""
    BGD, FGD, GREY, ENT = '#0b0b0b', '#f2f2f2', '#8a8a8a', '#181818'
    win = tk.Tk()
    win.title('Exam Countdown - setup')
    win.configure(bg=BGD, padx=20, pady=16)
    win.attributes('-topmost', True)

    def entry(r, c, width, text='', span=1):
        e = tk.Entry(win, bg=ENT, fg=FGD, insertbackground=FGD, relief='flat',
                     font=(FONT_UI, 11), width=width)
        e.insert(0, text)
        e.grid(row=r, column=c, columnspan=span, sticky='w', pady=3, ipady=3)
        return e

    def lab(r, c, txt, span=1, pady=3):
        tk.Label(win, text=txt, bg=BGD, fg=GREY, font=(FONT_UI, 10),
                 justify='left').grid(row=r, column=c, columnspan=span,
                                      sticky='w', pady=pady, padx=(0, 8))

    prev = prev or default_config()
    tk.Label(win, text='SET UP YOUR EXAM COUNTDOWN', bg=BGD, fg=FGD,
             font=(FONT_UI, 14, 'bold')).grid(row=0, column=0, columnspan=3,
                                              sticky='w', pady=(0, 10))
    lab(1, 0, 'header line (e.g. CBSE XII · MARCH 2027)')
    title_e = entry(1, 1, 30, prev.get('title', TITLE), span=2)
    lab(2, 0, 'short name ("till <this> ...")')
    till_e = entry(2, 1, 30, prev.get('till', TILL), span=2)
    lab(3, 0, 'leave-home time, 24h HH:MM')
    leave_e = entry(3, 1, 30, prev.get('leave', '13:30'), span=2)
    lab(4, 0, 'exam hours text (e.g. 2–5 PM)')
    window_e = entry(4, 1, 30, prev.get('window', WINDOW), span=2)
    lab(5, 0, 'papers (1-8): date + full name + short chip,\n'
              'leave rows blank to skip', span=3, pady=(12, 4))
    lab(6, 0, 'date (YYYY-MM-DD)')
    lab(6, 1, 'paper / subject name')
    lab(6, 2, 'chip')
    rows = []
    prev_p = prev.get('papers') or []
    for i in range(MAX_PAPERS):
        p = prev_p[i] if i < len(prev_p) else {'date': '', 'name': '', 'chip': ''}
        rows.append((entry(7 + i, 0, 14, p['date']),
                     entry(7 + i, 1, 28, p['name']),
                     entry(7 + i, 2, 8, p['chip'])))
    err = tk.Label(win, text='', bg=BGD, fg='#e63946', font=(FONT_UI, 10))
    err.grid(row=7 + MAX_PAPERS, column=0, columnspan=3, sticky='w')
    out = {}

    def ok():
        got = parse_paper_rows([(d.get(), n.get(), c.get()) for d, n, c in rows],
                               title_e.get(), till_e.get(), leave_e.get(),
                               window_e.get())
        if isinstance(got, str):
            err.config(text=got)
            return
        out.update(got)
        win.destroy()

    tk.Button(win, text='SAVE  &  LAUNCH', command=ok, bg='#e63946',
              fg='white', relief='flat', font=(FONT_UI, 11, 'bold'),
              padx=16, pady=4).grid(row=8 + MAX_PAPERS, column=0,
                                    columnspan=3, sticky='w', pady=(10, 0))
    win.mainloop()
    return out or None

# --- optional --now override (like the HTML ?now= param) ---
def _parse_now_arg():
    for i, a in enumerate(sys.argv):
        if a == '--now' and i + 1 < len(sys.argv):
            return dt.datetime.fromisoformat(sys.argv[i + 1])
        if a.startswith('--now='):
            return dt.datetime.fromisoformat(a.split('=', 1)[1])
    return None

_BASE = _parse_now_arg()
_T0 = dt.datetime.now()
PREVIEW = '--preview' in sys.argv

def get_now():
    if _BASE is None:
        return dt.datetime.now()
    return _BASE + (dt.datetime.now() - _T0)

# ---------------- win32 plumbing ----------------
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
u32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]

def single_instance():
    """Exit quietly if the widget is already running (autostart + manual run)."""
    ctypes.windll.kernel32.CreateMutexW(None, False, 'Exam_Countdown_Widget_Mutex')
    if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
        sys.exit(0)

def get_hwnd(root):
    root.update_idletasks()
    return u32.GetParent(root.winfo_id()) or root.winfo_id()

def load_anton():
    """Register anton.ttf privately for this process; returns the family to use."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'anton.ttf')
    FR_PRIVATE = 0x10
    if os.path.exists(path) and ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0):
        return FONT_BIG
    print('anton.ttf not loaded — falling back to', FONT_BIG_FALLBACK, flush=True)
    return FONT_BIG_FALLBACK

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

        self.f_label = tkfont.Font(family=FONT_UI,  size=SZ_LABEL)
        self.f_paper = tkfont.Font(family=FONT_UI,  size=SZ_PAPER, weight='bold')
        self.f_big   = tkfont.Font(family=BIG_FAMILY, size=SZ_BIG)
        self.f_unit  = tkfont.Font(family=FONT_UI,  size=SZ_UNIT)
        self.f_sub   = tkfont.Font(family=FONT_UI,  size=SZ_SUB)
        self.f_strip = tkfont.Font(family=FONT_UI,  size=SZ_STRIP)
        self.f_strip_b = tkfont.Font(family=FONT_UI, size=SZ_STRIP, weight='bold')
        self.f_strip_x = tkfont.Font(family=FONT_UI, size=SZ_STRIP, overstrike=1)
        print('big font resolved to:', self.f_big.actual('family'),
              '| measure("58"):', self.f_big.measure('58'), flush=True)

        self._pad = 14 if (not TRANSPARENT or PREVIEW) else 0
        box = self.box = tk.Frame(root, bg=BG, padx=self._pad, pady=self._pad)
        box.pack()
        self.label = tk.Label(box, bg=BG, fg=DIM, font=self.f_label, bd=0, pady=0,
                              text=' '.join(TITLE))
        self.label.pack(anchor='e', pady=(0, 17))
        self.paper = tk.Label(box, bg=BG, fg=RED, font=self.f_paper, bd=0, pady=0)
        self.bigcv = tk.Canvas(box, bg=BG, height=BIG_H, width=10,
                               highlightthickness=0, bd=0)
        self.bigcv.pack(anchor='e')
        self.sub = tk.Label(box, bg=BG, fg=DIM, font=self.f_sub, bd=0, pady=0)
        self.sub.pack(anchor='e', pady=(4, 0))
        self.sep = tk.Frame(box, bg='#1e1e1e', height=1)   # divider, like the logger's
        self.strip = tk.Frame(box, bg=BG)
        self.strip_sig = None
        self.last_size = (0, 0)
        self.hwnd = None
        self.desktop = None

        root.bind('<Button-3>', lambda e: root.destroy())   # right-click = quit
        self.tick()

    # --- big d/h/m/s row (canvas: digits/units share a baseline, dead space cropped) ---
    def set_big(self, segs, colour=FG):
        cv = self.bigcv
        cv.delete('all')
        base = BIG_H - BIG_BASE                       # digit baseline y
        y_num  = base + self.f_big.metrics('descent')   # cell-bottom anchors
        y_unit = base + self.f_unit.metrics('descent') - UNIT_RAISE
        x = 0
        for i, (val, unit) in enumerate(segs):
            txt = str(val)
            cv.create_text(x, y_num, text=txt, font=self.f_big,
                           fill=colour, anchor='sw')
            x += self.f_big.measure(txt) + GAP_UNIT
            cv.create_text(x, y_unit, text=unit.upper(), font=self.f_unit,
                           fill=DIM, anchor='sw')
            x += self.f_unit.measure(unit.upper())
            if i < len(segs) - 1:
                x += GAP_GROUP
        cv.config(width=x)

    def set_done(self):
        cv = self.bigcv
        cv.delete('all')
        cv.create_text(0, BIG_H - BIG_BASE + self.f_big.metrics('descent'),
                       text='DONE.', font=self.f_big, fill=FG, anchor='sw')
        cv.config(width=self.f_big.measure('DONE.'))

    # --- schedule strip (always visible; papers wear their subject hue) ---
    def build_strip(self, now):
        today = now.strftime('%Y-%m-%d')
        sig = ['today' if d == today else
               'past' if target(d) < now else 'up' for d, *_ in EXAMS]
        for i, cls in enumerate(sig):      # first future paper = 'next'
            if cls == 'up':
                sig[i] = 'next'
                break
        sig = tuple(sig)
        if sig == self.strip_sig:
            return
        self.strip_sig = sig
        for w in self.strip.winfo_children():
            w.destroy()
        for (d, _, chip, hue), cls in zip(EXAMS, sig):
            y_, m_, day = map(int, d.split('-'))
            mon = dt.date(y_, m_, day).strftime('%b').upper()
            if cls == 'today':
                fg, f = RED, self.f_strip_b
            elif cls == 'past':
                fg, f = FAINT, self.f_strip_x
            elif cls == 'next':
                fg, f = lift(hue, 0.45), self.f_strip_b
            else:
                fg, f = hue, self.f_strip
            tk.Label(self.strip, bg=BG, fg=fg, font=f,
                     text=f'{mon} {day} {chip}').pack(side='left', padx=(0, 12))

    # --- position bottom-right, only when size changed ---
    def place(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        if (w, h) != self.last_size:
            self.last_size = (w, h)
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f'+{sw - w - OFF_RIGHT}+{sh - h - OFF_BOTTOM}')

    def pin(self):
        """Pin to the desktop: child of Progman, raised above the icons layer.

        (Was: reparent into the wallpaper WorkerW — but windows there only
        repaint when they RESIZE, so the seconds stalled whenever consecutive
        digits had the same pixel width, and SHELLDLL_DefView above the
        WorkerW ate all clicks, breaking right-click-quit. Same fix as the
        study logger widget - see D:\\BOTS\\CA_Study_Logger\\GOAL.md.)"""
        if self.hwnd is None:
            self.hwnd = get_hwnd(self.root)
        if self.desktop is None or not u32.IsWindow(self.desktop):
            self.desktop = u32.FindWindowW('Progman', None)
            if self.desktop:
                u32.SetParent(self.hwnd, self.desktop)
                self.last_size = (0, 0)   # force re-place after reparent
                self.place()
                self.jiggle()
                print(f'pinned hwnd={self.hwnd:#x} into Progman {self.desktop:#x}',
                      flush=True)
            else:
                print('Progman not found — widget stays as a plain window',
                      flush=True)
        if self.desktop:
            # keep above the icons layer so right-click reaches the widget
            u32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0,
                             0x1 | 0x2 | 0x10)   # NOSIZE|NOMOVE|NOACTIVATE
        self.root.after(30000, self.pin)

    def jiggle(self):
        # a reparented window never paints until its SIZE changes once (the
        # digits row used to resize the window every second by accident; the
        # always-on strip is wider, so the size went constant and the widget
        # stayed blank). One 1px pady bump and back un-sticks it for good.
        self.box.config(pady=self._pad + 1)
        self.root.after(150, lambda: self.box.config(pady=self._pad))

    # --- 1-second tick ---
    def tick(self):
        now = get_now()
        if now > LAST:
            self.paper.pack_forget()
            self.sep.pack_forget()
            self.strip.pack_forget()
            self.set_done()
            self.sub.config(text='All papers written. Go rest.')
        elif now < FIRST:
            ms = FIRST - now
            d, rem = ms.days, ms.seconds
            self.paper.pack_forget()
            self.set_big(([(d, 'd')] if d > 0 else [])
                         + [(rem // 3600, 'h'), (rem % 3600 // 60, 'm'),
                            (rem % 60, 's')],
                         colour=heat_color(ms))
            self.sub.config(text=f'till {TILL} — first paper '
                                 f'{FIRST.strftime("%b")} {FIRST.day} · {WINDOW}')
            self.sep.pack(fill='x', pady=(10, 7), after=self.sub)
            self.strip.pack(anchor='e', after=self.sep)
            self.build_strip(now)
        else:
            nxt = next(e for e in EXAMS if target(e[0]) > now)
            tgt = target(nxt[0])
            ms = tgt - now
            d, rem = ms.days, ms.seconds
            segs = ([(d, 'd')] if d > 0 else []) + \
                   [(rem // 3600, 'h'), (rem % 3600 // 60, 'm'), (rem % 60, 's')]
            self.paper.config(text=nxt[1].upper())
            self.paper.pack(anchor='e', after=self.label)
            self.set_big(segs, colour=heat_color(ms))
            leave12 = f'{LEAVE_H % 12 or 12}:{LEAVE_M:02d} ' \
                      f'{"PM" if LEAVE_H >= 12 else "AM"}'
            self.sub.config(text=f'leave {leave12} · paper {WINDOW} · '
                                 + tgt.strftime('%A, %d %b'))
            self.sep.pack(fill='x', pady=(10, 7), after=self.sub)
            self.strip.pack(anchor='e', after=self.sep)
            self.build_strip(now)
        self.place()
        self.root.after(1000, self.tick)


def main():
    try:  # crisp text on scaled displays
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    # first run (no countdown_config.json) or --setup: pop the exam editor.
    # Runs BEFORE the single-instance check so --setup works while the
    # widget is up - save, then restart the widget.
    cfg = load_config()
    if cfg is None or '--setup' in sys.argv:
        cfg = run_setup(cfg) or cfg or default_config()
        save_config(cfg)
    apply_config(cfg)
    if not PREVIEW:
        single_instance()
    global BIG_FAMILY
    BIG_FAMILY = load_anton()   # must happen BEFORE tk.Tk() or Tk won't see it
    root = tk.Tk()
    root.title('Exam Countdown Widget' + (' Preview' if PREVIEW else ''))
    app = Widget(root)
    app.place()
    root.update()
    if PREVIEW:
        root.attributes('-topmost', True)
        shot = [sys.argv[i + 1] for i, a in enumerate(sys.argv)
                if a == '--shot' and i + 1 < len(sys.argv)]
        if shot:  # self-screenshot after 1.5s, then exit (for layout checks)
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
    print('widget running — right-click it to quit', flush=True)
    root.mainloop()


if __name__ == '__main__':
    main()
