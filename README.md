# Study Desktop Widgets

Two tiny Windows desktop widgets that live **on your wallpaper** — behind
every app, in front of the desktop icons — built with plain Python/tkinter.
No Electron, no browser engine, ~30 MB RAM total.

- **Study Logger** — pick a subject, run a stopwatch, every session is
  logged. Glance views: today's bars per subject, a 14-day heatmap, an
  all-time strength strip, and urgency colours that tell you *what to study
  next* (red = neglected, white = ahead).
- **Exam Countdown** — big live countdown to your next paper, heat-coloured
  digits as the day approaches, full schedule strip with each paper in its
  subject's colour.

**Works for any student, any stream** — the first launch pops a setup window
where you type your own subjects / exam dates. Everything is saved to a
small JSON file next to the script (re-open the editor anytime with
`--setup`).

## Screenshots

**Study Logger** — subject bars, 14-day heatmap, urgency strip:

![study logger](assets/study_logger.png)

**Exam Countdown** — heat-coloured live countdown + schedule strip:

![exam countdown](assets/countdown.png)

**Both, pinned to the wallpaper behind every app:**

![both widgets on the desktop](assets/desktop.png)

## Quick start

Needs Windows 10/11 and Python 3.11+ (only stdlib; Pillow optional, just for
`--shot` layout screenshots).

```
pythonw study_logger/study_logger_widget.pyw
pythonw countdown/ca_countdown_widget.pyw
```

First run opens the setup popup → enter your subjects (logger) or exam
title + dates (countdown) → SAVE & LAUNCH. The widget pins itself to the
desktop layer; press `Win+D` to see and interact with it.

- **Move:** double-click a blank spot (border turns red) → drag → double-click to lock.
- **Resize (logger):** in that same mode, drag a **corner** — the whole
  widget scales uniformly, fonts and all.
- **Quit:** right-click the widget (a running session is saved first).
- **Autostart:** put a shortcut to `pythonw.exe <path to the .pyw>` in
  `shell:startup`.
- **Stuck?** run `restart_widgets.pyw` — kills and relaunches both cleanly.

## How it works (the fun part)

Pinning a window to the wallpaper layer on Windows 11 hides two nasty traps
we hit and documented:

1. **A reparented window never repaints until its size changes once.**
   `RedrawWindow`, forced repaints, moves — nothing works. The widgets do a
   one-shot 1-pixel resize "jiggle" after pinning; after that, paints flow
   normally.
2. **The desktop-icons layer (`SHELLDLL_DefView`) eats every mouse click**
   aimed at the classic wallpaper `WorkerW`, so a widget parented there can
   never be interactive. These widgets parent into **Progman** and raise
   themselves above the icons layer instead — still behind all apps, but
   clickable.

The full debugging story (bisecting with `PrintWindow` pixel oracles,
FreeType ink measurements for cropped digit tops, etc.) is in
[study_logger/GOAL.md](study_logger/GOAL.md) and the two `upgrades.md`
changelogs.

## Files

| path | what |
|---|---|
| `study_logger/` | the study logger widget (one file) + docs |
| `countdown/` | the exam countdown widget (one file) + docs |
| `restart_widgets.pyw` | silent kill-and-relaunch for both |
| `*/anton.ttf` | Anton font for the big digits (SIL OFL — see FONT_LICENSE.md) |

Your data stays local and out of git: `study_log.jsonl` (one JSON line per
session), `subjects.json` / `countdown_config.json` (your setup),
`widget_state.json` (position/scale) are all gitignored.

## License

Code: MIT (see [LICENSE](LICENSE)). Anton font by Vernon Adams, SIL Open
Font License 1.1 (see [FONT_LICENSE.md](FONT_LICENSE.md)).
