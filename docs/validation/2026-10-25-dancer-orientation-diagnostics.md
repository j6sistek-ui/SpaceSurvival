# Dancer orientation diagnostics — October 25, 2026

**Result: diagnostic overlay verified; choreography repair remains PARTIAL.**
Active work and owner acceptance: RPT-20261021-01 in `docs/KNOWN_ISSUES.md`.

## Owner failure and correction of approach

James rejected G1/G2 and B1/B2 on Vexa, then rejected the procedural contact
candidate for backwards elbows, apparent missing-arm silhouette and body rotation
away from a planted hand. V8 is rejected and its library is not adopted.
The new-library adoption recipe now refuses to run; numeric reports cannot
override this rejection.

The requested limits are treated as a conservative animation direction: sideways
reach through T-pose, overhead reach no more than 10 degrees behind the head,
forearms facing forward on rise and no impossible twist. These are owner style
constraints, not a claim about universal human ranges of motion.

## Removable orientation marks

Small cyan arrow meshes follow each forearm bone and point toward the wrists.
They are fitted to the skin surface but are separate geometry. Skin textures,
original character files and original materials remain unchanged.

- CPU close-ups visually confirm the mark on the forearm.
- A rotation probe confirms the mark moves with forearm roll; removal removes
  the diagnostic collection without changing the character.
- Native follower meshes use the character's leader pose in the private map.
  Native Vexa and Roxie captures visibly show the arrows; four actors have the
  overlay, but the sampled Jinx/Vesper camera angles do not expose both marks.
- Remove the `REVIEW_ONLY_ForearmArrows` objects in Blender, or actors tagged
  `SS.ReviewOnly.ForearmMarker` in the private Unreal review map.

Local preview:
`C:/Users/j6sis/SpaceSurvival/SourceAssets/ZeroGChoreography_20261025/Diagnostics/Review.html`.
The compact `ForearmReviewOverlay.blend` contains the rig and overlay, not a
second packed character/artwork copy.

## Source-first baseline

Nwiro was not live during this pass. The owner-provided Control Rig/IK and
animation-system guides were consulted at commit
`023eaa68d80897e6df64a22fcf471940a7b6848b`; installed UE5.8 headers were checked
for IK Rig/Retargeter controller and batch-retarget APIs.

The four original GLBs were exported without changing their keys. A separate
native retargeter aligns the target F3 pose to the source, matches all 20 chains,
and runs pelvis/FK transfer only. It does not lock a hand, impose an orbit,
filter motion or change playback speed. No shared skeleton retarget modes change.
Exported target reference positions agree with the supplied F3 Blender rig
within 0.0000004 m; reference rotation comparison is 0 degrees.

Private map:
`/Game/SpaceSurvival/Licensed/ZeroGSourceBaseline_20261025/L_SourceBaseline_Review`
in `.agent/local/CharacterBatch_20261021/WorkbenchNative/CharacterWorkbench.uproject`.
This map and its new baseline assets have **not** been adopted into the main game.

The frame screen measures elbow bend-plane alignment in the humerus frame and
rearward reach in the upper-chest frame. It does not modify poses. The known
rejected G1 control produces 84 reversed-elbow frames. The new native baseline
produces 0 in 4,566 sampled frames, but all four clips still flag rearward reach.
Those flags require pose/source inspection; they are not a substitute for visual
motion review, palm/finger orientation, contact or the owner's acceptance.

## Existing six-file repair, separately verified

The original-name F3 clips had received a second mannequin retarget. Their
per-animation authored reference mesh is now the actual F3 Quinn mesh. Two joined
routines were rebuilt from unretargeted poses while preserving their original
0.48-second transition. Four raw source clips were not rewritten.

Six private native files were copied with SHA-256 before/after manifests and
backups. Fresh read-only canonical reload passes for all six; the maximum
evaluated-versus-unretargeted position difference is 0.00003814 cm. This proves the
proportion/reference repair, not acceptable choreography or pole contact.

## Evidence limits and retained failures

- Early position-only contact passes missed the backwards elbow. Those failures
  and the owner's screenshots remain part of the issue, not overwritten by a pass.
- A first native capture attempt could not spawn an editor camera during PIE;
  the camera is now created before Play. The first image on the retry captured
  an unsettled viewport; it is excluded from matched-pose conclusions.
- Later native back/side/arm captures show the marker and baseline skin pose.
  These are sampled poses, not full-routine or arbitrary-join acceptance.
- Source mannequin FBX imports report absent smoothing groups; retarget logs
  report no animation curves and Interchange import-data dependency warnings.
  They are recorded, not suppressed. Source/target animation and skin quality
  still require review.
- Prior five-segment zero-G endpoint/chamber measurements remain preliminary.
  They do not establish natural arms, AAA quality or approved choreography.

Local receipts are under `.agent/local/AnimationReview_20261025`: `ForearmMarkers`,
`NativeSourceBaseline`, `BaselineFbxInspection`, `BaselineArmScreen`,
`RejectedControlArmScreen`, `SourceReviewCaptures`, `OriginalRepairFreshReload`,
`Adoption_originals` and `ProtectedAfter` JSON files. The hash guard verifies
220 protected files plus 65 preserved source files. Original station/observatory,
character originals, saves and Editor DLL `70234269` remain unchanged.

No C++ changes or new binary/package were produced. Native authoring, CPU
Blender rendering and read-only native reload were exercised. Portable source
and documentation checks are recorded in the PR after execution.

## Open / Check / Still open

- **Open:** local `Diagnostics/Review.html` for the removable marker. Private
  review map uses the existing local Editor DLL; no new packaged build.
- **Check:** no new owner motion retest is requested. The arrows are a lead-side
  diagnostic aid; the prior failed owner result remains open.
- **Still open:** lead must inspect source-versus-retarget whole motion, repair
  reach and contact without unnatural joint forcing, rebuild fluid G/B joins,
  finish the modular zero-G set and verify all four dancers continuously from
  multiple angles before owner acceptance.

## October25 source refinement and hip proof (still partial)

The owner accepted only the near/front overhead arm in the Vexa G1 screenshot.
The far arm behind the head remains rejected. The initially pinched hip in
Roxie's curled floating pose was subsequently corrected and that specific hip
silhouette was owner-approved; knees and the full routine remain unaccepted.
Earlier supplied clips remain the primary choreography
reference. The later20-second video supplies pacing and purposeful-floating
guidance only; it is not a replacement or an artistic quality ceiling.

The private `DanceRefinement_20261025` library contains nine derivative clips.
G/B changes filter local rotations and constrain excessive rear reach without
fixed-hand IK; zero-G uses slow arm phrasing over the earlier torso/leg motions.
An automatic axial-arm turn was rejected before use. A projection-only trial
created a25cm one-frame hand jump and was also rejected. V3 reduces that maximum
to11cm in G1; this is still an inspection flag, not a fluidity pass. Sampled
overhead views show the far arm clear of the head. The full animation, contact,
hands, joins and four-character skin quality remain unaccepted.

The hip comparison isolates loss of volume from linear skinning. Whole-mesh
preserve-volume deformation improves the hip but introduces other distortions;
it is not an Unreal fix. A single fixed corrective also distorts adjacent poses
and was rejected. The current isolated Roxie Spiral proof instead samples local
hip corrections across241 poses, compresses them to24 morphs per mesh and bakes
the coefficients. The three-mesh proof reproduces the sampled target within
0.125mm; nine held-out pose times are within0.137mm in rest-space correction.
Blender opposing views at6/8/10seconds show improved hip volume. These numbers
only describe approximation to that target; they do not prove anatomy, clothing
contact, generalisation to other clips or native playback.

The compact proof Blender file is7.7MB and includes only rig, three meshes and
curves, with no duplicated texture library. Original character files, licensed
motions, production maps, saves and DLL remain unchanged; the220+65 hash guard
passes. New library adoption remains disabled.

The first native import exposed72 animation curves but reported an invalid bind
pose. Initial captures were black, and an unlit retry did not establish source
parity. Legacy FBX testing found an unsaved skeleton dependency: explicitly
saving it permits a fresh process to play the proof. Eight sub-micron bases
were explicitly removed after a961-frame cumulative audit (maximum0.00327mm);
the saved hip-only proof has64 matching morphs/curves. Multi-mesh FBX bind-pose
warnings remain; imported source geometry parity is not fully established.
Do not interpret an importer or screenshot callback as visual approval.

## October25 open-knee follow-up

The owner rejects partially open knees and the distorted thigh silhouette.
Their raised-leg anatomy photo is the contour reference. DQ-only knee volume,
local smoothing and calf-only axial cleanup did not establish an acceptable
result. The calf-only trial is disabled by default (`SS_REVIEW_CALF_ROLL`);
it was never adopted. A simple native negative-Z calf bend gives a cleaner
contour than the transferred pose, isolating a bend-plane/roll problem.

The isolated leg-plane candidate aligns thigh and calf to the native hinge
while retaining hip/knee/ankle centers and source foot transforms. Near straight
extension it transports the previous plane to avoid unstable cross-product
flips. The961-frame Spiral bake reports zero center displacement before
reconstruction and a maximum3.394-degree local leg rotation step; evaluated
four-pose reconstruction is within0.006mm. These are technical bounds, not
anatomical or fluidity acceptance. The first pose-assignment harness moved
joints because parent transforms were stale; it was rejected and replaced by
explicit local-basis reconstruction. The first full bake also correctly stopped
at frame723's nearly straight knee before plane continuity was introduced.

Changing thigh roll invalidates the old hip corrective. The candidate therefore
rebakes its own localized hip morphs and preserves the approved earlier proof
separately. Opposing Blender views show a cleaner open knee at~60 and~39degrees,
and a rounded curled hip; remaining skin/contact and full-motion quality still
need review. A16-second full-character diagnostic video is retained. The native
candidate imports65 matching morphs/curves into a separate private folder after
seven negligible bases are removed (combined error0.00195mm). First native
captures clipped exposure/framing and were rejected. The subsequent neutral
geometry run has12 settled images,65 curves and matching requested playback
positions after fresh load. A shader-pin naming assertion was fixed using the
installed MaterialEditingLibrary contract. A commandlet FBX export hit the
known MeshObject assertion; an ordinary offscreen editor export after ticks
succeeds. Reimported native FBX is compared at seven times against the Blender
proof:95 common bone centers differ by at most0.0108mm, and bidirectional nearest
surface vertices by at most0.0163mm after one fixed rigid alignment. This is
exported-data parity, not a GPU skinning, production-material or artistic pass.
No new knee/hip library or corrective is adopted in game.

See `Scripts/AnimationRecipes/DancerDiagnostics/DEFORMATION_RECIPE.md` for the
repeatable sequence and its acceptance limits. The guide distinguishes the
owner-approved hip frame from the still-unaccepted knee/leg candidate. Reuse on
other characters requires their actual meshes/weights and new motion checks.

Deferred at the owner's request: inspect existing CyberGirl `AS_falling_idle`,
standard fall loops and Space Crew zero-G float/move/push-off/grab/release clips
for useful future poses. Their local files exist; they were not added to this
routine or evaluated for quality during this pass.

Local receipts: `SourceComparison`, `RefinementReview`, `HipReview`,
`HipCorrectiveProof`, `HipCurveProof`, `NativeHipProof*`, `NativeHipCapture*`.
The initial fractional-frame harness exception is retained and fixed by passing
an integer frame plus subframe; the failed proof did not alter original assets.
The owner-provided importing-content guide and Epic's FBX morph/Interchange
documentation were consulted on2026-10-25. No plugin was installed and no
project-wide importer setting was changed.

## October25 Vexa-only shoulder follow-up

The owner rejected the collapsed underarm in the blue diagnostic, clarified the
pink/purple-haired character, and requested one target at a time. Vexa (saved
Eden) is now the sole repair target. The other three candidates were generated
before that direction and remain unadopted. The read-only compatibility audit
confirms identical body geometry, topology and weights and the same95-bone rest
rig. Bottom-garment transforms differ; outfit fit must still be checked per
character. The waist investigation finds48 matching skin-boundary pairs within
0.035mm across three poses; the pronounced grey ridge is the underwear overlay.
The owner reports reconnecting Vexa top/bottom in AFS; its setup/cause is unknown
and AFS was not modified.

Vexa controls separate arm direction, clavicle support and skinning collapse.
Whole-torso DQ and twist-only redistribution did not establish a good shoulder.
The separate candidate raises the clavicle with overhead reach and restores
volume locally around the shoulder. Three boundary rings protect modular joins.
Full-source assembly front, back, oblique and whole-body views at8 and9.033seconds
show improvement, not final anatomical acceptance. The resulting961-frame
Spiral action has a maximum0.437-degree shoulder local step. Twenty-four extra
shoulder bases reproduce the sampled target within0.024mm; eight held-out times
are within0.023mm. Boundary correction is effectively zero. These measure a
chosen deformation target, not artistic success.

The arm branch translates by up to4.32cm, so this free-floating correction must
not be used for fixed pole contact without recomputing contact. The compact
private Vexa proof retains89 hip/shoulder review morphs after seven negligible
hip bases are removed (combined maximum0.00195mm). Separate rest and animated
FBXs import successfully with89 matching native morph curves. New production
adoption remains disabled. Full continuous motion, hands, clothing, knee/thigh
acceptance and the remaining choreography are still open.

The owner subsequently said the result was more normal, then explicitly clarified
that it is better but still needs improvement. This is positive direction, not
completion or acceptance of every pose. The saved Vexa proof was reopened for
whole-character opposing captures and a16-second motion review. Original body
shape geometry is also identical across the four source files. Preserve Vexa's
improvement and finish her before propagating it.

Native readback matches95 bone centers within0.0066mm and the surface within
0.0135mm at seven times, but actual native close-ups reveal uneven surface/shading.
The first tangent toggle had no compute-shader support and was not a valid
tangent repair. A second process enables and reads back all three relevant
skin-cache flags as1; the visible defect remains. A world-position derivative
normal control also retains surface irregularity, so this is not accepted as
merely a normal-map issue. These failed captures are retained. A duplicate-mesh
precision probe changes morph compression from20 to0.01microns, with verified
readback, but does not establish a visual repair. The first property name was
obsolete; the next attempt changed a copy of an Unreal struct without writing
it back. Both failed attempts are retained. Material skeletal/morph usage flags
were already true. A runtime CPU-morph toggle is read-only and stayed1, so that
attempt is not a valid CPU/GPU comparison. Do not infer an engine defect.

A Geometry Script snapshot of the live component at four times contains8352
vertices. Against the saved Blender proof, bone centers match within0.143mm and
bidirectional surface positions within0.118mm. This CPU-skinned readback narrows
the discrepancy but does not certify the GPU image or appearance. The installed
GeometryScripting plugin was enabled only in the private process. No project
plugin/config setting was changed. Neutral shading and camera matching remain
part of the native visual investigation.

## October25 shoulder-girdle reference and underarm follow-up

The owner rejects the left-underarm fold while preferring the other shoulder.
Their later screenshot calls the isolated smoothing candidate possibly close,
not accepted. A raised-arm anatomy image and16.5-second screen recording of a
shoulder-blade rig are reference ideas, explicitly not an instruction to copy
that rig. The owner highlights coordinated scapula, clavicle and torso movement.
The original F3 hierarchy already connects clavicles to spine_05 and upper arms
to their clavicles. It has no scapula bones; the screenshot's reparenting advice
is therefore not a demonstrated repair for this rig.

A separate Vexa left-underarm proof uses a localized Corrective Smooth target,
then inverse-skins and bakes24 basis curves. The better right shoulder and modular
boundaries remain untouched. Sampled error is0.077mm; eight held-out times are
within0.056mm. These measure approximation, not anatomy. Freshly reopened
hair-hidden front/back/side views expose the remaining shoulder details; source
hair/materials are unchanged. The first bake stopped on a shadowed variable
before saving; the corrected run is retained separately from the earlier proof.

The separate ShoulderGirdle study adds two scapula helpers to a private copy,
parents them to the upper spine and derives their motion from the existing
clavicle/shoulder relationship. All95 original rest bones and arm motion are
preserved. Smooth posterior skin-weight transfer affects185 vertices per side;
weight sums remain normalized. This is an anatomy study, not an adopted or
native-validated new skeleton. Existing corrective targets must be recalibrated
before integration; remaining routine/contact and multi-character acceptance
stay open. The saved originals and the better shoulder baseline are preserved.
All961 frames retain the95 original bone matrices exactly; helper steps remain
below0.312degrees and normalized weight sums within6e-8. Front/back videos and
18 opposing stills were rendered. The first assembly capture was blank because
appended transforms were read before evaluation and already-correct parents were
reassigned; it was rejected. Updating after linking and leaving the new rig's
existing children intact repairs the review scene, not the anatomy.

The owner then circles the remaining left chest-to-arm crease; it is still a
failure. Preserve a soft neck contour and avoid exaggerated trapezius bulk.
Actual saved clavicle, scapula, upper-spine and upper-arm weight maps are retained
for diagnosis. They are not proof that these weights are correct. The new blade
helpers improve one rear fold but do not resolve the front fold. No visual or
whole-motion acceptance is claimed from the numeric parity or rendered video.

The creator's primary comments in the2024
[shoulder-blade rig thread](https://www.reddit.com/r/blender/comments/1apc8db/over_engineerd_shoulder_blade_rig_for_game/)
describe overlapping shoulder/blade/trapezius/arm influences, appropriate bend
topology, driven corrective shapes or an elbow helper with half forearm rotation.
The elbow approach is not automatically a shoulder repair. They export Blender
animations to Unreal and discuss rebuilding equivalent constraints in Control
Rig; the comments do not establish direct transfer of Blender constraints or
provide a complete rig download. Consulted2026-10-25. Treat these as author
implementation ideas, not a prescription to copy male neck/muscle shapes.

Primary references consulted2026-10-25: Epic UE5.8 Modular Control Rigs,
SideFX Houdini22 Scapula component (available since21.0), and Blender Corrective
Smooth API. The transferable idea is coupled shoulder-girdle movement; no
Houdini/ML/plugin installation or vendor rig replacement occurred.

Receipts: `DancerLegCompatibility.json`, `BodyJoinReview`, `VexaShoulderReview`,
`VexaClavicleReview`, `VexaFullShoulderReview`, `VexaShoulderProof`,
`VexaShoulderExportContract.json`, `NativeVexaShoulderProof.json`.

## October25 evening: isolate asymmetry before adding more helpers

Later owner feedback supersedes the tentative helper-study language above:
the expanded neck/trapezius, lifted blades, head contour and persistently worse
left shoulder are rejected. The earlier front view is visibly closer, but is
not full acceptance. Vexa remains the sole target; new GPU work is held while
the owner uses VRAM. No Unreal was launched for this source-only continuation.

The preserved vendor Blender master has95 bones, no rig constraints or drivers,
and no scapula bones. It contains no hidden corrective rig that can simply be
enabled. The supplied shoulder tutorial transcript and intro clip were examined.
Its useful lessons are coordinated bone motion, regional weights and separate
pose tests; its Blender B-Bones/modifiers are not automatically Unreal behavior.
Primary tutorial: [3D Character Creation for Animation - The Shoulder](https://www.youtube.com/watch?v=c_XM01I6ed0),
consulted2026-10-25. No tool installation or production skeleton replacement.

Two controlled findings explain much of the inconsistent result:

- The floating-arm rewrite retained clavicles from the earlier acrobatic clip.
  Rebuilding clavicle motion from chest-relative rest and actual arm elevation
  removes that mismatched input. It changes hand positions and is not a pole
  contact solver. The maximum shoulder-root shift is8.863cm, so fixed contacts
  must be rebuilt rather than reused.
- Original mirrored shoulder skin weights differ materially, even where paired
  rest points are less than1mm apart. In matched bilateral poses, a protected
  right-to-left weight transfer reduces maximum reflected surface mismatch
  from49.39/53.53mm to3.57/3.88mm and P95 from9.3/9.9mm to about1.2mm.
  Geometry and rest bones are unchanged; residual original shape asymmetry
  remains. This measures consistency, not anatomical correctness.

The resulting private95-bone `Vexa_CoordinatedSymmetry_Proof.blend` has961 frames,
maximum clavicle/neck/upper-arm local step0.583degrees,984 modified torso vertices
and132 protected boundary vertices. It retains the earlier leg/hip proof and
original source assembly. Lower-neck rotation is shared while original upper-neck
and head orientations are preserved; maximum head translation is2.27cm.
Fresh reload renders18 opposing views and two16-second motion captures. The
front retains the improvement; the nape notch remains visible and unaccepted.

The body/head join has44 paired vertices with matching weights; it is not a
disconnected head. Clearing custom normals also did not remove the notch.
A CPU geometry audit localizes abrupt weight changes near the posterior seam.
An isolated, seam-aware diffusion changes175 vertices across torso and head,
leaving rest geometry, front weights and distant shoulder weights unchanged.
CPU Cycles before/after views show a reduced nape notch without adding muscle
bulk. Full-motion seam and eight-influence readback are recorded separately
in `VexaNape/BalancedAudit.json`; neither closes artistic/native acceptance.
The961-frame seam check is within0.00122mm. Eight-influence compression exceeded
the0.05mm gate (0.0676mm), so it is rejected and full weights are restored exactly
at241 sampled frames. The saved candidate retains up to10 influences; its native
influence budget remains a follow-up. Current private proof is
`Vexa_ShoulderBalanced_Proof.blend`, SHA256
`844aae5f6ccfe4f25d5e8c8b5e9bd7e8d79e813b5375491b7749576bd2544824`.
Fresh saved-proof verification independently checks all961 frames and44 seam
pairs (maximum0.001206mm),95 bones, unchanged rest geometry and13,959 front-region
weight vectors. Opposing800px CPU stills and a low-resource12fps back preview
were rendered from that saved file. The latter does not prove final frame pacing.

The first manual-clavicle comparison was invalid because its still-active action
overwrote the held pose during rendering. The corrected comparison clears that
action and asserts that rendered bone matrices match the intended pose. Retain
this failure: a successfully rendered file does not prove which pose was rendered.

Private receipts: `VexaNativeMaster`, `VexaShoulderFoundation`,
`VexaGirdleAuthority`, `VexaCoordination`, `VexaSymmetry`,
`VexaCoordinatedSymmetry/Reload`, and `VexaNape`. Original licensed files,
production maps, saves and DLL are not replaced. Remaining work belongs to the
lead: continuous shoulder/neck and garment review, native playback, pole contacts,
knees/thighs, all segments and only then reuse on other dancers.

Final preservation check is partial: all220 protected project files and all65
private imported copies match their original hashes. However, the recorded AFS
project directory no longer exists at its old OneDrive path, so source-original
verification there is unavailable. The guard remains failed rather than being
rebased or silently treating missing files as unchanged. No AFS folder was moved,
recreated or modified in this continuation; the copied inputs remain usable.
