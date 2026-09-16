@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\PlayDevelopmentBuild.ps1"
if errorlevel 1 pause
