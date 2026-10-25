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
