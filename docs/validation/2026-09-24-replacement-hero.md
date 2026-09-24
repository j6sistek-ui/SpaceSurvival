# Replacement squirrel integration — 2026-09-24

The repaired game at `C:/Users/j6sis/.codex/worktrees/flight-loop-reset/SpaceSurvival` now selects the replacement for the existing **Squirrel** identity. This is the repaired gameplay checkout, separate from the original authoring checkout; Content is shared. The old packaged executable and itch payload have not changed.

The candidate has 76,623 triangles, 69 bones, seven tail joints and 180 lightweight fur cards. The rigid backpack and existing suit textures are retained. Import normalization preserves the geometry in centimeters with unit root scale: the original FBX imported with root scale100, which the retargeter removed and thereby shrank animated poses. The derived FBXs leave original sources untouched.

Eight clips combine retargeted body motion with the authored tail tracks: idle, walk, jog, run, seated pilot, takeoff, air and landing. Only tail joints are taken from the tail-only source FBXs. The optional jump set is all-or-nothing and skeleton checked; other heroes keep their previous behavior. A masked subtree layer continues the landing tail rebound while the body resumes locomotion, fading out at the end. Re-jump, hero change and disembark clear it. Movement and controls are unchanged.

## Evidence

- Repaired Editor build succeeded in43.78s. Existing UE5.8 header deprecation warnings remain.
- Two targeted native suites passed: `HeroJumpClips` and `HeroLandingTail`; zero failed, skipped or warning results. The second evaluates actual local poses to verify subtree isolation, fade and clearing.
- Native runtime grid confirmed body animation, lowered airborne tail and rigid backpack. Non-playing editor preview remained in reference pose, so it was not used as animation proof.
- The actual Survival-level pawn resolved the new mesh. The final scripted batch captured idle, walking, jumping and landing; capsule rose from80.15 to169.12cm and returned to its starting floor. Normal controller polling cancelled the first externally injected jump; disabling only that test controller tick let the real character movement execute it. This does not establish physical-input acceptance.
- First main-game capture exposed missing SkeletalMesh usage on the fur material. Enabling and saving that base-material usage removed the checkerboard fallback in the final walking/jump captures.
- Source structural checks, focused C++ formatting and Python compilation passed. Exact asset and image hashes are in the companion JSON. Private images/source FBXs are under `.agent/local/ReplacementHero` in the authoring checkout.

## Launch and remaining review

Desktop **Unreal Engine** now targets UE5.8 and the repaired `.uproject`; it previously targeted UE5.6 with no project. **Play SpaceSurvival - Current** targets the repaired `Play Development Build.cmd`. The repo also has `Open Repaired Game Editor.cmd`. The original shortcut is backed up under `Artifacts/LauncherBackups`.

Check the Squirrel wardrobe entry, walk/run, jump and land while moving. The new clips and tail continuation are implemented, but feel remains for owner review. Pilot pose/anchor compatibility is measured; a fresh boarding/cockpit visual check remains open. No full-game, packaged, performance, public release or Phase1 completion claim is made. The known station material usage warning is unchanged.

Reproduction and rollback inputs: [authoring recipe](../../Scripts/ReplacementHero/README.md). The old hero files remain intact. `Activate.py` preserves the prior tuning binary and Squirrel definition before changing the row; do not restore the whole tuning backup over later unrelated tuning edits.
