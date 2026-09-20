# Station authoring — the working process

How the space station is actually built, looked at, and validated. Written so the next session does
not re-learn any of this the expensive way.

This is **not** a rule set. [AGENTS.md](../AGENTS.md) owns scope and PR policy; [CLAUDE.md](../CLAUDE.md)
owns the toolchain. This file is *how the station work is done*, and every technique below is here
because doing it the other way cost a session.

---

## 1. The pipeline

```
Scripts/MakeStationRecipe.py          generator - EDIT THIS to change the station
        |  python Scripts/MakeStationRecipe.py --flat
        v
Artifacts/StationRecipe/station_recipe.json     (untracked, ~630 KB)
        |  USSStationLayoutAuthoringLibrary::CreateStationVisualLayout(json, bResetExisting)
        v
BP_StationVisualLayout   /Game/SpaceSurvival/Licensed/StationVisualPass/
        |  spawned by ASSStation  (SSStation.cpp:51, :178)
        v
the station in game
```

**Swapping the entire station needs no C++ change.** The recipe rebuilds the Blueprint's
SimpleConstructionScript wholesale. That is the single most useful fact in this document.

### `--flat` is required

The generator emits `instanced_meshes` by default and `static_meshes` under `--flat`. **Only the
flat form is parseable by the compiled binary** — the `instanced_meshes` path needs a change to
`SSStationVisualLayout.cpp` that was written, reverted, and never compiled. Always pass `--flat`
until that lands.

### Recipe schema

Read off the parser, not guessed:

```jsonc
{
  "static_meshes": [{
    "name": "...", "asset": "/Game/...",
    "location": [x, y, z], "rotation": [pitch, yaw, roll], "scale": [x, y, z],
    "materials": ["/Game/..."],          // optional override
    "cast_shadows": false
  }],
  "point_lights": [{
    "name": "...", "location": [x,y,z], "rotation": [0,0,0], "scale": [1,1,1],
    "color": [r, g, b], "intensity": 0.0, "attenuation_radius": 0.0, "cast_shadows": false
  }],
  "exclude_harvested": ["wildcard*"]
}
```

There is no `spot_lights` or `rect_lights` key. The generator counts what it drops and prints it —
believe that number rather than assuming a spot light made it through.

### Rotation conventions differ at every hop

This has bitten more than once. Three different orderings are in play:

| Where | Order |
|---|---|
| `Artifacts/StationLarge/kit_rooms.json` | `[roll, pitch, yaw]` |
| `unreal.Rotator(a, b, c)` in Python | `(roll, pitch, yaw)` |
| the recipe's `JsonTransform` -> `FRotator(X, Y, Z)` | `(pitch, yaw, roll)` |

**Recipe rotation is `[pitch, yaw, roll]`.** For a flat prop spun about its vertical axis that means
`(0, yaw, 0)`.

### Grounding a mesh

Pivots are arbitrary. Measure `min.z` once, record it in a table next to the asset, and place at
`z - min_z * scale` so the BASE meets the surface. The generator has `GROUND` and `COL_MINZ` tables
doing exactly this. Never eyeball a Z offset.

### One empty material slot aborts the whole build

`AddStatic` pre-fills materials from the mesh's own slots and **refuses any mesh with an unassigned
slot**. A single offender takes the entire station with it. `SM_Top_Wall02` proved this; the fix was
an explicit override on the affected entries (`SLOT_FIXES`). **Verify slots on every new asset before
it enters the generator:**

```python
[s.material_interface for s in mesh.get_editor_property("static_materials")]  # no Nones allowed
```

---

## 2. Running things

```bash
python Scripts/MakeStationRecipe.py --flat
```

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/Build.ps1 -Target Editor
```

`-Target` takes `Editor`, `Content`, `Validate`, `Test`, `Package`. **`-Target Test` does not
rebuild** — run `Editor` first or you are testing the previous binary.

One suite, not all 67, while iterating:

```bash
"C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" SpaceSurvival.uproject -unattended -NullRHI -stdout -FullStdOutLogOutput "-ExecCmds=Automation RunTests SpaceSurvival.Flight.DirectionalDodgeCollision" "-TestExit=Automation Test Queue Empty" -DisablePlugins=UAssetBrowser
```

Source-level checks, no Unreal needed:

```bash
python Scripts/CheckProject.py
```

```bash
python Tests/TestSourceDigests.py
```

### Applying a recipe to the live editor

Run it yourself through `mcp__nwiro__execute_python` — **do not assume a console paste happened.**
The owner has stated plainly they never run the Python by hand.

```python
import unreal
js = open(r"C:\Users\j6sis\SpaceSurvival\Artifacts\StationRecipe\station_recipe.json", encoding="utf-8").read()
bp = unreal.SSStationLayoutAuthoringLibrary.create_station_visual_layout(js, True)
```

About 5 s for ~2,700 meshes. Destroy any previously spawned instance **first**, or it keeps the old
generated class.

### PIE

PIE is play-in-editor: the game running inside the editor. `mcp__nwiro__play_in_editor` is **blocked
by the permission classifier** — starting PIE is the owner's call, not something to trigger
unattended.

Two things to know:

- **`captureviewport` reads the EDITOR world only, never the PIE world.** A capture taken during PIE
  shows the editor scene. To inspect a running game use the `pie_*` tools (`pie_list_actors`,
  `pie_get_property`, `pie_get_game_state`).
- A station Blueprint with 1,793 components was once blamed for hanging PIE. **That was wrong.** See
  section 5.

---

## 3. Camera and viewing

The capture loop that works:

```
setcameratransform  ->  captureviewport  ->  python Scripts/CaptureShot.py out.png [gamma]  ->  look
```

### Tool argument shapes

Both take their payload **nested**, and both reject a flat call:

```jsonc
setcameratransform: { "transform":        { "location": {x,y,z}, "rotation": {pitch,yaw,roll}, "scale": {x,y,z} } }
captureviewport:    { "captureTransform": { ...same... }, "annotations": [] }
```

`annotations` has no default — omit it and the call fails. When any nwiro tool rejects a call it
**prints its own JSON schema in the error**. Read that instead of guessing a second time.

### Captures never fit in a tool result

`captureviewport` returns 1-2 MB of inline base64 and **always** exceeds the token limit. The
harness spills it to a file and tells you the path. That is the normal path, not a failure.
`Scripts/CaptureShot.py` finds the newest spill, decodes it, lifts exposure, and deletes older spills
— a run of captures at 2 MB each has filled this disk before.

### Frames come back underexposed — fix it in post, not in the level

The station is graded dark on purpose (`DIM_INTENSITY = 0.34`). Raw frames land at mean luminance
about 0.03. **Lift the gamma locally; do not re-light the level to make a screenshot readable.** The
helper prints the RAW statistics before lifting — judge "is this lit?" from those, never from the
lifted image.

### Exposure inside the editor

A blank workshop map has **no PostProcessVolume**; the game's `Survival` map has
`ReadableSpaceExposure`. Without one, interiors clip to white. Calibrated by measurement:

| `auto_exposure_bias` | result |
|---|---|
| 0 | mean 10, 56% black |
| 3.6 | mean 103, **0.1% clipped** |
| 11 | mean 249, 88% clipped |

Use **3.6**. Note the volume is *bounded* — 2 km from the station it does not reach, and captures out
there come back black for that reason alone.

### Seeing 30 unknown assets at once

Asset thumbnails auto-frame, which destroys relative scale, and cost one tool call each. Instead:
spawn everything in a world-space grid, take **one** capture, then project each actor to screen
yourself and crop cells into a labelled contact sheet.

UE is left-handed, Z-up:

```python
fwd   = (cos(P)*cos(Y), cos(P)*sin(Y), sin(P))
right = (-sin(Y), cos(Y), 0)
up    = cross(fwd, right)
focal = (W/2) / tan(radians(FOV)/2)          # editor default FOV = 90
d  = world_point - camera_location
sx = W/2 + (dot(d, right) / dot(d, fwd)) * focal
sy = H/2 - (dot(d, up)    / dot(d, fwd)) * focal
```

One capture plus local cropping replaced 30 thumbnail calls and kept true relative scale.

### Hero/beauty stills: use SceneCapture2D, not the viewport

`captureviewport` is fine for checking work. It is **not** how to make a presentable still: it is
locked to the viewport size (2038x782, and a cine camera letterboxes inside that to ~1390x782) and it
inherits the cine camera's depth of field.

For anything going outside the project, render through a `SceneCapture2D` into a render target. Full
control of resolution, no viewport dependency, and it never stalls:

```python
rt = unreal.RenderingLibrary.create_render_target2d(
        world, 2560, 1440, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0,0,0,1), False)
sc = eas.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
comp = sc.capture_component2d
comp.set_editor_property("texture_target", rt)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property("fov_angle", 48.5)          # HORIZONTAL degrees, not focal length
comp.set_editor_property("capture_every_frame", True)   # see below - required
comp.set_editor_property("capture_on_movement", True)
comp.capture_scene()
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "shot.png")
```

Measured against the viewport path on the same frame: **sharpness (variance of the Laplacian) 749 vs
53, at 2560x1440 instead of 1390x782.**

Four traps, all of which cost a cycle:

- **`capture_every_frame = False` silently returns a stale image.** `capture_scene()` on its own does
  not refresh the target, so every export is byte-identical to the first one and it looks as though
  settings are being ignored. Diagnose by pointing the capture somewhere absurd (the ceiling) and
  checking the export actually changes.
- **SceneCapture does NOT inherit the level's PostProcessVolume exposure.** Straight out of the box it
  blew out at 74% of pixels clipped. Lock it: `override_auto_exposure_method` + `AEM_HISTOGRAM`, then
  `override_auto_exposure_min_brightness` / `max_brightness` set to the SAME value. **The override
  flag is what matters** - setting `auto_exposure_bias` without `override_auto_exposure_bias` does
  nothing at all, which reads exactly like a broken capture. Higher lock = darker image; for the
  station interior **60** gave mean 0.406 with 1.8% clipped.
- **Do not calibrate with `read_render_target_raw_pixel`.** Sampling ~150 pixels per iteration stalls
  the render thread long enough to close the MCP socket. Export the PNG and measure it locally.
- **Depth of field will quietly ruin a two-character shot.** A 40 mm at f/2.8 focused on a subject at
  3.9 m leaves a second figure at 7.9 m visibly soft. SceneCapture has no DoF by default, which is the
  correct look here; on a CineCamera, stop down or set the focus between the subjects.

`HighResShot` and `AutomationLibrary.take_high_res_screenshot` both work **exactly once** and then
stall forever, waiting on viewport redraws that never come. Requesting an oversize shot (5120x2880)
appears to wedge the subsystem outright. Neither realtime-on nor `editor_invalidate_viewports()`
revives it. Do not build a workflow on them.

### Fix the shot, not the set

Standing the hero beside the crew room's glass dividers made his arm render **torn** - a hard,
stair-stepped rip down it, with what looked like a second copy alongside.

**The mechanism is not known, and two confident diagnoses were wrong.** It was called reflections in
parallel glass; it was then called refraction through a panel. Neither holds up. What is established:

- The arm was genuinely torn, not mirrored. Only a native-resolution zoom showed this.
- The metal surface behind it is what made it read as a reflection, helped by a third small finger
  that looked like a panel edge.
- Disabling temporal AA changed nothing. Disabling SSR changed nothing. Both were toggled on a guess.
- `SM_GlassDivider` panels flank the spot about 2 m to either side - close enough to be implicated,
  too far for the arm to be intersecting them.
- Moving the subject 80 cm, with the camera left where it was, cleared it completely.

So the entry worth keeping is procedural, not technical:

1. **Zoom to native resolution before naming a cause.** One crop of the 5120x2880 frame settled in a
   glance what two render settings could not. Both were changed before anyone looked closely.
2. **Move the subject, or re-point the capture, and see whether the artefact follows.** That
   distinguishes the renderer from the room without touching a single setting.
3. **Do not repair the set to fix a photograph.** De-glossing the glass would have changed the running
   game to fix one still. The owner's call: *"it's probably good live but kills the picture."*

Not worth chasing further. The owner's call is that staged stills are a stopgap and the real answer is
a photo mode - logged in
[docs/production/FEATURE_PROPOSALS.md](production/FEATURE_PROPOSALS.md), not built. Until then, move
the subject and move on.

### Importing a rigged character: set the Skeleton field

**The single most expensive field in the import dialog is `Skeleton`.** Leave it empty and Unreal
creates a brand-new skeleton for that mesh. The mesh then owns a skeleton no clip in the project was
authored against, so it can never play an existing animation, and there is no cheap way back.

This is what happened to the Tripo alien. It imported with its own `_Skeleton`, and the wardrobe's own
rule - `ApplyHero` rejects a hero whose mesh skeleton differs from its walk clip's - meant it could be
listed as installed and still never appear.

Three findings from trying to repair it after the fact:

- **`SkeletalMesh.Skeleton` is read-only from Python.** There is no `set_skeleton`, no
  `merge_all_bones_to_bone_tree`, and `set_editor_property` refuses even with a notify-mode override.
  Re-pointing a mesh at another skeleton cannot be scripted; it is a Content Browser action.
- **Matching bone NAMES is not enough.** All 61 of the alien's bones existed in `SKEL_Nyxar`'s 164, on
  standard UE names, and that was taken as proof it would bind. It did not: *Assign Skeleton* returned
  **FAILED TO MERGE BONES**, because the hierarchy - parenting and order - is what has to match, not
  the name set. Compare hierarchy, not a set intersection.
- **`Skeleton.add_compatible_skeleton` registers but does not help here.** The compatibility entry is
  accepted, and the single-node animation path still refuses the clip.

> **Never accept "Would you like to regenerate the skeleton from this mesh?"** Its warning is literal:
> it invalidates every animation linked to the target skeleton. Accepting it on `SKEL_Nyxar` would have
> taken the six AlienCrew clips, the Nyxar playable body and the seven station crew NPCs with it.
> The answer is No, every time.

The fix is upstream, not in Unreal: re-rig or re-export against a known skeleton, then import with
`Skeleton` pointed at the existing asset. Rigs already carrying clip sets in this project:

| Rig | Body already on it | Clip set it brings |
|---|---|---|
| UE5 mannequin | `RetroFuturisticSoldier` | its own eight-way locomotion |
| UE4 mannequin | `Robot_scout`, `HeavyTrooper` | the MoCap library, plays untouched |
| `SKEL_Nyxar` | `Nyxar` | the six AlienCrew clips |

### Placing a character for a still

Never hand-place the hero as a bare `SkeletalMeshActor`. Spawn the game's own pawn, `ASSWalker`: it
carries `MeshYaw = -90`, the measured sole offset, `RenderedScale` (1.5) and its own authored key/rim
rig on lighting channel 1. For crew, copy `SSStationPresentation::BuildAlienCrew` - mesh
`/Game/Nyxar/Meshes/SKM_Nyxar`, `AlienMeshFacesPlusY = 90`, scale from native bounds, skin on the LAST
material slot. There is one Nyxar mesh and six colour skins; there is no male/female variant.

Three things that will each waste a shot:

- **`unreal.Rotator(a, b, c)` is `(roll, pitch, yaw)`.** `Rotator(0, yaw, 0)` sets PITCH. This laid the
  hero on his back, then stood him on his head. Always pass keywords: `unreal.Rotator(roll=0, pitch=0,
  yaw=...)`. `find_look_at_rotation` returns a correct rotator - prefer it for cameras.
- **`set_animation()` does not stick and the mesh renders its reference pose.** Confirm by reading
  back `animation_data.anim_to_play`; if it is `None` the clip never applied. The working sequence is
  `set_update_animation_in_editor(True)`, animation mode `ANIMATION_SINGLE_NODE`, assign
  `anim_to_play` **through the `animation_data` struct**, then `play(True)`. `set_position()` alone
  never evaluates in the editor.
- **`get_actor_bounds()` on a skeletal mesh is a FIXED box that ignores the pose.** Grounding off it
  put the hero 108 cm in the air. Ground off the skinned asset's own bounds
  (`bottom = actor_z + rel_z + (origin.z - extent.z) * scale`), and remember **the deck is not at
  z = 0**: `SM_Floor_C` is placed at 0 but its surface is at **+10.7**, so a character grounded to 0 is
  buried to the ankles.

### Hard rules

- **Never put a window on the owner's screen.** `-NullRHI` (no renderer) for automation,
  `-RenderOffscreen` (renderer, no window) for captures and content authoring.
- **Never run two captures concurrently.**
- **Verify from 3+ angles before calling a composition done**, plus a geometric check. A terrace that
  reads pure black from one side reads as a lit plated deck from the other — the key light is at
  pitch -38, yaw 25. Shoot the opposite side before concluding anything is broken.

### The workshop

`Scripts/StationWorkshop2.py` explodes the live Blueprint into individually labelled editor actors
(`find` / `move` / `place` / `look` / `stats`) so pieces can be nudged and re-examined. It also
carries `_environment()` (key/fill/skylight/atmosphere) and `_exposure()`.

**For pure looking, do not explode.** Spawning `BP_StationVisualLayout` as one actor renders the same
thing in about 5 s instead of building 3,000 actors.

> **Stale-workshop trap.** `OpenStationWorkshop` loads an existing map *unchanged* and never rebuilds.
> A saved workshop held 392 actors while the Blueprint held 2,815. Applying from it would have
> overwritten the station with the stale copy. Rebuild before you apply — always.

---

## 4. nwiro MCP

nwiro drives the **already-open editor with a real RHI**. That is what makes visual validation
possible at all; the `-NullRHI` automation path renders nothing and creates no Niagara components.

### Conventions

Parameter naming is **not consistent** across the toolset — some tools are camelCase (`assetPath`,
`captureTransform`, `onlyIfDirty`), some snake_case (`asset_paths`). Do not memorise; make the call,
read the schema it prints back, fix it once.

### What the permission classifier blocks

Blocked, by design, and **not to be worked around**:

- `EditorAssetLibrary.save_asset` inside `execute_python` — it crashes UE on freshly created
  Blueprints (null CDO). Use the dedicated **`ue_assettools_save_assets`** tool instead; persistence
  is deliberately explicit.
- Asset rename and delete
- `play_in_editor`
- Killing processes
- Writing your own permission grants (correctly refused)

When rename/delete is blocked, build under a *new* name rather than fighting it — that is why
`StationWorkshop2.py` exists beside the original.

### Python API gaps in UE 5.8

| Wanted | Reality |
|---|---|
| `mesh.post_edit_change()` | not exposed |
| `package.set_dirty_flag(True)` | not exposed |
| `world.get_editor_property("persistent_level")` | not exposed |
| reading a map's actors **without opening it** | `unreal.GameplayStatics.get_all_actors_of_class(loaded_world, unreal.StaticMeshActor)` on an `EditorAssetLibrary.load_asset`'d map. Use this to inspect a vendor demo map without unloading the owner's level. |
| `EditorLevelLibrary` | deprecated — use `EditorActorSubsystem` / `UnrealEditorSubsystem` |
| `EditorStaticMeshLibrary.get_number_triangles` | returns 0; use `mesh.get_num_triangles(0)` |

Setting a struct property (for example `nanite_settings`) via `set_editor_property` **does not
reliably mark the package dirty**. Set it, then persist with `ue_assettools_save_assets` and confirm
by checking file mtimes on disk.

### Line traces

Two separate bugs, both of which invalidated every number measured before they were fixed:

- **`trace_complex=True` is required** or rays hit the bounding box. Symptom: every distance exactly
  equals the bounds extent.
- **`actors_to_ignore` is required** or rays hit the station instead of the target.

---

## 5. Challenges, and how they were handled

The catalogue. Each of these cost real time.

### The modal that looked like a hang

Every MCP call started timing out. Conclusion drawn: 1,793 components had hung PIE. C++ was written
and the Blueprint reverted. **The editor was never hung** — a *Blueprint Asset Compilation Error*
modal was up, and a modal blocks the game thread, so every call times out identically to a hang.

> **If every nwiro call times out at once, ask for a screenshot before concluding anything.** The
> component-count theory was wrong and the C++ written for it was reverted.

### Lights that looked broken but were only dim

38 street lamps rendered as floating sprites over a black deck. Mobility, `affects_world` and
`visible` all checked out. The actual problem was arithmetic: illuminance falls off as 1/r-squared:

```
lamp:     15640 / 950^2  = 0.017
BayLight: 120000 / 650^2 = 0.284      <- what the station already reads by
```

**16x too dim.** Three wrong diagnoses (dark material, missing lighting build, static mobility) were
reached for before the division. **Compute `intensity / height^2` and compare to 0.284 first.** Also
note the recipe writes `intensity_units = UNITLESS`.

### "Looks like it was hit by a meteor"

Pseudo-random yaws — `(i * 47) % 360` in six places — read as debris, not architecture. **Snap every
rotation to a multiple of 90.** The follow-up collision pass then created its own bugs (two plinths
on kiosk terminals; a fix that slid two trophies 10 cm apart), settled by a peer-avoidance list.
Final state: 0 intersecting solids, 0 off-grid rotations.

### A fence instead of a town

The first colony pass put one row of structures around the terrace rim. It read as a **palisade**.
Two streets per side, corner clusters and varied massing read as a settlement. Density is the fix,
not size — the slab was already big enough.

### `SM_Pilar` as a generic "vertical thing"

26 three-metre columns ringed the landing pad like a fence. The owner circled it. Replaced with 15
`SM_Sci_Fi_Bollard_Light` at 1.02 m. **Named the habit so it stops: reaching for `SM_Pilar` whenever
something vertical is wanted.**

### The asteroid that would not nest

Three attempts to seat the station inside the asteroid's crater. Measured at scale 670 the bowl is
asymmetric — **+8 m on one side, -37 m on the other at 120 m out** — and every attempt left the base
perched on a shoulder. The owner's call was correct and is what shipped: **stop fighting the rock,
build a foundation platform on it.**

### Assets that arrive wrong

- The high-poly asteroid imported with **zero textures** and a blank `Material_45`; fixed with
  `MI_Debris14A_nanite`.
- Fab glTF conversions arrive at **wildly inconsistent scales** (divide by 1.7 to divide by 20, one
  unusable). Tripo GLBs are consistent at about 1 m.
- The colony pack ships at about 1 m per module with **centred** pivots.

### "Low poly" that is not

`Ultimate_Space_Colony_Outpost_Pack`: 30 meshes, each capped at about 1.5M triangles — **45M total**
— and **Nanite off on arrival**. Nanite was enabled on all 30 and re-saved; without it they are
unshippable. Three modules (`b8d2dede`, `c30d22d1`, `de44f686`) have **magenta baked into BaseColor**
— a generation artefact, not a missing material — and are excluded.

> Check `get_num_triangles(0)` and `nanite_settings.enabled` on every new pack. A store page saying
> "Low Poly" is not evidence.

### The white-out

Interior captures came back 88% clipped and the lighting was nearly "fixed" in response. The real
cause was a **missing PostProcessVolume in the blank workshop map**. See section 3.

### Disk

45M triangles of Nanite build plus a 2.2 GB pack filled the drive mid-session and a capture failed
with *No space left on device*. `Scripts/CaptureShot.py` now deletes stale spills. Worth knowing:
`User downloaded assets/VaultCache` is about 36 GB of re-downloadable Epic installers, and the NVIDIA
shader cache is usually larger than anything in the project.

---

## 6. Kits and design direction

What is in use, and what it is for.

| Role | Kit | Notes |
|---|---|---|
| Station interior | `SciFiCorridor` | floors, walls, ceilings, crates, props. `WALL_PITCH = 539.8`, `CEIL_PITCH = 300` |
| Station rooms | `StarterBundle/ModularSci_Comm` | white/grey; a faithful copy of its own lighting reads monochrome — warm floor wash plus cool rim per wing fixes it |
| Foundation and terrace | `Megastructure_Scifi_World` `SM_floor_module_01` | 2500x2500x200, **pivot at the TOP corner** (z -200..0), so placement Z *is* the walking surface |
| Background town | `Ultimate_Space_Colony_Outpost_Pack` | about 1 m modules, used at x8-x16 |
| Ground | high-poly asteroid plus `MI_Debris14A_nanite` | scale 670 is about 1.37 km across |
| Lighting props | `Sci_Fi_Light` bollards / monoliths / neon | bollard is 8x8x41, x2.5 is about 1 m |

### Measured dimensions — do not re-measure

| Asset | Size (cm) | Pivot |
|---|---|---|
| `SM_Pilar` | 58 x 137 x 300 | corner-ish |
| `SM_Wall_03` | 540 x 100 x 307 | min-X edge |
| `SM_Celling_01` | 300 x 512 | — |
| `SM_Crate` | 150 x 146 x 120 | centred, +60.31 |
| `SM_ArmoryBox` | 83 x 132 x 40 | centred, +19.98 |
| `SM_LampFloor` | 8.8 x 17.7 x **4.4** | tiny — x4 to be visible |
| `SM_Sci_fi_Console_Game` | 52 x 46 x 133 | base at 0 |
| `SM_Industrial_Loader_Robot` | 211 x 242 x 164 | -8.89 |
| `SM_Terminal_A` | 142 x 297 x 135 | +18.91 (floats) |
| `SM_Wall_B_Glass` | 122.7 x 10.3 x 335.9 | clean corner |
| `SM_Sci_Fi_Bollard_Light` | 8 x 8 x 41 | x2.5 = 1 m |
| `SM_floor_module_01` | 2500 x 2500 x 200 | **TOP corner** |

### Geometry that matters

```
deck        X -2200 .. 4500     Y -4200 .. 4200      (67 x 84 m)
landing pad X -6100 .. -2900    Y -1600 .. 1600
terrace     +/- 12500, chamfered corners, one tier (9 m) below the deck
```

`ASSStation::Walkable()` fences the player to `|X| <= 1750, |Y| <= 1450` plus the walkway band and
the pad. **The station is 108 x 86 m while `Walkable()` is 34 x 28 m** — a known open gap. Everything
in the colony district sits outside it deliberately: silhouette and depth only, no interiors.

### Direction that worked

- **Darker, with pools.** Cut intensity hard and pull radii in, so the place is lit *where something
  is happening* and dark between. Even grading reads as a showroom.
- **A base/outpost, not a floating station.** Exterior courtyards and a landing pad are fine; the core
  is interior with a roof.
- **Build the ground.** A foundation platform beats fighting terrain.
- **Zone it.** Habs, industry, tanks, containers, masts in distinct districts, each on a street.
- **Tiers read.** Station high on its foundation, town one step below on the terrace.

### Deferred, by the owner

- Verticality and facade buildings for skyline — "years down the road"
- The bubble dome — waits until there is something tall underneath

### Cost discipline

Most questions about the game are answered by **looking at it once**. Reaching for a full
instrument-rebuild-measure cycle first is the habit to break. Ask before investigating anything
unasked; noticing a defect is not authorisation to chase it.

**"67 tests green" was never the thing worth buying.** The suite runs headless, against source, on a
machine that has the licensed content. None of those three things is true of a shipped build.
