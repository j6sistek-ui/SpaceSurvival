<#
Capture a seeded, scripted rendered endgame fixture using normal engine frames.
Default: current packaged inner executable. -Editor uses the installed editor with -game.
Requires a rebuilt binary containing ASSWave10Soak. No install, build or package occurs here.
Every run uses a fresh GUID profile, preserves production saves, binds exact file hashes,
and rejects incomplete fixture/CSV evidence. This is not natural gameplay acceptance.
#>
param(
    [switch]$Editor,
    [string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8',
    [ValidateRange(160, 600)][int]$TimeoutSeconds = 240,
    [ValidateRange(640, 7680)][int]$Width = 2560,
    [ValidateRange(480, 4320)][int]$Height = 1440,
    [switch]$NoSound
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
function Assert-NoReparsePath([string]$Path) {
    $candidate = [IO.Path]::GetFullPath($Path)
    while ($candidate) {
        if (Test-Path -LiteralPath $candidate) {
            if (((Get-Item -LiteralPath $candidate -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing redirected path: $candidate"
            }
        }
        $parent = [IO.Directory]::GetParent($candidate)
        $candidate = if ($null -ne $parent) { $parent.FullName } else { $null }
    }
}
function FileIdentity([string]$Path) {
    Assert-NoReparsePath $Path
    $item = Get-Item -LiteralPath $Path
    [ordered]@{ path = $item.FullName; bytes = $item.Length; sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
}
function ProductionSaves {
    foreach ($directory in @((Join-Path $repoRoot 'Saved/SaveGames'),
        (Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'SpaceSurvival/Saved/SaveGames'))) {
        Assert-NoReparsePath $directory
        $exists = Test-Path -LiteralPath $directory -PathType Container
        $files = @()
        if ($exists) {
            $files = @(Get-ChildItem -LiteralPath $directory -File -Filter '*.sav' -Force | Sort-Object Name |
                ForEach-Object { FileIdentity $_.FullName })
        }
        [ordered]@{ directory = $directory; exists = $exists; files = $files }
    }
}
function SourceSnapshot {
    $head = (& git -C $repoRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read source HEAD.' }
    $paths = @(& git -C $repoRoot ls-files --cached --others --exclude-standard -- Source Config Content `
        Scripts/AnalyzePerformance.py Scripts/CaptureEndgame.ps1 SpaceSurvival.uproject | Sort-Object -Unique)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate source/content snapshot.' }
    $identities = @($paths | ForEach-Object { FileIdentity (Join-Path $repoRoot $_) })
    $dirty = @(& git -C $repoRoot status --porcelain -- Source Config Content Scripts/AnalyzePerformance.py Scripts/CaptureEndgame.ps1 SpaceSurvival.uproject)
    [ordered]@{ head = $head; dirtyEntries = $dirty; rawWorktreeFiles = $identities;
        bindingLimit = 'Exact contemporaneous source/content snapshot. A separate successful build/package receipt must bind these sources to this executable; HEAD alone does not prove compilation.' }
}
function NativeArgument([string]$Value) {
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsafe native argument.' }
    '"' + $Value + '"'
}
$python = Join-Path $EngineRoot 'Engine/Binaries/ThirdParty/Python3/Win64/python.exe'
$package = Join-Path $repoRoot 'Artifacts/Windows'
if ($Editor) {
    $exe = Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
    $artifactPaths = @($exe, (Join-Path $repoRoot 'Binaries/Win64/UnrealEditor-SpaceSurvival.dll'))
} else {
    $exe = Join-Path $package 'SpaceSurvival/Binaries/Win64/SpaceSurvival.exe'
    $artifactPaths = @((Join-Path $package 'SpaceSurvival.exe'), $exe)
    $paksRoot = Join-Path $package 'SpaceSurvival/Content/Paks'
    Assert-NoReparsePath $paksRoot
    foreach ($extension in @('pak', 'utoc', 'ucas')) {
        if (-not (Test-Path -LiteralPath (Join-Path $paksRoot "SpaceSurvival-Windows.$extension") -PathType Leaf)) {
            throw "Required project container missing: $extension"
        }
    }
    $artifactPaths += @(Get-ChildItem -LiteralPath $paksRoot -File |
        Where-Object { $_.Extension -in @('.pak', '.utoc', '.ucas') } | Sort-Object Name | ForEach-Object { $_.FullName })
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Existing Unreal Python required for CSV analysis.' }
$artifactsBefore = @($artifactPaths | ForEach-Object { FileIdentity $_ })
$sourceBefore = SourceSnapshot
$productionBefore = @(ProductionSaves)
$token = [Guid]::NewGuid().ToString('N')
$runRoot = Join-Path $repoRoot "Artifacts/EndgameSoak/$token"
Assert-NoReparsePath $runRoot
if (Test-Path -LiteralPath $runRoot) { throw 'Fresh fixture directory already exists.' }
$userRoot = Join-Path $runRoot 'User'
$savedRoot = Join-Path $userRoot 'Saved'
$slotsRoot = Join-Path $savedRoot 'SaveGames'
New-Item -ItemType Directory -Path $slotsRoot | Out-Null
$token | Set-Content -LiteralPath (Join-Path $runRoot '.ss-endgame-soak') -Encoding utf8
$logPath = Join-Path $runRoot 'Rendered.log'
$arguments = @()
if ($Editor) { $arguments += @((Join-Path $repoRoot 'SpaceSurvival.uproject'), '-game') }
$arguments += @('-SSWave10Soak', '-SaveToUserDir', "-UserDir=$userRoot", "-SSWave10SoakRoot=$runRoot", '-windowed', "-ResX=$Width", "-ResY=$Height",
    '-NoSplash', '-NoLiveCoding', '-csvGpuStats', "-abslog=$logPath", '-unattended')
if ($NoSound) { $arguments += '-nosound' }
$process = $null
$success = $false
$failure = $null
$fixture = $null
$analysis = $null
$started = [DateTime]::UtcNow.ToString('o')
$sourceBefore | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runRoot 'source-before.json') -Encoding utf8
$productionBefore | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runRoot 'production-before.json') -Encoding utf8
Write-Output "Endgame fixture evidence: $runRoot"
try {
    $native = ($arguments | ForEach-Object { NativeArgument $_ }) -join ' '
    $process = Start-Process -FilePath $exe -WorkingDirectory $repoRoot -ArgumentList $native -WindowStyle Normal -PassThru
    Write-Output "Started owned rendered process $($process.Id). Normal Wave 9 and 40-second Wave 10; no natural gameplay claim."
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while (-not $process.WaitForExit(1000)) {
        if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'Rendered fixture exceeded timeout.' }
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0) { throw "Rendered fixture exited $($process.ExitCode)." }
    $fixturePath = Join-Path $runRoot 'fixture.json'
    Assert-NoReparsePath $fixturePath
    $fixture = Get-Content -LiteralPath $fixturePath -Raw | ConvertFrom-Json
    if (-not $fixture.success -or $fixture.evidenceType -cne 'RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY' -or
        $fixture.token -cne $token -or $fixture.processId -ne $process.Id -or -not $fixture.noSaveSlotsWritten -or -not $fixture.allFixtureFramesForeground -or
        [IO.Path]::GetFullPath($fixture.savedDir).TrimEnd('\', '/') -ine [IO.Path]::GetFullPath($savedRoot).TrimEnd('\', '/') -or
        -not $fixture.sawWave9 -or -not $fixture.sawBreathing -or -not $fixture.sawClimax -or -not $fixture.sawApproach -or
        $fixture.climaxSimulationSeconds -lt 39.5 -or $fixture.compoundActorPresenceSeconds -lt 3.5 -or $fixture.approachSimulationSeconds -lt 5) {
        throw 'Fixture receipt did not satisfy exact process/profile/full-duration/composition checks.'
    }
    $csv = Join-Path $runRoot 'Endgame.csv'
    Assert-NoReparsePath $csv
    if ([IO.Path]::GetFullPath($fixture.csv) -ine [IO.Path]::GetFullPath($csv)) { throw 'Fixture returned an unexpected CSV path.' }
    $output = Join-Path $runRoot 'performance.json'
    & $python -B (Join-Path $repoRoot 'Scripts/AnalyzePerformance.py') $csv --log $logPath --output $output `
        --context-note 'Explicit seeded endgame fixture with enlarged durability and scripted controls; no natural progression/feel claim.'
    if ($LASTEXITCODE -ne 0) { throw 'Completed CSV analysis failed.' }
    $analysis = Get-Content -LiteralPath $output -Raw | ConvertFrom-Json
    if ($analysis.status -cne 'RENDERED_ENDGAME_FIXTURE_ONLY_NOT_60_FPS_ACCEPTANCE' -or -not $analysis.endgame_fixture.observed -or -not $analysis.endgame_fixture.all_fixture_frames_foreground -or
        $analysis.endgame_fixture.compound_presence_simulation_seconds -lt 3.5) { throw 'CSV lacks the required fixture/composition evidence.' }
    $success = $true
} catch {
    $failure = $_.Exception.Message
} finally {
    if ($null -ne $process -and -not $process.HasExited) {
        Stop-Process -InputObject $process -Force
        if (-not $process.WaitForExit(10000)) { throw 'Owned capture process did not exit.' }
    }
    $productionAfter = @(ProductionSaves)
    $sourceAfter = SourceSnapshot
    $artifactPathsAfter = $artifactPaths
    if (-not $Editor) {
        $artifactPathsAfter = @((Join-Path $package 'SpaceSurvival.exe'), $exe)
        $artifactPathsAfter += @(Get-ChildItem -LiteralPath $paksRoot -File |
            Where-Object { $_.Extension -in @('.pak', '.utoc', '.ucas') } | Sort-Object Name | ForEach-Object { $_.FullName })
    }
    $artifactsAfter = @($artifactPathsAfter | ForEach-Object { FileIdentity $_ })
    $productionPreserved = ($productionBefore | ConvertTo-Json -Depth 12 -Compress) -ceq ($productionAfter | ConvertTo-Json -Depth 12 -Compress)
    $sourceUnchanged = ($sourceBefore | ConvertTo-Json -Depth 12 -Compress) -ceq ($sourceAfter | ConvertTo-Json -Depth 12 -Compress)
    $artifactUnchanged = ($artifactsBefore | ConvertTo-Json -Depth 12 -Compress) -ceq ($artifactsAfter | ConvertTo-Json -Depth 12 -Compress)
    Assert-NoReparsePath $slotsRoot
    $noSlots = @(Get-ChildItem -LiteralPath $slotsRoot -File -Force).Count -eq 0
    $result = [ordered]@{
        evidenceType = 'RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY'
        success = ($success -and $productionPreserved -and $sourceUnchanged -and $artifactUnchanged -and $noSlots)
        failure = $failure; token = $token; mode = $(if ($Editor) { 'UncookedEditorGame' } else { 'WindowsDevelopmentPackage' })
        startedUtc = $started; finishedUtc = [DateTime]::UtcNow.ToString('o')
        processId = $(if ($null -ne $process) { $process.Id } else { $null })
        processExit = $(if ($null -ne $process -and $process.HasExited) { $process.ExitCode } else { $null })
        artifacts = $artifactsBefore; artifactsUnchanged = $artifactUnchanged
        sourceSnapshot = $sourceBefore; sourceUnchanged = $sourceUnchanged
        productionBefore = $productionBefore; productionAfter = $productionAfter; productionPreserved = $productionPreserved
        noTestSaveSlotsWritten = $noSlots; requestedResolution = @($Width, $Height); audioDisabled = [bool]$NoSound
        fixture = $fixture; analysisPath = $(if ($null -ne $analysis) { 'performance.json' } else { $null })
        evidenceFiles = @(Get-ChildItem -LiteralPath $runRoot -File | Sort-Object Name | ForEach-Object { FileIdentity $_.FullName })
        limits = 'Seeded Tier V starter/RapidLaser/OverdriveCooling; base durability 50000; normal timers/caps/budgets/spatial admission; scripted input. Exact bytes/process are recorded, but separate build provenance must bind compiled source. No physical input, natural balance, full ten-wave run, station docking, final art, clean-machine or representative FPS acceptance.'
    }
    $result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runRoot 'result.json') -Encoding utf8
    Write-Output "Endgame result: $(Join-Path $runRoot 'result.json'); success=$($result.success)"
}
if (-not $result.success) { throw "Endgame fixture did not pass all capture/isolation checks: $failure" }
