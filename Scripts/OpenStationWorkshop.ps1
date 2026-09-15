param([string]$EngineRoot = '', [switch]$Prepare)
$ErrorActionPreference = 'Stop'
$workshopRoot = Split-Path $PSScriptRoot -Parent
$workshopProject = Join-Path $workshopRoot 'SpaceSurvival.uproject'
if (-not $EngineRoot) {
    $EngineRoot = @('C:\Program Files\EpicGames2\UE_5.8','C:\Program Files\Epic Games\UE_5.8') |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Engine\Binaries\Win64\UnrealEditor.exe') } |
        Select-Object -First 1
}
if (-not $EngineRoot) { throw 'Unreal 5.8 not found. Supply -EngineRoot with your installed engine directory.' }
$workshopEditor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$workshopCmd = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$workshopModule = Join-Path $workshopRoot 'Binaries\Win64\UnrealEditor-SpaceSurvivalEditor.dll'
if (-not (Test-Path -LiteralPath $workshopModule)) {
    throw 'Build the editor once: Scripts\Build.ps1 -Target Editor, then run Scripts\OpenStationWorkshop.ps1 -Prepare.'
}
if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) {
    Write-Host 'Unreal is already open. In the SpaceSurvival editor choose Tools > Station Workshop, then Open Workshop.'
    exit 0
}
if ($Prepare) {
    $workshopScript = Join-Path $PSScriptRoot 'AuthorStationWorkshop.py'
    $workshopLog = Join-Path $workshopRoot 'Saved\Logs\WorkshopPreparation.log'
    New-Item -ItemType Directory -Path (Split-Path $workshopLog -Parent) -Force | Out-Null
    & $workshopCmd $workshopProject -run=pythonscript "-script=$workshopScript" -unattended -NullRHI -stdout -FullStdOutLogOutput 2>&1 | Tee-Object -FilePath $workshopLog
    if ($LASTEXITCODE -ne 0 -or (Select-String -LiteralPath $workshopLog -Pattern 'LogPython: Error:|LogSavePackage: Error:' -Quiet)) {
        throw 'Workshop preparation failed; inspect Saved\Logs\WorkshopPreparation.log.'
    }
    Write-Host 'Workshop prepared. Double-click Open Station Workshop.cmd when ready to edit.'
    exit 0
}
$workshopMap = '/Game/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop'
$workshopMapFile = Join-Path $workshopRoot 'Content\SpaceSurvival\Licensed\StationWorkshop\L_StationWorkshop.umap'
if (-not (Test-Path -LiteralPath $workshopMapFile)) {
    throw 'Prepare the workshop once: Scripts\OpenStationWorkshop.ps1 -Prepare.'
}
# This launcher is deliberately interactive; the owner runs it to open the editor.
Start-Process -FilePath $workshopEditor -ArgumentList @(('"' + $workshopProject + '"'), $workshopMap, '-ExecCmds="SS.Workshop.Open"')
