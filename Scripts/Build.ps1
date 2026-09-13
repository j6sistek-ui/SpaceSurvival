param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [ValidateSet('Editor','Content','Test','Package')][string]$Target = 'Editor'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$project = Join-Path $root 'SpaceSurvival.uproject'
$build = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$uat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat'
foreach ($required in @($build,$editor,$uat)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required Unreal tool is absent: $required. Install the full engine and Windows C++ toolchain before building. No artifact was produced." }
}
Push-Location $root
try {
    if ($Target -eq 'Editor') {
        & $build SpaceSurvivalEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE
    } elseif ($Target -eq 'Content') {
        & $editor $project -unattended -stdout -FullStdOutLogOutput -ExecutePythonScript="$root\Scripts\AuthorContent.py"
    } elseif ($Target -eq 'Test') {
        & $editor $project -unattended -NullRHI -stdout -FullStdOutLogOutput '-ExecCmds=Automation RunTests SpaceSurvival;Quit' '-TestExit=Automation Test Queue Empty' "-ReportExportPath=$root\Artifacts\UnrealTests"
    } else {
        if (-not (Test-Path -LiteralPath (Join-Path $root 'Content\SpaceSurvival\Maps\Survival.umap'))) { throw 'AuthorContent must finish successfully before packaging.' }
        & $uat BuildCookRun "-project=$project" -noP4 -platform=Win64 -clientconfig=Development -build -cook -stage -pak -iostore -archive "-archivedirectory=$root\Artifacts\Windows" -utf8output
    }
    if ($LASTEXITCODE -ne 0) { throw "$Target failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
