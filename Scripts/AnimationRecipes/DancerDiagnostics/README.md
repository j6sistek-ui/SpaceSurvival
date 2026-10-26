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
retained. Matched-camera controls reproduce the knee band in both Blender
and Unreal; the renderer-only inference is superseded. Videos are review evidence, not full rig/contact
or owner acceptance.

## Contact and unoccluded joint controls

Read the latest recipe section before repeating a trial. Knee helper/smoothing
controls and whole-clip fixed support are rejected. The local grip fit is useful
but not a completed routine. Run finger fit, thumb fit, full-motion audit and
then dense passage review in that order; each consumes the previous receipt.
The source-control scripts inspect materials, albedo and unoccluded distal
patches without adopting changes. Nested recipes resolve their code beside
these files and private data through SS_ANIMATION_PROJECT. Do not copy licensed
.blend/FBX/texture data into Git.

## Explicit supported-release candidate

Read the latest DEFORMATION_RECIPE section before the contact experiments.
Run review_supported_release, render_supported_release, bake_supported_release_candidate,
then verify_supported_release_reload with the existing hidden Blender. The
native capture/import script is restricted to CharacterWorkbench; its wide
recapture fixes first-pass framing and never saves assets. Fresh-reload and
fixed-basis bone comparison are separate from visual acceptance. The Cartesian,
hinge and keypose detours are rejected controls, not recommended solvers.
No complete routine or production adoption is claimed.

## Supported G2 and editable zero-G loops

The G2 passage is a selected570–770 source interval, not a complete original clip.
Use `review_g2_supported_passage.py` to retain its failed wider probe, then
`bake_g2_supported_candidate.py`, `capture_g2_supported_native.py`,
`verify_g2_support.py`, `reload_g2_support_native.py` and
`check_g2_support_media.py` for the guarded private transfer.
`author_zero_g_duet.py` creates two editable76s sequence orders referencing the
existing five clips. `validate_zero_g_duet.py` observes ordinary loop playback;
`verify_zero_g_sequence_joins.py` compares native curves/joints at boundaries.
See DEFORMATION_RECIPE.md for exact provenance and remaining limitations.

The historical right-hand50mm-pole calibration is versioned in
`calibration/vexa_right_pole_50mm.json`. `load_supported_grip.py` checks both
exact source hashes before returning its fitted matrices. Reproduction no
longer depends on a private optimizer receipt or rerunning the fit. This
preset is specific to Vexa a9dbcbde and action library0a38e12a; do not apply
it to Joy, Astra or another pole size without separate calibration.
**October26 supersession:** its signed finger curl is dorsal and rejected.
Retain it only to reproduce historical controls, not as an accepted grip.

## G2 posterior hip candidate

Run the consolidated contact validator/exporter, guarded four-vertex weight save,
posterior hip bake, actual-mesh validator, then proof export/import and fresh
native capture/parity comparison. See DEFORMATION_RECIPE.md for exact order,
input hashes, paired curves, failed broad targets and remaining defects. These
recipes refuse prior-output overwrite; they do not adopt production assets.

`audit_g2_hip_self_contact.py` adds the previously missing same-side hip/thigh
screen. Run it with the installed hidden Blender against the exact preserved
candidate. `SS_ANIMATION_PROJECT` selects the local project; the report goes to
the ignored G2PosteriorHip directory. Check `summary.screen_passed`, not just
process success: the current candidate fails822 of3682 side/frame samples.
This is a limited surface screen, not a complete collision or anatomy validator.



## G2 smooth hip-motion review (separate from skin repair)

`g2_smooth_hip_control.py`, `audit_g2_smooth_hip.py` and
`save_g2_smooth_hip_action.py` preserve the previous source and write only a
private action library. Run audit, save, then audit with `-- --reload-action`.
Read the latest recipe section for exact source/morph pairing and limitations.
The action clears the defined sampled hip/pole/distal-arm screens; it changes
the G2 leg motion and does not establish reusable weights, native parity or
artistic acceptance. Old REVIEW_G2_ hip curves must be muted on this action.

For the pacing derivative, run `retime_g2_smooth_hip.py`, then
`save_g2_paced_action.py`, then `audit_g2_smooth_hip.py -- --paced-action`
in separate hidden Blender processes. The authoring scripts preserve the mesh
and earlier action. The fresh audit compares the inverse-time pose path,
sampled skin surfaces and dense contacts; its timing targets are choreography
choices, not anatomical limits. See the recipe before reusing this on any rig.

For the local glute-follow candidate, add `--glute-follow` to the paced audit,
then run `save_g2_glute_follow.py` and a fresh `-- --verify-only` invocation.
The candidate requires its matching116-vertex weight manifest; the animation
alone is incomplete. Only two helper channels are rebaked; fractional old keys
must be cleared first. Full garment/native/artistic acceptance remains open.


For the saved glute-follow native proof, run `export_g2_glute_proof.py`, import
and compare with `SS_G2_VARIANT=glute_follow`, then retain its120Hz failure.
`probe_g2_glute_resampling.py` isolates sampling error;
`export_g2_glute_rate_refinement.py` writes the240Hz animation while reusing
the rest FBX. Import/capture/compare with `SS_G2_VARIANT=glute_follow_240`.
Author/import scripts refuse to replace previous proof payloads.

`review_g2_grip_motion.py` audits the exact saved candidate without modifying
it. Its `-- --labels` mode identifies thumb/little finger; `-- --isolate`
renders unobstructed forearm motion. Cyan is thumb, violet is little finger.
The sampled native/contact checks did not catch dorsal finger flexion; the
old grip is rejected. Read the recipe for source hashes, controls and limits.

`-- --palm-proof` captures anatomically named palm/back views plus an
open-finger control with the same wrist. Earlier front/back filenames name
cameras, not hand anatomy. The control changes no saved asset.

## Signed palmar grip controls

`probe_g2_palmar_grip.py` fits an unsaved grip with the correct signed curl.
The thumb-opposition control uses `-- --thumb-axis --surface --cmc --opposition --fit`;
the separate `--reuse` invocation records a private, guarded calibration only.
It refuses to overwrite that calibration. Earlier controls are rejected.

`g2_palmar_motion_control.py` compares whole-body translations with an arm-only
two-bone solve (`--arm-ik`) and staged thumb release (`--staged-release`).
`--dense` samples every60Hz frame; `review_g2_palmar_motion.py` uses the same
options for opposing views. `probe_palmar_release.py` isolates finger-opening
collisions. `plan_palmar_release_path.py` records a rejected discontinuous path:
clear individual points do not establish a collision-free continuous release.
All results remain private controls pending complete motion, speed, anatomy,
native and visual review; no saved game asset is changed by these scripts.

The current palmar motion candidate uses
`-- --arm-ik --staged-release --free-wrist --index-lead 2.3`.
Run `g2_palmar_motion_control.py` with those arguments and `--dense`, then
`check_palmar_timing.py` with the same arguments. Their exact source/control
hashes gate `save_g2_palmar_action.py -- --source-knots`. The saved action-only
library requires the existing116-vertex waist patch; it does not duplicate the
character mesh or textures. Existing outputs are never overwritten.

Fresh `save_g2_palmar_action.py -- --source-knots --verify-only` compares all95
bones at half-frame times and measures actual playback speed. Add
`--surface-only` for the saved right-hand/pole triangle screen. Uniform120Hz
baking is retained as a failed comparison (1.198mm bone error), even though its
6141 saved hand/pole samples clear. Preserve source fractional key breakpoints
when baking; increasing nominal frame rate alone does not preserve corners.

`review_g2_palmar_motion.py` adds `--saved --source-knots` for the current saved
candidate and `--movie` for opposing12Hz inspection frames. Camera names front/back identify
viewpoints, not anatomical palm/back orientation. No review script certifies
complete anatomy, artistry or native/game adoption.

The current409a79ad action passes12281 fresh source replay samples (maximum
0.0808mm bone error) and6141 saved hand/pole surface samples. Two615-frame
opposing videos fully decode. `export_g2_palmar_proof.py` exports only this
action at240Hz and reuses the existing unchanged glute-follow rest FBX.
Set `SS_G2_VARIANT=palmar` for `import_g2_posterior_proof.py`,
`capture_g2_posterior_proof.py` and `compare_g2_glute_native.py`. These target
the private CharacterWorkbench only. Import reuses the previous mesh/skeleton
without saving them; old proof hashes must remain unchanged. Fresh native
results are separate from source evidence and must be read before adoption.
Current fresh native receipts pass eight poses within0.116mm bones/0.195mm
surfaces;38 stills and1229 fully decoded loop frames remain private. Review
`SourceAssets/DanceRefinement_20261025/G2PalmarReview.html`. This is scripted
sampling, not natural gameplay or complete artistic/rig acceptance.

## G1 signed grip and folded-arm shoulder

`g1_palmar_motion_control.py -- --rigid --free-profile --continuous-release --pin-orientation --dense`
uses the signed G2 calibration while preserving the supporting arm's local
motion. `fit_g1_free_elbow.py` isolates the free arm's inherited chest contact;
the saved `FreeArmProfile.json` is guarded separately. Read the recipe before
recreating a profile. `check_g1_palmar_timing.py` records the shared slow timing.
`save_g2_palmar_action.py -- --g1` saves a separate G1 action; rerun with
`--verify-only`, then `--verify-only --surface-only` for fresh replay/contact
checks. Run `check_g1_palmar_timing.py` with `--continuous-release --pin-orientation`
to select this same control. It is a nonlooping passage, not an interchangeable
zero-G loop.

`review_g1_shoulder_regression.py` compares preserved torso weights and bare
body geometry at the actual bad pose. `review_g1_forward_shoulder.py` offers
separate `--smooth-control` and `--cap-control` comparisons. The latter checks
the axilla-only mask against one extending over the shoulder cap, with the
neck excluded. Neither control saves a character or changes weights.

`bake_g1_shoulder_corrective.py -- --cap` bakes that localized target for G1's
actual poses; it refuses to overwrite a saved candidate. The 120Hz target
sampling and held-out checks must pass before a file is written. Old Spiral
corrective curves cannot simply be replayed over G1. The new shape action and
G1 bone action must remain paired; this is a clip-specific correction, not a
general range-of-motion solver.

`review_saved_g1_shoulder.py -- --cap` makes matched source comparisons; add
`--video` for opposing full-passage views. `export_g1_shoulder_proof.py -- --cap`
checks fresh saved surfaces against the target and exports a new mesh plus
240Hz animation. Set `SS_G2_VARIANT=g1_shoulder_cap` for the existing
`import_g2_posterior_proof.py`, `capture_g2_posterior_proof.py` and
`compare_g2_glute_native.py` entrypoints. They create a new private workbench
proof, never replace the game character. Read their receipts before claiming
native success. Use hidden Blender with `--factory-startup` so unrelated user
addons do not run or race over their own startup files.

For the separately identified cap-normal artifact, run
`export_g1_shoulder_normals.py` and `import_g1_shoulder_normals.py` after the
cap proof import. These create a separate green-mask rest mesh, retaining the
original. With `SS_G2_VARIANT=g1_shoulder_cap`, capture first with
`SS_G1_NORMAL_CONTROL=local` (three poses, opposing A/B views), then unset that
variable and use `SS_G1_RECOMPUTE=local` for the complete passage. Global
recomputation is a retained control that affects unrelated seams; it is not
the selected treatment. Read receipts and inspect both geometry and shading.

Add `SS_G1_SHOULDER_MOTION=1` for the separate front close-up capture. After
both capture receipts and native parity pass, `build_g1_shoulder_review.py`
encodes/decodes both videos and creates the private `G1ShoulderReview.html`.
This is a nonlooping G1 review; no game build or broad rig acceptance follows.

## Current flow and source-library studies

Read [CHOREOGRAPHY_BLOCKS.md](CHOREOGRAPHY_BLOCKS.md) before creating new routines:
restore the current G1/G2 phrases first; show concepts before new rigging/animation.
The owner-facing CurrentGLegReview.html/video is an assembled82.75s review,
not an integrated loop. describe_g_routine_sections.py records its source coverage.

The private4s bridge uses review_g1_g2_join.py, fit_g1_g2_join_corrective.py,
save_g1_g2_join.py and review_saved_g1_g2_join.py. export_g1_g2_join_proof.py
and SS_G2_VARIANT=g1_g2_join select the existing native import/capture/compare
entrypoints. Read their receipts; no production adoption follows automatically.

For the first leg pass, review_g2_floating_life.py -- --phrase performs the
bounded audit; --phrase --render --framed renders unsaved control previews.
save_g2_floating_phrase.py / --verify-only and export_g2_floating_phrase.py
preserve original source keys; native variant is floating_phrase.
The separate --source-legs trial fails contact checks and is diagnostic only.
Only --render --framed --diagnostic allows its explicitly failed preview.
Never bypass the acceptance assertion to save or adopt that trial.

review_raw_motion_sources.py inventories original G1/G2 and IMG9733.
review_library_motion.py takes --out, --mesh, --slow and repeated
--clip Name=FBX options, using the source mannequin. CPU
build_library_motion_review.py --root REVIEW_DIR --output OUTPUT_DIR encodes
and fully decodes each view. Use hidden Blender --factory-startup; no downloads
or host installs are required. Private review paths/hashes are in the recipe.

`review_current_g_timing.py` creates a separate video-only timing comparison.
It preserves every original pose frame at a 60 Hz presentation rate, with
repeated frames, and does not edit an action or evaluate new poses. Smooth
speed ramps shorten four held sections from 82.75 to 75.05 seconds. This is
an editorial comparison, not a replacement animation or contact check.

`review_g2_floating_life.py -- --source-phrase` tests a coordinated G1 source
phrase in the existing G2 released return, preserving the saved first-leg pass
outside that window. The current control fails arm/body and posterior-hip
intersection checks and must remain diagnostic. Add `--render --framed
--diagnostic` only to inspect that failure; encode with
`build_g2_floating_review.py --source-phrase --framed --diagnostic`.
The resulting private `G2SourcePhraseCurrentReview.html` is an unsaved preview,
not an adopted action or a new conceptual block.
