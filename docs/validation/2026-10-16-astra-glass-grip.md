# Astra drinking-hand correction — October 16, 2026

RPT-20261015-01 remains open. An uninterrupted native motion review of the saved
bar exposed Astra's right fingers curling away from the tumbler. The glass
followed its hand socket, but the fingers did not grasp it. A successful service
state cycle alone had not detected this visible defect.

## Change

The separate private `A_Waitress_DrinkStanding_GraspV2` duplicates the existing
`A_Waitress_DrinkStanding_Contact`. It reverses the added bend of the right index,
middle, ring and pinky joints: twelve rotation tracks only. Translations, scales,
other bones, timing, arm trajectory, glass grips and character physics remain.
The thumb is unchanged. The original clip is retained.

The placed Astra now uses the derivative for `DrinkAnimation` and action1.
Current private Wayfarer map SHA-256:
`cebb5d83b817523511a1863b5a784e20edeea2709a71a2d5d1ff9da17ce83854`.
This supersedes the earlier shoes/drinks snapshot `fb604de9`; those appearance
changes remain intact. This PR contains evidence only; licensed animation/map
assets remain local. Runtime source/config and the combined editor module
`0a679b4305cd961dc72cfdb67b93613b6aa2a0b0fc22a63c8b0dd9af58a690ad`
are unchanged, so no new build is warranted.

## Verification

- The original uninterrupted review captured Joy pour/drink plus Astra service:
  600 samples and 19 native 1600x900 screenshots, without pausing for stills.
- Raw native finger transforms agree with the correction input at5s. The first
  comparison incorrectly rejected equivalent opposite-sign quaternions; using
  the shortest rotation distance fixes the diagnostic, not the animation.
- CPU generation asserts every non-target bone value and every translation/scale
  remains identical. The candidate uses only the twelve new rotation tracks.
- Candidate service completes406 samples/eight screenshots. Native views show
  the fingers enclosing the tumbler rather than extending away from it.
- Saved map unload/reload verifies all9480 actor names/labels/world transforms,
  body/V16 outfit references, all grip transforms, and other action references.
  Both drinking entry points resolve to the saved derivative; packages are clean.
- A new play session uses the saved references without a clip override:
  407 samples/four screenshots, complete collection/delivery/drink/return cycle.
  The three saved drink views were inspected. Original owner save preservation
  and final process-exit checks are recorded in the private final receipt.

Two adoption-helper failures are retained. An unused separate Shorts component
is empty because the combined V16 outfit lives in Corset; the first guard now
preserves that empty value. The first save persisted DrinkAnimation but not the
nested action-array element. Explicitly assigning the edited struct back to its
array fixes that second reference; reload then confirms both. The intermediate
map is not the final identity above. Existing vendor BP_Blinds runtime errors
remain outside this bounded repair.

Private evidence: `.agent/local/Waitress_20261015/ContactReview_20261016/`, including
`Motion.json`, `CandidateMotion.json`, `SavedMotion.json`, `Adopted.json`,
`Reload.json`, `FinalPreservation.json`, original backup and `Review.html`.

## Remaining work

This repairs finger curl only. Mouth/rim alignment and full prop contacts,
paired-shot motion, seated shorts, audible dialogue/laughter, physical input,
representative performance, owner appearance acceptance and packaged review
remain open. No fluid simulation, merge or release is claimed.
