# GOAL — CA Study Logger widget

## What we want (the spec)

A second desktop widget, sister of `D:\BOTS\CA_Exam_Countdown\ca_countdown_widget.pyw`,
that tracks **how much time is actually studied per CA Inter subject, per day**.

1. **Stopwatch logger**
   - Click a subject chip (ACC / LAW / TAX / COST / AUD / FMSM) → it turns red.
   - ▶ START / ⏸ PAUSE-RESUME / ■ END. Paused time never counts.
   - On END the session is appended to `study_log.jsonl` (one JSON line per
     session: subject, date, start, end, seconds). Sessions under 30 s are
     discarded. Can't switch subject mid-session.
2. **Glance overview** (click its header to flip between two views)
   - **TODAY** — horizontal bar per subject, red `0` for untouched subjects,
     daily total, 7-day sparkline (today red).
   - **LAST 14 DAYS** — heatmap grid (subjects × days, darker→brighter = more
     hours), today's column outlined red, per-subject totals on the right.
   - Buckets are **daily** (user explicitly changed this from weekly).
   - **Urgency colours** (v1.4, user's 2/3 rule): a subject is red under 2/3
     of the average subject's time, orange under 90%, white over 4/3 — over
     three windows: labels = last 14 days, TODAY's hour numbers = today
     (after 2 h logged that day), strength strip = all-time. Every window is
     only judged once it holds 2 h of study.
   - **STRENGTH strip** (v1.3, always visible below the board): per-subject
     all-time heat cell (shade = hours vs strongest), total hours + days
     studied beneath, red outline on the weakest. Dark shades, same palette.
3. **Aesthetic** — must match the Luffy Gear 5 wallpaper and the countdown
   widget: pure black background, white/grey text, `#e63946` red accent,
   Anton font for the big digits.
   - v1.5: plus per-subject identity hues on the graphics only (chips, bars,
     heatmap cells, strength cells — dark muted tones, no reds/oranges so
     red always means urgency). Text stays urgency-coloured.
4. **Movable + resizable** — double-click a blank spot → border turns red →
   drag the body to move, drag a **corner** to scale the whole widget
   uniformly (fonts and all geometry together, 0.6×–2×; never elongates one
   axis) → double-click again to lock. Position + scale remembered in
   `widget_state.json`.
5. **Always running** — autostarts with Windows via `CA_Study_Logger.lnk` in
   `shell:startup` (already created), single-instance mutex, right-click quits
   (saving any running session first).
6. **Crash safe** — running session checkpointed to `active_session.json`
   every 30 s; recovered into the log on next launch.
7. Pinned to the **desktop layer** (behind apps, in front of wallpaper),
   exactly like the countdown widget — interact via Win+D.

## Status (2026-07-04) — DONE, bug fixed

- Widget fully built in `study_logger_widget.pyw`. Both views verified by
  screenshot in `--preview` mode; log append / aggregation / crash recovery
  verified by a headless test. Startup shortcut created.
- The invisibility bug is **fixed and verified** (PrintWindow capture of the
  pinned window shows the full UI rendering live). Widget is running.
- Interactivity fixed too (v1.2): the widget is now a **Progman child raised
  above the icons layer** — the old WorkerW parenting left it under
  `SHELLDLL_DefView`, which ate all mouse input. Click routing verified with
  `RealChildWindowFromPoint` and **confirmed working by the user with a real
  mouse** (clicking + drag-to-move both work).
- v1.3 shipped the urgency colours + STRENGTH strip (see spec above).
  Widget is running, autostart shortcut verified in shell:startup, headless
  log/recovery tests pass. **Project complete** — user is off studying.

### Root cause of the invisibility bug (solved 2026-07-04)

- **A window reparented into the wallpaper WorkerW never repaints until its
  SIZE changes at least once.** Repaints, `RedrawWindow`, `update_idletasks`,
  `update()`, and position-only moves all do nothing; one 1-px resize
  un-sticks it permanently (normal paints flow fine afterwards).
- That's why the countdown never hit it: its digit canvas re-measures
  proportional text and resizes the window every second. The logger idles at
  a fixed-size `00:00:00`, so its size never changed after pinning and its
  pre-pin (blank) surface stayed on screen forever.
- Found by bisecting with a `PrintWindow(PW_RENDERFULLCONTENT)` pixel oracle:
  every static-size test variant (even an exact countdown-style skeleton) was
  black; only variants whose size changed painted.
- **The fix** (`jiggle()` in the widget, called right after `SetParent`):
  bump the card's `pady` 13→14 and back 150 ms later. Two real resizes via
  tk's own auto-sizing, so the window keeps auto-sizing to content later
  (view toggles etc.). Keep this in mind for ANY future widget pinned to the
  desktop layer.
