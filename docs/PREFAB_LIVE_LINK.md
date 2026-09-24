# Prefab library and Blender live link

Every static mesh the project owns, sorted by type, usable as a parts library from the Unreal editor or
from Blender, with a live connection between the two. From Blender you can also send a new model into
Unreal, fix the shape of a mesh the game already has, and open the station interior, rearrange it and
apply it back.

This page is written for the person using the tools. Button names are in **bold** exactly as they appear.
The last sections (pieces, transport, tests) are for whoever maintains them.

## Large window and laptop library (v0.4.0, September 22)

In **SS Link > Parts library**, press **Pop Out Library**. It opens Blender's native Asset Browser
in a separate window with large thumbnails, categories and search. Move it to another monitor and
drag a mesh into the main 3D viewport. **Prepare Large Library** builds this view in the background
when it is missing; the status line reports completion. Preparing does not save or replace your scene.
The September 22 desktop snapshot contains **1,325 static meshes with 1,325 thumbnails** (1,301 Unreal
previews and 24 clay fallbacks). It includes all `/Game` static-mesh packs, including newer colony,
Tripo and lighting assets; old 458-entry examples below are historical. Skeletal meshes, working
Blueprint assemblies and Niagara effects are not exported as functioning Blender assets.

**Export Library** makes one private ZIP of the prepared library. Copy it to the laptop and use
**Import Library** in SS Link. Import checks the ZIP, creates a fresh library folder and switches the
browser to it. The previous library and open `.blend` stay intact. Export refuses a stale prepared
catalog: wait for preparation to finish and retry. Both computers should use SS Link v0.4.1 or newer and Blender
5.2; native `.blend` library files are built with 5.2.2. Older-version compatibility is unverified.

For the first laptop installation, extract the supplied ZIP and run its
`SpaceSurvivalLibrary/Tools/SSLiveLink/Install Blender Add-on.cmd` with Blender closed. The extracted
folder is its project root; Unreal is not required. On another OS, install the zipped `ss_live_link`
folder manually and set the extracted library folder in preferences. Keep the folder structure.
Save your arrangement as `.blend` and open that file on the desktop: placed meshes and `/Game` asset
references travel together. Opening it does not push changes into Unreal; use the existing explicit
Push/Apply commands. Keep Live off until you want synchronization.

**Auto-refresh Library** enables saved-mesh scanning in the desktop Unreal editor, about every
30 seconds while outside Play. It processes one catalog entry per editor tick, then Blender notices
the catalog change and rebuilds only changed native asset files. An individual large mesh export can
still briefly stall the editor. Turning the checkbox off disables subsequent scans. Unreal must be
restarted after the Python update; Blender must remain open to pick up changes. Laptop libraries are
offline snapshots: refresh them with Export/Import. Dependency-only texture/material edits are not
detected by mesh timestamps; rebuild with forced thumbnails when those previews need updating.

### Per-object materials

Select a placed mesh and use **Surface**, **Glass** or **Mirror finish** under **Surface overrides**.
Edit the displayed color, metallic, roughness, alpha, transmission and IOR controls. These overrides
belong to that object, so another wall using the same mesh retains its material. Push, prefab saves
and Scene Apply carry the values; **Export Placement + Materials JSON** writes a separate handoff.
Unreal generates private materials under `/Game/SpaceSurvival/Licensed/BlenderSurfaces`, assigns them
to the placed component, and preserves vendor materials and mesh defaults.

This transfers six constant PBR properties, not arbitrary Blender shader graphs, textures or every
Principled setting. Complex connected nodes are rejected. Glass is a simple translucent approximation;
Mirror finish needs suitable Unreal reflections and is not a planar-mirror system. Verify their look
in Unreal before using them broadly. These controls apply to placements, not the separate **Edit Mesh**
geometry-replacement workflow.

The desktop v0.4.0 installation and focused data/material checks passed. Live pop-out dragging,
interactive editor refresh and final material appearance remain unverified; see the
[focused validation record](validation/2026-09-22-blender-library.md) and
[RPT-20260922-04](KNOWN_ISSUES.md#september22-blender-library--rpt-20260922-04).

## Before the first use (one time)

1. **Install the add-on into Blender.** Close Blender. In the project folder open `Tools/SSLiveLink` and
   double-click **Install Blender Add-on.cmd**. It installs into every Blender it finds (5.2 and 5.1
   here) and prints `Installed into Blender 5.2.` for each. Start Blender again.
   - Historical status on 2026-09-17: this had **not** been done on the owner's machine yet. Both Blenders held
     the old single-file add-on (v0.1.0), which has none of Types, Send to Unreal, Edit Mesh or Scenes.
     The installer removes that old file.
   - The panel's last line shows the version (`SS Live Link v0.4.1`). When the project's copy is newer
     than the installed one, a red note at the top of the panel says so: run the installer again. Run it
     again whenever these tools are updated.
   - By hand instead: zip the folder `Tools/SSLiveLink/ss_live_link` (the folder itself), then in Blender
     *Edit > Preferences > Add-ons > Install from Disk*, enable **SpaceSurvival Live Link**, and set the
     project root in its preferences.
2. **Restart the Unreal editor once.** The editor reads its Python scripts and the "remote execution"
   switch only when it starts. An editor that was already open when these files arrived cannot be found by
   **Connect**, does not import queued meshes, and runs old code.
3. **Build the parts catalogue** (only if `Artifacts/PrefabLibrary/catalog.json` does not exist, for example
   on a fresh checkout): in Unreal, main menu **SS Prefabs > Rebuild Catalogue (with Blender proxies)**.
   Minutes the first time. Without a catalogue, **Load Catalogue** and **Open Scene** refuse and say so.

Where the panel is: Blender, 3D viewport, press **N**, tab **SS Link**.

## What must be running

| You want to | Blender | Unreal editor |
| --- | --- | --- |
| Browse parts, place them, save and load prefabs, open the visual browser | yes | no |
| **Push**, **Live**, **Pull Selection** | yes | **open**, with a level open |
| **Send to Unreal** | yes | open: imports at once. Closed: the mesh waits and imports by itself the next time the editor starts |
| **Edit Mesh from Unreal** | yes | **open** (it fetches the real mesh from the editor) |
| **Open Scene** | yes | no |
| **Apply** the station | yes | **open**. Closed: the file is saved but the game is unchanged; open Unreal and press **Apply** again |

Only an editor on this machine can be reached, and if several are open the SpaceSurvival one is chosen.

## The panel, box by box

**Editor.** **Connect** finds the open Unreal editor. **Push Selected** / **Push All** create or move the
matching actors in the open level (outliner folder `LiveLink`). **Live** keeps doing that twice a second
while it is pressed in, including removing the actor of a part you delete. **Pull Selection** brings the
actors selected in Unreal into Blender as parts. The line underneath is the status.
- Opening another .blend (or File > New, Revert) switches **Live** off and forgets what was pushed, so
  Live in one file never removes actors that came from another file.
- When more than 12 pushed parts vanish at once, **Live** stops and says so before it removes that many
  actors; press **Live** again to go ahead, or undo first. Each removal is an ordinary undoable delete in
  Unreal until the level is saved.
- The parts of an opened game scene (the station) are left out of **Push All** and **Live**: a scene goes
  back through **Apply**. **Push Selected** still sends whatever you select by hand.

**Parts library.** **Load Catalogue**, then from top to bottom:
- the **type buttons** with counts (Building, Decoration, Exterior & Space, Ships, Characters & Robots,
  Game Objects, Misc), the **name field**, `79 of 458 parts`, and **Show All**, which clears every filter;
- the **category** menu (only the chosen type's categories) and the **pack** menu;
- the **picture grid** (click it to pick by picture) and the **list**. A tick in the list means *in game*:
  the game's code loads that mesh by name. Look-alikes without a tick (for example the V1 and V2 hazard
  meshes beside V3, or `SM_StationExterior` beside `SM_StationPitStop`) are not what a player sees;
- details of the highlighted part, then **Add at Cursor** (places it at the 3D cursor) and **Edit Mesh from
  Unreal** (see flow 4).
- A mesh you sent from Blender appears here at once, under the category you chose.
- Pasting an asset path (starts with `/Game/`) into the name field finds that part.

**Visual browser.** **Open Visual Browser** shows `Artifacts/PrefabLibrary/index.html`, a page of pictures of
every part and prefab, in the web browser; the small refresh button rebuilds the page. Clicking a card copies
its asset path: paste it into the name field of the Parts library to jump to the part. The pictures come
from Unreal (**Rebuild Catalogue** draws them, textured). **Render Thumbnails** is only the fallback for a
machine without the editor build: untextured clay pictures, rendered in a second Blender; **Reload
Thumbnails** (small button) picks them up.

**Prefabs.** Choose one and **Load Prefab at Cursor**; or select parts, fill **Category** and **Name**, and
**Save Selection as Prefab** (writes `Prefabs/<Category>/<Name>.json`; point lights in the selection are saved
too).

**Send to Unreal.** **Category**, **Name**, **One asset**, **Replace existing**, the button **Send to Unreal**,
and **Edit Mesh from Unreal** again. See flows 3 and 4.

**Scenes.** The scene menu, **Open Scene**, the round arrow beside it (**Reload from file**), **Apply <scene>**,
**Move Selected into Parts**, and, when they apply, **Apply Anyway** and **Copy Command**. See flow 5.

## The five flows, click by click

### 1. Find a part by type or picture and place it

1. **Load Catalogue**. Status: `catalogue: 458 parts, 7 types, ...`.
2. Press a type, for example **Building (188)**; narrow with the category menu or type part of a name.
3. Click the part in the picture grid or the list. **Add at Cursor**.
4. Move, rotate, scale and duplicate it like any Blender object. What you see is a light stand-in (a
   "proxy") of the real mesh; it carries the asset's path, so Unreal knows what it is.

### 2. Build something from parts and see it in the Unreal level

1. Unreal open with the level you want. In Blender **Connect**. Status: `connected: SpaceSurvival on ...`.
   `Unreal editor not found` means Unreal is closed, or has not been restarted since these tools arrived.
2. Select your parts, **Push Selected** (status `pushed 3: +3 ~0`), or **Push All**.
3. Optional: press **Live** and keep arranging; Unreal follows. Press it again to stop.
4. Changed something in Unreal instead? Select the actors there, then **Pull Selection** here.
5. Save the level in Unreal when you are happy. To reuse the arrangement elsewhere, save it as a prefab
   (Prefabs box) and place it from Unreal's **SS Prefabs > Place Prefab** menu.

### 3. Model something new in Blender and send it to Unreal

1. Model it. The object's origin becomes the asset's pivot; modifiers are applied in the file, your object
   is left as it is; where it stands in the scene does not matter.
2. Select it. In **Send to Unreal** choose the **Category** it should be filed under. Leave **Name** empty to
   use the object's name. Several objects as one mesh: tick **One asset** (the active object is the pivot).
3. **Send to Unreal**.
   - Unreal open: `SM_Bracket: imported 1: Bracket`. It is now `/Game/Blender/<Category>/SM_Bracket` with its
     materials and textures beside it, a collision box, and Nanite when it has 20,000 triangles or more.
   - Unreal closed: `queued: Unreal is not open, so it imports by itself when the Unreal editor next starts`.
4. The mesh is in the parts list at once, and your object now counts as a part: **Push** places it, and in
   an opened station scene **Apply** writes it into the station.
5. Changed the model? Select the same object and **Send to Unreal** again: the same asset is updated, and
   every placed copy changes with it. Typing a **Name** sends it as a new asset instead.

Rules:
- A name that is already taken is refused (`SM_Cube already exists: give yours another name, or tick Replace
  existing`). **Replace existing** sends over that asset; the button asks first and the tick clears itself.
- A library part (proxy) is never sent back; it would replace the real mesh with its light stand-in.
- The file Unreal replaces is always kept first: `Artifacts/LiveLink/Backups/<time>/<same path>.uasset`. To
  go back: close Unreal, copy that file over the one in `Content/`, start Unreal.
- Meshes that share one trim-sheet material belong in one category; each category folder gets its own
  copy of a material and its textures.
- Blender's +Y arrives as Unreal's -Y, the same flip the live link uses, so a sent mesh placed by **Push**
  looks the same in Unreal as it did in Blender.

### 4. Fix the shape of a mesh the game already has (also hazards and the station exterior)

1. Unreal open. In Blender click the part that looks wrong (a placed part, or one in an opened station
   scene), or with nothing selected highlight it in the parts list. For a hazard or the station exterior
   there is no scene to open: press the type **Game Objects** or **Exterior & Space** and pick the row with
   the *in game* tick.
2. **Edit Mesh from Unreal**. The real mesh arrives at the 3D cursor in a collection `SS Edit`. Status:
   `editing SM_Terminal_A (the selected part, RepairTerminal): Send to Unreal replaces /Game/...`.
3. Change its **shape**. Shape only: the asset keeps the materials it has in Unreal, so it may look grey
   here, and repainting it changes nothing in the game.
4. Select that same object, leave **Name** empty, **Send to Unreal**. The button asks `Replace /Game/... in
   the Unreal project?`. After it, every placed copy in the game has the new shape, and you can delete the
   copy in Blender.

Rules and limits:
- Only the one object **Edit Mesh** made may replace the original. A duplicate of it, a piece separated from
  it, or a renamed copy is treated as new work and is sent as a new asset under `/Game/Blender`, never over
  the pack's mesh. Typing a **Name** also makes a new asset.
- The mesh as it was is kept under `Artifacts/LiveLink/Backups` (see flow 3). Pack content is not in git,
  so that backup is the only way back.
- `SM_StationPitStop` (the live station exterior): the ship collides with 13 boxes generated separately
  from this shape, so they do not follow your change, and re-running the pit stop pipeline writes the mesh
  again. The panel says this when you fetch it.
- What goes back is the top level of detail without vertex colours. What Unreal does to extra LODs or
  vertex colours an asset already had was not checked.
- An Edit Mesh copy left standing in a station scene is ignored by **Apply**, **Push All** and **Live**.

### 5. Open the station interior, fix it by hand, apply it

1. In **Scenes** choose **Station interior**, **Open Scene**. A new Blender scene `SS Station interior` opens.
   Status: `opened Station interior: 231 parts, 18 lights, 252 locked`.
   - **Parts** and **Lights** are yours to move, duplicate, delete and add to.
   - **Context (locked)** are guides you cannot select: the deck, the wall limits, the **flight lane** (the wire
     box down the middle that a docking ship flies through), the mouth, the docked ship's spot, the service
     points.
   - **Built by the game (locked)** is the other half of the room: wall, ceiling and pipe panels, ceiling
     lamps, crates and the staff, which the station's own code adds and no recipe lists. They are shown as
     they were the last time the layout was built, so you do not set a part through a wall. They cannot be
     moved from here. To change the *shape* of one, find its mesh in the parts list and use flow 4. If the
     report line says they are NOT shown, no build receipt was found on this machine.
2. Work. To add a part use the Parts library (**Add at Cursor**), then select it and press **Move Selected
   into Parts**. To add something new, model it and **Send to Unreal** first (flow 3).
3. **Apply Station interior**. It asks first: the whole layout Blueprint is rebuilt from what is in this
   scene. Then:
   - `applied: wrote Prefabs/Scenes/StationInterior.json: ...` and `Unreal rebuilt the layout: 483
     components`: done. The lines below say where the previous Blueprint and the previous recipe file were
     kept.
   - `saved, but NOT in the game yet`: Unreal is closed. Open the project in Unreal and press **Apply** again.
     (**Copy Command** is the command-line route, for use with the editor closed.)
   - `saved, but NOT in the game: Unreal refused it`: the line below says why.
4. Opening the scene again shows it as you left it. The round arrow (**Reload from file**) throws away what
   you changed since the last Apply and reads the file again; it asks first.

What **Apply** refuses, and the click that settles it (the offenders are selected for you):

| It says | Why | Do this |
| --- | --- | --- |
| `in the flight lane` | a docking ship flies there | move the part out to the side, or above the wire box |
| `not in Unreal yet` | you modelled it here and it is not an asset | select it, **Send to Unreal**; or delete it |
| `also in scene 'Scene'` | the part is shared with another Blender scene | select only what belongs here, **Move Selected into Parts** |
| `skewed or squashed flat` | Unreal cannot hold that transform | clear its parent (Alt+P) or apply its scale (Ctrl+A, Scale) |
| `a material slot with nothing in it` | the station refuses such a mesh | use another part there |
| `there are no parts in this scene` | an emptied scene is never applied | Ctrl+Z, or **Reload from file** |
| `N of the M parts this scene had are gone` | more than a quarter vanished since it was opened | **Apply Anyway** if you meant it; otherwise undo |
| `StationInterior.json changed on disk since ...` | something else wrote the recipe (the generator, another .blend, a hand edit) | **Reload from file** to take that version, or **Apply Anyway** to overwrite it (the old file is kept) |
| `layout changed outside a recipe` (from Unreal) | the layout Blueprint was saved by the Station Workshop or the Blueprint editor since the last recipe build, or has unsaved changes there | **Apply Anyway** replaces that work with this scene (the Blueprint is backed up first); or stop and keep it |
| `stop Play before applying` | the running game is built from that Blueprint | stop Play in Unreal |

**One layout, three editors.** The station layout Blueprint (`BP_StationVisualLayout`) can be changed from
Blender (**Apply**), from the Station Workshop (**Save + Apply**), and by hand in the Blueprint editor
([Station editing](STATION_EDITING.md)). Each of the first two rebuilds the whole Blueprint from its own data
and does not see the others' work. Blender never reads the Blueprint, only the recipe file. So pick one
route per change; the `layout changed outside a recipe` question above is what stops Blender from silently
discarding work done in the other two, and every rebuild keeps the previous Blueprint byte for byte in
`.agent/local/StationVisualPass/EditableLayout-<id>/`. Once `Prefabs/Scenes/StationInterior.json` exists it,
not `PitStopLayout.json`, is the recipe Blender opens; see the note in [Build and run](BUILD_RUN.md) before
re-running the pit stop pipeline.

Any prefab can be opened the same way (it is in the same menu); **Apply** then just saves the prefab file.

## Where things land

| What | Where | In git? | Ships in the game? |
| --- | --- | --- | --- |
| Meshes sent from Blender, with materials and textures | `Content/Blender/<Category>/` (`/Game/Blender/...`) | **not ignored yet**: until `/Content/Blender/` is added to `.gitignore`, a broad `git add` would commit every experiment (no LFS; GitHub refuses files over 100 MB). Never `git add -A`; add a finished mesh on purpose | only when something in the game uses it (a placed actor, the station layout, a placed prefab). `/Game/Blender` is deliberately outside the always-cooked `/Game/SpaceSurvival` |
| Waiting sends | `Artifacts/LiveLink/Outbox/<Category>/<Name>.glb` + `.json`; fixes in `Outbox/_Edits` | ignored | no |
| Meshes fetched by Edit Mesh | `Artifacts/LiveLink/Edit/` | ignored | no |
| Backups of replaced assets and recipe files | `Artifacts/LiveLink/Backups/` (assets under `<time>/`, recipes under `Scenes/`) | ignored | no |
| The applied station recipe | `Prefabs/Scenes/StationInterior.json` | tracked | no (the Blueprint built from it does) |
| Prefabs | `Prefabs/<Category>/<Name>.json` | tracked | no |
| Catalogue, proxies, thumbnails, gallery, `sent.json` | `Artifacts/PrefabLibrary/` | ignored | no |
| Layout build receipts and Blueprint backups | `.agent/local/StationVisualPass/EditableLayout-<id>/` | ignored | no |

A kitbash that joins pieces of a licensed pack mesh into a new object is sent as a new asset under
`Content/Blender`: keep such meshes out of git like the packs themselves.

## Editor: the SS Prefabs menu

Main menu bar, **SS Prefabs**.

- **Place Prefab > Category > Name** spawns the prefab where the viewport is looking (first surface the
  camera ray hits, else 15 m ahead). Actors land in an outliner folder `Prefabs/<Name>` and carry the
  tag `SSPrefab:<Name>`.
- **Place Part > Category > Mesh** spawns one catalogued mesh the same way.
- **Save Selection as Prefab** writes `Prefabs/<Category>/<Name>.json`. The selection's outliner folder
  names it: put the actors in a folder `Prefabs/Doors/Airlock_A` (or just `Doors/Airlock_A`), select
  them, save. The prefab origin is the selection's bounds centre in XY and bounds bottom in Z, so a
  placed prefab stands on the point you place it at.
- **Open Prefabs Folder** opens `Prefabs/` in Explorer.
- **Rebuild Catalogue (with Blender proxies)** scans the asset registry, exports proxies and draws the
  thumbnails (minutes the first time; reruns update new or saved mesh changes). **Rebuild Catalogue (no proxies)** is
  the quick variant. A mesh sent from Blender is catalogued under the category folder it was filed in, and
  gets its row as soon as it is imported, without a rebuild.
- **Open Visual Browser** / **Rebuild Visual Browser**: the gallery page.
- **Select Blender-linked Actors** selects everything Push created. **Refresh Menus** re-reads the Prefabs
  folder after you add files by hand or from Blender.

From the editor's Python console, everything is a function: `ss_prefabs.place_prefab('Doors/Airlock_A',
[x, y, z], yaw)`, `ss_prefabs.place_part(asset_path)`, `ss_prefabs.save_prefab('Decor', 'Corner')`, and after
`import ss_send, ss_scenes`: `ss_send.import_outbox()`, `ss_scenes.apply_station_recipe(path)` (add
`target='/Game/...'` to build a copy somewhere free instead of the layout itself, `force=True` for Apply
Anyway).

## The pieces

| Piece | Where | What |
| --- | --- | --- |
| Catalogue | `Artifacts/PrefabLibrary/catalog.json` (generated, not committed) | Every owned static mesh: asset path, pack, type, category, bounds, triangles, materials, proxy, thumbnail |
| Proxies | `Artifacts/PrefabLibrary/proxies/<pack>/<mesh>.glb` (generated) | glTF of each mesh in metres, no textures, for Blender |
| Prefabs | `Prefabs/<Category>/<Name>.json` (committed) | Parts and point lights relative to a prefab origin. Same schema as the station interior recipe |
| Editor side | `Content/Python/ss_prefabs.py`, `ss_send.py`, `ss_scenes.py`, loaded by `Content/Python/init_unreal.py` when the editor starts | Catalogue, prefab save/place, live-link endpoint and the **SS Prefabs** menu; import of sent meshes and export for Edit Mesh; rebuilding the station layout from a recipe |
| Blender side | `Tools/SSLiveLink/ss_live_link/` (an add-on package), installed by `Tools/SSLiveLink/install.py` | The **SS Link** sidebar panel |
| Locked context | `Tools/SSLiveLink/context/station_interior.json` | The guides shown locked in an opened station scene, and the flight lane rule both sides check |
| Transfer folder | `Artifacts/LiveLink/` (generated) | Outbox, Edit, Backups |

Frames: Blender metres, Z up, right-handed; Unreal centimetres, Z up, left-handed. The conversion is a
Y flip and x100 applied to whole matrices, so no Euler angles cross the wire. The self-test proves
the mapping by checking that imported proxies sit exactly where the catalogue's bounds say.

## Transport

The engine's own Python remote execution (`Engine/Plugins/Experimental/PythonScriptPlugin/Content/
Python/remote_execution.py`), enabled in `Config/DefaultEngine.ini`:

```
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bRemoteExecution=True
```

The setting, and `Content/Python/init_unreal.py`, are read when the editor starts: restart the editor once
after they change. Blender multicasts on 239.0.0.1:6766 (local host only), the editor answers, and commands
run on the editor's game thread. Nothing listens on the Blender side beyond the reply socket, and only an
editor on this machine can be reached. If several editors are open, the one whose project is SpaceSurvival
is chosen.

## Tests

Commands are in [Build and run](BUILD_RUN.md#prefab-catalogue-thumbnails-and-vault-imports). All four passed
on 2026-09-17.

- `Tools/SSLiveLink/selftest.py` (Blender, headless, 5.1 and 5.2; last line `SSLIVELINK_SELFTEST_OK`):
  the package registers and unregisters cleanly; frame round trips; proxy bounds against the catalogue;
  prefab save and reload; every operator; the panel (type buttons inside the Parts library box, version
  line); the type, category, pack and name filter, pasted asset paths, the picture grid's cap; push, pull
  and live against a stand-in editor, including a file opened in between; Send to Unreal into a scratch
  Outbox (names, refusals, Replace existing, a copy of an Edit Mesh object never reaching `_Edits`, the sent
  mesh in the parts list); Edit Mesh with a stand-in editor (selection first); Open Scene / Apply on the
  real station recipe with a stand-in editor (where parts land, the locked context and what the game
  builds, every refusal in the table above, Apply Anyway, backups of the replaced recipe, reloads).
  `--live` adds a push/pull round trip against an open editor; that has not been run.
- `Scripts/TestSendScenes.py` (Unreal commandlet; last line `SENDSCENES_TEST_OK`; needs Blender 5.2 or 5.1,
  or `SS_BLENDER`): the editor halves, fed by the real add-on run headless through
  `Tools/SSLiveLink/test_send_helper.py`. Import of a new send (path, size, Y mirror, winding, materials,
  collision, catalogue row), re-send over the same asset with a byte-for-byte backup, a fix to a duplicate
  of a real pack mesh (shape changed, old materials kept, backup), a failed import leaving the asset as its
  file has it, sidecars that have no right to a pack asset refused, recipe checks, and
  `apply_station_recipe` building the real 231-part recipe into **scratch copies** of the layout. It leaves
  `BP_StationVisualLayout.uasset`, the owner's catalogue and `git status` exactly as they were, and removes
  only its own receipts.
- `Scripts/TestPrefabs.py` (Unreal commandlet; `PREFABS_SELFTEST_OK`): places parts, saves them as a prefab
  by folder, places the prefab, drives create/move/pull/remove through the live-link endpoint, and checks
  the rotator formula the Blender side uses against the engine's own matrices.
- `Install Blender Add-on.cmd` was run against a scratch Blender user folder for 5.2 and 5.1 (old
  single file removed, package installed and enabled). It has not been run against the owner's real Blender.

**Not tested: anything that needs a button pressed in a real Blender window talking to the owner's open
Unreal editor.** No test has clicked Connect, Push, Live or Pull against a real editor since the add-on
became a package; **Send to Unreal** asking an open editor to import, and the import of waiting sends when
an interactive editor starts; **Edit Mesh** fetching from an open editor; **Apply** rebuilding the real
`BP_StationVisualLayout` (only scratch copies have ever been built by `ss_scenes`), including the
`layout changed outside a recipe` question on the real layout; and the confirmation dialogs, which only
exist when a button is clicked. The first real use of each is its first real test: for Apply, note the
backup line it prints.

## Categories

Assigned from the mesh name (then the pack): Doors, Walls, Floors, Ceilings, Stairs & Rails, Pillars &
Frames, Pipes & Cables, Consoles & Screens, Planets & Sky, Characters & Robots, Game Objects, Lights,
Furniture, Containers, Machines, Signs & Banners, Ship Parts, Station Exterior, Asteroids & Debris, Wreckage,
Props, Misc. Each belongs to one type (the buttons): Building, Decoration, Exterior & Space, Ships,
Characters & Robots, Game Objects, Misc. A mesh sent from Blender takes the category of the folder it was
filed in. Effects demo packs and engine samples are left out (`EXCLUDED_PACKS` in `ss_prefabs.py`). A wrong
category is a one-line change to `CATEGORIES` followed by **Rebuild Catalogue (no proxies)**.

## Building examples sandbox

The owned Genesis and companion examples use a separate editable authoring level and a linked Blender
scene. See [Building sandbox workflow](BUILDING_SANDBOX.md) for walking, placement round trips, the
destination-map safeguard, laptop transfer and the boundary between Blender proxies and Unreal visuals.
