<##
Runs one read-only engine preflight followed by three fresh Unreal processes using the real
USSGameInstance storage methods. Every invocation creates a new GUID directory under
Artifacts/SaveLifecycle; nothing is deleted, backed up, or replaced in production storage.

UE 5.8 source contract, checked when authored:
  Core/Private/Misc/Paths.cpp: UserDir -> ProjectUserDir -> ProjectSavedDir (User/Saved).
  Engine/Public/SaveGameSystem.h: generic slots -> ProjectSavedDir/SaveGames/<slot>.sav.
  WindowsPlatformFeatures.cpp: optional custom backend; the test rejects any backend other
  than the exact generic singleton before GameInstance Init or any save write.

Build the Editor target first. Use -PreflightOnly to verify actual path/backend isolation
without initializing USSGameInstance or writing any save-game slots.
##>
param(
    [string]$EngineRoot = '',
    [ValidateRange(30, 1200)][int]$TimeoutSeconds = 300,
    [switch]$PreflightOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$project = Join-Path $repoRoot 'SpaceSurvival.uproject'
if (-not $EngineRoot) {
    $EngineRoot = @('C:\Program Files\EpicGames2\UE_5.8', 'C:\Program Files\Epic Games\UE_5.8') |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe') } |
        Select-Object -First 1
}
if (-not $EngineRoot) { throw 'An existing UE 5.8 installation is required; supply -EngineRoot.' }
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (-not (Test-Path -LiteralPath $editor -PathType Leaf)) { throw "Missing editor command executable: $editor" }
if (-not (Test-Path -LiteralPath $project -PathType Leaf)) { throw "Missing project: $project" }

function Assert-NoReparsePath([string]$Path) {
    $candidate = [IO.Path]::GetFullPath($Path)
    while ($candidate) {
        if (Test-Path -LiteralPath $candidate) {
            $item = Get-Item -LiteralPath $candidate -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing a redirected filesystem path: $candidate"
            }
        }
        $parentDirectory = [IO.Directory]::GetParent($candidate)
        $candidate = if ($null -ne $parentDirectory) { $parentDirectory.FullName } else { $null }
    }
}
function Get-ProductionSaveManifest {
    # Both default Windows locations for this project. Read hashes only; never copy payloads.
    $directories = @(
        (Join-Path $repoRoot 'Saved\SaveGames'),
        (Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'SpaceSurvival\Saved\SaveGames')
    ) | Sort-Object -Unique
    foreach ($directory in $directories) {
        Assert-NoReparsePath $directory
        $exists = Test-Path -LiteralPath $directory -PathType Container
        $files = @()
        if ($exists) {
            $files = @(Get-ChildItem -LiteralPath $directory -Filter '*.sav' -File -Force |
                Sort-Object Name | ForEach-Object {
                    Assert-NoReparsePath $_.FullName
                    [ordered]@{ name = $_.Name; bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
                })
        }
        [ordered]@{ directory = $directory; exists = $exists; files = $files }
    }
}
function ConvertTo-NativeArgument([string]$Value) {
    # All generated arguments have no embedded quotes or trailing backslash.
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsafe native argument quoting input.' }
    return '"' + $Value + '"'
}

$token = [Guid]::NewGuid().ToString('N')
$artifactParent = Join-Path $repoRoot 'Artifacts\SaveLifecycle'
$runRoot = [IO.Path]::GetFullPath((Join-Path $artifactParent $token))
Assert-NoReparsePath $runRoot
if (Test-Path -LiteralPath $runRoot) { throw 'Unexpected GUID directory collision; existing data is untouched.' }
$userRoot = Join-Path $runRoot 'User'
$savedRoot = Join-Path $userRoot 'Saved'
$saveGames = Join-Path $savedRoot 'SaveGames'
$productionBefore = @(Get-ProductionSaveManifest)
New-Item -ItemType Directory -Path $userRoot | Out-Null
[IO.File]::WriteAllText((Join-Path $runRoot '.ss-save-lifecycle'), $token)
$productionBefore | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runRoot 'production-before.json') -Encoding utf8
$stages = @('Preflight')
if (-not $PreflightOnly) { $stages += @('Suspend', 'ResumeDeath', 'FreshStart') }
$receipts = @()
$processIds = [Collections.Generic.HashSet[int]]::new()
$completed = $false
Write-Output "Lifecycle evidence directory: $runRoot"
try {
    foreach ($phase in $stages) {
        Assert-NoReparsePath $saveGames
        $phaseRoot = Join-Path $runRoot $phase
        New-Item -ItemType Directory -Path $phaseRoot | Out-Null
        $reportRoot = Join-Path $phaseRoot 'Report'
        $arguments = @(
            $project, '/Engine/Maps/Entry', '-unattended', '-NullRHI', '-nosound', '-NoSplash', '-NoLiveCoding',
            '-SaveToUserDir', "-UserDir=$userRoot", '-SSSaveLifecycle', "-SSSaveLifecycleRoot=$runRoot",
            "-SSSaveLifecycleToken=$token", "-SSSaveLifecyclePhase=$phase",
            '-ExecCmds=Automation RunTests SpaceSurvival.SaveLifecycle', '-TestExit=Automation Test Queue Empty',
            "-ReportExportPath=$reportRoot", "-abslog=$(Join-Path $phaseRoot 'Unreal.log')", '-stdout', '-FullStdOutLogOutput'
        )
        $nativeArguments = ($arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
        $process = Start-Process -FilePath $editor -WorkingDirectory $repoRoot -ArgumentList $nativeArguments `
            -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $phaseRoot 'stdout.log') `
            -RedirectStandardError (Join-Path $phaseRoot 'stderr.log')
        Write-Output "Started lifecycle $phase in process $($process.Id)."
        $timer = [Diagnostics.Stopwatch]::StartNew()
        while (-not $process.WaitForExit(1000)) {
            if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
                # This handle belongs only to the child process this harness just created.
                Stop-Process -Id $process.Id -Force
                throw "Lifecycle $phase exceeded $TimeoutSeconds seconds; only its owned process was stopped."
            }
        }
        $process.Refresh()
        if ($process.ExitCode -ne 0) { throw "Lifecycle $phase process exited $($process.ExitCode). Inspect $phaseRoot." }
        $reportPath = Join-Path $reportRoot 'index.json'
        $receiptPath = Join-Path $runRoot "$phase.json"
        if (-not (Test-Path -LiteralPath $reportPath) -or -not (Test-Path -LiteralPath $receiptPath)) {
            throw "Lifecycle $phase did not produce both a real automation report and a guarded success receipt."
        }
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        $expectedTest = "SpaceSurvival.SaveLifecycle.$phase"
        $matchingTests = @($report.tests | Where-Object { $_.fullTestPath -eq $expectedTest })
        if ($report.failed -ne 0 -or $report.notRun -ne 0 -or $matchingTests.Count -ne 1 -or
            $matchingTests[0].state -ne 'Success' -or @($report.tests).Count -ne 1) {
            throw "Lifecycle $phase automation did not pass its one expected test."
        }
        $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
        if ($receipt.token -ne $token -or $receipt.phase -ne $phase -or -not $receipt.success -or
            -not $receipt.genericBackendVerified -or $receipt.processId -ne $process.Id -or
            [IO.Path]::GetFullPath($receipt.savedDir) -ne [IO.Path]::GetFullPath($savedRoot) -or
            -not $processIds.Add([int]$receipt.processId)) {
            throw "Lifecycle $phase receipt failed path, backend, token, or distinct-process verification."
        }
        $actualSaves = @(if (Test-Path -LiteralPath $saveGames) {
            Get-ChildItem -LiteralPath $saveGames -Filter '*.sav' -File -Force
        })
        foreach ($file in $actualSaves) { Assert-NoReparsePath $file.FullName }
        if ($phase -eq 'Preflight') {
            if ($receipt.gameInstanceInitialized -or $actualSaves.Count -ne 0) {
                throw 'Preflight unexpectedly initialized a GameInstance or wrote a save-game slot.'
            }
            Write-Output "Verified isolated generic save path before writes: $saveGames"
        } else {
            $expectedSaves = @('SS_Account_v1.sav', 'SS_Settings_v1.sav', 'SS_Suspend_v1.sav')
            if (-not $receipt.gameInstanceInitialized -or
                @(Compare-Object $expectedSaves @($actualSaves.Name)).Count -ne 0) {
                throw "Lifecycle $phase did not produce exactly the three expected isolated save domains."
            }
        }
        $receipts += $receipt
        Write-Output "PASS $expectedTest (process $($process.Id))."
    }
    $completed = $true
} finally {
    $productionAfter = @(Get-ProductionSaveManifest)
    $productionAfter | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runRoot 'production-after.json') -Encoding utf8
    $productionUnchanged = ($productionBefore | ConvertTo-Json -Depth 8 -Compress) -ceq
                           ($productionAfter | ConvertTo-Json -Depth 8 -Compress)
    $isolatedFiles = @(if (Test-Path -LiteralPath $saveGames) {
        Get-ChildItem -LiteralPath $saveGames -Filter '*.sav' -File | Sort-Object Name | ForEach-Object {
            [ordered]@{ name = $_.Name; bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
        }
    })
    [ordered]@{
        success = $completed -and $productionUnchanged
        preflightOnly = [bool]$PreflightOnly
        token = $token
        root = $runRoot
        savedDir = $savedRoot
        productionSaveHashesUnchanged = $productionUnchanged
        processReceipts = $receipts
        isolatedSaveFiles = $isolatedFiles
        limitation = 'Storage lifecycle only; station UI, quit interaction and subjective gameplay are separate gates.'
    } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runRoot 'result.json') -Encoding utf8
    if (-not $productionUnchanged) {
        throw "Production save metadata changed during the harness; nothing was backed up or replaced. Inspect $runRoot."
    }
}
Write-Output "PASS: production save hashes unchanged. Evidence: $(Join-Path $runRoot 'result.json')"
