# Study Desktop Widgets

Two tiny Windows widgets that live **on your wallpaper** — behind every app,
in front of the desktop icons. Plain Python/tkinter, no browser engine,
~30 MB RAM total.

- **Study Logger** — pick a subject, run a stopwatch; every session is logged.
  Today's bars, a 14-day heatmap, an all-time strength strip, and urgency
  colours that show *what to study next* (red = neglected, white = ahead).
- **Exam Countdown** — live countdown to your next paper, digits that heat up
  as the day nears, and a schedule strip in each subject's colour.

First launch pops a **setup window** — type your own subjects / exam dates
(any stream). Nothing is hard-coded.

<p align="center">
  <img src="assets/study_logger.png" alt="Study Logger" width="46%">
  &nbsp;
  <img src="assets/countdown.png" alt="Exam Countdown" width="46%">
</p>
<p align="center">
  <img src="assets/desktop.png" alt="Both widgets pinned to the desktop" width="80%">
</p>

## Install — pick one

**A · One-click (easiest, no terminal).** [Download the ZIP](../../archive/refs/heads/main.zip)
→ *Extract All* → **double-click `setup.bat`**. A menu finds Python (and offers
to install it for you if missing), then launches the widgets, toggles Windows
auto-start, or restarts them.

**B · Terminal.** First install Python (`winget` ships with Windows 10/11 —
skip this if you already have Python):

```bat
winget install -e --id Python.Python.3.12
```

**Close and reopen the terminal** so it picks up Python. Then, in the extracted
folder (click the address bar, type `cmd`, Enter):

```bat
pythonw study_logger\study_logger_widget.pyw
pythonw countdown\ca_countdown_widget.pyw
```

`pythonw` runs them silently (no console window — that's normal).

**C · Clone with git.**

```bat
git clone https://github.com/AyYasshhh/Study-Logger-Exam-countdown-widgets.git
cd Study-Logger-Exam-countdown-widgets
pythonw study_logger\study_logger_widget.pyw
pythonw countdown\ca_countdown_widget.pyw
```

First run opens the **setup popup** → fill it in → **SAVE & LAUNCH**. The widget
pins behind your apps, so press **`Win + D`** (show desktop) to see and click it.

## Using it

- **Study Logger:** click a subject chip → **▶ START** → **⏸ PAUSE** →
  **■ END** (saved to `study_log.jsonl`; <30 s discarded). Click the panel
  header to flip **TODAY bars ⇄ 14-day heatmap**. Colours mean *what to study
  next*: red = neglected, orange = slipping, white = ahead.
- **Countdown:** live d/h/m/s to your next paper; digits go white → orange
  (≤15 d) → red (≤24 h). Schedule strip highlights the next paper and strikes
  out finished ones.

| Action | How |
|---|---|
| **Move** | Double-click a blank spot (border turns red) → drag → double-click to lock. |
| **Resize** (logger) | Same red-border mode → drag a **corner** (scales uniformly). |
| **Quit** | **Right-click** the widget (a running session is saved first). |

## Start automatically with Windows

Easiest: run `setup.bat` → option **2** (it makes the Startup shortcuts for
you; option 3 removes them). Or by hand: right-click a `.pyw` → *Create
shortcut*, press `Win+R`, type `shell:startup`, and drop the shortcut in.

## Change your setup later

Reopen the popup anytime (this keeps your logged history):

```bat
python study_logger\study_logger_widget.pyw --setup
python countdown\ca_countdown_widget.pyw --setup
```

<details>
<summary><b>What's in the setup popup?</b></summary>

**Study Logger** → *widget title* + **2–8 subjects**, each with a full name and
a short unique **chip** label (auto-uppercased, ≤6 chars, e.g. `PHY`). Saved to
`study_logger/subjects.json`.

**Exam Countdown** → *header line*, *short name* (used in "…till **this**…"),
*leave-home time* (`HH:MM`, 24h — the countdown targets when you leave, not the
paper start), *exam-hours text*, and **1–8 papers** (date `YYYY-MM-DD` + name +
unique chip). Saved to `countdown/countdown_config.json`. The popup validates
entries and shows a red hint instead of saving on a mistake.
</details>

<details>
<summary><b>Your data & backups</b></summary>

Everything stays local next to the scripts and is gitignored:

| File | What | Delete? |
|---|---|---|
| `study_logger/study_log.jsonl` | your study history (one JSON line/session) | **No — back this up** |
| `*/subjects.json`, `*/countdown_config.json` | your setup | yes (re-runs popup) |
| `*/widget_state.json` | position / scale / view | yes (resets position) |
| `study_logger/active_session.json` | crash-safety checkpoint (auto-cleaned) | yes |

A running session is checkpointed every 30 s, so a crash recovers your time on
next launch.
</details>

<details>
<summary><b>Troubleshooting</b></summary>

| Problem | Fix |
|---|---|
| Can't see the widget | It's behind your apps by design — press **`Win + D`**. |
| Stuck / frozen / invisible | Double-click `restart_widgets.pyw` (or `setup.bat` → 4) — kills & relaunches both. |
| Double-click does nothing | `.pyw` isn't linked to Python: right-click → *Open with* → **Python**, or use the terminal. |
| Want to see errors | Run with `python` (not `pythonw`) from a terminal for a console with logs. |
| Digits look like a plain font | `anton.ttf` must sit next to the `.pyw`; otherwise it falls back to Segoe UI Black. |
</details>

<details>
<summary><b>How it works (the fun part)</b></summary>

Pinning a window to the Windows 11 wallpaper layer hides two traps:

1. **A reparented window never repaints until its size changes once** — so the
   widgets do a one-shot 1-pixel "jiggle" after pinning.
2. **The desktop-icons layer (`SHELLDLL_DefView`) eats mouse clicks** aimed at
   the classic `WorkerW`, so the widgets parent into **Progman** and raise
   above the icons layer instead — still behind all apps, but clickable.

Full debugging story in [study_logger/GOAL.md](study_logger/GOAL.md) and the
per-widget `upgrades.md` changelogs.
</details>

## Files

| path | what |
|---|---|
| `setup.bat` + `setup.ps1` | one-click setup/launcher menu |
| `study_logger/study_logger_widget.pyw` | the study logger (one file) |
| `countdown/ca_countdown_widget.pyw` | the exam countdown (one file) |
| `restart_widgets.pyw` | silent kill-and-relaunch for both |
| `*/anton.ttf` | Anton font for the big digits (SIL OFL) |

## License

Code: MIT (see [LICENSE](LICENSE)). Anton font by Vernon Adams, SIL Open Font
License 1.1 (see [FONT_LICENSE.md](FONT_LICENSE.md)).
