# Build and run

**Phase 1 status: PARTIAL.** The editor module and Windows Development package build; persisted content, 12 Unreal tests and the isolated fresh-process GameInstance storage lifecycle pass. A limited packaged menu/launch/death/restart smoke is recorded; natural gameplay, physical input, final art/audio and performance acceptance remain open. See [PROJECT_STATE.md](PROJECT_STATE.md) for the current evidence boundary.

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
git diff --check
```

Portable tests compile the domain and its tests under strict C++17 and ASan/UBSan. They do not compile Unreal adapters or exercise input, rendering or gameplay. Formatting without `-Check` changes source files. Capture the actual result and source revision; a listed command is not a pass record.

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
- **Validate** starts a fresh editor process and checks persisted assets, the real map/GameMode class, fixed tuning rosters, backdrop collision and skeletal/instanced material usage. The complete target passed in `.agent/local/PersistedValidation2.log`.
- **Test** runs the `SpaceSurvival` Unreal automation prefix under NullRHI and writes `Artifacts/UnrealTests/index.json` and `index.html`. The latest suite has 12 successes with zero test warnings/failures: four flight adapters, accelerated ten-wave journey, death/fresh run, late event, station recovery, two admission regressions and two Save tests. NullRHI and shortened/assisted fixtures cannot establish graphics, natural balance, physical input or performance.

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

The wrapper requires the gameplay map, then runs Win64 Development BuildCookRun with build, cook, stage, pak, IoStore and archive enabled. Package 5 succeeded in **67.06 seconds, exit 0**, recorded in `.agent/local/WindowsPackage5.log`. The corresponding editor rebuild succeeded in 6.91 seconds. This package includes the GameInstance OnStart settings correction, mesh distance fields for Lumen and backed/wrapped encounter labels.

Archive: `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`.

**Recorded artifact identity: package 5, source `1ff473f2d37aa4c8e717fea75664eb2dd29dfa31`.** Both executable hashes below were read from the produced archive after the successful build. Keep this identity with the final source/receipt; a later package can replace the shared output path.

| Artifact | Size | SHA-256 |
| --- | --- | --- |
| `Artifacts/Windows/SpaceSurvival.exe` — launcher | 171,520 bytes | `619AC0779DCEABF638639193EFDEA0733E3B4626DEA623C07062F160F5ABCCF8` |
| `Artifacts/Windows/SpaceSurvival/Binaries/Win64/SpaceSurvival.exe` — game | 332,301,312 bytes | `43BC795AC6AE647A59B43FFF5D138F1C8CCCBDC05737EF532CFE399AAB41A45D` |

Keep the entire archive directory together; the launcher alone is not the game. Launch from the repository root:

```powershell
& './Artifacts/Windows/SpaceSurvival.exe' -windowed -ResX=1280 -ResY=720
```

**Package 5 smoke observed:** fresh native menu and New Run/Wave 1 rendered. In Wave 2, the long Salvage Cache offer and E/A prompt remained readable inside the backed/wrapped panel; native E accepted it and changed the label to three remaining objectives. This verifies the label and acceptance transition, not completing its objectives. Evidence directory: `Artifacts/PackageSmoke/5fedd7a0c1964923bd3937e4b159f21a`; `Saved/Logs/PackagedLabels.log`. The separate package 4 profile `57579fdb25bd449ba907598454c4fed4` records startup settings and performance. Earlier package 3 smoke exercised neutral-controls Wave 4 death/results, a fresh-run restart and retained account data after relaunch; that evidence remains tied to its earlier snapshot. Active piloting, natural ten-wave play, offline coverage and packaged station Save & Quit/Continue remain separate gates. The finalized package 4 Waves 1–3 capture held approximately 119.96 FPS at 1440p with zero gameplay frames over 16.667 ms; this is limited early-flight evidence. See [PERFORMANCE.md](PERFORMANCE.md).

GameInstance reapplies settings in OnStart after engine initialization. Package 4's fresh log shows all 11 scalability groups at quality 2 on frame 0, correcting the package 3 mismatch between session quality 2 and effective quality 3.

Windows defaults use DX12/SM6 with mesh distance fields enabled for Lumen. DX11/SM5 is also cooked as a fallback; append `-d3d11` to select it. The DX11 fallback has not received a rendered acceptance pass. Both `/Game/SpaceSurvival` and `/Engine/BasicShapes` are always cooked so runtime primitive references, including the station cube floor, have packaged dependencies.

The first package attempt encountered global Live Coding from another editor. The wrapper now passes `-ubtargs=-NoHotReloadFromIDE`, matching the successful editor-build pattern; it does not close unrelated owner sessions or change their Live Coding settings.

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

A native menu click changed mouse sensitivity from 1.0 to 1.2 and created a settings file. Readback of that preference after UI relaunch remains unverified.

Normal shell/settings menus pause flight. Depot/reward panels remain live. Their menu controls are consumed separately from flight controls; this recent behavior needs actual input verification.

## Local saves

Slots: `SS_Account_v1`, `SS_Settings_v1`, `SS_Suspend_v1`. The account payload writes version 2 and reads version 1; run/settings/envelope versions remain 1. Use the actual platform `Saved/SaveGames` location for the executable being tested.

Save & Quit is available at stations. Continue consumes the suspension before exposing restored play; death persists XP/run identity and invalidates suspension. Unreadable account data is protected from overwrite and requires a known-good backup for recovery. Use isolated test profiles for failure tests and preserve existing personal saves.

The dedicated lifecycle harness runs preflight plus three fresh Unreal processes using actual GameInstance Init/Suspend/Resume/PersistDeath:

```powershell
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'
```

Use `-PreflightOnly` for the backend/path guard without GameInstance Init or save writes. The normal harness creates a GUID directory under `Artifacts/SaveLifecycle`, verifies the generic SaveGame backend and absence of reparse paths before writes, and checks owner production save hashes before/after. Its successful receipt verifies station fixture persistence, settings, resumed death, 475 XP/both unlocks and fresh-run reset. It does not click station UI or test the packaged executable. See [VALIDATION.md](VALIDATION.md) for the exact token and limits.

Station 2 is the current live slice boundary. Services/suspension are available; further launch is disabled. Its explicit abandonment action gives no death XP. This boundary remains an unresolved scope issue.
