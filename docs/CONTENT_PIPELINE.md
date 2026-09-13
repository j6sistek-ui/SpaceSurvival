# Phase 1 content pipeline

Status: **PARTIAL — real Unreal assets imported and reloaded successfully; integrated gameplay presentation remains unverified.** UE 5.8.2 became available during the implementation pass at `C:/Program Files/EpicGames2/UE_5.8`. Asset import completed in its real editor through a temporary module-free descriptor while Windows C++ prerequisites were unavailable. The lead subsequently reported a successful real editor module build at the owner-requested reboot checkpoint. The saved `Content/SpaceSurvival` packages are real Unreal assets. `DA_Phase1` and the persistent `Survival` gameplay map still need the full authoring pass after reboot and have not been fabricated.

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
./Scripts/Build.ps1 -Target Content -EngineRoot 'C:/Program Files/Epic Games/UE_5.8'
```

Its direct equivalent is `UnrealEditor-Cmd.exe SpaceSurvival.uproject -unattended -ExecutePythonScript=Scripts/AuthorContent.py` with absolute paths where needed. A `-run=pythonscript` commandlet may have a reduced editor environment; if level-authoring subsystems are unavailable there, use the full Editor path and retain the failure log.

The importer:

1. Rechecks the supplied GLB hash and each committed OBJ/WAV against its source manifest.
2. Creates editable PBR/emissive materials with `Color`, `Tint`, `Metallic`, `Roughness` and `Emission` parameters.
3. Imports OBJ through Unreal's FBX/OBJ factory with supplied normals, centimeter scale, retained material slots and generated simple collision. The distant starfield receives no collision.
4. Copies the default Interchange assets pipeline into the project's own authoring folder, explicitly enables skeletal mesh and animation import, then imports the unchanged GLB. It discovers the real returned skeletal mesh/animation objects, checks counts, renames them to canonical paths, verifies the shared skeleton and nonzero animation duration, and saves associated assets.
5. Imports WAVs with loop properties. All spatial effects are mono; the three music stems are stereo.
6. Creates `DA_Phase1` from the C++ data asset's defaults and creates the persistent `Survival` map with the C++ GameMode override. Runtime gameplay owns player, hazards, station/hangar actors and progression. The map owns a dark background, distant starfield, two directional lights and fixed exposure/bloom.
7. Saves a real import result to `Saved/Validation/ContentImport.json`. Any unsupported operation, missing class, missing asset, unexpected character output or lost material group records an error and fails the run. Other independent import stages are attempted so one unavailable importer does not suppress unrelated work.

Existing authored materials, meshes, data assets and maps are preserved on rerun. WAV loop metadata is reapplied. The `SSAuthoringVersion` asset metadata marker distinguishes completed initial authoring from a partially created object; a missing marker fails closed for manual reconciliation. This is intentionally an initial authoring workflow, not a destructive bulk reimporter. Reimport changed assets deliberately in Editor; do not delete authored work to force reruns. A partial canonical character import stops with a clear reconciliation error. Import success is labeled `IMPORTED_NOT_GAMEPLAY_VALIDATED`.

For asset authoring before the gameplay module can compile, `--assets-only` omits the data asset and map stages and records `ASSETS_IMPORTED_GAMEPLAY_CLASSES_PENDING`. The September 13 import used an ignored temporary `ContentWorkbench.uproject` at repository root with no modules and PythonScriptPlugin, EditorScriptingUtilities, Interchange and InterchangeEditor enabled. AndroidFileServer was explicitly disabled. That descriptor is an authoring workaround, not an alternative game project or playable deliverable. It is removed after authoring. Run the regular content target with the actual game descriptor once its C++ build succeeds.

`Scripts/ValidateContent.py` is a separate read-only editor validation pass intended for a fresh editor process. It loads all expected static meshes and checks built LOD geometry, imported axis/centimeter bounds and material groups; it checks palette material classes, the skeletal mesh/walk/pilot shared skeleton, animation durations, physics asset and materials; and it checks all SoundWave durations, channels, imported sample rates and loop flags. Results go to `Saved/Validation/PersistedContent.json`. These checks establish saved-package integrity; they do not replace rendering, animation playback or game testing.

The Unreal Python APIs were initially checked against Epic's public UE 5.7/5.8 documentation on 2026-09-12: [Interchange import workflow](https://dev.epicgames.com/documentation/unreal-engine/importing-assets-using-interchange-in-unreal-engine), [InterchangeManager](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeManager?application_version=5.7), [generic assets pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericAssetsPipeline?application_version=5.7), [mesh pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericMeshPipeline?application_version=5.7), [DataAssetFactory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/DataAssetFactory). Installed UE 5.8.2 headers and execution then resolved the changed skeletal mesh combine setting: `combine_skeletal_meshes_behavior = BY_SKELETON` replaces the older boolean setting. Data asset and map APIs remain unexercised until the module is available.

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
| `Character` | `SK_Acornaut`, `A_Walk`, `A_Pilot`, plus actual imported skeleton/material/texture/physics assets |
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

Before a build can meet Phase 1 presentation requirements, perform and record: actual GLB import/texture integrity; character forward axis, centimeter scale, skeleton and walking animation playback; visible piloting pose and cockpit/tail clearance; mesh winding, tangent generation and material slot preservation; collision and hazard bounds; full-speed pickup differentiation; station prop integration; starfield behavior across rebases; bloom/exposure against warnings; audio listening and spatialization; simultaneous music-layer transitions; GPU/CPU cost in the Wave 10 compound climax; owner art review against the approved Hybrid direction.

Current generated rocks are modest topology, the palette lacks authored surface texture detail, station props are simple, and the supplied source contains walking animation only. A separate original provisional seated pilot animation has been authored and imported. Additional animation/presentation polish is a remaining Phase 1 requirement, not proof of finished art. The approximate software projection can show sorting artifacts where components intersect; final overlap and z-fighting must be checked in the Unreal renderer.

At the reboot checkpoint, the corrected `A_Pilot` was rendered in real UE 5.8.2 at animation time 1.0 seconds. `UnrealPilotPreview.png` shows an upright seated character with correct body proportions, textured helmet/suit and forward control hands. `Saved/Validation/PilotPreview.json` records the sample: head approximately 32.54 cm above pelvis and foot joints approximately 23.43 cm below it. The pelvis is at the animation origin; a component yaw of -90 degrees faces +X. This corrects a rejected FBX transport that produced joint translations 100 times too small; the retained transport uses original glTF joint bases and metre translations. The source validator verifies that the original nodes, skins, geometry and binary payload are preserved in the transport copy.

That image uses a temporary stock cube seat. Legs/tail intersect the cube; actual cockpit seat height, tail clearance, control placement, walk foot placement and continuous animation playback remain unverified. The current ship hull under the seat is closed geometry, so the pilot cannot simply be placed at the old runtime offset without a clearance pass. `UnrealHeroPreview.png` is an earlier diagnostic character frame, not evidence of walking playback. No integrated-game screenshot or gameplay completion is claimed. The owner requested a reboot immediately after the successful pilot capture, so further authoring and validation stopped there.
