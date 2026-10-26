# F3 deformation repair recipe

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
