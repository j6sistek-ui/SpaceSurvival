<# Open the station used by the current game in this project's normal editor. #>
param(
    [string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8',
    [switch]$Offscreen,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$project = Join-Path $root 'SpaceSurvival.uproject'
$map = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
$binaryName = if ($Offscreen) { 'UnrealEditor-Cmd.exe' } else { 'UnrealEditor.exe' }
$editor = Join-Path $EngineRoot ('Engine/Binaries/Win64/' + $binaryName)
$module = Join-Path $root 'Binaries/Win64/UnrealEditor-SpaceSurvival.dll'
$mapFile = Join-Path $root 'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
foreach ($required in @($editor, $project, $module, $mapFile)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Current station editor input is missing: $required. Restore the current content and build the Editor target first."
    }
}
if ($project.Contains('"')) { throw 'Unsupported quote in project path.' }
$arguments = @(('"' + $project + '"'), $map, '-nosplash')
if ($Offscreen) {
    $arguments += @('-RenderOffscreen', '-unattended', '-DisablePlugins=UAssetBrowser,NwiroIntegrationKit')
} else {
    $arguments += '-DisablePlugins=UAssetBrowser'
}
if ($DryRun) {
    [pscustomobject]@{ Editor = $editor; Project = $project; Map = $map; Arguments = $arguments }
    return
}
# Invoked by the owner to edit the current station; no build, map regeneration or profile reset.
$windowStyle = if ($Offscreen) { 'Hidden' } else { 'Normal' }
Start-Process -FilePath $editor -WorkingDirectory $root -WindowStyle $windowStyle -ArgumentList $arguments
