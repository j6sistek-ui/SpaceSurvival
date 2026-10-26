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

## Source refinement experiments

`compare_source_target.py` and `analyze_contact.py` compare source/target poses
and expose fast hand movement. `refine_motion.py` writes nine private derivative
actions; `review_refinement.py` screens and renders them. These are unaccepted
experiments, not a production contact solver.

`inspect_hip.py` and `compare_hip_skinning.py` inspect weights and compare linear
versus preserve-volume skinning without source writes. `bake_hip_correctives.py`
creates a clip-specific Roxie Spiral morph proof; `review_hip_curves.py` renders
it and `reexport_hip_proof.py` produces separate rest/animated FBXs.
`import_hip_proof.py` is guarded to the private workbench and uses an ephemeral
legacy-FBX setting in that process only. `capture_native_hip.py` creates a private
review map. Manually reject empty/misframed captures and inspect warnings; the
callback reports successful execution, not visual approval. This proof is not
yet a reusable four-character deformation system or adopted game asset.

`DEFORMATION_RECIPE.md` records the verified controls, narrow owner hip approval,
rejected knee approaches and separate leg-plane candidate. `leg_plane.py`,
`bake_leg_plane.py`, `export_leg_plane_proof.py` and
`review_leg_plane_motion.py` reproduce the candidate. `export_native_leg_proof.py`
requires a regular offscreen editor with ticks, not a commandlet;
`audit_native_leg_roundtrip.py` measures exported-data parity separately from
engine rendering. `build_deformation_review.py` creates a local comparison page.

Current target: **Vexa only**. `audit_dancer_leg_compatibility.py` verifies the
shared body before later reuse. `inspect_vexa_shoulder.py`,
`review_vexa_clavicle.py` and `review_vexa_full_shoulder.py` isolate the reported
shoulder collapse. `shoulder_support.py` and `bake_vexa_shoulder.py` create a
separate Vexa Spiral proof, not a general contact solver. For its export, native
import/capture and full-character review, set `SS_REVIEW_SHOULDER=1` (do not also
set `SS_REVIEW_LEG_PLANE`); the full-character review additionally requires
`SS_REVIEW_CHARACTER=Vexa`. These outputs remain private and unaccepted.

## Current symmetry and nape investigation

`audit_vexa_shoulder_foundation.py` separates rest weights from asymmetric poses.
`review_vexa_symmetry.py` tests exactly mirrored arm poses before and after the
protected transfer in `mirror_vexa_shoulder_weights.py`. `coordinated_girdle.py`
replaces mismatched inherited clavicle motion for free-floating review only.
`bake_vexa_coordination.py` and `review_vexa_coordination_saved.py` save/reload a
compact private proof. `audit_vexa_neck_seam.py` verifies paired modular vertices.

`audit_vexa_nape.py` localizes the posterior fold; `nape_weights.py` smooths only
its weights across the paired head/body boundary. `review_vexa_nape_cpu.py` uses
four CPU threads and Cycles CPU, and `audit_vexa_balanced_proof.py` checks the
whole961-frame seam and rejects lossy eight-influence pruning. The current proof
retains up to10 influences, pending native-budget checks. These scripts never
launch Unreal or adopt an asset. Earlier helper-bone studies are rejected
diagnostics, not the current candidate. See DEFORMATION_RECIPE.md for limits.

## Balanced native review

The balanced exporter preserves its source blend. Native import asserts the private workbench and unlimited-influence configuration; capture/readback and parity scripts distinguish component geometry from rendering. Clean captures remove misleading normal bands; motion capture and encoding retain two24fps native views. GPU and garment controls inspect the remaining axilla fold without changing original assets. These are diagnostic recipes, not production adoption or owner acceptance. The encoder uses an existing FFmpeg executable; it installs nothing.

## Distal and wrist-motion follow-up

The hand-contamination and continuous-distal recipes create separate guarded copies. The native distal harness tests48 views and sampled surface parity. G/B reuse disables Spiral-specific correction curves. The wrist continuity repair preserves other local keys and exports a separate library; the comparison harness captures matched native events and complete G1. See DEFORMATION_RECIPE.md for exact hashes, rejected controls, export-root identity and remaining gates. No recipe authorizes production adoption.

## Carrying the approved shoulder response into other clips

Start with the practical procedure at the top of DEFORMATION_RECIPE.md. The `review_gb_shoulder_response` and `bake_gb_shoulder_response` recipes isolate and bake the approved G1 response without replacing the Spiral proof. Export/capture/encode/reload scripts verify four native derivatives and opposing G1 views. No pole-contact or full-motion acceptance is implied. Recipe wrappers reuse the existing tracked harness; keep those dependencies together.

## One-vertex hand isolation

The finger control/audit/repair recipes isolate opposite-hand weight contamination without replacing hand animation. Export/capture/fresh-reload and whole-surface comparisons preserve the earlier proof. Use the SkeletalMeshEditorSubsystem LOD accessor for the actual influence setting; failed reflection controls remain documented. Raw GLB rotation auditing distinguishes source motion defects from skinning. See the recipe for exact hashes and evidence limits.

## Bounded motion edits

The three selected arm-passage repairs preserve earlier action libraries and
restrict their edits to inspected intervals. They deliberately change hand
paths; they are not a contact solver or a universal anatomical limiter. Read
the recipe before reproducing them. Matching full native videos and fresh
reloads remain separate from complete routine and owner acceptance.

## Shared zero-G correction

The five-segment proof uses one shared basis and explicitly paired rig/shape
actions. Read the working recipe before export; old Spiral coefficients do
not transfer by time alone. Normal-mask and failed interpolation controls are
retained so renderer faults are not mistaken for geometry failures. Native
normal bands remain unresolved. Videos are review evidence, not full rig/contact
or owner acceptance.
