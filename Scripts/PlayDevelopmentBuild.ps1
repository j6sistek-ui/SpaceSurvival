<# Open the rebuilt development game with its own persistent review profile. #>
param([string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$editor = Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
$project = Join-Path $root 'SpaceSurvival.uproject'
$module = Join-Path $root 'Binaries/Win64/UnrealEditor-SpaceSurvival.dll'
foreach ($required in @($editor, $project, $module)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Development build is missing: $required. Build the Editor target first."
    }
}
$profile = Join-Path $root 'Artifacts/DevelopmentReviewUser'
if ($profile.Contains('"') -or $project.Contains('"')) { throw 'Unsupported quote in project path.' }
# This opens the interactive game window requested by the owner. It does not
# build, author assets, package or overwrite the installed game's save profile.
Start-Process -FilePath $editor -WorkingDirectory $root -WindowStyle Normal -ArgumentList @(
    ('"' + $project + '"'), '-game', '-windowed', '-ResX=1600', '-ResY=900',
    ('-UserDir="' + $profile + '"'), '-SaveToUserDir', '-nosplash'
)
