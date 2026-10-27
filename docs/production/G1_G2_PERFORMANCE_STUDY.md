# G1/G2 full-performance study

2026-10-27. Planning and review artifact for RPT-20261021-01 in
`docs/KNOWN_ISSUES.md`; not a replacement issue list or an adopted animation.
Owner direction: continue imports, use CPU only, document the current routine
and its gaps before visualizing a complete proposed performance at two frames
per second. Keep the repaired rig; do not reduce choreography to conceal defects.

The [owner-feedback guide](DANCE_OWNER_FEEDBACK.md) preserves the referenced
videos/images and distinguishes accepted ideas or individual views from rejected
motion and unresolved quality. Consult it alongside this study; it does not
turn concept feedback into native animation acceptance or replace the issue log.

Current priority and full-rate review: [complete performance before detail](#full-flow-candidate--2026-10-27t0742z). Earlier two-frame studies below remain provenance; current preview is24fps and still CPU-only.

## What actually exists

- The latest complete video is still the 82.75-second private Unreal edit
  `G1G2_Current_LegPass_Unreal.mp4` (SHA prefix `aad072ad`). It combines captures,
  with camera resets, rather than demonstrating one continuously running level
  sequence. The 75.05-second comparison only changes timing.
- Its G1 action is `cc652d79`, the four-second bridge is `6172cbde`, and the
  subsequent leg-pass G2 action is `173a6223`. The accepted shoulder control
  `51c25e24` and local normal repair `e434f671` remain protected evidence;
  acceptance of those views does not approve every new pose.
- The source review documents only about seven seconds of original G1/G2
  material represented in the long edit, out of 30.866 seconds available.
  The useful source contains alternating reaches, folds, leg exchanges and
  changes of facing that the long routine largely loses.
- `ContinuedDeparture02` is a newer 6.2-second CPU pose trial with 373 samples.
  It is not a new full performance, saved rig action or accepted catch: its
  limited screen still flags 14/187 distal-arm/body and 6/187 pole samples.
- Owner review of the recording accepts approximately 1–6 seconds, objects to
  the cancelled flip at 7 seconds and rigid movement at 8–20 seconds. The
  measured recording offset is about +21.08 seconds, uncertainty about 0.13:
  preserve the idea at routine 22.08–27.08; repair the continuation near 28.08
  and approach around 29.08–41.08. Do not confuse this with the separate local
  G2 return diagnostics at 47–51.167 seconds.
- The new owner selection is **Sensual Moves / AS_Dance6**, original board trim
  **4.87–10.933333 seconds**, intended at roughly source speed (6.063 seconds).
  It is on the owner's now-used port 8770 board. The exported GLB later removed
  a 1/30-second key-time origin; its endpoint is 10.9. Preserve the saved board
  and record this mapping instead of silently changing the owner's trim.

## Gaps and their consequences

| Gap | Evidence | Required change in the target |
| --- | --- | --- |
| Long poses joined by rigid travel | Owner's 8–20-second recording rejection; long waits identified in the full edit | Each travel phrase needs a torso action, unequal leg phrase and free-arm follow-through, not a body translated between endpoints. |
| Flip begins, then unwinds into docking | Owner's 7-second observation | Finish a readable rotation, unfold, then use its momentum for the next action. Do not reverse the rotation merely to recover the old catch pose. |
| Source G1/G2 is underused | About 7/30.866 source seconds | Restore the source's leg exchanges, cradles and coordinated upper body, with phase-specific timing. |
| Regrip resembles fine spacecraft alignment | Owner's reach/catch feedback | One intentional reach, contact, load through elbow/shoulder/torso, and leg pull-up; overlap these actions rather than doing them serially. |
| Contact and skin acceptance are conflated | Earlier wrist/hip/shoulder regressions despite sampled contact passes | Keep grip direction, full arm reach, joint axes, deformation and visual motion as separate checks. A pinned hand is not a complete solution. |
| Free flight has fewer actions than pole support | Owner requests flips, twists, varied legs after release | Free flight is where the largest rotations and articulated unfolding belong; give those actions room and deliberate pacing. |
| Loop closure and reusable connections are unproven | Complete video is an edit with cuts | Plan both end pose and motion direction; do not claim arbitrary-order blocks or a seamless loop from the concept. |

## Performance language

The pole is an intermittent support and visual reference. The performer gathers,
spirals, releases, completes a free rotation, and catches with purpose. Use a
clear contrast between compact and extended shapes, upright and inverted facing,
and firm contact versus free motion. Both legs rarely duplicate each other.
An extended leg is answered by a folding or sweeping leg, not maintained for a
whole orbit. The head follows the intended destination before the catch; the
free arm helps the turn and then opens the silhouette.

Slower does not mean static. Slow free rotation exposes a sequence of distinct
shapes. The catch can be more decisive than the preceding float. A short accent
is allowed at a readable pose, but the whole body should not lock between poses.
Keep smooth directional continuity while allowing changes in speed; do not
apply one uniform slowdown to every action.

## Target and visualization contract

The proposed timing table and source intervals are recorded before images are
generated. Every section and every half-second frame receives a stable ID for
owner feedback. The whole performance must be shown, including both catches
and the final connection, rather than only attractive selected poses.

### Version 1 proposed phrase order: 80 seconds

These are target timings, not a claim that the source clips already connect.
The half-second visualization uses the source intervals below as pose references
and a separately authored space path; it is not a new target-rig action.

| ID / target time | Source pose basis | Connected action and accent | Connection intent |
| --- | --- | --- | --- |
| S01 / 0–8 | G1 original 0–3.5s | Gather one knee, open the opposite leg, exchange the emphasis and begin a shallow orbit. Free arm answers the legs. | Right support; travel and torso turn begin together. |
| S02 / 8–16 | G1 original 4.5–9.5s | Compact cradle, scissor opening, unequal leg fan and re-fold. Brief accent on the open shape, not an eight-second extension. | Keep an intentional support window; body follows a reachable arc around it. |
| S03 / 16–22 | G1 original 10–13s | Re-gather, coil through the torso, free-arm reach and rising leg exchange. | Prepare the support release before moving away. |
| S04 / 22–27.5 | Current G1 22–27.45s | Retain the owner-liked departure: soft release, changing legs and body opening. | Carry its outgoing rotation into S05 without cancelling it. |
| S05 / 27.5–32.5 | Flips and Tricks RM_Flip_B, airborne phrase | Complete a backward rotation: gather, pass through inversion, lead with one foot and unfold. Slower through the articulate middle, more decisive exit. | Hands free; no pole attraction during the flip. Source takeoff/landing are pose references, not floor contacts in space. |
| S06 / 32.5–35.5 | RM_ButterflyTwist_L airborne phrase | Continue into a diagonal twist with unequal knees, then open the chest and identify the pole. | Rotation decelerates into the reach; body remains active. |
| S07 / 35.5–38 | Dance6 entry 3.7–4.8367s in normalized export time | Turn and travel into the reaching arc without stopping; continue directly into the selected phrase. | Approach the future left-hand contact; the actual rising reach occurs at the beginning of S08. |
| S08 / 38–44 | Sensual Moves Dance6, owner trim 4.87–10.933s | Left hand rises into contact over the first 1.2s; then use the coordinated knee/torso/free-arm phrase with a pole support adaptation. | The source raises its left hand, not its right waist-level hand. Fit root travel and shoulder together; do not simply freeze the wrist against incompatible body rotation. |
| S09 / 44–54 | G2 original 0.5–7.5s | Renew the supported phrase with different leg and facing changes: unfold, cross the line of travel, gather and exchange. | The support direction must permit the body turn; release or change grip before winding the arm. |
| S10 / 54–63 | RM_Flip_L plus G1 original 5–6.5s shapes | A second release leads into a lateral roll, compact cradle and staggered extension. Distinct from the first backward flip. | A curved free path with visible whole-body rotation, not a held pose translated away. |
| S11 / 63–67 | G2 original 6–7.5s reach shapes | Approach along an arc, reach, catch and let a leg sweep pull the body into the new orbit. | Catch overlaps the torso turn and leg sweep; source time continues directly into S12. |
| S12 / 67–80 | G2 original 7.5–12.5s, then G1 entry | Supported inversion/fan, gathering turn, asymmetric opening and return to the initial motion family. | End with the same support identity, facing and travel direction; exact derivative/skin/loop matching remains an implementation gate. |

This restores broad G1/G2 pose variety while making the missing released actions
explicit. It deliberately does not include every library suggestion or invent
a wall collision to use the wall-run pack. Wall interaction is a later proposal
until the actual chamber surface and route are established. Repeated half-second
spin clips in MotionBoard are timing proposals, not seamless motion by default.

The independent source audit prompted two seconds to be removed from the first
flip/twist pair before rendering: both still need articulated shape changes,
not another long single rotation. The raw G1/G2 52-joint sources are unretargeted
pose references in this study. Pole anchoring of a proxy shows intended placement,
not compatible arm constraints. S04 retains actual recorded world joint motion;
the surrounding proposal must accommodate it rather than rewrite the liked part.

The CPU animatic is a **choreography proposal using a simple articulated proxy**.
Source pose samples and proposed spatial motion are identified separately. It
does not change Vexa, overwrite an action, retarget a character or prove skin,
finger contact, collisions, velocities between half-second samples, chamber
clearance or a production-quality loop. An orange pole and a second viewing
angle make contact intention and silhouette readable. Review detailed motion
at the eventual full sample rate before adopting anything.

The first proxy review found a discontinuous entry into the retained departure,
angular travel resetting at phrase changes, and a repeated Dance6 entry interval.
The revised study connects S03 before the unchanged 24 Hz departure, carries
travel phase and root position through released phrases, and ends each catch
at the next source interval's start. S05 uses RM_Flip_B 0–0.65s, S06 uses
RM_ButterflyTwist_L 0.1–0.85s, and S10 uses RM_Flip_L 0.05–0.7s before its
G1 cradle blend. These airborne slices avoid spending the new free phrases
on the source's grounded recovery. Blended source identities are shown on
the relevant frames. The Dance6 left-hand support continues through S09,
with a free release before the later right-hand catch. This is position-continuous blocking; smooth velocities,
anatomical transitions and a finished loop remain unverified.

Private review: `SourceAssets/PerformancePlan_20261027/Review.html`, with
`FullPerformance_2fps.mp4` and exact `TargetPlan.json`/`Frames.json` indices.
The video has 160 decoded frames over 80 seconds. The CPU checks confirm
both camera views contain the sampled figure, source hashes are unchanged,
section-boundary positions are continuous, and S04 matches its preserved
24 Hz source at the displayed times. They do not validate character quality.

## S09 replacement proposal — October27

Owner calls the complete CPU study a strong animation concept, but requests a
full replacement of S09. This is scoped concept feedback, not acceptance of
native rigging, grip, skin weights or the final loop. Preserve the 80-second
study as the comparison. The new review is a separate 88-second proposal.

The new Meshy download supplies `Upside_Down_Rope_Hang` and
`Upside_Down_Rope_Hang_1`; `Breakdance_1990` comes from the **earlier** Meshy
download. The nine-second owner recording shows a narrow inverted silhouette,
alternating folded and lengthened legs, and changing arms. It contains no pole,
so it is a motion reference, not evidence of an existing knee grip.

| Beat / target time | Intended movement | Support and connection |
| --- | --- | --- |
| S09a / 44–47.5 | Continue S08's arriving reach, pull the torso toward the pole and gather the knees into inversion. | S08 already ends with left-hand contact; retain that continuity rather than release merely to catch again. Add the supporting hand as the body folds. |
| S09b / 47.5–49.5 | Settle into a compact breakdance shape, with one leg folded and the opposite leg shaping the silhouette. | Transfer support toward the thigh/calf hold before freeing the hands. Avoid the wide Spider-Man shape. |
| S09c / 49.5–59.5 | Descend gently through **2.5 complete rotations**, with a free-leg fold/extension and arm response. | Allow a small, smooth change of contact along the thigh/calf region; prioritize fluid rotation and descent over an artificially fixed knee point. No pole-through-body contact is acceptable. |
| S09d / 59.5–62 | Unhook, gather and flip away, carrying angular motion into the existing zero-G section. | Clear the pole before extending; no magnetic return or cancelled flip. |

S01–S08 retain their existing times. Samples before43s remain unchanged; the
final S08 second prepares the corrected approach/support placement for S09.
S10–S12 move eight seconds
later (62–71, 71–75, 75–88); their existing phrases remain the comparison, with
the S09 exit connection and consistent proxy proportions adjusted where necessary. The extra time belongs
to inversion, visible support transfer and the slow descent, not uniform
slowing of the whole performance.

The 18-second timing is a lead proposal, not an owner-prescribed duration.
Owner's subsequent references explicitly permit different inverted holds and
limited grip movement: preserve character geometry, do not force a wider knee
bend, and make the smooth spin/descent the focus. The additional one-knee-up
pose references inform free-limb variety without changing this phrase order.

Sources and planned adjustments are explicit:

- New Meshy `Upside_Down_Rope_Hang` 0.533333–1.10s supplies the pull/inversion;
  mirror its pose to preserve S08's existing left-hand support.
- Earlier Meshy `Breakdance_1990` 0–0.5s supplies the descending phrase. Remove
  its existing axial turn before adding the stage's 2.5 turns, repeat it at
  four seconds per turn, and smooth only 0.025 source seconds on either side
  of its seam. Preserve source leg directions; no forced calf opening.
- New Meshy `Rope_Hang_Backflip_to_Crouch` 0.9–1.3s supplies the airborne exit,
  before the source's grounded landing. The moving exit blends into S10 until64s.
- Use the S08 endpoint's constant segment lengths for the new proxy poses.
  Tangent bridges interpolate travel/directions and rebuild the hierarchy at
  those lengths. This supersedes rejected direct position interpolation that
  shrank/stretched limbs; no source rig, skin, mesh or animation is edited.
- Fit a smooth periodic two-harmonic pole-relative offset against explicit
  study-capsule dimensions, allowing thigh/calf contact to shift. This
  supersedes a forced65-degree knee opening and a misleading fixed contact
  marker. The yellow marker now shows the nearest support proxy surface.
- The entry wrist was originally on the pole axis/radius despite having a
  nonzero forearm/hand radius. A corrected approach uses83mm wrist stand-off
  and source-plane two-bone IK, together with whole-body placement; moving
  the elbow cannot fix a shoulder origin already inside the pole. Incoming
  S08 velocity continues into the new pull. This is proxy placement, not a
  change to character geometry, a grip solution or native joint-limit proof.
- During47–49.5s, the transfer uses a bounded whole-body corridor around the
  folded leg and retains sliding cylindrical wrist contact until48.90s, when the
  left-leg proxy is near the pole. Then it releases around the pole surface
  into the descending pose. A stable projected elbow guide replaces the
  bridge's invalid through-pole elbow route; it is not a new anatomical limit.
  This preserves segment lengths. The quick arm motion through this inversion
  still needs full-speed review with the actual performer.
- The proxy hand is not a fixed world-space grip during this transfer. Direct
  normalized blending between nearly opposite finger directions caused a
  sharp snap; an outward spherical arc preserves the direction endpoints and
  avoids cancellation. This repairs the study marker, not native fingers or
  palm orientation. The verifier records angular speed and a recipe-specific
  regression alarm; it does not impose a universal anatomical threshold.
- Temporary outward clearance bumps on the release were rejected because
  they recoiled28.4cm toward the pole before departing again. The replacement
  uses continuously increasing root distance through59.5–64s, preserving
  endpoint tangents and source limb articulation. The authored path is a
  choreography proposal, not a validated zero-gravity dynamics simulation.

Use CPU source sampling and a two-angle articulated proxy at two frames per
second. The exact generated placement range, capsule gaps, source/recipe hashes
and validation results belong to the review receipts. Capsule clearance is a
planning screen, not actual skin clearance or physical support. Real thigh/calf
contact, joint limits, fingers, clothing, skin and swept clearance still require
the later actual-rig pass. No native asset or owner MotionBoard sequence changes.
The owner places hair last: evaluate hair/clothing follow-through after body
motion, support, deformation and transitions. Numeric simulation suggestions in
the reference screenshot are unvalidated and are not adopted settings.
Additional owner-supplied rigging and weightlessness notes are references for
the later actual-rig pass: evaluate pivot/contact-space switching, coordinated
limb counter-rotation and overlapping follow-through. They do not authorize a
blind replacement of the improved rig, fixed4–8-frame offsets, generic helper
bone gains or anatomical limits. Preserve source movement and assess the
existing corrected rig before introducing more controls.


## Full-flow candidate — 2026-10-27T07:42Z

The owner's later priority supersedes micro-contact-first work: get the complete
intended performance working, then fine-tune physics and deformation. The original
2fps studies remain history; current motion review is a separate88s/24fps proxy at
`SourceAssets/PerformancePlan_20261027/FullFlowReview/Review.html`.
Movie12860736 / posese1bfdc76 identify this candidate. Neither a numerical pass nor
this preview adopts a target-rig action. Keep the improved Vexa rig and original
motions intact while adapting the complete sequence.

The full phrase order and S09 pull,2.5-turn descending inversion and release remain.
This iteration changes only0–0.5,70.5–71.5 and84–88seconds relative to FullMotionReview.
The accepted departure and S09 are untouched. The final four seconds are a new
reverse-G1 gathering turn; do not label them unchanged G2 source motion.

### Repeatable motion recipe

Private recipe root:
`.agent/local/PerformancePlan_20261027/S09Replacement/CombinedCatch`.
`FullFlowReview/Receipt.json` pins all input and output hashes.

| Recipe | SHA-256 | Role |
| --- | --- | --- |
| full_flow.py | 943c619488e3696aa657362012bcec0023be8f2537af1df9f1ef811639e65c8e | Combines candidates; CPU24fps render and preservation receipt |
| full_motion.py | 59b222186988bbbb7f554968b3df575d5603c2373b6396ac9f6e90942eb86647 | Prior full-rate catch/timing base |
| return_overlap.py | 1478d62cb6091f601131bd3acbca10dfbc58685c19afe4eca73f7e0b7463aa5b | Moving return-source overlap |
| finish_loop.py | f3a4df7b7c6a7e28e672079f2b93ba8832e4ec9587e38848fb90afc0b4ea9f17 | Torso/local-limb finish connector and start clock |

1. **Return70.5–71.5s:** set x=t−70.5. Advance the outgoing old-clock donor by
   62.5+x−0.5x² and the incoming donor by63+0.5x². Normalize the individual
   proxy donors before blending; remove their stage yaw and apply one shared
   yaw12x+5x² above the entry yaw. Use the quintic overlap
   x³(10−15x+6x²), with root Hermite endpoints/tangents from the prior motion.
   This continues side-flip/G1 recovery into G2 rather than fading a frozen pose.
   The original routine resumes exactly at71.5s.
2. **Finish84–88s:** reverse-gather G1 with phase1.2((88−t)/4)².
   Its stage yaw follows a four-second Hermite turn263.209191→360degrees with
   22degrees/second endpoint rates. Tilt is8sin((t−88)×0.3)degrees.
   The right-wrist proxy anchor is[0.035,0,3]metres. It is a choreography anchor,
   not an accepted finger grip or force model.
3. **Overlap84–86s:** outgoing clock is84+2(x−0.5x²), x=(t−84)/2 clamped0–1.
   It advances rather than freezes immediately. Separate torso orientation
   from local articulation: construct an orthonormal right-handed frame from
   chest−pelvis and right-hip−left-hip; quaternion-blend the frames, then blend
   hierarchical limb directions in those local frames and reconstruct positions.
   This prevents whole-body inversion from forcing a near-antipodal leg swing.
4. **Opening0–0.5s:** G1 phase0.21875x²(2−x), x=t/0.5, starts with zero source
   speed and rejoins the original phase/rate at0.5s. Stage yaw22t and tilt
   8sin(0.3t), with the same right-wrist anchor, match the finish's direction.
   The exact end/start positions agree; finite-difference velocity mismatch
   is2.86e-5m/s. This is only proxy loop continuity.
5. **What not to repeat:** world-space limb-direction blending across nearly
   opposite whole-body poses produced an abrupt knee/leg arc even when the
   final pose matched. Shortening the fade alone did not solve it. Blend the
   body frame and local articulation separately; preserve moving donor clocks.
   Do not trade away the flip, leg variety or torso motion to hide rig problems.

The86s source-key speed corner remains; independent comparison isolates it to
G1 source phase0.3 rather than the new fade. Judge it in motion before retiming.
The preview still blends normalized source proxies with different proportions;
it does not prove fixed target-rig geometry, skin, fingers or anatomical limits.
Rejected finger candidates remain frozen. Fit this whole performance to the
preserved Vexa rig next, then assess detailed contact/physics and the other
characters in the established order.

## Whole-rig CPU motion — 2026-10-27T08:26Z

The owner explicitly prioritizes the entire intended performance before micro
contact, deformation or physics. The new private review is
`SourceAssets/PerformancePlan_20261027/FullRigFlowReview/Review.html`.
It shows actual95-bone motion at24fps with simplified anatomy, then the same
motion skinned onto the preserved mesh at2fps. Both movies run88seconds.
This is an offline motion draft, not a saved native action or final skin result.

### Reproducible transfer and rejected controls

Private recipe: `.agent/local/PerformancePlan_20261027/FullRigTransfer`.
Run `transfer.py`, then `verify_motion.py`, then `render_motion.py` with the
existing Python/NumPy/Pillow runtime and existing ffmpeg. These are CPU operations;
they do not launch Unreal or Blender. The private target/donor extraction uses
the existing Three parser only; no renderer, installation or shared-loader edit.

1. Preserve Vexa's shoulder candidate `51c25e24` and corrected rest FBX
   `243a8f3e`. Recover95 unique bones and actual parents from raw FBX Model
   connections: Three duplicates bone objects for the five mesh skins, so
   its object-instance parent list is not the hierarchy authority.
2. Read raw mesh cluster weights without Three's four-influence truncation.
   Retain all28,261 vertices,53,904 triangles and up to10 influences per vertex.
   Per-mesh bind matrices reproduce rest surfaces within4.324micrometres.
   No vertex, weight, bone length or source asset is changed.
3. Keep native G1/G2 full-joint donor rotations and GLB donor rotations.
   The target/native reference comparison is a single world Rz180 alignment;
   it is not a per-bone rotation and must not be applied again to the already
   aligned performance. Rest origins agree within5.32micrometres.
   Preserve target local translations, fit major directions, and carry donor
   roll/fingers through the actual hierarchy. Missing helpers retain rest locals.
4. The first full-rig draft exposed a161-degree upper-arm step near21.25s:
   the old proxy's Cartesian blend collapsed its arm direction to13.47mm.
   A direction-only spherical repair moved the flip into the forearm; adding
   a fast transverse-frame fade still produced94-degree and90-degree steps.
   These stacked fixes were rejected.
5. Replace only20.8–21.8s with one local quaternion connector for the left
   clavicle, upper arm and forearm. Spherical cubic control rotations match
   endpoint angular velocities sampled at0.0001s. Reconstruct descendants at
   fixed translations; keep current wrist/finger locals and the entire
   pelvis/spine/leg motion. Maximum24Hz upper-arm step falls161.43→17.27degrees;
   forearm89.29→15.91degrees. This is a new one-second transition, not unchanged
   source motion or a freeze.
6. A separate171.87-degree forearm step near69.35s came from minimum-swing
   ambiguity at nearly opposite aim directions. Over68.75–70s, project the
   donor world transverse onto the desired aim plane, build a proper frame,
   and blend at the boundaries. Using the already-fitted parent transverse
   failed. The successful bounded frame reduces the maximum step to19.61degrees.
7. Do not aim a wrist at middle_03: that is an articulated composite finger
   marker. Preserve donor wrist rotation instead. Fingers remain animated;
   fast or unsuitable source wrists are still a later repair, not accepted.
8. Never replay the original96 G1 time-indexed shoulder corrective curves on
   the new88s timeline. Original corrections are retained for later remapping.
   This first transfer also approximates the liked departure from source clocks;
   it is not an exact native replay of that previously accepted saved passage.

`MotionVerification.json` binds source and recipe hashes. All2113 samples at24Hz
have finite, proper rotations; fixed local-translation error is below0.290µm.
The88→0 matrix endpoint is exact. Protected body/legs match the first whole-rig
draft throughout; outside the two repair windows, non-wrist bones match it exactly.
Independent review verifies endpoint and local-chain preservation.

Remaining watchpoints include the94-degree left-wrist step at44.25s and rapid
source/transfer motion near15.83/16.25s. Endpoint equality does not prove velocity
or artistic continuity. Full-rate skinned playback, anatomical limits, gripping,
garment response, chamber clearance, native transfer and owner acceptance remain
open. Keep the whole-performance-first priority; do not resume isolated detail
experiments or weaken the choreography to conceal rig defects.

## Later implementation gates

1. Approve the phrase order, pacing and silhouette changes from the full study.
2. Fit the actual corrected Vexa rig to the selected source phrases, retaining
   original motions and the prior good deformation controls as comparisons.
3. Author contact windows and whole-body approach together; inspect palm/thumb,
   wrist roll, elbow direction, shoulder and torso throughout each catch.
4. Review hips, knees, ankles and all garment boundaries through moving poses
   from front, side and back. A neutral proxy cannot establish those results.
5. Check continuous joins, actual chamber swept clearance and full-speed looping.
   Save a repeatable recipe with source hashes and rejected approaches before
   applying it to Joy, Astra and the remaining dancers.

The five pole/five free-flight building-block concepts remain separate deferred
work. This study improves the current complete performance first.
