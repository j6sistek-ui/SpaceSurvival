# Station Workshop

**September 21 reset candidate:** gameplay selects the separate `StationReset/BP_StationReset` when installed. This workshop and the legacy Blueprint/Blender instructions below still write `StationVisualPass/BP_StationVisualLayout`; applying them does not change the active reset layout. Keep those original layouts as preserved authoring sources. The reset's recipe, ownership checks and matching physical solids are documented in [Station authoring](STATION_AUTHORING.md#functional-reset-layout--september-21-owner-redesign). Use that process for the new station; the workshop has not been migrated to it.

**Open `C:/Users/j6sis/SpaceSurvival/Open Station Workshop.cmd`.** It opens the working Unreal project directly into the saved workshop. If the editor is already open, use **Tools > Station Workshop**, then **Open Workshop**. No additional plugin purchase is needed.

This is an editor authoring tool. It uses the normal Unreal viewport for selection, movement and undo, with a focused asset/material panel. It is not an in-game construction mechanic. The workshop becomes the source for visual station placement; gameplay collision and interaction locations are still separate and their reported bugs remain open.

The panel can be undocked by dragging its tab beside the viewport, or resized to show more thumbnails. Search narrows the imported asset catalog; preset materials remain a separate ten-choice list.

## First edit

1. In the workshop panel, search for a mesh and drag it into the viewport, or double-click its thumbnail to place it in front of the camera. Existing furnishings are individually selectable too. Press **F** to focus the selected object.
2. Use **W** to move, **E** to rotate and **R** to scale. Every supported mesh can be scaled on individual axes. Use the Details panel for exact numbers, **Alt+drag** to duplicate, **Delete** to remove and **Ctrl+Z** to undo. Grid/rotation/scale snapping is in the viewport toolbar.
3. Click **Save + Apply**. This saves the workshop and updates the station visual Blueprint used by the game. The previous saved map/Blueprint is backed up before application. A result message confirms success or explains why nothing was applied.

**Save + Apply changes the project, not the already-packaged executable or itch.** To see it in editor gameplay, open `Content/SpaceSurvival/Maps/Survival`, start Play and enter the home hangar. A later package/update includes the saved layout. Stop Play before returning to the workshop. Playing the workshop map itself is only an editing preview, with the base GameMode and no survival loop.

## Inspect the complete alien world

In the current development project, play `/Game/SpaceSurvival/Maps/Survival`, close the opening menu and approach the cyan **ALIEN WORLD** doorway in the home hangar or a station. Press **E / A** at its prompt. This opens the complete owned `L_Showcase_level` for visual inspection. **Tab / Y** switches to the pack's complete `L_assets` layout; **Esc / B** returns to the station and original walker position.

| Gallery action | Keyboard/mouse | Controller |
| --- | --- | --- |
| Move / look | WASD / mouse | Left / right stick |
| Rise / fall | E / Q | Right / left bumper |
| Fast / slow movement | Shift / Ctrl | Right / left trigger |
| Showcase / asset layout | Tab | Y |
| Reset view | Home | Start |
| Return or cancel loading | Esc | B |

The labeled evaluation camera flies without collision so you can inspect large structures from any side. Run progression stops during review, and the existing station and session remain in memory for return. This is a viewer: movement does not edit, export or save vendor placements. Use the Workshop to arrange selected assets in your own station. If the owned map is missing, entry reports that it is unavailable and leaves the station in place.

**The old packaged EXE and itch build have no gallery doorway.** Open `Play Development Build.cmd` with the installed private megastructure maps; see [authoring and capture setup](BUILD_RUN.md#spatial-areas-and-alien-gallery-development-project). The first asset view showed empty floor. Corrected capture `3bc9ba3b7f2a42c8a3899b57ae024b38` shows the modular inventory and has independent acceptance for the scripted entry/switch/return path. Ordinary navigation, physical controls, detailed inspection and packaged behavior remain unverified.

## Assets and ten material choices

The thumbnail browser searches all currently imported static meshes, skeletal meshes and Niagara systems under Content, plus Unreal's basic shapes. The September 15 owned-asset pass validates **708** exact filtered entries: 702 under `/Game` and six engine basic shapes. It loads the selected asset when placed, rather than every model at once. New downloads must first be added/imported into the working project using the routes below. Lights can be placed with Unreal's Place Actors panel; point, spot and rect lights are supported.

Original asset materials stay assigned until you choose a preset and press **Apply to selection**. The ten choices are **Steel, Dark steel, Painted white, Copper, Caution yellow, Rubber, Glass, Cyan light, Amber light and Red light**. They are original, simple PBR/tinted or emissive starting materials; they do not replace a detailed textured vendor material automatically. Application affects every material slot on the selected meshes; Ctrl+Z reverses it. Editor-only guides are excluded.

Blueprint actors with behavior, instanced-mesh actors and other unsupported types are rejected by Save + Apply/Export with a named error; they are not silently converted or discarded. Place the underlying meshes or Niagara system instead. Material assets themselves are not listed in the mesh browser. Zero or invalid scale is rejected; finite nonzero scale, including mirrored and nonuniform scale, is supported.

## Saving, exporting and keeping your work

The editable source is `/Game/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop`. Open Workshop reuses its saved contents; it does not regenerate the station on every launch. Save + Apply derives `/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout` from it. Once using the workshop, make composition edits here; direct edits to the derived Blueprint can be overwritten by the next Apply.

**Export Layout** writes a timestamped `.json` into `.agent/local/StationWorkshop/Exports`. It contains stable object identifiers, asset references, world transforms, materials, animation references, visibility and editable Unreal settings. It can include unsaved editor changes, which is marked in the export. The saved map retains groups/attachments; the exported/applied layout flattens component world transforms. It is a handoff manifest, not a complete standalone project or a general-purpose scene importer.

Models and textures are referenced, not embedded in JSON. Keep the private Content folders with the map; GitHub does not contain these licensed files. Apply creates timestamped backups under `.agent/local/StationWorkshop/Backups`. These local copies are recovery checkpoints, not an off-machine backup. See [Project State](PROJECT_STATE.md#where-files-live) for the storage boundary.

The cyan docking-lane and service arrows are editor-only guides. Moving a guide does not move gameplay service locations. Component mobility becomes Movable on application so it attaches correctly to the station. Visual collision stays disabled and existing native collision remains in place; this authoring tool does not close the reported walk-through props, blocked labels or NPC placement issues. Keep clearance around the anchors listed below until that separately paused repair work resumes.

## Setup on another development checkout

Use the exact working project `C:/Users/j6sis/SpaceSurvival/SpaceSurvival.uproject`, not the staging project under User downloaded assets or the older separately converted SpaceSurvival 5.8 copy. Compile once with `Scripts/Build.ps1 -Target Editor`, restore/import the private station content, then run `Scripts/OpenStationWorkshop.ps1 -Prepare`. Preparation creates the ten presets and workshop only when absent, preserving saved owner edits. No engine/tool installation occurs. The launcher detects an already-open Unreal editor and directs you to its Tools menu instead of starting another instance.

Official editor references: [drag-and-drop asset placement](https://dev.epicgames.com/documentation/en-us/unreal-engine/placing-actors-in-unreal-engine) and [transform/duplicate controls](https://dev.epicgames.com/documentation/en-us/unreal-engine/transforming-actors-in-unreal-engine), checked September 14, 2026.

## Advanced: edit the derived Blueprint directly

This older route remains available, but the workshop is now the recommended source of composition. Do not alternate between the two without reconciling changes: Save + Apply replaces the derived component tree with workshop contents.

In the Content Browser, find **BP_StationVisualLayout** at **Content > SpaceSurvival > Licensed > StationVisualPass**. Double-click it and choose its **Viewport** tab.

### Add a Blueprint component

The Blueprint contains ordinary mesh components, two idle skeletal staff components and lights. Make one small change first:

1. With **BP_StationVisualLayout → Viewport** open, select **LayoutRoot** in the **Components** panel. Click **Add**, search for **Static Mesh**, and add that component.
2. Rename it to something recognizable, such as `Owner_StorageBox`. In **Details → Static Mesh**, use the asset picker to select **SM_ArmoryBox** from **Content → SciFiCorridor → Meshes**. The existing mesh brings its assigned materials with it.
3. Select the new component and press **F** to frame it. Use **W / E / R** to move, rotate or scale it, or enter numbers under **Details → Transform**. Put it beside existing storage, outside the cyan docking-lane guide described below.
4. Click **Compile**, then **Save** in the Blueprint editor. Stop and restart **Play** to see that saved change in the station from the normal game camera.

After that first saved prop, use the same process for another asset. Duplicate selected components for repeated objects, delete unwanted dressing, or add a **Point Light** component for local illumination. Make lasting changes in the Blueprint's **Components/Viewport**. An object dragged into the temporary Play level does not become part of this saved station layout.

The large exterior makes **Frame All** zoom far away. Start with a component whose name begins `Shell_`, a service terminal, or one of the `Guide_` markers and press **F**. Mesh names and recipe names are preserved in the component list so sections remain easy to find.

## Assets already in the working project

These folder names were checked on disk on 2026-09-14. Open the **Content** root in the Content Browser, then browse the listed folders. These assets are ready to select in this project; downloading another copy is unnecessary.

| Content Browser folder | What to browse |
| --- | --- |
| `SciFiCorridor/Meshes` | Existing corridor structure, panels and storage; includes `SM_ArmoryBox` |
| `StarterBundle/ModularScifiProps/Meshes` | Furniture and equipment, including `SM_Cabinet_A`, `SM_Cabinet_B`, floors and small props |
| `StarterBundle/ModularSci_Comm/Meshes` | The staged communications/interior kit meshes |
| `StarterBundle/ModularSciFiMats` | Shared StarterBundle materials used by its meshes |
| `Defect` | Electronic props and their materials; browse its mesh assets for meters, switches and lights |
| `Robot_scout_R_21/Mesh` | `SK_Robot_scout_R21`, the skeletal mesh already used by the two staff |
| `SciFITrooper_Man_03` | 26 filtered placeables; its character mesh plus matching walk/exit animations supply the temporary station hero |
| `Heavy_space_trooper` | Two filtered placeables; one mesh and matching idle clip supply a supplemental presentation-only staff member |
| `CosmicMaterial` | Material instances for manual use through Details plus two filtered mesh entries; material assets do not appear as placeable thumbnails |
| `SpaceSurvival/Licensed/StationAssets/Drone` | One private filtered skeletal mesh; its imported idle clip supplies a supplemental presentation-only drone |
| `SpaceSurvival/Licensed/StationVisualPass` | The editable layout and selected private station materials/derivatives |
| `Megastructure_Scifi_World/Meshes` | Owned alien structure, arch, pillar, panel, floor and lamp meshes; added locally September 16. The complete showcase and inventory maps remain under its `Level` folder |

For a cabinet or other ordinary prop, add a **Static Mesh** component as above. The robot is a **Skeletal Mesh**, with a compatible animation configured on the existing staff components. Move or duplicate those existing staff components only when another animated staff member is intended; a static prop needs no animation or Blueprint behavior.

## Bring another purchased pack into this project

Choose the route that matches the files supplied by the pack. A Fab **On disk** label confirms a local download; inspect the working project's Content Browser to confirm the asset has also been added here.

| Pack contents | Route into the working project |
| --- | --- |
| Native Unreal content (`.uasset`) offered by Fab | In the Epic Games Launcher, open the owned pack and choose **Add to Project**, selecting `C:\Users\j6sis\SpaceSurvival\SpaceSurvival.uproject`. Fab uses different actions for asset packs, complete projects and plugins. [Epic: Fab download and export workflow](https://dev.epicgames.com/documentation/en-us/fab/exporting-assets-from-fab-in-launcher) |
| A separate Unreal project that already contains the assets | Open that source project, select the desired assets in its Content Browser, then **right-click → Asset Actions → Migrate**. Keep the required materials/textures in the dependency report and select **`C:\Users\j6sis\SpaceSurvival\Content`** as the destination. Preserve existing working assets when a name conflict appears. Native `.uasset` files use this migration workflow rather than the raw-model Import button. [Epic: Migrating Assets](https://dev.epicgames.com/documentation/en-us/unreal-engine/migrating-assets-in-unreal-engine) |
| Raw model files such as `.fbx`, `.glb` or `.gltf`, plus textures | Keep the original download intact. In the working project's Content Browser, select a new private destination under `SpaceSurvival/Licensed`, use **Import**, choose the model file and review its mesh/material options. Inspect the imported mesh's scale and material slots before adding it to the station Blueprint. The importer used depends on the file format and project configuration. [Epic: Importing Assets](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-assets-using-interchange-in-unreal-engine) |

The workflow links above were checked on 2026-09-14. Adding an asset to **Content** makes it available for use; adding its mesh as a component in **BP_StationVisualLayout** places it in the station. Keep the pack's original folders and material dependencies together. Edit placement in the layout and use private material duplicates for customized looks, preserving the vendor originals.

## What the layout controls

- Floors, walls, ceiling sections, terminal/display meshes, storage, cables, machinery, staff appearance and local lighting live in the Blueprint. Each original instance becomes its own selectable component.
- The game keeps collision, service locations and labels, docking/entry, the displayed player ship, its service arm, the beacon and station ambience in C++. The authored layout replaces the native decorative shell, props and bay lights. It does not add another room behind them.
- The old floor, console and crate collision shapes stay in their existing positions, with their proxy visuals hidden. Cover those shapes with the intended visible furniture; moving a decorative terminal does not move its interaction or invisible collision. If a physical layout change is needed, change the native station and its tests together.
- The Blueprint parent disables collision, overlaps and navigation effects on its visual components, including newly added ones. Keep the layout focused on meshes and lights. Add no gameplay, AI or input logic to its Event Graph.

## Keep these areas readable and reachable

The editor-only cyan box marks the docking lane: local **X -1900 to 1715, Y -700 to 700, Z -10 to 967.5 cm**. Keep opaque furniture out of it. Floor panels are the exception: their visible upper surface belongs at **Z -7.25 cm**, matching the pilot's planted soles; the hidden physical floor stays at **Z -10 cm**. Yellow arrows mark fixed service locations, the walk spawn and docked ship. These guides are hidden in play and excluded from the cooked layout's editor-only components.

| Guide / service | Local location, cm |
| --- | --- |
| Upgrades / Loadout | `(200, -1000, 0)` |
| Repair / Ship Bay | `(-800, -1000, 0)` |
| Contracts / Pilot Record | `(-1100, 850, 0)` |
| Save / Settings | `(0, 1000, 0)` |
| Alien World review doorway | `(450, 1000, 0)`; doorway frame centered at `(450, 1180)`, extending to about Z 324 cm |
| Launch | `(950, -450, 0)` |
| Mica | `(1000, 1000, 0)` |
| Beacon | `(-1400, 0, 0)` |
| Walk spawn | `(-300, 0, 180)` |
| Docked ship | `(850, 0, 220)` |

The Mica robot starts at approximately `(1110, 1130)` with its feet on the deck; its interaction remains at the Mica service arrow. Keep the two original staff in their service alcoves. When the new local packages exist, a heavy trooper appears near `(-1450, 1120, 88)` and a drone near `(1390, -1080, 300)`. They are presentation-only: no collision, navigation, AI or service behavior. Their serialized idle clips loop and update at most at 30 Hz while rendered. Changing a skeletal mesh also requires a compatible animation.

Use a few localized light pools around work areas and leave readable contrast between paths and equipment. Add lights gradually and inspect the actual game camera; more lights, shadow casters, transparent screens or skeletal staff can raise rendering cost. Blueprint viewport appearance alone does not establish game exposure, camera readability or performance.

## A third route: open the interior in Blender

The Blender add-on can open the station interior as a scene, let you move, add and remove parts with the whole parts library at hand, and **Apply** it back. It writes the recipe `Prefabs/Scenes/StationInterior.json` and rebuilds `BP_StationVisualLayout` from it, after copying the previous Blueprint and recipe aside. Each route only sees its own work: Blender reads the recipe and never the Blueprint, so an Apply replaces changes made in the Station Workshop or the Blueprint editor since the last recipe build. It asks before doing that (`layout changed outside a recipe`), but pick one route per change. Clicks, refusals and what has and has not been tested are in [Prefab live link](PREFAB_LIVE_LINK.md).

## Initial authoring and preserving manual work

The lead runs [AuthorStationVisualPass.py](../Scripts/AuthorStationVisualPass.py) to prepare the selected private materials/screens, then [AuthorStationEditableLayout.py](../Scripts/AuthorStationEditableLayout.py) through the installed editor Python runner. The latter calls the small native editor bridge to create real Blueprint component templates. Its default supplemental recipe is private `.agent/local/StationVisualPass/EditableLayout.json`; use `--layout-recipe <path>` to select another recipe.

**An existing Blueprint is preserved by default.** Re-running the author script neither regenerates its components nor saves over hand edits. The script verifies the saved `.uasset` hash is unchanged and writes a separate private receipt under `.agent/local/StationVisualPass/EditableLayout-<GUID>/Authoring.json`. Subsequent recipe changes do not alter an existing layout automatically.

Only an explicit `--reset-layout` rebuilds the existing Blueprint. Save and close the Blueprint first. The script preserves the prior saved `.uasset` byte-for-byte in its new receipt directory before rebuilding; keep a separate project backup as well. Resetting discards manual changes from the active layout, so normal composition should happen directly in the Blueprint viewport.

The optional initial recipe accepts:

```json
{
  "exclude_harvested": ["Shell_SM_Monitor_*", "BayLight_*"],
  "static_meshes": [
    {
      "name": "RepairTerminal",
      "asset": "/Game/YourPack/Meshes/YourTerminal",
      "location": [-800, -1000, 0],
      "rotation": [0, 90, 0],
      "scale": [1, 1, 1]
    }
  ],
  "point_lights": [
    {
      "name": "RepairWorkLight",
      "location": [-800, -1050, 350],
      "color": [1, 0.8, 0.6],
      "intensity": 12000,
      "attenuation_radius": 650,
      "cast_shadows": false
    }
  ]
}
```

Locations place the source mesh's pivot in station-local centimeters. Scales are unitless multipliers; rotation order is pitch, yaw, roll in degrees. Static mesh entries may provide `materials` as an ordered slot override list and `cast_shadows`; otherwise their supplied mesh materials are retained. Exclusion patterns apply only to initially harvested component names, before supplemental recipe components are added. Shell components use `Shell_<mesh name>_<index>`; other props use their native component name plus an index; staff retain their names; initial lights use `BayLight_0` through `BayLight_3`.

The licensed Blueprint and its dependencies remain local private content and are cooked with the game. Public source reproduces the workflow but does not distribute raw pack assets. Without the Blueprint or licensed content, the existing native presentation fallbacks remain available.

## Verify a saved layout

Restart Play and check the approach, exit path, every service and launch from the normal game camera. Confirm that removed native props have not reappeared, the staff and screens resolve, and the scene contains the edited furniture and lights. Native `SpaceSurvival.Integration.StationEditableLayout` automation checks actual Blueprint loading, fallback, nonblocking components, unchanged collision/service anchors and ownership cleanup. The separate native visual-clearance and exterior tests continue to cover fallback presentation. Rendered art quality, owner edits and representative performance still require review in the game.
