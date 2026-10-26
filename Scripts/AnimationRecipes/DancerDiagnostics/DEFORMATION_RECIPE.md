# F3 deformation repair recipe

## Working procedure and transfer rules — October26

Use this section first; the sections below retain the experiments and evidence.
The current target is Vexa. Finish her rig and routines, then document their
verified results before adapting the technique to Joy, Astra and other dancers.
The owner approved specific shoulder/hip views, not a complete anatomical rig.

1. **Identify the exact failure.** Record character, source hash, clip, frame,
   visible body variant and camera. G1 frame881 (14.6667s) is the October26
   straight raised-arm shoulder regression. A different pose is not a control.
2. **Preserve a visual baseline.** Keep the original licensed source and the
   best accepted derivative. Never overwrite a better result to try a new idea.
   Use one mesh and change one cause at a time; render matching front, back and
   quarter views with the hair hidden equally. Inspect lit colour afterward.
3. **Separate the causes.** First compare rest hierarchy, joint placement,
   local axes, object transforms and animation reference pose. Next isolate
   clavicle/neck authority, then weights, then normals, then local corrections.
   Corrective smoothing cannot repair a backwards elbow or unreachable hand.
4. **Coordinate the shoulder with the actual arm pose.** `coordinated_girdle.py`
   derives each clavicle from the chest-relative rest frame and elevation,
   rather than inheriting an unrelated acrobatic clavicle pose. The evaluated
   recipe uses a smooth zero-to20-degree clavicle lift and shares lower-neck
   rotation between the two neck joints while retaining head orientation.
   These are tested F3 recipe settings, not universal anatomical limits.
5. **Carry that coordination to every clip.** Better Spiral images did not
   establish G/B quality. G1's raw transfer retained flat clavicles, giving the
   arm-from-neck silhouette. The matched coordinated G1 frame881 front was
   explicitly approved. `bake_gb_shoulder_response.py` rewrites only clavicle,
   upper-arm and neck channels (six bones); all other local keys stay exact.
   It moves the hands by up to4.671cm and the head by2.969cm in these clips.
   Solve contact afterward; never reapply an old pole constraint blindly.
6. **Balance weights using identical mirrored poses.** The original F3 left
   shoulder weights differ from the right. `mirror_vexa_shoulder_weights.py`
   mirrors the better side through matched vertices and protected boundaries.
   A head tilt or unequal arm height can still make correct shoulders differ.
   Do not force equal silhouettes in an asymmetric pose.
7. **Keep neck correction local.** `nape_weights.py` diffuses only the small
   posterior weight discontinuity and treats coincident head/body pairs as a
   unit. Broad trapezius/scapula helpers produced rejected neck and back bulk.
   The retained rig has95 original bones; no helper is needed for this result.
8. **Distinguish shading seams from separation.** Audit coincident vertex
   distances in motion. The ankle/wrist pairs stayed attached. Averaging normals
   on separate meshes failed; `build_vexa_continuous_distal.py` copies surfaces,
   stitches only40 wrist and44 ankle pairs and clears split normals. Original
   parts remain hidden. Export only the visible derived surfaces.
9. **Fix demonstrated weight contamination narrowly.** Eight hand vertices had
   pelvis weights. `repair_vexa_hand_contamination.py` removes only that influence
   and renormalizes the existing others; it does not auto-weight the hands.
   Later neutral-finger controls isolate one opposite-hand influence; the exact
   one-vertex repair and preserved controls are documented below. Other finger
   deformation/contact remains open and must be diagnosed independently.
10. **Do not confuse continuity with anatomy.** The wrist limiter flipped across
    quaternion branches, producing near80-degree frame jumps. The derivative
    filters bounded rotation vectors around fast events and keeps non-wrist
    keys exact. Its below5-degree/frame result is a continuity check, not a wrist
    range rule; source fidelity, finger pose and contact still need inspection.
11. **Keep pose corrections tied to their source.** Hip/axilla morph coefficients
    baked for Spiral are time-indexed. Disable them on G/B; do not replay them
    by frame number on another routine. Recompute or build a verified pose-driven
    correction after changing the joints. Blender preserve-volume and smoothing
    must be baked or implemented equivalently for Unreal; modifier presence in
    Blender is not native deformation evidence.
12. **Test more than showcase poses.** Use bilateral wrist flexion/deviation,
    forearm roll, ankle pitch/roll, toe and finger poses; test partially open
    knees as well as deep flexion. Then inspect complete original/retargeted
    clips, transitions, a moving body with fixed grip, reachable grip changes
    and garment contact. Reject snaps, inversion, collapsed volume and clipping.
13. **Check the actual exported result.** The FBX armature object must be
    `root.001`, matching the mesh's extra native root. Preserve all95 original
    bones. The private workbench retains12 influences and skin-cache tangents;
    do not silently prune to8. Verify fresh dependency loads, curve counts,
    bone/surface parity and actual native rendered frames. Seek times must stay
    inside each clip; endpoint clamping caused a retained failed capture.
14. **Transfer a technique, not an unverified file.** Check topology, bone names,
    rest matrices, shapes, weights and garment transforms before copying body
    repairs. The four inspected F3 bodies matched; Joy/Astra are not thereby
    proven compatible. Their repairs need their own source identity and tests.
15. **Record narrowly and retain failures.** Store exact scripts, hashes,
    parameters, before/after frames and rejected alternatives here and in the
    validation record. `docs/KNOWN_ISSUES.md` owns remaining work. A passing
    numeric screen, successful import or owner-approved still does not close
    full-motion, contact, native-game or other-character acceptance.

Preserved sources: balanced shoulder `844aae5f`, local axilla `1f677227`,
continuous distal mesh `d70f17f7`, wrist library `a865e0d9`, separate shoulder
action library `4d72c70e`, one-vertex hand isolation `a9dbcbde`. These remain private derivatives, not production swaps.

RPT-20261021-01, 2026-10-25. **Partial, private review only.**
The owner approved one corrected curled hip silhouette. Open knees, thighs,
the shoulder/underarm, complete motion and in-game adoption are not approved.
**Vexa (saved pink/purple-haired Eden) is the sole active repair target.**
Complete her before propagating changes to the other three dancers.
This recipe records reproducible work and rejected approaches; it is not a
universal repair or a numeric substitute for visual review.

## Preserve and isolate

Use the original licensed character-options Blender files read-only. Hash the
source meshes, skeleton, materials and clips before starting. Outputs belong in
the ignored `SourceAssets/DanceRefinement_20261025` directory; native experiments
belong only in the isolated `WorkbenchNative/CharacterWorkbench` project.
Keep the original mesh topology, UVs, shape options and source motion available.
Run Blender hidden with `--background`; Unreal must use `-RenderOffscreen` for
rendered inspection. Do not replace production assets or the shared skeleton.

## Diagnose before changing weights

1. Freeze the exact failed animation time and inspect both sides of the entire
   hip–thigh–knee–ankle chain. Include intermediate bends and straightening,
   not just the fully curled pose. Use the supplied anatomy reference.
2. Run `review_native_knee_hinge.py`: clear animation in memory, restore the
   native rest pose, and bend only the calf around its verified local axis.
   On this F3 rig, local negative Z gives a normal forward knee bend.
3. Compare that control with the transferred pose. A good native bend and bad
   transferred bend point to bone orientation/roll before topology or weights.
   Joint positions alone do not show which direction the kneecap faces.
4. Reject a change that merely shifts the pinch to the thigh, hip or ankle.
   DQ-only knee deformation, local smoothing and calf-only roll did not solve
   this report. `SS_REVIEW_CALF_ROLL` stays off by default.

## Coupled leg-plane candidate

`leg_plane.py` aligns the thigh's native hinge axis with the plane defined by
hip, knee and ankle, then reconstructs the calf bend. Twist-helper branches
follow their owning segment; the foot branch retains its source transforms.
Near full extension, carry the previous plane forward rather than normalizing
an unstable near-zero cross product. This is F3-specific and must be recalibrated
against a native bend control for another skeleton.

`bake_leg_plane.py` reads the preserved hip proof's original motion and writes
`Roxie_LegPlane_Actions.blend`, without replacing the default nine-clip library.
It evaluates 961 frames and refuses large rotation jumps. The current bake has
zero joint-center drift before reconstruction and a maximum 3.394-degree local
leg step. Four evaluated poses reconstruct within 0.006 mm. These guard against
technical mistakes; they do not certify anatomy, feet, timing or smoothness.

## Rebuild pose-dependent hip correction

Do not reuse corrective curves after changing thigh orientation. Run
`bake_hip_correctives.py` with `SS_REVIEW_LEG_PLANE=1` for the separate candidate.
The default mode is the earlier hip proof. The candidate samples 241 poses,
compares localized preserve-volume and linear skinning, inverse-skins the
difference, compresses it into 24 bases per affected mesh and bakes coefficients.
Retain held-out frame error and inspect the actual result: matching a DQ target
does not prove that target is anatomically correct. Only reuse body corrections
after comparing geometry, topology, weights, rest rig, object transforms and
active shape options. The October25 audit confirms the four local F3 bodies
match, so a verified body repair can transfer; their bottom-garment transforms
differ. Never assume this compatibility for a newly customized or unrelated mesh.

The three affected meshes are legs, torso and bottom. The small exported proof
contains only those parts and the rig; missing head/hands/feet in that isolated
native proof are deliberate. `review_leg_plane_motion.py` assembles the complete
source character in memory for full-body inspection and can render a 16-second
video with `-- --video`. The forearm markers remain removable diagnostic objects.

## Export and verify in Unreal

`export_leg_plane_proof.py` exports separate rest-mesh and animated FBXs. It
removes only sub-micron review bases after measuring their combined error over
all 961 frames. Current candidate: 65 retained bases; seven removed; maximum
combined removal error 0.00195 mm. Vendor shape options remain intact.

Run `import_hip_proof.py` with `SS_REVIEW_LEG_PLANE=1`. Its legacy-FBX switch is
ephemeral to that private process. Explicitly save the generated skeleton, mesh
and animation: task-level save alone previously left a null skeleton on reload.
Compare expected morph/curve names case-insensitively, matching Unreal FName
identity. Preserve import warnings; reconstructed FBX bind poses still require
visual and geometry comparison.

Use a fresh process for `capture_native_hip.py` with the same flag. Reject stale
poses, blank frames, clipped exposure and wrong aspect ratio. The native test
uses neutral normal-based diagnostic shading, not production skin materials.
Inspect open/closed knees from opposing views, then continuous playback and
foot/cloth/hand contact before any adoption. Verify multiple dancers and all
segment boundaries separately. New-library adoption remains disabled.

The current native check contains 12 settled views and the matching 65 curves.
`export_native_leg_proof.py` requires ordinary editor ticks: commandlet export
asserted on MeshObject. Its fresh FBX readback matches 95 bone centers within
0.0108 mm and bidirectional nearest surface vertices within 0.0163 mm at seven
times, after one fixed rigid alignment. This confirms exported data parity;
it does not measure engine GPU skinning or replace continuous visual review.

## Vexa shoulder candidate

`inspect_vexa_shoulder.py` compares the transferred pose and native raised-arm
controls. Correct arm direction does not guarantee acceptable skin deformation.
Clavicle participation and local shoulder volume need separate evaluation.
The current `shoulder_support.py` follows overhead reach with clavicle lift,
translates the arm branch to the new shoulder center, and preserves its world
orientation. This is for free-floating motion only: hands move by up to 4.32 cm,
so fixed pole contact must be solved separately.

`bake_vexa_shoulder.py` reads `Vexa_LegPlane_Proof.blend` and saves the separate
`Vexa_Shoulder_Proof.blend`. It bakes a derivative 961-frame Spiral action and
24 localized shoulder morph bases, retaining the existing hip proof. A three-ring
boundary mask prevents the new correction moving neck/wrist/waist boundaries.
Sampling and eight held-out times approximate the chosen volume target within
0.024 mm; the maximum shoulder local step is 0.437 degrees. These are engineering
checks, not anatomical or owner acceptance. The candidate remains unadopted.

Set `SS_REVIEW_SHOULDER=1` for `export_leg_plane_proof.py`,
`import_hip_proof.py`, `capture_native_hip.py` and `review_leg_plane_motion.py`.
Do not also set `SS_REVIEW_LEG_PLANE`. The full-character review requires
`SS_REVIEW_CHARACTER=Vexa`. Export retains 89 combined review morphs, imports
them into the isolated `VexaShoulderProof_20261025` folder, and preserves vendor
shape options. Whole-body and opposing shoulder views remain mandatory.

The first native close-ups exposed uneven shading despite 89 valid curves.
`SS_REVIEW_RECOMPUTE=1` is a separate, process-only tangent comparison; it does
not change production settings. Inspect its actual images before accepting it.
Epic's [skeletal rendering paths](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-rendering-paths-in-unreal-engine)
and installed `GPUSkinCache.h` describe runtime tangent recomputation for morphs.
Consulted October 25, 2026; version 5.8. Tangent repair cannot certify geometry.

## Native readback does not settle appearance

Compute skin-cache/tangent recomputation and a separate high-precision morph
duplicate did not repair the native close-up. Material skeletal/morph usage
flags were already correct. The attempted runtime CPU-morph toggle is read-only
and stayed enabled: it is **not** a valid CPU-versus-GPU comparison.
`audit_vexa_runtime_pose.py` compares a live Geometry Script CPU-skinned snapshot
at four times: 8,352 vertices agree within 0.118 mm after the fixed coordinate
alignment. That narrows the problem; it does not prove GPU-rendered quality or an
engine defect. Keep this distinction when interpreting an export round trip.

## Left underarm and shoulder-blade study

The owner rejects the left chest-to-arm crease and prefers the other shoulder.
The later smoothing screenshot was only "possibly close." Vexa remains the
single target. Keep her neck contour soft; do not copy exaggerated trapezius
bulk from the male rig reference.

`review_vexa_underarm.py` compares localized Corrective Smooth against the saved
baseline. `bake_vexa_underarm.py` creates a separate 24-basis left-only proof;
the other shoulder and modular boundaries receive no new correction. The chosen
target is approximated within 0.077 mm in sampled poses and 0.056 mm at held-out
times. This does not mean the target is anatomically correct. The owner still
rejects the crease, so this proof is not a final repair.

`build_vexa_girdle_study.py` adds two private scapula helpers under `spine_05`.
Their motion follows the existing clavicle/shoulder relationship; three boundary
rings protect modular joins. `audit_vexa_girdle.py` verifies all 95 original
bone matrices over 961 frames remain unchanged, normalized weights, and helper
continuity. It does not judge the skin. `review_vexa_girdle.py -- --video`
renders front/back motion plus opposing stills. When assembling the full
character, update the dependency graph after linking; do not reparent imported
objects already attached to the correct rig. The earlier blank capture failed
that requirement and was discarded.

`review_vexa_girdle_weights.py` shows the actual saved influence maps without
rescaling their values. Overlapping colors alone are not proof of good weights.
The original clavicle hierarchy was already correct; adding helper bones is an
isolated anatomy study, not a reason to replace the production skeleton.
Existing corrective targets require recalibration if their underlying weights
or rest frames change. Do not stack a new deformation on top of incompatible
correctives and call the extra volume a repair.

The [rig creator's comments](https://www.reddit.com/r/blender/comments/1apc8db/over_engineerd_shoulder_blade_rig_for_game/)
describe overlapping shoulder/blade/trapezius/arm weights, suitable bend topology,
driven shape keys, and an elbow helper copying half the forearm rotation.
The last technique addresses elbows, not automatically shoulders. They export
animation from Blender to Unreal and discuss recreating equivalent constraints
in Control Rig; Blender constraint transfer is not established. Consulted
October 25, 2026; the thread dates to February 2024. Their implementation is a
reference, not a complete downloadable rig or a required muscle shape.

## Coordinated motion and bilateral weights

Later owner feedback rejects the expanded neck, raised blades and head distortion
in the helper-bone experiments. Preserve those as failed controls. The current
candidate uses only the95 original bones. The front view was called much closer,
but this is not acceptance of the back, entire routine or native result.

`review_vexa_girdle_authority.py` isolates the animation contribution. The earlier
floating-arm rewrite retained clavicles from a different acrobatic arm pose.
`coordinated_girdle.py` instead derives clavicles from chest-relative rest and
actual elevation. It shares lower-neck rotation between the neck joints while
preserving upper-neck/head orientations. This displaces the hands: maximum arm
root shift8.863cm. It cannot be reused as fixed-pole contact motion.

Clear an action before holding a manually adjusted pose. The first control was
invalid because rendering reevaluated the original action; corrected captures
assert their bone matrices. Use identical poses and cameras before blaming a
left/right difference on weighting.

`audit_vexa_shoulder_foundation.py` and `review_vexa_symmetry.py` find genuinely
asymmetric original weights. Rest points less than1mm apart can have nearly1.0
L1 difference after side-name remapping. `mirror_vexa_shoulder_weights.py` copies
the better right weights into the left region with spatial and three-ring seam
masks. It changes984 torso vertices, protects132 boundary vertices, leaves the
right weights/rest bones/geometry unchanged, and rejects distant correspondences.
In two mirrored pose controls the worst surface mismatch falls from49.39/53.53mm
to3.57/3.88mm; P95 falls to about1.2mm. Residual rest-shape asymmetry remains.
This establishes consistency, not acceptable anatomy.

`bake_vexa_coordination.py` saves a compact95-bone/961-frame proof. Its shoulder,
neck and upper-arm maximum local step is0.583degrees. Original materials remain
in the licensed source; this private copy uses clay and hidden hair for inspection.
`review_vexa_coordination_saved.py` reloads it for opposing views and motion.

## Local nape correction, without muscle bulk

`audit_vexa_neck_seam.py` verifies44 paired body/head vertices and matching weights.
The visible notch was not a disconnected head. A custom-normal clearing control
also failed to remove it. `audit_vexa_nape.py` locates abrupt posterior weight
changes; `nape_weights.py` diffuses weights only in that small region, treating
each seam pair as one logical vertex. It does not weld, reshape or split meshes.
The front and remote shoulders are outside its mask. The original bone count and
rest geometry stay unchanged.

CPU before/after views show a reduced nape notch. The trial touches175 vertices
(173 exceed the reporting L1 threshold). An eight-influence compression trial
failed its0.05mm error gate at0.0676mm and was rejected; the saved candidate
retains up to10 influences, with exact restoration at241 samples. Do not widen
the gate or silently prune this at export. Verify the native influence budget
and fresh deformed-surface parity before adoption.

`audit_vexa_balanced_proof.py` checks961 seam frames and preserves the full weights
when the compression gate fails. Maximum measured seam discrepancy is0.00122mm.
`Vexa_ShoulderBalanced_Proof.blend` is the current private candidate; it is not a
native game asset. `review_vexa_balanced_cpu.py` uses four CPU threads, Cycles CPU,
opposing800px stills and an optional low-resource12fps back preview. That preview
does not establish final frame pacing or complete artistic acceptance.

The supplied [shoulder tutorial](https://www.youtube.com/watch?v=c_XM01I6ed0)
supports checking topology, joint placement, separate weight regions and one
modifier at a time. Its transcript and owner-supplied intro were reviewed on
October25,2026. Native Blender master inspection finds no existing corrective
rig to switch on. Blender B-Bones, constraints and smoothing modifiers need an
explicit baked or equivalent runtime solution; they do not transfer automatically.

## Preserve the outcome accurately

Keep the approved earlier hip proof separate from the new leg candidate. Record
owner feedback in `docs/KNOWN_ISSUES.md`; the current issue remains open. A build,
import, low numeric error or PR merge cannot close visual/feel acceptance.

## October25 balanced proof native verification

**October25 private native follow-up:** Owner authorizes full VRAM, superseding the CPU hold. Proof844aae5f remains private in CharacterWorkbench at /Game/SpaceSurvival/Licensed/VexaBalancedProof_20261025. All65 correction curves and16s duration reload. Four live28,345-vertex samples differ from Blender by at most0.302mm (bones0.199mm; curve error0.000944). Component-copy weights retain10 influences at35 vertices with more than8; direct GPU-buffer introspection is not claimed. Two16s/24fps native videos contain768 frames total. Largest frame changes were inspected and follow the moving camera. Lit multi-angle review identifies a remaining skin fold at the axilla; hiding the garment confirms it is not just clothing. No production adoption or anatomy/choreography acceptance. Lead retains localized shoulder correction, garments, knees/thighs, pole grips and later multi-dancer reuse. Owner now describes the shoulders as looking very good except one spot; this is narrow positive feedback. Six controlled Blender renders use the existing packed textures with neutral or pink/blue lighting: colour softens the fold but does not hide its highlight. A separate Vexa_AxillaLocal_Proof.blend bakes24 local curves, retaining the844 baseline. Compression error0.00394mm; eight held-time errors max0.02227mm. Its full-motion/garment acceptance remains open. Owner explicitly accepts the shown side as a massive improvement. After questioning the back, owner notes unequal arm/head pose and says the shoulders are generally very close. Preserve this appearance; do not reshape it merely to make an asymmetric pose symmetrical. This does not close full-motion, native-material, pole-contact or other-character acceptance. Owner asks about wrists, ankles and other joints; inspect them through this same routine before broad reuse. Existing knee/thigh and garment/contact failures remain open. The separate1f677227 axilla candidate now fresh-loads in the private native workbench with89 correction curves and16s duration. Five sampled live surfaces match Blender within0.302mm; two384-frame native views are retained at24fps. This closes bounded transfer verification, not continuous artistic acceptance or production adoption. Earlier malformed capture arguments and the dependent missing-report audit failure are retained; corrected captures and parity succeeded. Distal-joint follow-up:961-frame wrist/ankle scan and16 closeups retained. This shoulder-proof clip holds both wrists at their rest-relative orientation, so it does not exercise wrist flexion. A visible right ankle contour/lighting discontinuity remains. Seven samples of44 ankle and40 wrist coincident vertex pairs stay within0.0013mm; the parts are not separating. An in-memory normal-average control changes neither the ankle defect nor the source and is rejected as a fix. Thumb-web spikes in the hand closeups also require inspection. No distal repair or full joint-range acceptance is claimed. Owner explicitly rejects calling this a gold-standard rig: no satisfactory wrist/ankle has yet been seen. The shoulder approval is local only. Required reuse gate: dedicated bilateral wrist flexion/deviation, forearm twist, ankle pitch/roll and foot/toe poses; complete source and retargeted clips on each distinct mesh/rig; torso-relative arm limits during pole-locked motion, including grip changes and body rotation. Unreachable contact must remain rejected or use a feasible body path/release; do not force a pinned hand by breaking the arm chain. Static pose passes, this16s clip and skin parity do not close any of those gates. Dedicated24-case/48-view isolated probes now exist on Vexa, with wrist flexion/deviation, ankle pitch/roll and forearm twist. Representative bent joints expose contour discontinuities and remain rejected; these diagnostic angles are not declared anatomical limits. No proof or production file was changed by the probes. Superseding the missing-source uncertainty: owner identifies AFS on M;58 exact files under M:/UnrealProjects/AFS now match the original source-manifest hashes. Original path manifest and failed historical path guard remain intact. Combined with the seven accessible originals, all65 source contents are accounted for; no AFS writes occurred.

Source SHA256:844aae5f6ccfe4f25d5e8c8b5e9bd7e8d79e813b5375491b7749576bd2544824. Export does not resave it. Seven negligible morphs are pruned from FBX only; maximum combined source error0.00195mm. Curve comparison excludes those pruned names.

Private workbench only: r.GPUSkin.UnlimitedBoneInfluences=True, threshold8, DefaultBoneInfluenceLimit=(Default=12), mesh LOD limit12. Canonical project/engine configuration is unchanged. GeometryScript readback is a component copy, not direct render-buffer inspection.

Native receipts: NativeVexaBalancedRuntimeSkin.json, VexaBalancedRuntimeSkinParity.json, NativeVexaBalancedMotion.json and NativeBalancedVideos.json under .agent/local/AnimationReview_20261025. Native MP4s are SourceAssets/DanceRefinement_20261025/Vexa_ShoulderBalanced_Native_front.mp4 and _back.mp4;384 frames each,24fps,16s. Blender previews are separately named.

The first capture's world-fixed cameras, obscuring hair and absolute-normal dark bands are superseded by body-relative cameras, hair-free diagnostic import and a signed normal ramp. This shading is not final skin/material acceptance. Lit96-sample OptiX views independently inspect geometry. Known FBX bind-pose reconstruction warnings remain; no warning-free import claim. No C++ changed, so a module rebuild was not warranted. Actual station performance, packaged behavior, whole-routine quality and owner acceptance remain open.

Preservation: the old AFS source path is unavailable; do not rebase the guard. All previously retained imported copies remain the protected working sources.

## October26 distal and G/B continuity repair

**October26 distal and wrist-motion repair (supersedes the no-repair note above):** Private Vexa d70f17f7 removes pelvis influence from8 hand vertices and stitches only40 wrist/44 ankle boundary pairs, with source parts retained. Sampled thumb spikes and seam shading improve. The95 original deform/rest bones remain; FBX adds its armature-object root. Seven source comparisons differ by at most0.001437mm; five native surfaces by0.302mm. Native89-curve load,24 distal cases/48 views and4 shoulder preservation captures are retained. The full4566-frame G/B screen uses the same rest rig and disables Spiral-only correction curves. It detects near80-degree wrist jumps introduced by the earlier limiter. Separate action library a865e0d9 repairs wrist continuity: maximum4.932degrees/frame at60fps; all non-wrist local keys preserved, B2 unchanged in motion. This is a numerical continuity gate, not an anatomical bound or source-fidelity acceptance. Native before/after excerpts plus the complete G1 candidate contain789 frames; no pole constraint is active. Remaining fast upper-arm/leg motion, contact/body paths, finger/ankle contours, knees/thighs, garment fit and per-character full-motion acceptance stay AI-owned and OPEN. No production character/map/DLL/package adoption or merge.

- `repair_vexa_hand_contamination.py` changes only eight contaminated hand vertices, removes pelvis influence and renormalizes their remaining weights. All other hand weights are asserted identical. Matched renders expose the before/after thumb web. Original proof1f677227 remains unchanged.
- `build_vexa_continuous_distal.py` copies the torso/hands and legs/feet, joins only the audited84 boundary pairs and clears split custom normals on the new surfaces. All source faces/material slots/UVs are retained; original parts remain hidden. Seven posed comparisons reject shape-animation drift above0.02mm; measured0.001437mm. Export filters hidden originals. Do not apply a broad merge-by-distance to this model.
- Private blend d70f17f7 remains95 bones; native import adds the FBX armature root. All89 retained curves survive import, with28,261 sampled native vertices. Private workbench skin-cache shader compilation/recomputed tangents are enabled; canonical/engine configuration is unchanged. No direct GPU-buffer introspection claim.
- Wider-weight and four-half-angle-helper trials had too little visible benefit and were not promoted. Their private files/reports remain separate; the current mesh has no new deform bones.
- `audit_vexa_gb_reuse.py` checks4566 frames and36 stills. Same-world rest error3.58e-7, same object matrix; no extra retarget. The existing elbow/rear-reach screens flag no frames. They do not establish anatomy or contact. G1/G2/B1 retain other local steps up to25.64degrees/frame after wrist repair; they are not polished motion.
- `repair_gb_wrist_continuity.py` filters bounded wrist rotation vectors only near fast events, avoiding the shortest-quaternion-branch jump at pi. Source cfebfc7e is immutable. All other action key coordinates, interpolation and handles are checked unchanged. The greatest wrist orientation change is47.33degrees; this remains a candidate to compare against source intent. Fresh reload/export repeats the step gate; B2's motion is unchanged.
- `export_gb_wrist_comparison.py` must match the mesh armature object name `root.001`. The first native attempt failed because animation export used `root`, while the mesh expected `root_001`. That failed log is retained; renaming the export-only object fixes the extra-root identity without renaming any deform bone. Eight native animations then import with matched durations.
- `capture_gb_wrist_comparison.py`/encoder retain four matched1.6s before/after event pairs at30fps plus complete G1 at24fps. Diagnostic camera/shading and offscreen seeks are not natural-play/skin-material/performance evidence. Maximum seek discrepancy is0.000000890s. The excerpts are not loopable dance segments.

Receipts under `.agent/local/AnimationReview_20261025`: `VexaDistalRepair/HandRepair.json`, `ContinuousSurface.json`, `GBReuse/Report.json`, `GBRotationSteps.json`, `GBWristContinuity.json`, `GBWristExport.json`, `NativeGBWristVideos.json`; native `NativeVexaContinuousDistalFullRange.json`, `VexaContinuousDistalRuntimeSkinParity.json`, `NativeVexaContinuousShoulderCapture.json`, `NativeGBWristComparison.json`. Private editable sources/FBXs/videos remain under `SourceAssets/DanceRefinement_20261025`; no licensed/native payload is committed.

No C++ changed; no module rebuild or package was warranted. Source/Python/documentation checks accompany publication. Whole choreography, contact and owner acceptance remain RPT-20261021-01, with no blocking owner checkpoint.

Fresh-process follow-up reloads all eight native comparison animations with their expected skeleton and duration. The first comparison capture extended a late G1 excerpt past the clip endpoint; the encoder rejected its0.2s seek discrepancy. The retained EndpointClamp receipt is not passing timing evidence. Corrected capture windows produce789 frames with maximum0.000000891s seek error; all nine encoded videos decode to their exact expected frame counts without decode errors. Existing FFmpeg PNG chunk warnings remain in the encoding log. Matched native wrist frames visibly remove the abrupt snap, but finger distortion remains visible.220 protected project files,65 imported copies and all65 original source contents (58 relocated AFS files) still match their hashes.50 source structural checks, Python compileall,26 mesh/17 WAV format checks, both documentation gates and scoped whitespace checks pass.

## October26 approved shoulder response carried to G/B

**October26 G/B shoulder response:** Owner rejected G1 frame881 (14.667s) for an arm-from-neck silhouette, then explicitly approved the matched coordinated front. Earlier Spiral acceptance had not established G/B quality. Separate private action library4d72c70e applies the existing chest-relative clavicle/neck recipe to4566 G/B frames, changing only six local bone channels and retaining all other keys. Maximum sampled matrix reconstruction error4.18e-7; wrist continuity remains below5degrees/frame. Maximum hand-path shift4.671cm means pole contact must be solved again. Four native clips fresh-load;822 captures include two405-frame G1 shoulder-oriented views and12 stills. Both videos decode exactly; maximum seek error0.000000636s. Native front/back samples retain the improved shoulder response. Other rapid motion (up to25.65degrees/frame), fingers, knee/thigh shape, garments, transitions, reachable grips and full-body/multi-character quality remain OPEN. Original mesh, earlier accepted proofs and production assets are unchanged. Owner authorizes continued autonomous work: Vexa first, document the complete process, then Joy/Astra, then remaining dancers. No new owner checkpoint, ClickUp write, schedule or merge.

Source: `GB_ShoulderResponse_ActionLibrary.blend`, SHA256 `4d72c70e5410b55847c81943c4ab7c6a3e4d2baa5b151611673dbec6216f4679`. Its source wrist library `a865e0d9` and current mesh `d70f17f7` remain unchanged. `review_gb_shoulder_response.py` isolates the cause at identical poses/cameras. `bake_gb_shoulder_response.py` rewrites clavicle_l/r, upperarm_l/r and neck_01/02 only. The shoulder action keeps the arm world orientations; its attachment positions move. This is not fixed-contact choreography.

The source recipe now begins with a fifteen-step practical procedure, tested settings, retained failures, export pitfalls, transfer requirements and exact baseline hashes. Do not restart helper-bone/neck-bulk trials or replay Spiral-specific morph coefficients on G/B. Do not transfer weights to Joy/Astra by vertex index without proving compatibility.

Receipts: `GBShoulderResponse/Report.json`, `BakeReport.json`, `Export.json`, `NativeReload.json`, `Videos.json`, `NativeSamples.png`, and `NativeGBShoulderResponse.json`, under the ignored animation review directory. Native assets remain in the private `VexaContinuousDistalProof_20261025` package folder. Captures use diagnostic shading and shoulder-oriented cameras; cropped hands/feet and unsampled transitions are not full-body quality evidence. Known PNG encoding warnings are retained; full video decoding passed. No C++ changes, rebuild, package, production adoption or whole-routine acceptance.

## October26 opposite-hand weight contamination

**October26 hand spike isolation:** One left-ring-finger vertex4472 retained4.4068% right-index influence. The spike remains with neutral fingers, isolating weights from animation. Private Vexa a9dbcbde removes only that opposite-hand influence and renormalizes the existing three;6265 other joined-surface vertex weights remain exact. Matched sixteen native controls show the spike removed. Two whole native surface comparisons contain28261 vertices each: only one vertex differs, with all28260 others exactly equal. Fresh reload retains248 morphs, the same skeleton, four unchanged shoulder clips and an explicit12-influence LOD build setting. Existing proof files remain hash-identical. Hand overlap, abrupt source rotations and pole contact remain OPEN; this is not complete hand/anatomy acceptance or a production swap.

The preserved input is `Vexa_ContinuousDistal_Proof.blend` (`d70f17f7`). The output is `Vexa_HandIsolation_Proof.blend`, SHA256 `a9dbcbde4743c2eed97b92c1ab18157d8b903a620206e17cd325031a0e976e6e`. Native destination: `/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026/SK_VexaHandIsolationProof` in the private workbench. `probe_gb_finger_shape.py` compares animated and neutral fingers; `audit_gb_hand_spikes.py` identifies the stretched edge. `repair_vexa_cross_hand_weights.py` requires dominant owning-hand weights and independent rest-space proximity, changes one demonstrated point and checks every other vertex. Do not broadly remove cross-body weights without these controls.

At G1 frame881, the affected edge changes from7.72014x rest length to below the post-repair worst hand-region edge of1.9988x. This is a spike diagnostic, not an anatomical threshold. G1 frame220 still contains hand/forearm overlap; the recipe does not hide or solve it. Native skinned-component copies at8s and12.2s preserve all other surface positions exactly; this is GeometryScript component geometry, not direct GPU-buffer readback.

The first reload gate inspected initialization data instead of effective LOD build settings, then two attempts to reflect renderer settings failed. Those receipts are retained. Installed UE5.8 `SkeletalMeshEditorSubsystem.get_lod_build_settings` is the correct readback. A limit of0 means the project default (12 in this workbench), not pruning; the private mesh now explicitly saves12 using `set_lod_build_settings`, and a fresh process verifies it. Never lower the validated influence budget merely to satisfy a generic limit. See [Epic skeletal-mesh rendering documentation](https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-rendering-paths-in-unreal-engine?lang=en-US), accessed October26.

`audit_raw_gb_rotations.py` reads original GLB quaternion keys before retargeting. It finds rapid arm rotations in the supplied files as well: G1 right forearm about2352degrees/s at2.433s and G2 right arm about2259degrees/s at1.4s. This identifies source motion requiring visual repair; it does not judge the separate generation video or excuse native defects. Keep motion repair separate from mesh weights.

Receipts: `GBFingerShape/Repair.json`, `After/EdgeAudit.json`, `NativeReload.json`, `InfluenceSetting.json`, `NativeSkinDelta.json`, `RawRotationAudit.json`, `NativeVexaHandIsolation.json`, `NativeVexaHandIsolationSkin.json`. Initial rejected reload/reflection receipts remain alongside them. All are private under the established animation-review directory. No C++ changes, new game build/package, production-map edit, merge or owner acceptance.

## October26 bounded arm passage repair

The skinning repair cannot remove a bad joint trajectory. Original GLB rotation
audits plus identical-rest-pose controls show the rapid rotations predate the
latest retarget. A threshold above10 degrees per60fps frame only nominates views;
it does not authorize flattening every fast gesture. Nineteen intervals were
screened; opposing start/peak/end views identify specific local loops to change.

| Change | Preserved input | Output hash prefix | Frames | Worst upper-arm step after | Max hand-path change |
|---|---|---|---|---|---|
| G2 right downward loop | 4d72c70e | ac64f038 | 59-109 | 5.658 deg/frame | 54.274 cm |
| G2 left downward loop | ac64f038 | fa3967d2 | 787-830 | 7.863 deg/frame | 55.848 cm |
| G1 left behind-torso loop | fa3967d2 | 0a38e12a | 192-270 | 1.970 deg/frame | 54.440 cm |

Each trial copies the action and replaces only interior arm-chain rotations
with a smooth endpoint quaternion path and an eight-frame smoothstep taper.
The existing chest-relative clavicle coordination is recalculated; the neck
pass is not applied twice. Untouched curves retain all key metadata exactly.
Exterior coordinates/interpolation on touched LINEAR curves remain exact;
Blender may recompute unused Bezier handles by floating-point roundoff. The
initial over-strict handle assertion is retained, not hidden. Maximum sampled
matrix reconstruction error is2.862e-6. Finger/wrist local keys are unchanged;
the earlier wrist continuity stays below5 degrees/frame. These numbers do not
prove anatomy, contact, source-video fidelity or artistic quality.

The final local library is `GB_SelectedPassages_ActionLibrary.blend`, SHA256
`0a38e12a774436fd08a44508f32820573cdc0dab4a56658737ecc1b7d4060b8e`.
It retains the earlier actions; selected exports use `A_F3_SelectedPassages_g1`
and `A_F3_TwoPassages_g2`. Do not apply the retained Spiral-only morph curves to
these clips. Matching source/native views show the edited limbs in front of the
torso and the approved raised-arm pose retained. Remaining quick movements,
wrists/ankles, garments and reach/contact require continuous scrutiny.

Private native assets are `A_SelectedPassages_g1_selected` and
`A_SelectedPassages_g2_selected` under
`/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026`. Four complete
24fps captures contain405/405 G1 and338/338 G2 frames. All four videos decode to
the expected count; maximum pose-seek error is0.000000636s. Initial PNG chunk
warnings are retained; decoded video verification succeeds. A fresh NullRHI
process loads the same skeleton and durations16.85/14.05s. Earlier proof files
are hash-identical. Native captures use diagnostic shading and a body-following
camera; this is not final skin, fixed-camera choreography, gameplay or package
acceptance. No production assets/map/DLL/save were replaced.

Reproduction: `repair_g2_arm_excursion.py`, `repair_g2_late_excursion.py`, then
`repair_g1_left_excursion.py` require the exact previous hashes and refuse an
existing destination. Review with the matching passage scripts before export.
Then `export_gb_selected_passages.py`, `capture_gb_selected_passages.py`,
`encode_gb_selected_passages.py` and `reload_gb_selected_passages.py` provide the
separate native checks. Never move an old pinned hand onto these new paths.
Use feasible body travel or a deliberate release/regrip when contact is added.

Private receipts: `GBFastPassage/{Repair,LateRepair,G1Repair,SelectedExport,
SelectedVideos,SelectedReload}.json`, `GBArmEventViews/Report.json`,
`NativeGBSelectedPassages.json`. Earlier trials remain separate. PR96 remains
draft/unmerged; hand-repair head1cae454f source409 and documentation597/598 passed.
No C++ changes or module rebuild were needed. Whole-routine and other-character
acceptance remain in RPT-20261021-01.

## October26 one mesh, five paired zero-G segments

Preserve `Vexa_HandIsolation_Proof.blend` (`a9dbcbde`) and the original
`Refined_ActionLibrary.blend` (`cfebfc7e`). The new private joint library is
`ZeroG_Coordinated_ActionLibrary.blend`, SHA256
`fc2df16b48e1ef4c6ec6775c4744abc90da26f0fdca4d35b04283d21a339f357`.
It contains Drift16s, Spiral16s, Butterfly14s, Inversion16s and LateralArc14s.
The12 changed local bones are both clavicles, upper arms, neck joints and
thigh/calf/foot chains. All unrelated keys are exact,95 bones retained and
all sampled hip/knee/ankle centres remain unchanged. Parent-relative
`matrix_basis` reconstruction is required: sequential world-matrix assignment
in a live hierarchy produced an exploded rejected preview. The correct bake
checks all4565 frames; maximum matrix error is2.265e-6.

All25 ordered endpoint pairs have positional mismatch below0.061mm,
orientation agreement within the quaternion comparison's precision and
maximum velocity mismatch0.003765m/s. This checks joins, not artistic quality.
Two higher thigh-roll passages were inspected separately. Do not smooth an
intentional leg-crossing simply because its angular velocity is larger.

### Rebuild correction curves after the joint changes

1. Clear old time-indexed REVIEW coefficients on the private copy. The retained
   old Spiral curves cannot be retimed onto five different joint trajectories.
2. Evaluate linear skinning and the localized preserve-volume target at the
   actual pose. The hip mask uses distance to the nearest rest thigh joint:
   `smoothstep(clamp((0.42-distance)/0.22,0,1))`, metres. This is the tested F3
   target, not an anatomy rule. Inverse skin only where the active determinant
   remains above0.01; reject singular transforms instead of inflating deltas.
3. Build one shared PCA basis across the five clips, not five incompatible
   meshes. The private source has168 new bases:48 Bottom,16 joined torso/hands,
   96 joined legs/feet and8 Top. Part names describe combined objects; do not
   mistake the joined hand object for hands alone.
4. Test interpolation in the final posed surface. Four-frame coefficient
   sampling initially missed1.803mm between keys. Its10.62mm rest-space error
   was amplified by inverse skinning and was not a10.62mm visible defect.
   Keep the rejected draft and measure in the space the player sees.
5. Refine only intervals whose midpoint posed error exceeds0.2mm (four levels
   maximum), then check independent quarter-interval samples. Drift uses344
   coefficient samples, Spiral278, Butterfly229, Inversion241, LateralArc211.
   All2596 held-out samples stay within0.164mm. Basis vectors do not change.
6. Pin all five joint actions with fake users and store the explicit
   `zero_g_curve_pairs` scene mapping. A fresh reload previously dropped unused
   actions. Assign BOTH the rig action/slot and every corresponding shape-key
   action/slot when switching clips. A rig-only action switch is invalid.

The saved shared source is `Vexa_ZeroG_SharedHip_Proof.blend`, SHA256
`455c499224fb39bbd6de41ee3c98bf5fac69916a1b3cceb710e17888acd326b8`.
Export only visible derived surfaces, object root `root.001`, all95 original
bones and120fps sampled curves. Eight negligible Top bases are pruned only in
the export with a combined displacement bound below0.01mm. Import160 morphs
and160 matching curves into each native clip. Duplicate the proof skeleton
into the new namespace first so its added curve names cannot mutate the older
proof skeleton. `AnimSequence.get_editor_property('skeleton')` is required;
the initial direct-property error and guarded exact-namespace resume remain
recorded. The old-proof hash guard covers the resume and later finalization;
the interrupted first import did not persist its guard receipt.

### Knee-band controls: source and native comparison

**October26 matched-camera correction:** The same normal ramp and camera reproduce the knee band in Blender. Static native snapshots with newly calculated smooth normals also retain it. This supersedes the earlier inference of an Unreal-only normal fault; neither explicit-white masking nor duplicate-vertex/cache controls fixed the appearance. The preserved source455c4992 is unchanged. Inspect the source knee contour, weights and intermediate bends next. These controls do not certify anatomy or final materials.

The new assets live only in the private CharacterWorkbench under
`/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026`:
`SK_VexaZeroGShared`, `SKEL_VexaZeroGProof`, and `A_ZG_01_Drift` through
`A_ZG_05_LateralArc`. Five complete posed-surface comparisons contain28261
vertices each, maximum bidirectional position difference0.276mm;27 sampled
bone poses differ by at most0.192mm using one fixed coordinate conversion.
This establishes bounded transfer, not topology equivalence or full motion.

The native normal ramp initially showed harsh bands around the hips and knee.
Enabling global recompute, explicitly opting the component into skin cache,
enabling the section, and changing VertexNormalWS to PixelNormalWS did not
remove them. A derivative-of-world-position control removed the bands while
showing the underlying triangles. That initially suggested a shading-only
fault, but the matched-camera control below supersedes the native-only
inference. The installed cache summary confirmed the mesh participating;
Nanite was false. A flat-normal control alone cannot certify good geometry.

The first green-mask control looked better, but this did NOT establish a fix.
Both component and source-asset colour copies returned black green, and a
rendered VertexColor.G control independently confirmed black. The installed
shader blends toward the recomputed tangent with that channel: black selects
the original tangent. Preserve both aborted0-frame capture receipts; do not
call these colour-copy failures or claim that the source colours are white.
Normalizing the diagnostic shader alone also did not remove the bands.

A separate mesh-only import, `SK_VexaZeroGWhiteMask`, explicitly overrides
vertex colours to white (green range0.99999988..1) and retains the same source,
160 morphs, skeleton and12 influences. It has SHA256
`5c5bdbbb625837b30382c98ee65792a4e7ae953a5f75d3e56b066cfc1bc36528`.
Its saved section0 enables recomputation with green mask1. Identical views
still show bands, including when the console settings are enabled before
component registration. This is an UNRESOLVED normal-path comparison, not an
engine fix. The older black-mask experiment `b83de5a2` is retained separately.
Fresh full-motion capture uses the explicit-white control and
`r.SkinCache.RecomputeTangents=2`, checking saved flags, colours,160 curves and
12 influences. Its footage is useful for movement but is not accepted shading.
Production settings and older proof assets are unchanged.

Epic's [render-path documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-rendering-paths-in-unreal-engine)
describes masked recomputation. [UE-305999](https://issues.unrealengine.com/issue/UE-305999)
documents a no-mask regression, resolved August29,2025 with target5.7. Both
were consulted October26,2026. This installed5.8 comparison does not prove the
same upstream bug regressed, and the tested mask is not a verified fix. The
documented old memory-limit CVar is absent here; do not interpret its failed
lookup as zero memory. Installed headers/shaders and live readback govern.

### Reproduction and remaining review

Run joint review/bake, shared hip bake, adaptive refinement, fresh source
controls, export and isolated native import in that order. The normal controls
and saved black-mask settings are retained experiments, not a recommended fix.
Run `import_zero_g_white_mask.py` before the current full-motion control.
Then `capture_zero_g_full_motion.py` fresh-loads the
proof and renders all five clips from front, back and a fixed stage camera.
The5472 frames produce15 videos whose decoded frame counts agree. This checks
capture integrity and provides continuous evidence; it is not owner visual
approval, playable input, packaged performance or an anatomical guarantee.
Inspect partially open knees, wrists/ankles, rear shoulder motion and garments
through the complete paths. Pole grip must be solved after final body motion;
the previously rejected V8 constraint and old contact paths remain invalid.
The separate60fps visible-surface scan covers all4565 samples. With unchanged
duet offsets of +/-1.70m and base height10.80m, the3.48m-radius chamber has
at least0.5987m glass clearance,0.5276m central-pole clearance and1.1605m
separation between conservative X slabs across any sampled clip ordering.
The lowest floor/ceiling margins are2.6235m/2.9483m. These bounds cover the
five visible proof objects, not future hair, physics, other meshes, unsampled
interpolation or production placement. The chamber itself was not modified.

The distal scan nominates Butterfly left foot frame474 (91.283degrees from
the imported rest basis); ten opposing source closeups inspect that passage.
Quaternion magnitude alone is not an anatomical verdict. The five clips have
neutral local wrists, so they cannot serve as a wrist-range acceptance suite.
The previous bilateral distal stress cases and real G/B contacts remain
required. Keep Vexa first; do not infer Joy/Astra compatibility from F3 results.

Private receipts are `ZeroGJointBake/Report.json` and `ZeroGSharedHip/`:
`Report`, `PosedHoldouts`, `AdaptiveCurves`, `Export`, `NativeImport`,
`NativeParity`, `NativeControls`, `NativeRecomputedControls`,
`NativeExplicitSkin`, `NativePixelNormals`, `NativeGeometricNormals`,
`NativeMaskedTangents`, `SavedTangents`, `NativeNormalized`, `NativeVertexGreen`,
`WhiteMaskImport`, `NativeWhiteMask`, `NativeCacheStartup`, `FullMotion`, `Videos`,
`FullSurfaceEnvelope` and `AnklePeak/Report`
JSON files. The first white-mask wrapper had a nested-string syntax error;
its log remains, and the corrected retry captures six frames successfully.
Original native sources, approved proof blends, production map/DLL/saves and
Joy/Astra remain unchanged. Full Vexa/contact/artistic approval remains open
before any repair is transferred. PR96 stays draft/unmerged; b9cdff07 source410
and documentation599/600 passed. No C++ changed or module rebuild was needed.

## October26 contact and source-control findings

The approved shoulder copies remain unchanged. Vexa is still the sole repair
target; none of these experiments is a production swap or a complete rig pass.

### Knee and material controls

Matched-camera Blender normal ramps reproduce the knee band, and newly
recomputed static Unreal normals retain it. This supersedes the earlier
Unreal-only-normal inference. The next work belongs on source contour/weights,
not another skin-cache toggle. After the verified leg-plane correction, a
local half-bend helper makes a visible knot and is rejected. A knee-only DQ
control changes little at43degrees and adds bulk in deep flexion. A bound
Corrective Smooth mask (radius0.14m, fade0.09m, factor0.5, ten length-weighted
iterations, pinned boundary) moves at most3.812/8.462/7.594mm in three poses,
with zero change outside the mask, but does not remove the objectionable crease.
Do not promote these controls as fixes.

Rest-triangle matching restores53904 original material assignments on a
separate assembly without changing UVs or geometry. Unlit albedo shows that
most of the apparent torso/leg colour difference was lighting and contour.
Across48 waist pairs, the largest mean channel difference is about0.014;
the largest sampled channel difference is about0.029 in linear RGB. Top and
bottom skin material slots have zero faces, so there is no duplicate body
inside those garments. No skin recolour was applied. The first material
render's front/rear labels were reversed by the camera cross-product order;
use the corrected albedo control for direction, not the old filename alone.

### Unoccluded wrists and ankles

`review_distal_unoccluded.py` extracts the same evaluated surface and cuts it
only at the proximal forearm/calf for a clear diagnostic view. Twenty cases
and40 opposing views cover bilateral wrist flexion/deviation and ankle
pitch/roll. These are controlled ranges, not a universal anatomical standard.
The repaired wrist is clearer than the old occluded shot; the ankle still has
an angular heel/Achilles profile in dorsiflexion. Neither is owner-approved.
The rig object has0.01 scale: normalize camera direction vectors before adding
the camera distance. Earlier cameras accidentally sat inside the limb. Use
explicit parent-relative matrix_basis assignment and verify the resulting
pose; direct world-matrix assignment silently produced stale test poses.

### Supported pole grip: useful local fit, rejected whole-clip constraint

The controlled experiment fixes the right hand through one rigid whole-body
transform, preserving all arm local transforms. It does not use the rejected
V8 arm IK, but it intentionally changes the original root trajectory. The
target hand matrix must retain the rest scale0.01; a unit-scale target made an
invalid100x character. Finger flexion uses the verified inward sign; the first
sign bent fingers away from the pole. Both failed controls remain recorded.

`fit_supported_finger_contact.py` fits four three-joint curls against a50mm
diameter pole using actual weighted mesh vertices. The local CPU evaluator
matches Blender within0.00349mm. The retained static settings give pad gaps
of0.19–0.34mm without vertex penetration. `fit_supported_thumb_contact.py`
adds16degrees of base opposition and0/50/52degrees of the tested thumb flexion
channels, with about0.296mm pad gap. These are source-specific fitted controls,
not human range limits or transferable raw angles. The saved Fit.json contains
exact local matrices and the hand target for reproduction. Opposing and top
views show contact, but thumb/index self-contact still requires review.

Triangle radial tests, not only vertices, give a minimum pole gap near0.016mm
for this static grip. Skinning parity does not certify the hand's shape.
The whole G1/G2 fixed-support experiment is REJECTED: maximum pelvis speeds
are10.06/6.55m/s and angular speeds1253/1150degrees/s;32/26 of the six-frame
surface samples contain body/pole intersections. Preserving the arm pose
alone cannot make a support trajectory safe or artistic.

A separate slowed G1 passage (source frames780–1000 at20percent speed) has441
samples and two opposing640px videos. Evaluated surface parity is within
0.00525mm. Importantly, its denser half-source-frame scan catches eight free
hand/pole intersection samples at944–947.5, missed by the coarse scan. It is
still a failed contact candidate, not a finished sequence. Keep exact contact
windows, route the free hand, and use intentional release/regrip passages;
never force the shoulder or wrist through a constraint to hide these failures.
The existing five free-floating segments are separate from this pole study.

Private receipts: ZeroGSharedHip/KneeSourceControl, AlignedKneeTargets,
AlignedKneeSmoothing, MaterialReview, VexaDistalRepair/UnoccludedFinal,
GBSupportedFingerFit2, GBSupportedThumbFit, GBSupportedMotionAudit and
GBSupportedPassage beneath .agent/local/AnimationReview_20261025. Inputs remain
hash-identical. Joy/Astra and the other dancers remain after Vexa, not silently
marked complete. No game/map/DLL/save changes or Unreal invocation occurred
in this follow-up; the prior native proof remains available and unchanged.

## October26 explicit pole release and labelled knee controls

### Retained working candidate, not a complete routine

The action-only `GB_SupportedRelease_ActionLibrary.blend` (SHA256
49f8765479a611da20536ca2576879ab845cc9ba16558d5912866e3a8dd72cc2)
uses the unchanged a9dbcbde hand mesh and 0a38e12a selected-passage library.
It covers G1 source780–1000 at20percent playback:1101 frames,60fps,18.333s.
The static50mm-pole finger/thumb fit is retained while the body follows one
rigid support frame. At source920–940, quintic easing opens the fingers,
translates the body40cm away and releases the moving hand-frame constraint
into its fixed source920 frame. Later movement resumes the original local
arm poses. No arm IK is forced to hold a hand through the obstructed crossing.

Interpolate local rotations and rebuild hierarchical FK. Independently
interpolating world joint matrices can shorten the limb between source keys.
Bake quaternion keys with continuous signs and LINEAR interpolation, then
fresh-reload the saved action rather than evaluating only the authoring scene.
The candidate contains one action, not another duplicate body/texture file.

`review_supported_release.py` performs1101 triangle-radius pole checks:
zero intersection samples at0.01mm tolerance, minimum gap about0.015mm.
That tiny static contact margin is not a robust production collision allowance.
`render_supported_release.py` exposes the release fingers from opposite sides.
`bake_supported_release_candidate.py` requires the recorded source hashes and
zero collision samples; it refuses to overwrite the action candidate.
`verify_supported_release_reload.py` fresh-reloads95 bones at nine poses,
with maximum matrix-element discrepancy0.00000453.

Private native prefix: `/Game/SpaceSurvival/Licensed/VexaPoleReleaseProof_20261026`.
`capture_supported_release_native.py` imports only animation against the
preserved skeleton and creates `L_G1SupportedRelease_Review`; it does not open
or save the production station. Native95-bone comparisons over nine poses
agree within0.103mm using one fixed basis, explicit actor-origin subtraction
and no per-frame fit. A fresh NullRHI reload verifies map, mesh, skeleton and
18.333s clip dependencies. Grey materials isolate motion; existing XANDRA
UDIM/virtual-texturing warnings mean this is not a skin-material validation.

The first882-frame native capture clipped feet in some views. Retain it as
failed framing, not full-body visual proof. `capture_supported_release_wide.py`
loads the saved review without saving assets and increases camera distance
40percent at800px. The corrected882-frame capture completes with no errors,
old-proof hashes unchanged and sampled filmstrips fully framed. Both opposing
441-frame videos decode successfully. The first recapture attempt failed on a
missing report variable before playback; that failed log is retained.
Initial PNG/MP4 inspection found all882 PNG inputs valid and both441-frame
videos decodable despite an encoder PNG warning; that does not cure framing.

This is a supported turn and deliberate release, not loop closure, a full
G1/G2 repair, chamber integration or complete anatomical/artistic acceptance.
The five free-floating segments remain separate. Vexa stays first; only after
her reusable repair is ready do Joy/Astra and other dancers receive adaptation.

### Rejected routes: collision clearance alone is insufficient

A Cartesian free-arm detour clears the pole but creates120.46degrees of
off-axis elbow rotation in this rig's diagnostic coordinates, versus31.20
in the source. Its coupled roll/hinge retry still reaches108.21degrees.
Both are rejected; do not copy these solvers as successful repairs.
A local-keypose blend preserves the source elbow range, but its return path
has nine pole collision samples with up to25mm penetration. Also rejected.
The earlier sinusoidal waypoint bump has three collisions and was superseded
by the explicitly rejected Cartesian trial, not accepted. Joint continuity,
orientation, body clearance and visible deformation must be reviewed together.
The explicit release avoids this failure without changing local arm motion.

### Knee camera/topology controls, no mesh change adopted

The earlier bend-plane camera called front actually faced the inside/back
of the knee. `review_knee_anatomical_views.py` derives the anterior direction
from the rest foot-to-ball vector transported with the thigh; all six tested
poses give inside-dot-anterior near-0.9997. Its24 labelled bilateral views
separate the patella silhouette from the posterior flexion crease. Do not
mistake a view label or natural posterior fold for an anterior knee defect.

`audit_knee_topology.py` finds no0.01mm coincident vertex pairs, boundary or
nonmanifold edges among731 near-knee vertices/1564 triangles. The knee is not
a disconnected seam. Deep Spiral and Butterfly poses each compress12
triangles below10percent rest area; source contour still deserves review.
Longitudinal thigh/calf redistribution and posterior-only DQ controls show
little useful improvement and remain unadopted. The latter moves at most
7.8mm while leaving the anterior mask untouched; displacement is not quality.

Private receipts: GBSupportedRelease, NativeSupportedRelease,
NativeSupportedReleaseWide, GBSupportedPassageRouted2, GBSupportedPassageHinge,
GBSupportedPassageKeypose, and ZeroGSharedHip/{KneeTopology,
KneeAnatomicalViews,PosteriorKneeVolume}. Originals and accepted derivatives
remain hash-identical. No production mesh/map/DLL/save or package adoption.

### Continuous arm screen and heel control

The saved support/release yields2202 bilateral arm samples with no reversed
elbows or owner chest-relative rear-reach flags; maximum rear reach9.785degrees
is within its overhead allowance. The five shared zero-G segments yield9130
bilateral samples without those two flags. These screens do not certify palm
orientation, self-contact, wrists, ankles or artistic quality.

The heel has52/58 lower posterior vertices already weighted rigidly to the
respective foot. A212-vertex posterior influence transition changes the
Achilles contour without fixing the pointed heel appearance; preserve-volume
control also does not repair it. Both remain unadopted. Source shape and camera
orientation must be distinguished from weight collapse before further edits.
Receipts: GBSupportedRelease/ArmScreen.json, ZeroGSharedHip/ArmRangeScreen.json,
AnkleWeights.json and VexaDistalRepair/HeelWeightControl. No saved mesh change.
