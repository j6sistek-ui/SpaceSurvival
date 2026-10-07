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
The exact contribution of native material layers versus capture convergence is
unconfirmed; no light reduction, global material edit or random geometry addition
is justified by those images alone.

## Still open

At2026-10-07T04:23Z the owner requests clean white and metallic silver station
floor comparisons because the rusty floor clashes with the sci-fi palette. The
next bounded preparation is three unsaved T-only material options at identical
entrance/podium cameras, preserving panel detail, lighting, transforms and
collision. Native floor identities/material interfaces must be inspected first;
no floor assets or map have changed and no station-wide choice is accepted.
No new rotation mechanism, light or geometry belongs to the saved material finish.
Saved implementation, visual quality, owner approval and published build remain
separate; T is unfinished and no8/10 room or gameplay/package pass is claimed.
