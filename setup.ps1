# Study Desktop Widgets - one-click setup & launcher.
# Launched by setup.bat (double-click that). Finds Python (offers to install
# it if missing), then a small menu: launch, autostart on/off, restart,
# reconfigure. Nothing here changes your machine without you choosing it.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Info($m) { Write-Host $m -ForegroundColor Gray }
function Ok($m)   { Write-Host "  [ok] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Pause-Any { Write-Host ''; Read-Host 'Press Enter to return to the menu' | Out-Null }

# ---- find pythonw.exe (silent launcher), or $null ----
function Find-Pythonw {
    foreach ($cmd in 'py', 'python') {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            try {
                $base = (& $cmd -c "import sys,os;print(os.path.dirname(sys.executable))" 2>$null).Trim()
                if ($base) {
                    $pw = Join-Path $base 'pythonw.exe'
                    if (Test-Path $pw) { return $pw }
                }
            } catch { }
        }
    }
    # fallback: scan the usual install locations (covers a fresh winget install)
    $globs = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\pythonw.exe",
        "$env:ProgramFiles\Python3*\pythonw.exe",
        "${env:ProgramFiles(x86)}\Python3*\pythonw.exe",
        "C:\Python3*\pythonw.exe"
    )
    foreach ($g in $globs) {
        $hit = Get-ChildItem $g -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

# widget file paths (each writes its data next to itself, cwd doesn't matter)
$LOGGER    = Join-Path $root 'study_logger\study_logger_widget.pyw'
$COUNTDOWN = Join-Path $root 'countdown\ca_countdown_widget.pyw'
$RESTART   = Join-Path $root 'restart_widgets.pyw'
$startup   = [Environment]::GetFolderPath('Startup')
$links     = @{ 'Study Logger'   = $LOGGER
                'Exam Countdown' = $COUNTDOWN }

function Launch($file) {
    Start-Process -FilePath $pythonw -ArgumentList "`"$file`"" -WorkingDirectory (Split-Path $file)
}

function Add-Autostart {
    $wsh = New-Object -ComObject WScript.Shell
    foreach ($name in $links.Keys) {
        $lnk = $wsh.CreateShortcut((Join-Path $startup "$name.lnk"))
        $lnk.TargetPath       = $pythonw
        $lnk.Arguments        = "`"$($links[$name])`""
        $lnk.WorkingDirectory = Split-Path $links[$name]
        $lnk.Save()
        Ok "added '$name' to startup"
    }
}

function Remove-Autostart {
    foreach ($name in $links.Keys) {
        $p = Join-Path $startup "$name.lnk"
        if (Test-Path $p) { Remove-Item $p -Force; Ok "removed '$name' from startup" }
        else { Info "  ('$name' was not in startup)" }
    }
}

Clear-Host
Write-Host ''
Write-Host '  ================================================' -ForegroundColor Cyan
Write-Host '    STUDY DESKTOP WIDGETS  -  one-click setup' -ForegroundColor Cyan
Write-Host '  ================================================' -ForegroundColor Cyan
Write-Host ''

# ---- 1. ensure Python ----
$pythonw = Find-Pythonw
if (-not $pythonw) {
    Warn 'Python is not installed (or not on PATH).'
    Write-Host ''
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        $a = Read-Host '  Install Python 3.12 now with winget? (Y/N)'
        if ($a -match '^(y|yes)$') {
            Info '  Installing Python - this can take a minute...'
            winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
            $pythonw = Find-Pythonw
        }
    }
    if (-not $pythonw) {
        Write-Host ''
        Warn 'Could not find Python. Install it, then run setup.bat again:'
        Info '   https://www.python.org/downloads/windows/'
        Info '   (tick "Add python.exe to PATH" during install)'
        Start-Process 'https://www.python.org/downloads/windows/'
        Pause-Any
        return
    }
}
Ok "using: $pythonw"

# ---- 2. menu loop ----
while ($true) {
    Write-Host ''
    Write-Host '  --------------------------------------------' -ForegroundColor DarkGray
    Write-Host '    1  Launch both widgets now' -ForegroundColor White
    Write-Host '    2  Start automatically with Windows (add to startup)' -ForegroundColor White
    Write-Host '    3  Remove from Windows startup' -ForegroundColor White
    Write-Host '    4  Restart both widgets (fix a stuck one)' -ForegroundColor White
    Write-Host '    5  Change my subjects / exams (setup popup)' -ForegroundColor White
    Write-Host '    Q  Quit' -ForegroundColor White
    Write-Host '  --------------------------------------------' -ForegroundColor DarkGray
    $choice = Read-Host '  Choose'

    switch ($choice.Trim().ToUpper()) {
        '1' {
            Info '  Launching Study Logger...'   ; Launch $LOGGER
            Info '  Launching Exam Countdown...' ; Launch $COUNTDOWN
            Write-Host ''
            Ok 'Launched. First run shows a setup popup for each widget.'
            Info '  Then press  Win + D  to see them on your desktop.'
            Pause-Any
        }
        '2' {
            Add-Autostart
            Ok 'Done - both will start silently at every login.'
            Pause-Any
        }
        '3' { Remove-Autostart; Pause-Any }
        '4' {
            Info '  Restarting both widgets...'
            Launch $RESTART
            Ok 'Restart triggered.'
            Pause-Any
        }
        '5' {
            Info '  Opening the setup popups (change subjects / exams)...'
            Start-Process -FilePath $pythonw -ArgumentList "`"$LOGGER`"", '--setup'    -WorkingDirectory (Split-Path $LOGGER)
            Start-Process -FilePath $pythonw -ArgumentList "`"$COUNTDOWN`"", '--setup' -WorkingDirectory (Split-Path $COUNTDOWN)
            Ok 'Edit and press SAVE & LAUNCH in each popup.'
            Pause-Any
        }
        'Q' { Write-Host ''; Info '  Bye.'; return }
        default { Warn 'Type 1, 2, 3, 4, 5 or Q.' }
    }
}
