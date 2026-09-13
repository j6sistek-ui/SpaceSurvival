<##
Runs one read-only engine preflight followed by three fresh Unreal processes using the real
USSGameInstance storage methods, including real Windows locked-file replacement failures
and retries for suspension consumption and death progression. Every invocation creates a
new GUID directory under Artifacts/SaveLifecycle; production storage is never modified.

UE 5.8 source contract, checked when authored:
  Core/Private/Misc/Paths.cpp: UserDir -> ProjectUserDir -> ProjectSavedDir (User/Saved).
  Engine/Public/SaveGameSystem.h: generic slots -> ProjectSavedDir/SaveGames/<slot>.sav.
  WindowsPlatformFeatures.cpp: optional custom backend; the test rejects any backend other
  than the exact generic singleton before GameInstance Init or any save write.

Build the Editor target first. Use -PreflightOnly to verify actual path/backend isolation
without initializing USSGameInstance or writing any save-game slots.
Use -PreparePackagedStation 5 or 10 to run only Preflight and one preparation process,
leaving a live suspension for a later packaged Continue check. The receipt is explicitly
PREPARED_FIXTURE_NOT_GAMEPLAY; preparation does not launch the package or consume the save.
Use -StorageFaults for GUID-only staging-create/readback permission failures and a real
parent-held oplock interruption before suspension replacement, followed by fresh recovery.
This does not simulate disk-full, short writes, or hardware power loss.
Use -CorruptAccount separately to verify account overwrite/resume/New Run protection after
fresh Init encounters a valid Unreal save envelope with invalid domain text. A verified
copy of only this GUID fixture is manually restored, then a fresh Init verifies normal
loading. This is not arbitrary binary corruption or an automatic backup/recovery feature.
##>
param(
    [string]$EngineRoot = '',
    [ValidateRange(30, 1200)][int]$TimeoutSeconds = 300,
    [switch]$PreflightOnly,
    [ValidateSet(5, 10)][int]$PreparePackagedStation,
    [switch]$StorageFaults,
    [switch]$CorruptAccount
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prepareStation = $PSBoundParameters.ContainsKey('PreparePackagedStation')
if (([int][bool]$PreflightOnly + [int][bool]$prepareStation + [int][bool]$StorageFaults + [int][bool]$CorruptAccount) -gt 1) {
    throw 'Choose only one of -PreflightOnly, -PreparePackagedStation, -StorageFaults or -CorruptAccount; nothing was created.'
}
$repoRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$project = Join-Path $repoRoot 'SpaceSurvival.uproject'
if (-not $EngineRoot) {
    $EngineRoot = @('C:\Program Files\EpicGames2\UE_5.8', 'C:\Program Files\Epic Games\UE_5.8') |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe') } |
        Select-Object -First 1
}
if (-not $EngineRoot) { throw 'An existing UE 5.8 installation is required; supply -EngineRoot.' }
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (-not (Test-Path -LiteralPath $editor -PathType Leaf)) { throw "Missing editor command executable: $editor" }
if (-not (Test-Path -LiteralPath $project -PathType Leaf)) { throw "Missing project: $project" }

function Assert-NoReparsePath([string]$Path) {
    $candidate = [IO.Path]::GetFullPath($Path)
    while ($candidate) {
        if (Test-Path -LiteralPath $candidate) {
            $item = Get-Item -LiteralPath $candidate -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing a redirected filesystem path: $candidate"
            }
        }
        $parentDirectory = [IO.Directory]::GetParent($candidate)
        $candidate = if ($null -ne $parentDirectory) { $parentDirectory.FullName } else { $null }
    }
}
function Get-ProductionSaveManifest {
    # Both default Windows locations for this project. Read hashes only; never copy payloads.
    $directories = @(
        (Join-Path $repoRoot 'Saved\SaveGames'),
        (Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'SpaceSurvival\Saved\SaveGames')
    ) | Sort-Object -Unique
    foreach ($directory in $directories) {
        Assert-NoReparsePath $directory
        $exists = Test-Path -LiteralPath $directory -PathType Container
        $files = @()
        if ($exists) {
            $files = @(Get-ChildItem -LiteralPath $directory -Filter '*.sav' -File -Force |
                Sort-Object Name | ForEach-Object {
                    Assert-NoReparsePath $_.FullName
                    [ordered]@{ name = $_.Name; bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
                })
        }
        [ordered]@{ directory = $directory; exists = $exists; files = $files }
    }
}
function ConvertTo-NativeArgument([string]$Value) {
    # All generated arguments have no embedded quotes or trailing backslash.
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsafe native argument quoting input.' }
    return '"' + $Value + '"'
}

function Stop-OwnedProcess([Diagnostics.Process]$Owned) {
    if ($null -eq $Owned) { return }
    if (-not $Owned.HasExited) { Stop-Process -InputObject $Owned -Force }
    if (-not $Owned.WaitForExit(10000)) { throw 'Owned fault writer did not terminate; its oplock must remain held.' }
    $Owned.Refresh()
}
function Get-IsolatedSaveManifest {
    Assert-NoReparsePath $saveGames
    foreach ($name in @('SS_Account_v1.sav', 'SS_Settings_v1.sav', 'SS_Suspend_v1.sav')) {
        $path = Join-Path $saveGames $name
        Assert-NoReparsePath $path
        $file = Get-Item -LiteralPath $path
        [ordered]@{ name = $name; bytes = $file.Length; sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
    }
}
function Get-SharedFileHash([string]$Path) {
    Assert-NoReparsePath $Path
    $stream = [IO.FileStream]::new($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read,
        ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}
function Save-TestAcl([string]$Path, [Collections.Generic.List[object]]$Snapshots) {
    Assert-NoReparsePath $Path
    if ($Path -ne $saveGames -and ([IO.Path]::GetDirectoryName($Path) -ne $saveGames -or
        [IO.Path]::GetFileName($Path) -notin @('SS_Account_v1.sav', 'SS_Settings_v1.sav', 'SS_Suspend_v1.sav'))) {
        throw 'ACL target is not an exact test-owned save path.'
    }
    if ([IO.Path]::GetFullPath($saveGames) -ne [IO.Path]::GetFullPath((Join-Path $runRoot 'User\Saved\SaveGames')) -or
        ([IO.File]::ReadAllText((Join-Path $runRoot '.ss-save-lifecycle'))).Trim() -cne $token) {
        throw 'ACL isolation marker/path check failed.'
    }
    $acl = Get-Acl -LiteralPath $Path
    $Snapshots.Add([pscustomobject]@{ path = $Path; descriptor = $acl.GetSecurityDescriptorBinaryForm() })
    # Persist recovery material before changing any DACL, even if the harness itself is interrupted.
    $Snapshots | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $phaseRoot 'OriginalAcls.json') -Encoding utf8
    return $acl
}
function Enable-StagingFault([string]$Phase, [Collections.Generic.List[object]]$Snapshots) {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
    if ($Phase -eq 'StageReadDenied') {
        # Existing slots stay readable; only subsequently created staging files inherit the denial.
        foreach ($name in @('SS_Account_v1.sav', 'SS_Settings_v1.sav', 'SS_Suspend_v1.sav')) {
            $path = Join-Path $saveGames $name
            $acl = Save-TestAcl $path $Snapshots
            $acl.SetAccessRuleProtection($true, $true)
            Set-Acl -LiteralPath $path -AclObject $acl
        }
    }
    $directoryAcl = Save-TestAcl $saveGames $Snapshots
    $rights = if ($Phase -eq 'StageCreateDenied') { [Security.AccessControl.FileSystemRights]::CreateFiles }
              else { [Security.AccessControl.FileSystemRights]::ReadData }
    $inherit = if ($Phase -eq 'StageReadDenied') { [Security.AccessControl.InheritanceFlags]::ObjectInherit }
               else { [Security.AccessControl.InheritanceFlags]::None }
    $propagate = if ($Phase -eq 'StageReadDenied') { [Security.AccessControl.PropagationFlags]::InheritOnly }
                 else { [Security.AccessControl.PropagationFlags]::None }
    $rule = [Security.AccessControl.FileSystemAccessRule]::new($identity, $rights, $inherit, $propagate,
        [Security.AccessControl.AccessControlType]::Deny)
    $directoryAcl.AddAccessRule($rule)
    Set-Acl -LiteralPath $saveGames -AclObject $directoryAcl
}
function Restore-TestAcls([Collections.Generic.List[object]]$Snapshots) {
    # Restore the directory first, then the original child inheritance/protection states.
    $failures = [Collections.Generic.List[string]]::new()
    foreach ($entry in ($Snapshots | Sort-Object { if ($_.path -eq $saveGames) { 0 } else { 1 } })) {
        try {
            Assert-NoReparsePath $entry.path
            if (Test-Path -LiteralPath $entry.path -PathType Container) {
                $acl = [Security.AccessControl.DirectorySecurity]::new()
                $acl.SetSecurityDescriptorBinaryForm($entry.descriptor, [Security.AccessControl.AccessControlSections]::Access)
                [IO.FileSystemAclExtensions]::SetAccessControl([IO.DirectoryInfo]::new($entry.path), $acl)
            } else {
                $acl = [Security.AccessControl.FileSecurity]::new()
                $acl.SetSecurityDescriptorBinaryForm($entry.descriptor, [Security.AccessControl.AccessControlSections]::Access)
                [IO.FileSystemAclExtensions]::SetAccessControl([IO.FileInfo]::new($entry.path), $acl)
            }
            $actual = (Get-Acl -LiteralPath $entry.path).GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access)
            $original = [Security.AccessControl.RawSecurityDescriptor]::new($entry.descriptor, 0)
            if ($actual -cne $original.GetSddlForm([Security.AccessControl.AccessControlSections]::Access)) {
                throw 'Restored access descriptor differs from its original.'
            }
        } catch { $failures.Add("$($entry.path): $($_.Exception.Message)") }
    }
    if ($failures.Count -ne 0) { throw ('Test ACL restoration failed: ' + ($failures -join '; ')) }
}
if ($StorageFaults -and -not ('SpaceSurvival.SaveFaults.ReplacementGate' -as [type])) {
    Add-Type -TypeDefinition (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'SaveFaultNative.cs') -Raw)
}

$token = [Guid]::NewGuid().ToString('N')
$artifactParent = Join-Path $repoRoot 'Artifacts\SaveLifecycle'
$runRoot = [IO.Path]::GetFullPath((Join-Path $artifactParent $token))
Assert-NoReparsePath $runRoot
if (Test-Path -LiteralPath $runRoot) { throw 'Unexpected GUID directory collision; existing data is untouched.' }
$userRoot = Join-Path $runRoot 'User'
$savedRoot = Join-Path $userRoot 'Saved'
$saveGames = Join-Path $savedRoot 'SaveGames'
$productionBefore = @(Get-ProductionSaveManifest)
New-Item -ItemType Directory -Path $userRoot | Out-Null
[IO.File]::WriteAllText((Join-Path $runRoot '.ss-save-lifecycle'), $token)
$productionBefore | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runRoot 'production-before.json') -Encoding utf8
$stages = @('Preflight')
if ($prepareStation) { $stages += "PrepareStation$PreparePackagedStation" }
elseif ($StorageFaults) {
    $stages += @('Suspend', 'StageCreateDenied', 'StageReadDenied', 'InterruptConsume', 'RecoverInterrupted', 'ResumeDeath', 'FreshStart')
}
elseif ($CorruptAccount) { $stages += @('SeedCorruptAccount', 'ProtectCorruptAccount', 'RecoverAccount') }
elseif (-not $PreflightOnly) { $stages += @('Suspend', 'ResumeDeath', 'FreshStart') }
$receipts = @()
$corruptFixtureHashes = $null
$corruptFixtureSlots = @()
$processIds = [Collections.Generic.HashSet[int]]::new()
$completed = $false
Write-Output "Lifecycle evidence directory: $runRoot"
try {
    foreach ($phase in $stages) {
        $phaseAclSnapshots = [Collections.Generic.List[object]]::new()
        $gate = $null
        $process = $null
        try {
            Assert-NoReparsePath $saveGames
            $phaseRoot = Join-Path $runRoot $phase
            New-Item -ItemType Directory -Path $phaseRoot | Out-Null
            $reportRoot = Join-Path $phaseRoot 'Report'
            $arguments = @(
                $project, '/Engine/Maps/Entry', '-unattended', '-NullRHI', '-nosound', '-NoSplash', '-NoLiveCoding',
                '-SaveToUserDir', "-UserDir=$userRoot", '-SSSaveLifecycle', "-SSSaveLifecycleRoot=$runRoot",
                "-SSSaveLifecycleToken=$token", "-SSSaveLifecyclePhase=$phase",
                '-ExecCmds=Automation RunTests SpaceSurvival.SaveLifecycle', '-TestExit=Automation Test Queue Empty',
                "-ReportExportPath=$reportRoot", "-abslog=$(Join-Path $phaseRoot 'Unreal.log')", '-stdout', '-FullStdOutLogOutput'
            )
            if ($prepareStation -and $phase -ne 'Preflight') {
                $arguments += "-SSPreparePackagedStation=$PreparePackagedStation"
            }
            if ($StorageFaults) { $arguments += '-SSSaveFaults' }
            if ($CorruptAccount) { $arguments += '-SSCorruptAccount' }
            if ($phase -in @('ProtectCorruptAccount', 'RecoverAccount')) {
                # Check both test copies and all three live domains before each fresh process.
                foreach ($name in @('CorruptAccount.original', 'CorruptAccount.corrupt')) {
                    $copyPath = Join-Path $runRoot $name
                    Assert-NoReparsePath $copyPath
                    if ($null -eq $corruptFixtureHashes -or
                        (Get-FileHash -LiteralPath $copyPath -Algorithm SHA256).Hash -cne $corruptFixtureHashes[$name]) {
                        throw 'A test-owned account fixture copy changed between processes.'
                    }
                }
                if (($corruptFixtureSlots | ConvertTo-Json -Compress) -cne
                    (@(Get-IsolatedSaveManifest) | ConvertTo-Json -Compress)) {
                    throw 'The isolated corruption fixture slots changed outside the expected test phase.'
                }
            }
            $slotsBefore = @()
            if ($phase -in @('StageCreateDenied', 'StageReadDenied', 'InterruptConsume')) {
                $slotsBefore = @(Get-IsolatedSaveManifest)
            }
            if ($phase -in @('StageCreateDenied', 'StageReadDenied')) {
                Enable-StagingFault $phase $phaseAclSnapshots
            }
            if ($phase -eq 'InterruptConsume') {
                $gate = [SpaceSurvival.SaveFaults.ReplacementGate]::new($repoRoot, $runRoot, $token)
            }
            $nativeArguments = ($arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
            $process = Start-Process -FilePath $editor -WorkingDirectory $repoRoot -ArgumentList $nativeArguments `
                -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $phaseRoot 'stdout.log') `
                -RedirectStandardError (Join-Path $phaseRoot 'stderr.log')
            if ($null -ne $gate) { $gate.BindWriter($process) }
            Write-Output "Started lifecycle $phase in process $($process.Id)."
            $timer = [Diagnostics.Stopwatch]::StartNew()
            if ($phase -eq 'InterruptConsume') {
                while (-not $gate.WaitForBreak(100)) {
                    if ($process.HasExited) { throw 'Writer exited before an acknowledgement-required replacement barrier.' }
                    if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'Timed out waiting for the replacement oplock.' }
                }
                if ($process.WaitForExit(250)) { throw 'Writer did not remain blocked while the parent withheld acknowledgement.' }
                $readyPath = Join-Path $runRoot 'InterruptConsumeReady.json'
                Assert-NoReparsePath $readyPath
                $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
                if ($ready.token -cne $token -or $ready.phase -cne 'InterruptConsumeReady' -or -not $ready.success -or
                    -not $ready.genericBackendVerified -or -not $ready.gameInstanceInitialized -or $ready.processId -ne $process.Id -or
                    [IO.Path]::GetFullPath($ready.savedDir) -ne [IO.Path]::GetFullPath($savedRoot)) {
                    throw 'Interrupted writer did not reach the guarded real ResumeRun call.'
                }
                $staging = @(Get-ChildItem -LiteralPath $saveGames -Filter '*.tmp' -File -Force)
                if ($staging.Count -ne 1 -or $staging[0].Name -cnotmatch '^SS_Suspend_v1\.sav\.[0-9a-fA-F]{32}\.tmp$') {
                    throw 'Replacement barrier does not have one completed suspension stage.'
                }
                $expectedPath = Join-Path $runRoot 'InterruptConsume.expected'
                Assert-NoReparsePath $expectedPath
                $expectedHash = (Get-FileHash -LiteralPath $expectedPath -Algorithm SHA256).Hash
                $stagingHash = Get-SharedFileHash $staging[0].FullName
                if ($stagingHash -cne $expectedHash) { throw 'Blocked replacement staging bytes differ from the real serialized invalidation.' }
                $breakInfo = $gate.Break
                # This parent continues holding the oplock through confirmed writer termination.
                Stop-OwnedProcess $process
                $gate.Dispose()
                $gate = $null
                $slotsAfter = @(Get-IsolatedSaveManifest)
                if (($slotsBefore | ConvertTo-Json -Compress) -cne ($slotsAfter | ConvertTo-Json -Compress) -or
                    (Get-SharedFileHash $staging[0].FullName) -cne $stagingHash) {
                    throw 'Interruption did not preserve all previous live bytes and the recorded abandoned stage.'
                }
                $seed = Get-Content -LiteralPath (Join-Path $runRoot 'Suspend.json') -Raw | ConvertFrom-Json
                if (-not $processIds.Add($process.Id)) { throw 'Interrupted process ID was already used by another stage.' }
                $receipt = [ordered]@{
                    phase = $phase; token = $token; savedDir = $savedRoot; processId = $process.Id
                    success = $true; genericBackendVerified = $true; gameInstanceInitialized = $true
                    evidenceType = 'OWNED_PROCESS_TERMINATED_BEFORE_REPLACEMENT'
                    accountPayload = $seed.accountPayload; settingsPayload = $seed.settingsPayload; runPayload = $seed.runPayload
                    stagingName = $staging[0].Name; stagingSha256 = $stagingHash; expectedSha256 = $expectedHash
                    acknowledgementRequired = $true; originalOplockLevel = $breakInfo.OriginalLevel
                    newOplockLevel = $breakInfo.NewLevel; oplockFlags = $breakInfo.Flags
                    conflictingAccessMode = $breakInfo.AccessMode; conflictingShareMode = $breakInfo.ShareMode
                    observedBlockedMilliseconds = 250; writerExitedBeforeOplockRelease = $true
                    previousLiveSlotBytesPreserved = $true; exitCode = $process.ExitCode
                    automationCompletionExpected = $false
                }
                $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runRoot "$phase.json") -Encoding utf8
                $receipts += $receipt
                Write-Output "PASS: real replacement blocked; owned writer $($process.Id) terminated before oplock release."
                continue
            }
            while (-not $process.WaitForExit(1000)) {
                if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
                    # This handle belongs only to the child process this harness just created.
                    Stop-OwnedProcess $process
                    throw "Lifecycle $phase exceeded $TimeoutSeconds seconds; only its owned process was stopped."
                }
            }
            $process.Refresh()
            if ($process.ExitCode -ne 0) { throw "Lifecycle $phase process exited $($process.ExitCode). Inspect $phaseRoot." }
            $reportPath = Join-Path $reportRoot 'index.json'
            $receiptPath = Join-Path $runRoot "$phase.json"
            if (-not (Test-Path -LiteralPath $reportPath) -or -not (Test-Path -LiteralPath $receiptPath)) {
                throw "Lifecycle $phase did not produce both a real automation report and a guarded success receipt."
            }
            $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
            $expectedTest = "SpaceSurvival.SaveLifecycle.$phase"
            $matchingTests = @($report.tests | Where-Object { $_.fullTestPath -eq $expectedTest })
            if ($report.failed -ne 0 -or $report.notRun -ne 0 -or $matchingTests.Count -ne 1 -or
                $matchingTests[0].state -ne 'Success' -or @($report.tests).Count -ne 1) {
                throw "Lifecycle $phase automation did not pass its one expected test."
            }
            $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
            if ($receipt.token -ne $token -or $receipt.phase -ne $phase -or -not $receipt.success -or
                -not $receipt.genericBackendVerified -or $receipt.processId -ne $process.Id -or
                [IO.Path]::GetFullPath($receipt.savedDir) -ne [IO.Path]::GetFullPath($savedRoot) -or
                -not $processIds.Add([int]$receipt.processId)) {
                throw "Lifecycle $phase receipt failed path, backend, token, or distinct-process verification."
            }
            if ($prepareStation -and $phase -ne 'Preflight') {
                if ($receipt.evidenceType -cne 'PREPARED_FIXTURE_NOT_GAMEPLAY' -or
                    $receipt.preparedWave -ne $PreparePackagedStation -or -not $receipt.runActive -or
                    $receipt.xpAwarded -or -not $receipt.unconsumedSuspensionVerified -or
                    $receipt.xp -ne 0 -or $receipt.completedRuns -ne 0) {
                    throw 'Prepared station receipt failed its fixture, exact-wave, live-state or unconsumed-save checks.'
                }
            }
            if ($CorruptAccount -and $phase -ne 'Preflight') {
                $requiredChecks = switch ($phase) {
                    'SeedCorruptAccount' { @('domainCorruptEnvelopeSeeded', 'exactOriginalFixtureCopyVerified', 'exactCorruptFixtureCopyVerified') }
                    'ProtectCorruptAccount' { @('freshInitProtectedAccount', 'resumeBlocked', 'gameModeNewRunBlocked',
                        'persistAccountBlocked', 'corruptBytesPreservedBeforeRestore', 'exactOriginalFixtureCopyRestored',
                        'sameInstanceRemainsBlockedAfterFixtureRestore') }
                    'RecoverAccount' { @('freshInitRestoredAccount', 'originalCheckpointAvailable', 'validAccountPersistenceRestored') }
                }
                foreach ($check in $requiredChecks) {
                    if ($null -eq $receipt.PSObject.Properties[$check] -or $receipt.$check -ne $true) {
                        throw "Corrupt-account $phase did not verify its expected check: $check."
                    }
                }
                if ($receipt.xp -ne 0 -or $receipt.completedRuns -ne 0) {
                    throw 'The domain-corruption fixture unexpectedly awarded progression.'
                }
                $currentSlots = @(Get-IsolatedSaveManifest)
                $copyHashes = [ordered]@{}
                foreach ($name in @('CorruptAccount.original', 'CorruptAccount.corrupt')) {
                    $copyPath = Join-Path $runRoot $name
                    Assert-NoReparsePath $copyPath
                    $copyHashes[$name] = (Get-FileHash -LiteralPath $copyPath -Algorithm SHA256).Hash
                }
                if ($phase -eq 'SeedCorruptAccount') {
                    if ($copyHashes['CorruptAccount.original'] -ceq $copyHashes['CorruptAccount.corrupt']) {
                        throw 'The original and corrupt account fixture bytes are identical.'
                    }
                    $corruptFixtureHashes = $copyHashes
                } else {
                    if (($copyHashes | ConvertTo-Json -Compress) -cne ($corruptFixtureHashes | ConvertTo-Json -Compress)) {
                        throw 'A test-owned account fixture copy changed during the engine phase.'
                    }
                    $previousOtherSlots = @($corruptFixtureSlots | Where-Object { $_.name -ne 'SS_Account_v1.sav' })
                    $currentOtherSlots = @($currentSlots | Where-Object { $_.name -ne 'SS_Account_v1.sav' })
                    if (($previousOtherSlots | ConvertTo-Json -Compress) -cne ($currentOtherSlots | ConvertTo-Json -Compress)) {
                        throw 'Account protection/restoration changed settings or the unconsumed checkpoint.'
                    }
                }
                $account = @($currentSlots | Where-Object { $_.name -eq 'SS_Account_v1.sav' })
                $expectedCopy = if ($phase -eq 'SeedCorruptAccount') { 'CorruptAccount.corrupt' } else { 'CorruptAccount.original' }
                if ($account.Count -ne 1 -or ($phase -ne 'RecoverAccount' -and
                    $account[0].sha256 -cne $corruptFixtureHashes[$expectedCopy])) {
                    throw 'Live account bytes do not exactly match the expected original/corrupt fixture copy.'
                }
                if ($phase -eq 'RecoverAccount') {
                    # Exact original bytes were checked before launching this process and by C++
                    # before its deliberate PersistAccount. A successful re-save may reorder UE's
                    # custom-version header array, so its final account domain is the invariant.
                    $seedReceipt = @($receipts | Where-Object { $_.phase -eq 'SeedCorruptAccount' })
                    if ($seedReceipt.Count -ne 1 -or $receipt.accountPayload -cne $seedReceipt[0].accountPayload) {
                        throw 'The successfully re-saved account differs from the original account domain.'
                    }
                }
                $corruptFixtureSlots = $currentSlots
            }
            if ($phase -in @('StageCreateDenied', 'StageReadDenied')) {
                if (-not $receipt.allThreeWritesRejectedAndPreserved -or -not $receipt.nativePermissionProbeVerified -or
                    ($slotsBefore | ConvertTo-Json -Compress) -cne (@(Get-IsolatedSaveManifest) | ConvertTo-Json -Compress)) {
                    throw 'Staging fault did not preserve all three original domains or verify the native permission behavior.'
                }
            }
            if ($phase -eq 'RecoverInterrupted' -and (-not $receipt.abandonedInvalidationIgnored -or
                -not $receipt.originalCheckpointAvailable -or -not $receipt.onlyRecordedTemporaryRemoved)) {
                throw 'Fresh process did not verify abandoned-stage recovery.'
            }
            if ($phase -eq 'ResumeDeath') {
                foreach ($check in @('lockedSuspensionRejectedAndPreserved', 'lockedAccountRejectedAndPreserved',
                    'replacementRetriesSucceeded', 'failedReplacementStagingCleaned')) {
                    if ($null -eq $receipt.PSObject.Properties[$check] -or $receipt.$check -ne $true) {
                        throw "Lifecycle ResumeDeath did not verify its actual filesystem fault check: $check."
                    }
                }
            }
            $temporarySaves = @(if (Test-Path -LiteralPath $saveGames) {
                Get-ChildItem -LiteralPath $saveGames -Filter '*.tmp' -File -Force
            })
            if ($temporarySaves.Count -ne 0) { throw "Lifecycle $phase leaked an isolated staging file." }
            $actualSaves = @(if (Test-Path -LiteralPath $saveGames) {
                Get-ChildItem -LiteralPath $saveGames -Filter '*.sav' -File -Force
            })
            foreach ($file in $actualSaves) { Assert-NoReparsePath $file.FullName }
            if ($phase -eq 'Preflight') {
                if ($receipt.gameInstanceInitialized -or $actualSaves.Count -ne 0) {
                    throw 'Preflight unexpectedly initialized a GameInstance or wrote a save-game slot.'
                }
                Write-Output "Verified isolated generic save path before writes: $saveGames"
            } else {
                $expectedSaves = @('SS_Account_v1.sav', 'SS_Settings_v1.sav', 'SS_Suspend_v1.sav')
                if (-not $receipt.gameInstanceInitialized -or
                    @(Compare-Object $expectedSaves @($actualSaves.Name)).Count -ne 0) {
                    throw "Lifecycle $phase did not produce exactly the three expected isolated save domains."
                }
            }
            $receipts += $receipt
            Write-Output "PASS $expectedTest (process $($process.Id))."
        } finally {
            try {
                Stop-OwnedProcess $process
                if ($null -ne $gate) { $gate.Dispose() }
            } finally {
                Restore-TestAcls $phaseAclSnapshots
            }
        }
    }
    $completed = $true
} finally {
    $productionAfter = @(Get-ProductionSaveManifest)
    $productionAfter | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runRoot 'production-after.json') -Encoding utf8
    $productionUnchanged = ($productionBefore | ConvertTo-Json -Depth 8 -Compress) -ceq
                           ($productionAfter | ConvertTo-Json -Depth 8 -Compress)
    $isolatedFiles = @(if (Test-Path -LiteralPath $saveGames) {
        Get-ChildItem -LiteralPath $saveGames -Filter '*.sav' -File | Sort-Object Name | ForEach-Object {
            [ordered]@{ name = $_.Name; bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
        }
    })
    [ordered]@{
        success = $completed -and $productionUnchanged
        preflightOnly = [bool]$PreflightOnly
        storageFaults = [bool]$StorageFaults
        corruptAccount = [bool]$CorruptAccount
        testAccountCopySha256 = $corruptFixtureHashes
        preparedStationWave = if ($prepareStation) { $PreparePackagedStation } else { $null }
        evidenceType = if ($prepareStation) { 'PREPARED_FIXTURE_NOT_GAMEPLAY' } elseif ($StorageFaults) { 'STORAGE_FAULT_AUTOMATION' } elseif ($CorruptAccount) { 'CORRUPT_ACCOUNT_PROTECTION_AUTOMATION' } else { 'STORAGE_LIFECYCLE_AUTOMATION' }
        token = $token
        root = $runRoot
        savedDir = $savedRoot
        userDir = $userRoot
        productionSaveHashesUnchanged = $productionUnchanged
        processReceipts = $receipts
        isolatedSaveFiles = $isolatedFiles
        limitation = if ($prepareStation) {
            'PREPARED_FIXTURE_NOT_GAMEPLAY. Assisted station state written through real GI SuspendRun, without consuming it. No natural waves/contracts, packaged Continue, station UI, quit interaction, audio or subjective gameplay was exercised.'
        } elseif ($StorageFaults) {
            'Real Windows staging-create/readback access denial, parent-held acknowledgement-required oplock interruption before replacement, and fresh-process recovery/once-only XP. No disk-full, short-write, hardware-loss, station UI or subjective gameplay claim.'
        } elseif ($CorruptAccount) {
            'Real fresh Init protects a valid Unreal envelope with invalid account domain text; actual GI resume/persistence and GameMode New Run are rejected without changing corrupt bytes. Exact test-owned copy restoration is manual, followed by fresh Init. No arbitrary binary corruption, automatic recovery/backup feature, hardware-loss or gameplay claim.'
        } else {
            'Storage lifecycle and actual Windows locked-destination failure/retry only. No forced process termination, disk-full/short-write, staged-readback fault, hardware-loss, station UI or subjective gameplay claim.'
        }
    } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runRoot 'result.json') -Encoding utf8
    if (-not $productionUnchanged) {
        throw "Production save metadata changed during the harness; nothing was backed up or replaced. Inspect $runRoot."
    }
}
Write-Output "PASS: production save hashes unchanged. Evidence: $(Join-Path $runRoot 'result.json')"
if ($prepareStation) {
    Write-Output "PREPARED_FIXTURE_NOT_GAMEPLAY: Wave $PreparePackagedStation; packaged QA UserDir: $userRoot"
}
