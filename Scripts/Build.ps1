param(
    [string]$EngineRoot = '',
    [ValidateSet('Editor','Content','Validate','Test','Package')][string]$Target = 'Editor'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if (-not $EngineRoot) {
    $EngineRoot = @('C:\Program Files\EpicGames2\UE_5.8','C:\Program Files\Epic Games\UE_5.8') |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe') } |
        Select-Object -First 1
    if (-not $EngineRoot) { throw 'Full UE 5.8 was not found. Supply -EngineRoot with the installed engine directory.' }
}
$project = Join-Path $root 'SpaceSurvival.uproject'
$build = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$uat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat'
foreach ($required in @($build,$editor,$uat)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required Unreal tool is absent: $required. Install the full engine and Windows C++ toolchain before building. No artifact was produced." }
}
function Invoke-ContentPython([string]$Script, [switch]$NoRendering) {
    $logDirectory = Join-Path $root 'Saved\Logs'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $scriptLog = Join-Path $logDirectory (([IO.Path]::GetFileNameWithoutExtension($Script)) + '-Harness.log')
    [string[]]$renderOptions = if ($NoRendering) { @('-NullRHI') } else { @() }
    & $editor $project -unattended -stdout -FullStdOutLogOutput @renderOptions "-ExecutePythonScript=$Script" 2>&1 | Tee-Object -FilePath $scriptLog
    if ($LASTEXITCODE -ne 0 -or (Select-String -LiteralPath $scriptLog -Pattern 'LogEditorPythonExecuter: Error:|LogPython: Error:|LogSavePackage: Error:' -Quiet)) {
        throw "Unreal Python/content failed; inspect $scriptLog. Editor exit code alone is insufficient."
    }
}
Push-Location $root
try {
    if ($Target -eq 'Editor') {
        & $build SpaceSurvivalEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE
    } elseif ($Target -eq 'Content') {
        Invoke-ContentPython "$root\Scripts\AuthorContent.py"
    } elseif ($Target -eq 'Validate') {
        Invoke-ContentPython "$root\Scripts\ValidateContent.py" -NoRendering
    } elseif ($Target -eq 'Test') {
        & $editor $project -unattended -NullRHI -stdout -FullStdOutLogOutput '-ExecCmds=Automation RunTests SpaceSurvival' '-TestExit=Automation Test Queue Empty' "-ReportExportPath=$root\Artifacts\UnrealTests"
    } else {
        if (-not (Test-Path -LiteralPath (Join-Path $root 'Content\SpaceSurvival\Maps\Survival.umap'))) { throw 'AuthorContent must finish successfully before packaging.' }
        & $uat BuildCookRun "-project=$project" -noP4 -platform=Win64 -clientconfig=Development '-ubtargs=-NoHotReloadFromIDE' -build -cook -stage -pak -iostore -prereqs -archive "-archivedirectory=$root\Artifacts\Windows" -utf8output
    }
    if ($LASTEXITCODE -ne 0) { throw "$Target failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
