<#
Capture the normal-stat Wave1 visual fixture in a hidden editor game process.
No build, package, publication or save operation is performed. Screenshots are not FPS evidence.
#>
param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')][string]$Label = 'CombinedLook',
    [string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8',
    [switch]$Packaged
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
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
            [Convert]::ToHexString($header[0..7]) -cne '89504E470D0A1A0A' -or
            [Text.Encoding]::ASCII.GetString($header, 12, 4) -cne 'IHDR') { throw "Invalid PNG header: $Path" }
        $width = [uint32]$header[16] * 16777216 + [uint32]$header[17] * 65536 + [uint32]$header[18] * 256 + [uint32]$header[19]
        $height = [uint32]$header[20] * 16777216 + [uint32]$header[21] * 65536 + [uint32]$header[22] * 256 + [uint32]$header[23]
        if ($width -ne 1920 -or $height -ne 1080) { throw "Unexpected screenshot size ${width}x${height}: $Path" }
        $identity.width = $width
        $identity.height = $height
        return $identity
    } finally { $stream.Dispose() }
}
function NativeArgument([string]$Value) {
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsafe native argument.' }
    '"' + $Value + '"'
}
$token = [Guid]::NewGuid().ToString('N')
$parentRoot = [IO.Path]::GetFullPath((Join-Path $repo 'Artifacts/EndgameSoak'))
$root = [IO.Path]::GetFullPath((Join-Path $parentRoot $token))
if ([IO.Directory]::GetParent($root).FullName -ine $parentRoot -or
    [IO.Path]::GetFileName($root) -cne $token -or $token -cnotmatch '^[0-9a-f]{32}$') { throw 'Unexpected fixture root.' }
Assert-NoReparsePath $root
if (Test-Path -LiteralPath $root) { throw 'Fresh fixture root already exists.' }
$userRoot = Join-Path $root 'User'
$savedRoot = Join-Path $userRoot 'Saved'
$slotsRoot = Join-Path $savedRoot 'SaveGames'
$pointerRoot = Join-Path $repo 'Artifacts/EnvironmentRefresh'
Assert-NoReparsePath $pointerRoot
$pointer = Join-Path $pointerRoot "$Label.json"
Assert-NoReparsePath $pointer
$exe = if ($Packaged) {
    [IO.Path]::GetFullPath((Join-Path $repo 'Artifacts/Windows/SpaceSurvival/Binaries/Win64/SpaceSurvival.exe'))
} else { [IO.Path]::GetFullPath((Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe')) }
function CaptureArtifacts {
    FileIdentity $exe
    if ($Packaged) {
        $paksRoot = Join-Path $repo 'Artifacts/Windows/SpaceSurvival/Content/Paks'
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
$arguments += @('-SSWave10Soak', '-SSSoakScenario=Wave1',
    '-SSSoakVisuals', '-SaveToUserDir', "-UserDir=$userRoot", "-SSWave10SoakRoot=$root", '-RenderOffscreen',
    '-ForceRes', '-windowed', '-ResX=1920', '-ResY=1080', '-NoSplash', '-NoLiveCoding', '-csvGpuStats',
    '-nosound', '-unattended', "-abslog=$(Join-Path $root 'Rendered.log')")
$metadata = [ordered]@{
    evidenceType = 'WAVE1_VISUAL_ONLY_SCRIPTED_NORMAL_STATS'; status = 'starting'; success = $false
    root = $root; label = $Label; token = $token; pid = $null; processStartUtc = $null; processExit = $null
    startedUtc = [DateTime]::UtcNow.ToString('o'); finishedUtc = $null; timeoutSeconds = 120
    mode = $(if ($Packaged) { 'WindowsDevelopmentPackage' } else { 'UncookedEditorGame' })
    sourceBefore = $sourceBefore; sourceAfter = $null; artifacts = $artifactsBefore; artifactsUnchanged = $false
    productionBefore = $productionBefore; productionAfter = $null; productionPreserved = $false
    noTestSaveSlotsWritten = $false; requestedResolution = @(1920, 1080); images = @(); fixture = $null
    suitableForPerformanceFinding = $false
    limits = 'Hidden rendered game; 29 seconds of scripted normal-stat cruise/turn/boost/brake and no fire. PNG headers/dimensions/hashes are verified, not visual quality. No FPS, physical input, natural balance or complete run claim.'
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
    Write-Output "Owned hidden Wave1 capture $($process.Id): $root"
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while (-not $process.WaitForExit(1000)) {
        if ($timer.Elapsed.TotalSeconds -ge 120) { throw 'Owned visual capture exceeded its 120-second timeout.' }
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0) { throw "Visual capture exited $($process.ExitCode)." }
    $fixturePath = Join-Path $root 'fixture.json'
    Assert-NoReparsePath $fixturePath
    $fixture = Get-Content -LiteralPath $fixturePath -Raw | ConvertFrom-Json
    $metadata.fixture = $fixture
    if (-not $fixture.success -or -not $fixture.noSaveSlotsWritten -or
        $fixture.evidenceType -cne 'WAVE1_VISUAL_ONLY_SCRIPTED_NORMAL_STATS' -or $fixture.scenario -cne 'Wave1' -or
        $fixture.token -cne $token -or $fixture.processId -ne $process.Id -or -not $fixture.sawWave1 -or
        -not $fixture.visualCaptureEnabled -or -not $fixture.offscreenVisualOnly -or $fixture.suitableForPerformanceFinding -or
        [IO.Path]::GetFullPath($fixture.savedDir).TrimEnd('\', '/') -ine $savedRoot.TrimEnd('\', '/') -or
        [IO.Path]::GetFullPath($fixture.csv) -ine (Join-Path $root 'Endgame.csv')) { throw 'Fixture identity, visibility or save isolation receipt failed.' }
    $names = @($fixture.visualRequests | ForEach-Object { $_.name })
    if (($names -join ',') -cne 'Cruise,Turn,Boost,Brake') { throw 'Fixture did not capture the four required stages in order.' }
    $metadata.images = @($names | ForEach-Object { PngIdentity (Join-Path $root "$_.png") })
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
    $metadata.status = if ($metadata.success) { 'validated_visual_capture' } else { 'failed' }
    $metadata.finishedUtc = [DateTime]::UtcNow.ToString('o')
    $metadata.failures = @($failures.ToArray())
    $metadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $metadataPath -Encoding utf8
    @{ root = $root; pid = $metadata.pid; label = $Label; metadata = $metadataPath; status = $metadata.status; success = $metadata.success } |
        ConvertTo-Json | Set-Content -LiteralPath $pointer -Encoding utf8
    Write-Output "Capture receipt: $metadataPath; success=$($metadata.success)"
}
if (-not $metadata.success) { throw "Space-look capture failed: $($failures -join '; ')" }