# upgrades — CA_Study_Logger

## 2026-07-04 — v1.8: timer digit headroom
- Same bug the user spotted on the countdown (round digit tops clipped):
  measured Anton ink rises 45px above the baseline at the logger's 52px
  size, and the canvas allowed exactly 45px — zero margin, so corner-resize
  rounding could flatten 0/6/8/9 tops. `BIG_H` 48 → 50.

## 2026-07-04 — v1.7: corner-drag resize (uniform scaling)
- In move mode (double-click), dragging within 22px of any corner now scales
  the whole widget instead of moving it: all fonts and every canvas
  dimension (bars, heatmap cells, strength strip, paddings) multiply by one
  factor, clamped 0.6×–2×. Dragging the body still moves. No per-axis
  stretching, per user spec.
- Scale persists as `scale` in `widget_state.json`; live-applied in 4% steps
  during the drag to stay light on the laptop.
- Verified by screenshotting --preview at 0.7 / 1.0 / 1.3 / 1.5 with sample
  data (deleted after): both views + strength strip scale proportionally.

## 2026-07-04 — v1.6: deep jewel palette + white digits (anti-pastel pass)
- User verdict on v1.5: palette too pastel, widget felt dull next to the
  countdown's big white digits.
- Subject hues deepened to jewel tones (deep steel blue / deep teal / dark
  gold / deep green / deep violet / deep cyan). Chips now show the full hue
  when unselected and **lighten toward white** when selected (new `lift()`
  helper) instead of being dimmed.
- Heat cells use new `heat_shade()`: dark hue → full hue → glows toward
  white at the top, so the strongest cells pop on black.
- Stopwatch digits now big white (like the countdown) when idle/running,
  grey only while paused. FAINT idle grey was what made it feel dead.
- Also this session: countdown widget ported to the same Progman pinning
  (its seconds stalled + right-click never worked; see its upgrades.md).

## 2026-07-04 — v1.5: per-subject identity colours
- Each subject got its own dark hue (`SUBJ_HUE` in the config block): ACC
  steel blue, LAW teal, TAX sand gold, COST moss green, AUD violet, FMSM
  cyan. No reds/oranges — those stay reserved for urgency.
- Channel split: **text = urgency** (unchanged 2/3 rule), **graphics =
  identity** — chips (dim when unselected, full hue when selected; selection
  no longer uses red), TODAY bar fills, heatmap cells (brightness within the
  subject's hue via new `tint()` helper), strength cells.
- Removed the now-unused greyscale `SHADES` ramp.
- Verified: both views screenshot-checked with throwaway sample data
  (deleted after), widget restarted, paint + click routing re-checked.

## 2026-07-04 — v1.4: urgency rule switched to the user's 2/3-of-average
- One formula everywhere now (user's design, tuned): red < 2/3 of the average
  subject's time, orange < 90%, white > 4/3, judged only after 2 h in the
  window. Three windows: labels = last 14 days, TODAY's hour numbers = today
  (so a subject that got under 2/3 of today's per-subject average shows a red
  time), strength strip = all-time.
- Rationale: user proposed "below today's average = red for the day"; tuned
  to 2/3 + a 2 h floor so one morning session doesn't paint the other five
  subjects red instantly.
- Verified with a throwaway sample log (deleted after): TAX at 20 m of a
  4 h 50 m day correctly went red while 1 h 30 m LAW stayed white; strength
  strip flags all-time weak subjects; paint + click routing re-checked after
  restart.

## 2026-07-04 — v1.3: urgency colours + all-time STRENGTH strip
- Subject labels (TODAY bars, 14-day heatmap, strength strip) now coloured by
  last-14-day study time vs the subject average: red <50%, dark orange <80%,
  grey ≈ average, white >130% (ahead). No colours until 2 h total is logged
  (too little data to judge; avoids everything screaming red on day one).
- New always-visible **STRENGTH** strip under the board: per subject an
  all-time heat cell (shade = total hours vs strongest subject), total hours
  and days-studied beneath, red outline on the weakest. Live session is
  folded in.
- Verified: headless log/aggregation/recovery test re-run (temp paths), both
  views screenshot-checked in --preview with throwaway sample data (deleted
  after), pinned widget restarted and paint + click-routing re-verified.

## 2026-07-04 — v1.2: made the pinned widget clickable
- Problem: visible but dead to clicks/drag. Cause: it was parented into the
  wallpaper WorkerW, and the desktop-icons layer (`SHELLDLL_DefView`) sits
  ABOVE that WorkerW and swallows every mouse click over the whole desktop.
- Fix: `pin()` now parents the widget into **Progman itself** and raises it
  above the icons layer (`SetWindowPos` to top of Progman's children,
  re-asserted every 30 s). Still behind all apps; interact after Win+D.
  Removed the now-unused `find_desktop_layer()`. The v1.1 resize-jiggle is
  still needed and still applied after pinning.
- Verified: widget sits above `SHELLDLL_DefView` in Progman's z-order,
  `RealChildWindowFromPoint` routes clicks at title/buttons/board to the
  widget, and PrintWindow confirms it still paints.
- Note: the countdown widget still lives in the WorkerW below the icons, so
  its right-click-quit likely doesn't work either — same 3-line fix applies
  if wanted.

## 2026-07-04 — v1.1: fixed the desktop-layer invisibility bug
- Root cause: a window reparented into the wallpaper WorkerW never repaints
  until its **size** changes once (repaints / RedrawWindow / moves don't help).
  The countdown widget dodged this by accident — its digit canvas resizes the
  window every second; the logger idles at a fixed size, so it stayed blank.
- Fix: new `jiggle()` — right after pinning, bump the card `pady` 13→14 and
  back 150 ms later (two real resizes through tk auto-sizing, so the window
  still auto-sizes to content afterwards). Removed the useless `RedrawWindow`
  call. Verified rendering via PrintWindow capture of the pinned window.

## 2026-07-04 — v1: initial build
- New widget, sister of the CA_Exam_Countdown one (same black / white / `#e63946` red, Anton digits, desktop-layer pinning via WorkerW).
- Stopwatch: subject chips → start / pause / end; sessions append to `study_log.jsonl`; <30 s sessions discarded; can't switch subject mid-session.
- Overview panel, click header to toggle:
  - **TODAY** bars per subject (red `0` for untouched) + total + 7-day sparkline.
  - **LAST 14 DAYS** heatmap (subjects × days, shade = hours, today outlined red) + per-subject totals.
  - Buckets are **daily** (user changed from weekly during planning).
- Live session is folded into the board mid-session (refreshes every minute).
- Double-click blank space → drag-to-move mode (red border), double-click to lock; position persisted in `widget_state.json`.
- Right-click quit ends & saves any running session first.
- Crash recovery: `active_session.json` checkpoint every 30 s, banked into the log on next launch.
- Tested: both views screenshot-verified in `--preview`; append/aggregate/recovery covered by a headless test. Heatmap totals column was clipped → widened canvas.
