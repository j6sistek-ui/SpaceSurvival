# Build and run

**Current archive: Package 11, source `6912684223f4a93f4010cd12201aee7fb42395f3`.** The package and normal-timing station/endgame fixtures passed with the boundaries in [current state](PROJECT_STATE.md) and the [package receipt](validation/2026-09-13-windows-integrated-presentation-package.json). Phase 1 remains PARTIAL; see the physical playtest and presentation gaps before treating the build as accepted.

## Tooling and repository

Run commands from the repository root, currently `C:/Users/j6sis/SpaceSurvival`.

- Owner-installed Unreal Engine 5.8.2: `C:/Program Files/EpicGames2/UE_5.8`.
- Owner-installed Visual Studio 2026 C++ toolchain: MSVC 14.51.36257, Windows SDK 10.0.26100.0. Builds have succeeded; UBT reports that this compiler is newer than its preferred version. Consult the installed engine's `Engine/Config/Windows/Windows_SDK.json` if changing toolchains.
- Docker Desktop Linux containers supply GCC and clang-format. No host system packages were installed by the implementation.
- Existing Python 3 validates/generates source assets. Blender/Pillow are used by optional source previews; they are not needed to run the game.

The similarly named `C:/Program Files/Epic Games/UE_5.8` directory was an incomplete installation location. Use the complete engine above or pass an explicit `-EngineRoot`.

## Source checks

```powershell
./Scripts/TestCore.ps1
./Scripts/Format.ps1 -Check
python Scripts/CheckProject.py
python -m compileall -q Scripts ContentSource
python ContentSource/ValidateSources.py
python Tests/TestSourceDigests.py
python Scripts/TestFreshCheckout.py
git diff --check
```

Portable tests compile the domain and its tests under strict C++17 and ASan/UBSan. They do not compile Unreal adapters or exercise input, rendering or gameplay. Formatting without `-Check` changes source files. Capture the actual result and source revision; a listed command is not a pass record. Source-format validation writes its routine receipt to Saved/Validation rather than mutating historical source receipts. Fresh-checkout checks use an immutable Git export: uncommitted candidates are not included. The current implementation accepts only exact or complete uniform LF/CRLF forms for UTF-8 OBJ/MTL/JSON; original GLB/binary hashes remain exact.

## Unreal build, content and automation

```powershell
./Scripts/Build.ps1 -Target Editor
./Scripts/Build.ps1 -Target Content
./Scripts/Build.ps1 -Target Validate
./Scripts/Build.ps1 -Target Test
```

Each target accepts `-EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'`. Close project instances that lock the module before rebuilding; do not close unrelated owner editor sessions.

- **Editor** invokes UnrealBuildTool for SpaceSurvivalEditor, Win64 Development.
- **Content** imports canonical sources and authors the tuning asset and Survival map. Inspect `Saved/Validation/ContentImport.json`; the successful status is `IMPORTED_NOT_GAMEPLAY_VALIDATED` with no errors. Existing authored assets are preserved, and partial/wrong-type imports are rejected. Read [CONTENT_PIPELINE.md](CONTENT_PIPELINE.md) before deliberate reimport.
- **Validate** starts a fresh rendering-enabled editor process and checks persisted assets, map/GameMode, fixed rosters/selections, backdrop collision, mesh material usage and compiled field shader statistics. NullRHI cannot supply those shader statistics and is not used for this target. The full rendering-enabled readback passed at 11:48:03 UTC in `.agent/local/VisualIntegrationValidate2.log`; the preceding no-change content rerun preserved all 110 asset files byte-for-byte.
- **Test** remains NullRHI and runs the SpaceSurvival automation prefix into Artifacts/UnrealTests/index.json/index.html. It requires a fresh nonempty report, at least one success, zero warnings/failures/not-run cases and every state Success; process exit 0 alone is insufficient. The current 24-test result passed at 12:00:54 UTC and is retained in `.agent/local/ChaseAim-tests.json`. Earlier authored-exit contact failures and their correction remain in [VALIDATION.md](VALIDATION.md). Shortened/assisted fixtures do not establish rendering, balance, physical input or performance.

`Scripts/ValidateScene.py`, executed by the editor Python runner, checks saved background collision and skeletal/instanced-material usage. Its `--repair` option intentionally changes those owned assets; omit it for readback validation. Results go to `Saved/Validation/SceneValidation.json`. The latest repair/readback is recorded in [VALIDATION.md](VALIDATION.md).

Open `SpaceSurvival.uproject` in UE 5.8.2 and load `/Game/SpaceSurvival/Maps/Survival`. For a separate development game window:

```powershell
$ueEditor = 'C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$ssProject = Join-Path (Get-Location) 'SpaceSurvival.uproject'
& $ueEditor $ssProject -game -windowed -ResX=1280 -ResY=720 -log
```

This runs the project through the installed editor executable. It is not a packaged build.

## Windows package

```powershell
./Scripts/Build.ps1 -Target Package
```

The wrapper requires the gameplay map, then runs Win64 Development BuildCookRun with build, cook, stage, pak, IoStore, prerequisites and archive enabled. Package 11 succeeded in 87.75 seconds, exit 0, with a 29.09-second native build.

Archive: `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`. **Verified identity: Package 11, source `6912684223f4a93f4010cd12201aee7fb42395f3`.** Later packaging replaces this shared path; compare the [retained receipt](validation/2026-09-13-windows-integrated-presentation-package.json) before relying on a historical hash.

| Artifact | Size | SHA-256 |
| --- | --- | --- |
| `Artifacts/Windows/SpaceSurvival.exe` launcher | 171,520 bytes | `619ac0779dceabf638639193efdea0733e3b4626dea623c07062f160f5abccf8` |
| `Artifacts/Windows/SpaceSurvival/Binaries/Win64/SpaceSurvival.exe` game | 332,566,528 bytes | `10b9b664c9a9d7480d96412999dd9da0b33215bc423eaae77a395fde8c9ed32c` |

The receipt also binds all five .pak/.utoc/.ucas containers, all 110 project packages plus Engine Cube, 2,171 index rows and prerequisite provenance. The Package 11 Station 5/Wave 10 measurements and their scripted-input limits are in [PERFORMANCE.md](PERFORMANCE.md).

Keep the entire archive directory together; the launcher alone is not the game. Launch from the repository root:

```powershell
& './Artifacts/Windows/SpaceSurvival.exe' -windowed -ResX=1280 -ResY=720
```

## Historical package checks

Package 9/source 4178 built in 74.18 seconds and audited all 78 project packages/Engine Cube. Native Station 1 showed full 2K deck residency; its full Wave 10 fixture has a separate [package](validation/2026-09-13-windows-visual-package.json) and [performance](validation/2026-09-13-endgame-performance.json) identity. Package 8/source 442ff06 built in 86.44 seconds with 62 project packages plus Cube; its 13-test/524-domain-assertion results remain historical.

**Package 8 exit smoke:** Package 8's guarded SSReviewExit replay visibly reached seated, airborne, landing and full standing poses, suppressed interaction prompts during exit, then allowed service E and departure into Wave 6. It used a prepared station profile and Slomo 0.1, restored to 1 afterward; it does not establish natural docking/camera feel. Neutral Wave 7 death then displayed score 11,800, 510 XP, level 3 and both unlocks from the seeded 100-kill fixture. The owned launch closed normally and production-save hashes remained unchanged. See [VALIDATION.md](VALIDATION.md) and the [package 8 receipt](validation/2026-09-13-windows-exit-package.json) for exact fixture limits and audit provenance. Panorama v1 residency was observed at 2048×1024/12 mips; seams, poles and flight readability remain unaccepted.

**Historical package 7 station smoke:** Package 7 exercised actual prepared-station menus and process restarts. Station 1 Save & Quit/Continue retained 1,070 credits, Hull 145 and Hunter 0/6; departure entered Wave 6. Neutral Wave 7 death awarded 510 XP and both unlocks; a third launch retained 510 XP/highest wave 7/best score 11,800/one run, with Continue disabled. Station 2 Cooling cost exactly 150 credits (1,220 to 1,070), a repeated fitted click could not charge again, and the live summary/Save & Quit/relaunch retained Cooling and the build. The discard option was displayed, not invoked. See the [package 7 receipt](validation/2026-09-13-windows-station-package.json) and [VALIDATION.md](VALIDATION.md) for fixture/assistance limits.

**Earlier package 6 smoke observed:** native Settings/Controls saved mouse 1.2, then replaced the same file with controller 1.2; after a normal process close/relaunch both values displayed 1.2. New Run displayed Wave 1, zero credits, full starting meters and Rapid Laser. Both isolated launches closed normally with no remaining staging files. The [package 6 receipt](validation/2026-09-13-windows-save-package.json) binds the executable, source, content, logs and save hashes. Profile: `Artifacts/PackageSmoke/f6233b51c944457b9f25edfa8cba285b`.

**Earlier package 5 smoke observed:** fresh native menu and New Run/Wave 1 rendered. In Wave 2, the long Salvage Cache offer and E/A prompt remained readable inside the backed/wrapped panel; native E accepted it and changed the label to three remaining objectives. This verifies the label and acceptance transition, not completing its objectives. Evidence directory: `Artifacts/PackageSmoke/5fedd7a0c1964923bd3937e4b159f21a`; `Saved/Logs/PackagedLabels.log`. The separate package 4 profile `57579fdb25bd449ba907598454c4fed4` records startup settings and performance. Earlier package 3 smoke exercised neutral-controls Wave 4 death/results, a fresh-run restart and retained account data after relaunch; that evidence remains tied to its earlier snapshot. Active piloting, natural ten-wave play and offline coverage remain open; package 7 has separate prepared-station Save & Quit/Continue evidence. The finalized package 4 Waves 1–3 capture held approximately 119.96 FPS at 1440p with zero gameplay frames over 16.667 ms; this is limited early-flight evidence. See [PERFORMANCE.md](PERFORMANCE.md).

GameInstance reapplies settings in OnStart after engine initialization. Package 4's fresh log shows all 11 scalability groups at quality 2 on frame 0, correcting the package 3 mismatch between session quality 2 and effective quality 3.

Windows defaults use DX12/SM6 with mesh distance fields enabled for Lumen. DX11/SM5 is also cooked as a fallback; append `-d3d11` to select it. The DX11 fallback has not received a rendered acceptance pass. Both `/Game/SpaceSurvival` and `/Engine/BasicShapes` are always cooked so runtime primitive references, including the station cube floor, have packaged dependencies.

The first package attempt encountered global Live Coding from another editor. The wrapper now passes `-ubtargs=-NoHotReloadFromIDE`, matching the successful editor-build pattern; it does not close unrelated owner sessions or change their Live Coding settings.

## Runtime prerequisite boundary

Package 7 bundled runtime 14.50.35719.0 for compiler 14.51.36257. Packages 8 through 10 replace the x64 installer under `Engine/Extras/Redist/en-us` with Microsoft-signed **14.51.36247.0**, 18,731,856 bytes, SHA-256 `843068991DAAA1F73AD9F6239BCE4D0F6A07A51F18C37EA2A867E9BECA71295C`. Independent inspection verified source/destination equality and Valid Microsoft signatures. The game still has no app-local CRT; no installer or clean-PC launch was run. Microsoft requires matching runtime major and equal-or-newer minor; see [DLL redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute?view=msvc-170), checked 2026-09-13.

The implemented packaging correction retains unique UAT logs under Artifacts/BuildLogs, then invokes `Scripts/BundlePrerequisites.ps1`. The helper binds to the game link response file and matching built/archive executable, corroborates the selected toolchain from the log, checks a compatible Microsoft-signed x64 runtime from that VS installation, copies only into the archive and writes `Artifacts/Windows/Prerequisites.json` with provenance. Missing compatibility fails clearly; no host installation or Engine modification occurs. ARM64 is outside this Windows x64 target.

Packages 8 through 10 exercised the copy/receipt path successfully. `Artifacts/Windows/Prerequisites.json` binds the selected toolchain, UAT log, link response file, game hash, signed runtime source and destination. To inspect candidate selection without changing the archive, use its matching retained UAT log:

```powershell
./Scripts/BundlePrerequisites.ps1 -BuildLog "./Artifacts/BuildLogs/WindowsPackage-b5ba16e6aba94998beddf035bf05017a.log" -DryRun
```

The dry run binds the current built/archive executable and link response file; use a UAT log from that matching build. A historical log can be rejected after newer builds replace those files. Preserve the prerequisite receipt with the package and separately validate clean-PC startup.

## Controls

| Capability | Keyboard/mouse | Controller |
| --- | --- | --- |
| Flight steering / on-foot look | Mouse | Right stick |
| Flight lateral / vertical | A/D and R/F | Left stick |
| Throttle | W/S | D-pad up/down |
| Fire | Left mouse | Right bumper |
| Boost | Shift | Right trigger |
| Heat-limited brake | Space | Left trigger |
| Directional dodge | Q with movement direction | Left bumper with left-stick direction |
| Walk / run | WASD / Shift | Left stick / X |
| Interact / choose | E / Enter | A |
| Shell / back | Escape | Menu / B |

Banking follows steering/lateral movement. Settings expose independent mouse/controller sensitivity dials from 0.3–2.9 in 0.2 steps (upper clamp, then wrap), pitch inversion, boost/brake hold/toggle, subtitles, UI scale, camera shake, blur, volumes, scalability and frame cap. Full remapping is absent; it is not an explicit Phase 1 acceptance requirement.

Package 6 native clicks saved mouse/controller sensitivity 1.2. After normal close/relaunch the isolated Controls menu displayed both 1.2. This verifies persistence, not comfortable steering response.

Normal shell/settings menus pause flight. Depot/reward panels remain live. Their menu controls are consumed separately from flight controls; this recent behavior needs actual input verification.

## Local saves

Slots: `SS_Account_v1`, `SS_Settings_v1`, `SS_Suspend_v1`. The account payload writes version 2 and reads version 1; run/settings/envelope versions remain 1. Use the actual platform `Saved/SaveGames` location for the executable being tested. The Windows generic backend writes verified/flushed sibling temporary files before replacing each live slot; non-Windows or custom backends are rejected. Interrupted temporary files are ignored as saves. There is no multi-slot transaction or automatic backup manager.

Save & Quit is available at stations. Continue consumes the suspension before exposing restored play; death persists XP/run identity and invalidates suspension. Unreadable account data is protected from overwrite and requires a known-good backup for recovery. Use isolated test profiles for failure tests and preserve existing personal saves.

The dedicated lifecycle harness runs preflight plus three fresh Unreal processes using actual GameInstance Init/Suspend/Resume/PersistDeath:

```powershell
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'
```

Use `-PreflightOnly` for the backend/path guard without GameInstance Init or save writes. The normal harness creates a GUID directory under `Artifacts/SaveLifecycle`, verifies the generic SaveGame backend and absence of reparse paths before writes, and checks owner production save hashes before/after. Its successful receipt verifies station fixture persistence, settings, resumed death, 475 XP/both unlocks and fresh-run reset, plus actual locked-suspension/account failures that preserve bytes and succeed after releasing the locks. It does not click station UI or test the packaged executable. See [VALIDATION.md](VALIDATION.md) for the exact token and limits.

For guarded prepared-station UI QA, `TestSaveLifecycle.ps1 -PreparePackagedStation 5` (or 10) runs isolated preflight/preparation and leaves a suspension in its reported GUID UserDir. Fixtures seed build/kills/contract state and mute audio; use fresh ordinary runs for gameplay acceptance. Package 7 consumed them through actual station UI, as recorded in [VALIDATION.md](VALIDATION.md).

Station 2 is a live slice boundary. Its departure panel shows live statistics and services/save/discard without death XP/history. Native summary/save/relaunch and the five-process actual discard failure/retry/reload harness passed. Native discard usability and completion/retry acceptance remain open. No Wave 11 or victory award exists.


## Additional isolated QA modes

```powershell
./Scripts/TestSaveLifecycle.ps1 -StorageFaults
./Scripts/TestSaveLifecycle.ps1 -CorruptAccount
./Scripts/TestSaveLifecycle.ps1 -Station2Discard
```

These are explicit fresh-GUID fault tests against real Windows files/processes, not production saves. The wrapper rejects unsafe/reparse paths, binds the generic backend and checks production hashes before/after. It restores test-owned ACLs/copies and cleans only owned processes/files. The successful eight/four/five-process receipts and precise interruption/domain-corruption limits are in [VALIDATION.md](VALIDATION.md). They do not prove disk-full, short-write, arbitrary malformed-binary or hardware-loss behavior.

For a normal-frame scripted benchmark, use `CaptureEndgame.ps1` without visual readbacks. The following current-source example deliberately requests diagnostic screenshots instead:

```powershell
./Scripts/CaptureEndgame.ps1 -Editor -Scenario Station5 -CaptureVisuals
./Scripts/CaptureEndgame.ps1 -Editor -Scenario Wave10 -CaptureVisuals
```

`-Editor` uses the installed editor's uncooked game mode and current project DLL; omitting it selects the current packaged inner executable. Each launch owns a fresh GUID under Artifacts/EndgameSoak, records exact source/artifact/production-save identities, waits for foreground and requires complete fixture output. Keep the window foreground. Station 5 defaults to 330 seconds timeout, Wave 10 to 240 seconds; cleanup only terminates the owned process. No build, install or package occurs in this wrapper.

`-CaptureVisuals` captures the normal viewport/HUD, pose request metadata and ListTextures without camera/pose overrides. Current source expects 12 Station 5 or 4 Wave 10 images. Readback delays can skip early exit checkpoints; requested times are not proof of rendered poses. These runs are excluded from performance findings even when a CSV/performance.json is produced. Package 11 includes this switch and has a separate visual/residency receipt; Package 10 predates it. See [ENDGAME_CAPTURE.md](ENDGAME_CAPTURE.md) for fixture guards and [PERFORMANCE.md](PERFORMANCE.md) for benchmark limits.
