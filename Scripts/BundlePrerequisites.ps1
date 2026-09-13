<#
Bundles the x64 Visual C++ prerequisite without installing it or changing the Engine.
The game's link response file identifies its selected MSVC installation; the retained UAT
log corroborates the exact compiler version when UBT rebuilt the target. -DryRun only reads.
#>
param(
    [Parameter(Mandatory = $true)][string]$BuildLog,
    [switch]$DryRun
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$archive = Join-Path $root 'Artifacts\Windows'
$destination = Join-Path $archive 'Engine\Extras\Redist\en-us\vc_redist.x64.exe'
$game = Join-Path $archive 'SpaceSurvival\Binaries\Win64\SpaceSurvival.exe'
$localGame = Join-Path $root 'Binaries\Win64\SpaceSurvival.exe'
$response = Join-Path $root 'Intermediate\Build\Win64\x64\SpaceSurvival\Development\SpaceSurvival.exe.rsp'
$BuildLog = [IO.Path]::GetFullPath($BuildLog)
foreach ($required in @($BuildLog, $response, $game, $localGame)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Prerequisite verification requires $required." }
}
$gameHash = (Get-FileHash -LiteralPath $game -Algorithm SHA256).Hash
if ($gameHash -ne (Get-FileHash -LiteralPath $localGame -Algorithm SHA256).Hash) {
    throw 'Archived and built game executables differ. Repackage before selecting a runtime for this archive.'
}
$links = @([regex]::Matches((Get-Content -LiteralPath $response -Raw),
    '(?m)^/LIBPATH:"(?<path>[^"\r\n]+[/\\]VC[/\\]Tools[/\\]MSVC[/\\](?<family>\d+\.\d+\.\d+(?:\.\d+)?))[/\\]lib[/\\]x64"\r?$'))
if ($links.Count -ne 1) { throw 'Cannot identify one x64 MSVC toolchain from the game link response file.' }
$toolchain = [IO.Path]::GetFullPath($links[0].Groups['path'].Value)
$family = $links[0].Groups['family'].Value
$toolVersion = [version]$family
$toolEvidence = 'game link response file (up-to-date target fallback)'
$compilerSelections = @([regex]::Matches((Get-Content -LiteralPath $BuildLog -Raw),
    'Using Visual Studio (?<version>\d+\.\d+\.\d+(?:\.\d+)?) toolchain \((?<path>.+?)\) and Windows'))
foreach ($selection in $compilerSelections) {
    if ([IO.Path]::GetFullPath($selection.Groups['path'].Value) -eq $toolchain) {
        $toolVersion = [version]$selection.Groups['version'].Value
        $toolEvidence = 'retained UAT log and game link response file'
    }
}
$familyVersion = [version]$family
if ($toolVersion.Major -ne $familyVersion.Major -or $toolVersion.Minor -ne $familyVersion.Minor) {
    throw 'The compiler log and link response file disagree about the MSVC toolset.'
}
# Only inspect this selected VS installation's matching folder and its declared default.
$vcRoot = Split-Path (Split-Path (Split-Path $toolchain -Parent) -Parent) -Parent
$candidates = @(Join-Path $vcRoot "Redist\MSVC\$family\vc_redist.x64.exe")
$defaultFile = Join-Path $vcRoot 'Auxiliary\Build\Microsoft.VCRedistVersion.default.txt'
if (Test-Path -LiteralPath $defaultFile -PathType Leaf) {
    $declared = (Get-Content -LiteralPath $defaultFile -Raw).Trim()
    if ($declared -match '^\d+\.\d+\.\d+(?:\.\d+)?$') {
        $candidates += Join-Path $vcRoot "Redist\MSVC\$declared\vc_redist.x64.exe"
    }
}
function Get-VerifiedRuntime([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $file = Get-Item -LiteralPath $Path
    $info = $file.VersionInfo
    $version = [version]::new($info.FileMajorPart, $info.FileMinorPart, $info.FileBuildPart, $info.FilePrivatePart)
    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate -or
        $signature.SignerCertificate.Subject -notmatch '(^|,\s*)CN=Microsoft Corporation(,|$)') { return $null }
    # Microsoft requires the matching major and the same or newer toolset minor.
    # Compiler patch versions and redistributable servicing versions are different series.
    if ($version.Major -ne $toolVersion.Major -or $version.Minor -lt $toolVersion.Minor) { return $null }
    return [pscustomobject]@{
        path = $file.FullName
        version = $version.ToString()
        bytes = $file.Length
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        signature = [string]$signature.Status
        signer = $signature.SignerCertificate.Subject
        certificateThumbprint = $signature.SignerCertificate.Thumbprint
    }
}
$selected = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    $selected = Get-VerifiedRuntime $candidate
    if ($null -ne $selected) { break }
}
$bundled = Get-VerifiedRuntime $destination
if ($null -ne $bundled -and ($null -eq $selected -or [version]$bundled.version -ge [version]$selected.version)) {
    $selected = $bundled
}
if ($null -eq $selected) {
    throw "No signed Microsoft x64 runtime compatible with MSVC $toolVersion was found in this archive or the selected VS installation. Provide a compatible redistributable there, then repackage; nothing was installed."
}
# Archive writes stay within the project and reject junction/symlink redirects.
$receiptPath = Join-Path $archive 'Prerequisites.json'
foreach ($outputPath in @($destination, $receiptPath)) {
    $checkPath = $outputPath
    while ($checkPath -and $checkPath -ne $root) {
        if (Test-Path -LiteralPath $checkPath) {
            if ((Get-Item -LiteralPath $checkPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Refusing a redirected prerequisite output path: $checkPath."
            }
        }
        $checkPath = Split-Path $checkPath -Parent
    }
    if ($checkPath -ne $root) { throw 'Prerequisite output is outside the project.' }
}
$before = if (Test-Path -LiteralPath $destination -PathType Leaf) {
    [pscustomobject]@{
        version = (Get-Item -LiteralPath $destination).VersionInfo.FileVersion
        sha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    }
} else { $null }
$needsCopy = $null -eq $before -or $before.sha256 -ne $selected.sha256
$receipt = [ordered]@{
    status = if ($DryRun) { 'DRY_RUN_NO_ARCHIVE_CHANGES' } else { 'BUNDLED_SIGNATURE_AND_BYTES_VERIFIED' }
    dateUtc = [DateTime]::UtcNow.ToString('o')
    platform = 'Windows x64'
    toolchain = [ordered]@{ path = $toolchain; version = $toolVersion.ToString(); family = $family; evidence = $toolEvidence }
    buildLog = [ordered]@{ path = $BuildLog; sha256 = (Get-FileHash -LiteralPath $BuildLog -Algorithm SHA256).Hash }
    linkResponse = [ordered]@{ path = $response; sha256 = (Get-FileHash -LiteralPath $response -Algorithm SHA256).Hash }
    gameExecutableSha256 = $gameHash
    selectedSource = $selected
    previousArchiveRuntime = $before
    destination = $destination
    replacementRequired = $needsCopy
    limits = 'Bundle presence, Microsoft signature and version compatibility only. No installer execution or clean-PC launch verification; ARM64 is outside this Windows x64 target.'
}
if (-not $DryRun) {
    if ($needsCopy) {
        New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $selected.path -Destination $destination -Force
    }
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $selected.sha256) {
        throw 'Archived prerequisite bytes do not match the verified source; do not distribute this archive.'
    }
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
}
$receipt | ConvertTo-Json -Depth 6
