# Building library

Use the outpost authoring checkout at `C:/Users/j6sis/SpaceSurvival/Artifacts/Worktrees/asteroid-outpost`. Double-click **Edit Outpost Sandbox.cmd** there. It opens that checkout and `/Game/OutpostSandbox/L_AsteroidOutpost` in Unreal Editor.

**Saved locally as of September27:** 43 complete placement assets and the 2,156-row ULAT palette. The September24 loading/movement checks covered the prior 41 building assemblies and complete Cargo Level Instance; see that [focused receipt](validation/2026-09-24-building-library.md) for its preview evidence and limits. The newly added furnished apartment is saved as a separate Level Instance and connected to the outpost, and the focused native entry/return walk, door opening/closure and four rendered views pass review. This is sampled traversal, not unrestricted-room or physical-controller acceptance. See the [home-library receipt](validation/2026-09-27-home-library.md); raw records are under `Artifacts/ApartmentHome`.

## Place a complete assembly

Open the Content Browser and select the local collection **SS_01_Assembled___Drag_These**. You can also browse **Content → BuildingLibrary → Assembled**. Drag one Blueprint into the viewport; its pieces move together as one actor.

The 43 generated Blueprints include:

- **Windows:** 30 Genesis frame-and-surface combinations, with glass or digital panels in several sizes.
- **Screens:** six Genesis graphic screens and the P3 complete three-part screen.
- **Workstations:** Goliath complete workstation, P3 complete computer bank, and P3 console with chair.
- **Chairs:** P3 complete chair.
- **Ships:** Cargo ship as a Level Instance Blueprint, containing its full authored interior, local lighting and gate Blueprints.
- **Home:** complete furnished Cyberpunk apartment as a Level Instance Blueprint, with its native room layout, furniture, local lights and an automatic entry door.

These are reusable visual assemblies. New groups do not gain door movement or other interaction automatically. To change a shared assembly without affecting its other instances, duplicate its Blueprint into your own folder before editing it. Keep vendor originals intact.

**Level Instance exception:** duplicating a Cargo or Home Blueprint alone still points at the same private level. For an independent interior variation, duplicate the private level as well and assign that copy to the duplicate Blueprint's **World Asset** before editing. Otherwise an interior change affects every instance using the shared level.

**Cargo ship:** find **BP_CargoShip_Complete** under **Assembled → Ships**. Its private level retains 2,078 actors; the vendor's global environment, camera/sequence rig and grouping actors were removed. Its footprint is approximately **29.8 × 65.1 metres**. Fresh single-placement loading/movement checks pass; the receipt separates preview review from gameplay acceptance. This is a heavy art asset: one pod alone has approximately **8.86 million source triangles**. That is an asset-complexity figure; frame rate and suitability for repeated placement have not been measured.

**Crew apartment:** find **BP_CrewApartment_Complete** under **Content → BuildingLibrary → Assembled → Home**, or in either **SS_01_Assembled___Drag_These** or **SS_New_CP_Apartment**. Its full asset path is `/Game/BuildingLibrary/Assembled/Home/BP_CrewApartment_Complete`; its private level is `/Game/BuildingLibrary/Home/L_CrewApartment`. The private level contains 742 actors from the furnished composition, entry setup and four added local ceiling fills. Vendor global showcase effects, camera/sequence actors and the opaque exterior city-image backdrop are excluded so the apartment uses the outpost's shared environment. The original `/Game/Cyberpunk_Room/Maps/Cyberpunk_Room` is preserved.

The apartment already placed in Wayfarer Exchange is reached from the east side of the Crew Lounge approach. A covered glass passage and six descending steps lead to its automatic door. See [Outpost sandbox](OUTPOST_SANDBOX.md#home-annex) for the route and validation scope. Dragging the complete Blueprint creates another apartment; it does not relocate the existing home.

To edit the placed home's interior, stop Play and back up the outpost map and private apartment level first. Select the apartment Level Instance, enter its Level Instance editing mode, make the intended changes, then save/commit the private level and exit that mode before moving the whole assembly. Preserve the doorway, automatic-door actors and their attachments. Use the Blueprint actor to move the complete home; do not harvest or ungroup its interactive contents into unrelated static pieces. Recheck both entry and return passage after changing nearby furniture, the door or floor levels.

## Use ULAT for individual pieces

On the main toolbar after **Play**, open **Ultimate Level Art Tool → Modular Building**. Choose **Modular** for building pieces or **Props** for screens, light fixtures, furniture and other props. The prepared group names are **Buildings and Structure**, **Screens and Displays**, **Light Fixtures**, **Furniture and Workstations**, **Ships and Vehicles**, and **Props and Details**.

The palette now contains **2,156 entries**: the September27 batch adds 1,006 rows and retains all 1,150 previous rows. The five new groups are **CP Apartment**, **CP Bar**, **CP Megapack**, **CP SciFi** and **CP Holograms**. Click a thumbnail, move into the viewport and left-click to place it. Press **Esc** when finished. Close and reopen the ULAT panel if it was open during configuration.

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

The September27 Cyberpunk import adds **3,491 files** from the owner's downloads, with **1,049 Static Mesh assets** found by the native registry. These are separate counts: the imported files also include materials, textures, Blueprints and maps. Browse the five new local collections for the full native selection:

| Collection | Imported Content Browser root | ULAT group |
| --- | --- | --- |
| **SS_New_CP_Apartment** | `/Game/Cyberpunk_Room` | **CP Apartment** |
| **SS_New_CP_Bar** | `/Game/CyberPunkBarAssetSet01` | **CP Bar** |
| **SS_New_CP_Megapack** | `/Game/CyberPunkMegapack` | **CP Megapack** |
| **SS_New_CP_SciFi** | `/Game/CyberPunkAssets` | **CP SciFi** |
| **SS_New_CP_Holograms** | `/Game/CyberpunkHolograms` | **CP Holograms** |

ULAT adds 1,006 of those meshes. The other **43 have short names that collide with existing rows**, so they are intentionally skipped in ULAT rather than replacing another asset. They remain available in their original folders and the native collections. The apartment is the only complete scene from this batch newly connected to the outpost; importing the other packs does not place their example scenes or add them to the packaged game. `Artifacts/ApartmentHome/library-registration.json`, `apartment-author.json` and `home-integration.json` record the registration, private assembly and station-preservation results.

The assembly assets and local collections are private local data. The collections live in `Saved/Collections`; keep them with the project's private assets when backing up the library.

ULAT's palette data is stored in the installed engine plugin and is **shared across projects using that engine**. It is not a project-private library. Configuration backs up its original data assets and table under `Artifacts/PrefabLibrary/ULATBackups/<run>/` before saving changes. Reports live beside that folder as `ULAT-<run>.json`.

ULAT uses short mesh names internally. The September24 importer retained 91 same-name meshes in the Content Browser instead of overwriting another ULAT entry; the September27 batch separately skips the 43 collisions described above. Their original project folders and the categorized collections remain available.

Glass and holographic pane components are visual surfaces; they are not validated movement barriers. Check collision when building an enclosed playable room. The downloaded Cargo gate Blueprints are preserved, but their controls and walking access have not been tested here.
