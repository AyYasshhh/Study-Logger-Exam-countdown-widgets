# folderuse — CA_Exam_Countdown

- `ca_countdown_widget.pyw` — **the countdown (current).** Tiny tkinter desktop
  widget, pinned to the wallpaper layer bottom-right, ticks every second.
  Config block at top (offsets, colors, TRANSPARENT toggle). Auto-starts via
  `CA_Countdown_Widget.lnk` in `shell:startup`. Right-click text to quit.
  Preview states: `python ca_countdown_widget.pyw --now 2026-09-05T10:00`.
- `anton.ttf` — Anton font converted from `anton.woff2` (fontTools). The widget
  loads it privately at startup (AddFontResourceExW) so the big digits match
  the old wallpaper exactly. Keep next to the .pyw.
- `luffy_gear5.png` — Gear-5 Luffy art (copy of D:\downloads\14_upscaled.png).
  Now set as the **static Windows wallpaper** (Fill); the widget sits in its
  black bottom-right corner.
- `README.md` — schedule, how the widget runs, tuning, preview.
- `upgrades.md` — changelog.

## Retired (kept for reference, safe to delete)
- `ca_countdown_luffy.html` — old Lively HTML wallpaper (art + countdown + ASCII
  fire). Retired 2026-07-04: Lively's embedded browser + 80-row/22-fps fire
  lagged the laptop. Still opens in a normal browser.
- `fire_config.js` — ASCII-fire settings for the HTML version.
- `anton.woff2` — Anton font for the HTML version (source of `anton.ttf`).

(Fire tuner server deleted 2026-07-03 after finalizing.)
(Old plain blue `ca_countdown_wallpaper.html` deleted 2026-07-03.)
(Toast-notification part removed 2026-07-03: task `CA_Inter_Countdown`
unregistered, its scripts deleted.)
