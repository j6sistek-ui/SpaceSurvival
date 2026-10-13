# Silver hair coverage and face collision — 2026-10-13

Related issue: RPT-20261013-01. Saved hair repair; owner acceptance and broader motion/performance remain open.

The owner reported bald-looking sides and bangs passing through the skin. Hair swinging in front of the face is allowed. Colors are left to the owner; shoulders and other anatomy are outside this repair.

## Cause and change

The retained master contains all original strands, but `BackHairVisible` hides all3,535 right-side and1,212 right-top source curves. Both sections exported empty; native hair contained12,298 curves. The tip-only rear-hair filter removed scalp coverage as well as front-falling lengths.

Restoring the complete long locks produced unstable simulation and was rejected. The saved repair instead adds15,228 short, tapered strand prefixes as a nonsimulated scalp/temple layer, bound to the current mesh. The original12,298-strand groom still supplies moving lengths. The hair-only editable source and Alembic live under the task's `HairCoverage` folder; the full master and856-frame cache are unchanged.

The former head proxy belonged to `neck_01`, and its front envelope sat inside the measured face. A separate PhysicsAsset reuses the installed mannequin's head-body structure with Silver's fitted body shapes. Its head capsules follow `head`; the front capsule runs from(0,6,158) to(0,6,169)cm with7.2cm radius, covering the approximately12cm facial projection. The original PhysicsAsset remains unchanged on disk. This is approximate guide collision, not exact per-strand skin contact.

Current additions under `/Game/SpaceSurvival/Licensed/ViableEldReview_20261013/HairCoverage_v3`:

- `G_Silver_ScalpFoundation` and `GB_Silver_ScalpFoundation`.
- `PA_Silver_HeadCollision`, assigned to the original dynamic hair component.
- Existing `MotionFinish_v1/BP_Silver_Apartment` gains `PlatinumScalpCoverage`; its saved hash starts `fae67c6d`.

Both hair components use the existing platinum material. Body, outfit, colors, animations, original groom/binding and source PhysicsAsset hashes are preserved. The station map is not resaved or restored over later owner changes.

## Native evidence

`Silver_HairCoverage_Dance.gif` contains148 actual native frames covering28.49seconds, SHA256 `ba67836e936ffd552172b7577ea8b25bb424644465f2e6775258d98287f1583f`. Capture used quarter-speed game time to avoid large simulation steps caused by synchronous image export; GIF timings are reconstructed from animation time. This is not a frame-rate benchmark.

After saving the Blueprint, a separate normal-speed full-dance probe collected121 tick samples and seven three-quarter views. Niagara stayed active. Reviewed views show scalp/side coverage retained and the fringe outside the face during the turn and dip; temporary front coverage remains possible. Long-hair contact against arms/torso, arbitrary future clips, representative performance and natural gameplay remain unverified.

Local evidence: `HairCoverage/FinalFrames/Capture.json`, `GIF_Receipt.json`, contact sheet, `NormalSpeedProbes/Probes.json` and seven native images, `FaceBounds.json`, `FaceFit.json`, `Adoption.json`, and `ApartmentReadback.json` for saved apartment verification. Earlier trial images/receipts remain labeled as historical; v1/v2 native trial assets were removed.

Fresh headless-editor readback confirms the saved apartment actor still at(6900,4620,-169.5), both expected hair components/bindings,15,228+12,298 curves and the new face collision assignment. The9,408-actor station map remains byte-identical at`a36bffca`; both owned editors closed cleanly. This verifies saved asset loading, not an additional apartment performance test.

## Preservation and validation

The native repair changes only Silver's existing Blueprint plus the three new hair/collision assets. Protected mesh, material, original groom/binding/PhysicsAsset hashes pass. No C++ source, build, cook or release change. Python syntax and repository documentation checks apply; no new C++ build or unrelated test suite is warranted.

The earlier cleanup measurement of3,001,998,411bytes is historical, before these new retained assets and previews. Keep the four original Downloads GLBs (54.2MB). Rejected exports and raw capture frames are disposable once the final GIF and diagnostic samples are verified; preserve the final hair source, master/cache and receipts.
