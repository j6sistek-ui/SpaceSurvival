# Dance owner feedback and evaluation guide

Consolidated 2026-10-27 from this conversation, its supplied images/videos, and
the existing source-bound review records. Individual message timestamps are not
available for every observation; the date above is the consolidation date.

This is a durable reference for decisions, comparisons and troubleshooting.
It is **not a second task queue**. Current ownership, priorities and closure
evidence remain in [KNOWN_ISSUES](../KNOWN_ISSUES.md), chiefly
RPT-20261021-01 (rig/choreography), RPT-20261016-03 (animation planning tools),
and RPT-20261015-01 (bar interactions). The current target and timing are in
[G1_G2_PERFORMANCE_STUDY](G1_G2_PERFORMANCE_STUDY.md). Reproducible deformation
work is in the local-only recipe at
`C:/Users/j6sis/SpaceSurvival/Scripts/AnimationRecipes/DancerDiagnostics/DEFORMATION_RECIPE.md`;
that file is not present on PR97 or current main at this consolidation's check.

## Main takeaways

1. **Preserve the dance.** Do not remove difficult motion, simplify a strong
   source into a static orbit, or lower quality to conceal rigging defects.
   A material artistic compromise belongs to the owner.
2. **Movement connects the poses.** Coordinate torso, hips, arms, legs, wrists
   and ankles through transitions. A good still is insufficient if the figure
   becomes a rigid doll between stills.
3. **Purposeful weightlessness.** Deliberate flips, twists, extensions and
   gathers should feel controlled and artistic, with floating travel. Avoid
   helpless falling, uncontrolled AI drift or a slow docking/magnetic return.
4. **Preserve character proportions.** Pose and placement may change; do not
   stretch limbs, reshape anatomy or force a knee wider merely to fit the pole.
5. **Contact must work through motion.** A planted hand cannot force the body
   into impossible shoulder/elbow/wrist poses as it rotates. Pole-through-skin,
   floating grips and unmotivated hand switches are failures.
6. **S09's gold is a smooth descending spiral.** A natural inverted hold may
   lock or shift slightly along the thigh/calf region; it need not be an exact
   knee-gap anchor. Let the spin/descent lead, then flow into the released flip.
7. **Acceptance is narrow.** Approval of one shoulder, angle, frame or concept
   is not acceptance of the whole rig, routine or native Unreal result.
8. **Inspect both sides and intermediate bends.** The recurring worse shoulder,
   partially opened knee, wrist, ankle and pole-gripping hand need explicit
   review, not inference from a successful overhead pose.
9. **Keep the recipe and rejected controls.** Preserve the better version,
   source identities and exact changes so later characters benefit without
   restarting trial and error. Similar bodies still need compatibility checks.
10. **Finish the current performer/routine first.** Vexa's purple-haired variant
    is the focus; Joy and Astra follow, then other dancers. Hair is last.

## What the owner accepted, rejected or qualified

| ID | Owner evidence / decision | Scope to retain |
| --- | --- | --- |
| FB-A01 | First overhead image improved; subsequent correction said the front arm was good but the arm behind the head was wrong. | Preserve the good front-arm comparison, not the whole pose. |
| FB-A02 | Hips looked normal in one comparison; knees still pinched, especially partially open. | Hip approval does not clear knees or other hip motions. |
| FB-A03 | Several shoulder trials were much better; one side remained consistently worse. Neck, head and over-raised shoulder blades later regressed. | Keep approved comparisons and reject neck/back regression independently. |
| FB-A04 | Latest raised-arm comparison was “better. good with this.” | Accepted appearance of that shot only; later ordinary folded-arm defects reopen broader coverage. |
| FB-A05 | A rear-view difference was initially questioned, then owner acknowledged head tilt/asymmetric pose could explain it and said the shoulders were generally close. | Compare matched/mirrored poses before imposing artificial symmetry. |
| FB-A06 | A leg-direction pose was initially rejected, then owner explicitly withdrew that rejection. | Do not keep the withdrawn pose rejection as an active defect. The associated glute-volume collapse remains distinct. |
| FB-A07 | Many pole stills looked good; the actual gripping hand did not. Thumb identity/orientation was uncertain in the image. | Do not rotate a hand based on an ambiguous camera view; label right/left and palm/back first. |
| FB-A08 | The old 82.75s performance had good parts but rigid, sliding release/return. In the owner recording, 1–6s was good, about 7s cancelled a promising flip, and 8–20s was doll-like. | Keep the liked departure; fix the connection and follow-through, not just pose thumbnails. See the existing dated alignment receipt before using recording times as routine times. |
| FB-A09 | The 80s CPU study was called a strong animation, except S09 needed full replacement. | Broad concept approval only. S09 and native anatomy/contact/full-speed motion remain unaccepted. |
| FB-A10 | New inverted-hold references allow a natural contact range, including shifts outside the exact knee gap. | Supersedes a rigid knee-point requirement. Preserve geometry and prohibit pole-through-skin. |
| FB-A11 | Hair explicitly agreed as last priority. | Do not let secondary-motion work displace body motion/contact/rig validation. |

## Evaluation guide

These are owner requirements and observations. The checks below are lead
evaluation methods, not evidence that a check has passed.

### Shoulders, neck, back and torso

- Retain a visible natural shoulder cap; avoid an arm appearing to grow directly
  out of the neck, jagged axilla folds, sloping neck bulges or bodybuilder-like
  trapezius volume on this character.
- Review the recurring poorer side against the better side using identical
  arm elevation, chest orientation, head tilt and camera/light conditions.
- Shoulder-blade movement can help, but excessive blade elevation and neck/head
  distortion are regressions. More helper motion is not automatically better.
- The owner supplied scapula/clavicle/pectoral rig examples and a transcript
  describing topology, bone placement, weights, selective volume preservation
  and corrective smoothing. These are references, not instructions to copy
  generic gains, reparent bones blindly or replace the improved rig.
- Evaluate overhead, side-raised, forward reach, folded-across-body, behind-head
  and rotating support poses, plus the transitions between them.
- Textures/lighting may change visibility but are not a repair for a bad
  silhouette, collapse or intersection. Compare neutral and final materials.

### Hips, legs, knees, wrists and ankles

- High leg lifts must preserve the rear/glute volume instead of sinking it
  inside the torso. Check both the joint direction and the skinned response.
- Avoid the “dolphin” thigh shape and pinched knee. Inspect straight, partly
  bent, deeply folded and reopening knees; closed knees alone were misleading.
- Add leg-direction checks, while respecting the withdrawn rejection in FB-A06.
- Wrists and ankles were explicitly called out as broadly poor in prior
  characters. The shown shoulder poses are not a gold-standard full-rig test.
- Treat the owner's conservative arm-direction comments as a requested motion
  guard: avoid arms dragged backward behind the torso, twisted elbows and
  backward forearms during raises. The mentioned 90°/~10° limits require a
  calibrated local-axis interpretation; they are not a universal clamp on all
  arm elevation, since good overhead reaches are explicitly desired.
- Preserve original mesh pieces, seams, topology and proven weights. A similar
  body is a transfer candidate, not proof that weights/correctives can be copied
  blindly. Verify the actual asset; the purple-haired Vexa was the selected one.

### Hands, pole contact and release

- Keep the orange diagnostic pole and temporary forearm direction marks while
  useful; remove diagnostic marks from the final presentation later.
- Identify hand side, thumb, palm and dorsal surface before changing grip roll.
  An upside-down or misidentified grip can drive bad wrist/arm compensation.
- Evaluate contact during whole-body rotation, not only at the first planted
  frame. Fingers, wrist, elbow, shoulder and torso must agree with the hold.
- Reach, grab, pull and leg inversion should read as a connected action. Avoid
  hesitant hand alignment, slowly sliding back into a frozen pose, or a release
  that immediately cancels a promising flip to dock again.
- For S09, allow a small natural contact range along the thigh/folded calf and
  other plausible inverted holds. Do not alter proportions or force an opening
  to accommodate the pole. No pole cutting through skin.
- Verify both the sustained hold and its entry/exit. Passing a descent-only
  clearance screen does not clear an intersecting forearm during the flip out.

### Choreography, pacing and zero-G feel

- Restore the rich G1/G2 source motion. The owner specifically preferred the
  G1 pose-sheet leg variation over the earlier long, extended orbit.
- Use alternating knees, uneven extensions, gathers, reopens and controlled
  split transitions where they fit the phrase. Do not keep both legs rigidly
  shoulder-width or fully extended for long travel intervals.
- Let multiple body regions participate. Slow, subtle free-limb motion supports
  continuity; deliberate holds are for key poses/strong accents.
- Pole approaches/catches can be quicker and more decisive. Free-floating
  flips/twists are the place for slower, detailed articulation.
- Use released time for actual acrobatics: complete the flip, twist, fold,
  extend and redirect. Do not replace that opportunity with a fixed body drift.
- Later physics guidance suggests counter-rotation, momentum-aware travel and
  overlapping follow-through. Use it as an artistic/technical evaluation lens,
  not a mandate to copy fixed frame offsets or rework the whole rig now.
- Coordinate a gather with faster rotation and an extension with a calmer
  rotation where that reads naturally. Preserve travel through released phases;
  do not repeatedly brake or accelerate in empty space without a visible cause.
- The intended outcome is in-game quality across multiple dancers, not only a
  cinematic shot. Avoid promising “AAA,” “perfect” or “gold standard” from a
  small set of images or one successful proof.

## Current S09 intent and source distinctions

Owner direction: continue S08's reach, pull into compact inversion, transition
into modified breakdance, hold with the thigh/calf region while descending for
two to three full turns, then flip off into the zero-G section. Avoid the wide
Spider-Man pose. The lead's current timing proposal is 18s with 2.5 turns; these
numbers are proposed implementation, not an exact duration supplied by owner.

- **Earlier Meshy:** `SourceAssets/MotionBoard/Meshy_Reference.glb` contains
  `Breakdance_1990` and the previously discussed move library. Do not confuse it
  with the latest download. Its original half-second axial spin needs deliberate
  looping/retiming and seam review, not merely freezing its pose.
- **Latest Meshy:** `Downloads/Meshy_AI_Violet_Wraith_Queen_All_Animations.glb`,
  copied privately to `SourceAssets/MotionBoard/libraries/meshy_hangs.glb`,
  supplies the upside-down rope hangs and rope-hang backflip donor. The reference
  recording has no pole, so a demonstrated pose is not existing grip evidence.
- **Dance6:** owner-selected Sensual excerpt was approximately 4.87–10.93s,
  displayed for 6.06s, with the raised hand intended for pole support. Retain the
  owner's exact board trim where available rather than replacing it from a
  rounded screenshot or a newer export's slightly different duration.
- G1→G2 and B1→B2 mean consecutive clips on one performer, not paired dancers.
- Flips and Tricks was installed in AFS and later located/copied for review.
  Existing dance, sensual, social and even a jump/arise motion can provide useful
  transition pieces when their actual motion fits. Names alone are insufficient.

The earlier proposal to create five pole and five free-flight 10–15s building
blocks remains later work. Concept frames/sequence IDs come before rigging those
new blocks. The owner asked to pause that side work and finish this routine,
then Joy/Astra. Do not silently resume it because new inspiration was supplied.

## MotionBoard requirements retained from the same discussion

- One browsable library across owned packs, grouped by package; avoid default
  clips cluttering the requested library. “Downloaded” in Fab is not proof of
  where the files currently reside, and UASSET-only packs need an export path.
- Animated previews on cards are essential. Keep moving characters framed;
  no one-frame flashes, runaway root motion, vanishing text or collapsing UI.
- Drag/drop or simple selection into eight ordered slots; trim source in/out,
  specify timing, preview the sequence and export the proposal with provenance.
- Global card-preview speeds: 0.25×, 0.5×, 1×, 2×. This must not silently retime the
  saved sequence.
- Distinguish stretch from repeat. A 0.5s move repeated ten times at 1× lasts 5s;
  specifying 10s of looping repeats it twenty times, rather than stretching one
  cycle into slow motion. Preserve reverse and source trims consistently.
- Accept actual local FBX as well as GLB sources. Preserve the owner board and
  source files; no destructive path moves or duplicated asset collections.
- Full-performance video is needed for pacing judgment. Provide numbered
  sequences/frames; mobile stills are not a substitute for video review.

## Joy/Astra and transfer boundary

After the current routine/rig is established, evaluate Joy and Astra using the
documented methods and their actual current assets. Prior owner reports include
Joy's D-pad story stopping after a teaser, hunching into the bar, and stationary
bottle/glass props while her body moves; Astra's service arm bending backward,
tray near/intersecting face/body, and later inactivity. These are separate
animation/contact/state defects, not all skin-weight problems. Existing bar
interaction acceptance remains limited; do not mark these closed from this
dancer work. Other dancers follow after that, with compatibility evidence.

## Review and troubleshooting method

1. Identify exact source, character variant, candidate recipe, clip/time and
   reviewer angle. Hash sources; preserve the better comparison.
2. Classify the defect: source motion, retarget axes, joint direction/limits,
   contact placement, interpolation, weights/correctives, garment, rendering,
   or runtime state. Do not compensate for one by damaging another.
3. Change one causal element in an isolated candidate. Retain rejection evidence
   and explain what it disproved. Avoid broad gain sweeps without a hypothesis.
4. Review neutral front/side/back and close contact views, then final materials;
   include intermediate bends and continuous motion around every transition.
5. Check fixed limb lengths, source continuity, signed orientation, source-loop
   seams, contact windows, swept clearance and whole-stage envelope. A contact
   marker or a solved IK target is not proof that skin clears the pole.
6. Distinguish CPU proxy, Blender skin proof, native Unreal playback and owner
   acceptance. Two-fps concept output shows phrasing; it cannot prove full-rate
   fluidity, physical support, fingers, final skin or a seamless runtime loop.
7. Record the result under existing issue IDs. Transfer a recipe only after
   testing the next asset, retaining source/variant identity and failure cases.

### Check each stage, not only the finished pose

| Stage | Review question | Evidence to retain |
| --- | --- | --- |
| Source selection | Is the actual useful movement present, and is an apparent defect source drift, retargeting or skinning? | Source/clip identity, interval and unmodified comparison. |
| Concept and timing | Are all phrases connected, with varied coordinated limbs, completed rotations and purposeful accents? | Numbered full-performance frames plus playable video; section/time labels. |
| Rig and skin | Do both sides retain the accepted silhouette across ordinary and extreme poses, including intermediate bends? | Matched front/back/side views, neutral/final materials and continuous joint tests. |
| Contact | Does entry, sustained support, any slide and release work without penetration, wrist flips or impossible body rotation? | Close opposing views and continuous surface/clearance checks, not only IK targets. |
| Integrated performance | Does the entire sequence play at intended speed and connect to the next phrase or loop without snaps, freezes or drift? | Full-speed playback including boundaries; verify final stage footprint and height. |
| Transfer | Does the recipe still work on the actual next character and its garments, proportions, hierarchy and runtime system? | Separate source-bound result for each character; no inherited acceptance. |

### Ideas to assess when a concrete defect calls for them

The latest supplied rigging text is **reference advice**, not an approved rig
specification. Retain these intended outcomes without copying arbitrary bone
counts, rotation gains, weight values or modifier settings:

- A movable trajectory/pivot control may help rotate around the torso or a
  support contact. Check that changing the pivot does not pop position or break
  existing animation, instead of assuming every standard rig is ground-locked.
- Quaternion or layered rotation controls are candidates for multi-axis turns.
  Inspect the actual rotation curves and complete turn count; changing rotation
  representation alone is not proof of continuous intentional spins.
- A spline/ribbon-style spine is an option if existing torso controls cannot
  produce distributed waves. Preserve the currently improved silhouette and
  compatible export skeleton; do not rebuild it merely because advice suggests
  five or six bones.
- Matched world/local contact spaces and FK/IK switching are useful goals for
  catches and releases. Verify matching poses at switches and feasible full-body
  motion afterward; a world-locked hand alone does not solve the performance.
- Twist distribution, localized hip/glute helpers and pose correctives may
  address a demonstrated collapse. Calibrate against the actual topology and
  local axes. Do not apply a universal 50% thigh gain or overwrite good shoulders.
- Ribcage and abdomen should articulate coherently while retaining their
  intended shape. Evaluate the existing spine weights before adding bones or
  copying suggested weight percentages.
- Zero-gravity hair, cloth and soft-tissue response remain later refinements.
  Suggested gravity/damping values are unvalidated; body animation and contact
  are first, and hair is explicitly last.

For each interim review, record: **candidate/hash; clip and time; view; feedback
ID/reference; observation; proposed cause; one change; measured and visual
result; preserved comparisons; remaining uncertainty**. Label statements as
owner direction, lead interpretation or verified evidence. Owner approval must
quote its scope; do not convert an attractive concept into native acceptance.

Operate within the current resource permission. The active phase is CPU-only;
no new Unreal/Blender/GPU jobs or visible pop-ups. Scheduled ClickUp reminders
were cancelled; do not recreate them. New references are input to evaluation,
not permission to install tools or replace the rig.

## Private reference index

Original media remain private and are not copied into this PR. Attachment paths
below are rooted at
`C:/Users/j6sis/.codex/codex-remote-attachments/01a13228-86f6-7140-9cca-c0371d6efc87/`.
Use the stated subpath; image evidence is scoped to what it shows.

Availability was checked for all 40 indexed files on 2026-10-27; none were
missing. SHA-256 identities and original paths are saved privately in
`SourceAssets/DanceFeedback_20261027/ReferenceManifest.json`. Temporary clipboard
images were also preserved under that folder's `References` directory, with
identical images deduplicated: 12 files, 2,154,225 bytes. Large source videos and
models were not duplicated. Resolve a missing temporary path through this
manifest before requesting the same reference again.

| Ref | Private subpath or exact file | Why retained |
| --- | --- | --- |
| R01 | `4845D458-C27F-4B5A-BA19-7ACA97C1CB69/1-Photo-1.jpg` | Better front overhead arm; behind-head arm subsequently rejected. |
| R02 | `EDEE7A8F-191B-497D-800F-AAA99DFD79C3/1-Photo-1.jpg` | Hip pinching example. |
| R03 | `1EB2AACE-DE7F-45CF-A620-337D6E0B4600/1-Photo-1.jpg` | Better hip comparison, not full leg acceptance. |
| R04 | `FDBD00CA-A8B1-41CC-B595-84624167703D/1-Photo-1.jpg` | Partially bent knee pinch. |
| R05 | `A3AF8204-CA12-48F7-8F97-CAF280E998EA/1-Photo-1.jpg` | Correct arm direction but poor shoulder weighting. |
| R06 | `79C595B9-8B55-4841-BE5B-AF970EE2E217/1-Photo-1.jpg` | Green/better versus red/jagged shoulder; center neck/back also rejected. |
| R07 | `65E9EA02-CCAA-485E-BB43-26C5005B21A0/1-Photo-1.jpg` | Explicitly accepted raised-arm comparison. |
| R08 | `F81BDC2E-3B3F-4436-8094-FA3D88C36FB7/1-Photo-1.jpg` | Rear comparison, later qualified by asymmetric pose/head tilt. |
| R09 | `6B3EA3D2-8528-4159-BFBC-3D4AC7E6A9B7/1-Photo-1.jpg` and `BD1B2772-06DD-4BE7-9049-AD447229B115/1-Photo-1.jpg` | Leg-direction discussion; initial rejection later withdrawn. |
| R10 | `2AE3F7DE-8E0D-4631-9130-42A65C763467/1-Photo-1.jpg` | Distinct glute/rear-volume collapse remains relevant. |
| R11 | `8AA7DE47-FA31-4D8A-87FE-2B0422886933/1-Photo-1.jpg` | Ambiguous thumb/palm and upside-down-grip discussion. |
| R12 | `985EFDDF-AB9B-487D-9E7B-FFB13127A2FE/1-Photo-1.jpg` | Shoulder defect in an ordinary folded-arm pose after earlier improvement. |
| R13 | `E80CD924-B3AB-42E6-AE36-7B8477DA6367/1-Photo-1.jpg` | G1 leg variety the owner explicitly wants restored. |
| R14 | `06D43CD6-854C-4C2C-8AE6-7CBABC1DE88D/1-IMG_9733_default.glb` | Imperfect generated source; salvage useful segments without copying drift. |
| R15 | `B5BB35F5-7F0C-4F0F-AFDE-7BFCD04CBC8C/1-users_c22ce5da-d72e-424e-8cfe-737acc12d3c2_generated_a5744caf-1add-4ae8-a38a-123522bb8a01_generated_video.mp4` | Backward flip and leg variation despite AI drift. |
| R16 | `8367059C-B2F7-4EC0-88F5-EFE3D843AA53/1-gemini_generated_video_EFCB9CE4.mp4` | Movement/flow inspiration, not a demanded exact routine. |
| R17 | `68DABAD7-DC79-480A-9B80-52CBFC102F6D/1-ScreenRecording_10-26-2026-17-57-23_1.mp4` | Jump/arise/social motion as potential transitions. |
| R18 | `8E6B631A-016F-4C9F-8AB7-299108592EA3/1-IMG_9694.mov` | Shoulder rig rotation and figure change. |
| R19 | `1DBE918E-7EF4-4C24-8FD6-6E15AD4C6E37/2-ScreenRecording_10-25-2026-19-05-30_1.mov` | Scapula/pectoral rig inspiration. |
| R20 | `76F07F60-159C-4E13-B0E7-2CD3D78E7A89/1-Photo-1.jpg` through `4-Photo-4.jpg` | Early-video bone-placement screenshots; not proof of the final setup. |
| R21 | `C:/Users/j6sis/Videos/Screen Recordings/Screen Recording 2026-10-26 195012.mp4` | Liked 1–6s, cancelled flip about 7s, rigid 8–20s. |
| R22 | `C:/Users/j6sis/Downloads/Recording 2026-10-26 232500.mp4` | New inverted-pose motion reference, no pole. |
| R23 | `C:/Users/j6sis/AppData/Local/Temp/codex-clipboard-95cbbe11-40f7-40c2-9b65-b36f04fd9fa1.png` | Dance6 trim/duration and intended pole line. |
| R24 | `C:/Users/j6sis/AppData/Local/Temp/codex-clipboard-e486db18-8d3e-41f4-87a8-be0cc585abfb.png` | New Meshy upside-down hang clip names. |

The following recent images use the prefix
`C:/Users/j6sis/AppData/Local/Temp/codex-clipboard-` and suffix `.png`:

| Ref | Filename UUID(s) | Why retained |
| --- | --- | --- |
| R25 | `fc07e872-0280-4f3b-a191-f97970830887`, `d92d4601-5cb3-4d33-85fd-29d074463ca2`, `572e7950-a2e0-44bf-9b11-d2bb769119b9` | Natural inverted holds; folded knee/calf/thigh and offset torso. |
| R26 | `7786b8d1-5b29-45e1-ad88-27edc9b30ca7`, `611d328b-bc46-4432-8649-1331f2c453be` | Inverted extension reference; duplicate view retained by identity. |
| R27 | `005dd885-cc84-46c0-9352-9606b1c85691`, `77c7d093-13fe-4374-bbe7-c8405037ba46` | Alternative inverted contact/hand-foot pose, not mandatory choreography. |
| R28 | `ba85c380-661b-454d-8f75-42ca4b4d57de`, `ba8f450e-cd4a-47ae-803c-e83e4e891c5d` | Extended and compact inverted support options. |
| R29 | `dca18c3f-c439-4aee-b003-62def23f1c76` | One-knee-up and free-leg dance silhouettes. |
| R30 | `84ca235c-cc89-4588-af52-fb496e8952e2` | Secondary-motion suggestions; hair explicitly last, values unvalidated. |
| R31 | `002df086-7360-4975-a053-ba6d1fe97fd3` | Weightless travel, limb counter-rotation and overlapping follow-through guidance. |

The pasted shoulder tutorial transcript and latest zero-G architecture/weighting
advice are preserved here as paraphrased takeaways, not verbatim technical
authority. Owner supplied `https://m.youtube.com/watch?v=c_XM01I6ed0` and
`https://www.reddit.com/r/blender/s/gykESSwzkI`; this consolidation does not claim
the full linked videos/comments were newly watched or verified. Read the actual
source and installed tool behavior before relying on a specific API/rig recipe.

Later feedback should append a stable FB identifier, exact reference/time,
accepted/rejected/qualified scope and the canonical issue it affects. Supersede
withdrawn conclusions explicitly rather than accumulating contradictory rules.
