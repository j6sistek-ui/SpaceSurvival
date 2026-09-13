# Build and run

> Reboot checkpoint, 2026-09-13 04:35 UTC: the editor C++ build **succeeded** using MSVC14.51.36257 and Windows SDK10.0.26100.0; earlier missing-toolchain statements below are historical and superseded. Current portable tests pass372 assertions in each strict/sanitizer build. Gameplay content creation, Unreal save-test execution, package and player validation remain pending. See [PROJECT_STATE](PROJECT_STATE.md) for resume order.

## Present delivery boundary

The repository is a source implementation with imported art/audio `.uasset` files. No gameplay `.umap`, compiled game module or packaged Windows build is claimed. Initial UE folders contained plugin/installation metadata only. Full UE5.8.2 subsequently appeared at `C:/Program Files/EpicGames2/UE_5.8`, enabling real asset import and header checks. The fresh editor build reaches UBT, but stops at missing Win64 SDK validation (minimum10.0.19041.0); MSVC remains absent.

## Tooling

- Full Unreal Engine 5.8, including editor, UBT/UHT, automation tool, engine headers and Windows platform support.
- Visual Studio C++ game-development toolchain and Windows SDK compatible with the installed engine. Follow that engine's prerequisite check; none were installed by this implementation session.
- Docker Desktop for portable C++ checks. The `gcc:14-bookworm` container supplies the compiler; no compiler/system packages are installed on the host.
- Python 3 for deterministic source generation/validation. Standard-library audio/geometry generation works offline; preview rendering additionally uses existing Pillow/Blender.

## Portable rules verification

From the repository root, run `./Scripts/TestCore.ps1`. It builds the exact `Source/SpaceSurvival/Domain` and `Tests` files, compiles with strict warnings, and executes both ordinary and AddressSanitizer/UndefinedBehaviorSanitizer binaries. This is not an Unreal compilation or gameplay test.

Run `python Scripts/CheckProject.py` and `python -m compileall -q Scripts ContentSource` for source checks. `python ContentSource/ValidateSources.py` checks authored OBJ/WAV formats and the original character hash. GitHub Actions repeats the core and structural checks for the PR.

## Unreal workflow

1. Set `-EngineRoot` to a complete engine directory, not an Epic plugin folder. Run `./Scripts/Build.ps1 -Target Editor -EngineRoot '<engine>'`.
2. Run `./Scripts/Build.ps1 -Target Content -EngineRoot '<engine>'`. This imports the preserved GLB, original OBJ/WAV sources, creates materials and `DA_Phase1`, then creates `/Game/SpaceSurvival/Maps/Survival`. Inspect `Saved/Validation/ContentImport.json`; only `IMPORTED_NOT_GAMEPLAY_VALIDATED` with no errors establishes import success. No substitute assets are written on failure.
3. Open `SpaceSurvival.uproject`, load Survival, and inspect character orientation, imported material groups, collision and camera composition. See the content pipeline's idempotency and partial-import rules before rerunning it.
4. Run `./Scripts/Build.ps1 -Target Test -EngineRoot '<engine>'` for the native SaveGame serialization test. Reports belong under `Artifacts/UnrealTests`.
5. Exercise the manual validation protocol. Then run `./Scripts/Build.ps1 -Target Package -EngineRoot '<engine>'`. The configured artifact location is `Artifacts/Windows`; it does not currently contain a successful package.
6. Test the packaged executable again, including application close/relaunch. Editor success does not establish packaged behavior.

The source is associated with UE5.8 and asset import ran in installed5.8.2. The installed engine's `Engine/Config/Windows/Windows_SDK.json` prefers SDK10.0.22621.0 and contains exact supported/banned MSVC versions. Use that file when provisioning build tools. Runtime API compatibility remains unverified until UHT and the Windows compiler run.

## Controls

| Capability | Keyboard/mouse | Controller |
|---|---|---|
| Flight steering / on-foot look | Mouse | Right stick |
| Flight lateral / vertical | A/D and R/F | Left stick |
| Throttle | W/S | D-pad up/down |
| Fire | Left mouse | Right bumper |
| Boost | Shift | Right trigger |
| Heat-limited brake | Space | Left trigger |
| Directional dodge | Q with movement direction | Left bumper with left-stick direction |
| Walk | WASD | Left stick |
| Run on foot | Shift | X / left face button |
| Interact / choose | E / Enter | A / bottom face button |
| Shell / back | Escape | Menu / B |

Banking is coupled to steering/lateral movement. Independent manual roll is not implemented. Mouse and controller sensitivity, pitch inversion, boost/brake hold/toggle, subtitles, UI scale, shake, blur, volume, quality and frame cap are available in source UI. They require functional input/accessibility verification.

Ordinary shell/settings menus pause active flight. Depot and secured-reward interactions remain in the moving universe. The hangar provides physical loadout points plus launch shortcuts.

## Local saves

Unreal SaveGame slots use `SS_Account_v1`, `SS_Settings_v1`, and `SS_Suspend_v1` (normally the platform's project Saved/SaveGames directory). Back up the directory before manual validation. Suspended runs are offered only from station snapshots; continuing durably invalidates that snapshot before restoring play. Death records its run ID with account XP and invalidates any stale suspension. Corrupt account data is protected from automatic overwrite; recovery currently requires restoring a known-good local backup while the application is closed.

Station 2 is the authored Phase 1 boundary. It offers services and suspension. The shell can explicitly abandon that slice without death XP and return to a fresh hangar; no final-wave victory or further authored content is fabricated.
