<#
Capture normal-stat Wave1, the seeded Wave5 wormhole, or the inactive startup title in a hidden game process.
No build, package, publication or save operation is performed. Screenshots are not FPS evidence.
#>
param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')][string]$Label = 'CombinedLook',
    [string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8',
    [switch]$Packaged,
    [switch]$Sequence,
    [switch]$OfflineSequence,
    [switch]$WeaponReadability,
    [switch]$DirectorReview,
    [switch]$WormholeReview,
    [switch]$OutpostReview,
    [switch]$ApartmentWalk,
    [switch]$TailReview,
    [switch]$QualityBenchmark,
    [ValidateSet(2048,6144)][int]$DistantCount = 6144,
    [switch]$MainMenu,
    [switch]$UIRefresh,
    [switch]$UIFollowup,
    [switch]$UIFlightMenus,
    [ValidateRange(640,7680)][int]$Width = 1920,
    [ValidateRange(480,4320)][int]$Height = 1080,
    [ValidateRange(0.8,1.4)][double]$UIScale = 1.0,
    [ValidateRange(-1,3)][int]$Area = -1,
    [ValidateRange(0,10000)][int]$Variation = 0,
    # Owner review aid for RPT-20260915-08: capture thruster candidates without an editor session.
    [ValidateRange(-1,3)][int]$ThrusterShape = -1,
    [ValidateRange(0,40)][double]$ThrusterEmission = 0,
    [ValidateRange(0,10)][double]$ThrusterScale = 0,
    [ValidateRange(-1,16)][int]$ThrusterMaterial = -1,
    [switch]$ThrusterLayered,
    [ValidateRange(0,5)][double]$ThrusterTrailScale = 0,
    [ValidateRange(-400,400)][double]$ThrusterTrailHeight = 0,
    [ValidateRange(-400,400)][double]$ThrusterHeight = 0,
    [string[]]$ExtraArgs = @()
)
if ($OfflineSequence -and (-not $Sequence -or $QualityBenchmark -or $TailReview -or $OutpostReview -or $ApartmentWalk -or $WormholeReview -or $DirectorReview -or $WeaponReadability -or $MainMenu -or $UIRefresh -or $UIFollowup -or $UIFlightMenus -or $Packaged -or $ExtraArgs.Count -ne 0)) { throw 'OfflineSequence requires only the editor Wave1 Sequence scenario and accepts no other review modes or extra arguments.' }
if ($ApartmentWalk -and -not $OutpostReview) { throw 'Apartment walking is an opt-in part of the isolated OutpostReview scenario.' }
if (($QualityBenchmark -or $TailReview) -and ($OutpostReview -or $WormholeReview -or $DirectorReview -or $WeaponReadability -or $MainMenu -or $UIRefresh -or $UIFollowup -or $UIFlightMenus -or $Sequence)) { throw 'Benchmark and tail review are separate isolated scenarios.' }
if ($QualityBenchmark -and $TailReview) { throw 'The benchmark cannot capture tail review screenshots.' }
if ($QualityBenchmark -and ($Width -ne 1920 -or $Height -ne 1080 -or $Area -ne -1 -or $Variation -ne 0 -or $ExtraArgs.Count -ne 0)) { throw 'The comparison benchmark requires 1920x1080, ordinary region selection, and no extra arguments.' }
if ($QualityBenchmark -and ($ThrusterShape -ne -1 -or $ThrusterEmission -ne 0 -or $ThrusterScale -ne 0 -or $ThrusterMaterial -ne -1 -or $ThrusterLayered -or $ThrusterTrailScale -ne 0 -or $ThrusterTrailHeight -ne 0 -or $ThrusterHeight -ne 0)) { throw 'The comparison benchmark retains the default ship presentation.' }
if ($TailReview -and $Packaged) { throw 'Exact rendered tail-surface measurement requires the installed editor mesh source.' }
if ($OutpostReview -and ($WormholeReview -or $DirectorReview -or $WeaponReadability -or $MainMenu -or $UIRefresh -or $UIFollowup -or $Sequence)) { throw 'Outpost review is a separate isolated integration scenario.' }
if ($WormholeReview -and ($DirectorReview -or $WeaponReadability -or $MainMenu -or $UIRefresh -or $UIFollowup)) { throw 'Wormhole review is a separate seeded transition; only the optional sequence may be combined.' }
if ($DirectorReview -and ($WeaponReadability -or $MainMenu -or $UIRefresh -or $UIFollowup -or $Sequence)) { throw 'Director review uses ordinary Wave1 captures plus one close camera.' }
if ($UIFlightMenus -and $UIFollowup) { throw 'Flight pause and walking wardrobe are separate UI contexts.' }
if ($UIFollowup -or $UIFlightMenus) { $UIRefresh = $true }
if ($UIRefresh) { $MainMenu = $true }
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($WeaponReadability -and $Sequence) { throw 'Weapon readability captures its four named stages; do not combine it with the cruise sequence.' }
if ($MainMenu -and ($WeaponReadability -or $Sequence)) { throw 'Main-menu capture is separate from flight and weapon review.' }
$repo = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
function Assert-NoReparsePath([string]$Path) {
    $candidate = [IO.Path]::GetFullPath($Path)
    while ($candidate) {
        if (Test-Path -LiteralPath $candidate) {
            if (((Get-Item -LiteralPath $candidate -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing redirected capture path: $candidate"
            }
        }
        $parent = [IO.Directory]::GetParent($candidate)
        $candidate = if ($null -ne $parent) { $parent.FullName } else { $null }
    }
}
function Resolve-ArtifactRoot([string]$RepoRoot) {
    Assert-NoReparsePath $RepoRoot
    $artifactRoot = [IO.Path]::GetFullPath((Join-Path $RepoRoot 'Artifacts'))
    if (Test-Path -LiteralPath $artifactRoot) {
        $item = Get-Item -LiteralPath $artifactRoot -Force
        if (-not $item.PSIsContainer) { throw "Expected an artifact directory: $artifactRoot" }
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            $targets = @($item.Target)
            if ($item.LinkType -ne 'Junction' -or $targets.Count -ne 1 -or
                $targets[0] -notmatch '^[A-Za-z]:[\\/]') {
                throw "Expected one absolute directory target for the Artifacts junction: $artifactRoot"
            }
            # Resolve only the approved top-level storage junction. Source/save checks
            # stay on the checkout; nested capture and package redirects remain refused.
            $artifactRoot = [IO.Path]::GetFullPath($targets[0])
            if (-not (Test-Path -LiteralPath $artifactRoot -PathType Container)) {
                throw "Artifact junction target is missing: $artifactRoot"
            }
        }
    }
    Assert-NoReparsePath $artifactRoot
    return $artifactRoot
}
$artifactRoot = Resolve-ArtifactRoot $repo
function FileIdentity([string]$Path) {
    Assert-NoReparsePath $Path
    $item = Get-Item -LiteralPath $Path
    [ordered]@{ path = $item.FullName; bytes = $item.Length; sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
}
function ProductionSaves {
    foreach ($directory in @((Join-Path $repo 'Saved/SaveGames'),
        (Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'SpaceSurvival/Saved/SaveGames'))) {
        Assert-NoReparsePath $directory
        $exists = Test-Path -LiteralPath $directory -PathType Container
        $files = if ($exists) {
            @(Get-ChildItem -LiteralPath $directory -File -Force | Sort-Object Name | ForEach-Object { FileIdentity $_.FullName })
        } else { @() }
        [ordered]@{ directory = $directory; exists = $exists; files = @($files) }
    }
}
function SourceIdentity {
    $head = (& git -c "safe.directory=$repo" -C $repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read source HEAD.' }
    $dirty = @(& git -c "safe.directory=$repo" -C $repo status --porcelain)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read source worktree state.' }
    [ordered]@{ head = $head; dirtyEntries = $dirty;
        bindingLimit = 'HEAD and worktree state are recorded; a separate build/package receipt must bind source to the recorded compiled files. Artifacts identify Editor module or packaged executable/containers as applicable.' }
}
function PngIdentity([string]$Path) {
    $identity = FileIdentity $Path
    $stream = [IO.File]::OpenRead($Path)
    try {
        $header = [byte[]]::new(24)
        if ($stream.Read($header, 0, 24) -ne 24 -or
            [BitConverter]::ToString([byte[]]$header[0..7]).Replace('-', '') -cne '89504E470D0A1A0A' -or
            [Text.Encoding]::ASCII.GetString($header, 12, 4) -cne 'IHDR') { throw "Invalid PNG header: $Path" }
        $imageWidth = [uint32]$header[16] * 16777216 + [uint32]$header[17] * 65536 + [uint32]$header[18] * 256 + [uint32]$header[19]
        $imageHeight = [uint32]$header[20] * 16777216 + [uint32]$header[21] * 65536 + [uint32]$header[22] * 256 + [uint32]$header[23]
        if ($imageWidth -ne $Width -or $imageHeight -ne $Height) { throw "Unexpected screenshot size ${imageWidth}x${imageHeight}: $Path" }
        $identity.width = $imageWidth
        $identity.height = $imageHeight
        return $identity
    } finally { $stream.Dispose() }
}
function NativeArgument([string]$Value) {
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsafe native argument.' }
    '"' + $Value + '"'
}
$token = [Guid]::NewGuid().ToString('N')
$parentRoot = [IO.Path]::GetFullPath((Join-Path $artifactRoot 'EndgameSoak'))
$root = [IO.Path]::GetFullPath((Join-Path $parentRoot $token))
if ([IO.Directory]::GetParent($root).FullName -ine $parentRoot -or
    [IO.Path]::GetFileName($root) -cne $token -or $token -cnotmatch '^[0-9a-f]{32}$') { throw 'Unexpected fixture root.' }
Assert-NoReparsePath $root
if (Test-Path -LiteralPath $root) { throw 'Fresh fixture root already exists.' }
$userRoot = Join-Path $root 'User'
$savedRoot = Join-Path $userRoot 'Saved'
$slotsRoot = Join-Path $savedRoot 'SaveGames'
$pointerRoot = Join-Path $artifactRoot 'EnvironmentRefresh'
Assert-NoReparsePath $pointerRoot
$pointer = Join-Path $pointerRoot "$Label.json"
Assert-NoReparsePath $pointer
$exe = if ($Packaged) {
    [IO.Path]::GetFullPath((Join-Path $artifactRoot 'Windows/SpaceSurvival/Binaries/Win64/SpaceSurvival.exe'))
} else { [IO.Path]::GetFullPath((Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe')) }
function CaptureArtifacts {
    FileIdentity $exe
    if ($Packaged) {
        $paksRoot = Join-Path $artifactRoot 'Windows/SpaceSurvival/Content/Paks'
        Assert-NoReparsePath $paksRoot
        foreach ($extension in @('pak', 'utoc', 'ucas')) {
            if (-not (Test-Path -LiteralPath (Join-Path $paksRoot "SpaceSurvival-Windows.$extension") -PathType Leaf)) {
                throw "Required packaged container missing: $extension"
            }
        }
        Get-ChildItem -LiteralPath $paksRoot -File | Where-Object { $_.Extension -in @('.pak', '.utoc', '.ucas') } |
            Sort-Object Name | ForEach-Object { FileIdentity $_.FullName }
    } else { FileIdentity (Join-Path $repo 'Binaries/Win64/UnrealEditor-SpaceSurvival.dll') }
}
$artifactsBefore = @(CaptureArtifacts)
$sourceBefore = SourceIdentity
$productionBefore = @(ProductionSaves)
New-Item -ItemType Directory -Path $slotsRoot | Out-Null
New-Item -ItemType Directory -Path $pointerRoot -Force | Out-Null
$token | Set-Content -LiteralPath (Join-Path $root '.ss-endgame-soak') -Encoding utf8
$arguments = if ($Packaged) { @() } else { @((Join-Path $repo 'SpaceSurvival.uproject'), '-game') }
$scenario = if ($QualityBenchmark) { 'QualityBenchmark' } elseif ($TailReview) { 'TailReview' } elseif ($OutpostReview) { 'OutpostReview' } elseif ($WormholeReview) { 'WormholeReview' } elseif ($MainMenu) { 'MainMenu' } else { 'Wave1' }
$arguments += @('-SSWave10Soak', "-SSSoakScenario=$scenario",
    '-SaveToUserDir', "-UserDir=$userRoot", "-SSWave10SoakRoot=$root", '-RenderOffscreen',
    '-ForceRes', '-windowed', "-ResX=$Width", "-ResY=$Height", '-NoSplash', '-NoLiveCoding', '-csvGpuStats',
    '-nosound', '-unattended', "-abslog=$(Join-Path $root 'Rendered.log')")
if ($QualityBenchmark) { $arguments += '-SSQualityBenchmark' } else { $arguments += '-SSSoakVisuals' }
if ($TailReview -or $OfflineSequence) { $arguments += @('-UseFixedTimeStep', '-FPS=60') }
if ($OfflineSequence) { $arguments += '-SSOfflineSequence' }
if ($ApartmentWalk) { $arguments += '-SSSoakApartmentWalk' }
if ($UIRefresh) { $arguments += @('-SSUIRefreshReview', "-SSUIReviewScale=$($UIScale.ToString([Globalization.CultureInfo]::InvariantCulture))") }
if ($UIFollowup) { $arguments += '-SSUIFollowupReview' }
if ($UIFlightMenus) { $arguments += '-SSUIFlightMenus' }
if ($Sequence) { $arguments += '-SSSoakSequence' }
if ($WeaponReadability) { $arguments += '-SSWeaponReadability' }
if ($DirectorReview) { $arguments += '-SSDirectorReview' }
# Engine diagnostic messages include the green CSV counter. Keep the actual Canvas player HUD visible.
$execCmds = "DisableAllScreenMessages,csv.AlwaysShowFrameCount 0,ss.SpaceAreaPreview $Area,ss.SpaceAreaVariation $Variation"
if ($QualityBenchmark) { $execCmds += ",ss.DistantAsteroidCount $DistantCount,t.IdleWhenNotForeground 0,r.VSync 0,t.MaxFPS 0,r.ScreenPercentage 100" }
else { $execCmds += ',t.MaxFPS 30' } # Visual review shares the owner's GPU; timing evidence uses the uncapped benchmark.
if ($ThrusterShape -ge 0) { $execCmds += ",ss.ThrusterShape $ThrusterShape" }
if ($ThrusterEmission -gt 0) { $execCmds += ",ss.ThrusterEmission $ThrusterEmission" }
if ($ThrusterScale -gt 0) { $execCmds += ",ss.ThrusterScale $ThrusterScale" }
if ($ThrusterMaterial -ge 0) { $execCmds += ",ss.ThrusterMaterial $ThrusterMaterial" }
if ($ThrusterLayered) { $execCmds += ",ss.ThrusterLayered 1" }
if ($ThrusterTrailScale -gt 0) { $execCmds += ",ss.ThrusterTrailScale $ThrusterTrailScale" }
if ($ThrusterTrailHeight -ne 0) { $execCmds += ",ss.ThrusterTrailHeight $ThrusterTrailHeight" }
if ($ThrusterHeight -ne 0) { $execCmds += ",ss.ThrusterHeight $ThrusterHeight" }
$arguments += "-ExecCmds=$execCmds"
$arguments += $ExtraArgs
$evidenceType = if ($QualityBenchmark) { 'ENVIRONMENT_FLIGHT_COST_BENCHMARK' } elseif ($OfflineSequence) { 'OFFLINE_WAVE1_VISUAL_REVIEW_NOT_PERFORMANCE' } elseif ($TailReview) { 'SQUIRREL_JUMP_RENDERED_REVIEW' } elseif ($OutpostReview) { 'OUTPOST_SCRIPTED_INTEGRATION_REVIEW' } elseif ($WormholeReview) { 'WORMHOLE_SEEDED_VISUAL_REVIEW_NORMAL_STATS' } elseif ($UIRefresh) { 'UI_REFRESH_RENDERED_REVIEW' } elseif ($MainMenu) { 'TITLE_MENU_RENDERED_REVIEW' } elseif ($WeaponReadability) { 'WEAPON_READABILITY_SCRIPTED_NORMAL_STATS' } else { 'WAVE1_VISUAL_ONLY_SCRIPTED_NORMAL_STATS' }
$timeoutSeconds = if ($OfflineSequence) { 600 } elseif ($OutpostReview) { 300 } elseif ($QualityBenchmark -or $TailReview) { 240 } else { 120 }
$metadata = [ordered]@{
    evidenceType = $evidenceType; status = 'starting'; success = $false
    root = $root; label = $Label; token = $token; pid = $null; processStartUtc = $null; processExit = $null
    startedUtc = [DateTime]::UtcNow.ToString('o'); finishedUtc = $null; timeoutSeconds = $timeoutSeconds
    mode = $(if ($Packaged) { 'WindowsDevelopmentPackage' } else { 'UncookedEditorGame' })
    sourceBefore = $sourceBefore; sourceAfter = $null; artifacts = $artifactsBefore; artifactsUnchanged = $false
    productionBefore = $productionBefore; productionAfter = $null; productionPreserved = $false
    noTestSaveSlotsWritten = $false; requestedResolution = @($Width, $Height); requestedUIScale = $UIScale; images = @(); fixture = $null
    suitableForPerformanceFinding = $false
    qualityBenchmarkRequested = [bool]$QualityBenchmark
    benchmarkDistantCount = $(if ($QualityBenchmark) { $DistantCount } else { $null })
    tailReviewRequested = [bool]$TailReview
    sequenceRequested = [bool]$Sequence
    offlineSequenceRequested = [bool]$OfflineSequence
    requestedSimulationClock = $(if ($TailReview -or $OfflineSequence) { 'Engine UseFixedTimeStep/FPS60; 1/60 simulation second per rendered frame, independent of wall time.' } else { 'Ordinary variable timestep; fixed timestep and time dilation are forbidden.' })
    directorReviewRequested = [bool]$DirectorReview
    wormholeReviewRequested = [bool]$WormholeReview
    outpostReviewRequested = [bool]$OutpostReview
    apartmentWalkRequested = [bool]$ApartmentWalk
    weaponReadabilityRequested = [bool]$WeaponReadability
    mainMenuRequested = [bool]$MainMenu
    areaPreview = $Area; areaVariation = $Variation
    limits = $(if ($QualityBenchmark) {
        'Environment/flight cost only: fixed seed, 1920x1080 High/100%, uncapped offscreen rendering, normal starter stats and damage, Director disabled and wave phase age held. At least 15s quiet warmup plus 60s ordinary physics cruise/turn/boost via scripted SetFlightInput. Swept-hull route probes included in CPU cost; collisions/damage invalidate comparison. No PNG readbacks, immunity, refills, natural combat, audio, physical input or packaged performance acceptance.'
    } elseif ($OfflineSequence) {
        'OFFLINE_WAVE1_VISUAL_REVIEW_NOT_PERFORMANCE. Existing 29-second simulated Wave1 trajectory, normal stats/collision/damage and scripted cruise/turn/boost/brake. Explicit engine UseFixedTimeStep/FPS60, actual 1/60-second ticks and time dilation 1 required. Minimum40/maximum80 sequence images and eight viewport frames between all PNG requests; no interpolated images. Simulation time is independent of wall time; screenshot readbacks and the offline clock invalidate performance and real-time smoothness claims. No physical input, natural balance, audio or complete run acceptance.'
    } elseif ($TailReview) {
        'Fresh isolated home; actual possessed Squirrel Jump/StopJumping and Move, fixed side camera, two jumps including landing into movement, sampled real floor/tail envelope and exact run/account preservation. No physical input, performance or natural gameplay acceptance.'
    } elseif ($OutpostReview) {
        'Protected fresh home profile; scripted walker placements at real services, normal Interact panels, 27 sampled apartment-route floor and upper-capsule checks excluding doors, authored cameras, real StartFreeFlight takeoff/powered movement and EndFreeFlight return. Exact account/run roundtrip, then isolated seeded Wave5 Station with real EnterStation, supported walker and Upgrades/Repair/Contracts/Save panel openings; no save/purchase actions. No physical input, actual apartment traversal, landing approach, complete run or FPS claim.'
    } elseif ($WormholeReview) {
        'Seeded Wave5 Flight with 2 seconds remaining after asset warmup; fresh normal starter stats, no durability increase or invulnerability. Real Session/GameMode transition through the normal 8-second wormhole and 3 seconds of climax exit. Four normal chase-camera stages plus optional 8fps-target readbacks with actual timestamps. Ordinary SetFlightInput steering/brake attempts; no physical input, ten-wave journey, cold-first-transition, natural balance, audio or FPS acceptance. PNG identity and runtime receipt guards do not establish visual quality.'
    } elseif ($DirectorReview) {
        'Normal-stat scripted flight with a final transient camera for the runtime villain. No physical input, natural balance or FPS acceptance. Loaded tuning, actual rider mesh and animation are recorded.'
    } elseif ($UIFlightMenus) {
        'Actual StartFreeFlight, normal takeoff and scripted powered departure followed by four paused Canvas menus over the possessed ship camera. Exact paused account/run/settings conservation; isolated fresh profile and production-save hashes. No physical controller, natural play, balance or FPS acceptance.'
    } elseif ($UIFollowup) {
        'Hidden six-frame changed-UI batch: aligned audio/controls sliders, wardrobe top/end/drag, actual walking HUD with crew/services radar. Synthetic menu navigation and pointer drag; read-only account/run guards. No physical input, natural gameplay or performance acceptance.'
    } elseif ($UIRefresh) {
        'Hidden seven-screen native UI render with synthetic focus and read-only HUD sample values. Menu centers map to native actions; run/account/settings are preserved. No physical input, natural gameplay, FPS or save-operation acceptance.'
    } elseif ($MainMenu) {
        'Hidden startup title with actual imported Figma textures; synthetic no-selection/NewGame/Settings focus. Real rendered button centers must map to existing actions. No StartRun, menu activation, OS pointer movement, physical input, FPS or save operation.'
    } elseif ($WeaponReadability) {
        'Hidden rendered game; normal-stat straight powered flight and both weapons fired through the actual ship/camera. One normal-health Pursuer target at a time with AI/director paused. Four shot/hit frames require real hit feedback. PNG identity is verified, not visual quality. No unlock, FPS, physical input, natural balance, audio or complete run claim.'
    } else {
        'Hidden rendered game; 29 seconds of scripted normal-stat cruise/turn/boost/brake and no fire. PNG headers/dimensions/hashes are verified, not visual quality. No FPS, physical input, natural balance or complete run claim.'
    })
    failures = @()
}
$metadataPath = Join-Path $root 'capture.json'
$metadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $metadataPath -Encoding utf8
$process = $null
$ownedStart = $null
$failures = [Collections.Generic.List[string]]::new()
$captureValid = $false
try {
    $native = ($arguments | ForEach-Object { NativeArgument $_ }) -join ' '
    $process = Start-Process -FilePath $exe -WorkingDirectory $repo -ArgumentList $native -WindowStyle Hidden -PassThru
    $ownedStart = $process.StartTime.ToUniversalTime()
    $metadata.pid = $process.Id
    $metadata.processStartUtc = $ownedStart.ToString('o')
    $metadata.status = 'running'
    $metadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $metadataPath -Encoding utf8
    @{ root = $root; pid = $process.Id; label = $Label; metadata = $metadataPath; status = 'running' } |
        ConvertTo-Json | Set-Content -LiteralPath $pointer -Encoding utf8
    Write-Output "Owned hidden $scenario capture $($process.Id): $root"
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while (-not $process.WaitForExit(1000)) {
        if ($timer.Elapsed.TotalSeconds -ge $timeoutSeconds) { throw "Owned visual capture exceeded its $timeoutSeconds-second timeout." }
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0) { throw "Visual capture exited $($process.ExitCode)." }
    $fixturePath = Join-Path $root 'fixture.json'
    Assert-NoReparsePath $fixturePath
    $fixture = Get-Content -LiteralPath $fixturePath -Raw | ConvertFrom-Json
    $metadata.fixture = $fixture
    if (-not $fixture.success -or -not $fixture.noSaveSlotsWritten -or
        $fixture.evidenceType -cne $evidenceType -or $fixture.scenario -cne $scenario -or
        $fixture.token -cne $token -or $fixture.processId -ne $process.Id -or (-not $QualityBenchmark -and -not $TailReview -and -not $MainMenu -and -not $WormholeReview -and -not $OutpostReview -and -not $fixture.sawWave1) -or
        [IO.Path]::GetFullPath($fixture.savedDir).TrimEnd('\', '/') -ine $savedRoot.TrimEnd('\', '/') -or
        [IO.Path]::GetFullPath($fixture.csv) -ine (Join-Path $root 'Endgame.csv')) { throw 'Fixture identity, visibility or save isolation receipt failed.' }
    if ($QualityBenchmark) {
        if ($fixture.visualCaptureEnabled -or $fixture.offscreenVisualOnly -or -not $fixture.suitableForPerformanceFinding -or
            -not $fixture.qualityBenchmark -or $fixture.benchmarkWarmupSeconds -lt 15 -or $fixture.benchmarkMeasuredSeconds -lt 60 -or
            $fixture.benchmarkContactCount -ne 0 -or $fixture.benchmarkDistantAsteroidCount -ne $DistantCount -or
            @(Get-ChildItem -LiteralPath $root -Recurse -Filter '*.png' -File).Count -ne 0) { throw 'Benchmark timing, contact or no-screenshot contract failed.' }
        $metadata.suitableForPerformanceFinding = $true
    } elseif (-not $fixture.visualCaptureEnabled -or -not $fixture.offscreenVisualOnly -or $fixture.suitableForPerformanceFinding) {
        throw 'Visual capture identity was replaced by an unintended benchmark mode.'
    }
    if ($OfflineSequence -and (-not $fixture.offlineSequence -or -not $fixture.useFixedTimeStep -or
        [Math]::Abs($fixture.fixedDeltaSeconds - 1.0 / 60.0) -gt 0.00000001 -or
        [Math]::Abs($fixture.effectiveTimeDilation - 1.0) -gt 0.000001 -or
        $fixture.flightSimulationSeconds -lt 29 -or $fixture.fixtureFrames -lt 1740)) {
        throw 'Offline sequence did not retain its explicit 60 Hz simulation clock and complete 29-second flight.'
    }
    $allNames = @($fixture.visualRequests | ForEach-Object { $_.name })
    $names = @($allNames | Where-Object { $_ -notlike 'Sequence_*' })
    $expectedNames = if ($OutpostReview) { 'OutpostPad,OutpostServices,OutpostApartment,OutpostFlight,OutpostReturn,OutpostPitStop' } elseif ($WormholeReview) { 'Entrance,Transit,DeepTransit,Exit' } elseif ($UIFlightMenus) { 'UIPauseFlight,UIGraphicsFlight,UIAudioFlight,UIControlsFlight' } elseif ($UIFollowup) { 'UIAudioAligned,UIControlsAligned,UIWardrobeTop,UIWardrobeBottom,UIWardrobeDragTop,UIWalking' } elseif ($UIRefresh) { 'UIGeneral,UIGraphics,UIAudio,UIControls,UIPause,UIWardrobe,UIFlight' } elseif ($MainMenu) { 'MainMenuNormal,MainMenuNewGame,MainMenuSettings' } elseif ($WeaponReadability) { 'RapidShot,RapidHit,CannonShot,CannonHit' } elseif ($DirectorReview) { 'Cruise,Turn,Boost,Brake,VillainCloseup' } else { 'Cruise,Turn,Boost,Brake' }
    if ($QualityBenchmark) { $expectedNames = '' }
    if ($ApartmentWalk) { $expectedNames = 'OutpostPad,OutpostServices,ApartmentWalkIn,ApartmentWalkBack,OutpostApartment,OutpostFlight,OutpostReturn,OutpostPitStop' }
    if ($TailReview) {
        if (-not $fixture.tailReviewComplete -or $fixture.tailJumpCount -ne 2 -or $fixture.tailOffDeckRescues -ne 0 -or $names.Count -lt 45) { throw 'Tail review did not complete two real jumps and the required rendered sequence.' }
        $expectedNames = ((0..($names.Count - 1)) | ForEach-Object { 'Tail_{0:d3}' -f $_ }) -join ','
    }
    if (($names -join ',') -cne $expectedNames) { throw 'Fixture did not capture the required named stages in order.' }
    if ($UIRefresh -and (-not $fixture.uiRefreshReview -or -not $fixture.mainMenuStatePreserved)) { throw 'UI frame state checks failed.' }
    if ($UIRefresh) {
        foreach ($row in $fixture.visualRequests) {
            if ($row.viewportWidth -ne $Width -or $row.viewportHeight -ne $Height -or
                [Math]::Abs($row.uiScale - $UIScale) -gt 0.001) { throw 'UI frame resolution or scale did not match the request.' }
            if ($UIFlightMenus -and (-not $row.actualFlightCamera -or -not $row.worldPaused)) {
                throw 'Flight pause frame did not retain the actual ship camera and paused world.'
            }
        }
    }
    if ($MainMenu -and -not $UIRefresh) {
        if (-not $fixture.mainMenuReview -or -not $fixture.mainMenuStatePreserved -or $fixture.sawWave1) { throw 'Title-only state preservation failed.' }
        $expectedFocus = @(-1, 1, 2)
        for ($i = 0; $i -lt 3; ++$i) {
            $row = $fixture.visualRequests[$i]
            if (-not $row.actualFigmaTitleDrawn -or $row.selectedEntry -ne $expectedFocus[$i] -or
                $row.renderedFocusEntry -ne $expectedFocus[$i] -or @($row.titleRows).Count -ne 4) {
                throw 'Title frame used fallback art or an unintended focus state.'
            }
            if (($row.titleRows.action -join ',') -cne '2,4,5,7' -or $row.titleRows[0].enabled) { throw 'Title frame lost existing actions or disabled Continue.' }
            for ($index = 0; $index -lt 4; ++$index) {
                $button = $row.titleRows[$index]
                if ($button.index -ne $index -or $button.centerHitIndex -ne $index -or
                    $button.minX -lt 0 -or $button.minY -lt 0 -or $button.maxX -gt $Width -or $button.maxY -gt $Height -or
                    $button.maxX -le $button.minX -or $button.maxY -le $button.minY) { throw 'Rendered title button has invalid bounds or hit mapping.' }
            }
        }
    }
    if ($OutpostReview) {
        if ($ApartmentWalk -and (-not $fixture.apartmentWalkComplete -or $fixture.apartmentWalkPasses -ne 2 -or
            $fixture.apartmentOffDeckRescues -ne 0 -or $fixture.apartmentSetupPlacements -ne 1 -or
            $fixture.apartmentDoorClosures -ne 1)) { throw 'Actual apartment out/back movement, door closure or rescue guards failed.' }
        if (-not $fixture.outpostReviewComplete -or -not $fixture.outpostFreeFlightDeparture -or
            -not $fixture.outpostFreeFlightReturn -or $fixture.outpostServicesChecked -ne 4 -or
            $fixture.outpostFloorAndClearanceSamples -ne 27 -or -not $fixture.outpostSeededPitStopSupported -or
            $fixture.outpostPitStopServicesChecked -ne 4) {
            throw 'Runtime station, home/pit-stop services, apartment probes or free-flight roundtrip did not pass.'
        }
        $pitStop = @($fixture.visualRequests | Where-Object { $_.name -ceq 'OutpostPitStop' })[0]
        if ($pitStop.wave -ne 5 -or -not $pitStop.activeRun -or -not $pitStop.stationPhase -or $pitStop.pitStopPanelsOpened -ne 4) {
            throw 'Pit-stop frame did not retain seeded active Wave5 Station with four real service panels opened.'
        }
        foreach ($row in $fixture.visualRequests) {
            if (-not $row.runtimeOutpost) { throw 'Outpost capture used the legacy station or lost the runtime outpost.' }
        }
    }
    if ($WormholeReview) {
        if (-not $fixture.wormholeReview -or -not $fixture.wormholeSeededFlight -or
            -not $fixture.sawWave5 -or -not $fixture.sawWormhole -or -not $fixture.sawClimax -or
            $fixture.sawWave1 -or $fixture.wormholeRenderingReadyAtSeconds -lt 3 -or
            $fixture.startingMaxHull -le 0 -or $fixture.startingMaxShield -le 0) {
            throw 'Wormhole fixture did not record the actual seeded normal-stat transition and rendering warmup.'
        }
        $stages = @($fixture.visualRequests | Where-Object { $_.name -notlike 'Sequence_*' })
        $earliest = @(.25, 2.0, 5.5, 2.5)
        $latest = @(1.5, 3.5, 7.7, 4.0)
        for ($i = 0; $i -lt 4; ++$i) {
            $row = $stages[$i]
            if ($row.wave -ne 5 -or -not $row.normalChaseCamera -or -not $row.tunnelMaterialLoaded -or
                $row.phaseSeconds -lt $earliest[$i] -or $row.phaseSeconds -gt $latest[$i] -or
                $row.actualCameraFov -le 0 -or $row.shipSpeedCmPerSecond -le 0 -or $row.hullHealth -le 0) {
                throw "Wormhole stage $($row.name) lost its normal camera, loaded material or bounded phase window."
            }
            if ($i -lt 3) {
                if ($row.phaseName -cne 'Wormhole' -or -not $row.shipInWormholeTransit -or
                    -not $row.tunnelVisible -or -not $row.tunnelMaterialMatchesExpected -or
                    -not $row.scriptedBrake -or [Math]::Abs($row.phaseDuration - 8) -gt .001) {
                    throw "Wormhole stage $($row.name) lacks the real visible tunnel or locked-transit input attempt."
                }
            } elseif ($row.phaseName -cne 'Climax' -or $row.shipInWormholeTransit -or $row.scriptedBrake -or
                [Math]::Abs($row.phaseDuration - 40) -gt .001) {
                throw 'Wormhole exit did not restore ordinary flight in the real climax phase.'
            }
        }
        if ($Sequence -and ($fixture.sequenceTargetFps -ne 8 -or $fixture.sequenceFrames -lt 16)) {
            throw 'Wormhole sequence did not record its target interval and actual frame count.'
        }
    }
    if ($WeaponReadability) {
        if (-not $fixture.weaponReadabilityReview) { throw 'Fixture did not confirm the requested weapon review mode.' }
        if ($fixture.weaponUncapturedWarmupShots -ne 2 -or $fixture.weaponRenderingReadyAtSeconds -lt 0) { throw 'Weapon rendering warmup was not completed.' }
        foreach ($row in $fixture.visualRequests) {
            if ($row.uncapturedWarmupShots -ne 2 -or $row.requestStageSeconds -lt $fixture.weaponRenderingReadyAtSeconds) { throw 'Weapon frame preceded the recorded rendering warmup.' }
        }
        foreach ($row in @($fixture.visualRequests | Where-Object { $_.name -in @('RapidHit', 'CannonHit') })) {
            if ($row.confirmedHitFeedbackSeconds -le 0) { throw 'Weapon hit frame has no actual hit confirmation.' }
        }
        $rapid = @($fixture.visualRequests | Where-Object { $_.name -ceq 'RapidShot' })[0]
        $cannon = @($fixture.visualRequests | Where-Object { $_.name -ceq 'CannonShot' })[0]
        if ($rapid.liveLaserPulses -le 0 -or $cannon.liveProjectiles -le 0) { throw 'Weapon shot frame has no corresponding live visual.' }
    }
    $minimumSequenceFrames = if ($WormholeReview) { 16 } else { 40 }
    if ($Sequence -and @($allNames | Where-Object { $_ -like 'Sequence_*' }).Count -lt $minimumSequenceFrames) { throw 'Dense sequence did not produce enough real frames.' }
    if ($Sequence -and -not $WormholeReview) {
        if ($fixture.sequenceFrames -gt 80) { throw 'Wave1 sequence exceeded its 80-image cap.' }
        if ($fixture.sequenceMinimumRenderFrames -ne 8 -or $fixture.sequenceObservedMinimumRenderFrames -lt 8) { throw 'Wave1 sequence did not retain eight viewport frames between screenshot requests.' }
        for ($index = 1; $index -lt $fixture.visualRequests.Count; ++$index) {
            $spacing = $fixture.visualRequests[$index].requestFrame - $fixture.visualRequests[$index - 1].requestFrame
            if ($spacing -lt 8 -or $fixture.visualRequests[$index].renderFramesSincePreviousScreenshot -ne $spacing) { throw 'Wave1 screenshot spacing metadata disagrees with its actual request frame counter.' }
        }
    }
    if ($scenario -ceq 'Wave1' -and -not $WeaponReadability) {
        $boost = @($fixture.visualRequests | Where-Object { $_.name -ceq 'Boost' })[0]
        if (-not $boost.scriptedBoostRequested -or -not $boost.actualBoosting -or
            $boost.requestStageSeconds -lt 15.5 -or $boost.requestStageSeconds -ge 21) {
            throw 'The named Boost image did not record active ordinary boost during its scripted input interval.'
        }
    }
    $metadata.images = @($allNames | ForEach-Object { PngIdentity (Join-Path $root "$_.png") })
    $captureValid = $true
} catch {
    $failures.Add($_.Exception.Message)
} finally {
    if ($null -ne $process -and -not $process.HasExited) {
        try {
            $current = Get-Process -Id $process.Id -ErrorAction Stop
            if ($null -eq $ownedStart -or $current.StartTime.ToUniversalTime() -ne $ownedStart -or
                [IO.Path]::GetFullPath($current.Path) -ine $exe) { throw 'Refusing to stop a process whose ownership identity changed.' }
            Stop-Process -InputObject $process -Force
            if (-not $process.WaitForExit(10000)) { throw 'Owned timed-out capture did not exit.' }
        } catch { $failures.Add($_.Exception.Message) }
    }
    if ($null -ne $process -and $process.HasExited) { $metadata.processExit = $process.ExitCode }
    try {
        $metadata.productionAfter = @(ProductionSaves)
        $metadata.productionPreserved = ($productionBefore | ConvertTo-Json -Depth 12 -Compress) -ceq
            ($metadata.productionAfter | ConvertTo-Json -Depth 12 -Compress)
        if (-not $metadata.productionPreserved) { $failures.Add('Production save hashes changed during capture.') }
    } catch { $failures.Add($_.Exception.Message) }
    try {
        $metadata.sourceAfter = SourceIdentity
        $artifactsAfter = @(CaptureArtifacts)
        $metadata.artifactsUnchanged = ($artifactsBefore | ConvertTo-Json -Depth 8 -Compress) -ceq
            ($artifactsAfter | ConvertTo-Json -Depth 8 -Compress)
        if (-not $metadata.artifactsUnchanged) { $failures.Add('Compiled executable, module or packaged containers changed during capture.') }
        if ($metadata.sourceAfter.head -cne $sourceBefore.head) { $failures.Add('Source HEAD changed during capture.') }
    } catch { $failures.Add($_.Exception.Message) }
    try {
        Assert-NoReparsePath $slotsRoot
        $metadata.noTestSaveSlotsWritten = @(Get-ChildItem -LiteralPath $slotsRoot -File -Force).Count -eq 0
        if (-not $metadata.noTestSaveSlotsWritten) { $failures.Add('Isolated fixture wrote save slots.') }
    } catch { $failures.Add($_.Exception.Message) }
    $metadata.success = $captureValid -and $failures.Count -eq 0
    $metadata.status = if (-not $metadata.success) { 'failed' } elseif ($QualityBenchmark) { 'validated_environment_benchmark' } else { 'validated_visual_capture' }
    $metadata.finishedUtc = [DateTime]::UtcNow.ToString('o')
    $metadata.failures = @($failures.ToArray())
    $metadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $metadataPath -Encoding utf8
    @{ root = $root; pid = $metadata.pid; label = $Label; metadata = $metadataPath; status = $metadata.status; success = $metadata.success } |
        ConvertTo-Json | Set-Content -LiteralPath $pointer -Encoding utf8
    Write-Output "Capture receipt: $metadataPath; success=$($metadata.success)"
}
if (-not $metadata.success) { throw "Space-look capture failed: $($failures -join '; ')" }
