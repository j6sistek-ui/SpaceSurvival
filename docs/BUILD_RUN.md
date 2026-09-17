# Build and run

**Start with [Project State](PROJECT_STATE.md#source-build-and-release) for the current source, local package and separately published itch identity.** Older package receipts below are historical evidence, not the current contents of the shared archive. Phase 1 remains PARTIAL.

Play the packaged game at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`, keeping its entire folder. Do not open the `.uproject` just to play: it starts Unreal Editor and may offer a conversion copy. The authoritative project folder is `C:/Users/j6sis/SpaceSurvival`. See [your next review](KNOWN_ISSUES.md#what-to-personally-review-next) and [local-versus-GitHub storage](PROJECT_STATE.md#where-files-live).

## Tooling and repository

Run commands from the repository root, currently `C:/Users/j6sis/SpaceSurvival`.

- Owner-installed Unreal Engine 5.8.2: `C:/Program Files/EpicGames2/UE_5.8`.
- Owner-installed Visual Studio 2026 C++ toolchain: MSVC 14.51.36257, Windows SDK 10.0.26100.0. Builds have succeeded; UBT reports that this compiler is newer than its preferred version. Consult the installed engine's `Engine/Config/Windows/Windows_SDK.json` if changing toolchains.
- Docker Desktop Linux containers supply GCC and clang-format. No host system packages were installed by the implementation.
- Existing Python 3 validates/generates source assets. Blender/Pillow are used by optional source previews; they are not needed to run the game.

The similarly named `C:/Program Files/Epic Games/UE_5.8` directory was an incomplete installation location. Use the complete engine above or pass an explicit `-EngineRoot`.

## Orbital wreck authoring and comparison (target unaccepted)

`PrepareOrbitalWreck.py` runs in the installed Blender background process and writes private broken Station3 sections plus a Figur kit beam. `PreviewOrbitalWreck.py` produces a Blender-only contact sheet. Both preserve supplied sources. After a successful Editor build, execute `AuthorOrbitalWreck.py` through the same Unreal Python runner shown below. It backs up the private look/cloud/sky, imports three derivatives, persists private Nanite material usage, then authors twelve placements and trial lighting/volume settings. It writes private content hashes in `Artifacts/OrbitalWreck/<id>/report.json`. Rerunning resets this trial composition: do not run over unsaved or owner-edited layouts without preserving them. Integration and rendering have run; the concept is still unaccepted under ACT-03.

`./Scripts/CaptureSpaceLook.ps1 -Label OrbitalWreckReview -Sequence` additionally records nominal quarter-second game-view samples from six seconds into the standard fixture. Four required Cruise/Turn/Boost/Brake images remain present. Actual request times/FOV/camera transforms are in `fixture.json`; image hashes and save isolation are checked in `capture.json`. Readbacks perturb frame time and sampling intervals: this is visual sequence evidence, not real-time motion smoothness, FPS or natural-play acceptance. Omit `-Sequence` for the established four-image comparison.

## Spatial areas and alien gallery (development project)

The current source adds four spatial area recipes and an **ALIEN WORLD** review doorway in the home hangar and stations. Use a freshly built Editor game with the owned private content. The existing packaged EXE and published itch build do **not** contain this doorway or these changes; consult [Project State](PROJECT_STATE.md#source-build-and-release) before choosing a build.

Double-click `Play Development Build.cmd` to open the rebuilt game directly. It uses a separate persistent profile under `Artifacts/DevelopmentReviewUser`, preserving the installed game's saves. In the hangar/station, approach **ALIEN WORLD** and press E/A. This launcher requires the local Editor DLL and private content; it does not build or download them.

After `./Scripts/Build.ps1 -Target Editor`, run these scripts **in order**, one completed Unreal editor Python process at a time, using the `-ExecutePythonScript` runner below:

1. `Scripts/AuthorWreckAssemblies.py` — creates private three-dimensional assemblies from owned megastructure meshes in a disposable unsaved map.
2. `Scripts/AuthorSpaceAreas.py` — backs up the private look asset and authors the four recipes using those assemblies and the existing owned asteroid/atmosphere content.
3. `Scripts/AuthorAlienGallery.py` — authors `/Game/SpaceSurvival/Licensed/AlienGallery/DA_AlienGalleryCook`, selecting both complete vendor maps and recursive dependencies for a future licensed cook.

Keep `Content/Megastructure_Scifi_World` intact, including `Level/L_Showcase_level` and `Level/L_assets`. The scripts preserve vendor packages; generated assets and the cook label remain private. Existing Asteroid Library, atmosphere and orbital-wreck derivatives are prerequisites. These authoring scripts intentionally update their private outputs; preserve manual changes before rerunning. Do not run them over an owner's unsaved editor session. A label is cook intent, not evidence that an existing package contains either map.

```powershell
./Scripts/CaptureSpaceLook.ps1 -Label ObsidianArea -Area 0 -Variation 0
./Scripts/CaptureSpaceLook.ps1 -Label AreaVariant -Area 0 -Variation 1
./Scripts/CaptureAlienGallery.ps1 -Label AlienGalleryReview
```

For area comparisons, repeat `CaptureSpaceLook.ps1` with `-Area 0`, `1`, `2` and `3`; `-Variation` selects a repeatable review variation, and `-Sequence` adds sampled motion frames. `-Area -1` retains automatic area selection. These are scripted visual fixtures, not representative performance or physical-input evidence.

The gallery fixture uses a fresh isolated home hangar, the ordinary service interaction, full showcase, asset-layout switch and return. It requires `GalleryDoorway`, `GalleryShowcase`, `GalleryAssets` and `GalleryReturn` PNGs, unchanged encoded run/account state, restored pawn/transform, production-save preservation and exact process/artifact identities. The first capture framed empty floor; corrected capture `3bc9ba3b7f2a42c8a3899b57ae024b38` visibly includes the inventory and passed independent bounded review. Physical input and packaged execution remain unverified. Acceptance belongs in [the active log](KNOWN_ISSUES.md), not the fixture's success flag. See [gallery controls](STATION_EDITING.md#inspect-the-complete-alien-world) for manual inspection.

## Owned asteroid presentation authoring

After the Editor build, execute `Scripts/PreviewAsteroidLibrary.py` through Unreal's editor Python runner for an unsaved native-field audition, then `Scripts/AuthorAsteroidDepth.py` to bake layouts and select 2K BC6H skies. Asteroid Library, NebulaFantasy and the private `DA_DeepSpaceLook` must already exist. These scripts require a rendering-enabled editor, not ordinary Python or NullRHI. Serialize project automation instances.

Example (one script at a time):

```powershell
& 'C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' 'C:/Users/j6sis/SpaceSurvival/SpaceSurvival.uproject' '-ExecutePythonScript=C:/Users/j6sis/SpaceSurvival/Scripts/AuthorAsteroidDepth.py' -unattended -nosplash -RenderOffscreen
```

Authoring backs up four private packages under `Artifacts/AsteroidDepth/<run>/`, preserves existing layout arrays and verifies vendor bytes. `-SSSkyResolution=4096` is an optional comparison; 2048 is the default. `AuthorSpaceVisualPass.py` also selects 2K BC6H for these three derivatives. A separate rendered check is required; authoring does not package or publish. Current evidence and open work remain in VALIDATION and KNOWN_ISSUES.

## Station pit stop authoring (development project, unaccepted)

Added 2026-09-17. The current source composes the station exterior as one body the hangar is cut into and dresses the hangar interior. Nothing here has been packaged or published, and the look is not owner-accepted: the installed package in `Artifacts/Windows` predates this work and still shows the old exterior. Generated outputs under `Artifacts/`, `.agent/local/` and `Content/SpaceSurvival/Licensed/` are git-ignored; only the scripts and the generated collision include are tracked. Open work stays in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

Run the steps **in order**, one completed process at a time:

1. `Scripts/AuthorStationPitStop.py` - Blender 5.1 background process. Reads the owned station kitbash `.blend` from the vault cache (vendor geometry is read, never written), composes the body around the hangar volume, renders ten views and prints its checks; the last check requires 0 body vertices inside the hangar volume. Writes `Artifacts/StationPitStop/<tag>/StationPitStop.glb`, `PitStop.json` and the renders. `--tag` defaults to `default`; the current composition is `keel`.
2. `Scripts/ImportStationPitStop.py -- --tag keel` - editor Python. Clears and reimports `/Game/SpaceSurvival/Licensed/StationPitStop/SM_StationPitStop` through Interchange as one combined static mesh, import scale 0.01 (the composition is authored in centimetres), Nanite on, no collision. It asserts size and X/Z centre against the receipt and records `y_sign` in `Import.json`; the glTF round trip mirrors Y, so the recorded value is -1. Success logs `STATION_PITSTOP_IMPORTED`.
3. `python Scripts/GenerateStationPitStopBoxes.py --tag keel` - plain Python. Refuses to run without an `Import.json` matching the receipt's GLB hash, then writes the tracked `Source/SpaceSurvival/Private/SSStationPitStopBoxes.inl` (13 boxes) with that sign. Do not edit the include by hand; regenerate it.
4. `./Scripts/Build.ps1 -Target Editor` - the include is compiled into `ASSStation` and the station tests, so rebuild after every regeneration. Without the imported asset the hub falls back to the previous exterior (`SM_StationExterior` plus one proxy cube).
5. `python Scripts/PrepareStationPitStopLayout.py` - plain Python, no Unreal. Needs the private `OwnerStationAssets.json` and `EditableLayout.json` under `.agent/local/StationVisualPass` plus `Artifacts/Refresh/vendor-meshes.json`. Writes `.agent/local/StationVisualPass/PitStopLayout.json` (231 parts, 18 lights on 2026-09-17) and asserts the flight lane X -1900..1715, |Y|<=700, Z -10..967.5 stays empty.
6. `Scripts/AuthorStationEditableLayout.py --layout-recipe <absolute path to PitStopLayout.json> --reset-layout` - editor Python. `--reset-layout` rebuilds `BP_StationVisualLayout` from the recipe (483 components from this one) after preserving the prior saved `.uasset` in its receipt directory. It discards manual changes from the active layout: read [Station editing](STATION_EDITING.md#initial-authoring-and-preserving-manual-work) and save/close the Blueprint first. A refused recipe now logs the rule that rejected it (duplicate name, NaN, zero scale, missing mesh, empty material slot, invalid material override, Blueprint compile) instead of returning nothing.
7. `./Scripts/CaptureEndgame.ps1 -Editor -Scenario Station5 -CaptureVisuals` - rendered fixture check of the result; see [Additional isolated QA modes](#additional-isolated-qa-modes) for why both switches are needed.

```powershell
$blender = 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe'
$ueCmd = 'C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$root = 'C:/Users/j6sis/SpaceSurvival'
& $blender --background --factory-startup --python "$root/Scripts/AuthorStationPitStop.py" -- --tag keel
& $ueCmd "$root/SpaceSurvival.uproject" -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser "-ExecutePythonScript=$root/Scripts/ImportStationPitStop.py -- --tag keel"
python Scripts/GenerateStationPitStopBoxes.py --tag keel
./Scripts/Build.ps1 -Target Editor
python Scripts/PrepareStationPitStopLayout.py
& $ueCmd "$root/SpaceSurvival.uproject" -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser "-ExecutePythonScript=$root/Scripts/AuthorStationEditableLayout.py --layout-recipe $root/.agent/local/StationVisualPass/PitStopLayout.json --reset-layout"
./Scripts/CaptureEndgame.ps1 -Editor -Scenario Station5 -CaptureVisuals
```

Headless editor runs share three gotchas:

- **Absolute script path.** A relative `-ExecutePythonScript` path resolves against the engine `Binaries` folder, not the repository root. `Build.ps1` already passes absolute paths; do the same by hand.
- **Script arguments travel inside the same value.** The engine must see `-ExecutePythonScript="<absolute script> <arguments>"`; the September 17 logs record exactly that form in `LogInit: Command Line`. The pit stop import, vault import and catalogue export read only what follows a bare `--`; `AuthorStationEditableLayout.py` uses argparse and takes its flags directly.
- **`-DisablePlugins=UAssetBrowser`.** That third-party plugin crashed once at start-up in its `FExtFolderGatherer` thread (access violation, frame 0, before any project script ran). The headless runs on 2026-09-17 passed the switch; `Build.ps1` does not add it, so check for that frame before blaming a project script.

In editor Python, `unreal.Rotator` positional order is (roll, pitch, yaw); pass `roll=`, `pitch=` and `yaw=` by keyword.

## Prefab catalogue, thumbnails and vault imports

Added 2026-09-17. [PREFAB_LIVE_LINK.md](PREFAB_LIVE_LINK.md) describes the prefab library, the **SS Prefabs** editor menu and the Blender add-on; these are its headless entry points. Everything generated lands under `Artifacts/PrefabLibrary` or `Artifacts/VaultImport` (git-ignored). Imported listings are licensed content and stay out of git; see the `ImportVaultGlb.py` note below for where they land, because one of the two locations is not ignored yet. Prefab recipes are tracked as `Prefabs/<Category>/<Name>.json`; none exist yet. The add-on under `Tools/SSLiveLink` is a package (`ss_live_link/`, v0.3.0) with Types, Send to Unreal, Edit Mesh and Open Scene / Apply; that document is its owner-facing guide, and says what was and was not tested. Install it with `Tools/SSLiveLink/Install Blender Add-on.cmd` (double-click; it runs `install.py` in every Blender under Program Files), then restart Blender; restart the Unreal editor once as well, because `bRemoteExecution` and `Content/Python/init_unreal.py` are read only at start-up.

Meshes sent from Blender land in `/Game/Blender/<Category>/` (`Content/Blender`), outside the always-cooked `/Game/SpaceSurvival` for the same reason as `/Game/Fab`: they ship only when something in the game references them. `Content/Blender/` and the test folder `Content/_SSSelfTest/` are **not git-ignored yet**; until those two lines are added to `.gitignore`, do not `git add -A`. Every asset file an import goes over is first copied to `Artifacts/LiveLink/Backups/<time>/`, and every recipe file Blender's Apply replaces to `Artifacts/LiveLink/Backups/Scenes/`.

Once Blender's Apply has written `Prefabs/Scenes/StationInterior.json`, that file is the station interior's recipe: Blender opens it in place of `PitStopLayout.json`. Step 6 of the pit stop pipeline above (`AuthorStationEditableLayout.py --layout-recipe .../PitStopLayout.json --reset-layout`) then rebuilds the layout from the older generated recipe and discards what was applied from Blender, while Blender goes on showing its own file. Pass `Prefabs/Scenes/StationInterior.json` to step 6 instead, or delete that file on purpose to start again from the generator. In the open editor, `ss_scenes.apply_station_recipe` refuses to rebuild a layout that something other than a recipe has saved since the last build (the Station Workshop, the Blueprint editor) unless called with `force=True` (Blender's Apply Anyway); the headless author script has no such check.

```powershell
$blender = 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe'
$ueCmd = 'C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$root = 'C:/Users/j6sis/SpaceSurvival'
& $ueCmd "$root/SpaceSurvival.uproject" -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser "-ExecutePythonScript=$root/Scripts/ImportVaultGlb.py"
& $ueCmd "$root/SpaceSurvival.uproject" -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser "-ExecutePythonScript=$root/Scripts/ExportPrefabCatalog.py"
& $blender --background --factory-startup --python "$root/Tools/SSLiveLink/render_thumbnails.py"
python Tools/SSLiveLink/build_gallery.py
& $ueCmd "$root/SpaceSurvival.uproject" -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser "-ExecutePythonScript=$root/Scripts/TestPrefabs.py"
& $ueCmd "$root/SpaceSurvival.uproject" -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser "-ExecutePythonScript=$root/Scripts/TestSendScenes.py"
& $blender --background --factory-startup --python "$root/Tools/SSLiveLink/selftest.py" -- --project $root
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python "$root/Tools/SSLiveLink/selftest.py" -- --project $root
```

- **`ImportVaultGlb.py`** imports each Fab listing that exists only as `User downloaded assets/VaultCache/FabLibrary/<Listing>-<hash>/glb/converted/*.glb` as one static mesh, with a receipt in `Artifacts/VaultImport`; rigged listings are forced static. The script committed in `8e90995` targets `/Game/SpaceSurvival/Licensed/Fab/<Name>/SM_<Name>` (git-ignored); a later 2026-09-17 edit changes the target to `/Game/Fab/<Name>/SM_<Name>` because `/Game/SpaceSurvival` is always cooked, and the ten meshes and receipts on disk are at that second location. `Content/Fab/` is git-ignored. An existing target is kept unless `-- --force`; `-- --only <text>` and `-- --skip <text>` filter by name. Of the eleven GLB-only listings in the vault on 2026-09-17, ten have import receipts and Space Station 4 is left alone because it was already imported as `SM_StationExterior`. Success logs `VAULT_GLB_IMPORTED`. Run it before the catalogue export so the new meshes are catalogued. Owned Unreal-format listings whose vault entry is only a launcher manifest cannot be imported this way; only the owner can add them through Fab/Epic.
- **`ExportPrefabCatalog.py`** writes `Artifacts/PrefabLibrary/catalog.json` and glTF proxies under `proxies/<pack>/` (458 meshes on 2026-09-17). The first run takes minutes; existing proxies are kept, so reruns add only what is new. `-- --no-proxies` is the quick variant and `-- --limit N` bounds a trial. It needs the GLTFExporter plugin, which is enabled for the Editor target only. Success logs `PREFAB_CATALOG`. The editor equivalent is SS Prefabs > Rebuild Catalogue.
- **Thumbnails come from the engine.** `ExportPrefabCatalog.py` writes each part's real textured preview through `USSThumbnailLibrary` (`Source/SpaceSurvivalEditor`): textures pinned resident, a full turn of camera yaws tried so one-sided walls face the viewer, drawn at 512 and averaged to 256, exposure lifted, flat `#1b1d22` backdrop. Rows record `"thumb_source": "unreal"` and are kept on later runs; `-- --force-thumbnails` redraws them all. The Blender renderer below is the fallback for a machine without the editor build: its proxies carry no textures, so its pictures are clay shapes.
- **`render_thumbnails.py`** renders a 256x256 PNG per proxy into `Artifacts/PrefabLibrary/thumbs` in one Blender session and rewrites `catalog.json` with the `thumb` entries. Existing thumbnails are kept unless `--force`; `--limit N` and `--only <text>` go after the bare `--`. The last line printed is `THUMBNAILS_OK` with rendered/skipped/failed counts.
- **`build_gallery.py`** is plain Python (no Blender, no Unreal) and writes the offline page `Artifacts/PrefabLibrary/index.html` from the catalogue and any prefab recipes; it fails clearly when no catalogue exists.
- **`TestPrefabs.py`** runs in the unsaved start-up level: save-to-place round trip, live create/move/pull/remove and the rotator formula against the engine. It logs `PREFABS_SELFTEST_OK` or raises; that run passed on 2026-09-17.
- **`TestSendScenes.py`** tests the editor halves of Send to Unreal, Edit Mesh and Open Scene / Apply (`Content/Python/ss_send.py`, `ss_scenes.py`) with files the real add-on makes: it starts headless Blender 5.2 (else 5.1, else the one `SS_BLENDER` names) through `Tools/SSLiveLink/test_send_helper.py`, once per step. It takes two to three minutes, may run beside an open editor (one Unreal commandlet at a time), builds the real 231-part recipe only into scratch copies under `/Game/Blender/_SelfTest`, and must leave `BP_StationVisualLayout.uasset` (sha256), `Artifacts/PrefabLibrary/catalog.json` and `git status` exactly as they were; its assets live under `Content/Blender` and `Content/_SSSelfTest`, never under the always-cooked tree, and a killed run's leftovers are removed by the next run. The last line is `SENDSCENES_TEST_OK {json}` or `SENDSCENES_TEST_FAIL {json}` with every failed check listed; passed 2026-09-17. It does not press any button against an open editor: see the "Not tested" paragraph of the guide.
- **`selftest.py`** is the add-on's own headless check against the real catalogue and station recipe, with a stand-in editor; run it in both Blender versions. The last line is `SSLIVELINK_SELFTEST_OK {json}`; passed in 5.1 and 5.2 on 2026-09-17. `--live` after the bare `--` adds a push/pull round trip against an open editor and has not been run.

The live link uses the engine's Python remote execution, enabled in `Config/DefaultEngine.ini` with multicast 239.0.0.1:6766 bound to 127.0.0.1, so only an editor on this machine can be reached.

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

Portable tests compile the domain and its tests under strict C++17 and ASan/UBSan. They do not compile Unreal adapters or exercise input, rendering or gameplay. `TestCore.ps1` and `Format.ps1` both call `docker build` and `docker run`, so Docker Desktop must be running first; the formatter and GCC check images are cached locally, but the daemon still has to be up. Formatting without `-Check` changes source files. Capture the actual result and source revision; a listed command is not a pass record. Source-format validation writes its routine receipt to Saved/Validation rather than mutating historical source receipts. Fresh-checkout checks use an immutable Git export: uncommitted candidates are not included. The current implementation accepts only exact or complete uniform LF/CRLF forms for UTF-8 OBJ/MTL/JSON; original GLB/binary hashes remain exact.

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
- **Validate** starts a fresh rendering-enabled editor process and checks persisted assets, map/GameMode, fixed rosters/selections, backdrop collision, mesh material usage and compiled field shader statistics. NullRHI cannot supply those shader statistics and is not used for this target. The historical September 13 rendering-enabled readback passed through 13:44:39 UTC in `.agent/local/SkyStation-Validate.log`, with all 120 content files unchanged. The prior 110-asset Package 11 source run remains historical.
- **Test** remains NullRHI and runs the SpaceSurvival automation prefix into Artifacts/UnrealTests/index.json/index.html. It requires a fresh nonempty report, at least one success, zero warnings/failures/not-run cases and every state Success; process exit 0 alone is insufficient. The historical September 13 37-test gameplay result passed at 15:12:50 UTC and is retained in `.agent/local/GameplayFollowup-tests.json`; the prior 24-test Package 11 source result remains in `.agent/local/ChaseAim-tests.json`. Earlier authored-exit contact failures and their correction remain in [VALIDATION.md](VALIDATION.md). Shortened/assisted fixtures do not establish rendering, balance, physical input or performance.

`Scripts/ValidateScene.py`, executed by the editor Python runner, checks saved background collision and skeletal/instanced-material usage. Its `--repair` option intentionally changes those owned assets; omit it for readback validation. Results go to `Saved/Validation/SceneValidation.json`. The latest repair/readback is recorded in [VALIDATION.md](VALIDATION.md).

Open `SpaceSurvival.uproject` in UE 5.8.2 and load `/Game/SpaceSurvival/Maps/Survival`. For a separate development game window:

```powershell
$ueEditor = 'C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$ssProject = Join-Path (Get-Location) 'SpaceSurvival.uproject'
& $ueEditor $ssProject -game -windowed -ResX=1280 -ResY=720 -log
```

This runs the project through the installed editor executable. It is not a packaged build.

For manual station composition, open the populated `BP_StationVisualLayout` Blueprint described in [STATION_EDITING.md](STATION_EDITING.md). Its mesh and light components drive the live station presentation; the create-once authoring script preserves saved manual edits.

## Windows package

```powershell
./Scripts/Build.ps1 -Target Package
```

The wrapper requires the gameplay map, then runs Win64 Development BuildCookRun with build, cook, stage, pak, IoStore, prerequisites and archive enabled. Historical Package 14 succeeded (UAT log: 0h 2m 8s, exit 0; native build 69.48 seconds).

Archive: `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`. Packaging replaces this shared path. Match the receipt linked from [Project State](PROJECT_STATE.md#source-build-and-release), including the inner game and containers; the launcher alone is not a build identity.

The historical Package 13 receipt also binds all five .pak/.utoc/.ucas containers, all 120 project packages plus Engine Cube, 2,184 index rows, prerequisite provenance and copied acknowledgements. Package 13 Wave 10 passed its normal-timing fixture. Package 12 separately retains the preceding Station 1 transition benchmark; that earlier capture does not establish a new Package 13 Station 1 measurement. Exact measurements and their limits belong in [PERFORMANCE.md](PERFORMANCE.md); earlier package results remain historical.

Keep the entire archive directory together; the launcher alone is not the game. Launch from the repository root:

```powershell
& './Artifacts/Windows/SpaceSurvival.exe' -windowed -ResX=1280 -ResY=720
```

## Historical package checks

Package 12/source3536 passed both normal-timing Station 5 and Wave 10 fixtures before the three follow-up fixes. Its [artifact](validation/2026-09-13-windows-gameplay-quality-package.json) and [performance](validation/2026-09-13-gameplay-quality-performance.json) receipts are immutable; the shared archive has since been replaced; use the current Project State pointer.

Package 11/source `6912684223f4a93f4010cd12201aee7fb42395f3` is historical. It built in 87.75 seconds, audited 110 project packages and exercised Station 5/Wave 10 scripted fixtures. Its inner executable was `10b9b664c9a9d7480d96412999dd9da0b33215bc423eaae77a395fde8c9ed32c`; that identity does not describe the current shared archive. See its [retained package receipt](validation/2026-09-13-windows-integrated-presentation-package.json).

Package 9/source 4178 built in 74.18 seconds and audited all 78 project packages/Engine Cube. Native Station 1 showed full 2K deck residency; its full Wave 10 fixture has a separate [package](validation/2026-09-13-windows-visual-package.json) and [performance](validation/2026-09-13-endgame-performance.json) identity. Package 8/source 442ff06 built in 86.44 seconds with 62 project packages plus Cube; its 13-test/524-domain-assertion results remain historical.

**Package 8 exit smoke:** Package 8's guarded SSReviewExit replay visibly reached seated, airborne, landing and full standing poses, suppressed interaction prompts during exit, then allowed service E and departure into Wave 6. It used a prepared station profile and Slomo 0.1, restored to 1 afterward; it does not establish natural docking/camera feel. Neutral Wave 7 death then displayed score 11,800, 510 XP, level 3 and both unlocks from the seeded 100-kill fixture. The owned launch closed normally and production-save hashes remained unchanged. See [VALIDATION.md](VALIDATION.md) and the [package 8 receipt](validation/2026-09-13-windows-exit-package.json) for exact fixture limits and audit provenance. Panorama v1 residency was observed at 2048×1024/12 mips; seams, poles and flight readability remain unaccepted.

**Historical package 7 station smoke:** Package 7 exercised actual prepared-station menus and process restarts. Station 1 Save & Quit/Continue retained 1,070 credits, Hull 145 and Hunter 0/6; departure entered Wave 6. Neutral Wave 7 death awarded 510 XP and both unlocks; a third launch retained 510 XP/highest wave 7/best score 11,800/one run, with Continue disabled. Station 2 Cooling cost exactly 150 credits (1,220 to 1,070), a repeated fitted click could not charge again, and the live summary/Save & Quit/relaunch retained Cooling and the build. The discard option was displayed, not invoked. See the [package 7 receipt](validation/2026-09-13-windows-station-package.json) and [VALIDATION.md](VALIDATION.md) for fixture/assistance limits.

**Earlier package 6 smoke observed:** native Settings/Controls saved mouse 1.2, then replaced the same file with controller 1.2; after a normal process close/relaunch both values displayed 1.2. New Run displayed Wave 1, zero credits, full starting meters and Rapid Laser. Both isolated launches closed normally with no remaining staging files. The [package 6 receipt](validation/2026-09-13-windows-save-package.json) binds the executable, source, content, logs and save hashes. Profile: `Artifacts/PackageSmoke/f6233b51c944457b9f25edfa8cba285b`.

**Earlier package 5 smoke observed:** fresh native menu and New Run/Wave 1 rendered. In Wave 2, the long Salvage Cache offer and E/A prompt remained readable inside the backed/wrapped panel; native E accepted it and changed the label to three remaining objectives. This verifies the label and acceptance transition, not completing its objectives. Evidence directory: `Artifacts/PackageSmoke/5fedd7a0c1964923bd3937e4b159f21a`; `Saved/Logs/PackagedLabels.log`. The separate package 4 profile `57579fdb25bd449ba907598454c4fed4` records startup settings and performance. Earlier package 3 smoke exercised neutral-controls Wave 4 death/results, a fresh-run restart and retained account data after relaunch; that evidence remains tied to its earlier snapshot. Active piloting, natural ten-wave play and offline coverage remain open; package 7 has separate prepared-station Save & Quit/Continue evidence. The finalized package 4 Waves 1–3 capture held approximately 119.96 FPS at 1440p with zero gameplay frames over 16.667 ms; this is limited early-flight evidence. See [PERFORMANCE.md](PERFORMANCE.md).

GameInstance reapplies settings in OnStart after engine initialization. Package 4's fresh log shows all 11 scalability groups at quality 2 on frame 0, correcting the package 3 mismatch between session quality 2 and effective quality 3.

Windows defaults use DX12/SM6 with mesh distance fields enabled for Lumen. DX11/SM5 is also cooked as a fallback; append `-d3d11` to select it. The DX11 fallback has not received a rendered acceptance pass. Both `/Game/SpaceSurvival` and `/Engine/BasicShapes` are always cooked so runtime primitive references, including the station cube floor, have packaged dependencies.

The first package attempt encountered global Live Coding from another editor. The wrapper now passes `-ubtargs=-NoHotReloadFromIDE`, matching the successful editor-build pattern; it does not close unrelated owner sessions or change their Live Coding settings.

## Runtime prerequisite boundary

Package 7 bundled runtime 14.50.35719.0 for compiler 14.51.36257. Package 13 retains the correction introduced in Package 8: it replaces the x64 installer under `Engine/Extras/Redist/en-us` with Microsoft-signed **14.51.36247.0**, 18,731,856 bytes, SHA-256 `843068991DAAA1F73AD9F6239BCE4D0F6A07A51F18C37EA2A867E9BECA71295C`. Independent inspection verified source/destination equality and Valid Microsoft signatures. The game still has no app-local CRT; no installer or clean-PC launch was run. Microsoft requires matching runtime major and equal-or-newer minor; see [DLL redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute?view=msvc-170), checked 2026-09-13.

The implemented packaging correction retains unique UAT logs under Artifacts/BuildLogs, then invokes `Scripts/BundlePrerequisites.ps1`. The helper binds to the game link response file and matching built/archive executable, corroborates the selected toolchain from the log, checks a compatible Microsoft-signed x64 runtime from that VS installation, copies only into the archive and writes `Artifacts/Windows/Prerequisites.json` with provenance. Missing compatibility fails clearly; no host installation or Engine modification occurs. ARM64 is outside this Windows x64 target.

Package 13 independently verified the copy/receipt path, compatible runtime and Microsoft signatures. `Artifacts/Windows/Prerequisites.json` binds the selected toolchain, UAT log, link response file, game hash, signed runtime source and destination. To inspect candidate selection without changing an archive, use its matching retained UAT log. The following is a historical Package 13 example and must not be used against a newer archive:

```powershell
./Scripts/BundlePrerequisites.ps1 -BuildLog "./Artifacts/BuildLogs/WindowsPackage-bbe5c66ccd604a518d096ef1a8834121.log" -DryRun
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

Normal shell/settings menus pause flight. The depot now uses an aboard-ship magnetic service lock (up to 20 seconds); closing its panel releases the ship, and mooring grants no wave progress. Reward panels retain live flight. Physical-device menu behavior remains open in ISS-13 / PT-08 and PT-16.

## Local saves

Slots: `SS_Account_v1`, `SS_Settings_v1`, `SS_Suspend_v1`. The account payload writes version 3, which appends the four paint-bay choices (-1 for factory finish, 0-9 for a colour; out-of-range values are refused), and still reads versions 2 and 1 as the factory finish; run/settings/envelope versions remain 1. Use the actual platform `Saved/SaveGames` location for the executable being tested. The Windows generic backend writes verified/flushed sibling temporary files before replacing each live slot; non-Windows or custom backends are rejected. Interrupted temporary files are ignored as saves. There is no multi-slot transaction or automatic backup manager.

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

`-Editor` uses the installed editor's uncooked game mode and current project DLL; omitting it selects the current packaged inner executable. Each launch owns a fresh GUID under Artifacts/EndgameSoak, records exact source/artifact/production-save identities and requires complete fixture output. Visual captures launch hidden with `-RenderOffscreen -ForceRes` and do not require focus. Runs without `-CaptureVisuals` still require foreground: focus the owned game window within 60 seconds and keep it foreground for the timing fixture. Station 5 defaults to 330 seconds timeout, Wave 10 to 240 seconds; cleanup only terminates the owned process. No build, install or package occurs in this wrapper.

As of 2026-09-17 both switches matter for the station pit stop work. The default mode runs the packaged build in `Artifacts/Windows`, which predates that work and still shows the old exterior, so only `-Editor` (receipt mode `UncookedEditorGame`) renders the current source. Without `-CaptureVisuals` the wrapper opens a window that asks for focus, which an unattended run cannot give. Two `-Editor -Scenario Station5 -CaptureVisuals` runs reported success that day: `Artifacts/EndgameSoak/a495a8bb393243dfa7f9349e2d5df40f`, then `Artifacts/EndgameSoak/df3bbc149c764c9995700b5ae0e19182` after the lane/frame lights were dimmed and the gantry legs removed. They are rendered fixture evidence only: not natural play, not 60 FPS acceptance and not owner acceptance of the look.

Current `-CaptureVisuals` source requires exactly **16 Station 5 images**: Flight, Climax, Wormhole, Approach, Docking, Exit0-Exit6, StationIdle, StationServices, StationOverview and CombatImpact. Wave 10 requires exactly four: Flight, Climax, Compound and Approach. The wrapper checks names, PNG dimensions and request metadata. StationServices and StationOverview use labeled fixture review cameras without changing possession; the other frames retain the normal viewport/HUD. CombatImpact must identify a live enemy-explosion effect 0.15-0.65 seconds after an actual weapon kill. Pose requests do not override animation, and requested exit times are not proof of the rendered pose.

Visual runs also request ListTextures and are excluded from performance findings even when a CSV/performance.json is produced. The executable must contain the matching capture implementation; these current-source instructions do not establish which historical package supports the complete image set. Package 12 introduced the earlier visual switch, and its normal-timing Station 5 fixture does not establish a visual readback. See [ENDGAME_CAPTURE.md](ENDGAME_CAPTURE.md) for the underlying fixture and historical receipts, and [PERFORMANCE.md](PERFORMANCE.md) for benchmark limits.

## Station Workshop editor setup

After restoring the private station content, run `Scripts/Build.ps1 -Target Editor`, then `Scripts/OpenStationWorkshop.ps1 -Prepare` once. Double-click `Open Station Workshop.cmd` for subsequent editing; an already-open editor is reused through Tools > Station Workshop. Preparation preserves existing presets and the saved map. See [Station editing](STATION_EDITING.md) for the source-map/derived-Blueprint and package boundaries. `Scripts/ValidateStationWorkshop.py` is a bounded integration fixture for a freshly prepared development workshop, not a command owners need for routine edits.
