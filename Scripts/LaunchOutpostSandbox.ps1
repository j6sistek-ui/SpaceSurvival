param([switch]$Editor, [switch]$Offscreen)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $taskRoot 'SpaceSurvival.uproject'
$map = '/Game/OutpostSandbox/L_AsteroidOutpost'
$engine = @('C:\Program Files\EpicGames2\UE_5.8','C:\Program Files\Epic Games\UE_5.8') |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Engine\Binaries\Win64\UnrealEditor.exe') } |
    Select-Object -First 1
if (-not $engine) { throw 'Unreal Engine 5.8 is required.' }
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'Content\OutpostSandbox\L_AsteroidOutpost.umap'))) {
    throw 'The private outpost map is not authored in this checkout. See docs/OUTPOST_SANDBOX.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'Binaries\Win64\UnrealEditor-SpaceSurvival.dll'))) {
    throw 'Build this checkout with Scripts/Build.ps1 -Target Editor first.'
}
$binary = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor.exe'
$profile = Join-Path $taskRoot 'Artifacts\Outpost\PlayerProfile'
New-Item -ItemType Directory -Path $profile -Force | Out-Null
$arguments = @($project,$map,('-UserDir=' + $profile),'-SaveToUserDir','-nosplash','-DisablePlugins=UAssetBrowser,NwiroIntegrationKit')
if (-not $Editor) { $arguments += @('-game','-windowed','-ResX=1600','-ResY=900') }
if ($Offscreen) { $arguments += @('-RenderOffscreen','-unattended'); $binary = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe' }
& $binary @arguments
exit $LASTEXITCODE
