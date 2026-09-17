@echo off
rem Installs (or updates) the SpaceSurvival Live Link add-on into every Blender found on this machine.
rem Double-click it. Close Blender first, or restart it afterwards: an open Blender keeps running the old copy.
rem It runs Tools\SSLiveLink\install.py once per Blender version; that script copies the add-on into Blender's own
rem add-ons folder, records where this project is, and switches the add-on on in Blender's saved preferences.
setlocal
title Install the SpaceSurvival Blender add-on
set "HERE=%~dp0"
set "FOUND="
for %%V in (5.2 5.1 5.0 4.5 4.4 4.3 4.2) do call :install "%ProgramFiles%\Blender Foundation\Blender %%V\blender.exe" %%V
echo.
if not defined FOUND goto :none
echo Finished. If Blender is open, close it and start it again.
echo The panel is in the 3D viewport: press N, then the "SS Link" tab. Its last line shows the add-on's version.
goto :end

:none
echo No Blender was found under "%ProgramFiles%\Blender Foundation".
echo Install Blender, or run this by hand:   blender.exe --background --python "%HERE%install.py"

:end
echo.
pause
exit /b 0

:install
if not exist "%~1" exit /b 0
set "FOUND=1"
echo.
echo === Blender %2 ===
"%~1" --background --python "%HERE%install.py"
if errorlevel 1 (
  echo   FAILED for Blender %2: the lines above say why.
) else (
  echo   Installed into Blender %2.
)
exit /b 0
