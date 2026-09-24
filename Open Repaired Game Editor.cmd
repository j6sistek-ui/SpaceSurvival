@echo off
setlocal
set "UE_EDITOR=C:\Program Files\EpicGames2\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EDITOR%" (
  echo Unreal Engine 5.8 is not installed at the configured location.
  pause
  exit /b 1
)
start "SpaceSurvival - Repaired Game" "%UE_EDITOR%" "%~dp0SpaceSurvival.uproject" /Game/SpaceSurvival/Maps/Survival -NoSplash -DisablePlugins=UAssetBrowser
