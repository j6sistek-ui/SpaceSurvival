# Dancer source return and parallel service-motion audit

2026-10-26. RPT-20261021-01 and RPT-20261015-01 remain open. These are isolated
authoring/diagnostic results, not production changes or whole-routine acceptance.
Owner explicitly authorized Joy/Astra evaluation in parallel; Vexa remains the
main implementation. Concept side work is paused.

## Owner direction and preserved scope

The owner reviewed the82-second edit and says the approach looks like spacecraft
docking: fixed, slow sliding in the release/return. The requested contact phrase
is a fluid reach, grasp, pull-in and legs rising with continuous momentum and
faster contact. Free flight is where slower detailed
flips, twists and coordinated limbs belong. A shorter video edit alone does not
satisfy this. Current experiments have not replaced the complete review video.
Do not remove choreography to conceal deformation/contact failures.

The later owner recording narrows the immediate repair target. Its first1–6s
are accepted G1 departure motion, approximately22.08–27.08s in the complete
review; preserve that departure. The near-flip cancellation at recording7s is
approximately28.08s in the added bridge. The doll-like motion at recording8–20s
is approximately29.08–41.08s: bridge, G2 approach and early support. Repair that
connected phrase next. It is **not** the G2 final-return47–51.167s diagnostic
described below, which does not fix the recording or replace the complete video.

This correspondence is an approximate +21.08s offset (about0.1s uncertainty)
inferred from CPU image matching, not native timeline telemetry. It supersedes
the preliminary +21.29s estimate: ffmpeg's `fps=2` nearest-frame selection added
about0.23s bias, corrected by selecting exact recording frames0,15,30,... .
The added bridge starts around recording6.44s; the G2 camera cut is around10.48s
and approach ends around17.17s. The private
`G2FloatingLife/ContactPhrasePlanning/RecordingImageMatches.json`
(`d9184830ae694e5c8015230fab439bebb5b37ec98e65f4abd1cd07738c2ff6e4`)
compares48 recording samples at2Hz with1986 review frames at24Hz using cropped
luminance signatures. Repeated poses produce alternate matches, particularly
recording10.5–16.5s; do not present the offset as frame-exact throughout. Source
video SHA256 is `aad072adbe63fa501139e17dbf27db1e3e0490128e6c29bf48ea45cc41a92d9b`;
owner recording SHA256 is
`6ddd9148e9a40a353cd4a2929da5567e3e9a66c78b24a03e939b66b1b1ded3fc`.

Ten final concept sheets with60 numbered beats and notes were copied and
SHA-verified in `C:/Users/j6sis/OneDrive/Pictures/SpaceSurvival_Animation_Concepts_2026-10-26`.
The owner will propose combinations later. No new concept rigging/animation;
the local gallery builder remains an unpublished draft.

## Vexa: narrow hand-path improvement, hips still unresolved

Inputs remain shoulder51c25e24, saved first-leg action173a6223 and repaired
donor0a38e12a; exact hashes remain in the source recipe and private receipts.
The unsaved source-return controlaf9b48e6 transfers G1 source7–9.5s into
G2 return47–51.167s while retaining the original world route and poses outside
that window. Its earlier769-sample screen flagged28 times, including right-arm
contacts and posterior-hip folds. This follow-up does not close those failures.

Source/donor comparison found no new axis or translation error: thigh-direction
differences were below0.000059degrees and pelvis-aligned joint differences below
0.000764mm. A pelvis/rest alignment difference predates this restoration. Local
hip-weight mirroring did not reduce18L/45R triangle contact pairs at49.2s and worsened
local edge stretch from1.215x to1.263x. Protected waist points and outside
vertices remained unchanged. Do not undo the separate116-vertex waist repair
or apply another broad mirrored weight gain on this evidence.

The free left hand intersects the foot near49.4s. A measured chest-relative
route uses a0.18m outside/up target with0.4s smooth entrance/exit, a conservative
reachable-arm envelope, then a small measured residual pulse. Two-bone IK
preserves segment lengths and all matrices outside the left arm. This is a
released-hand path; applying it to a locked grip would move the contact target.

| Orientation policy | Limited surface flags | Wrist-local change | Decision |
|---|---:|---:|---|
| Preserve hand world orientation |0/319|41.80588degrees|Visually rejected: sharper wrist kink|
| Preserve source wrist relative to forearm |0/319|0.0000212degrees|Better in inspected views; held for full motion/native checks|

The319 samples run at240Hz from48.7875–50.1125s, including unchanged boundaries.
Only distal left-arm triangles versus the defined body triangles and pole are
screened. Upper-arm, hips, garments and full anatomical ranges are excluded.
Maximum observed world joint speed is313.55degrees/s for the source-local
option; this includes source motion and is not a smoothness/ROM pass.
The original float32 quaternion-dot report had an approximately0.04degree
precision floor; the precise receipt normalizes and compares in float64.
Geometry/controllers were unchanged between these numerical receipts.
The precise audit binds controller SHA256
`80085249cf013a5e9ff559c40c13ea97f1f580b5f230ff35924b90297f9354da`.
The published `24641f672f901b49e3b8bacd8a0f42a44b2e48322eeff6fc58cbc4b601d3ea1f`
revision only clarifies the module docstring's world/local orientation policies;
the lead confirmed no functional change. Retain the tested hash as provenance;
the publication copy was not replayed in Blender during this preparation pass.

Forty detached posed-mesh stills compare baseline/candidate at49.2,49.245833,
49.433333 and49.6s. The independent reviewer inspected20, verified all40 hashes,
and found the additional wrist kink removed at the two central poses. Hip
folds remain. Front fingertips still touch the frame edge; opposing/hand
closeups supply visibility. Bone-joint marker spheres are mostly occluded,
so they do not establish signed thumb/palm direction. These are smooth-normal
Blender diagnostic views, not native material or continuous playback evidence.

Private receipts under `.agent/local/AnimationReview_20261025`:

- `G2FloatingLife/SourcePhraseWristPoliciesPrecise/Audit.json`: final two-policy
  screen, controller/calibration hashes, per-sample metrics and original guards.
- `G2FloatingLife/SourcePhraseLocalWristViews/Manifest.json`:40 image hashes.
- `SourcePhraseDirectionAudit/LocalWristReview.json`: independent comparison.
- `SourcePhraseDirectionAudit/FinalFindings.json`: source alignment and rejected
  hip-mirror trial with exact dependencies.

Reproduction uses `validate_g2_free_hand_corridor.py -- --output NEW_DIRECTORY
--calibration .../SourcePhraseSmoothCorridor/Audit.json` in hidden Blender.
The helper never saves an action or imports native assets.

## Joy: distinguish contact-solver error from skin deformation

Joy uses the101-bone CC_Base rig, not Vexa's95-bone F3 body. Archived exports
of the assigned `A_Joy_PourStanding_Contact` hold both hands effectively fixed
from2–8s while chest/head bounding-box diagonals move35.28/46.61cm. The old
contact script explicitly pins their positions and world orientations. This
reproduces the stationary-props complaint in source data; it is not a fresh
read of today's runtime bindings or counter clearance.

At3.833–3.867s the corrected right forearm jumps51.79degrees and local wrist
57.45degrees, compared with3.29/4.62degrees in the original retargeted source.
The shortest-arc forearm alignment nearly reverses direction, then the fixed
world hand compensates for amplified roll. This is real rotation, not only
quaternion-sign ambiguity. Copying Vexa skin weights would not repair it.

An isolated patch restores the original cup-hand arc as shared cup/bottle
translation:12.16cm arc diagonal,8.33cm peak displacement, preserved relative
placement and intended world pouring tilt. A framewise elbow-plane solve was
rejected for >120degree jumps near extension; a short localized fix still
introduced a23degree return-blend step.

Candidate04 instead calibrates a hinge axis from Joy's original2.0s pose,
transports it with bone orientation through near-extension and uses continuous
signed roll with the original engagement/release envelope. Across381 frames,
largest right-wrist step falls57.45→16.22degrees, right-forearm51.79→11.51 and
left-wrist25.62→17.25. Six tracks change;95 tracks and endpoint rows remain
exact. The patch hash is
`be9e2d6a88c28d84b6865f64defd34ee81e5d468e8d5a34b1c59895898e32eb4`.

**Held:** remaining joint rates, axial rotation, skin/garment response, actual
counter clearance and native playback need review. Source-local free-wrist
following is appropriate for Vexa's released hand; Joy's pouring props require
their coordinated world orientation, so the same hand policy is not reusable.
Current Joy uasset import metadata points to `outfit_v25/SK_Joy.fbx`; the older
`soft_tissue_v2` source is not the current outfit. That source/rest identity is
matched for the isolated comparison below; native bindings still need a fresh
check. No Joy mesh, action, map or native asset changed.

Subsequent isolated visual evidence uses the matching `outfit_v25` source:
18 paired front/side/rear stills at0.900,2.733,3.833,4.400,5.667 and8.300s,
plus one fixed-camera side-by-side381-frame video at30Hz (12.7s media duration,
12.6667s last pose). The MP4 SHA256 is
`884eb3813fd292ae4c085ff36c26534a52b486723a7ac0560d362a3b860b5108`;
full decode retained381 frames. Nine baseline/candidate event/end samples
validate the per-bone rest-basis conversion within0.00248mm bone-origin error,
with positive determinants. These conversion/decode checks are not motion approval.

The capture agent inspected all18 paired event views and selected adjacent
frames; those samples show no gross missing arm or elbow-branch inversion.
The right pouring wrist still looks strongly flexed. Neutral Blender jacket,
hair and trouser artifacts also appear in the unchanged rest control, while
cloth obscures shoulder skin. The grip triads are markers, not actual props;
cup/bottle meshes and the bar are absent. Thus wrist/skin/garment quality,
actual prop/counter clearance, continuous-motion judgment and current native
assignments remain open. All14 original/native guard hashes remained unchanged;
capture processes exited. No visual pass for the full motion is claimed.
Private `VisualProof_Candidate04/VisualAssessment.md`, `PoseConversionProof.json`
and `FinalArtifactReceipt.json` retain these limits and the rejected framing pass.

Private evidence: `JoyAssessment_20261026/Assessment.md`,
`Candidate04Readback.json` and `RigFrameCandidate04Metrics.json`. The
[three-file source-only reproduction bundle](../../Scripts/AnimationRecipes/DancerDiagnostics/JoyPour/README.md)
uses Python/NumPy and guarded private pose exports. It refuses an existing output
directory and an existing readback report. Generated patches, raw pose exports,
licensed/native content and media are not published. Current-source/native visual
acceptance remains open.

The publication copy was regenerated with the existing Python3.11/NumPy2.4.6
runtime into a new ignored directory. It reproduced the exact `be9e2d6a…` patch
above. Independent readback passed381 frames,95 protected tracks and exact
endpoints, with maximum hand-pair relative-position error9.21e-14cm and world
hand-orientation error0.00000296degrees. Reusing the output directory failed
with exit1; reusing the report failed with exit2. Both existing output hashes
remained unchanged. These preservation checks add no native or visual proof.

## Astra: a walking transition, not a transferable shoulder repair

Astra uses PerfectFemaleBody with a different71-bone rig. Source code changes
the pickup animation directly to carry without a blend. Pickup ends with
stationary feet; carry frame0 already has component-space foot speeds302.16
and165.76cm/s. Endpoint mismatch is12.06cm pelvis and19.93/28.21cm feet,
although the tray wrist differs by only0.98cm.

Two offline0.5s bridge controls were withheld. The first has zero endpoint
velocity; the second matches source endpoint derivatives and holds tray tilt
below0.020degrees, but makes left-ankle travel20.76→59.84cm and lowers the toe
by2.21cm. These are joint origins, not a measured floor penetration. No discrete
elbow-plane flip appeared, but that is not skin or anatomy acceptance. Simply
choosing the nearest carry phase also leaves a large stance mismatch.

The required next check is current native clip phase, actor acceleration/speed,
support foot, tray and play rate at the actual pickup-to-travel transition.
A private read-only observer is prepared with exact PID/project/map/file guards; it
does not launch an editor, start PIE, request service, change properties or
save assets. It has passed static checks only and has not run in Unreal.
Its configuration/output path still needs isolation before any execution and
the observer is not part of this source publication. Both bridge candidates
remain withheld; no production change is implied.

Private evidence: `AstraAssessment_20261026/Assessment.md`, `BridgeFollowup.md`,
`BridgeMotionVerification.json`, `DerivativeConvergence.json`,
`SupportScheduling.json`, `NativeTraceRequirements.md` and unarmed trace config.

Joy's counter hunch, Astra's reported inactivity, D-pad Story continuation and
sparse NPC population remain distinct open reports. These motion assessments
do not close them. No ClickUp write, new schedule, merge, package or release.

## Publication checks

The scoped Python/docs worktree passed `CheckProject.py` (50 structural checks),
Python compileall for `Scripts`/`ContentSource`, `ValidateSources.py`
(26 meshes,17 WAVs and unchanged GLB), `CheckPrDocumentation.py`, and
`Tests/TestSourceDigests.py` (13 tests). `git diff --check` passed. No C++ or
Unreal code changed, so no Unreal build or native application was launched.
The unrelated backlog-consolidation receipt and ZeroG files retained their
preparation-time hashes. No files were staged, committed or pushed by this pass.
