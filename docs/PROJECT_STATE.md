# SpaceSurvival project state

**Phase 1: PARTIAL.** Updated 2026-09-13 UTC. The compiled Unreal implementation, imported content and Windows Development package exist. Automated integration and storage milestones have passed. The complete player experience and near-alpha quality requirements in [IMPLEMENT.md](../IMPLEMENT.md) and [GAME_SCOPE.md](GAME_SCOPE.md) remain unmet.

**The owner rejected the current graphics as far below acceptable.** Generated spacecraft, station and secondary art are provisional, not final selections. A substantial art replacement pass remains open; preserve the supplied Acornaut. No owner touch/feel, audio or replay-motivation result has been received.

Branch: `codex/phase1-implementation`. Draft [PR #3](https://github.com/j6sistek-ui/SpaceSurvival/pull/3) is open and unmerged. Package 8 binds to `442ff06aa88e64569155f099b2fd38a56450d11e`; both CI jobs passed in run `34744692538`. Package 7 station save/vendor/account evidence remains historical at source 6146e9f; later uncommitted work does not inherit package 8's acceptance.

**New source milestone:** `442ff06aa88e64569155f099b2fd38a56450d11e` adds the authored exit, panorama, HUD interaction priority and prerequisite packaging guard. After correcting the initial floor/contact failure, all 13 Unreal tests passed with zero warnings/failures/not-run cases at 07:11:25 UTC in 2.263 seconds. See the [authored-exit receipt](validation/2026-09-13-authored-exit.json). Package 8 built in 86.44 seconds and passed the guarded native exit/service/departure smoke below. Both CI jobs passed in run 34744692538 with 524 strict and 524 sanitizer assertions. Bundled-runtime copying/signature/bytes passed; clean-PC startup and natural animation/sky acceptance remain open. Later starless-sky, ship and storage-test work is excluded from this package.

## Verified evidence

| Item | Observed result | Boundary |
| --- | --- | --- |
| Toolchain | UE 5.8.2 at `C:/Program Files/EpicGames2/UE_5.8`; MSVC 14.51.36257; SDK 10.0.26100.0 | Installation/reboot complete; no missing-toolchain blocker |
| Editor builds | Station builds: 22.63 and 6.44 seconds; authored-exit builds: 18.64 and corrected 5.73 seconds | Source compiled; package 8 has a guarded slowed exit smoke, with natural presentation acceptance open. Nonpreferred compiler and engine-header warnings remain |
| Portable checks | 524 strict GCC 14 assertions and 524 ASan/UBSan assertions verified in CI run 34744692538; source job passed | Source 442ff06, tested merge b43946d5c9207d6a68ccd403da0df04e4c31cd2d; local raw domain stdout was not retained |
| Package 7 Unreal automation | 12 succeeded, zero warnings/failures/not run; 3.310 seconds at 06:35:50 UTC | Includes Station 2 summary/departure state preservation and exact-price/duplicate utility checks. Later authored-exit suite separately passed all 13 tests |
| Ten-wave actor journey | Both stations/climaxes, both events, depot upgrade purchase, paid shield recharge and out-of-range rejection passed | 12-second waves, enlarged durability, forced objectives, fixture bootstrap and assisted positioning; no natural run or device input |
| Fresh-process storage | Actual Init/Suspend/Resume/PersistDeath and real locked-file failure/retry passed; 475 XP/both unlocks/fresh run verified | Isolated profile, production hashes unchanged. Package 7 adds separate native station UI evidence; interruption remains open |
| Persisted content | Full Validate target passed; saved map/classes/rosters, backdrop NoCollision, hero skeletal and station instanced-material flags checked | Asset integrity, not art approval |
| Character integration | Pilot derivative/A_Pilot retained; newer source uses the same derivative at scale 1.5 for A_Disembark/A_Walk, preserving original assets | Automated pose/contact/handoff passed; tail distortion and native animation/readability acceptance remain open |
| Windows package | Package 8 BuildCookRun succeeded in 86.44 seconds, exit 0; 62 project packages plus Engine Cube verified | Source 442ff06; bundled Microsoft runtime 14.51.36247.0 signature/bytes match the selected VS installation. Clean-PC launch remains open |
| Package 5 encounter-label smoke | At 21 m, the long Salvage Cache label wrapped within dark backing near the right edge; E/A prompt legible. Native E changed text to 3 OBJECTIVES REMAIN, removed the prompt and retained live flight | Label/acceptance observation only; no objective completion or human feel claim |
| Package 4 startup settings | All 11 scalability groups applied at quality 2 on frame 0 after Game Engine Initialized | Verified OnStart correction; package 4 has separate measured performance identity |
| Actual editor-game smoke | Home shell, visible pilot and New Run flight observed; backdrop/material defects repaired | Limited smoke observation, not complete controls, balance or gameplay acceptance |
| Earlier package 3 smoke | Neutral-controls Wave 4 death: score 1,740 / 105 XP / 45 XP to Heavy Cannon; another run reset to Wave 1; relaunch retained account 105 XP / highest wave 4 / best score 1,740 / one run | Real packaged death/results/restart and account retention for that snapshot. No active-piloting, full ten-wave or owner feel result |
| Settings UI smoke | Package 6 clicks saved mouse/controller 1.2; normal close/relaunch displayed both 1.2 | Isolated settings replacement/readback, not physical comfort |
| Early-flight performance | Package 4, Waves 1–3, 14,530 frames after five-second warmup: approximately 119.96 FPS, p99 9.119 ms, maximum 10.898 ms; zero active-flight frames above 16.667 ms | 2560×1440, DX12/SM6, quality 2, 120 FPS cap, i7-14700F/RTX 5080; neutral controls. Climaxes/stations/full-run gate remains open |

GameInstance now reapplies settings in OnStart because Init precedes engine scalability initialization. The corrected editor/package builds pass; the fresh package 4 log shows all 11 scalability groups at quality 2 on frame 0 after Game Engine Initialized. Automated suite/storage results and earlier package 3 smoke retain their recorded snapshot boundaries.

The early-flight performance sample is bound to package 4, before the later encounter-label patch. A separate 2,174.921 ms startup frame is retained in [PERFORMANCE.md](PERFORMANCE.md); no hitch-free startup or representative 60 FPS gate is claimed.

Exact test coverage, receipts and fixture limits are in [VALIDATION.md](VALIDATION.md). Package paths/hashes and reproduction commands are in [BUILD_RUN.md](BUILD_RUN.md). Older receipts retain historical results; current status comes from the latest evidence above.

Package 7 exercised actual prepared-station menus and process restarts. Station 1 Save & Quit/Continue retained 1,070 credits, Hull 145 and Hunter 0/6; departure entered Wave 6. Neutral Wave 7 death awarded 510 XP and both unlocks; a third launch retained 510 XP/highest wave 7/best score 11,800/one run, with Continue disabled. Station 2 Cooling cost exactly 150 credits (1,220 to 1,070), a repeated fitted click could not charge again, and the live summary/Save & Quit/relaunch retained Cooling and the build. The discard option was displayed, not invoked.

Both station profiles seeded station state, 100 kills, upgrades, utility and contract state. Native BugItGo positioning assisted access to physical terminals, followed by Walk to restore collision; interaction used keyboard E/mouse menus and master audio was zero. All five owned launches closed normally, no staging files remained, and owner production-save hashes stayed unchanged. This is not natural arrival, service discovery, full contract/upgrade coverage, earned-unlock pacing, physical controller feel, audio or retry appeal. See the [package 7 receipt](validation/2026-09-13-windows-station-package.json).

Package 8's guarded SSReviewExit replay visibly reached seated, airborne, landing and full standing poses, suppressed interaction prompts during exit, then allowed service E and departure into Wave 6. It used a prepared station profile and Slomo 0.1, restored to 1 afterward; it does not establish natural docking/camera feel. Neutral Wave 7 death then displayed score 11,800, 510 XP, level 3 and both unlocks from the seeded 100-kill fixture. The owned launch closed normally and production-save hashes remained unchanged.

Package 8 loads panorama v1 at 2048×1024 with 12 mips (BGRA8, ListTextures reported 10,944 KB). The observed stars were soft/oversized and the forward nebula weak; seams/poles and flight readability remain unaccepted. See the [package 8 receipt](validation/2026-09-13-windows-exit-package.json). Its artifact audit binds 45 committed source/config/script hashes and 62 content hashes to source 442ff06; later worktree edits are excluded.

## Implemented source and recent corrections

Source covers flight, combat/damage, pressure-budget Director, four hazard families, two enemies and weapons, two events, one guaranteed depot, five upgrade tracks, two utilities/contracts, wave/climax routing, station/hangar services, settings, account XP/unlocks/history and separate local save domains.

Integration fixes retain flight controls in live depot/reward menus, recover walkers leaving the deck, keep accepted events alive through their objective deadlines, normalize mouse input and preserve requested window resolution. Feedback discloses unlock milestones and complete contract terms, with restrained Acornaut captions and directional/spatial threat warnings. Separate steering sensitivity dials span 0.3–2.9.

Wave 10 now admits gravity, an asteroid and an enemy through existing budget/cap/clearance rules before random composition. Event acceptance checks objective routes before committing. The live depot offers paid shield-only recharge at 21 credits by default, with range rechecked when selected. Automated coverage verifies these bounded regressions; natural fairness and usability are still open.

Windows defaults explicitly use DX12/SM6 with DX11/SM5 fallback support. Runtime primitive dependencies under `/Engine/BasicShapes` are included in cooking. Mesh distance fields are enabled after the first rendered package exposed a Lumen warning; the latest package menu has no such warning or station checkerboard. Renderer support is not a performance result.

## Remaining implementation work

The remaining job is not limited to owner playtesting. The authored exit has automated contract coverage and a guarded slowed native smoke; natural docking/camera and continuous motion quality remain open. Primitive vendor activity, synthesized audio, VFX, panorama and rejected art need further implementation/acceptance. Utility/contract/weapon policies, station layout and reward/menu content remain mostly native. The prerequisite helper's archive replacement, provenance receipt, signature and byte checks passed in package 8; clean-PC launch remains pending. Storage interruption, disk-full/short-write and corrupt-data behavior remain unverified. Station 2 now has a live summary with direct services/save/discard choices; save/relaunch passed, while discard and completion/retry acceptance remain open. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Remaining delivery gates

1. Validate later sky/ship/storage changes as a new milestone. Extend coverage to natural docking/exit, sky seam/pole/readability, clean-PC/offline startup, Station 2 discard and storage faults; measure both climaxes, station transitions and full-run memory/frame times.
2. Complete the unchecked [hands-on playtest log](PLAYTEST_TOMORROW.md): natural ten-wave runs, keyboard/mouse and physical controller, station services, contracts/utilities, UI Save & Quit/Continue, progression, listening and immediate desire to retry.
3. Replace rejected provisional art and evaluate the supplied hero, animation, VFX, HUD, audio and hazard readability against the Hybrid direction.
4. Evaluate the implemented Station 2 live summary/save/discard handoff and retry appeal without introducing later waves or changing locked progression.
5. Reconcile final evidence/docs, commit the tested snapshot, update the existing PR and leave a clean implementation branch. Do not auto-merge.

Station 2 remains a live services/suspension boundary. Its summary and Save & Quit/relaunch passed native checks; disclosed discard gives no death XP/history. No formal victory, completion XP or owner-approved resolution of indefinite-run/slice semantics is implied.

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PERFORMANCE.md](PERFORMANCE.md) and [PHASE2_INTEGRATION.md](PHASE2_INTEGRATION.md).
