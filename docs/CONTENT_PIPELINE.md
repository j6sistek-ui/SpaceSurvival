# Phase 1 content pipeline

Status: **PARTIAL — source assets generated and checked; Unreal import and in-game presentation unverified.** The machine used for this pass has no usable Unreal Editor, UnrealBuildTool or Windows packaging toolchain. No `.uasset` or `.umap` substitutes have been written. The scripts must run inside a built Unreal Editor project to produce real engine assets.

The geometry, material palette and audio are original generated **provisional** content. They establish consistent identifiers, silhouettes and editable sources. They have not met the approved Hybrid art direction or near-alpha quality bar. Source projection checks cannot establish Unreal lighting, texture quality, animation, flight readability or final sound quality.

## Sources and preservation

- `model-rigged.glb` is the supplied rigged Acornaut source. It is preserved byte-for-byte. SHA-256: `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91`.
- `ContentSource/GenerateGeometry.py` creates 26 deterministic OBJ sources and `Palette.mtl`. It uses Python's standard library. No external mesh packs or raster assets are required.
- `Scripts/GenerateAudio.py` creates 10 original PCM WAV sources using mathematical synthesis. There are no sampled third-party recordings.
- `ContentSource/Meshes/manifest.json` records topology, bounds, material names and SHA-256 hashes.
- `ContentSource/Audio/manifest.json` records duration, sample format, loop flags, level measurements and SHA-256 hashes.
- `ContentSource/ValidateSources.py` checks actual OBJ indices, normals, finite coordinates, nonzero triangle area, material references, WAV headers, frame counts, peak headroom, loop boundary discontinuities and the preserved GLB hash. Results are in `ContentSource/source_validation.json`.
- `ContentSource/PreviewGeometry.py` optionally uses an existing Pillow installation to make `ContentSource/GeometryPreview.png`. The image is a software source-geometry projection, **not a game screenshot**. Pillow is not needed to generate or import assets.

## Generate source content

From repository root, using existing Python 3 or the Unreal bundled Python:

```powershell
python Scripts/AuthorContent.py --source-only
python ContentSource/ValidateSources.py
```

Generation is deterministic for the same Python/runtime and never writes to the supplied GLB. Generated source files are intentionally reviewable and committed. Content changes should edit their generator, regenerate, and review the source diffs and preview.

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

1. Rechecks the supplied GLB hash and generates source geometry/audio.
2. Creates editable PBR/emissive materials with `Color`, `Tint`, `Metallic`, `Roughness` and `Emission` parameters.
3. Imports OBJ through Unreal's FBX/OBJ factory with supplied normals, centimeter scale, retained material slots and generated simple collision. The distant starfield receives no collision.
4. Copies the default Interchange assets pipeline into the project's own authoring folder, explicitly enables skeletal mesh and animation import, then imports the unchanged GLB. It discovers the real returned skeletal mesh/animation objects, checks counts, renames them to canonical paths, verifies the shared skeleton and nonzero animation duration, and saves associated assets.
5. Imports WAVs with loop properties. All spatial effects are mono; the three music stems are stereo.
6. Creates `DA_Phase1` from the C++ data asset's defaults and creates the persistent `Survival` map with the C++ GameMode override. Runtime gameplay owns player, hazards, station/hangar actors and progression. The map owns a dark background, distant starfield, two directional lights and fixed exposure/bloom.
7. Saves a real import result to `Saved/Validation/ContentImport.json`. Any unsupported operation, missing class, missing asset, unexpected character output or lost material group records an error and fails the run. Other independent import stages are attempted so one unavailable importer does not suppress unrelated work.

Existing authored materials, meshes, data assets and maps are preserved on rerun. WAV loop metadata is reapplied. The `SSAuthoringVersion` asset metadata marker distinguishes completed initial authoring from a partially created object; a missing marker fails closed for manual reconciliation. This is intentionally an initial authoring workflow, not a destructive bulk reimporter. Reimport changed assets deliberately in Editor; do not delete authored work to force reruns. A partial canonical character import stops with a clear reconciliation error. Import success is labeled `IMPORTED_NOT_GAMEPLAY_VALIDATED`.

The Unreal Python APIs used here were checked against Epic's public UE 5.7/5.8 documentation on 2026-09-12: [Interchange import workflow](https://dev.epicgames.com/documentation/unreal-engine/importing-assets-using-interchange-in-unreal-engine), [InterchangeManager](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeManager?application_version=5.7), [generic assets pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericAssetsPipeline?application_version=5.7), [mesh pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericMeshPipeline?application_version=5.7), [DataAssetFactory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/DataAssetFactory). Documentation review is not an executed import test; installed-version differences remain possible.

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
| `Character` | `SK_Acornaut`, `A_Walk`, plus actual imported skeleton/material/texture/physics assets |
| `Audio` | `Engine`, `Laser`, `Cannon`, `Impact`, `Pickup`, `Alarm`, `Station`, `MusicBase`, `MusicPressure`, `MusicClimax` |
| `Data` | `DA_Phase1`, an instance of `USSPhase1Data` |
| `Maps` | `Survival`, persistent world with `ASSGameMode` override |
| `Authoring` | `P_AcornautImport`, project-owned copy of the engine Interchange import settings |

## Audio integration

All source WAVs are signed 16-bit PCM at 32 kHz. Engine and station ambience loop for 4 seconds. `MusicBase`, `MusicPressure` and `MusicClimax` share a 20-second, eight-bar, 96 BPM grid in D minor. Start all music stems together, keep them playing, and interpolate their volumes as pressure changes. Starting a new stem only when pressure changes loses bar alignment. Station ambience provides a different resting texture; reduce combat stems during breathing windows and stations.

The generator retains authored relative levels and rejects clipping rather than peak-normalizing every effect. It does not replace listening tests. Engine modulation, positional attenuation, weapon tails, repeated alarms, headroom with all three music stems, UI/audio settings and transition behavior require an in-game mix pass.

## Open quality gates

The source projection was inspected for distinct player/enemy/pickup silhouettes and genuinely hollow warning rings. Source formats pass the recorded checks. Repeating generation produced byte-identical results across all 39 OBJ/MTL/WAV/manifest files. All five Python scripts passed syntax compilation. No engine execution is claimed.

Before a build can meet Phase 1 presentation requirements, perform and record: actual GLB import/texture integrity; character forward axis, centimeter scale, skeleton and walking animation playback; visible piloting pose and cockpit/tail clearance; mesh winding, tangent generation and material slot preservation; collision and hazard bounds; full-speed pickup differentiation; station prop integration; starfield behavior across rebases; bloom/exposure against warnings; audio listening and spatialization; simultaneous music-layer transitions; GPU/CPU cost in the Wave 10 compound climax; owner art review against the approved Hybrid direction.

Current generated rocks are modest topology, the palette lacks authored surface texture detail, station props are simple, and the supplied source contains walking animation only. Additional animation/presentation polish is a remaining Phase 1 requirement, not proof of finished art. The approximate projection can show sorting artifacts where components intersect; final overlap and z-fighting must be checked in the Unreal renderer.
