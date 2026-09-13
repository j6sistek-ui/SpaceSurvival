# AcornShip candidate source and Unreal import

This is a separate authored replacement candidate for the initial acorn ship. The lead reviewed the source renders as an improvement worth inspecting in Unreal. The owner has not accepted its art quality, and these studio renders are not gameplay captures.

The seed body uses curved ceramic plates with physical seams and a scalloped bronze aft cap. Beveled champagne trim, graphite cockpit structure, titanium nozzles and restrained cyan navigation/engine details separate the materials. The low curved windscreen and open cockpit keep Acornaut visible. Existing character and tail files remain unchanged.

## Review package

- `../GenerateAcornShipCandidate.py`: editable Blender authoring code.
- `AcornShipCandidate.blend`: 185 authored ship parts plus studio lights/floor/camera, no character rig or image files embedded. Fresh reload verified this.
- `AcornShipCandidate.glb`: one merged ship mesh, nine material primitives, no skin, animation or images.
- `AcornShipCandidate.obj` and `.mtl`: merged import source, centimetres, +X forward, +Z up, evaluated corner normals and nine named material groups.
- `Hero.png`, `Chase.png`, `Side.png`, `Cockpit.png`, `EngineDetail.png`: five purposeful 1800x1200 Blender Cycles studio views. The hero is loaded transiently only while rendering.
- `Report.json`, `SourceValidation.json`, `BlendReload.json`: source dimensions, PBR values, hashes and independent file/reload checks.
- `AcornShipImport.json`, `AcornShipPersisted.json`: actual isolated Unreal import and fresh-editor reload results, copied from Saved/Validation without raw logs.

## Bounds, materials and integration contract

Source bounds in centimetres are `(-244.799995, -142.784309, -65.377539)` to `(209.999991, 142.784309, 97.800082)`. These stay within the original `(-247, -145, -66.516)` to `(210, 145, 100)` envelope. The engine reload matches source axes and bounds within 0.03 cm. The pivot remains world/local zero.

The pilot remains at `(-15, 0, 72)` cm, Unreal mesh yaw `-90`, uniform scale `1.5`. The preview uses the existing PilotMesh plus Pilot animation time zero. Hands float somewhat around the control grips, especially the open palm. Tail artifacts remain visible. This does not establish contact fit through the entire pilot or disembark animation.

The real asset is `/Game/SpaceSurvival/Meshes/SM_AcornShipV2`. Its nine materials are `/Game/SpaceSurvival/Materials/M_AcornV2_` followed by `WarmCeramic`, `IvoryPanels`, `BurnishedBronze`, `ChampagneEdges`, `GraphiteStructure`, `CockpitPadding`, `MachinedTitanium`, `IonAndNav`, and `Windscreen`. Preserve all imported slots; overriding with legacy hull/gold materials would flatten this palette.

Unreal preserves the recorded linear base colors, metallic values and roughness. Six opaque surfaces add only +/-0.008 roughness modulation from one level of 3D texture noise. The 2026-09-13 repair in `NormalDiagnostics/Review.md` corrected two disconnected graph inputs so the noise now receives object-local position; packaged motion/rebasing appearance remains to be reviewed. Cyan emission is 3.5. Glass uses its own two-sided translucent surface material at opacity 0.18, without screen-space refraction; it is an Unreal readability approximation of the Blender transmission shader, not an exact match. Blender procedural micro-bump is not transferred.

The mesh has no generated simple collision, no section collision, and a `NoCollision` body profile. The existing native ship collision body still governs gameplay. Runtime code and original mesh/material/character packages were not edited by this candidate pipeline; all 63 existing noncandidate content packages retained their hashes during import.

## Actual checks and limits

Source GLB checks found one mesh, nine material primitives, 82,859 exported vertices, 134,678 triangles, finite coordinates/normals and maximum normal-length error 0.000000131. Fresh Unreal reload found 79,268 LOD0 vertices and 134,262 triangles, one LOD and nine material sections, with errors empty. The 416-triangle difference is about 0.31%. The source contains 276 exact zero-area triangles and 404 triangles with nearly coincident vertices; the difference is consistent with importer degeneracy cleanup, but the exact removed-triangle correspondence has not been proven. Geometry was not changed solely to make counts match.

Source render inspection corrected cap-row surface overlap and incomplete overview framing. The final five views show the cap/body silhouette, cockpit and recessed engine rings. Side.png retains a studio floor horizon; it is not an asset seam. Existing pilot palms/control contact and tail defects are unresolved. At the initial import checkpoint no in-engine rendered appearance was verified. Subsequent native stock-actor diagnostics are recorded in `NormalDiagnostics/Review.md`; they do not establish acceptance of shadows, translucency sorting, full animation clearance, LOD transitions, actual draw cost, shader cost or frame times. Nine sections and a single 134k-triangle LOD warrant measurement before fleet/station-scale reuse. Native collision is independent, so this candidate does not itself validate collision feel.

## Reproduce

From repository root using the installed tools:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --factory-startup --python ContentSource/GenerateAcornShipCandidate.py
& 'C:\Program Files\EpicGames2\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' SpaceSurvival.uproject -unattended -ExecutePythonScript=Scripts/AuthorAcornShip.py
& 'C:\Program Files\EpicGames2\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' SpaceSurvival.uproject -unattended -ExecutePythonScript=Scripts/ValidateAcornShip.py
```

Use absolute project/script paths if the working directory differs. The generator overwrites only its separate candidate outputs. Import refuses a changed source against a completed candidate hash; deliberate reviewed reimport is required after a source revision. Unreal can return exit code zero on a Python failure, so inspect fresh receipts and log success markers. `AuthorAcornShip.py` does not wire gameplay; lead-owned runtime integration and actual rendered inspection are subsequent steps.
