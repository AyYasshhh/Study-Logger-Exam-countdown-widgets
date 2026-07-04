"""One-click restarter for both study widgets (countdown + study logger).

Runs silently (no console). Kills any running copies first - each widget
holds a single-instance mutex, so a plain relaunch of a stuck/invisible
widget would just exit quietly - then starts both fresh.

Make a shortcut to this file (target: pythonw.exe "...\restart_widgets.pyw")
and drop it on your desktop as the everything-is-broken button.
"""
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PYW = sys.executable          # run the widgets with the same pythonw
WIDGETS = [
    (os.path.join(BASE, 'countdown'),    'ca_countdown_widget.pyw'),
    (os.path.join(BASE, 'study_logger'), 'study_logger_widget.pyw'),
]
NOWIN = 0x08000000   # CREATE_NO_WINDOW - keep everything invisible

kill = ("Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | "
        "Where-Object { $_.CommandLine -match "
        "'ca_countdown_widget|study_logger_widget' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")
subprocess.run(['powershell', '-NoProfile', '-Command', kill],
               creationflags=NOWIN)
time.sleep(1)

for cwd, script in WIDGETS:
    subprocess.Popen([PYW, os.path.join(cwd, script)], cwd=cwd,
                     creationflags=NOWIN)
