# G1/G2 restoration and reusable choreography concepts

Planning record, 2026-10-26. Active work and acceptance remain RPT-20261021-01
in `docs/KNOWN_ISSUES.md`; this is not a second task queue.

## Order and boundaries

**Owner update, October26 23:12 UTC:** Concept side work is paused. Ten final
numbered F1–F5/P1–P5 sheets and frame notes were copied and SHA-verified in
`C:/Users/j6sis/OneDrive/Pictures/SpaceSurvival_Animation_Concepts_2026-10-26`.
The owner will propose combinations later. The gallery builder remains an
unpublished draft, not an available review delivery. Continue the current
Vexa sequence; parallel Joy/Astra source evaluation is now explicitly allowed.

1. Continue the current Vexa routine. Restore the missed G1/G2 body phrases,
   including coordinated torso, free arm, knees and feet. A periodic leg
   overlay alone does not meet the owner's correction.
2. Show image/video concept frames for the proposed new sequences **before
   rigging or animating them**. Current routine repair can continue. The owner
   explicitly requested concept designers and an independent reviewer;
   their assignments do not authorize production asset changes.
3. Target five pole and five off-pole blocks, each10–15seconds. These are
   proposed building blocks, not ten completed clips or a new runtime system.
4. Preserve choreography while fixing rig/contact problems. A necessary cut
   or reduction needs concrete evidence and an owner decision. Do not stretch
   a tiny source fragment into a long rigid orbit to avoid difficult poses.

The current82.75second native-video edit covers only about7seconds of the
original30.866second G1/G2 source. Restoring source coverage is the immediate
implementation problem. Original target-rig FBX baselines remain in private
`AnimationReview_20261025/SourceBaseline`. The selected target-rig library
0a38e12a contains arm repairs; it is not untouched full-body source.

## Proposed blocks, not approved animation

### Numbered concept revision requested October26

Owner feedback rejects F4's malformed limb and the sparse/slow impression of
the first sheets, and requests usable pole visuals. Revision2 keeps F1–F5 and
P1–P5 but gives each six individually addressable beats: `.01` through `.06`.
The proposal must show multiple coordinated moves rather than one extension
held for an entire block. Proposed times are not proof of playback pacing.
Frame IDs are revision-specific; do not silently apply v2 feedback to v1 art.

Private source plans/images are under `BuildingBlocks/*Concepts/V2`; the
final revision has ten sequence IDs and sixty frame IDs. F4's malformed leg
was corrected; drawing QA found no obvious extra limbs in the final sheets.
Concept anatomy/hand continuity is still not rig or motion acceptance.
Use the saved Pictures copies for later feedback. Every new transition requires the contact,
velocity, orientation and swept-volume checks below. Current routine repair
continues separately; none of these new blocks is authorized for animation
before its concept is shown and directed.

The table below retains the first proposal's source basis and durations. V2
`Frames.json` owns the revised beat timings and captions (10–12seconds),
superseding v1 durations for this review; neither is a completed action.

| ID | Target | Main phrase | Evidence or inspiration |
| --- | --- | --- | --- |
| P1 |12s| Gather and fan, alternating leg emphasis, shallow orbit | G1 source0.5–3s and9–11s pose sheets |
| P2 |13s| Compact cradle, scissor, reopen and exchange | G1 source4.5–6.5s and7.5–9.5s |
| P3 |12s| Gather, handover ascent, unwind and open | G1 source10–16.833s shapes; pole handover must be authored |
| P4 |10s| Torso ripple, soft knee exchange, opposing reach | G2 source0.5–4.5s and7.5–9.5s |
| P5 |15s| Supported fold, release, free rotation, recovery | G2 source10–13.5s/G1 tilt; clean full backward flip is a proposal |
| F1 |14s| Gather, backward twisting flip, twirl, full-body extension | Original RM_Flip_B and RM_ButterflyTwist_L plus G1 leg ideas |
| F2 |12s| Diagonal hover, scissor, reach, leg exchange | G1 source0–3s and4–6.5s |
| F3 |13s| Modest arch, gather, side cradle, sequential opening | Backflip fold and G1 compact pose near5s |
| F4 |12s| Lateral roll, unequal leg unfolding, travelling hover | Original RM_Flip_L rotation and leg exchange |
| F5 |15s| Gather, rising spiral, staggered unfolding, long reach | G2 gather/reach and G1 leg exchanges; jump/get-up reference |

Exact prompts, source observations, proposed beats and generated images are
private under `.agent/local/AnimationReview_20261025/BuildingBlocks`.
FloatingConcepts/Floating_Phrases_Concept.png is a visual proposal. PoleConcepts/
PoleConcepts_v1_REJECTED_ExtraArm.png has an extra arm in P4's middle panel;
that panel is rejected, not an anatomical target. Its attempted image correction
was blocked by the generator, with failure metadata retained. Neither board
demonstrates continuous movement or compatible endpoint poses.

## Connections and shared space

Design connection families before promising arbitrary order: right-hand pole
support, brief two-hand handover, released upright float and diagonal free hover.
Record pole-relative anchor height/facing, hand identity, thumb/palm orientation,
finger closure/release, root/pelvis transforms and linear/angular velocity.
Match nearby motion on both sides of a join, not only a single endpoint pose.
Keep the paired rig and corrective curves together; current clip-specific
shape curves are not a universal deformation fix for new poses.

Use a tested transition graph and short connectors where required. A rising
block cannot feed an unrelated lower anchor without descent/repositioning.
Free-floating blocks must clear held-hand constraints. A stationary grip
cannot be carried through a rotation that winds the wrist or shoulder backward.
No fixed neutral pause is required at every join: preserve momentum and limb
follow-through while matching contact state.

For two performers, evaluate swept body/garment/hair volumes through the actual
chamber and its ring obstructions, with separate sectors/heights and intentional
phase/order offsets. Mirroring or offsetting origins alone does not establish
clearance. Actual stage fit and secondary-character retargets remain untested.

## Information supporting this approach

Official Epic UE5.8 documentation consulted2026-10-26; pages have no displayed
publication date. These are tool capabilities, not evidence that they are
configured or validated in the current character.

- [Full-Body IK](https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-full-body-ik-in-unreal-engine):
  procedural reaching with per-bone stiffness, preferred bend directions and
  limits. Use calibrated rig-local axes and whole-body coordination when a
  hand target affects the torso; it does not repair skin weights or supply
  choreography. The installed5.8 `PBIK_Shared.h` exposes these fields.
- [Blend nodes / inertialization](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprint-blend-nodes-in-unreal-engine):
  pose and curve motion can continue through a transition. Epic recommends
  beginning transitions while the outgoing animation is moving and applying
  final IK after the blend. Source notifies stop with source evaluation, so
  release/grip state must not depend on a later outgoing notify. Installed
  `AnimNode_Inertialization.h` confirms the native request interface. This is
  an integration option; the current private sequence has not been replaced.
- [Motion Warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine):
  aligns root motion to named targets over authored windows. It may assist
  approach/anchor placement later; it cannot guarantee a pole grip or repair
  joint deformation. Preserve deliberate full-body rotation and check travel
  with the source, rather than flattening it into a uniform orbit.

Original FlipsAndTricks previews on their matching mannequin were rendered
front/side at3x source duration: BackFlip, ButterflyTwist and SideFlip,726
decoded frames total. They show useful fold/open and unequal-leg rotation
ideas; target-dancer fit and floating adaptation are not established.
Space Crew zero-G and social/dance names are discovery candidates only until
their full motion is inspected. No local Arise clip was verified: the owner's
Meshy recording illustrates reuse of a jump/get-up phrase, not a new download.

## Review gates for the existing routine

The isolated source-leg control has39 flagged samples in769 at15Hz: four
opening pole intersections and35 return arm/body samples, with posterior-hip
overlap in part of the return. Do not adopt that candidate or delete its useful
poses to hide the failure. Coordinate the free upper body, pelvis and travel,
then resolve remaining skin/contact defects with matched views.

Inspect complete motion front/back/side, including normal and extreme joint
poses, grip/release, limb intersections, cloth/hair and all intended joins.
Measure source coverage, pose/velocity continuity and transport separately
from surface parity. Neither numerical parity nor concept approval is whole
routine or multi-character acceptance.
