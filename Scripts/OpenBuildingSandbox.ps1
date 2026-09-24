param([string]$EngineRoot = '', [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$sandboxRoot = Split-Path $PSScriptRoot -Parent
$sandboxReceipt = Join-Path $sandboxRoot 'Artifacts\BuildingSandbox\build.json'
if (-not (Test-Path -LiteralPath $sandboxReceipt)) { throw 'The building sandbox has not been prepared yet.' }
$sandboxData = Get-Content -LiteralPath $sandboxReceipt -Raw | ConvertFrom-Json
if (-not $sandboxData.complete -or $sandboxData.target_map -notmatch '^/Game/Blender/Sandbox/[A-Za-z0-9_]+$') {
    throw 'Sandbox preparation is incomplete or the map path is invalid. Inspect Artifacts\BuildingSandbox\build.json.'
}
$sandboxMap = $sandboxData.target_map
$sandboxMapFile = Join-Path $sandboxRoot ('Content\' + $sandboxMap.Substring(6).Replace('/', '\') + '.umap')
if (-not (Test-Path -LiteralPath $sandboxMapFile)) { throw "Sandbox map is missing: $sandboxMapFile" }
if (-not $EngineRoot) {
    $EngineRoot = @('C:\Program Files\EpicGames2\UE_5.8', 'C:\Program Files\Epic Games\UE_5.8') |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Engine\Binaries\Win64\UnrealEditor.exe') } |
        Select-Object -First 1
}
if (-not $EngineRoot) { throw 'Unreal 5.8 not found. Supply -EngineRoot with your installed engine directory.' }
$sandboxEditor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
if ($CheckOnly) {
    Write-Host "Sandbox ready: $sandboxMap"
    exit 0
}
if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) {
    Write-Host 'Unreal is already open. Save your current work, then open this map from the Content Browser:'
    Write-Host $sandboxMap
    exit 1
}
# Intentionally interactive: this launcher opens only when the owner runs it.
$sandboxProject = Join-Path $sandboxRoot 'SpaceSurvival.uproject'
Start-Process -FilePath $sandboxEditor -WindowStyle Normal -ArgumentList @(('"' + $sandboxProject + '"'), $sandboxMap)
