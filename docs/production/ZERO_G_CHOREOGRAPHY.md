# Zero-G choreography and G/B contact review

Owner request: October 25, 2026. **RPT-20261021-01** owns animation quality,
integration and acceptance; this guide is usage/provenance, not a second task queue.

**Contact V8 is rejected.** Body rotation around a fixed hand produced unnatural
arm poses. New-library adoption is disabled. The five zero-G segments also remain
preliminary; bounded paths and endpoint checks do not accept their anatomy or
artistic quality. Current source-first baseline and removable forearm diagnostics
are documented in [the diagnostic receipt](../validation/2026-10-25-dancer-orientation-diagnostics.md).

## Open

The private native review level is
`/Game/SpaceSurvival/Licensed/ZeroGChoreography_20261025/L_ZeroG_Choreography_Review`.
It uses the existing observatory chamber dimensions and four saved customized
characters. The original workshop, observatory and production station are not
rebuilt. This is a separate inspection level, not a replacement default map.

The local motion review and editable library live in
`C:/Users/j6sis/SpaceSurvival/SourceAssets/ZeroGChoreography_20261025/`.
`Diagnostics/Review.html` shows the removable marker and sampled native evidence.
`ZeroG_and_Contact_ActionLibrary.blend` contains the rig and derivative actions;
append an action into one of the four existing character-options files and set
the scene to **60 fps**. Those complete character files and their packed artwork
remain unchanged. Do not run a 60 fps action at their older 25 fps setting.

## Five reusable zero-G segments

| Segment | Duration | Source and movement |
| --- | ---: | --- |
| Drift | 16 s | Lira IMG9451; gentle lateral/vertical suspension |
| Spiral | 16 s | Lira IMG9452; rising curled aerial shape |
| Butterfly | 14 s | Hammerhead RM_ButterflyTwist_L; slow horizontal twist |
| Inversion | 16 s | Hammerhead RM_Flip_B; descending inverted shape |
| Lateral Arc | 14 s | Hammerhead RM_Flip_L; lateral extension and roll |

Asset prefix: `A_F3_ZeroG_`. Segment files are `01_Drift` through `05_LateralArc`.
Each starts and ends in the same asymmetric hover, with stopped endpoint travel
and 2.5-second pose blends. The source acrobatics are time-remapped and filtered;
their large captured root travel is replaced by bounded authored motion.

The saved sequences use the **five individual clips**, so reorder sections without
making new animation bakes. Keep sections contiguous at their full durations.
All 25 endpoint pairings are measured; two complete 76-second orders were played
repeatedly in Unreal. This does not mean every arbitrary multi-clip order has
received a separate visual review.

- Vexa / Orbit A: Drift, Butterfly, Spiral, Inversion, Lateral Arc.
- Roxie / Orbit B: Inversion, Drift, Lateral Arc, Spiral, Butterfly.
- Jinx and Vesper also received the two orders in transient native role-swap tests.
- `OrbitA` and `OrbitB` are convenient complete-loop actions for Blender or
  single-animation playback. Prefer the editable segment sequences for staging.

## Chamber placement

The reference chamber has a 348 cm inner radius and glass from Z615 to Z1775 cm.
The two **mesh origins**, not capsule origins, are `(170,0,1080)` and
`(-170,0,1080)` cm in the inspection map. Mesh world rotation is zero; the vendor
character actor yaw is 90 degrees to compensate its mesh-relative rotation.
Keep scale at 1. The root stays in place and the pelvis carries bounded travel.

The measured body landmarks span Z918.5–1470.5 cm across the two routines. A
15 cm envelope around landmarks retains at least 50 cm to the glass; the two
envelopes retain at least 133 cm separation. These are conservative geometric
screens, with skinned multi-angle playback checked separately. Loose accessories,
new costumes, different skeleton proportions, changed origins or extreme play
rates need fresh contact review. This is authored choreography, not collision-aware
navigation, live zero-G physics or runtime avoidance.

## G1/G2 and B1/B2

The four original-name Unreal clips were already authored for F3. A second
mannequin retarget changed their proportions. Set each animation's authored
reference mesh to the actual F3 Quinn mesh; do **not** change shared skeleton
retarget modes. The two original joined routines additionally required rebuilding
from unretargeted source poses. The source GLBs and four original Blender files
remain preserved. The older 0.48-second join is retained for those original-name
routines; contact-specific derivatives remain separate.

Derived `g1_Contact`, `g2_Contact`, `G1_G2_ContactLoop`, `b1_Contact`, `b2_Contact`
and `B1_B2_GroundedLoop` use the same `A_F3_` prefix in the new library. Their
review state and exact metrics are in the dated validation receipt. A plausible
grip needs torso clearance, elbow/wrist/finger shape and continuous playback;
small wrist error alone is insufficient. The first hand-only candidate was
rejected because it pulled the torso through the pole.

## Scope and evidence

Hammerhead Flips and Tricks was already owned and installed in AFS. Sources were
hash-copied to the private authoring workbench; AFS and original Lira clips remain
unchanged. Generated FBXs/native animations do not reference AFS, M or D at runtime.
Licensed source/native art is private; the PR contains recipes and concise evidence.

Technical checks do not close James's artistic/feel acceptance. Garment simulation,
hair/material polish, normal station role/dialogue integration and packaged
performance remain distinct open work. See [validation](../validation/2026-10-25-dancer-orientation-diagnostics.md)
and the canonical [issue log](../KNOWN_ISSUES.md).
