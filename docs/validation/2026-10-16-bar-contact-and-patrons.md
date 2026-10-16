# Bar drinking contacts and existing patrons — October 16, 2026

RPT-20261015-01 and RPT-20261016-02 remain open. Normal drinks and smaller
staff-shot glasses needed different arm poses. The bar also lacked the requested
visibly drunk and permanently resting patrons. Pending owner in-game checks now
have a table in `docs/KNOWN_ISSUES.md`; those checks do not pause lead repairs.

## Saved changes

- Astra normal drinking uses `A_Waitress_DrinkStanding_RimV4`; Joy's normal
  action1 uses `A_Joy_CheersStanding_RimV3`. Three right-arm rotation tracks per
  clip bring the rim to native, head-local mouth landmarks. Existing finger
  correction, all other tracks, translations, scales and timing are preserved.
- Separate `A_Waitress_StaffShot_V1` and `A_Joy_StaffShot_V1` fit the existing
  center-preserving0.55-scale shot grip. Optional `BarShotAnimation` selects them
  only for staff breaks. The protected ambient action helper checks clip
  compatibility and uses its duration without rewriting the normal action array.
  Missing overrides retain normal clips; wrong-skeleton overrides reject a break.
- Existing Nyxar arcade and seated lounge actors use private retargets of owned
  DrunkAnimations `AS_DrunkIdle` and `AS_Laying`. The latter moves to a lounge
  corner and retains its resting loop without route/gesture/action/chatter
  overrides. Original meshes/materials and cast count remain. The prepared
  `AS_SleepingAtTheTable` retarget is not placed.

Current local map SHA-256: `5ac00104acaebc6ae83a8c4854033eafa7a284f11041e72e6c8ede6af5519d86`.
Combined editor module SHA-256: `4c9dc8eb094c5656e5ecd3bd41f1cf04fdca40c63b101d605fabfbf6a2d749ea`.
The map supersedes intermediate e58eba9e/57be5a6b and prior cebb5d83 snapshots.
All9,480 actors remain;9,479 original world transforms are unchanged, with only
the corner patron moved. The later shot-property save preserves all9,480
transforms and normal service/action/grip/character-part references exactly.
Licensed clips, rigs and map stay local. No package, release or merge is made.

## Verification

- Worktree build1 compiled gameplay but failed linking shared plug-in DLLs held
  by the owned offscreen editor. After a clean editor exit, build2 succeeds
  in2.01s. Canonical combined editor builds in37.85s, retaining wardrobe changes.
- Fresh-process save/reload verifies shot references, original normal actions,
  parts/grips, normal180–420s break interval and clean packages.
- New-build ordinary Play uses saved normal clips through595
  samples and13 native1600x900 captures: pour, bartender drink, order, collection,
  delivery, serving, shared guest drink and return.
- Two saved staff-break cycles provide664 samples and six native
  captures. Actual animation-instance readback confirms both shot clips while
  both glasses are visible. The start timer alone is accelerated for review;
  animation playback is not paused or accelerated. Missing-override fallback
  completes another cycle with331 samples and actual normal clips.
- Wrong-skeleton overrides on either character reject the break; normal Joy
  action still selects the normal clip; invalid action index leaves it playing.
- Earlier saved patron review covers403 samples,21 resting loops and4 drunk
  loops with stationary actors and finite head/pelvis transforms. Fresh-build
  service also samples both patrons; final saved patron views were inspected.
- Preservation verifies132 prior non-map files,
  including three owner saves, plus hashes of new private assets. Packages are
  clean; the editor remains owned for subsequent authorized work.
- 49 structural checks,13 source-digest tests, Python compilation, content-source
  validation and scoped clang-format22/whitespace pass. Docker's service is
  stopped; container core/sanitizer/clang-format14 confirmation belongs to CI.

Retained unsuccessful diagnostics: the first estimated mouth landmark missed
the lips and was not adopted; a signed-zero transform difference required a
numeric-equivalent reload comparison; simulation-mode camera capture stalled
and was repeated in ordinary Play; `AnimationData` did not expose the running
clip, so validation now uses the animation instance's `GetAnimationAsset`.
Existing vendor `BP_Blinds` runtime errors remain recorded, outside this change.

Private evidence: `.agent/local/Waitress_20261015/BarFinish_20261016/`, including
original backups, MouthCalibration/Rim/Shot data, PatronsReload, ShotsReload,
FinalMotion, FinalPatronMotion, FinalStaffShots, FallbackStaffShots,
ShotGuardRegression, Preservation and Review.html. No raw logs or licensed
assets are committed.

## Still open

Natural play and physical-input checks; seated shorts; broader hand/prop and
pouring polish; audible voice/laughter and mix; nearby patron interactions and
collision comfort; exterior-window composition; appearance acceptance,
representative performance and packaged review. The first patron pair is
presentation, not an intoxication or consumable-effects system. Hero/squirrel
work and held PR73 remain untouched. Lead continues these repairs while owner
checks stay logged; no acceptance is inferred from this receipt.
