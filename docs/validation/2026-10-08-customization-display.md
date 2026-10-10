# Customization display — saved upright placement and five-campaign capture

**2026-10-08 update: saved/reloaded with adoption PASS; bounded five-campaign visual PASS; owner approval pending.**
This supersedes the initial unsaved/pending-capture state. The second mounted fit
is accepted locally; corrected `RDisplayFixed48` completed eleven images and
finalization/preservation checks. Root and independent peer identified all five campaigns. The placement
and two materials are now saved, with a verified prior-map backup. This is not
owner approval, post-reload cycling or whole-room acceptance.
T's separate hardware choice remains held.

## Exact scope

The trial uses owner-preview `/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006`,
initially bound to saved map SHA256
`16818b1bb54d7ee6794501a2684bdf450760834d5f434af6c1a0c58423ef05a9`.
The first display save produced map
`c059ea5326d1228fe1105029699c6c7f37d4b705020c2c880400cc7537763fef`.
The later collision-profile repair saved/reloaded map
`242418570781e06a7297997a90e2c99459f6a4f622199c221b1be993a49b910e`.
The subsequent seven-NPC enrollment save/reload uses current map
`e7958758a861d17fe189601b17b486db9ea75086080a8e1b5f17e56cbb7b18db`;
R's existing adoption also passes against that map.
Build49 is linked and reopened, DLL SHA256
`e2e7b5c7ba25ce9e77f50545a6dbeea3f7f29531d332b9b9f33dcd57508560ff`.
Its full link result is separate from the display save; the
[NPC component receipt](2026-10-08-npc-headfill-component.md) records that build.

- New `StaticMeshActor_7721` frame and `_7722` pane share position
  `(2927.318441390991,3221.666666666667,75)`cm, yaw180 and unit scale.
  Assets are P4 `SM_Window200X250_V1_Part1` and
  `SM_Window200X250_V2_Part2_DigitalWindow` under
  `/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/`.
- Native LOD0 room-facing section1 maps to material slot1. Only that pane slot
  receives the new campaign MIC; original frame slots and rear glass remain.
  The local contained art rectangle is Y[-67,67], Z[24.5,225.5]:134×201cm.
- Decorative SmartStorage panels923/924 become invisible; existing solid backing925
  becomes visible. These are three specific visibility changes, not window, service
  or room-light replacement. The two added actors are NoCollision.
- Two private material objects, `M_R_UprightFive` and `MI_R_WestBay`,
  are under `CustomizationCampaigns20261008A/Materials`. The opaque/unlit/two-sided
  thirteen-expression graph uses the five already saved R textures in order:
  Morph Clinic, Hologram Doctor, Zero-G Massage, Vacuum Valet, First Contact Photo.
  Each complete portrait is contained without stretch/crop. Native timing is20s
  per campaign,0.6000000238418579s crossfade, phase0 and brightness8. Time uses
  the ordinary paused-game clock; source seed/artwork remain unchanged.

## Retained results and repairs

The first three-view fit had a visible backing/mount gap and was rejected visually,
despite successful capture/restoration. Moving both actors from X2930 to the exact
position above and unhiding backing925 produced the second locally accepted fit:
upright readable art, native case thickness and a coherent solid-wall installation.
Physical bracket contact, collision/traversal and fine-print readability at distance
are still unverified.

`RDisplayCycle48` captured seven views, including transitions; overlapping titles
did not prove steady readability. Independent review of **all eleven**
`RDisplaySteady48` images found only four identifiable campaigns: Morph Clinic
(01/10/11), Hologram Doctor(02–05), Vacuum Valet(06/07), First Contact Photo(08/09).
The distinct Zero-G Massage campaign was absent from those identifiable frames.
Technical capture success is retained separately from this visual failure.

R03's native export contains the correct selected source, and native graph readback
confirms all five texture parameters and Custom input links. That does not prove
all five are visible. A narrow candidate repair changed float-remainder indexing
to integer modulo. Its first variable name `step` shadowed HLSL `step()` and failed
compilation. Renaming only that variable/reference to `cycleIndex` compiled with
no errors. Floating-remainder truncation remains a proposed cause, not a proven
diagnosis. Corrected native adoption checks pass two roles/three visibility changes,
exact geometry/material/timing/source checks, zero new assets and no map save;
their visual/cycle result explicitly remains unverified.

Completed Fit/Cycle/Steady manifests record1014×344 ordinary Play images, original
view restoration, camera destruction, stopped PIE and unchanged map bytes, player
saves, editor world, dirty package lists, viewport and quality. They explicitly
claim **no full-world equality**. The map and two materials were dirty during those
unsaved captures; the later save below cleared both dirty package lists.

## Corrected capture and save — October8 supersession

`RDisplayFixed48` completed eleven1014×344 ordinary Play images, stopped PIE and
passed the same view/camera/map/save/editor/dirty/viewport/quality finalization
gates with no errors and no full-world equality claim. Root identifies First Contact
Photo in02, Morph Clinic in04, Hologram Doctor in06, Zero-G Massage in08 and Vacuum
Valet in10. The independent all-eleven-image review at2026-10-08T01:37Z passes
upright complete illustrations, titles, lower copy and original borders, including
the previously missing Zero-G Massage in08/09. This supersedes the earlier
missing-R03 limitation for the corrected capture. Sampled frames across101.174s
do not prove uninterrupted playback or crossfade smoothness, saved reload or owner approval.

`RDisplay48_Save.json` records `SAVED_VERIFIED_PLACEMENT_AND_MATERIALS`, two material
saves and a map save, exact read-only adoption after saving, empty dirty map/content
lists and `owner_approval:false`. The backup
`.agent/local/Outpost/RDisplay48_SaveBackup/OwnerPreview.before.umap` retains exact
initial map16818. Saved material hashes are:

| Private material | SHA256 |
| --- | --- |
| `M_R_UprightFive` | `de926404b21a8c0e523762dd20b34a4e60a33f9a365ce64c9249ecca8307122c` |
| `MI_R_WestBay` | `4a6c0df4be92165ee285d4c0a0b6853ee1dbac2a9190b3a47a6b39af509e963b` |

Saved bytes, backup and empty dirty lists were rechecked from retained receipts/local
files. The later reload repair below supersedes the pending adoption/reload check;
post-reload playback remains pending.

## Reload profile repair — October8 supersession

After Build49 reopen, both added actors restored the **BlockAll** profile with
QueryAndPhysics despite the earlier NoCollision setting. Native poses, materials
and attachment state matched. Root changed only the two profiles to **NoCollision**,
checked exact adoption and saved the map; no material/art/timing edits accompanied
this repair. `RDisplay49_ProfileRepair.json` records map242418 and backup
`.agent/local/Outpost/RDisplay48_SaveBackup/OwnerPreview.c059-before-profile.umap`,
whose bytes match the prior c059 map.

Native `ReloadMap` followed by `RootNPC49_Reopen2Result.json` passes read-only
adoption: two roles, three source-visibility changes, no new assets, the same
134×201cm rectangle/front slot1 and no save performed by the check. Both dirty
package lists are empty. This supersedes the repair receipt's initial
`reload_verified:false`; the helper still explicitly does not prove visual fit or
cycling. Fresh post-reload playback/crossfade and owner acceptance remain open.

The later `NPC49_ReloadVerified.json` checks the same R pair after saving/reloading
seven NPC instance enrollments in mape7958758. R adoption again passes two roles/
three visibility changes/the same rectangle with empty dirty lists. The prior242418
map is backed up before that NPC-only save. This advances the current map identity
without adding new R fit/playback or owner-approval evidence.

## Evidence identities

Local receipt paths below are relative to `.agent/local/`; hashes bind the reviewed
files, not approval of their contents.

| Evidence | SHA256 |
| --- | --- |
| `Outpost/RootReopen47_CustomizationSave.json` — five saved textures | `41666a6ebd32f16d289141518ec1377a0416c7d5aed037bd7e1e0367793eb370` |
| `Outpost/RDisplay48_Trial.json` — second fit scope | `069d2e56936fb03333b46812de9f3789a2d50159e765ff9abd11962dc3a5541d` |
| `Outpost/LiveOperationsPIEReview1_RDisplayFit48/manifest.json` | `7ad6637c544bfdd06d64af47342912e9f1705f54aa65a48f55bad85baa80948e` |
| `Outpost/LiveOperationsPIEReview1_RDisplayCycle48/manifest.json` | `494cb5fa1f12671fa5c3dffbe98d64e7fac712ddcce55b993001ffd7cafd57c1` |
| `Outpost/LiveOperationsPIEReview1_RDisplaySteady48/manifest.json` — finalized | `edbeddc05aa4f57b6d1b85e77e86fee535accaccabf2386ebf923b2b850686d9` |
| `StationRefinement/RDisplay48VisualPeer.md` — prior failure plus Fixed48 PASS | `7501aab3b772636186308633d313cbaf67978b354d87663d404c1c9137c59331` |
| `Outpost/RootRDisplay48_GraphRead2Result.json` — five bindings/links | `a63b9e5ffcf4d8f46b92c857652a5c6c9fa66bfe7ccb2c8941461a7035bc6bd2` |
| `Outpost/RDisplay48_R03Native.png` — retained export preview | `89c53502c22ca41bce32aabfd8af19e4a14758eda26b53b4d134d64aff2ac9f8` |
| `Outpost/RDisplay48_IndexRepair.json` — failed `step` candidate | `3e1e85c33332a6690ada40fd650627cd6c819e4a414daa4c8c9197dbc8313a70` |
| `Outpost/RDisplay48_IndexRepair2.json` — compiled `cycleIndex` candidate | `a6ed24862570fdfaf696c44b96b870147573938f34fb4b69ee8c023d97a1f54b` |
| `Outpost/RootRDisplay48_DurableCheckResult.json` — read-only adoption | `d631d396ba2742ddfa5c136822c0e4f8aa34fb7ddf5c14b9f845c55c753be860` |
| `Outpost/LiveOperationsPIEReview1_RDisplayFixed48/manifest.json` — finalized | `c4b9b158d250d94170740b19adf0decf17d21f67d582b199bedd0b027fe1aace` |
| `Outpost/RDisplay48_Save.json` — saved map/materials | `01046c9131c3c6d1e3d22b9d199323c7564b5953f5746e3a0c9727e7008b581c` |
| `Outpost/RootRDisplay48_SaveResult.json` — native save return | `b1a4de8cf48eb8e70ac50839786bed8f1680339b06ac35d0c7da876dd8dcd1fb` |
| `Outpost/RDisplay49_ProfileRepair.json` — two persistent profiles/map save | `3ed2f2097facbf5f038e0ec11512069a197044f9343d3f62380766b99507ef8b` |
| `Outpost/RootNPC49_ReloadMapResult.json` — actual reload | `c6d471063a6508727cd01e63b65287e77a752436fb723bc5fc311ad57336603a` |
| `Outpost/RootNPC49_Reopen2Result.json` — post-reload adoption/clean packages | `41f727ec62eae6f006719a97578c6b5d3cdcd7eb9d339c859f5fe5abf8580899` |
| `Outpost/NPC49_ReloadVerified.json` — final-map R adoption after seven-NPC save | `72f2c060f5c1e45e7618cd8f3210daf2ea1713a6e40e4439128bae8bb2f1b41b` |

`Scripts/RefineStationCustomizationDisplays.py`, SHA256
`1be08f1a30faefa5da45080bdf8cc7bc56be83a737b9f1d4e4f144596b38b59c`,
records the repaired geometry/shader and persistent **NoCollision** profile in both
placement and read-only `check_adoption`. This supersedes the pre-reload recipe hash
`352f460e83b8c6618b608df0627c4b9b0cba4ec8ace3dc28e92c159f4dadcd53`.
Fresh `apply` requires separately prepared assets and absent role actors; it never
imports, authors materials, loads/saves a map or starts PIE. It cannot take over
the existing trial. The earlier root trial helper SHA256 is
`1d484c602564cbd8100f907fe2d3b7ccd28b16b5d8ec667b0509ab745804f073`.

`r_display48.STATE`/`r_durable48` globals are editor-epoch references, not durable
packages. Do not reuse trial rollback after reopen or rerun placement over the saved
roles. `check_adoption` can inspect the saved pair using its new reviewed map hash
and loaded private MIC; it neither acquires trial ownership nor proves playback.
Fresh `apply` remains for absent roles only. The lead must verify post-reload
playback and obtain owner acceptance separately from the prior bounded visual pass.
