# Edit the station in Unreal

Start by opening this exact project file: **`C:\Users\j6sis\SpaceSurvival\SpaceSurvival.uproject`**. It already targets Unreal Engine 5.8. Use this working project when the Launcher asks where to add an asset. The project under `User downloaded assets\SpaceSurvival` is a source/staging project; the older separately converted `SpaceSurvival 5.8` copy is not the working project.

In its Content Browser, find **BP_StationVisualLayout** at **Content → SpaceSurvival → Licensed → StationVisualPass**. Double-click it and choose its **Viewport** tab. This is the saved visual layout loaded by `ASSStation` for the home hangar and service stations. The one-time authoring step below creates it; once present, ordinary layout editing does not require a script or C++ build.

## Add your first prop

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
| `SpaceSurvival/Licensed/StationVisualPass` | The editable layout and selected private station materials/derivatives |

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
| Launch | `(950, -450, 0)` |
| Mica | `(1000, 1000, 0)` |
| Beacon | `(-1400, 0, 0)` |
| Walk spawn | `(-300, 0, 180)` |
| Docked ship | `(850, 0, 220)` |

The Mica robot starts at approximately `(1110, 1130)` with its feet on the deck; its interaction remains at the Mica service arrow. Keep the two staff in their service alcoves. Their serialized idle clips loop without AI and update at most at 30 Hz while rendered. Changing a skeletal mesh also requires a compatible animation.

Use a few localized light pools around work areas and leave readable contrast between paths and equipment. Add lights gradually and inspect the actual game camera; more lights, shadow casters, transparent screens or skeletal staff can raise rendering cost. Blueprint viewport appearance alone does not establish game exposure, camera readability or performance.

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
