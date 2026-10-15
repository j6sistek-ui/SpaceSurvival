# Astra social, seating, photo and controller review — October 15

Partial acceptance: implementation and bounded native checks are recorded here; physical controls, listening, appearance/contact preference and representative performance remain open in RPT-20261015-01/02. No package/upload/merge is included. This extends, rather than rewrites, the earlier [V14/service receipt](2026-10-15-waitress-bar-service.md).

## Saved native character and prop

Fresh Editor23 loads the saved Wayfarer map with Astra's selected WhitePurpleRings eye mesh, common S_AstraEyes skeleton for five presets, head attachment, colon-format Astra/Waitress tags, original body/physics and enabled post-process. All 193 protected original character files retain their baseline hashes. Fifty-five seat markers exist, 51 enabled; four plant-covered contacts are disabled. The eight-exchange bar bank retains its production 180–420 second interval, not the accelerated test interval.

The microwave door faces the working aisle at yaw -90. The save preserved 9,472 other actor transforms, and a fresh process verifies its saved orientation. A prior comparison mistakenly included Python struct memory addresses; that assertion failed before save, was corrected to numeric transforms, and the original map backup remains private. Early rotation trials on a static PIE actor did not move it; those images are not final evidence. `ActualMinus9000000.png` shows the corrected door.

## Runtime evidence

- Five original service cases: 439 samples; menu-free GameMode order/sit-dismiss: 161 samples (earlier receipt).
- Two complete autonomous staff-break cycles use different exchanges and return Astra to service. Both drink clips start together. Sampled body/corset and eye/head discrepancies are 0 cm. Far-player, occupied crew seat and guest-interruption/return/glass guards pass; full 1600×900 drink captures reviewed.
- Hero sit/stand checks pass for armchair, sofa, bench and bar stool. Blocked approach/exits reject safely; disabled and occupied seats are rejected. Universal seating on arbitrary furniture/hero rigs is not claimed.
- Side chat reviewed at 1600×900 with long history and long-word wrapping beneath the compass. It holds 12 utterances and hides after inactivity. Other UI scales remain owner checks.
- Separate Astra and existing Joy voice references resolve by name. Thirty-four cached lines pass word-coverage transcription. Unreal ran with NoSound; this does not establish audible playback, pleasant delivery or expressive laughter quality. The supplied text files are prompts, not LoRA weights.
- Photo mode freezes world time and Astra's animation, still moves its camera, stops at a real bar wall, clamps a long unobstructed step to 4,000 cm, saves a nonempty HUD-free PNG, and restores the prior pawn/view/pause state. The pad anchor is farther than 4,000 cm from the bar; a market viewpoint inside the radius is captured. The market fixture positions the camera explicitly within the bound and is not a natural complete fly-through. Failed pad-settle assertions are retained: the walking pawn moved back to safe ground, and a second path hit collision before reaching the radius. Neither failure was evidence of a broken range clamp.

Evidence files are in `.agent/local/Waitress_20261015`: `FinalReload.json`, `SocialChat/Result.json`, `SocialGuardsFull/Result.json`, `Seating/Runtime2`, `Seating/Guards`, `Voice/Verified.json`, `PhotoMode`, and `MicrowaveReview`. [Sanitized results](2026-10-15-astra-social-ui.json) retain exact saved paths and measured values. Ordinary screenshots retain native pixels, not generated repairs.

## Builds and checks

CanonicalBuild12 passed in 12.68 seconds; CanonicalBuild13 passed in 39.95 seconds with photo mode, bumper navigation and interaction legend. Isolated WorktreeBuild6 passed in 41.24 seconds before the additional raw photo-input assertions. Build11's private-member access error was repaired; it also encountered an editor DLL lock, and later builds run only after the owned editor exits. Existing engine deprecation warnings, BP_Blinds null-material and vendor Humanoid-reference diagnostics remain out of scope.

CanonicalBuild14 passed in 5.49 seconds; isolated WorktreeBuild7 passed in 32.88 seconds. `SpaceSurvival.UI.StationControllerShortcuts` passes one test with zero failures, skipped tests or warnings. It exercises simulated raw bumper/tab wrap, LB+D-pad suppression, photo entry/pause and B exit/resume. The earlier title-menu fixture passed assertions with two station-placement warnings and was not counted as a clean gate. The final shortcut fixture avoids spawning an unauthored station. Physical-controller use and the interaction legend's rendered layout still need review. Final source checks pass: 49 structural checks, Python compilation, 26 source meshes/17 WAVs, scoped clang-format22 (23 C++ files), and documentation consistency. Docker's daemon is stopped; container core checks and clang-format14 await CI. No native/editor check here establishes a release, every animation contact or 60 FPS performance.


## Shorts owner rejection and partial repair

The owner rejected V14's front waistband and hem. Rest-geometry review found uneven vertical displacement introduced by earlier fitting. V15 restored the purchased silhouette but clipped the body; V16 adds horizontal clearance/rebinding without moving the hem vertically. Native idle, walking and carrying close views improve. Seven V16 pose views and three additional high-angle seated views were inspected at 1600×900. Sitting still rides the shorts up, so this is **partial**, not visual acceptance. A weight-only trial and three seated corrective-shape trials did not produce acceptable results; none were imported or adopted. No runtime morph logic was added.

V16 is saved on the existing Blueprint and actor. The original body, corset, UVs/material slots, eyes, identity and 180–420 second staff-break interval remain. The save preserves 193 original character-file hashes and 9,472 other actor transforms. Backups and failed candidates remain under `.agent/local/Waitress_20261015/WaistRepair`; `AdoptionPlan.json`, `Adopted.json`, `NativeV16` and `SeatedAboveV16` are the local evidence. Fresh Editor25 reload passes: both saved outfit references are V16, with identity, selected eyes, original physics/post-process, seats and staff-break interval preserved; `WaistRepair/Reload.json` is the receipt.

The morph-target study used Epic's [FBX morph-target documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-morph-target-pipeline-in-unreal-engine), accessed October 15, 2026. Support for morph import did not establish that these garment candidates fit, and none is reported as fixed.
