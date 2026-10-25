# Kraken: fitted model, native groom and station walking

October 15, 2026. RPT-20261015-03. The owner accepted the walk for now and
explicitly authorized game integration, superseding the earlier asset-only hold.
Other animation improvements are deferred. Cyborg, Silver and Abyss are outside
this change. No new packaged build or release is claimed.

## Saved result

The local current Wayfarer station contains `Crew/Kraken visitor` and its attached
`Crew/Kraken fitted hair`. The existing native `SSOutpostAmbientActor` performs
walking and turns; no new movement system, runtime code or Blueprint event graph
was added. A 70 cm capsule follows a tested southern/eastern atrium route at
70 cm/s. The accepted tentacle walk is the only assigned clip; the same gentle
loop is retained during incidental stops. No gestures or acrobatics are assigned.

The hair uses the owner's MetaHair162 strand groom, with a fitted head-socket
attachment, black color, roughness .62 and specular .16. It moves with the head;
strand simulation is disabled. This supplied hairstyle is shorter and wider than
the waist-length reference. Hair physics and full-animation collision are not
claimed. The native groom is not embedded into the Blender master.

Native assets are private under
`/Game/SpaceSurvival/Licensed/StationAssets/KrakenRefresh_20261015`:
`SK_Kraken`, `SK_Kraken_Skeleton`, `A_Kraken_Walking`, `BP_Kraken`,
`G_Kraken_MetaHair162`, five materials and twelve texture maps (22 packages).
They remain on this machine and are not redistributed in the source PR.
Four mesh material slots are matched by imported name, rather than assuming
Blender and FBX slot orders agree. Base-color maps use sRGB; normal and packed
metal/roughness maps use their appropriate non-color import settings.

The groom is a separate attached actor in the same streaming level. Retain it
with the NPC when moving or duplicating the placed character. The first Blueprint
component attempt lost its socket and was rejected. The final saved pair survives
reload and normal Survival station streaming with the `head` attachment intact.

## Verification

- Saved station SHA-256:
  `edeeed766c8a9a63887cb23a6e6973493dcd293526c29815f93e6adf59f80dc2`.
  Baseline `3fb8df40db7f91cfdfab2ff1d5d961be5331d5a2ab8063db92777d7717129d33`
  was copied before changes. The 9,414 existing actor identities, labels and
  transforms are preserved; only the NPC and attached groom were added, totaling
  9,416 actors. The original map GameMode was restored before saving.
- Saved map reload verifies mesh, exact compatible skeleton/clip, six route
  points, capsule and head attachment. The temporary capture actors and preview
  GameMode were not saved.
- The first 520 cm circular route encountered reception furniture and was
  rejected. Sweeps with a 75 cm radius identified clear edges of the outer arc;
  the final route retraces those edges rather than crossing the desk.
- Actual native NPC simulation in the station: 70.02 seconds, 141 samples,
  48.39 metres traveled, zero stationary sample pairs, stable capsule height
  87 cm, and all four unique waypoints approached within 27 cm at half-second
  sampling. Eight 1600x900 views were captured; representative full-body views
  were visually inspected for hair attachment, appearance and floor clearance.
- Normal `/Game/SpaceSurvival/Maps/Survival` startup with `SSGameMode` streams the
  saved NPC and hair. A separate 20-second / 41-sample check records 13.96 metres
  of movement and the correct hair parent/socket in every sample.
- Four additional 1600x900 scene captures from that actual streamed game world
  show full body, face, side and back using the same camera position as the
  temporary player camera. The separate ordinary `Shot` attempt captured the
  wrong editor viewport and is rejected; it is not player-viewport evidence.
  No station lighting was changed. These images retain the station's existing
  strong light/shadow contrast.
- Native module identities: runtime `bff8ea9a`, editor `ffedc271`. No C++ changes
  or rebuild were required for this content/authoring-recipe change. Existing
  `BP_Blinds` material Accessed None warnings recur during station startup;
  the Kraken actor still loads and moves. These pre-existing room warnings were
  not hidden or fixed as part of character integration.

This is bounded native walking and visual evidence, not physical-input play,
all-animation acceptance, representative FPS/VRAM profiling or a cooked test.
The owner retains the final appearance decision.

## Sources and recovery

Editable delivery: `C:/Users/j6sis/OneDrive/Desktop/MODELANDRIGKRAKEN_FITTED.blend`
(`e3b0092e`). Original Desktop `MODELANDRIGKRAKEN.blend` remains unchanged
(`aa601537`). The fitted body plus armor totals 181,357 triangles and 243 bones.
Local neck and arm-cut boundary checks report zero open edges in those repair
regions; the original hidden hip contacts mean this is not a globally manifold
mesh certification. Full lower-tentacle separation caused visible slits and was
rejected. The retained lower surface remains continuous with some fused contacts.

The original 17 clips and donor rig are saved as asset-marked Blender actions in
`C:/Users/j6sis/OneDrive/Documents/Blender/Assets/Animations/Kraken_17_20261015/Kraken_Original_17_Animations.blend`.
Curve hashes match the original. Separate adapted copies are retained in
`Kraken_Creature_17.blend` and the fitted master. Their existence does not imply
all seventeen are visually accepted; the owner deferred that work.

Owned groom source: `g_metahair162.mhpkg` under the downloaded MetaHair162 Fab
library's `metahuman/UE_5.6` directory on M:. No acquisition or host installation
was performed. Native strand import uses the installed Unreal HairStrands plugin.

Ignored evidence and authoring root in the canonical checkout:
`.agent/local/Kraken_20261015`. Key receipts are `FittedDelivery.json`,
`OriginalsVerified.json`, `NativeCopy.json`, `FinalRoute.json`,
`FinalStationWalking.json`, `StationActorsBefore.json`, `StationAdopted.json`,
`StationReloaded.json`, `ActualGameProbe.json` and `ActualGameWalking.json`.
`StationBeforeKraken.umap` is the pre-adoption backup; never blindly restore it
over subsequent owner work. The final FBX and maps are under `Export`; failed
geometry, route and attachment trials remain separate from the adopted assets.

`Scripts/IntegrateKrakenNpc.py` is the bounded deployment recipe. Its preflight
checks the prepared assets, compatible skeleton, unchanged map, clean editor and
route clearance. Staging refuses duplicate placement and does not save the map.
Use `verify(unreal)` on an already adopted station, rather than replaying staging.
The equivalent retained local authoring steps created this reviewed placement.

Source checks: 45 structural checks, Python `compileall`, content-source validation
(26 meshes,17 WAVs, unchanged GLB), documentation consistency and whitespace checks
pass. No C++ formatting/build or unrelated domain suite is required by this Python
recipe and documentation diff. The native Blueprint compiled successfully.
