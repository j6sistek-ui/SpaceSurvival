# Dancer orientation diagnostics

These recipes serve RPT-20261021-01. They require the owner's licensed local
character/source files and an existing isolated `CharacterWorkbench` project.
They do not install tools or launch an application themselves. Set
`SS_ANIMATION_PROJECT` when the canonical project is not `~/SpaceSurvival`.
Run Blender with `--background --factory-startup` and Unreal with `-NullRHI`
or `-RenderOffscreen`, always from a hidden process on Windows.

- `forearm_markers.py`: add/remove separate cyan arrows, skinned to the forearm
  bones. They follow roll and point toward the wrists. No texture edits.
- `prepare_source_baseline.py`: export the four untouched GLB rigs/motions;
  create a compact removable marker library and CPU close-ups. `--markers-only`
  skips source exports. Originals are only read.
- `retarget_source_baseline.py`: isolated native IK Rig/Retargeter setup with
  matching chains and a named aligned target pose. Pelvis and FK operations only;
  no forced grip, invented orbit, smoothing or time remapping.
- `export_baseline_review.py`: native baseline FBX export for inspection.
- `author_source_review.py`: private review-map copy and tagged marker actors.
  Remove `SS.ReviewOnly.ForearmMarker` actors to remove the native overlay.
- `capture_source_review.py`: hidden native pose captures. Inspect image framing
  and settled poses; a successful screenshot call is not visual acceptance.
- `audit_baseline_arms.py`: frame screening for reversed elbow hinges and the
  owner's torso-relative reach limits. `--rejected-control` must detect the
  known V8 reversal. Flags identify frames for inspection; the script does not
  clamp poses or establish anatomical quality.
- `repair_existing_retarget.py`: repair per-animation F3 reference data and
  rebuild two joins from unretargeted poses in the workbench only. Shared
  skeleton modes and original source files remain unchanged.
- `verify_original_repair.py`: read-only fresh canonical reload of six repairs.
- `adopt_native.py`: hash-backed six-file original-name adoption path. New
  choreography-library adoption deliberately raises an error while V8 is
  rejected. Do not replace that guard with numeric-only success criteria.

All generated FBXs, Blender files, native packages and raw evidence remain
private under `.agent/local/AnimationReview_20261025` or `SourceAssets`.
See [evidence](../../../docs/validation/2026-10-25-dancer-orientation-diagnostics.md)
and the canonical [issue log](../../../docs/KNOWN_ISSUES.md). Character/skin,
contact, continuous motion, four-performer reuse and owner acceptance remain
open. This is diagnostic delivery, not an approved animation set.
