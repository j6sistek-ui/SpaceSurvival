<# Open this checkout's packaged game with a separate persistent review profile.
   -DryRun validates paths and prints the launch plan without launching or writing files. #>
param([switch]$DryRun)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$package = Join-Path $repoRoot 'Artifacts/Windows'
$executable = Join-Path $package 'SpaceSurvival.exe'
$profile = Join-Path $repoRoot 'Artifacts/PackagedReviewUser'

function Assert-NoRedirectedPath([string]$Path) {
    $candidate = [IO.Path]::GetFullPath($Path)
    while ($candidate) {
        if (Test-Path -LiteralPath $candidate) {
            $item = Get-Item -LiteralPath $candidate -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing redirected package/profile path: $candidate"
            }
        }
        $parent = [IO.Directory]::GetParent($candidate)
        $candidate = if ($null -ne $parent) { $parent.FullName } else { $null }
    }
}

function Assert-NoRedirectedTree([string]$Path) {
    Assert-NoRedirectedPath $Path
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Expected a directory: $Path"
    }
    # Inspect before descending, including an existing Saved/SaveGames directory.
    # A review-profile junction must never redirect writes to the installed profile.
    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push($Path)
    while ($pending.Count -gt 0) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing redirected package/profile entry: $($item.FullName)"
            }
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
        }
    }
}

foreach ($path in @($repoRoot, $executable, $profile)) {
    if ($path.Contains('"') -or $path.Contains("`r") -or $path.Contains("`n")) {
        throw 'Unsupported quote or newline in checkout path.'
    }
}
Assert-NoRedirectedTree $package
Assert-NoRedirectedTree $profile
Assert-NoRedirectedPath $executable
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Packaged review build is missing: $executable. Package this checkout first."
}

$launchArguments = @(
    '-windowed', '-ResX=1600', '-ResY=900',
    ('-UserDir="' + $profile + '"'), '-SaveToUserDir', '-nosplash'
)
Write-Output "Executable: $executable"
Write-Output "Working directory: $package"
Write-Output "Persistent review profile: $profile"
Write-Output ('Arguments: ' + ($launchArguments -join ' '))
if ($DryRun) {
    Write-Output 'Dry run only; no process launched and no files written.'
    return
}

# The owner invokes this launcher to open the interactive game. Unreal creates
# the isolated profile as needed; this script never builds, installs or copies saves.
Start-Process -FilePath $executable -WorkingDirectory $package -WindowStyle Normal -ArgumentList $launchArguments
