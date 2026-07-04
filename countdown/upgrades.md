# upgrades — CA_Exam_Countdown

## 2026-07-04 (late night) — round digit tops were clipped
- User spotted 8/2/0-style digits looking flattened on top. Measured the
  actual glyph ink with FreeType: at 88px Anton, round digits (0/6/8/9)
  overshoot 76px above the baseline but the digit canvas only left 74px —
  every digit clipped 1px, round tops 2px.
- `BIG_H` 78 → 82 (78px above baseline now). Verified by screenshot: curves
  intact. Same fix applied to the study logger (its margin was exactly 0).

## 2026-07-04 (late night) — schedule strip always on, subject hues
**Why:** user felt the widget looked "way too plain" next to the upgraded
study logger.

**What changed:**
- The exam schedule strip now shows in the pre-exam state too (was
  exam-window only), under a thin `#1e1e1e` divider like the logger's.
- Papers renamed to the logger's chip labels (ACC/LAW/TAX/COST/AUD/FMSM) and
  each wears its subject's deep jewel hue — same palette as the logger
  (`EXAMS` config now carries chip + hue). Next paper = hue lifted toward
  white + bold, today = red, past = struck-through grey.
- Big digits / heat colours untouched.
- Gotcha found while shipping: the always-on strip is now the widget's
  widest element, so the digits row's per-second width wobble stopped
  resizing the window — and a freshly reparented window never paints until
  its size changes once, so the widget came up blank. Ported the study
  logger's `jiggle()` (1px pady bump and back after pinning); after that one
  resize, paints flow normally and the seconds update every second — which
  the old accidental-resize mechanism never guaranteed anyway.
- Verified: --preview screenshots of both states, pinned widget restarted,
  live pixel-diff confirms per-second updates on the desktop layer.

## 2026-07-04 (late night) — pinning ported to the Progman method
**Why:** two quirks of the old WorkerW parenting, discovered while debugging
the study-logger widget (full writeup: `D:\BOTS\CA_Study_Logger\GOAL.md`):
windows in the wallpaper WorkerW only repaint when they **resize**, so the
seconds visually stalled whenever consecutive digits had the same pixel
width; and the desktop-icons layer (`SHELLDLL_DefView`) sits above the
WorkerW and eats every click, so right-click-quit never actually worked.

**What changed:**
- `pin()` now parents the widget into **Progman** and raises it above the
  icons layer (`SetWindowPos` to top, re-asserted every 30 s). Still behind
  all apps. Seconds now update smoothly; right-click-quit works after Win+D.
- Removed the now-unused `find_desktop_layer()`.

## 2026-07-04 (night) — final layout polish (user-verified)
- Label + sub line enlarged 14px → 20px.
- Digit row moved onto a Canvas that crops Anton's empty line-box headroom;
  digits and D/H/M/S drawn on a shared baseline (UNIT_RAISE = 0, i.e. flush).
- Line spacing settled at: label → digits 17px, digits → sub 4px.

## 2026-07-04 (evening) — heat colours + bigger units
- Digit colour now reflects urgency (whole d/h/m/s row changes together, driven
  by total time left to the current target): white normally, orange ≤ 15 days,
  reddish orange ≤ 7 days, deep red ≤ 24 hours. Thresholds/colours in the
  `HEAT` list in the config block.
- D/H/M/S unit letters enlarged 18px → 46px (> half the 88px digits) per
  user request; still dim grey, baseline-aligned.
- Days group now hidden when it reaches 0 in the pre-exam state too (was
  already the case during the exam window).

## 2026-07-04 (later) — widget typography pass
**Why:** first version used Segoe UI Black digits with tiny subscript-looking
unit letters — didn't match the old wallpaper's Anton look.

**What changed:**
- Converted `anton.woff2` → `anton.ttf` (fontTools + brotli, installed --user);
  widget now loads it privately at startup. Key gotcha: the font must be
  registered **before** `tk.Tk()` is created or Tk never sees the family.
- Digits bumped to 88px Anton (HTML used ~110px); D/H/M/S units enlarged to
  18px and auto-aligned to the digit baseline via font descent metrics
  (`UNIT_RAISE` config for manual tweak).
- New `--preview` flag (normal topmost window, solid bg, no pinning/mutex) and
  `--shot out.png` (self-screenshot then exit) for checking looks without
  touching the pinned instance. Verified all three states visually.

## 2026-07-04 — Lively wallpaper → native desktop widget
**Why:** the Lively HTML wallpaper lagged the laptop. Two causes: Lively keeps a
full embedded browser (~245 MB RAM + CEF renderer) running behind the desktop,
and the ASCII fire was set to 80 rows @ 22 fps — a huge full-width text repaint
22×/second.

**What changed:**
- New `ca_countdown_widget.pyw`: plain Python/tkinter, ~30 MB RAM. Same states
  and colors as the HTML (pre-exam d/h/m/s, exam-window paper + strip, DONE).
  Pins itself into the Windows wallpaper layer (WorkerW) so apps cover it like
  a normal desktop element; transparent background so only text shows.
  Live seconds always (user choice). Single-instance mutex. Right-click quits.
- `luffy_gear5.png` set as the static Windows wallpaper (Fill) — same look,
  zero running cost.
- Auto-start shortcut `CA_Countdown_Widget.lnk` added to `shell:startup`
  (target `C:\Python314\pythonw.exe`).
- Lively processes stopped. HTML/fire/font files kept but retired.
- README + folderuse rewritten for the widget.
