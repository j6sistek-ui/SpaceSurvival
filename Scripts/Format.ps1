param([switch]$Check)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    & docker build -f Tools.Dockerfile -t spacesurvival-format .
    if ($LASTEXITCODE -ne 0) { throw 'Container formatter build failed.' }
    $files = @(Get-ChildItem Source,Tests -Recurse -File | Where-Object { $_.Extension -in '.cpp','.h' } |
        ForEach-Object { [IO.Path]::GetRelativePath($root,$_.FullName).Replace('\','/') })
    [string[]]$formatOptions = if ($Check) { @('--dry-run','--Werror') } else { @('-i') }
    & docker run --rm --mount "type=bind,source=$root,target=/workspace" spacesurvival-format @formatOptions @files
    if ($LASTEXITCODE -ne 0) { throw 'C++ formatting check failed.' }
} finally { Pop-Location }
