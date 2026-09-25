# Building library

Use the outpost authoring checkout at `C:/Users/j6sis/SpaceSurvival/Artifacts/Worktrees/asteroid-outpost`. Double-click **Edit Outpost Sandbox.cmd** there. It opens that checkout and `/Game/OutpostSandbox/L_AsteroidOutpost` in Unreal Editor.

**Verified locally:** 42 placement assets and the 1,150-row ULAT palette are saved. Fresh loading and movement checks passed for the 41 building assemblies and the complete Cargo Level Instance. See the [focused receipt](validation/2026-09-24-building-library.md) for preview evidence and remaining collision/performance limits.

## Place a complete assembly

Open the Content Browser and select the local collection **SS_01_Assembled___Drag_These**. You can also browse **Content → BuildingLibrary → Assembled**. Drag one Blueprint into the viewport; its pieces move together as one actor.

The 42 generated Blueprints include:

- **Windows:** 30 Genesis frame-and-surface combinations, with glass or digital panels in several sizes.
- **Screens:** six Genesis graphic screens and the P3 complete three-part screen.
- **Workstations:** Goliath complete workstation, P3 complete computer bank, and P3 console with chair.
- **Chairs:** P3 complete chair.
- **Ships:** Cargo ship as a Level Instance Blueprint, containing its full authored interior, local lighting and gate Blueprints.

These are reusable visual assemblies. New groups do not gain door movement or other interaction automatically. To change a shared assembly without affecting its other instances, duplicate its Blueprint into your own folder before editing it. Keep vendor originals intact.

**Cargo ship:** find **BP_CargoShip_Complete** under **Assembled → Ships**. Its private level retains 2,078 actors; the vendor's global environment, camera/sequence rig and grouping actors were removed. Its footprint is approximately **29.8 × 65.1 metres**. Fresh single-placement loading/movement checks pass; the receipt separates preview review from gameplay acceptance. This is a heavy art asset: one pod alone has approximately **8.86 million source triangles**. That is an asset-complexity figure; frame rate and suitability for repeated placement have not been measured.

## Use ULAT for individual pieces

On the main toolbar after **Play**, open **Ultimate Level Art Tool → Modular Building**. Choose **Modular** for building pieces or **Props** for screens, light fixtures, furniture and other props. The prepared group names are **Buildings and Structure**, **Screens and Displays**, **Light Fixtures**, **Furniture and Workstations**, **Ships and Vehicles**, and **Props and Details**.

The palette now contains **1,150 entries: 1,146 added and all four existing entries preserved**. Click a thumbnail, move into the viewport and left-click to place it. Press **Esc** when finished. Close and reopen the ULAT panel if it was open during configuration.

ULAT's palette accepts Static Mesh assets. Use the Content Browser collection above for complete Actor Blueprints.

## Save your own reusable assembly

**Ctrl+G** groups selected actors for convenient movement within the level. The group is saved with that level, but it does not create a reusable Content Browser asset. **Shift+G** ungroups it.

To create a persistent Blueprint from static pieces:

1. Duplicate the pieces into a scratch map, arrange them, then select only the pieces belonging to the assembly.
2. Open **Blueprints → Convert Selection to Blueprint Class...** on the main toolbar. Select **Harvest Components** in **Create Blueprint From Selection**.
3. Set **Blueprint Name** and **Path**, choose **Actor** as the parent class, then click **Select**. Unreal replaces the selected scratch actors with one Blueprint instance.
4. Save the new Blueprint. Drag it from the Content Browser into the outpost and check its position, scale and collision before using more copies.

Harvest Components preserves the selected visual components; it does not transfer separate actors' gameplay logic. Keep existing interactive vendor Blueprints intact.

## Downloaded content and storage

This import batch belongs to the outpost checkout: **Rocket** furniture/lights/props, **CyberpunkRestaurant** (Nova Space Burgers), and **CargoShip**. Their original downloads remain under `C:/Users/j6sis/Downloads/down`. Portal and Solar helper content uses separate `/Game/ImportedLibrary/Portal` and `/Game/ImportedLibrary/Solar` roots to keep their references distinct.

Some downloads are materials, textures or effect resources rather than standalone meshes. Apply a material to compatible geometry or use the supplied effect asset; a material thumbnail does not represent a complete placeable object. Only Static Mesh assets appear in ULAT's placement palette.

Use the local collections **SS_New___Furniture_Lights_and_Props**, **SS_New___Nova_Space_Burgers**, **SS_New___Cargo_Ship**, and **SS_New___Solar_and_Portal_Materials** to browse this batch. Imported content is not automatically placed in the outpost or included in a packaged game.

The assembly assets and local collections are private local data. The collections live in `Saved/Collections`; keep them with the project's private assets when backing up the library.

ULAT's palette data is stored in the installed engine plugin and is **shared across projects using that engine**. It is not a project-private library. Configuration backs up its original data assets and table under `Artifacts/PrefabLibrary/ULATBackups/<run>/` before saving changes. Reports live beside that folder as `ULAT-<run>.json`.

ULAT uses short mesh names internally. The importer retained 91 same-name meshes in the Content Browser instead of overwriting another ULAT entry. Their original project folders and the categorized collections remain available.

Glass and holographic pane components are visual surfaces; they are not validated movement barriers. Check collision when building an enclosed playable room. The downloaded Cargo gate Blueprints are preserved, but their controls and walking access have not been tested here.
