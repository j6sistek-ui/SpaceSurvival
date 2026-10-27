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
