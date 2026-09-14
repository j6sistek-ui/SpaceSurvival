param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    docker build --progress plain -t spacesurvival-core-checks .
    if ($LASTEXITCODE -ne 0) { throw 'Container build failed; no domain test pass is claimed.' }
    docker run --rm spacesurvival-core-checks
    if ($LASTEXITCODE -ne 0) { throw 'Domain checks failed.' }
} finally { Pop-Location }
