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
function Invoke-ContentPython([string]$Script) {
    $logDirectory = Join-Path $root 'Saved\Logs'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $scriptLog = Join-Path $logDirectory (([IO.Path]::GetFileNameWithoutExtension($Script)) + '-Harness.log')
    # -RenderOffscreen keeps a real RHI (content authoring builds meshes and shaders and needs one)
    # while leaving the editor window off the owner's screen. NullRHI would take the RHI away too.
    & $editor $project -unattended -stdout -FullStdOutLogOutput -RenderOffscreen "-ExecutePythonScript=$Script" 2>&1 | Tee-Object -FilePath $scriptLog
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
        Invoke-ContentPython "$root\Scripts\ValidateContent.py"
    } elseif ($Target -eq 'Test') {
        $testStarted = [DateTime]::UtcNow
        & $editor $project -unattended -NullRHI -stdout -FullStdOutLogOutput '-ExecCmds=Automation RunTests SpaceSurvival' '-TestExit=Automation Test Queue Empty' "-ReportExportPath=$root\Artifacts\UnrealTests"
        if ($LASTEXITCODE -ne 0) { throw "Unreal automation process failed with exit code $LASTEXITCODE." }
        $reportPath = Join-Path $root 'Artifacts\UnrealTests\index.json'
        if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf) -or
            (Get-Item -LiteralPath $reportPath).LastWriteTimeUtc -lt $testStarted) {
            throw 'Unreal automation produced no fresh report; process exit code alone is insufficient.'
        }
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        if ($report.succeeded -lt 1 -or $report.failed -ne 0 -or $report.notRun -ne 0 -or
            $report.succeededWithWarnings -ne 0 -or @($report.tests).Count -ne $report.succeeded -or
            @($report.tests | Where-Object { $_.state -ne 'Success' }).Count -gt 0) {
            throw "Unreal automation did not pass cleanly; inspect $reportPath."
        }
    } else {
        if (-not (Test-Path -LiteralPath (Join-Path $root 'Content\SpaceSurvival\Maps\Survival.umap'))) { throw 'AuthorContent must finish successfully before packaging.' }
        $packageLogs = Join-Path $root 'Artifacts\BuildLogs'
        New-Item -ItemType Directory -Path $packageLogs -Force | Out-Null
        $packageLog = Join-Path $packageLogs ("WindowsPackage-" + [Guid]::NewGuid().ToString('N') + '.log')
        & $uat BuildCookRun "-project=$project" -noP4 -platform=Win64 -clientconfig=Development '-ubtargs=-NoHotReloadFromIDE' -build -cook -stage -pak -iostore -prereqs -archive "-archivedirectory=$root\Artifacts\Windows" -utf8output 2>&1 | Tee-Object -FilePath $packageLog
        if ($LASTEXITCODE -ne 0) { throw "Package failed with exit code $LASTEXITCODE; inspect $packageLog." }
        & "$PSScriptRoot\BundlePrerequisites.ps1" -BuildLog $packageLog
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'TryNewShip.cmd') -Destination (Join-Path $root 'Artifacts\Windows\Try New Ship.cmd') -Force
        $acknowledgements = Join-Path $root 'THIRD_PARTY.md'
        $acknowledgementsOutput = Join-Path $root 'Artifacts\Windows\THIRD_PARTY.md'
        if ((Test-Path -LiteralPath $acknowledgementsOutput) -and
            ((Get-Item -LiteralPath $acknowledgementsOutput -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Refusing redirected acknowledgements output.'
        }
        Copy-Item -LiteralPath $acknowledgements -Destination $acknowledgementsOutput -Force
        if ((Get-FileHash -LiteralPath $acknowledgements -Algorithm SHA256).Hash -ne
            (Get-FileHash -LiteralPath $acknowledgementsOutput -Algorithm SHA256).Hash) {
            throw 'Packaged acknowledgements differ from the project source.'
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "$Target failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
