# Local asset refresh

## Provenance and storage

The owner acquired the following Fab products and authorized their use in the refresh on 2026-09-13:

| Product | Source | Local Unreal content root |
|---|---|---|
| Asteroid Library, Makemake | Owner-provided Fab library / local package | `/Game/Asteroid_Library` |
| Sci-Fi / Futuristic Corridor, Leartes Studios | https://www.fab.com/listings/f2f045e8-bbc3-46be-bfcf-f6b3920ac17e | `/Game/SciFiCorridor` |

Original cached packages are preserved at these owner-local paths:

- `C:\Users\j6sis\SpaceSurvival\User downloaded assets\VaultCache\Asteroid1a31297b46f6V1\data\Content\Asteroid_Library`
- `C:\Users\j6sis\SpaceSurvival\User downloaded assets\VaultCache\SciFiFut0522070825dbV1\data\Content\SciFiCorridor`
- Other downloaded formats are under `C:\Users\j6sis\SpaceSurvival\User downloaded assets\VaultCache\FabLibrary`. Their presence does not imply runtime adoption.

`User downloaded assets`, `Content/Asteroid_Library`, `Content/SciFiCorridor`, and `Content/SpaceSurvival/Licensed` are ignored by Git. Raw purchased geometry, textures, vendor maps, and generated derivatives must not be added to the public repository. Source references and placement instructions are tracked. A source checkout alone therefore does not reproduce the licensed presentation. Collaborators need appropriately licensed access to the original products; do not distribute the cache as a substitute.

## Reproduce local staging

1. Obtain the Unreal packages through Fab under an appropriately licensed account. The two cache names above describe this machine; other downloads may have different cache identifiers.
2. With authoring/build processes stopped, copy each complete content-root directory into the project's `Content` directory, preserving its name. The resulting paths must be `Content/Asteroid_Library` and `Content/SciFiCorridor`, not a nested `Content/Content` directory. Preserve the source cache and avoid mirroring/deleting project content. Keeping the original mount paths preserves material/texture references.
3. Run `Scripts/InspectRefreshAssets.py` using the installed Unreal Python workflow from `Scripts/Build.ps1`. Schedule a single authoring process; use a hidden process when unattended. It writes the read-only mesh bounds/material inventory to `Artifacts/Refresh/vendor-meshes.json`.
4. Run `python Scripts/AuthorStationRefresh.py` with the existing Python runtime. It generates `Source/SpaceSurvival/Private/SSStationRefresh.inl` and bounds evidence under `Artifacts/StationRefresh`. Review the text diff if the vendor version changed.
5. Build, cook, and validate the game through the normal project workflow. Inventory or generation success is not a rendering, navigation, or performance pass.

## Station integration

`ASSStation::BuildLicensedShell()` creates eight instanced-mesh batches using 279 placements. It retains the vendor material interfaces and source meshes. The arrangement uses the original 34 by 28 metre deck and service positions, with native-height wall tiers, a broad inbound opening, perimeter dressing and a roof.

The generated code checks package existence before loading meshes, so absent licensed content selects the existing station presentation without missing-package load attempts. A present but corrupt asset can still fail loading and requires repair. All required meshes are resolved before creating presentation components.

The licensed presentation has no collision. The existing station collision, service interactions, ship docking and character movement remain authoritative. The original decorative floor and old shell must be suppressed while the licensed shell is active. Floor top is -7.25 cm; roof underside is 1000 cm in station-local coordinates. A generation-time bounds guard checks the inbound volume. Runtime testing must still verify walls, camera clearance, visibility, services and docking together.

## Known limitations and rejected work

A merged static-shell experiment did not preserve the material slots: Unreal returned WorldGridMaterial. That candidate is rejected; do not use or package `SM_StationRefresh` from the private generated-content directory. The final path uses instanced source meshes instead, reducing duplicate geometry and retaining the original material interfaces.

The text generator and bounds inventory are reproducible tooling, not evidence of visual acceptance. First-person vendor demonstration scenes do not establish third-person navigation quality. Texture memory, material cost, visibility and packaged performance require integrated checks. Paid assets improve the available artwork; they do not establish near-alpha acceptance by themselves.

## Gameplay and character refresh

The depot is an optional stationary signal. Explicit interaction engages a suspended magnetic hold for up to 20 seconds; closing the menu releases it immediately. Director admissions and wave progress stop during the hold, while existing threats remain live and damage still applies. Admission rejects nearby solid hazards and environmental fields. A used depot cannot reset its timer through immediate re-entry. There is no pad or on-foot depot scene.

Both enemy archetypes use hostile HUD identification, with a short kill confirmation. Accepted contracts retain a descriptive progress objective. Soft assistance tapers to zero at its cone boundary and defaults to a 20-percent maximum correction. Existing sensitivity and inversion settings remain persisted.

The wormhole exit applies bounded disturbance followed by recovery and a gradual destination tint change. This does not introduce another galaxy simulation or change the five-wave cadence.

The left leg repair changes left knee and ankle animation rotations in new walk/disembark derivatives. Original mesh, skin weights, bind pose and source clips remain preserved. `Scripts/AuthorHeroLegRepair.py` produces the derivatives with Blender; `Scripts/ImportHeroLegRepair.py` imports only new animation assets and refuses overwriting existing ones. Blender comparison evidence lives under `Artifacts/HeroLegRepair`; integrated animation acceptance remains separate.

## Validation

The final source build and all 39 Unreal integration tests passed with zero failures, warnings or not-run tests. The suite includes the accelerated ten-wave journey, depot release/re-entry and rotating asteroid centering. Initial station validation correctly rejected two unassigned vendor slots; explicit kit material assignments fixed them. Offscreen Station5 reached docking, exit and Station1 with twelve captures. These bounded checks do not establish natural gameplay quality or FPS acceptance.

Offscreen visual fixtures require both `-RenderOffscreen` and `-SSSoakVisuals`. They record `offscreenVisualOnly` and cannot support performance findings. Normal foreground performance-fixture requirements remain unchanged.

## Optional Ludo ship trial

Launch with `-SSShipRefresh` to use the owner's 31,056-triangle ship candidate on the starter chassis. Without that argument the original ship remains selected. The alternative does not change stats, save data or unlocks. Its closed canopy requires hiding the seated flight pilot; the existing on-foot character and exit animation remain. This is a comparison candidate, not an approved replacement for the scoped visible cockpit. The wider hull retains the existing forgiving collision body, so edge contact accuracy remains a trial limitation.

`Scripts/AuthorShipRefresh.py` preserves the source and writes a fitted GLB under `Artifacts/ShipRefresh`. `Scripts/ImportShipRefresh.py` imports it new-only with its PBR material and textures. Source and derivative hashes are recorded locally.

## Delivery and follow-up boundaries

Run `Artifacts/Windows/SpaceSurvival.exe -SaveToUserDir` for the default ship or `Artifacts/Windows/Try New Ship.cmd` for the optional Ludo starter. The launcher adds `-SSShipRefresh -SaveToUserDir`. No itch upload is automatic.

The current restricted itch release remains 0.1.14-alpha until the owner chooses a new publication. This branch is a refresh of the existing Phase1 foundation; it does not close original near-alpha acceptance. Controller/mouse comfort, natural ten-wave balance, audio, retry appeal and representative 60-FPS validation remain open. Docker domain checks could not run because the Docker Linux engine pipe was absent; installed Unreal automation, source checks and the existing Visual Studio formatter were used.

Two original corridor mesh slots were null: the monitor screen now receives `MI_MonitorError_Inst2`, and top wall trim receives `MI_CorridorWall_02`. Overrides affect components only; vendor source packages remain untouched.

The generic depot exterior has not been replaced by the downloaded standalone station GLBs. The optional ship has a closed canopy; cockpit visibility and an appropriate opening/exit animation require further art work. The existing 105cm forgiving flight collider also remains smaller than that trial hull. Ship fill lighting improves deep-shadow readability but does not establish final lighting quality.

Final receipt: [2026-09-14-asset-refresh.json](validation/2026-09-14-asset-refresh.json). Final source milestone `1777db7`; package game SHA256 `70c78997babe5595cda3fb5b1bf6e1d625a6929deb7653b6897ae6061a3929fd`. Final packaged sequence succeeded with twelve captures, no save-slot writes and offscreen-only labeling. Archive size is 1,527,561,532 bytes across 53 files including development files and prerequisites. The 39-test report precedes the last lighting-only adjustment; that adjustment was compiled and checked in the packaged run.
