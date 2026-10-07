# T Operations Phoenix podium — 2026-10-07

Recorded at 2026-10-07T03:42Z; Capture6 and independent visual review added after
its 2026-10-07T03:46:58Z completion. **PARTIAL: the separate owner preview is saved
and natural rotation passes; visual quality is unfinished.** This implements the central
glass Phoenix display requested under RPT-20261006-04. T room quality and owner
approval remain open. The accepted L lounge, canonical station, gameplay service
behavior and published package are preserved.

## Saved scope and native result

The lead-run fifth author transaction passes its fixture and preservation guards;
the lead independently observes native exit0. The receipt's process-exit field is
unset, so its success field alone is not the process-exit evidence.

- Map: `/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006`.
- Input SHA256: `3e3f187c81de87f2fc14b2fc8f57d624ef82c6a2bbf1321eb0c764b9dad2c49f`.
- Saved SHA256: `bcadec049db0bf58c5a5a1c511ac3e7fce34f7e7ac1876a03b526e7146b83639`.
- Canonical Wayfarer remains `9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.
- Author receipt: `.agent/local/StationRefinement/StationOperationsComposition5.json`,
  SHA256 `2944f5f19ed180afcb7f8511933bc4e04135b3053ddebe76eb092f8cf39ac8ce`.

A 4.8 m octagonal enclosure centers at `(8170, 0)` cm. Its fitted native metal base
ends at 105 cm and framed clear glass reaches 285 cm. The supplied Phoenix hull,
both supplied engines and airbrake form one complete 3.2 m hologram centered at
190 cm. A neutral pivot has a private linear 60-second yaw loop with infinite
autoplay. There are no camera, input, gameplay, sound or particle tracks.

The 54 hardware actors use owned P4 Smart Storage panels, P5 profiled posts and
the restaurant projector. Four explicit native mesh actors, one pivot and one
sequence actor bring the addition to 60 actors. Five new private assets are saved
under `/Game/OutpostSandbox/StationRefinement/OperationsComposition20261007`:
the octagonal plate mesh, enclosure glass, Phoenix hologram, projector lens and
rotation sequence. No light is added or moved.

## Actual source geometry and preservation

The read-only placed-Phoenix probe identifies the exact four rendered source
meshes and their world matrices. The author copies those matrices into neutral
native mesh actors and holds the original hull end-pose and airbrake initial pose.
It does not construct the supplied presentation Blueprint, its demo components
or a Pawn. Source meshes, animations, materials and Blueprint bytes remain intact.

The actual fitted four-part geometry spans 320×222.037×90.795 cm. Its bounds are
`(8010, -111.018647, 144.602449)` through
`(8330, 111.018647, 235.397551)` cm; conservative swept radius 194.743780 cm.
The guard requires the complete ship inside the glass envelope before any save.
Rebinding all four actors to the centered neutral pivot with world transforms
preserved changes measured bounds by less than 0.05 cm.

Native floor traces support all nine podium samples. Pawn capsule traces use
34 cm radius and 75 cm half-height across the existing command approach, north
and south exterior routes at Y±460 cm, and rear connection at X8520 cm. All four
routes pass before and after authoring. The 80 cm gap behind the existing console
is an equipment gap, not a claimed walkway. These static traces are not a player
walking test.

All 8,343 pre-existing actor snapshots remain unchanged, including the complete
29-part Goliath and four 17-part staffed pods. All five service identities/anchors
and six retired label actors are preserved. The receipt verifies 1,117 protected
asset entries, six other map files and three save files unchanged. Accepted L
content and lighting receive no edit. No gameplay C++ changes belong to this pass.

## Retained failures and repair

| Attempt | Native result and repair evidence |
| --- | --- |
| Composition1 | Native exit0; unexported `set_generate_overlap_events` call stops authoring before all saves. The repair uses the installed5.8 exported editor property. |
| Composition2 | Native exit0; source-prefix guard rejects an unexpected placed render component before all saves. The exact source inventory is probed instead of accepting a broader prefix. |
| Composition3 | Native exit0; template-name mapping cannot prove the complete placed hull and engines. No saves; the new actual placed-actor probe records instance names, classes, meshes and matrices. |
| Composition4 | Native exit0; Blueprint construction produces unexpected `TRASH_SkeletalMeshComponent_5`. No saves; the guard remains strict and author5 uses four neutral mesh actors without Blueprint construction. |
| Composition5 | Author and preservation pass; lead observes native exit0. Five private assets and the owner preview save. |
| CompositionCapture5 | Native exit0; runner fails before images because the installed Python API exposes `sequence_player` as a property, not `get_sequence_player()`. Files/saves remain unchanged and PIE stops. New Capture6 uses the exact successful pool runner's property and qualified-time access; no room reauthoring. |
| CompositionCapture6 | Six actual saved-room SIE images and natural rotation pass; lead observes native exit0. Files, saves and ships remain unchanged and PIE stops. Podium material finish fails visual review. |

Every failed author preserves protected sources/maps/saves. Its helper, wrapper,
capture input and receipt remain in immutable ignored `FrozenOperationsCompositionN`
history. The original composition helper remains frozen for density-probe dependencies.

## Frozen input identities

Paths are relative to `.agent/local/StationRefinement` unless prefixed `Scripts/`.
Raw native logs, receipts and screenshots remain private/ignored.

| Receipt or input | SHA256 |
| --- | --- |
| `StationOperationsCompositionProbe1.json` | `594247794f1048db936dbc1beaba5284f5cfd5a80377c0ea68b1a56158b9fa39` |
| `StationPhoenixPlacedProbe1.json` | `e61db7653b772cf65c7548d15ae7ee80a517bce1f3b08d7d64191eb30396ff0c` |
| `StationOperationsComposition1.json` | `90b5feba73260a65121b273f17a4251962a7ab1f810a98b8e7022ffdc4c4d93b` |
| `StationOperationsComposition2.json` | `9ddfc079bd1986565baea993dc78e51b249149a1429fcec4fb927a069034b02a` |
| `StationOperationsComposition3.json` | `28c41e853e14e6f3d9520b8023fde31fb86ac75bcf46b201e90cd6317e87a2dd` |
| `StationOperationsComposition4.json` | `45ff455441878c87a5f053c7f3472dff21e9dd7db7a3103130c4b521a8d0f647` |
| `Scripts/RefineStationOperationsComposition5.py` | `d69ca492c266e57626389c30e7694aa0d0ffbd647f046512d5d4585ea739c9b9` |
| `apply_operations_composition5.py` | `a6981f6b41985f2f26b596673b385a092dba45f03e2c7d64ca92e43895e69b86` |
| `capture_operations_composition5.py` | `91006f6f5dc086ad3b25592a7d30f2d320f54522cddbd0dceb180e91ac2e79f4` |
| `StationOperationsCompositionCapture5/manifest.json` | `77dad1f810553858aa4d42e3c7f5a236881068cfe87449138082f009177e0425` |
| `capture_operations_composition6.py` | `877a8db9b00bc4da70bd096d100ebc897b796cb09ab6d772610e817ccf2bae5a` |
| `StationOperationsCompositionCapture6/manifest.json` | `0af2c3670848fa499f5a256b027ac177147a0c49985d5fbc0d53b5bb17edb174` |
| `StationOperationsMaterialFinish2.json` | `eb61d1045b7bc91eaa37d09a2da171b7391eac46435d498573753f46afee7691` |
| `StationOperationsDensity4.json` | `22dfb8e6565a8c0cd4272ed94087c5083642883151ec072bad8158e02a3628e9` |
| `StationOperationsDensityCapture3/manifest.json` | `9a819592026749b1f1b8c3aaaf6687caf34ec3c7b6190bcb7a6fa49e9529d49e` |

Bundled Python compilation passes for all three fifth-attempt inputs and Capture6. Installed5.8
skeletal-mesh setter, quaternion and detach APIs were checked before authoring;
the native author then exercises them successfully. A gameplay build, portable
domain tests, packaging, performance and controller checks are not established
by this presentation transaction.

## Natural motion and actual pixels

Capture6 observes 69.680770 seconds of ordinary game time across 136 samples:
418.084634 degrees of unwrapped yaw and one native sequence wrap. The actual
player autoplays its 60-second sequence at 1×, bound only to the actual PIE
neutral pivot. There is no seek, start, rate, pose or shader-time override.
All six 1600×900 screenshots complete; 1,120 files, three saves and gameplay
ship transforms remain unchanged. PIE stops. The lead verifies native exit0
independently of the manifest.

Independent review inspects all six current saved-preview views: entrance,
two matched command angles, side, reverse and matched loop angle. The glass
enclosure reads clearly and the Phoenix's complete supplied silhouette remains
recognizable at different ordinary rotation phases. The base reads as coarse
stone and the deck/plinth as white slabs, which does not meet the intended
high-tech metal finish. The ceiling and broad surrounding spaces remain plain;
staff contrast is weak. Whole T is judged about 5/10, not owner-approved.

The matching older `StationOperationsDisplaysCapture3/01_OperationsEntrance.png`
comparison already contains the noisy desk/floor reflections. Their presence
is not evidence of a regression from this podium pass. A convergence or material
root cause has not been measured, and no global source-material change follows
from these images.

## Private metal finish — saved and visually reviewed

Joint material-only revision2 completes at2026-10-07T04:07:37Z with fixture and
preservation success; the lead independently collects native exit0. Its receipt
process-exit field remains unset. The saved preview SHA is
`c7e9e99ce69b6e6fcb9a1b3dc997b03d6f97cba9ee07731c152574df54464f9d`,
superseding the earlier Composition5 snapshot for this bounded finish.
It replaces exactly 44 hardware slots on 36 podium actors with two opaque private
graphite/titanium materials. Graphite uses base color `(0.045, 0.060, 0.078)`,
metallic 0.80 and roughness 0.42; titanium uses `(0.22, 0.26, 0.31)`, metallic 0.90
and roughness 0.31. Fine world-space grain changes only roughness by ±0.02;
there is no coarse albedo noise, normal relief or emissive response.

The same transaction saves eight private children for the existing central
Goliath, retaining each native parent, texture, switch and unlisted parameter.
It saves all ten new material assets and then the owner preview once, after the
union whitelist passes: exactly 37 existing actors and 52 material slots. Both
helpers preserve actor/component transforms, mesh identities, lighting, glass,
hologram, sequence, service anchors and accepted L. Installed5.8 expression
interfaces were checked; bundled Python compilation, exact recipe hashes,
scoped diff and the podium whitelist check pass. The earlier prepared revision1
was withdrawn before native execution: the existing author at
`Scripts/OutpostWorkstationFinish.py:198` documents a5.8 setter returning false
after a correct write. Revision2 uses the full actual scalar/vector/texture/switch
readbacks after update, preserving the same union scope. The unrun revision1
inputs remain in `FrozenOperationsMaterialFinish1`. These are preparation checks,
not visual quality evidence. The actual author exercises the graph and parameter
readbacks successfully and preserves1,122 protected source entries, six other
maps, three saves and the canonical station bytes.

| Frozen candidate | SHA256 |
| --- | --- |
| `Scripts/RefineStationOperationsPodiumFinish.py` | `78f6422405eb23986d148e0283100b325a26c2b6b596b0d0126852605f92797d` |
| `Scripts/RefineStationOperationsFinishPass3.py` | `9ab29fd44c7406e52954a899b78f1fb7e26174cca5ed88fd5f61ecb6e228eeaf` |
| `apply_operations_material_finish2.py` | `c827b059e60a4de28e7bf6c033a599fe672c4801a54a70b30119657cc27b06b7` |

## Current density and actual room review

The ceiling/storage/illustrated side-display transaction remains separate; its
third author stops before imports
or saves on a fixture broad-phase guard, with preservation passing and native
exit0 observed by the lead. Its fourth author subsequently saves successfully
against the exact finish2 receipt, with preservation passing and native exit0
independently collected by the lead. Density4 adds20 fitted hardware actors and
four private assets; it retains the finish2 podium and sequence. Its saved snapshot
is `c1f62aed453362a1eacc20faeb6f9d589bae5e9f42f03053a28dd3e2c5f1371c`.
Capture3 subsequently completes at2026-10-07T04:19:07Z; the lead collects clean
native exit0. All eight1600×900 images and their hashes are independently checked:
entrance, two command angles, side, reverse, two illustrated service screens and
supported ceiling. The capture binds the current saved Density4 snapshot and
reports protected files, saves and gameplay ship poses unchanged, with PIE stopped.
The original full natural-loop proof remains unchanged; this capture does not
repeat a70-second motion test or alter sequence time/rate.

Independent review agrees with the lead's6–6.5/10 assessment. The graphite base
now reads as metal and the glass-enclosed complete Phoenix provides a strong
central focus. Both new illustrated adverts read about8/10: original subjects,
short copy and fitted physical frames are clear. The supported overhead panels
add structural depth. Podium faces remain too plain, and the central assembly
still looks excessively reflective/noisy; staff contrast and overall composition
remain below the target. These are image-based judgments, not owner approval.
The exact material-layer contribution remains unconfirmed. A separate ordinary
PIE capture completes with native exit0 at the same saved map: two actual1014×344
viewport screenshots activate the PC CameraActor and verify its position,
rotation and FOV after at least90ticks/sixseconds. The noisy chrome and worn floor
remain visible, so the defect is not entirely a high-resolution capture or missing
camera warmup artifact. This diagnostic does not prove owner-size quality or FPS.
Its obsolete `r.DefaultFeature.AntiAliasing` queries produce four retained warnings;
the registered `r.AntiAliasingMethod` reads4. The missing-query fallback0 is not
evidence that antialiasing is disabled. New comparisons omit that obsolete getter.
No light reduction, shared material edit or random geometry addition follows.

The preserved native floor probe completes with native exit0: exact84 T panels,
420 material references, ten current material instances and one377-node native
master. Actual geometry identifies slot1 as the dominant top plate and slot2 as
the secondary plate/trim. The master uses a darkening tint blend; setting white
tint cannot brighten rusty source albedo. The approved test therefore duplicates
the full master only in unsaved private memory and reconnects BaseColor, Metallic
and Roughness while retaining native Normal/AO/UV wiring and original parameter,
texture and switch values. Eight matching control/white/silver/trim frames use
the active PC camera and90tick/sixsecond warmup before1600×900 high-res screenshots.
Their capture method differs from older DensityCapture3, so comparisons belong
within the new eight-frame set. At this record update the frozen test is still
preparing materials; no completed frame, preservation result or new saved floor
is claimed. Multi-minute synchronous preparation is consistent with30 transient
instances each retaining115 native effective parameters, but expected duration
is unverified.

| New read-only/test evidence | SHA256 |
| --- | --- |
| `StationOperationsNormalShot1/manifest.json` | `ac2f08e3a82458153518f405d8c4f337bcaa2836a04402fbe119c19d51a859d7` |
| `StationOperationsFloorProbe1.json` | `e8481055d10aa1f11c896b663f95bfabdb76e8096f98d231c98f6c505b1c604a` |
| `Scripts/PreviewStationOperationsFloors.py` | `c7ba30d436cae106c191b3d8d436d5dc2cbaa2fdf7f46f5998cdc7af220c8e7c` |
| `capture_operations_floor_options1.py` | `62dbcaf8892358c7bac6687b01cccef9102d7b6fd138f22ef822a01b66e1cf4c` |
| `OperationsFloorOptionsPlan1.json` | `f1e8cd2525d79e1b5deba41bab79dae261085f8dbaccd3039ac37eb47c539817` |

The2026-10-07T05:03Z receipt records termination of only the lead's verified isolated process after
more than12minutes of synchronous material preparation; collected native exit is
−1. No images or completed capture manifest exist. Independent protection checks
retain all1164 files and three saves unchanged, and no private candidate package
was written. This supersedes the preceding in-flight status without a white
visual result. The frozen failed attempt remains intact; termination receipt
`OperationsFloorOptions1Termination.json` has SHA256
`1b7f78090a0aad2cd57c36dd15226e1f405cc2d7a2723adbe8bd74ea3b6d6391`.
A new white-only test copies the measured inherited material chains once and
sets only three added values per leaf. Stage progress receipts and an external
owned-process wall watchdog replace reliance on a callback deadline that cannot
interrupt synchronous engine calls. It is prepared for review, not run or saved.

The corrected isolated White1 retry subsequently completes at05:17:54Z with
root-collected native exit0. Its private master retains377 original nodes and
Normal/AO/UV wiring. Twenty-five cached native MIC copies retain shared ancestors,
local overrides and all effective parameters; only three new white values per
leaf are set. Preparation completes at37.97seconds elapsed. All1170 protected
files, three saves and gameplay ship poses remain unchanged; all420 temporary
floor references restore before PIE stops, and no candidate package is written.
An earlier launch was rejected before map load because of a mistyped input SHA;
its launch error/log remain retained separately from this corrected retry.

All four actual1600×900 PNGs are independently reviewed. The two podium-side
views match and show diffuse low-gloss white replacing rust, with native panel
seams and normal detail retained. The white entrance view is visibly brighter,
but the first saved-control entrance image actually shows the close side angle
despite correct PC camera-manager readbacks. That entrance pair is excluded from
comparison: the editor high-resolution screenshot API does not independently
prove its rendered POV. The capture's technical success is not a four-view
visual comparison pass. No material reauthor is required for this camera defect.
The lead approves the white finish for the owner's selected station-wide recipe;
the floor is still UNSAVED, and whole-station assignment awaits measured native
floor/slot inventory. Desks remain excessively reflective, the podium is plain,
and T has no9/10 quality acceptance.

| White-only evidence | SHA256 |
| --- | --- |
| `StationOperationsFloorWhite1/manifest.json` | `40341b218ea8909387727a0872a63a68a28b91eae26293664de4e656f2d7f5c4` |
| `Scripts/PreviewStationOperationsWhiteFloor.py` | `8bec1d913cbe8a2a882d15864b73b014ae954c5bc67a9eec36a083fcf608f56d` |
| `capture_operations_floor_white1.py` | `f98abf6aa5a332c2fdd0b2a830f2609c2cb00444a854b7d6e355ac46b198fbf2` |
| `OperationsFloorWhitePlan1.json` | `661b0ddc62776e43a25f53e7f8e95e3505ce6b842f745ea475619a99252af6fd` |

## Saved main-station white floor pass

The lead collects native exit0 for Main1 after the saved author finishes at2026-10-07T05:50Z. The owner preview
is saved with exact1,022 measured floor components and5,017 material references.
Four private full native masters and49 cached inherited MICs are saved;44 leaf
materials use whiteRGB1, metallic0 and roughness0.6. Each source and clone proves
`use_material_attributes=false`; native Normal/AO/UV graph connections, textures,
local overrides and all original effective parameters remain intact. Main1
retains all1,281 protected inputs, three saves and all original actor, instance,
mesh, collision, service and numeric-light state. No shared licensed material is
edited. Prepared revision1 is retained as unrun history; the final reviewed
revision adds the direct-material-output guard before duplication.

The new saved preview SHA256 is
`211c812516fd81a71be64c6ddd3a372b3a2a94187f56790c03bc60719a077f34`.
This is a main-floor implementation result, not full-station completion or a
fresh visual rating. The exact whitelist covers T, lounge, market, reception,
crew/archive, three berths, observation gallery, promenade and the apartment
and cargo connectors. Same-mesh exterior roofs, equipment and the market's
roof-height instance component stay unchanged. BeeCell underside slot5 and
native-market underside slot3 retain their original material.

Three combined owner foundation slabs and the curved owner ring share material
slots with sidewalls/undersides; they are deliberately excluded until actual
floor faces can be separated. The ring's retained actor label is
`Owner platform/SM_Arco_Tubo`, but its private mesh is
`SM_OwnerRing_AccurateCollision`, so the earlier asset-name predicate missed it.
The apartment and docked cargo child interiors are not in the main editor-world
inventory; their private maps require separate measured floor-only treatment.
These gaps explicitly keep `full_station_complete=false`.

A new read-only14-view capture completes its images at2026-10-07T05:54Z using the actual PC console
`HighResShot 1600x900` route from `ValidateOutpostPlay.py`. It checks the active
camera's transform/FOV before and after each shot, waits for a complete PNG,
validates1600×900 dimensions and two stable hash ticks, then changes view. It
includes representative views for every affected main-floor group. It does not
use the editor high-resolution screenshot API that produced the earlier wrong
entrance POV. All14 actual PNGs are independently reviewed: white floor panels
retain seams and normal detail; warm lounge lighting makes its white surface
read cream, while the cyan routes, berth panel patterns and narrow connector
floors remain visible. T's entrance and side are now the intended distinct
views. The market overview includes the existing player model in the foreground;
this is an occlusion in the actual game camera, not the earlier wrong-editor-POV
defect. Apartment and cargo views cover their connectors only.

This capture is a retained mixed outcome, **not a clean pass**. Protected files,
three saves and gameplay ship poses remain unchanged, and PIE stops. Its final
manifest reports `editor_scene_unchanged=false` and overall `success=false`
without a Python error. The lead collects native exit−1073741819
(`0xC0000005`) after the log's normal exit messages. The wrapper compares an exact
whole-editor actor/component snapshot before the temporary camera against the
post-PIE state after camera destruction; neither snapshot nor individual deltas
was retained. The exact difference is therefore UNCONFIRMED and must not be
reclassified as harmless from preserved disk files alone. The14 completed images
remain useful bounded visual evidence; the successful Main1 save and its clean
native exit0 remain independent. Existing apartment `BP_Blinds` runtime material
access errors recur in the capture log.

The floor appearance meets the selected main-room finish, but the independent
whole-T assessment remains about6.5–7/10, below the owner's required lead9/10.
Chrome/noisy desks, weakly lit overhead detail and broad plain podium panels
remain visible. The market close view exposes floating loose props, and visitor
ships still sit on literal blocks; these existing unfinished elements are not
floor-material regressions. No new lighting, geometry, actor placement or shared
source-material edit follows from this floor capture. Services/NPC work and
owner approval remain open.

| Saved-main evidence | SHA256 |
| --- | --- |
| `StationOperationsServicesProbe4.json` (successful floor section; later desk check failed) | `38ba0dca69bd5d17709fe6fb923f1843e4c0771cfb789a20e4c931287e41383d` |
| `StationWhiteFloorsMain1.json` | `71bf0fb1f31e2673adb2bdd7b2c2ff28f27f727dbfacf8ccd31081ca5a84f1c2` |
| `Scripts/AuthorStationWhiteFloorsMain.py` | `4680a7ae6aae9d3da2927f3b8ee017f813ddb26c6f972b224764dfd2bae28c0a` |
| `apply_station_white_floors_main1.py` | `9c6f329178b770b60402ffaf2b427b5599255c45c1d3088d7cda1c11999fe08a` |
| `StationWhiteFloorsMainPlan1.json` | `30f2323bfa31af5538ff61d75ff672f4648a0a50ab3bcab6b13d226bfb716684` |
| `capture_station_white_floors_main1.py` | `60df8e8f849e331a620dac82f006292c18f6248fc329fad0964a6e7ac4fe8866` |
| `StationWhiteFloorsMainCapture1/manifest.json` (14 images; state guard failed; native `0xC0000005`) | `74e428958579ef2780b7465c845a10fd57e3542f1944e8e51568fd36ca93a7b8` |

## Remaining floor survey — retained mixed native outcome

The read-only remainder survey completes at2026-10-07T06:03:40Z with all three
map sections successful, every editor scene unchanged and file/save preservation
passing. The lead subsequently collects native exit−1073741819 (`0xC0000005`)
during shutdown. The measured sections are usable guarded evidence; the process
outcome is not a clean native pass. No floor, map, collision or instance reference
is authored by this survey.

The exact saved main map contains four omitted owner foundations with four meshes
and two materials. Actual raw vertices, triangles, material IDs and transforms
prove that the three thick slabs share their top, side and underside slot. Their
upper horizontal faces lie near localZ0; positive winding alone incorrectly
identifies localZ−200 underside faces. The curved ring has negative X scale and
more than one nearly horizontal height band. Any white surface treatment must
use the measured upper face role and retain the other structural surfaces.

The private apartment `/Game/BuildingLibrary/Home/L_CrewApartment` contains742
actors and33 candidate components over six meshes/three materials. Its floor
candidates include a proved countertop at local-mapZ90 and a ceiling atZ349;
those are excluded. The docked cargo child contains71 candidates over14 meshes
and12 materials, including four proved vertical finished-wall panels that are
also excluded. Floor names are not an author whitelist. The owner authorizes
private child-map derivatives and exactly two existing LevelInstance references
in the owner preview; original child maps and supplied assets remain protected.
Nonrust decorative rug and fabric artwork stay unchanged. The new prepared
remainder plan selects exactly30 apartment hard-floor components,60 cargo
hard-floor/stair components and four main foundations. It excludes the apartment
rug/countertop/ceiling and seven cargo cloth props/four vertical wall panels.

The first remainder candidate prepares34 private material assets across17 exact
mesh roles and two private child-map copies. Native original color, metal and
roughness feed masked Lerps; source normal/AO/UV wiring, textures and effective
parameters remain intact. Exact packed ORM and Cargo BreakMaterialAttributes
output pin names are read rather than assumed. Pure CPU checks select the three
slab tops (16/4/15 triangles) and upper ring (272 triangles), excluding lower
bands. Thick plates, inverted winding and stepped heights pass; a shared
top/underside height correctly fails. Child raw geometry and masks are checked
and retained before any asset creation. Shader vertex-normal behavior, saved
remainder references and actual pixels remain unverified. The subsequent native
attempts below supersede this candidate's initial unrun status.

| Remainder evidence | SHA256 |
| --- | --- |
| `StationFloorRemainderProbe1.json` | `d4d3bfa5cc6d47e0f717d07cb177a72212da154b8fef556969a33dbc6945cac8` |
| `Scripts/InspectStationFloorRemainder.py` | `56585ad3cc1fafb9c02f73e45f07d1c20fc7fbbfee205bba2e360192209b47a5` |
| `probe_station_floor_remainder1.py` | `a3d1fd5540b057478c79f1282773879036c60333cd3dd40432bca710e26b1dfb` |
| `StationWhiteFloorsRemainderCPU1.json` (pure CPU geometry/unsafe-mask checks only) | `d1f15d27d8c6ab75f9401b0dd6c5a8842647d8e6d9ace56bdaf148fddafbd8c4` |

By2026-10-07T06:49Z the lead has collected two remainder author failures with
native exit0, file/save preservation passing and zero new assets or child maps.
Attempt1 stops on the exact Cargo instance label: the original placement helper
adds `Refine/`, yielding `Refine/CargoPort/Complete docked cargo`. Attempt2 uses
that source-backed identity and retains the strict class/LevelInstance guard;
it stops before asset creation on the complex49,769-triangle docking hatch:
the height-only mask has7,386 ambiguous rejected faces and47 missing chosen
faces. Exact geometry is retained for inspection. The saved main map remains
`211c8125`; neither failure converts the remainder.

The lead authorizes a smaller interpretation for the next prepared attempt:
coat the90 isolated child hard-floor/stair components fully, including their
edges and undersides; retain top-only masks on the four mixed foundations.
The exact94-component whitelist, original geometry/collision/UV/normal/AO,
34 private materials and two private child copies remain unchanged. The four
foundation masks now explicitly interpolate vertex position and geometric
normal into the pixel shader; direct VertexNormalWS use is restricted to
vertex-stage inputs in [Epic's UE5.8 documentation](https://dev.epicgames.com/documentation/unreal-engine/vector-material-expressions-in-unreal-engine).
The installed interpolator header declares the `VS` input; actual CDO pins,
shader compilation and pixels remain native gates. Typed RGBA/numeric light
snapshots replace memory-address strings, preserving exact values without
rounding or ignored scene fields; CPU checks prove stable equal colors and
detection of a real color change. Attempt3 subsequently exits0 with preservation
passing and zero assets before creation: the measured direct `M_Trim` has both
scalar and vector `emmisive_strength` parameters, so the implementation's
parameter-free assumption is false. The next bounded candidate preserves its
copied defaults, reads the installed Material default getters and verifies the
private MIC inherits those exact values. Scope, masks and94 assignments remain
unchanged. Attempt4's actual partial result is recorded below.

| Retained remainder author evidence | SHA256 |
| --- | --- |
| `StationWhiteFloorsRemainder1.json` (native0; identity guard; zero assets) | `bc75597bcc24da9ffcf7ed4d9a5c83ca038373fe98908a54a7dcf74f059b5176` |
| `StationWhiteFloorsRemainder2.json` (native0; ambiguous hatch mask; zero assets) | `34e5841fc6675a0cc68a7b75c69842542178c2df45eb4e80ab8679c6e3af5649` |
| `StationWhiteFloorsRemainder3.json` (native0; direct-material default assumption; zero assets) | `d0323b1ec832214e0d07fb5e69f278fbab20c4923fc1994cf064972cddb40cc9` |
| `StationWhiteFloorsRemainderCPU3.json` (scope/typed-color checks; no native shader proof) | `3d7bacc5501bb588f922258092ab27dc9829dc15cfb8047d01f2c60f18f4b5b9` |
| `StationWhiteFloorsRemainderCPU4.json` (overlapping default names/change detection; no native save proof) | `cb6688511fdf05f9ed85429fa480effcbedd2ddb840584ed06a3498118e87868` |

At2026-10-07T07:06Z attempt4 saves all34 private material assets and the private
Apartment's30 floor references, then fails the exact copied-Cargo scene guard.
Root collects native exit1, source/save preservation passing and unchanged main
map`211c8125`. The Apartment private map hash is`33b336a1`; Cargo's initial private
copy is`07c9f027`, with no white-floor references yet. Neither child is referenced
by the main preview, and the four main foundations remain unchanged. These
partial assets are retained, not recreated or overwritten.

The failed raw Cargo snapshots both contain2,074 actors. Of7,556 exact delta
entries,7,436 arise from generated actor-name permutations: all28 generated
families preserve the exact multiset of full physical actor/component states
after aliasing only each actor's own object name. The remaining120 entries are
quaternion xyz values on40 procedural cable components in three rope actors;
their maximum difference is`8.881784197001252e-16`. All other fields are exact.
Root authorizes only these120 observed value pairs and the measured generated
families for cross-load comparison. No general tolerance, rounding or omitted
physical field is introduced; same-loaded floor-reference edits remain exact.
Nine negative CPU mutations reject new pose, visibility, population, material,
lighting and collision changes. Prepared resume5 checks the34 saved graphs,
defaults, parameters, masks and file hashes, reuses the completed Apartment,
finishes only the existing Cargo copy and then updates the four main floor slots
and two existing instance references. Native continuation and nine actual
game-camera views remain pending.

At2026-10-07T07:19Z resume5 revalidates all34 saved material graphs/parameters,
preserves the completed Apartment and saves Cargo's60 white-floor references
with an exact same-loaded scene guard. Cargo's private map is now`105f94d3`.
Root collects native exit0 and source/save preservation passing. The attempt
then fails a separate Main cross-load scene comparison before any Main save:
both snapshots have8,423 actors and only two changed string fields, each a
terminal's `presentation_target` UObject memory address. Their object paths and
classes are unchanged; no pose, material, collision or light delta appears.
Raw snapshots and this failed check remain retained; no cross-load exact pass
is claimed. Both private children are complete, while the preview still points
to the originals and its four foundations remain unconverted.

Root authorizes final6 to verify the existing34 material and two completed child
file hashes, load Main once, then apply only four foundation slots and two
instance world references. Fresh same-loaded full scene and CDO checks stay
exact before and after its one Main save. It creates no materials or maps and
resaves no children. CPU6 verifies those call counts/source guards; native
finalization and actual remainder pixels remain pending.

Final6 subsequently passes with native exit0, source/save preservation passing
and saved preview hash`c0c25d69`. One fresh Main load and one Main save apply the
four mixed-foundation floor slots and two existing LevelInstance world-reference
overrides. The total recorded coverage is94 remainder slots:90 previously saved
child-floor references plus the four new Main slots. All34 material assets and
both completed child maps are reused and protected; no material or child map is
created or resaved. Full same-loaded scene checks before and after save preserve
all actor/mesh/pose/collision/light fields, and both source Blueprint CDO world
references remain unchanged. The earlier cross-load failure is retained without
claiming it passed. Native implementation is saved; actual foundation,
Apartment and Cargo game-camera pixels remain pending. Capture6 stops before
map load or images because its verified mount list omits the existing CargoShip
junction; native exit3 follows a World Partition shutdown assertion. The failed
source, launch error and native log are retained. A read-only scan of all1,453
saved protected paths finds exactly41 CargoShip entries, each with its expected
digest and the exact existing junction target. New Capture7 binds that audit and
adds only this verified mount; it retains all nine views and preservation checks
and loads Entry before quitting after a preflight failure. Its pixels are unrun
at this record's2026-10-07T07:35Z update.

At2026-10-07T07:38Z Capture7 completes all nine actual1600x900 game-camera
images and root collects native exit0. File, save, ship and editor-scene
preservation all pass; the exact editor delta count is zero. The active player
camera is verified before and after each completed PNG, with90 ticks and at
least six seconds of warmup. Both root and the composition specialist inspect
all nine images. Apartment05/06 retain embossed white floor and stair detail;
Cargo08/09 retain white grilles, panels and treads under the existing warm
lights. Foundation01/02 remain dark blue under ambient light,03 is partly
occluded and04 provides a narrow visible white-top comparison. Those angles
do not establish complete foundation-mask visibility or lighting acceptance.

Cargo07 exposes a real omission: the brown walking threshold outside the hatch
is the existing `Refine/Cargo/Sleeve floor`, a single colliding Cube at child
position(420,-1140,478), scale(5.6,2.2,.12), mapped to world
(-1860,-7580,-6) with its top atZ0. The original label-prefix filter omitted it;
it is separate from the preserved decorative rugs. Its existing P4Metal02
source exactly matches an already saved Main1 white derivative, including all
115 inherited native parameters. A bounded one-slot correction and new private
Cargo child reference are being prepared; no additional material, geometry,
collision or lighting change is needed. Full-station visual completion remains
open until this threshold is saved and its actual pixels are checked.

| Partial-save and continuation evidence | SHA256 |
| --- | --- |
| `StationWhiteFloorsRemainder4.json` (native1; partial34 materials/Apartment; main unchanged) | `822d176b0b80723df3548470de04d89b6914613605e3f2acd8975a0c09a03c73` |
| `StationWhiteFloorsRemainder4ExactDelta.json` (all raw Cargo differences retained) | `cfaba9dd8cd4ebed8e1d4b0a5a2b95c6055dcf09fa2158767ce0a97f863391f5` |
| `StationWhiteFloorsRemainderCPU5.json` (exact observed representations/nine negative mutations) | `a5f7af8c0b001fe7dd516159c3fee7679f3cd0b67608ce6ab68ff1be5a185605` |
| `StationWhiteFloorsRemainder5.json` (native0; completed Cargo; Main cross-load check failed) | `9136953944a1189025b4b2eb3112d835aefc758a49511f2261261d1b3012a120` |
| `StationWhiteFloorsRemainder5ExactDelta.json` (two UObject address strings; raw failure retained) | `620677946ba3417771908c8e920169574b2bcd6f9bf5bca19ca67fb6f12d1f4f` |
| `StationWhiteFloorsRemainderCPU6.json` (one Main load/save; no child/material writes; source hash guards) | `58e62a9592628d29bd5bd47a40f4ff355db6009f63561c7c79bf2529e8d11793` |
| `StationWhiteFloorsRemainder6.json` (native0; final four floor slots/two references saved; preservation pass) | `627e5897c0b8c4301005471bcbda81c2e64b8ff847565a22c4e0e119711a8ec3` |
| Saved remainder preview `.umap` | `c0c25d69e16342dadc274976b1e4c81b8d46130ee98b7b8bc3310f03d5058f50` |
| Capture6 retained preflight error (zero images; native3 shutdown assertion) | `b8317a2dfc0acecb3ad9d90d7368167e8ea6adea8c0b9bb5231ec0a5efebbf33` |
| Capture7 complete protected-path/mount audit (read-only; all digests match) | `e0f92be3e8633ec44b73f43bf6237662aa2b39b58a9a192e69e6344bf797c602` |
| Capture7 actual nine-image manifest (native0; all preservation checks pass) | `1a5c76bbe06f88803da4fecba6fe6b7482dad74afab28869e7f06f9ef1264940` |
| Capture7 exact editor-scene deltas (zero changes) | `a5338d955b09046ec0b16f3a9625b7955c763aae07dc722e474e6078745f932f` |
| Capture7 Cargo07 actual brown threshold image | `638b44ba4900f05d16e0fd501c3a3a4ab36dde2ebcaae286a299063ab86be4b5` |

## Saved opaque finish and six-view review

At2026-10-07T08:07Z FinishCapture2 completes six actual1600x900 player-camera
PNGs and root collects native exit0. Its manifest is
`c709af07f2b33adc0e830c423858b57bcb52d71ba1c54a1634383bf997150587`;
source files, saves, ships and the editor scene remain exact, with zero editor
deltas. It shows the saved Opaque2 preview`f8b49d93`, whose native0 author
receipt`7368247a` records58 private assets and145 material slots on57 actors.
All six images are independently inspected. The graphite podium now reads
as clean metal with a recognizable complete Phoenix focal point; the white
floor retains panel seams and relief. Desk finishes improve, but the native
cyan screen graphics remain busy and obscure service identity, especially
the Pilot close view. The two bank overviews show hardware layout but do not
prove fine-copy readability. The bright floor and dark ceiling still create
strong contrast. Both lead and specialist rate the room about7/10; the9/10
gate remains open. Floor and light settings are retained.

FinishCapture1's omitted exact EngineResources/Black source classification,
zero images and native shutdown crash remain retained. Art1 and Art2 fail
before import/save on actual LCD plane/footprint guards; no new fitted
five-service artwork is shown by this successful capture. The next visual
correction is clear mounted illustrated service identity, followed by the
actual mixed-crew fit/contact and standing rings; that is not inferred from
the saved material finish.

Art3 subsequently saves all ten private assets and five existing display slots,
with source/save preservation passing and preview hash`eeffd79b`. Its saved
receipt is`5eac150f83215f6ac3a97f741b77537bd5623f5b11282874f70e0358331c7121`.
Root collects a native access-violation exit after shutdown; this is retained
and the run is not called an aggregate clean native pass. Its fit reuses the
retained complete7,668-triangle/3,836-vertex source and checks four supported
inner rectangles using121 samples and continuous native triangle coverage.
The central supported insert's private copy is opaque with gain1.5 to suppress
the observed competing underlay; its original shader/UV connections and source
bytes remain protected. Fresh saved player-camera pixels are pending; the
previous room score is not raised from these authoring checks.

At2026-10-07T08:11Z the one-threshold author stops before loading a child or
saving any asset/map. Its receipt`14fe9e4e` preserves all source/save files and
the saved Opaque2 preview; native shutdown fails separately. The failed guard
compared the source master directly with Main1's historical private-clone
``before`` graph, including different asset/node paths. Main1's saved material
bytes and parameters are unchanged. New attempt2 retains the failure and
uses exact four material-file digests, current inherited parameter/parent
readbacks and typed graph snapshots before/after the same session. It creates
no material and still changes only the measured Cube and one Main instance
reference. Native save and matched threshold pixels remain pending.

At2026-10-07T08:28Z FinishCapture3 completes all six fresh saved-Art3
1600x900 PNGs, manifest`f54f5fabbbda731198b6db50a87090c5555b5fd40abcd77600a2e85b63cc707e`.
Files, saves, ships and the same-loaded editor scene remain exact, with zero
deltas. Root collects a shutdown access violation separately; this is not an
aggregate clean native pass. Independent inspection verifies all six PNG
hashes/dimensions and agrees with the lead's approximately7/10 assessment.
Flight's competing underlay is removed and its title reads more clearly, but
the illustrated subject is dim. Pilot's close view is horizontally mirrored
and its title/footer are obstructed by existing hardware. Triangle support
does not establish unobstructed visibility through that hardware. Other panels
are also dark at room distance; the white floor/dark ceiling contrast, sparkling
edges and soft image remain. Private material orientation/visible-window and
brightness corrections are next; no geometry, floor or lighting rollback is
justified by this review.

The corrected Threshold2 author then passes, and root collects native exit0.
Receipt`67bf51f6ce0629c6d719c7b9b0bb42039ed07be8ea91919ff50c8c7fd2a8b0a2`
saves one new private Cargo map with only the exact Cube's material reference
changed, then one existing Main LevelInstance world reference. The preview is
`fb3d5ed7ee58afc3e90044cec21a4428022a7224f9d7b1fa71e0d65bab3ff3b2`;
the new Cargo map is`65362fa46045cfe3bbe40ef0ee88ac9d91ad04a09fc5fdfa1a31d70bd2fce9fa`.
No material is created or rewritten. All115 native parameters, the three white
values, parents and current same-session graphs remain exact; original child,
asset, save, geometry, collision, light and source-CDO guards pass.

At2026-10-07T08:33Z ThresholdFloorCapture2 completes both actual1600x900
player-camera images, manifest`2ad29370868bbba89ac17be00dec0f3cc84f7e9c1cd591202c508c55e9798cad`.
All protected files/saves/ships and the same-loaded editor scene remain unchanged,
with zero deltas. Root again collects a shutdown access violation separately.
Root and specialist independently inspect both matched hatch and threshold-close
views: the previously brown walking plane is now diffuse white, while bulkhead
wear, frame colors and the interior grilles remain. The original Cube has no
authored panel texture; its plain surface is not evidence of lost panel detail.
The measured omission is corrected and saved. These two views do not establish
complete mixed-foundation lighting/mask visibility, owner-device performance or
T9 acceptance.

The bounded read-only capture audit records current`r.HighResScreenshotDelay=4`
before/after every FinishCapture3 frame. Warmup occurs at1014x344; capture requests
1600x900. The prior paired native observer's actual high-res draw records TSR
method4, enabled AA/TemporalAA flags, a ViewState, nonzero jitter and no camera
cut. AA is therefore not shown to be disabled by this path. Epic's current5.8
[console-variable reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-console-variables-reference)
documents a default delay4 and disables TemporalAA below that default. Installed
headers expose the capture interfaces but the private implementation is absent;
history-reset/convergence behavior is unconfirmed, not an established cause.
The retained ordinary1600x900 draw is also noisy. Keep identical high-res frames
for bounded comparisons; future acceptance should use the existing full-size
ordinary Shot route warmed at its actual output resolution, with its known
next-tick log-flush proof repaired. No new renderer run or quality/light/source
change belongs to this audit.

## Five physical service rings: saved, appearance pending

At 2026-10-07T09:10Z Marker1 stops before saving any asset or map. Root collects
native exit 0; receipt `9c0a9fb96eb7f3f2a95457fd9c9308ac17c4d8858d376bcc3d61e4c1e1a82b4d`
retains the failed decimal face-comparison predicate and complete source/save
preservation. Its raw created mesh was not retained and is not reconstructed
as evidence. The original source, wrapper and failure remain immutable.

Marker2 uses the installed source-model `FVector3f` representation explicitly,
then compares all oriented triangle faces and material roles exactly. It accepts
cyclic corner reordering; reversed winding, material changes and coordinate
changes fail the CPU regressions. Full copied positions, triangles and material
IDs are persisted before the native predicate. Actual raw artifact
`4ee0fae0a576c695aa1bb019f6398d730854874bfb616e37879434a24fad59cf`
contains 5,768 vertices and 2,980 triangles, with no missing or unexpected faces.
Normal/UV buffer readbacks and all three material sections pass. This actual
float32 result supports the precision explanation without waiving geometry.

Root collects Marker2 native exit 0. Successful saved/preserved receipt
`c581987a09117dda13f00bafb0d88bdcdd0edf5da47ccee7b3443ad8313c2271`
saves nine new private assets and five cosmetic NoCollision actors; the owner
preview is `8c65e4501320b65335ae016b86dee78c774580388a646bfb14063b05416e60bd`.
The shared chamfered segmented mesh has a graphite body, titanium fasteners and
five service accent children. A five-second material pulse varies emission from
0.75 to 1.15; no light is added. All original actors, service identities/actions,
materials, floor contacts, source files and saved progress remain unchanged.
These are presentation markers; no gameplay action or purchase is called.

Capture2 completes nine actual 1600x900 player-camera images and all five initial
standing/FocusedTerminal checks. Manifest
`2069f6e647f7bdc1a81b2913fbebebb8d84acf99108a8be760966be293d1c510`
passes exact scene/service/ship/file/save/quality preservation with zero deltas.
Root separately collects a shutdown access violation; this is a successful
capture receipt, not a clean native process. The original alien crew remains;
model substitutions are still separate unsaved tests. No gameplay action is
called by the initial selection checks.

Root and specialist inspect all nine images: the segmented graphite markers
and distinct accents visibly identify the five standing positions. Their narrow
lenses contrast clearly with the white walking surface; marker quality is about
7.5–8/10. The original desks still look shiny/noisy and their old images remain
dim or frame-obscured. The dark ceiling, bright floor and unchanged alien-heavy
staff hold whole-room quality near 7/10, below the required 9/10 gate.

The three fixed views span 5.207 natural game seconds. Pixel audit
`ef42b16bc2920f82ea692b21e333bd7c2393601ea84580eac0ca19530a4d068b`
compares 14,463 common cyan lens interior pixels after one-pixel erosion, without
editing images or time/material settings. Mean linear luminance is 0.16595,
0.15395 and 0.16840; the middle lens is 7.23% darker than the first, and the third
is 1.48% brighter. Adjacent floor luminance varies less than 0.026%. This supports
subtle captured brightness modulation; elapsed time alone is not the evidence.
Three stills do not establish continuous smoothness, exact shader phase or
owner-device comfort. The matched high-resolution pipeline still has the known
noise/softness limitation; a warmed ordinary full-size view remains needed for
final room judgment.

## Mounted service displays saved and fresh views reviewed

Mounted5 stops before map load on the quaternion argument to Python's
`Transform` constructor; its native process exits 0, but receipt
`b335ccca080dadd739882e6cb12ef14d3d1f293968fb7342364aa908b67fe788`
is a preserved failure with no saved assets. Mounted6 uses the installed
reflected quaternion fields, matching the existing native kit authoring helper,
and checks identity and nonidentity transforms before loading content.

Root collects Mounted6 native exit 0. Receipt
`d46ac4227db8281acdf813508d4796e8afaf066db2dc3ebf241e04edab887364`
saves thirteen private assets, four small NoCollision monitors and five private
material references; the preview becomes
`5b2d7bdcefaa2f6493bc43b34cc2ce5631bb8f03f21bdb7a997c5b7f18be8d2f`.
Known screen UVs present the full illustrations in shallow graphite/titanium
housings attached to existing hardware. The five markers, original actors,
service actions, walking floors, lights, source assets and saved progress are
preserved. This saved implementation does not establish visual acceptance.

The nine-view Capture6 source and exact classifier receive independent review:
1,710 protected files are hashed and classified, including nine exact engine
files, four art references, two fonts and seven verified content junctions.
Capture6 subsequently stops before images on its exact mounted-parent/pose
readback. File/save/editor preservation passes with zero scene deltas; root
separately collects a shutdown access violation. The retained before-camera
snapshot shows exact positions and scales for all four monitors, exact north
quaternions, and componentwise sign-reversed south quaternions. Quaternion sign
reversal represents the same rotation; the parent was not recorded before that
predicate, so parent validation remains unconfirmed. The failure is preserved;
no saved geometry or material is changed to repair the capture guard.

Capture7's bounded repair receives independent offline review. Both observed
south sign reversals transform all 272 native vertices and eight bound corners
exactly; north poses remain exact. Tiny position, scale or rotation changes and
an unobserved north sign reversal are rejected. All 1,720 protected inputs are
hashed and classified against the exact engine, art, font and content-junction
allowlists. Capture7 records all four raw parents and poses before predicates;
parent identity and the original scene comparison remain exact. This source
review is not a native capture or appearance pass.

Root subsequently collects Capture7 native exit 0. Manifest
`4e259652f66fde0c3c6da6f04024fd2d8e397244b584412396d23e74c751908b`
passes all preservation checks and records zero editor deltas. All nine actual
1600x900 PNGs are independently hashed and reviewed. The four mounted service
titles read correctly, their complete hero images remain visible, and the
frames no longer obscure the art. The display presentation is approximately
8/10. Flight's ship image and heading remain comparatively dim. The whole room
is approximately 7–7.5/10: the podium and Phoenix focal point work, but sparkling
desk surfaces, a washed-out floor and dark ceiling still limit the finish.
These saved views retain the original alien operators; the corrected crew
preview below is separate unsaved evidence.

Root's required 9/10 room gate remains open. The ordinary capture below uses
the final saved crew lineage. Earlier full-size failures and their raw deltas
remain unchanged.

## Corrected crew preview reviewed and captured tracks installed

The six actual unsaved CrewPreview6 images are independently checked against
manifest `72718460afd7ebdb51fb9fa81b0c813688bab354b2e9b5609f8dddafd757051f`;
all are 1600x900. Whole heads and bodies remain visible. Human knees and pelvis
read as seated, boots rest on the support blocks, and the robot fits the chair
footprint without gross visible penetration. The human correction is relative
to the actual previously rendered origin; the robot receives the declared
chair-axis correction. The mixed silhouettes improve the prior all-alien set.

This is cosmetic placement approval for the exact captured 121-key tracks,
not a claim of desk-working animation or continuous furniture contact. Hands
remain in a lap/rest idle. The preview saves no assets and restores the three
original animation lifecycles exactly; file/save/ship preservation and zero
editor deltas pass. Root separately collects a shutdown access violation.
No current 9/10 room acceptance is inferred from these close views.

Captured1 subsequently saves exactly the reviewed Human and Robot tracks in
two private animation clips, changing three existing operators and saving the
main preview once. Receipt
`9b68ab66e02aae7bf2035911c04a08d0a23f589ccbb074b63d520e32508780cd`
binds the accepted preview and its two captured 121-key, twelve-track artifacts;
source poses and the fitter are not reevaluated. Native local-position readback
error is zero, quaternion agreement exceeds 0.99999995, and all unit scales
match exactly. Full scene, other actors, lifecycle, source files and saved
progress are preserved. The current saved preview becomes
`13787cce1fba901869556676fb14b3f2aff57bc76fd00325d2b439d1f3d824dc`.
Root separately collects a shutdown access violation; the saved receipt is
valid evidence, not a clean process-exit claim.

## Ordinary full-size saved-room verification

At 2026-10-07T10:14Z Ordinary3 completes with manifest
`1fbd3e0ff1ecba368a2878b6a4b439ca29195f31da68cfcb81d1654991e81835`;
root collects native exit 0. The actual ordinary viewport screenshot is
1600x900, SHA
`7d189a7ef171ce79d9945b0775ebe55e2daa15bb6441e7a8532b35638f4c56d6`.
It uses the active player camera at the existing podium-side position after
six seconds of warmup, with no renderer-quality or lighting changes and no
high-resolution screenshot request. Native renderer samples verify the full
viewport and output rectangle. Deferred later-tick proof confirms restoration
of the original viewport and fixed-size state. All three freshly loaded saved
crew lifecycles match before and after Play; the complete editor snapshots
match exactly with zero deltas. Files, saved progress, ships and quality
settings remain unchanged, and Play stops.

Independent actual-pixel review finds substantially cleaner podium surfaces,
glass edges and ceiling structure than the earlier high-resolution views.
The saved mixed crew and Phoenix focal point read coherently. This angle is
approximately 8/10; the bright central desk and floor against almost-black
ceiling recesses still prevent whole-room 9/10 acceptance. One view does not
prove all service close views, continuous crew contact, owner-resolution
performance or the cause of the earlier sparkling pixels. Native
`BP_Blinds` AccessedNone messages remain in the raw log separately from the
successful capture and preservation checks.

## Bounded normal comparison and central finish candidate

Normal2 fails before loading the map because the native scalar override does
not expose the assumed Python `expression_guid` property. No material
preparation, image or disk edit occurs. Receipt
`b44d6348c757d105315fe3ae6b96b9abc66e07a07375110e2d5ac9953a4cf551`
retains the failure and separately collected shutdown access violation. Its
editor baseline is uninitialized; the 7,782 raw deltas do not establish scene
preservation. Normal3 replaces that getter with the complete native scalar
export, masking only its single numeric `ParameterValue` token and retaining
all other metadata exactly. Raw native exports are written before predicates.

Normal3 then completes cleanly with root-collected native exit 0 and receipt
`13b920779302d7fb9534a719e65e404a5670836b67e910f8b6213be0071d6308`.
Two matched ordinary 1600x900 images compare the saved PortSouth P3 body with
four unsaved leaf copies whose normal intensity alone is reduced. Both other
body slots remain unchanged. All four original references restore, complete
editor snapshots have zero deltas, and files, saved progress, ships, quality
and fresh saved crew lifecycles remain unchanged. Root and independent pixel
reviews find little meaningful visual benefit. The original saved normals
remain; no normal material is authored or saved.

The next candidate is an unsaved twelve-slot comparison on the four existing
central Goliath body/support actors. It increases only the active private
graphite/satin coating mix and softens metallic response through four role
scalars. Existing normal/AO/UV, textures, role colors, glass, emissive, lighting
and white floor remain exact. Its source review and 2,198-file classifier audit
pass. Contrast1 subsequently records two ordinary views in receipt
`20b72bdf24ad366ebe9e2cda6cfc3c3f778741f3a3cea42a2599e11c441094f3`:
all twelve temporary references restore, full editor snapshots match with zero
deltas, and files, saved progress, ships, quality and saved crew lifecycles are
preserved. Root separately collects a shutdown access violation.

Actual pixel review finds the right-hand white workstation apparently
unchanged, despite native readbacks of the declared dark role colors and four
changed scalars. No saved finish is accepted. The current raw scene and prior
measured bounds identify that visible body as the intended P1 Goliath table at
(7800,0,0), projecting to the right of the podium from this camera; it is not
another room. The effective render route and the contribution of other
assembly surfaces remain unconfirmed. Route1 exits cleanly but rejects its
incorrect assumption that the twelve immediate MIC parents are two masters,
before creating its result. The failed source and launch error remain intact.
Route2 follows the actual measured inheritance instead and completes with
root-collected native exit 0 and receipt
`aad2d44d83594980321d9ad0dd8631e338a058408627b0390be966f9778ab276`.
This Entry-only readback loads no preview or Play session and changes no
material, setting or package. All twenty-one inherited MICs and both ultimate
private masters have no Nanite override material; the body mesh has Nanite
disabled, and both masters have no Front Material connection. Protected files
and saved progress remain exact. Those alternate-render-route hypotheses are
excluded for this body.

The retained native graph connects BaseColor to the declared role Lerp: native
color in A, role color in B and the actual TintMix parameter in Alpha. Metal
and roughness connections also match live outputs. Disabled body emissive
selects an unconnected zero branch. The remaining assembly audit identifies
twenty-five other actors with thirty slots: twenty-five already use saved
graphite roles and five retain functional emissive/service display surfaces,
including the thin workplan top. No missing broad body-material whitelist is
proved. No further finish is saved from these getter checks, and they alone
do not establish appearance or a 9/10 result.

The subsequent bounded pixel analysis supersedes the initial whole-image
judgment of an apparently unchanged workstation. Its retained record is
`OperationsCentralContrastPixelRegions1.json`, SHA
`03d0f567edb6d78be376922eb459f3b1a48a7cb5cd81ba2d65eb0813e397fd78`.
Two graphite front-housing rectangles darken by 33.3% and 20.1% in gamma-encoded
weighted RGB; a lower-leg rectangle darkens 30.2%, though its slot is unknown.
Three upper satin-frame rectangles instead brighten 3.6–7.1%. The unchanged
floor/podium controls change less than 0.15%, and the functional worktop changes
about 1%. The sampled family rectangles agree with measured projected bounds;
they are not per-triangle material segmentation, scene radiance, or BRDF proof.
Natural animated objects and indirect light remain comparison limitations.
These pixels establish a rendered graphite response; a general temporary-MIC
update failure is not supported. The pale upper satin frame still dominates.

The next unsaved Contrast2 preserves the tested six graphite recipes and
changes only six satin leaf colors to linear RGBA (.12,.15,.19,1) with TintMix .95.
It retains their saved MetalScale .65 / RoughMin .55 / RoughMax .77. Each previously
inherited color receives one declared local override on a temporary clone;
native metadata is retained while only its RGBA value changes. Twelve original
slot references and all source materials must restore exactly. No lighting,
floor, texture, normal/AO/UV, functional emissive or geometry change is proposed.
Contrast2 subsequently produces the two actual ordinary images in receipt
`ac5c7dfe3dc33c1f9ceecc4c17b32cf29eaa70178bf58f394c2d0beba536892f`.
The twelve exact references restore, complete scene snapshots have zero deltas,
and files, saved progress, ships, crew lifecycles, quality and the viewport are
preserved. Root separately collects another shutdown access violation; this
is not a clean native process pass. Root and two independent actual image
reviews find a modest local improvement: the housing and upper support
recesses separate better from the white floor. Original functional worktop
brightness and specular edges still dominate. The local finish is selected
for a narrow saved implementation, with no whole-room 9/10 or owner acceptance.

The prepared captured installation duplicates twelve existing leaves into a
new private namespace and compares their complete native before, inherited
color seed and after snapshots directly with the rendered Contrast2 records.
It installs recorded values without reevaluating proposed material values;
parents and existing metadata remain exact, and no master changes. Root alone
saves the leaves and twelve existing references after source, full scene and
crew checks. The current producer is the separately saved Flight2 gain5 MIC;
its actual receipt is `ce32d2ea35920b16f2b13592f2264a4c1e07bb8d522275809ff12ee292bc2d61`,
with another shutdown access violation retained separately.

CentralCaptured1 now saves that selected finish, receipt
`b0ef717cd2021de999a13c5187618461c7013ae0cb09b3cae40ad1cc8df22bff`.
The current editable preview is
`03852cf1ff951c41779c99e4c74a2e3f7c82728c9ae57e41d8208ebc54068214`.
Independent receipt/file verification confirms all 2,244 protected bytes and
the twelve new private MIC files, all twelve complete captured before/seed/after
metadata records, and the complete same-loaded scene with only twelve allowed
material references changed on four existing actors. Sources, parents, normals,
textures, emissive, glass, lights, floors, saved progress and crew are preserved;
there are no new actors, lights or masters. Main loads and saves once, with no
reported author errors or proposed-value reevaluation. Root separately collects
a shutdown access violation after this saved result; it is not a clean native
process pass. Fresh nine-view saved room appearance, owner acceptance and the
whole-room 9/10 gate remain open. Published build state is unchanged.

FloorDepth2 meanwhile completes with clean native exit 0 and actual receipt
`d3af43118e6cb01c1fb53352d93432832922a5ab90991571e369ba3826dceefe`.
Both matched ordinary 1600 images and exact 420-reference restoration pass;
files, saves, ships, crew lifecycles, quality and viewport are preserved with
zero scene deltas. Root and independent actual pixel review reject saving the
18% native-albedo luminance blend: its benefit is slight and some native wear
and seam contrast becomes weaker. The saved textured white floor remains.

## Still open

At 2026-10-07T11:58Z, the nine fresh ordinary 1600x900 saved-room images in
`StationOperationsRoomOrdinaryCapture1` complete, manifest
`c0f3e0073fb782ab22abef5f829edc4ba7dbd45e051bb37a3a41b25540ced9c4`.
All nine PNG hashes, actual cameras, renderer observations, viewport restoration,
fresh three-crew lifecycles, files, saves, ships and quality settings pass.
Full editor-state preservation remains PARTIAL: the retained comparison adds
2,076 private Cargo and 745 private Apartment LevelInstance actor paths after
PIE; the original 8,439 snapshot rows do not change. These population differences
are retained rather than excluded. Root separately collects shutdown access
violation exit -1073741819; this is not a clean process or aggregate pass.

The NEW saved-room capture2 supersedes that baseline timing failure with actual
receipt `53505701bef8438cd0685e8755504aa785c50025c34c71a54ce0ef6316588833`
and root-collected native exit 0. Before PIE, the two measured child populations
and complete actor-path set stabilize; both full snapshots contain 11,260 actors
with zero exact deltas. All nine ordinary images, renderer/viewport restoration,
fresh crew and file/save/ship/quality guards pass. The original failure and raw
additions remain retained; this verifies the fresh loaded-world comparison,
not global streaming completion or a gameplay/performance pass.

Root and independent review of all nine actual images rate the furnished T room
approximately 7.5–8/10. The five mounted service titles and complete illustrated
subjects read clearly, darker hardware separates from the textured white floor,
and the glass Phoenix remains a strong side-view focal point. The upper room is
too dark compared with the floor, and the busy central control assembly competes
with the ship from the entrance. Gentle upward fill from existing fixture
housings and a separately bounded decorative-worktop cleanup are proposals;
neither is saved or visually accepted. A six-view UNSAVED comparison is prepared
to isolate three upward fills, then those fills with all four Phoenix children
30 cm higher and two subdued decorative WorkPlan slots. The neutral yaw pivot,
functional Flight plate and service actions remain intact; measured ship
geometry leaves 19.6 cm below the glass ceiling. Actual bounce, hotspots and
hero visibility still require the comparison pixels. The editable map remains `03852cf1…`,
and the owner/whole-room 9/10, gameplay, canonical promotion and published build
gates remain open.

UpperFillPreview1 then fails before lights or images on a broad bounds lookup;
its native shutdown access violation and exact unchanged saved scene are retained.
UpperFillPreview2 corrects the lookup to the three measured housing rows and
produces four ordinary baseline/fill-only images, receipt
`14d39eb7c947d12e55e91aec5f812c9f78e8b5d44a60c7119c827b26fd6572ff`.
Actual pixel review rejects the 700-lumen/specular-zero fill as negligible.
The combined comparison stops on tiny native relative-XY roundtrip changes
while raising/restoring one attached ship part; precise PIE restoration fails,
although the final editor has zero deltas and files, saves, ships, crew and
quality remain unchanged. Root separately collects shutdown exit -1073741819.
Neither attempt is saved or reported as an aggregate pass.

NEW3 completes six actual ordinary images, receipt
`a26fa718754ff2ee189ddcf5144ac3e50564310b02256a86baeb1687fa679ae9`.
The same three physical mounts use
1,400 lumens, specular scale 1 and 1,300 cm attenuation. Direct native relative
property writes now retain exact local ship fields and restoration. All six
warmed native world-height checks pass; raised geometry spans Z174.64–260.90
within the glass. Full editor comparison has zero deltas, and files, saves,
ships, crew, quality, renderer and viewport restoration pass. Root separately
collects shutdown exit -1073741819; this remains an aggregate process limitation.
Root and two independent actual pixel reviews reject saving the lamps: upper
room gain is negligible, with mainly the pendant stems brighter. No major new
floor hotspot is visible. The higher Phoenix and quieter decorative WorkPlan
give modest useful focal-point separation and remain selected unsaved candidates.
Whole T is approximately 8/10, below 9; the editable map remains unchanged.
CanopySatinPreview1 completes six ordinary comparison images, receipt
`38fbd216b1dd424510684d829099739cda7007a2080204a85c9a65442f54e4fc`.
Root separately collects shutdown exit -1073741819. Exact PIE restoration,
full editor zero deltas, files, saves, ships, crew, quality, viewport and renderer
checks pass; the saved map remains `03852cf1`. The source mesh stays native:
867,568 triangles and 433,918 vertices, with no dense Python geometry export.
Fifteen upward ray hits identify slots 1/2 on downward sloped body faces and
slot 3 on all five flat centerline samples. Two unsaved MICs change only tint,
metal and roughness on 22 references across the eleven panels; normal/AO/UV,
textures, switches and emissive remain original. Slot 3 was preserved by its
silver material name, which did not prove that it was perimeter trim.
Actual entrance, side and upper-room reviews show modest clearer panel/brace
relief, while the flat dark center strip and upper roof still dominate. The
co-varied higher Phoenix and quiet WorkPlan remain useful; natural yaw differs.
Root holds the canopy save and requests one final coherent comparison including
the geometrically measured flat slot 3. Whole T remains approximately 8/10,
below 9. This result does not establish full underside coverage or final lighting
acceptance; no canopy finish, lights or map are saved by the comparison.

PodiumCaptured1 fails before saving on a tuple-mutation expectation error after
the first child assignment. Receipt `3e65ec17…` retains exact rollback of all
temporary changes, full scene/file/save preservation and zero private files;
root separately collects shutdown exit -1073741819. Corrected PodiumCaptured2,
receipt `8bdb0b582bfd474f47b245d4aed9f4180fbb3831d8caf0c2bb9b33f4e89015b9`,
saves the four accepted child local-Z increases and two quiet WorkPlan MICs.
Five existing actors, four pose fields and two material references change;
the neutral yaw loop, all ship parts, glass, controls and services remain.
Full scene, source, crew, files and saves pass with no recorded errors and one
Main load/save. Root separately collects shutdown exit -1073741819.
The current editable Main is `32469e3a…`. CanopySatinPreview2, receipt
`474451503e9d68300b625067a2757706a2c3139e7e0b41d72806ac82df0fd61e`,
completes eight ordinary views: three freshly saved Podium2 baseline views,
three temporary canopy-slot 1/2/3 satin views, then two with fourteen redundant
decorative console fixtures temporarily hidden. Exact restoration, full scene
zero deltas, files, saves, crew, ships, quality and viewport checks pass with
no errors. Root separately collects shutdown exit -1073741819. The saved map
remains unchanged; neither canopy finish nor fixture visibility is saved.
Actual review shows modest clearer underside facets and less side-view cyan
task-light/cable clutter. The upper void stays dark, bright console hardware
still competes with the Phoenix, and wall-level service context remains sparse.
Whole T remains approximately 8/10, below 9; natural ship yaw differs across
frames. Owner acceptance, canonical promotion and the published build remain
open.

The owner then identifies the odd one-sided central-console piece and clarifies
that Flight is a walk-up upgrade station with no chair needed. Exact native
and owned assembly metadata identify the piece as the single offset
`StaticMeshActor_1415` / `GoliathChair01`, at `(7700,-60,0)`, yaw -30. Both
console supports 1417/1419 are present; this is the imported demo chair placement,
not a missing support. The chair-reposition proposal is cancelled. A prepared
read-only plan checks that one chair and 43 protected console/service/marker/
mounted-display actors before and after the lead's live deletion. The lead then
removes only chair 1415 through live Nwiro and saves the preview map.
`StationOperationsFlightChairRemoved1.json`, receipt
`942686e4906002dd188513a554263aa5f61226b1d69dd85c6bee4e9f17eca933`,
records the pre-save one-actor removal and exact preservation of all 43 targeted
actors and source bytes. The subsequent live save is independently reflected by
the current map digest
`5029100d1aa17c3911778132873a3f890e1c4275312db9c47da53f9195492e24`;
the receipt's `map_saved:false` describes its earlier verification stage.
Both current saved editor photos, `RootChairEntranceResult2_0.png` and
`RootChairWalkupResult1_0.png`, are independently reviewed: the chair is gone,
both console supports remain and the player-facing upgrade approach is clear.
These are editor views with icons and different exposure, rather than PIE or
whole-room 9/10 evidence. No replacement chair, source asset, other station,
canopy finish or fixture visibility changes accompany the correction. The
owner's open Unreal/Nwiro session takes precedence: no concurrent headless
editor or map writes.

At2026-10-07T04:49Z the owner supersedes the04:23 comparison-only scope and chooses
textured low-gloss white across the full station; rust must go beyond T. The
retained comparison remains unchanged. Main1 now saves the measured1,022 main
floor components; its14 actual game-camera views are reviewed, with the failed
editor-state guard and native shutdown crash retained. Private
cloned inheritance preserves normal/AO/UV detail, local overrides and effective
parameters. Only floor BaseColor/Metallic/Roughness changes. Mixed owner
foundations and both private child interiors now have saved white-floor
assignments; the preview references those interiors, and all34 remainder
materials are saved. Nine remainder views now pass capture preservation and
are reviewed; the one uncovered Cargo walking threshold subsequently receives
the bounded saved correction and both actual comparison views show white.
Foundation visibility and station-wide lighting quality remain limited by the
recorded views. No full-station
visual completion, current9/10 room
acceptance, canonical-map promotion or packaged release is claimed.

The owner also raises T's lead visual gate to9/10 before later rooms: existing
upgrade desks/services must read clearly through physical layout, mounted
identity and pulsing standing rings. Staff need a less alien-heavy model mix.
Those follow the floor check; exact service actions and access remain intact.
No new rotation mechanism, light or geometry belongs to the saved material finish.
Saved implementation, visual quality, owner approval and published build remain
separate; the latest ordinary saved angle is approximately8/10, while the prior
nine-view whole-room assessment is superseded by the current7.5–8/10 assessment
above. The lead's required9/10 gate remains
open. No9/10 room or gameplay/package pass is claimed.
