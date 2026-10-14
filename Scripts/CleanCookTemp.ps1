param(
    [string[]]$ProjectRoot = @((Split-Path $PSScriptRoot -Parent)),
    [ValidateRange(24, 8760)][int]$MinimumAgeHours = 48,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'

# Only disposable cook/stage outputs. Never widen this to Saved or Intermediate.
$relativeTargets = @('Saved\Cooked', 'Saved\StagedBuilds', 'Intermediate\Staging')
$receiptRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.agent\local\CookCleanup'
$cutoff = [DateTime]::UtcNow.AddHours(-$MinimumAgeHours)

function Assert-NoCook {
    $running = @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(UnrealEditor|UnrealPak|AutomationTool|dotnet)' -and
        $_.CommandLine -match '(?i)BuildCookRun|(?:^|\s)-run=cook|AutomationTool|UnrealPak'
    })
    if ($running.Count) { throw 'A cook/package process is running; cleanup refused.' }
}

function Assert-PlainPath([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Reparse path refused: $($item.FullName)"
        }
        $item = $item.Parent
    }
}

function Get-OutputFiles([string]$Path) {
    $pending = [Collections.Generic.Stack[string]]::new()
    $pending.Push($Path)
    while ($pending.Count) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Linked cook output refused: $($item.FullName)"
            }
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
            else { $item }
        }
    }
}

Assert-NoCook
$plan = @()
foreach ($requestedRoot in $ProjectRoot) {
    $root = (Resolve-Path -LiteralPath $requestedRoot).ProviderPath.TrimEnd('\')
    if (-not (Test-Path -LiteralPath (Join-Path $root 'SpaceSurvival.uproject') -PathType Leaf)) {
        throw "Not a SpaceSurvival project: $root"
    }
    Assert-PlainPath $root
    $tracked = @(git -C $root ls-files -- Saved/Cooked Saved/StagedBuilds Intermediate/Staging)
    if ($LASTEXITCODE -ne 0 -or $tracked.Count) { throw "Tracked outputs or failed Git check: $root" }
    foreach ($relative in $relativeTargets) {
        $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
        if (-not $target.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Output escaped the explicitly selected project.'
        }
        if (-not (Test-Path -LiteralPath $target)) { continue }
        Assert-PlainPath $target
        $files = @(Get-OutputFiles $target | Sort-Object FullName)
        if (@($files | Where-Object { $_.Extension -in '.sav', '.blend', '.fbx', '.glb' }).Count) {
            throw "Save/source file in cook output; manual review required: $target"
        }
        $newest = (Get-Item -LiteralPath $target).LastWriteTimeUtc
        foreach ($file in $files) {
            if ($file.LastWriteTimeUtc -gt $newest) { $newest = $file.LastWriteTimeUtc }
        }
        $plan += [pscustomobject]@{
            Root = $root; Relative = $relative; Path = $target
            Bytes = [long](($files | Measure-Object Length -Sum).Sum)
            FileCount = $files.Count; NewestUtc = $newest
            Eligible = ($newest -lt $cutoff)
            Files = @($files | ForEach-Object {
                [pscustomobject]@{ Path = $_.FullName; Bytes = $_.Length; ModifiedUtc = $_.LastWriteTimeUtc }
            })
        }
    }
}
New-Item -ItemType Directory -Path $receiptRoot -Force | Out-Null
Assert-PlainPath $receiptRoot
$receipt = Join-Path $receiptRoot (([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')) + '.json')
$result = [ordered]@{
    TimeUtc = [DateTime]::UtcNow.ToString('o'); Applied = [bool]$Apply
    MinimumAgeHours = $MinimumAgeHours; RemovedBytes = [long]0
    Plan = $plan; Removed = @(); Complete = $false
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receipt -Encoding utf8

if ($Apply) {
    # Recheck every eligible path before any removal, then immediately before it.
    foreach ($entry in @($plan | Where-Object Eligible)) {
        Assert-PlainPath $entry.Path
        $current = @(Get-OutputFiles $entry.Path | Sort-Object FullName)
        $before = $entry.Files | ConvertTo-Json -Depth 4 -Compress
        $now = @($current | ForEach-Object {
            [pscustomobject]@{ Path = $_.FullName; Bytes = $_.Length; ModifiedUtc = $_.LastWriteTimeUtc }
        }) | ConvertTo-Json -Depth 4 -Compress
        if ($before -ne $now -or (Get-Item -LiteralPath $entry.Path).LastWriteTimeUtc -ge $cutoff) {
            throw "Output changed during review; cleanup refused: $($entry.Path)"
        }
    }
    foreach ($entry in @($plan | Where-Object Eligible)) {
        Assert-NoCook
        Assert-PlainPath $entry.Path
        # Path was resolved and proven inside its named project; no shell handoff.
        Remove-Item -LiteralPath $entry.Path -Recurse -Force
        if (Test-Path -LiteralPath $entry.Path) { throw "Incomplete removal: $($entry.Path)" }
        $result.Removed += $entry.Path
        $result.RemovedBytes += $entry.Bytes
        $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receipt -Encoding utf8
    }
}
$result.Complete = $true
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receipt -Encoding utf8
$plan | Select-Object Path, Bytes, FileCount, NewestUtc, Eligible | ConvertTo-Json -Depth 3
[pscustomobject]@{ Applied = [bool]$Apply; RemovedBytes = $result.RemovedBytes; Receipt = $receipt } | ConvertTo-Json -Compress
