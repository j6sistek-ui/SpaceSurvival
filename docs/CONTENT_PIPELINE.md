# Phase 1 content pipeline

Status: **PARTIAL — real Unreal content is imported, the native module and Windows package build, and the Survival map/Phase 1 Data Asset pass persisted validation.** UE 5.8.2 is at `C:/Program Files/EpicGames2/UE_5.8`; the owner completed C++/SDK installation and reboot. See [PROJECT_STATE.md](PROJECT_STATE.md) and [VALIDATION.md](VALIDATION.md) for current verification boundaries.

**The owner explicitly rejected the current graphics as far below acceptable.** Generated spacecraft, station and secondary meshes/materials are provisional implementation content, not approved final art. A substantial art replacement pass remains open; preserve the supplied Acornaut. Primitive dressing does not meet near-alpha presentation. No owner touch/feel/audio/replay result has been received; those checks are scheduled in [PLAYTEST_TOMORROW.md](PLAYTEST_TOMORROW.md).

The geometry, material palette and audio are original generated **provisional** content. They establish consistent identifiers, silhouettes and editable sources. They have not met the approved Hybrid art direction or near-alpha quality bar. Source projection checks cannot establish Unreal lighting, texture quality, animation, flight readability or final sound quality.

## Sources and preservation

- `model-rigged.glb` is the supplied rigged Acornaut source. It is preserved byte-for-byte. SHA-256: `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91`.
- `ContentSource/GenerateGeometry.py` creates 26 deterministic OBJ sources and `Palette.mtl`. It uses Python's standard library. No external mesh packs or raster assets are required.
- `Scripts/GenerateAudio.py` creates 10 original PCM WAV sources using mathematical synthesis. There are no sampled third-party recordings.
- `ContentSource/Meshes/manifest.json` records topology, bounds, material names and SHA-256 hashes.
- `ContentSource/Audio/manifest.json` records duration, sample format, loop flags, level measurements and SHA-256 hashes.
- `ContentSource/ValidateSources.py` checks actual OBJ indices, normals, finite coordinates, nonzero triangle area, material references, WAV headers, frame counts, peak headroom, loop boundary discontinuities and the preserved GLB hash. Results are in `ContentSource/source_validation.json`.
- `ContentSource/PreviewGeometry.py` optionally uses an existing Pillow installation to make `ContentSource/GeometryPreview.png`. The image is a software source-geometry projection, **not a game screenshot**. Pillow is not needed to generate or import assets.
- `ContentSource/GeneratePilot.py` uses an already installed Blender to author `ContentSource/Animation/Pilot.glb`, a separate 52-bone, four-second seated pilot animation with forward control hands and restrained breathing/head/arm motion. It samples the supplied rig as a starting point and preserves its source GLB. The transport copy retains the original nodes, skin, geometry, inverse binds and binary payload and appends original authored animation channels in the original glTF joint basis. Unreal imports exactly one `A_Pilot` animation onto the existing character skeleton, without replacing that skeleton or mesh. `Pilot.json` records provenance and source hash. This remains provisional animation requiring cockpit and aesthetic review.
- `ContentSource/PreviewUnreal.py` builds an unsaved stock-actor editor scene and uses Unreal's D3D12 renderer and screenshot API. `UnrealAssetPreview.png` is an actual imported-asset preview, **not SpaceSurvival gameplay**. Optional `--hero` and `--pilot` views isolate the character. Preview actor lights/cameras/floor are discarded and never become the gameplay map.

## Generate source content

From repository root, using existing Python 3 or the Unreal bundled Python:

```powershell
python Scripts/AuthorContent.py --source-only
python ContentSource/ValidateSources.py
```

Generation is deterministic for the same Python/runtime and never writes to the supplied GLB. Geometry output normalizes rounded negative zero so negligible floating-point sign differences between bundled Python and Unreal Python do not cause normal-coordinate churn. Generated source files are intentionally reviewable and committed. Content changes should edit their generator, regenerate, and review the source diffs and preview. Normal engine import consumes and hash-checks the committed sources; it does not regenerate them.

## Import and author real Unreal assets

Build `SpaceSurvivalEditor` first. Enable the project's Python, Editor Scripting Utilities, Interchange and Interchange Editor plugins. The importer requires the reflected classes `/Script/SpaceSurvival.SSPhase1Data` and `/Script/SpaceSurvival.SSGameMode`.

With the project open, use the Output Log's console command (`Cmd`) input and run:

```python
py "C:/path/to/SpaceSurvival/Scripts/AuthorContent.py"
```

The repository build wrapper uses the full Editor scripting path, which supports map authoring:

```powershell
./Scripts/Build.ps1 -Target Content -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'
```

Its direct equivalent is `UnrealEditor-Cmd.exe SpaceSurvival.uproject -unattended -ExecutePythonScript=Scripts/AuthorContent.py` with absolute paths where needed. A `-run=pythonscript` commandlet may have a reduced editor environment; if level-authoring subsystems are unavailable there, use the full Editor path and retain the failure log.

The importer:

1. Rechecks the supplied GLB hash and each committed OBJ/WAV against its source manifest.
2. Creates editable PBR/emissive materials with `Color`, `Tint`, `Metallic`, `Roughness` and `Emission` parameters.
3. Imports OBJ through Unreal's FBX/OBJ factory with supplied normals, centimeter scale, retained material slots and generated simple collision. Map authoring sets both space backgrounds to NoCollision and disables their actor collision.
4. Copies the default Interchange assets pipeline into the project's own authoring folder, explicitly enables skeletal mesh and animation import, then imports the unchanged GLB. It discovers the real returned skeletal mesh/animation objects, checks counts, renames them to canonical paths, verifies the shared skeleton and nonzero animation duration, and saves associated assets.
5. Imports WAVs with loop properties. All spatial effects are mono; the three music stems are stereo. Hero skeletal-material usage, station instanced-static-mesh material usage and directional-light priorities are explicitly authored and saved.
6. Creates `DA_Phase1` from the C++ data asset's defaults and creates the persistent `Survival` map with the C++ GameMode override. Runtime gameplay owns player, hazards, station/hangar actors and progression. The map owns a dark background, distant starfield, two directional lights and fixed exposure/bloom.
7. Saves a real import result to `Saved/Validation/ContentImport.json`. Any unsupported operation, missing class, missing asset, unexpected character output or lost material group records an error and fails the run. Other independent import stages are attempted so one unavailable importer does not suppress unrelated work.

Existing authored materials, meshes, data assets and maps are preserved on rerun. WAV loop metadata is reapplied. The `SSAuthoringVersion` asset metadata marker distinguishes completed initial authoring from a partially created object; a missing marker fails closed for manual reconciliation. This is intentionally an initial authoring workflow, not a destructive bulk reimporter. Reimport changed assets deliberately in Editor; do not delete authored work to force reruns. A partial canonical character import stops with a clear reconciliation error. Import success is labeled `IMPORTED_NOT_GAMEPLAY_VALIDATED`.

`--assets-only` omits map/data stages and reports `ASSETS_IMPORTED_GAMEPLAY_CLASSES_PENDING`. It was used historically through a temporary module-free workbench while the owner installed the toolchain. The normal post-install Content target has since created the map and Data Asset using the actual game project. Use that regular target for current authoring; the historical workbench was not a playable deliverable.

`Scripts/ValidateContent.py` is a separate read-only editor validation pass intended for a fresh editor process. It loads all expected static meshes and checks built LOD geometry, imported axis/centimeter bounds and material groups; it checks palette material classes, the skeletal mesh/walk/pilot shared skeleton, animation durations, physics asset and materials; and it checks all SoundWave durations, channels, imported sample rates and loop flags. Results go to `Saved/Validation/PersistedContent.json`. The wrapper exposes this as `./Scripts/Build.ps1 -Target Validate`; it additionally checks the real map/GameMode class, fixed Data Asset rosters and the scene checks in `ValidateScene.py`. The separate scene validator supports deliberate `--repair` for owned backdrop collision and skeletal/instanced-material usage. The complete fresh-process Validate target passed in `.agent/local/PersistedValidation2.log`, including the repaired saved flags. These checks establish persisted Unreal asset integrity, not visual quality, animation, input or gameplay acceptance. The Windows cook/stage/archive has separately succeeded; a limited packaged menu/launch/death/restart smoke is recorded. Package 3 enables mesh distance fields for Lumen and shows no observed menu warning or station checkerboard.

The Unreal Python APIs were initially checked against Epic's public UE 5.7/5.8 documentation on 2026-09-12: [Interchange import workflow](https://dev.epicgames.com/documentation/unreal-engine/importing-assets-using-interchange-in-unreal-engine), [InterchangeManager](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeManager?application_version=5.7), [generic assets pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericAssetsPipeline?application_version=5.7), [mesh pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericMeshPipeline?application_version=5.7), [DataAssetFactory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/DataAssetFactory). Installed UE 5.8.2 headers and execution then resolved the changed skeletal mesh combine setting: `combine_skeletal_meshes_behavior = BY_SKELETON` replaces the older boolean setting. The normal gameplay authoring pass has now exercised Data Asset and map creation successfully after the module compiled.

## Runtime path contract

All paths below start with `/Game/SpaceSurvival/`. All static source meshes use centimeters, +X forward and +Z up. The world adapter normalizes hazard visuals against loaded mesh bounds so physical radii remain authoritative.

| Folder | Assets and purpose |
| --- | --- |
| `Meshes` | `SM_AcornShip`, `SM_AgileShip`: original acorn-inspired hulls, open pilot area, metallic cap/ribs, engine pods, readable cyan strips; the agile hull is longer and has wider swept fins |
| `Meshes` | `SM_Asteroid`, `SM_AsteroidSmall`, `SM_AsteroidMedium`, `SM_AsteroidMassive`: distinct irregular source shapes around 100 cm radius; runtime determines physical size and behavior |
| `Meshes` | `SM_Debris`, `SM_Wreckage`: authored plate/beam/equipment fragments |
| `Meshes` | `SM_Pursuer`, `SM_Flanker`: the two scoped enemy silhouettes with amber identity strips |
| `Meshes` | `SM_PickupCredit`, `SM_PickupRepair`, `SM_PickupShield`, `SM_PickupBuff`: ring/token, cross, shield plate and chevron, respectively; shape remains a discriminator without color |
| `Meshes` | `SM_Console`, `SM_Crate`, `SM_ServiceArm`, `SM_StationRing`: compact station props and approach ring |
| `Meshes` | `SM_VectorThrusters`, `SM_OverdriveCooling`: reward module presentation assets, not additional mechanics |
| `Meshes` | `SM_StormRing`, `SM_GravityRing`: hollow rings in local YZ plane, outer radius approximately 100 cm; these do not obstruct the warning volume with an opaque sphere |
| `Meshes` | `SM_MobileDepot`, `SM_EventBeacon`, `SM_Projectile`: scoped encounter and combat presentation |
| `Meshes` | `SM_Starfield`: 1,200 triangles across a 40 km sphere, one static mesh with two materials, no collision |
| `Materials` | `M_Hull`, `M_Gold`, `M_Rock`, `M_Cyan`, `M_Amber`, `M_Violet`, `M_Hazard`, `M_Emissive`, `M_Space`, `M_Star`, `M_StarWarm` |
| `Character` | Original walking `SK_Acornaut`, pilot-only corrected-tail `SK_AcornautPilot`, `A_Walk`, `A_Pilot`, plus shared imported skeleton/material/texture/physics assets |
| `Audio` | `Engine`, `Laser`, `Cannon`, `Impact`, `Pickup`, `Alarm`, `Station`, `MusicBase`, `MusicPressure`, `MusicClimax` |
| `Data` | `DA_Phase1`, an instance of `USSPhase1Data` |
| `Maps` | `Survival`, persistent world with `ASSGameMode` override |
| `Authoring` | `P_AcornautImport`, project-owned copy of the engine Interchange import settings |
| `Authoring` | `P_PilotImport`, animation-only pipeline referencing the existing character skeleton, with mesh/material/texture/physics creation disabled |

## Audio integration

All source WAVs are signed 16-bit PCM at 32 kHz. Engine and station ambience loop for 4 seconds. `MusicBase`, `MusicPressure` and `MusicClimax` share a 20-second, eight-bar, 96 BPM grid in D minor. Start all music stems together, keep them playing, and interpolate their volumes as pressure changes. Starting a new stem only when pressure changes loses bar alignment. Station ambience provides a different resting texture; reduce combat stems during breathing windows and stations.

The generator retains authored relative levels and rejects clipping rather than peak-normalizing every effect. It does not replace listening tests. Engine modulation, positional attenuation, weapon tails, repeated alarms, headroom with all three music stems, UI/audio settings and transition behavior require an in-game mix pass.

## Open quality gates

The source projection was inspected for distinct player/enemy/pickup silhouettes and hollow warning rings. Source formats pass the recorded checks. Repeating generation produced byte-identical results across the 39 OBJ/MTL/WAV/manifest files in the same runtime. Real UE 5.8.2 import completed with zero authoring errors; a fresh editor process validated 26 meshes, 11 palette materials, the hero/walk and 10 SoundWaves. The walk sequence is 2.4667 seconds; the imported skeletal bind bounds are approximately 64.0 × 99.8 × 92.1 cm. Those bounds do not establish standing height, facing or cockpit placement during animation.

The import log reported absent FBX smoothing group metadata for OBJ input while explicit source normals were supplied, and the supplied GLB importer reported a skinned node with a parent transform plus a MikkTSpace zero-length normal warning. Import, build and reload still succeeded. These warnings remain reasons to inspect final shading and animated transform behavior. Skeletal build briefly estimated approximately 4 GiB while available memory was below that estimate; no measured runtime memory or FPS claim follows from editor import.

Import, shared skeleton/material references, source integrity and sampled pilot/walker preview fit have recorded evidence. Remaining in-game presentation gates include continuous animation and texture/shading behavior; pilot/cockpit/tail and feet during motion; collision and hazard bounds; full-speed pickup differentiation; station dressing; space backdrop across rebases; bloom/exposure against warnings; audio listening/spatialization and music transitions; measured Wave 10 CPU/GPU cost; and owner art review after replacement against the approved Hybrid direction.

Current generated rocks are modest topology, the palette lacks authored surface texture detail, station props are simple, and the supplied source contains walking animation only. A separate original provisional seated pilot animation has been authored and imported. Additional animation/presentation polish is a remaining Phase 1 requirement, not proof of finished art. The approximate software projection can show sorting artifacts where components intersect; final overlap and z-fighting must be checked in the Unreal renderer.

At the reboot checkpoint, the corrected `A_Pilot` was rendered in real UE 5.8.2 at animation time 1.0 seconds. `UnrealPilotPreview.png` shows an upright seated character with correct body proportions, textured helmet/suit and forward control hands. `Saved/Validation/PilotPreview.json` records the sample: head approximately 32.54 cm above pelvis and foot joints approximately 23.43 cm below it. The pelvis is at the animation origin; a component yaw of -90 degrees faces +X. This corrects a rejected FBX transport that produced joint translations 100 times too small; the retained transport uses original glTF joint bases and metre translations. The source validator verifies that the original nodes, skins, geometry and binary payload are preserved in the transport copy.

That early image used a temporary cube seat and exposed leg/tail overlap. A subsequent cockpit pass produced `ContentSource/GeneratePilotMesh.py` and `Animation/PilotMesh.glb`: a pilot-only derivative correcting selected tail positions/normals/weights while retaining the supplied GLB, original walking mesh, textures, UVs, triangles, materials and shared skeleton. `ImportPilotMesh.py` imports only `SK_AcornautPilot`, reusing the existing skeleton/material and `A_Pilot`. Its receipt records one new mesh and protected-asset hashes.

`ContentSource/PilotMeshFitReview.json` records stock-actor front/rear/side/chase and sampled-cycle review at position (-15, 0, 72) cm, yaw -90 degrees and scale 1.5. The reviewed curl remains upright above the seat and the ship remains dominant. Walker samples retain the original mesh at scale 1, capsule half-height 88 cm and relative mesh Z -23 cm; sampled soles lie approximately -0.89 to +2.10 cm from the preview floor. These are preview-fit measurements, not moving gameplay or disembark acceptance. Original malformed tail limb weights are corrected only for the pilot derivative; remaining root fur is intentionally occluded by the cockpit.

The reviewed pilot derivative and animation are imported and wired into the runtime ship; the original walker remains unchanged. `ContentSource/Shaders/SpaceBackdrop.hlsl` supplies the procedural background, which was seen in a limited actual-game smoke. Package 5 builds and renders its menu/New Run plus the backed/wrapped event label and native acceptance transition. Package 4 separately verifies the corrected OnStart application of all 11 scalability groups at quality 2 and supplies the finalized early-wave performance sample in PERFORMANCE.md. Earlier package 3 smoke records limited death/restart/account retention. These observations and the automated NullRHI journey do not establish natural flight/camera readability, continuous animation quality, audio or representative full-run performance. The owner's graphics rejection remains open until a substantial real art pass is reviewed; no amount of source validation converts provisional geometry into accepted art.

A bounded read-only inventory of known Epic VaultCache and Unreal Projects locations found no downloaded replacement environment pack or Stack O Bot project ready for use. Engine templates/sample-card assets are present but are not selected replacement art. No third-party pack was downloaded, imported or treated as licensed project content.
