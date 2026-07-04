# CA Study Logger — desktop widget

Sister widget to `D:\BOTS\CA_Exam_Countdown`. Pick a subject, run a stopwatch,
and every finished session is logged. The lower panel shows where your study
time actually went — per day, at a glance.

## Run it

```
C:/Python314/pythonw.exe study_logger_widget.pyw     (silent, normal use)
python study_logger_widget.pyw                        (with console, debug)
python study_logger_widget.pyw --preview              (normal topmost window, for testing)
```

It pins itself to the **desktop layer** — behind all your apps, in front of
the wallpaper and the desktop icons. To interact with it, show the desktop
(`Win+D`), then click. (Technically: it's a child of Progman raised above the
icons layer — see GOAL.md for why; the countdown's WorkerW trick renders but
can't receive clicks.)

## How to use

1. **Click a subject chip** (ACC / LAW / TAX / COST / AUD / FMSM) — turns red.
2. **▶ START** — big timer runs, red dot pulses.
3. **⏸ PAUSE / ▶ RESUME** — pause breaks; paused time is never counted.
4. **■ END** — session saved to `study_log.jsonl`. Sessions under 30 s are discarded.
5. You can't switch subjects mid-session — END first (keeps the log honest).

## The overview panel (click its header to flip views)

- **TODAY** — bar per subject for today, `0` in red for untouched subjects,
  daily total, and a 7-day sparkline (today's bar is red).
- **LAST 14 DAYS** — heatmap grid, subjects × days, darker→brighter = more
  hours, today's column outlined red, per-subject 14-day totals on the right.

## Subject colours (identity)

Every subject owns a deep jewel tone, used on all the *graphics*: its chip,
its TODAY bar, its heatmap row and its strength cell. Heat cells run dark →
full hue → a white-ish glow for the strongest, so the busiest cells pop.
Chips show their full hue; the selected one lightens toward white.

ACC deep steel blue · LAW deep teal · TAX dark gold · COST deep green ·
AUD deep violet · FMSM deep cyan. Deliberately no reds/oranges — those are
reserved for urgency. (Palette lives in `SUBJ_HUE` in the config block.)

## Reading the colours (urgency at a glance)

One rule everywhere — a subject is judged against **the average subject's
time** in a window, and goes red at **2/3 of that average**:

| colour | meaning |
|---|---|
| **red** | under 2/3 of the average — needs the most work |
| **dark orange** | under 90% of the average — falling behind |
| grey | around average — fine |
| **white** | over 4/3 of the average — ahead, can ease off |

The same rule runs over three windows:

- **Subject names** (both views + strength strip labels) → **last 14 days**:
  your current pattern. Fix a subject this week and it stops being red.
- **Hours numbers in TODAY** → **today only**: once 2h+ is logged today, a
  subject that got under 2/3 of today's per-subject average shows its time
  in red. Untouched subjects show a red `0` regardless.
- **Strength strip** → **all-time** balance (see below).

A window only gets judged after 2 hours of study are in it — before that
everything stays grey (too little data; day one won't scream red).

## The STRENGTH strip (always visible, bottom)

One column per subject, all-time: cell shade = total hours vs your strongest
subject (darker→brighter), with total hours and days-studied underneath
(`30h / 10d`). The weakest subjects get a red outline. This is the "where am
I weak overall" glance; the panel above is the "what about today / this
fortnight" glance.

## Moving & resizing it

Double-click any blank spot (title, timer, empty space) → border turns red:

- **drag the body** → moves it anywhere
- **drag a corner** → resizes the whole widget uniformly — fonts, bars,
  heatmap cells, everything scales together (0.6×–2×, no stretching one
  axis)

Double-click again to lock. Position and scale are remembered in
`widget_state.json`.

## Quitting

Right-click the widget. A running session is ended and **saved first** — you
never lose time by quitting.

## Crash safety

While a session runs, progress is checkpointed to `active_session.json` every
30 s. If the laptop dies mid-session, the next launch banks the time up to the
last checkpoint into the log (marked `"recovered": true`).

## Data

`study_log.jsonl` — one JSON line per session, append-only, plain text:

```json
{"subject": "Tax", "date": "2026-07-04", "start": "2026-07-04T10:36:42", "end": "2026-07-04T12:06:42", "sec": 5400}
```

Easy to back up, grep, or load into polars later for deeper stats.

## If it ever disappears / acts stuck

Double-click **"Restart CA Widgets"** on the desktop — it silently kills and
relaunches BOTH widgets (this one + the countdown). The script behind it is
`D:\BOTS\restart_widgets.pyw`. A plain relaunch wouldn't work on a stuck
widget because of the single-instance lock; this shortcut handles that.

## Autostart

Already set up (2026-07-04): `CA_Study_Logger.lnk` in `shell:startup` runs
`C:\Python314\pythonw.exe study_logger_widget.pyw` at every login, same as the
countdown widget. Single-instance lock means a manual run while it's already
up just exits quietly. To disable autostart, delete that shortcut from
`shell:startup`.
