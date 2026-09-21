<#
Capture a seeded, scripted rendered endgame fixture using normal engine frames.
Default: current packaged inner executable. -Editor uses the installed editor with -game.
Requires a rebuilt binary containing ASSWave10Soak. No install, build or package occurs here.
Every run uses a fresh GUID profile, preserves production saves, binds exact file hashes,
and rejects incomplete fixture/CSV evidence. This is not natural gameplay acceptance.
Visual captures render offscreen. Nonvisual runs still require the caller to focus
the hidden launched game window before the foreground-only timing fixture starts.
#>
param(
    [switch]$Editor,
    [ValidateSet("Wave10", "Station5")][string]$Scenario = "Wave10",
    [string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8',
    [ValidateRange(160, 600)][int]$TimeoutSeconds = 240,
    [ValidateRange(640, 7680)][int]$Width = 2560,
    [ValidateRange(480, 4320)][int]$Height = 1440,
    [switch]$CaptureVisuals,
    [switch]$StationExterior,
    [ValidateSet('AlienFemale')][string]$Walker = '',
    [switch]$NoSound,
    # Passed through verbatim to the game. For opt-in build flags the fixture itself knows nothing about,
    # such as -SSPhoenix, so capturing a variant does not mean editing this script each time.
    [string[]]$ExtraArgs = @()
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Scenario = if ($Scenario -ieq 'Station5') { 'Station5' } else { 'Wave10' }
if ($StationExterior -and ($Scenario -ne 'Station5' -or -not $CaptureVisuals)) {
    throw '-StationExterior requires -Scenario Station5 -CaptureVisuals.'
}
if ($Walker -and ($Scenario -ne 'Station5' -or -not $CaptureVisuals)) {
    throw '-Walker requires -Scenario Station5 -CaptureVisuals.'
}
if ($Scenario -eq 'Station5' -and -not $PSBoundParameters.ContainsKey('TimeoutSeconds')) { $TimeoutSeconds = 330 }
$evidenceType = if ($Scenario -eq 'Station5') { 'RENDERED_TRANSITION_FIXTURE_NOT_NATURAL_GAMEPLAY' } else { 'RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY' }
# The seven Exit frames are shots of a hero climbing out of the ship. The owner cancelled that animation
# (RPT-20260917-01), so a hero may have no exit clip at all, and a run with that hero has no climb-out to
# film: it is standing outside the ship when the docking motion ends. Which list applies is not knowable
# before the run - the hero the station actually possessed decides it - so the Station5 list is completed
# from the receipt below rather than assumed here.
$expectedVisualNames = if ($Scenario -eq 'Station5') {
    @('Flight', 'Climax', 'Wormhole', 'Approach', 'Docking',
        'StationIdle', 'StationServices', 'StationOverview', 'CombatImpact')
} else { @('Flight', 'Climax', 'Compound', 'Approach') }
if ($StationExterior) { $expectedVisualNames += @('StationColonyOverview', 'StationPadMouth') }
if ($Walker) { $expectedVisualNames += @('WalkerOut', 'WalkerTurn', 'WalkerReturn') }
$exitVisualNames = @('Exit0', 'Exit1', 'Exit2', 'Exit3', 'Exit4', 'Exit5', 'Exit6')
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
function SourceFileIdentity([string]$RelativePath) {
    $logicalPath = Join-Path $repoRoot $RelativePath
    $contentRoot = Join-Path $repoRoot 'Content'
    # Isolated Unreal worktrees may share the owner's licensed Content through one junction.
    # Resolve only this read-only source input. Output, binary and save paths retain the strict
    # no-reparse rule, and FileIdentity still rejects nested redirects in the resolved input.
    if ($RelativePath.Replace('\', '/').StartsWith('Content/', [StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $contentRoot) -and
        (((Get-Item -LiteralPath $contentRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        $targets = @((Get-Item -LiteralPath $contentRoot -Force).Target)
        if ($targets.Count -ne 1 -or -not [IO.Path]::IsPathRooted($targets[0])) {
            throw 'Shared Content must have one absolute junction target.'
        }
        $resolvedRoot = [IO.Path]::GetFullPath($targets[0]).TrimEnd('\', '/')
        $resolved = [IO.Path]::GetFullPath((Join-Path $resolvedRoot $RelativePath.Substring(8)))
        if (-not $resolved.StartsWith($resolvedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Source content escaped the resolved Content root.'
        }
        $identity = FileIdentity $resolved
        $identity.logicalPath = $logicalPath
        return $identity
    }
    FileIdentity $logicalPath
}
function PngIdentity([string]$Path) {
    $identity = FileIdentity $Path
    $stream = [IO.File]::OpenRead($Path)
    try {
        $header = [byte[]]::new(24)
        if ($stream.Read($header, 0, 24) -ne 24 -or
            [BitConverter]::ToString([byte[]]$header[0..7]).Replace('-', '') -cne '89504E470D0A1A0A' -or
            [Text.Encoding]::ASCII.GetString($header, 12, 4) -cne 'IHDR') { throw "Invalid PNG header: $Path" }
        $pngWidth = [uint32]$header[16] * 16777216 + [uint32]$header[17] * 65536 + [uint32]$header[18] * 256 + [uint32]$header[19]
        $pngHeight = [uint32]$header[20] * 16777216 + [uint32]$header[21] * 65536 + [uint32]$header[22] * 256 + [uint32]$header[23]
        if ($pngWidth -ne $Width -or $pngHeight -ne $Height) { throw "Unexpected screenshot size ${pngWidth}x${pngHeight}: $Path" }
        $identity.width = $pngWidth
        $identity.height = $pngHeight
        return $identity
    } finally { $stream.Dispose() }
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
    $identities = @($paths | ForEach-Object { SourceFileIdentity $_ })
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
$arguments += @('-SSWave10Soak', "-SSSoakScenario=$Scenario", '-SaveToUserDir', "-UserDir=$userRoot", "-SSWave10SoakRoot=$runRoot", '-windowed', "-ResX=$Width", "-ResY=$Height",
    '-NoSplash', '-NoLiveCoding', '-csvGpuStats', "-abslog=$logPath", '-unattended')
if ($NoSound) { $arguments += '-nosound' }
if ($ExtraArgs.Count -gt 0) { $arguments += $ExtraArgs }
if ($CaptureVisuals) { $arguments += @('-SSSoakVisuals', '-RenderOffscreen', '-ForceRes') }
if ($StationExterior) { $arguments += '-SSStationExteriorReview' }
if ($Walker) { $arguments += "-SSSoakWalker=$Walker" }
$process = $null
$success = $false
$failure = $null
$fixture = $null
$analysis = $null
$images = @()
$started = [DateTime]::UtcNow.ToString('o')
$sourceBefore | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runRoot 'source-before.json') -Encoding utf8
$productionBefore | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runRoot 'production-before.json') -Encoding utf8
Write-Output "Endgame fixture evidence: $runRoot"
try {
    $native = ($arguments | ForEach-Object { NativeArgument $_ }) -join ' '
    $process = Start-Process -FilePath $exe -WorkingDirectory $repoRoot -ArgumentList $native -WindowStyle Hidden -PassThru
    Write-Output "Started owned hidden process $($process.Id). Scenario $Scenario; offscreen visuals=$([bool]$CaptureVisuals); no natural gameplay claim."
    if (-not $CaptureVisuals) { Write-Output 'Foreground timing run: focus this owned game window within 60 seconds.' }
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while (-not $process.WaitForExit(1000)) {
        if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'Rendered fixture exceeded timeout.' }
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0) { throw "Rendered fixture exited $($process.ExitCode)." }
    $fixturePath = Join-Path $runRoot 'fixture.json'
    Assert-NoReparsePath $fixturePath
    $fixture = Get-Content -LiteralPath $fixturePath -Raw | ConvertFrom-Json
    if ($Scenario -eq 'Station5') {
        if (-not ($fixture.PSObject.Properties.Name -contains 'heroClimbsOut')) {
            throw 'Fixture receipt predates the conditional exit; rebuild the binary before capturing.'
        }
        if ($fixture.heroClimbsOut) { $expectedVisualNames += $exitVisualNames }
        if ($StationExterior -and (-not ($fixture.PSObject.Properties.Name -contains 'stationExteriorReview') -or
                -not $fixture.stationExteriorReview)) {
            throw 'Fixture receipt does not certify the requested station exterior review; rebuild the binary.'
        }
        if ($Walker -and ($fixture.requestedWalker -cne $Walker -or $fixture.stationHero -cne $Walker -or
                -not $fixture.walkerMotionComplete -or $fixture.walkerMaximumTravelCm -lt 100)) {
            throw 'Fixture did not certify the exact requested walker and actual short movement.'
        }
    }
    if (-not $fixture.success -or $fixture.evidenceType -cne $evidenceType -or $fixture.scenario -cne $Scenario -or
        $fixture.token -cne $token -or $fixture.processId -ne $process.Id -or
        ($CaptureVisuals -and (-not $fixture.visualCaptureEnabled -or -not $fixture.offscreenVisualOnly -or
            $fixture.suitableForPerformanceFinding -or @($fixture.visualRequests).Count -ne $expectedVisualNames.Count)) -or
        (-not $CaptureVisuals -and ($fixture.visualCaptureEnabled -or $fixture.offscreenVisualOnly -or -not $fixture.allFixtureFramesForeground)) -or
        -not $fixture.noSaveSlotsWritten -or
        [IO.Path]::GetFullPath($fixture.savedDir).TrimEnd('\', '/') -ine [IO.Path]::GetFullPath($savedRoot).TrimEnd('\', '/') -or
        -not $fixture.sawBreathing -or -not $fixture.sawClimax -or -not $fixture.sawApproach -or
        $fixture.climaxSimulationSeconds -lt 39.5) {
        throw 'Fixture receipt did not satisfy exact process/profile/full-duration/composition checks.'
    }
    if ($CaptureVisuals) {
        $actualNames = @($fixture.visualRequests | ForEach-Object { $_.name } | Sort-Object -CaseSensitive)
        $expectedNames = @($expectedVisualNames | Sort-Object -CaseSensitive)
        if (($actualNames -join ',') -cne ($expectedNames -join ',')) { throw 'Visual receipt has missing, duplicate or unexpected scene names.' }
        $actualPngNames = @(Get-ChildItem -LiteralPath $runRoot -Filter '*.png' -File | ForEach-Object { $_.BaseName } | Sort-Object -CaseSensitive)
        if (($actualPngNames -join ',') -cne ($expectedNames -join ',')) { throw 'PNG files do not match the exact required scene names.' }
        $images = @($expectedVisualNames | ForEach-Object { PngIdentity (Join-Path $runRoot "$_.png") })
        if ($Scenario -eq 'Station5') {
            $combat = @($fixture.visualRequests | Where-Object { $_.name -ceq 'CombatImpact' })[0]
            if (-not $combat.normalWeaponKill -or $combat.combatSecondsSinceKill -lt 0.15 -or
                $combat.combatSecondsSinceKill -gt 0.65 -or -not $combat.combatSourceEnemy -or
                $combat.combatSystem -cne '/Game/SpaceSurvival/Licensed/Combat/NS_EnemyExplosion.NS_EnemyExplosion') {
                throw 'Combat capture does not identify a live explosion after a real weapon kill.'
            }
            $reviewStages = @(@('Wormhole', 2), @('StationServices', 7), @('StationOverview', 12))
            if ($StationExterior) { $reviewStages += @(@('StationColonyOverview', 17), @('StationPadMouth', 22)) }
            foreach ($stage in $reviewStages) {
                $row = @($fixture.visualRequests | Where-Object { $_.name -ceq $stage[0] })[0]
                if ($row.requestStageSeconds -lt $stage[1]) { throw "Visual stage captured too early: $($stage[0])" }
                if ($stage[0] -cne 'Wormhole' -and -not $row.scriptedStationReviewCamera) { throw 'Station review frame lacks its labeled fixture viewpoint.' }
            }
            if ($Walker) {
                foreach ($name in @('StationIdle', 'WalkerOut', 'WalkerTurn', 'WalkerReturn')) {
                    $row = @($fixture.visualRequests | Where-Object { $_.name -ceq $name })[0]
                    if ($row.hero -cne $Walker -or $row.requestedWalker -cne $Walker -or
                        -not $row.walkerMeshVisible -or -not $row.actualWalkerView -or
                        $row.scriptedStationReviewCamera -or -not $row.walkerMesh) {
                        throw "Requested walker frame lacks the actual visible body/player camera: $name"
                    }
                    if ($name -cne 'StationIdle' -and ($row.walkerSpeed -le 40 -or -not $row.animation)) {
                        throw "Requested motion frame does not show an actually moving, animated walker: $name"
                    }
                }
            }
        }
    }
    if ($Scenario -eq 'Station5') {
        # Getting off the ship is certified two ways and the hero decides which one this run owes. One with
        # an exit clip owes the climb-out itself. One with none owes the same arrival without the animation:
        # the docking motion really ran, and it really ended with the player standing on the station's own
        # floor, on the deck, clear of the docked hull, collision and walking restored, for at least as long
        # as the climb-out would have taken. Neither may be paid with the other's evidence - a hero with no
        # clip that somehow recorded exit time is a broken transition, not a pass.
        # The standing arrival is owed for the whole idle window rather than a slice of it, and it is owed
        # without a rescue: the walker's own Tick hauls a pawn that is off the deck back to its spawn and
        # sets it walking, which rebuilds every clause of that evidence, so an arrival that went wrong and
        # was healed would otherwise read exactly like one that was right.
        foreach ($field in 'offDeckRescues', 'playerViewOnDeckSeconds') {
            if (-not ($fixture.PSObject.Properties.Name -contains $field)) {
                throw "Station receipt predates '$field'; rebuild before certifying."
            }
        }
        $arrival = if ($fixture.heroClimbsOut) {
            $fixture.sawAuthoredExit -and $fixture.exitSimulationSeconds -ge 2.3
        } else {
            (-not $fixture.sawAuthoredExit) -and $fixture.exitSimulationSeconds -eq 0 -and
            $fixture.sawStandingExit -and $fixture.standingOnDeckSeconds -ge 2.3 -and
            $fixture.standingOnDeckSeconds -ge ($fixture.stationIdleSimulationSeconds - 1.5) -and
            $fixture.playerViewOnDeckSeconds -ge 2.3
        }
        $arrival = $arrival -and $fixture.offDeckRescues -eq 0
        if (-not $fixture.sawWave5 -or -not $fixture.sawWormhole -or -not $fixture.sawDocking -or -not $arrival -or
            $fixture.wormholeSimulationSeconds -lt 7.9 -or $fixture.dockingSimulationSeconds -lt 2.9 -or
            $fixture.stationIdleSimulationSeconds -lt 15 -or $fixture.approachSimulationSeconds -le 0) {
            throw "Station fixture lacks full wormhole/docking/arrival/idle coverage (hero=$($fixture.stationHero) climbsOut=$($fixture.heroClimbsOut) exit=$($fixture.exitSimulationSeconds) standingOnDeck=$($fixture.standingOnDeckSeconds) of $($fixture.stationIdleSimulationSeconds) playerView=$($fixture.playerViewOnDeckSeconds) rescues=$($fixture.offDeckRescues))."
        }
    } elseif (-not $fixture.sawWave9 -or $fixture.compoundActorPresenceSeconds -lt 3.5 -or $fixture.approachSimulationSeconds -lt 5) {
        throw 'Endgame fixture lacks full Wave9/compound/approach coverage.'
    }
    $csv = Join-Path $runRoot 'Endgame.csv'
    Assert-NoReparsePath $csv
    if ([IO.Path]::GetFullPath($fixture.csv) -ine [IO.Path]::GetFullPath($csv)) { throw 'Fixture returned an unexpected CSV path.' }
    $output = Join-Path $runRoot 'performance.json'
    $captureNote = if ($CaptureVisuals) { 'Screenshot readbacks and ListTextures perturb timing: this run is visual evidence only, not a performance finding.' } else { 'No automated screenshot readback.' }
    if ($Walker) { $captureNote += ' Requested walker motion is appended as CSV Stage9 after stationary acceptance; stationary counters exclude that motion.' }
    & $python -B (Join-Path $repoRoot 'Scripts/AnalyzePerformance.py') $csv --log $logPath --output $output `
        --context-note "Explicit seeded $Scenario fixture with enlarged durability and scripted controls; no natural progression/feel claim." --context-note $captureNote
    if ($LASTEXITCODE -ne 0) { throw 'Completed CSV analysis failed.' }
    $analysis = Get-Content -LiteralPath $output -Raw | ConvertFrom-Json
    if ($Scenario -eq 'Station5') {
        # Stage 7 in the timeline is the climb-out. A run whose hero has one owes 2.3 s of it in the CSV as
        # well as in the receipt; a run whose hero has none owes exactly zero, and its arrival is the
        # docking stage plus the full stationary hub. Demanding zero is not a relaxation: it is what catches
        # the receipt and the timeline disagreeing about whether a transition ran at all.
        $exitStageSeconds = $analysis.station_fixture.stages.AuthoredExit.simulation_seconds
        $exitStageOk = if ($fixture.heroClimbsOut) { $exitStageSeconds -ge 2.3 } else { $exitStageSeconds -eq 0 }
        if ($analysis.status -cne 'RENDERED_STATION_FIXTURE_ONLY_NOT_60_FPS_ACCEPTANCE' -or -not $analysis.station_fixture.observed -or
            (-not $CaptureVisuals -and -not $analysis.station_fixture.all_fixture_frames_foreground) -or $analysis.station_fixture.stages.Wormhole.simulation_seconds -lt 7.9 -or
            $analysis.station_fixture.stages.Docking.simulation_seconds -lt 2.9 -or -not $exitStageOk -or
            $analysis.station_fixture.stages.StationIdle.simulation_seconds -lt 15) { throw "CSV lacks station transition and foreground evidence (exitStage=$exitStageSeconds climbsOut=$($fixture.heroClimbsOut))." }
    } elseif ($analysis.status -cne 'RENDERED_ENDGAME_FIXTURE_ONLY_NOT_60_FPS_ACCEPTANCE' -or -not $analysis.endgame_fixture.observed -or (-not $CaptureVisuals -and -not $analysis.endgame_fixture.all_fixture_frames_foreground) -or
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
        evidenceType = $evidenceType; scenario = $Scenario
        success = ($success -and $productionPreserved -and $sourceUnchanged -and $artifactUnchanged -and $noSlots)
        failure = $failure; token = $token; mode = $(if ($Editor) { 'UncookedEditorGame' } else { 'WindowsDevelopmentPackage' })
        startedUtc = $started; finishedUtc = [DateTime]::UtcNow.ToString('o')
        processId = $(if ($null -ne $process) { $process.Id } else { $null })
        processExit = $(if ($null -ne $process -and $process.HasExited) { $process.ExitCode } else { $null })
        artifacts = $artifactsBefore; artifactsUnchanged = $artifactUnchanged
        sourceSnapshot = $sourceBefore; sourceUnchanged = $sourceUnchanged
        productionBefore = $productionBefore; productionAfter = $productionAfter; productionPreserved = $productionPreserved
        noTestSaveSlotsWritten = $noSlots; requestedResolution = @($Width, $Height); audioDisabled = [bool]$NoSound
        visualCaptureEnabled = [bool]$CaptureVisuals; suitableForPerformanceFinding = -not [bool]$CaptureVisuals
        requestedWalker = $Walker
        offscreenVisualOnly = [bool]$CaptureVisuals; images = $images
        fixture = $fixture; analysisPath = $(if ($null -ne $analysis) { 'performance.json' } else { $null })
        evidenceFiles = @(Get-ChildItem -LiteralPath $runRoot -File | Sort-Object Name | ForEach-Object { FileIdentity $_.FullName })
        limits = 'Seeded Tier V starter/RapidLaser/OverdriveCooling; base durability 50000; normal timers/caps/budgets/spatial admission; scripted input. Exact bytes/process are recorded, but separate build provenance must bind compiled source. No physical input, natural balance, full ten-wave run, natural station interactions, final art, clean-machine or representative FPS acceptance.'
    }
    $result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runRoot 'result.json') -Encoding utf8
    Write-Output "Endgame result: $(Join-Path $runRoot 'result.json'); success=$($result.success)"
    # Say which hero the token certifies. Nothing fails when the licensed pack is absent - selection just
    # falls through to a hero that does climb out and the other branch passes - so the one way to notice
    # that a capture certified somebody else's arrival is for the capture to name who it filmed.
    if ($Scenario -eq 'Station5' -and $null -ne $fixture) {
        Write-Output "Station hero: $($fixture.stationHero); climbsOut=$($fixture.heroClimbsOut); onDeck=$($fixture.standingOnDeckSeconds) of $($fixture.stationIdleSimulationSeconds); playerView=$($fixture.playerViewOnDeckSeconds); rescues=$($fixture.offDeckRescues)"
    }
}
if (-not $result.success) { throw "Endgame fixture did not pass all capture/isolation checks: $failure" }
