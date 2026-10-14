$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$helper = Join-Path $repo 'Scripts\CleanCookTemp.ps1'
$fixture = Join-Path $repo ('.agent\local\CookCleanup\fixture-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture -Force | Out-Null
Set-Content -LiteralPath (Join-Path $fixture 'SpaceSurvival.uproject') -Value '{}' -NoNewline

# Test the process guard without inspecting or changing the owner's processes.
$mockCook = $false
function Get-CimInstance {
    param([string]$ClassName)
    if ($mockCook) { [pscustomobject]@{ Name = 'UnrealEditor-Cmd.exe'; CommandLine = '-run=cook' } }
}
function Assert([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Expect-Refusal([scriptblock]$Action, [string]$Message) {
    $caught = $false
    try { & $Action | Out-Null }
    catch { $caught = $_.Exception.Message -like ('*' + $Message + '*') }
    Assert $caught ('Expected refusal: ' + $Message)
}

$target = Join-Path $fixture 'Saved\Cooked'
$protected = Join-Path $fixture 'Saved\SaveGames\owner.sav'
New-Item -ItemType Directory -Path $target, (Split-Path $protected -Parent) -Force | Out-Null
Set-Content -LiteralPath $protected -Value 'protected save' -NoNewline
$file = Join-Path $target 'discard.tmp'
Set-Content -LiteralPath $file -Value 'rebuildable output' -NoNewline

# Recent outputs survive even an explicit Apply.
& $helper -ProjectRoot $fixture -Apply | Out-Null
Assert (Test-Path -LiteralPath $file) 'Recent output was deleted'

# Dry run preserves an old eligible output; Apply removes only its allowlisted tree.
$old = [DateTime]::UtcNow.AddHours(-72)
(Get-Item -LiteralPath $file).LastWriteTimeUtc = $old
(Get-Item -LiteralPath $target).LastWriteTimeUtc = $old
& $helper -ProjectRoot $fixture | Out-Null
Assert (Test-Path -LiteralPath $file) 'Dry run deleted output'
& $helper -ProjectRoot $fixture -Apply | Out-Null
Assert (-not (Test-Path -LiteralPath $target)) 'Old output was not removed'
Assert ((Get-Content -LiteralPath $protected -Raw) -eq 'protected save') 'Save outside target changed'

# Save-like files in a target and any active cooker must fail before deletion.
New-Item -ItemType Directory -Path $target -Force | Out-Null
Set-Content -LiteralPath (Join-Path $target 'unexpected.sav') -Value 'keep'
Expect-Refusal { & $helper -ProjectRoot $fixture -Apply } 'Save/source file'
Assert (Test-Path -LiteralPath (Join-Path $target 'unexpected.sav')) 'Refused file was deleted'
$mockCook = $true
Expect-Refusal { & $helper -ProjectRoot $fixture -Apply } 'cook/package process'
$mockCook = $false
Expect-Refusal { & $helper -ProjectRoot (Split-Path $fixture -Parent) } 'Not a SpaceSurvival project'

'PASS: recent retention, dry run, old-output removal, protected-save preservation, source-file refusal, active-cook refusal and invalid-root refusal.'
# Tiny fixture/receipts are retained for inspection; no broad test-tree deletion.
