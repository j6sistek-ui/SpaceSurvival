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

## Still open

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
are reviewed; one uncovered Cargo walking threshold remains brown and requires
the bounded correction described above. No full-station
visual completion, current9/10 room
acceptance, canonical-map promotion or packaged release is claimed.

The owner also raises T's lead visual gate to9/10 before later rooms: existing
upgrade desks/services must read clearly through physical layout, mounted
identity and pulsing standing rings. Staff need a less alien-heavy model mix.
Those follow the floor check; exact service actions and access remain intact.
No new rotation mechanism, light or geometry belongs to the saved material finish.
Saved implementation, visual quality, owner approval and published build remain
separate; the independent post-white T assessment is6.5–7/10, and the lead's
required9/10 gate remains open. No9/10 room or gameplay/package pass is claimed.
