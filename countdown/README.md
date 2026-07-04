# CA Inter Exam Countdown (Sept 2026) — Desktop widget

**`ca_countdown_widget.pyw`** — a tiny Python/tkinter widget pinned to the desktop
layer (behind all apps, in front of the wallpaper), bottom-right corner. Live
d/h/m/s countdown, ticks every second. No browser engine, no Lively — ~30 MB RAM,
near-zero CPU. Pair it with `luffy_gear5.png` set as the normal Windows wallpaper
(already done) and it looks like the old Lively version, minus the lag.

## Exam schedule (all papers 2–5 PM, countdown targets 1:30 PM leave time)
| Date | Paper |
|---|---|
| Sep 1 | Advanced Accounting |
| Sep 3 | Corporate & Other Laws |
| Sep 6 | Taxation |
| Sep 8 | Cost & Management Accounting |
| Sep 10 | Auditing & Ethics |
| Sep 12 | FM & SM |

## How it runs
- **Auto-starts with Windows** via a shortcut `CA_Countdown_Widget.lnk` in the
  Startup folder (`shell:startup`). Delete that shortcut to stop auto-start.
- Start manually: double-click `ca_countdown_widget.pyw`, or
  `C:/Python314/pythonw.exe ca_countdown_widget.pyw`
- **Quit:** right-click the widget text (or kill `pythonw.exe` in Task Manager).
- Only one instance can run at a time (a second launch exits silently).
- States switch by themselves:
  - before Sep 1 → live d/h/m/s till CA Inter + schedule strip
  - Sep 1–12 → next paper name (red) + live countdown + schedule strip
  - after Sep 12 1:30 PM → "DONE."
- The schedule strip (always visible) shows every paper in its subject's
  deep hue — same palette as the study-logger widget. Next paper = bright,
  today = red, past papers = struck through grey.
- Digit colour = urgency: white → orange (≤15 days) → reddish orange (≤7 days)
  → deep red (≤24 hours), based on time left to the current target
  (`HEAT` list in the config block to tweak).

## Tuning
Config block at the top of `ca_countdown_widget.pyw`: position offsets, colors,
font sizes, `TRANSPARENT` (True = text floats over wallpaper; False = solid black
card behind the text). Big digits use the Anton font (`anton.ttf`, loaded
privately at startup — falls back to Segoe UI Black if missing). Restart the
widget after editing.

**Preview looks/states without touching the running widget:**
- `python ca_countdown_widget.pyw --preview` — opens as a normal topmost window
  (no desktop pinning, no single-instance lock).
- add `--now 2026-09-05T10:00` to preview a future state.
- add `--shot out.png` to save a screenshot of the widget and exit.

## Old Lively wallpaper (retired 2026-07-04, kept for reference)
`ca_countdown_luffy.html` + `fire_config.js` + `anton.woff2` — the previous
Lively HTML wallpaper with ASCII fire. Retired because Lively's embedded browser
plus the 80-row/22-fps fire lagged the laptop. Still works if opened in a browser
(`?now=...` to preview states).
