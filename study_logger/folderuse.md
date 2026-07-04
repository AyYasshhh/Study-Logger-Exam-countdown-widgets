# folderuse — CA_Study_Logger

| file | purpose |
|---|---|
| `study_logger_widget.pyw` | The whole widget — stopwatch + subject chips + TODAY bars / 14-day heatmap views + urgency colours + all-time STRENGTH strip, desktop pinning (Progman child above the icons layer + resize-jiggle, see GOAL.md), drag-to-move, crash recovery. One file, config block at top. |
| `anton.ttf` | Anton font for the big timer digits (copied from CA_Exam_Countdown, loaded privately at runtime). |
| `study_log.jsonl` | The study log — one JSON line per ended session. Created on first END. **This is the data; back it up.** |
| `widget_state.json` | Remembered widget position + which overview view is active. Safe to delete (resets position). |
| `active_session.json` | Crash-safety checkpoint of the currently running session. Exists only while a session runs; auto-cleaned. |
| `README.md` | How to run and use the widget. |
| `upgrades.md` | Changelog. |
| `D:\BOTS\restart_widgets.pyw` (outside this folder) | The "Restart CA Widgets" desktop shortcut runs this — kills + relaunches both widgets when one is stuck or missing. |
