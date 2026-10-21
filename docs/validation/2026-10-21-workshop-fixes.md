# Workshop follow-up — October 21, 2026

**Partial: joined routines and catalog regression repair verified; contact,
appearance and natural-play acceptance remain open.** RPT-20261021-01 and
RPT-20261020-13 retain lead ownership. RPT-20261021-02 records the newly requested
ship rigging, flight, thrust physics and landing animations as queued work.

## Animation joins

The seven adapted original clips remain unchanged. Two derived assets align
the second clip's horizontal pelvis position with the first's ending position,
preserve vertical movement, and insert eleven intermediate poses over twelve
frames (0.48 seconds at25fps). Translation/scale interpolation uses smoothstep;
rotations use quaternion slerp. No original motion keys are discarded.

| Routine | Duration | Previous pelvis discontinuity | Maximum pelvis step across bridge |
| --- | --- | --- | --- |
| G1 then G2 | 31.36s /785keys | 117.738cm | 4.598cm per frame |
| B1 then B2 | 45.60s /1141keys | 64.530cm | 0.321cm per frame |

Eight native character sequences now use the two derived routines; twelve
single-clip sequences remain unchanged. All four packed Blender files reopen
with nine actions each: seven originals plus both routines. Original pose
samples agree within0.000457cm in Unreal and0.00000050m in Blender after the
intended horizontal offset. Twenty fresh canonical real-RHI captures show
different transition poses on all four girls, including Vexa's saved pink hair.
These sampled views do not prove continuous choreography or owner acceptance.

A separate CPU-skinned foot survey sampled121times per clip on the actual
F3 feet mesh. Original G1 soles range about-1.84 to125.62cm and G2 about4.77
to77.91cm; their aerial height must not be flattened. Other originals include
roughly3.18cm low soles. Workshop mesh origins are599cm over a600cm floor;
that additional1cm is not the cause of large aerial gaps. Pole contact still
visibly misses, and foot/garment/hair quality remains lead work.

## Workshop collision

The initial physical queries missed the custom upper-deck floor while finding
all forty stairs and the landing. Floor probes cover the staircase-to-pole route
and each of the25 existing upper-deck sectors. Capsule probes check overhead
and side clearance above the45cm step-up band; they do not simulate a player's
CharacterMovement step climbing or establish normal walking acceptance.

Final repair uses four exact centimeter-scale convex prisms for each of four
meshes (deck, wall and two rail pieces). Fresh isolated and canonical real-RHI
reloads pass75floor probes with0cm height error and49overhead/side capsule probes
without obstruction. The final hall capture retains the visible room structure.
This establishes collision queries, not physical keyboard/controller walking.

Collision repair and fresh canonical verification are recorded in
`WorkshopCollisionFix.json`, `CollisionAdopted.json` and `WorkshopPath.json`
under the private evidence directory. The initial in-session triangle result
passed75floor probes, but fresh canonical reload still missed30samples; that
candidate was rejected. Do not substitute the in-session pass for reload proof.

## Editor catalog restart defect

The live log previously reported `generator already executing` while repeatedly
restarting a3581-mesh pass. Export work pumps Slate and re-enters the post-tick
callback before its active generator yields. The callback now guards the entire
scan/export operation, releases the guard in `finally`, keeps real failure
backoff, and clears interrupted scan identity when disabled.

`Tests/TestCatalogRefresh.py`: four passing regression cases cover nested Slate
re-entry, real export failure/backoff, disable/re-enable with unchanged sources,
and exclusion during Play. CI runs this test. Python compilation passes. No
checkbox/marker setting was changed; both the prior pause marker and a current
enabled marker exist. Restart Unreal normally to load changed Python. A single
large export can still block the editor; whole-library responsiveness, daylight
cost, FPS/VRAM and owner navigation acceptance remain unmeasured.

## Preservation and retained failures

- Before motion changes,24files/579,994,966bytes were hash-preserved under
  `D:/SpaceSurvival_AssetArchive/CharacterWorkshop_20261021/BeforePolish`.
  Four original collision meshes are additionally preserved in its `Collision`
  folder. D is recovery only; active native and authoring assets remain on C.
- Current native manifest combines the original adoption with the two routine
  additions and scoped replacements. `NativeDeliveryCurrent.json` records847
  files; `DeliveryManifest.json` records the refreshed30portable authoring files.
  Final native size is2,559,920,132bytes; portable files total1,092,731,887bytes.
  Historical manifests remain intact; do not validate replacements against old hashes.
- Hall map remains SHA256
  `8b0838d6312e481a70a574dd1632736f24576131d544cf6552fba692571ccd8b`.
  Game module remains `2ca94427aec85f0040612d7a9b21620d8044fad6b4b2febec76d73ab775d533f`.
  Eighteen station/config/module guards and owner HEAD/index are unchanged.
- An initial Blender pelvis offset ignored its rest-bone basis; the corrected
  local-space transform passes source fidelity. Appended actions initially lost
  fake-user retention; explicit retention passes fresh reopen on all four files.
- Early collision queries assumed Python HitResult attributes and failed before
  checking anything. Installed reflection/native BreakHitResult order confirmed
  `to_tuple()` access. `get_simple_collision_count` excludes convex hulls;
  `get_convex_collision_count` correctly identifies them. Voxel decomposition
  raised the floor about3.29cm, so that candidate was rejected.
- Deferred probe callbacks initially lost `__file__` and failed without replacing
  the previous receipt. Corrected callbacks supply an explicit script context;
  receipts now include project identity and UTC time. The failed callbacks are
  not collision results. A UCX trial then exposed meter coordinates treated as
  centimeters; explicit centimeter export and import-coordinate assertions fix
  that scale mismatch. Legacy FBX import is selected only inside the authoring
  child because Interchange did not apply the supplied collision import options.

No C++ changed or rebuilt, no station layout or default hero/hull was changed,
and no packaged release or merge occurred. Vendor dependency/bind-pose/UDIM
warnings from the [initial receipt](2026-10-21-character-workshop.md) remain open.
New ship work is a backlog addition, not implemented flight behavior.

Private evidence: `.agent/local/CharacterBatch_20261021`, including
`BeforePolish`, `NativeRoutines`, `RoutineVerification`, `RoutinesAdopted`,
`BlenderRoutines`, `BlenderRoutineVerification`, `FootSurfaceSurvey`,
`RoutineVisual` and the collision records above. Visual samples are in
`Review/Joins/JoinReview.jpg`; the main private `Review.html` links them.
Licensed art, captures and raw logs are excluded from the source PR.

Source checks: four catalog regressions,50project structure checks, Python
compilation,26source meshes/17WAVs/unchanged GLB validation, canonical issue
navigation/counts and scoped whitespace checks pass. No C++ build applies to
this editor-Python/native-asset change. Full game performance is not measured.
