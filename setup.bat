@echo off
REM One-click entry point: just launches the PowerShell menu next to this file.
REM Double-click this. Everything else happens in setup.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
