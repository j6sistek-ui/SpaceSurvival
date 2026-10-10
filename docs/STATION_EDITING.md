# Station editing and preserved Workshop

**October10 Central authoring:** candidate107 adopts four new Central recipes
(`RefineStationCentralArchitecture`, `RefineStationCentralFeatures`,
`RefineStationCentralCheckIn`, `RefineStationCentralLightGarden`). Do not replay
their one-shot stages. The bounded three-mesh planter end-cap correction is now
saved and passes CPU asset reload119/124; do not reapply it or scene actors.
Rendered work remains held by the owner's CPU-only instruction. The fixed generated target-v2 and native pictures are in
the [concept receipt](validation/2026-10-10-central-hub-concept.md). Existing owned kiosk, P4/Clinic kits
and Nanite Plants assets supply the authored scene; no new service mechanic.
Current owner scope is Central first, R second, plus the explicit Joy color and
animation-transfer exception. JoyLightBlue117 is a private preview asset with135
clips/two groom bindings; no permanent actor placement. Rendered motion/contact
review remains pending. [CPU evidence](validation/2026-10-10-joy-blue-cpu.md).
Other areas and NPC repairs remain held.
The October9 pause below is historical.

**October9 handoff:** work paused with central/R unfinished and later priorities
held. The adopted `Scripts/RefineStationDockAtmosphere.py` is preserved source;
do not replay its creation/correction stages. Final standing workers replace
rejected kneeling poses; original source assets remain intact. Joy's private
reference-pose review asset has corrected hair alignment and translucency;
animation/groom binding/behaviors are unverified. Import helpers, backups and
diagnostics remain local. No permanent diagnostic actors were saved in the map.
[Handoff and scope](validation/2026-10-09-station-handoff.md).

**Current Wayfarer layout work:** open `C:/Users/j6sis/SpaceSurvival/Edit Current Station.cmd`. It opens `/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime`, the station used by the current game, in the canonical project's normal Unreal editor. This is also the editor startup map. Stop Play before editing, save the map, then press Play to review through the normal Survival game. [Building library](BUILDING_LIBRARY.md) covers ULAT, native collections and complete assemblies in this project.

The current station was derived from the original outpost, but routine current-station edits now go directly into this Wayfarer map. Play redirects to `/Game/SpaceSurvival/Maps/Survival` so the game creates its player and streams the station once. Preserve service actors, doors, connectors and the player berth when dressing the scene. The apartment level `/Game/BuildingLibrary/Home/L_CrewApartment` is shared by its instances: duplicate both its level and Blueprint before making an independent interior variant. Saving local changes does not update an existing Windows package or itch. [Project State](PROJECT_STATE.md) owns build/release and verification status.

The original `/Game/OutpostSandbox/L_AsteroidOutpost` remains a separate experiment, opened by `Edit Outpost Sandbox.cmd`. The purchased-kit studio `/Game/Blender/Sandbox/BuildingSandbox_20260922` remains available through `Open Building Sandbox.cmd`, on its flat platform with a space backdrop. Both live in the canonical project alongside the current station. Edits in either sandbox do not automatically replace Wayfarer. The verified native library here covers 16,051 assets and 2,617 ULAT entries; use the native collections for complete assemblies and the 208 meshes skipped by ULAT registration. [Building library](BUILDING_LIBRARY.md) records the complete 2,825-mesh Blender cache and thumbnails.

The native `CurrentStationVerification5` check confirms Play reaches Survival/SSGameMode with one current station and its loaded apartment; all 12 checks pass and four protected map files remain unchanged. It does not establish physical-controller or visual acceptance.

## October9 crew and central/R authoring

NPC job labels are authoring conveniences, not placement restrictions. The owner
explicitly allows vendor and worker variants to join seated conversations and
other everyday activity. Give each group a purpose and fit its actual motion to
the furniture. Visually screen the model before placement: graphic nudity is
excluded from every common area, and no separate adult area currently exists.
Dancers remain outside this pass. Retain supplied costume/material identities.

`Scripts/RefineStationMarketAtmosphere.py` is also already adopted in candidate84.
It moves complete original market assemblies, preserves source assets and uses
screened covered cast/compatible existing seated clips. Private animated glass
materials preserve all five campaign images in upright original P4 frames.
The observed ComponentMask input is `None`; after any partial graph failure,
inspect before retrying. The `refine` stage records actual sightline/face/light
repairs. Never replay apply/refine on the current map. See the
[market receipt](validation/2026-10-09-market-atmosphere.md) for rollback location,
private packages, failed/corrected walking routes and current image hashes.

The concept-detail stages are `Scripts/RefineStationConcept.py` (central),
`Scripts/AuthorStationVisitorSeats.py` (four compatible seated derivatives) and
`Scripts/RefineStationArchiveConcept.py` (R furniture/display composition). They
have already been adopted: do not replay their creation stages on the live map.
They require the inspected live state/stopped PIE; initial apply uses an exact
map hash and clean packages. Later stages are bounded corrections, not a general
rollback or scene generator. Keep native backups and inspect partial failures.
The caller saves and reviews; no recipe supplies room acceptance.

Private assets live under `OutpostSandbox/StationRefinement/Concept73`,
`ArchiveConcept77` and `VisitorSeats20261009`. Native retargeting derives four
4-second seated clips for Seer, Robe, Glyph and Tendril from the owned Nyxar loop,
preserving source clips/skeletons. Six R chairs/three tables use two private mesh
copies with simple BOX collision; original owned meshes lack simple collision
and remain untouched. Two central readers have hand-attached tablets. Review
actual seat/sole/hand positions for each new cast; a compatible skeleton alone
does not establish contact or a usable pose.

Amethyst's common-area visitor actor is hidden/NoCollision and replaced by a
covered Olive clone. The original assignment recipe below is historical and must
not unhide it. Elf's exposed-body preview was excluded. Source character assets
are retained. R's wardrobe use point, source floors, five campaign display and
T hold remain; its projector adopts the new private blue holo material.
[Saved candidate, native checks and limits](validation/2026-10-09-central-r-concept-detail.md).

`Scripts/RefineStationWholeRooms.py` is the earlier central/R-only composition
recipe. `apply` and `refine_grouping` are separate reviewed stages; both require
the live map, expected disk hash, stopped PIE and clean packages, return rollback
state and never save automatically. Do not replay either on the adopted map.
It reuses complete owned P1/P3 furniture, preserves shared assembly pivots, caps
thin prop width, and creates16 child instances under
`/Game/OutpostSandbox/StationRefinement/WholeRooms20261009`. Original material
parents/maps remain. Save the changed map and those private instances together;
the script alone does not restore the current scene. Before/after native evidence,
backups and the remaining visual defects are recorded in the
[whole-room receipt](validation/2026-10-09-central-r-whole-room-review.md).

The new helpers target the **live Wayfarer map**, require PIE stopped and verify
the expected saved-map hash before changing placed actors. Back up the exact map
first. Do not reapply to an already adopted map: use `IntegrateStationCrew.verify`
and inspect current placements instead. Source meshes, materials and original kits
are preserved; the caller owns final review and saving.

`Scripts/IntegrateStationCrew.py` contains ten stable-label assignments: Dread as
bartender; Robe/Glyph/Tribal as outside merchants; Seer/Tendril reception; Olive
security; Crest courier; Warden maintenance; the historical Amethyst wardrobe
visitor, now hidden/replaced as described above. It checks
178cm mesh height, floor-level source soles, exact Skeleton identity for every role
clip and material slots. It clears old per-instance material overrides, uses unit
scale/mesh yaw−90/offsetZ−85 for these normalized deliveries and reuses the shared
head fill. Existing routes and actor identity remain intact. The produce seller
also moves behind the south stall. New models need an assignment and compatible
clips, followed by actual animated contact and lighting review; normalization is
not proof that every pose fits.

`Scripts/RefineStationCentralR.py` changes only bounded furniture, guides, lights
and props, with rollback snapshots. The complete owned Fab Sci-fi Console Game
faces the wardrobe approach; the existing service/use point remains. Eight
placed props use persistent NoCollision profiles. The pen is capped at14cm height
instead of scaling a thin mesh solely by width. Its four mechanical waiting
chairs are now hidden in favor of the concept-detail furniture above. Keep the
guide/use-point relation, two central information boards and T hold.
The terminal's monitor slot uses two private `WardrobeGuide20261009` assets, made
by `stage_wardrobe_guide` from the original SVG/PNG in
`ContentSource/WardrobeConsole`. It says "Choose your character / Interact to open";
the real service still opens the existing wardrobe UI. Stage once, inspect any
partial result rather than rerunning, and save/review those two assets explicitly.
The console monitor UVs require V flipped (`UV * (1,-1) + (0,1)`); the private
material uses gain8 and the actual saved Play view confirms upright readable copy.
Native terminal Use opens Crew Wardrobe without changing the selected character.

`Scripts/IntegrateHero178.py` adopts the separate owner's delivery without
reimporting art. It verifies the 17-package hash manifest, mesh/skeleton/materials,
eight clips and seven tail envelopes before editing only the existing Squirrel
row. The private manifest/derivation inputs are required; see
[content provenance](CONTENT_PIPELINE.md#october9-normalized-crew-and-replacement-hero).
The saved wardrobe choice is independent: an account wearing Nyxar stays Nyxar.
The replacement is available through Crew Wardrobe and is the default Squirrel
presentation, including the pilot. No fresh cockpit-contact approval is implied.

## Reusing the NPC lighting preset

October8: the refined preview checkpoint is also saved/reloaded in the live
Wayfarer map76e3c8c2. Sourcepreviewe795 stays unchanged. Use the current-station
entry above for live edits. Old preview recipes require new baselines/guard review
before reuse there. `Scripts/PromoteStationPreview.py` is the explicit promotion
adapter; the older `PrepareWayfarerRuntime.py` starts from the original outpost.
[Promotion/rollback receipt](validation/2026-10-08-live-station-closeout.md).

The shared `USSNPCHeadFillComponent` enrollment API is linked and loaded in Build49;
its focused native lifecycle case passes. Seven existing plain NPC enrollments are
saved and pass native reload. A matched Trooper/alien comparison supports keeping
the shared preset; full variant appearance and performance remain unverified. See the
[component receipt](validation/2026-10-08-npc-headfill-component.md) and
[Project State](PROJECT_STATE.md) before using it in the editor. The October7
owner-preview source is preserved; its October8 checkpoint is now also adopted
into the normal Wayfarer map.

1. Create a Blueprint child of **SSOutpostAmbientActor** for the model. Select its
   **CharacterMesh** component and assign the **Skeletal Mesh**, then choose a
   skeleton-compatible **Idle Animation**. Place the bottom of **Body** on the
   floor; its origin is the capsule center (default half-height85cm). Adjust the
   mesh's relative position/scale until its animated soles meet the floor.
   Reuse this child wherever that variant is needed.
2. Keep **Ambient > Readability** defaults. Change **Head Fill Socket** only if the
   model uses a different head bone/socket; adjust **Head Fill Offset** only if
   the face needs it. The shared lamp and lighting channel are configured for you.
3. Check the moving face from the actual player camera. Construction and BeginPlay
   refresh the lamp automatically; after runtime mesh, material, socket or preset changes, call
   **Refresh Readability Lighting**. Keep channel2 off room geometry.

The shared defaults are40lumens,100cm reach,12cm source radius and an actor-frame
offset of(45,0,15)cm from the head. Ambient actors retain their original
`NPCHeadFill` point-light subobject, settings and **Refresh Readability Lighting** API.

For an existing plain **SkeletalMeshActor** NPC, call the Blueprint-callable
`USSNPCHeadFillComponent::EnrollNPCMesh`
with that actor's skeletal mesh component. It returns the reusable configuration;
set **Head Fill Socket** or **Head Fill Offset** only when the model needs it, then
call its **Refresh Readability Lighting**. Repeated enrollment reuses the same
configuration. The caller owns saving; enrollment does not replace the actor,
sequence, mesh or animation. Known runtime staff builders enroll their explicitly
selected staff components automatically; there is no world-wide skeletal scan.
The seven current plain actors use their mesh as **Offset Frame** and(0,45,15)cm
**Head Fill Offset** for their mesh-forward orientation; this preserves the common
40lm profile. Do not copy that orientation override to an unreviewed model.

To undo a plain actor's enrollment, call **Disable And Restore Receiver**, then
destroy its configuration component. Disable restores the receiver's prior
channel2 and hides the light; destruction removes only a light created by that
configuration. An Ambient actor's borrowed original light is retained. Channels0/1
remain unchanged; player lighting keeps channel1. The head attachment needs no
additional Tick.

All `APawn` owners, including the player and ship, are excluded. Receivers named or
tagged `StationCompanionDrone`, `OutpostRole:Hologram` actors/receivers, missing head
anchors and meshes without opaque/masked materials also skip the fill. Ambient
actors retain their **Drone** and **Animation Managed Externally** exclusions;
other drone/projection models require those explicit tags. Reload readback finds
one configuration on each of34 existing Ambient actors:25 lights visible and9
excluded. The seven new plain-actor enrollments preserve pose, animation and bounds
and pass idempotence. Saved reload verifies one configuration/visible head-attached
light per actor, the same profile/frame/offset and unchanged pose/animation/bounds.
Fresh saved-scene Play appearance and full variant coverage remain unverified.
Check each new variant's moving face, room spill and performance. Preserve the
bartender's existing model/clip/grounding and measured bounds-scale4 workaround;
do not copy that workaround to every NPC.

## Preparing a room's five ad sources

`Scripts/StationAdCampaignSet.py` checks a manually reviewed five-campaign manifest
without importing Unreal or changing files. With the existing Python runtime, run:

```powershell
python -B Scripts/StationAdCampaignSet.py <manifest5.json> <reviewed-SHA256> --room R
```

Use `--room Market` or `--room L` for those rooms. The prepared private folders are
`.agent/local/StationRefinement/CustomizationCampaigns20261007`,
`MarketCampaigns20261007` and `LoungeCampaigns20261007`; their exact reviewed hashes
are in the [source-set receipt](validation/2026-10-07-room-ad-source-sets.md).
The checker verifies the selected files and declared campaign identities. Different
hashes or IDs do not prove different campaigns; that still requires artwork review.
Aspect variants count once. Changing the selected variant requires a new manifest
review and hash. The current lounge selection is portrait; its landscape alternatives
are preserved separately, and neither selection establishes physical screen fit.

When native work is authorized, the lead may explicitly call
`stage_textures(unreal, manifest_path, reviewed_sha256, room_id, stage_id)`.
It creates five **unsaved** textures in a fresh room-specific folder beneath
`/Game/OutpostSandbox/StationRefinement/`, using sRGB/BC7 and clamped texture edges.
All destinations must be absent before the first import. It excludes T and central,
never overwrites, assigns a screen, changes an actor or saves a package. On failure,
preserve `StageError.report` and inspect partial imports before choosing the next
action; do not retry under a new name to hide them. Texture compilation, native
dimensions, screen ratio/readability, all five cycle transitions and explicit saving
are separate subsequent checks. On October8, all three five-texture sets passed
native source/dimension/settings readback and were saved in private folders with
suffix `20261008A`. No screen assignments or cycling checks followed from those
imports. Do not rerun the helper against those occupied destinations. See the
[native checkpoint](validation/2026-10-08-editor-recovery.md).

R's later upright P4 frame/pane and two campaign materials are now saved in the
separate owner-preview map. The corrected eleven-shot capture passes preservation,
and root/independent peer identify all five upright, contained campaigns. Build49
reload exposed a restored BlockAll profile on the two added actors; only their
profiles were repaired to persistent **NoCollision**, saved and reloaded with
read-only adoption PASS. R adoption also passes after the later seven-NPC map save.
Post-reload playback, continuous crossfade review and owner
approval are still pending. See the
[display receipt](validation/2026-10-08-customization-display.md).
`Scripts/RefineStationCustomizationDisplays.py::check_adoption` checks the existing
saved pair with the reviewed **current** map hash and its loaded `MI_R_WestBay`.
It does not assign, save or prove playback. Do not call `apply` over those existing
roles or reuse old trial globals after reopening. Market/L texture imports do not
imply corresponding display assignments, and T's hardware choice remains held.

## Current station in Blender

Use **SS Prefabs > Export Current Station to Blender**, then **SS Link > Scenes > Open Current Wayfarer** in Blender. The loaded snapshot has 12,315 mesh placements: 7,172 editable direct placements and 5,143 locked references, including 924 apartment placements, from 423 unique assets. Move direct placements with **Push Selected**; edit the functional Blueprint assemblies, doors, lighting and animation in Unreal. See [Prefab live link](PREFAB_LIVE_LINK.md#current-station-workflow-ss-link-050) for the preservation checks. The full station is open in Blender and saved as `Artifacts/WayfarerBlender/Wayfarer-Working-20261006.blend`; the previous Blender scene remains in that file.

## Legacy Station Workshop

The instructions below preserve the older Workshop workflow. **Save + Apply writes `BP_StationVisualLayout`; it does not update Wayfarer or the separate building sandbox.**

**Historical September21 reset:** gameplay selected the separate `StationReset/BP_StationReset` when installed. This workshop and the legacy Blueprint/Blender instructions below still write `StationVisualPass/BP_StationVisualLayout`; applying them does not change the active reset layout. Keep those original layouts as preserved authoring sources. The reset's recipe, ownership checks and matching physical solids are documented in [Station authoring](STATION_AUTHORING.md#functional-reset-layout--september-21-owner-redesign). That recipe remains the older fallback; it is not the Wayfarer editing process. The Workshop has not been migrated to Wayfarer.

**Open `C:/Users/j6sis/SpaceSurvival/Open Station Workshop.cmd`.** It opens the working Unreal project directly into the saved workshop. If the editor is already open, use **Tools > Station Workshop**, then **Open Workshop**. No additional plugin purchase is needed.

This is an editor authoring tool. It uses the normal Unreal viewport for selection, movement and undo, with a focused asset/material panel. It is not an in-game construction mechanic. The workshop is the source for legacy visual station placement; gameplay collision and interaction locations are still separate and their reported bugs remain open.

The panel can be undocked by dragging its tab beside the viewport, or resized to show more thumbnails. Search narrows the imported asset catalog; preset materials remain a separate ten-choice list.

<a id="first-edit"></a>

## First legacy Workshop edit

1. In the workshop panel, search for a mesh and drag it into the viewport, or double-click its thumbnail to place it in front of the camera. Existing furnishings are individually selectable too. Press **F** to focus the selected object.
2. Use **W** to move, **E** to rotate and **R** to scale. Every supported mesh can be scaled on individual axes. Use the Details panel for exact numbers, **Alt+drag** to duplicate, **Delete** to remove and **Ctrl+Z** to undo. Grid/rotation/scale snapping is in the viewport toolbar.
3. Click **Save + Apply**. This saves the workshop and updates its legacy station visual Blueprint. The previous saved map/Blueprint is backed up before application. A result message confirms success or explains why nothing was applied.

**Save + Apply changes the legacy authoring assets, not Wayfarer, a packaged executable or itch.** Normal Survival now prefers the runtime Wayfarer copy, so restarting Play is not a way to apply Workshop edits to the new station. Playing the Workshop map remains an editing preview with the base GameMode and no survival loop.

## Inspect the complete alien world

**Historical gallery instructions:** the ALIEN WORLD gameplay service was removed on September22; the owned maps remain library resources. The following describes the earlier viewer and is not a current game entry point. In that older implementation, players could play `/Game/SpaceSurvival/Maps/Survival`, close the opening menu and approach the cyan **ALIEN WORLD** doorway in the home hangar or a station. Press **E / A** at its prompt. This opens the complete owned `L_Showcase_level` for visual inspection. **Tab / Y** switches to the pack's complete `L_assets` layout; **Esc / B** returns to the station and original walker position.

| Gallery action | Keyboard/mouse | Controller |
| --- | --- | --- |
| Move / look | WASD / mouse | Left / right stick |
| Rise / fall | E / Q | Right / left bumper |
| Fast / slow movement | Shift / Ctrl | Right / left trigger |
| Showcase / asset layout | Tab | Y |
| Reset view | Home | Start |
| Return or cancel loading | Esc | B |

The labeled evaluation camera flies without collision so you can inspect large structures from any side. Run progression stops during review, and the existing station and session remain in memory for return. This is a viewer: movement does not edit, export or save vendor placements. Use the Workshop to arrange selected assets in your own station. If the owned map is missing, entry reports that it is unavailable and leaves the station in place.

The September16 capture `3bc9ba3b7f2a42c8a3899b57ae024b38` belongs to that retired scripted viewer. It is retained as asset-inspection history, not evidence that the current game has a gallery doorway. See [owned gallery authoring](BUILD_RUN.md#spatial-areas-and-alien-gallery) for the preserved maps.

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
4. Click **Compile**, then **Save** in the Blueprint editor. Review this legacy asset in its own preview; normal gameplay now selects Wayfarer, so restarting Survival does not apply these edits to the current station.

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

## Verify a saved legacy layout

These checks concern the legacy Blueprint, not the current Wayfarer runtime copy. Use the scoped [OutpostReview fixture](BUILD_RUN.md#wayfarer-gameplay-and-preserved-building-areas) for the latter, keeping scripted service/geometry evidence separate from actual walking and physical input.

Restart the legacy preview and check the approach, exit path, every service and launch from the normal game camera. Confirm that removed native props have not reappeared, the staff and screens resolve, and the scene contains the edited furniture and lights. Native `SpaceSurvival.Integration.StationEditableLayout` automation checks actual Blueprint loading, fallback, nonblocking components, unchanged collision/service anchors and ownership cleanup. The separate native visual-clearance and exterior tests continue to cover fallback presentation. Rendered art quality, owner edits and representative performance still require review in the game.
