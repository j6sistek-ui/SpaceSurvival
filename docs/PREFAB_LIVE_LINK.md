# Prefab library and Blender live link

Every static mesh the project owns, organised into categories, usable as a prefab library from either
the Unreal editor or Blender, with a live connection between the two. Decorate any level from the
same directory of prefabs.

## The pieces

| Piece | Where | What |
| --- | --- | --- |
| Catalogue | `Artifacts/PrefabLibrary/catalog.json` (generated, not committed) | Every owned static mesh: asset path, pack, category, bounds, triangles, materials, proxy file |
| Proxies | `Artifacts/PrefabLibrary/proxies/<pack>/<mesh>.glb` (generated) | glTF of each mesh in metres, no textures, for Blender |
| Prefabs | `Prefabs/<Category>/<Name>.json` (committed) | Parts and point lights relative to a prefab origin. Same schema as the station interior recipe |
| Editor side | `Content/Python/ss_prefabs.py`, loaded by `Content/Python/init_unreal.py` | Catalogue, prefab save/place, live-link endpoint, the **SS Prefabs** menu |
| Blender side | `Tools/SSLiveLink/ss_live_link/` (an add-on package) | Sidebar panel: parts library, prefab save/load, push/pull/live |

## Editor: the SS Prefabs menu

Main menu bar → **SS Prefabs**.

- **Place Prefab ▸ Category ▸ Name** spawns the prefab where the viewport is looking (first surface the
  camera ray hits, else 15 m ahead). Actors land in an outliner folder `Prefabs/<Name>` and carry the
  tag `SSPrefab:<Name>`.
- **Place Part ▸ Category ▸ Mesh** spawns one catalogued mesh the same way.
- **Save Selection as Prefab** writes `Prefabs/<Category>/<Name>.json`. The selection's outliner folder
  names it: put the actors in a folder `Prefabs/Doors/Airlock_A` (or just `Doors/Airlock_A`), select
  them, save. The prefab origin is the selection's bounds centre in XY and bounds bottom in Z, so a
  placed prefab stands on the point you place it at.
- **Rebuild Catalogue** scans the asset registry and exports proxies (minutes the first time; reruns
  only add what is new). **(no proxies)** is the quick variant.
- **Refresh Menus** re-reads the Prefabs folder after you add files by hand or from Blender.

Headless equivalents: `Scripts/ExportPrefabCatalog.py` and `Scripts/TestPrefabs.py`, both run with
`UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput -ExecutePythonScript=...`.

From the editor's Python console, everything is a function: `ss_prefabs.place_prefab('Doors/Airlock_A',
[x, y, z], yaw)`, `ss_prefabs.place_part(asset_path)`, `ss_prefabs.save_prefab('Decor', 'Corner')`.

## Blender: the SS Link panel

Install: `blender --background --python Tools/SSLiveLink/install.py`. The add-on is a package, the
folder `Tools/SSLiveLink/ss_live_link/`; the script copies it to `<user scripts>/addons/ss_live_link/`
of whichever Blender runs it (so run it once per version in use: 5.1 for the headless tools, 5.2 live),
removes the single-file `ss_live_link.py` an older install left there, records the project and engine
roots, and enables the add-on in the saved preferences. Run it again after the add-on changes; an open
Blender picks the new copy up the next time it starts. By hand instead: zip the `ss_live_link` folder
(the folder itself, not just its files), *Edit ▸ Preferences ▸ Add-ons ▸ Install from Disk*, enable
**SpaceSurvival Live Link**, and set the project root in its preferences. The panel is in the 3D
viewport sidebar (N) under **SS Link**.

- **Parts library**: Load Catalogue, pick a category, search by name, **Add at Cursor**. The proxy
  of the real mesh appears, tagged with the asset path (`ss_asset`) and a link id (`ss_link`). Missing
  proxies come in as a box of the mesh's bounds, still placeable.
- **Prefabs**: pick one from the `Prefabs` tree and **Load at Cursor** (proxies in a collection named
  after it), or select tagged objects, set Category and Name, **Save Selection as Prefab**. Point
  lights in the selection are saved too.
- **Editor**: **Connect** finds the open editor. **Push Selected / Push All** creates or moves the
  matching actors (folder `LiveLink`, tag `SSLink:<id>`). **Live** does that twice a second while it
  is on, including deletions. **Pull Selection** mirrors the editor's selected actors here; actors
  that had no link get one, so the next push moves them instead of duplicating.

Frames: Blender metres, Z up, right-handed; Unreal centimetres, Z up, left-handed. The conversion is a
Y flip and ×100 applied to whole matrices, so no Euler angles cross the wire. The self-test proves
the mapping by checking that imported proxies sit exactly where the catalogue's bounds say.

## Transport

The engine's own Python remote execution (`Engine/Plugins/Experimental/PythonScriptPlugin/Content/
Python/remote_execution.py`), enabled in `Config/DefaultEngine.ini`:

```
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bRemoteExecution=True
```

Blender multicasts on 239.0.0.1:6766 (local host only), the editor answers, and commands run on the
editor's game thread. Nothing listens on the Blender side beyond the reply socket, and only an editor
on this machine can be reached. If several editors are open, the one whose project is SpaceSurvival is
chosen.

## Tests

- `Scripts/TestPrefabs.py` (editor, headless): places parts, saves them as a prefab by folder, places
  the prefab, drives create/move/pull/remove through the live-link endpoint, and checks the rotator
  formula the Blender side uses against the engine's own matrices.
- `Tools/SSLiveLink/selftest.py` (Blender, headless): frame round trips, proxy bounds against the
  catalogue, prefab save/reload; `--live` adds a push/pull round trip against an open editor.

## Categories

Assigned from the mesh name (then the pack): Doors, Walls, Floors, Ceilings, Stairs & Rails, Pillars &
Frames, Pipes & Cables, Consoles & Screens, Lights, Furniture, Containers, Machines, Signs & Banners,
Ship Parts, Station Exterior, Asteroids & Debris, Props, Misc. Effects demo packs and engine samples are
left out (`EXCLUDED_PACKS` in `ss_prefabs.py`). A wrong category is a one-line change to `CATEGORIES`
followed by Rebuild Catalogue (no proxies).
