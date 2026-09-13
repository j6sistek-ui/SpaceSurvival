# Phase 1 validation record

**Overall status: PARTIAL.** Updated 2026-09-13 UTC. [GAME_SCOPE.md](GAME_SCOPE.md) is authoritative design; [IMPLEMENT.md](../IMPLEMENT.md) is the execution contract. A Windows package and automated integration/storage evidence now exist. Natural ten-wave play, physical controller acceptance, final art/audio, representative performance acceptance and immediate desire to retry remain open. The owner explicitly rejected the current graphics.

## Executed evidence

| Evidence | Result | Boundary / location |
| --- | --- | --- |
| Editor builds | Station: 22.63/6.44 seconds; authored exit: 18.64 seconds, then corrected 5.73 seconds | Station source 6146e9f and newer exit source 442ff06 have separate receipts/logs; package 8 has guarded native exit smoke; natural animation acceptance remains open |
| Portable domain checks | 524 strict GCC 14 assertions and 524 ASan/UBSan assertions verified in CI | Run 34744692538, core job 103690318007: PASS 524 twice; local raw stdout was not retained |
| Source CI | Both jobs succeeded for source 442ff06aa88e64569155f099b2fd38a56450d11e; source job 103690318074 passed | Tested PR merge b43946d5c9207d6a68ccd403da0df04e4c31cd2d; older CI receipts retain their own historical snapshots |
| Structural/Python checks | 20 structural checks and Python syntax passed | Source shape/syntax, not execution of every script |
| Source assets | Historical station milestone validated 26 OBJ and 10 WAV formats; original GLB hash preserved | New exit/panorama source identities and persisted validation are in the authored-exit receipt; source integrity is not quality approval |
| Gameplay content | Survival map and Phase 1 Data Asset authored; import receipt has no errors | `Saved/Validation/ContentImport.json`: `IMPORTED_NOT_GAMEPLAY_VALIDATED` |
| Persisted validation | Full fresh-editor Validate target passed, including latest material usage flags | `.agent/local/PersistedValidation2.log`; saved map/class/rosters, backgrounds NoCollision, hero skeletal and station instanced-material usage |
| Package 7 Unreal automation | 12 succeeded; zero warnings/failures/not run | `.agent/local/StationFinalAutomation.log`, report 2026-09-13 06:35:50, duration 3.310 seconds |
| Authored-exit Unreal automation | All 13 succeeded; zero warnings/failures/not run | `.agent/local/ExitContactAutomation.log`, report 2026-09-13 07:11:25, duration 2.263 seconds; separate guarded package 8 render smoke below |
| Fresh-process storage lifecycle | Preflight plus three fresh Unreal processes passed, including real locked-file replacement failures/retries; owner save hashes unchanged | `Artifacts/SaveLifecycle/7ce1831d0fac419dacb90d47a1d17eec/result.json`; exact scope below |
| Character derivative | Pilot fit imported/wired; newer source reuses the derivative for exit/walk and preserves original assets | `ContentSource/PilotMeshFitReview.json` plus authored-exit receipt; tail distortion and rendered motion/art acceptance remain open |
| Editor-game smoke | Shell, visible pilot and New Run flight observed; backdrop/material defects found and repaired | Limited observation, not a complete controls or natural gameplay pass |
| Windows package | Package 8 BuildCookRun succeeded in 86.44 seconds, exit 0; all 62 project packages and Cube verified | `.agent/local/WindowsPackage8.log` and [package 8 receipt](validation/2026-09-13-windows-exit-package.json); source 442ff06. Compatible runtime bundled; clean-PC launch open. Performance remains package 4 evidence |
| Package 6 save smoke | Native settings first write, existing-file replacement, process close/relaunch readback of mouse/controller 1.2, and New Run baseline passed | Isolated profile `f6233b51c944457b9f25edfa8cba285b`; launchers 25896/61868; both closed normally, no staging files remain. No station lifecycle/feel claim |
| Earlier package 5 smoke | Native New Run rendered; Wave 2 Salvage Cache label at 21 m wrapped inside dark backing near the right edge, with legible E/A prompt. Native E accepted it; text changed to 3 OBJECTIVES REMAIN, prompt disappeared and flight continued | `Artifacts/PackageSmoke/5fedd7a0c1964923bd3937e4b159f21a`; label/acceptance smoke only, not objective completion or human feel |
| Earlier package 4 smoke | Fresh native menu/New Run at Wave 1 rendered; all 11 scalability groups applied at quality 2 on frame 0 after Game Engine Initialized | `Artifacts/PackageSmoke/57579fdb25bd449ba907598454c4fed4/Saved/Logs/PackagedFinal.log`; startup correction verified |
| Earlier package 3 smoke | Neutral-controls Wave 4 death/results, another fresh run and account retention after relaunch observed | `Artifacts/PackageSmoke/f1721585eb9544fbb8eb02181a06e528`; launch PID 23348. No full ten-wave or active-piloting claim |
| Settings UI smoke | Package 6 native Controls readback after relaunch showed mouse/controller 1.2 | Settings write/replacement/persistence passed; feel remains unverified |
| Early-flight performance | Package 4 Waves 1–3: approximately 119.96 FPS, p99 9.119 ms, maximum 10.898 ms; zero active-flight frames above 16.667 ms | 14,530 frames after five-second warmup, 120 FPS cap; representative gate remains open. [Finalized analysis](PERFORMANCE.md), [receipt](validation/2026-09-13-final-performance.json) |
| Encounter-label readability repair | Contrast backing and bounded wrapping compiled in 6.91 seconds | Actual glow washed out the prior label; package 5 Salvage Cache backing/wrapping and native acceptance are now observed. Busiest-scene readability still requires acceptance |

Package 3 capture review found effective scalability quality 3 while the session/menu held quality 2. GameInstance Init ran before engine scalability initialization. The OnStart reapplication now builds and is verified in fresh package 4: Game Engine Initialized precedes all 11 quality-2 groups on frame 0. The 12-test suite, storage harness and earlier package 3 smoke remain evidence for their recorded snapshots; the startup correction has separate build/packaged verification.

Editor builds used UE 5.8.2, MSVC 14.51.36257 and SDK 10.0.26100.0. Newer-than-preferred compiler and engine-header C4996 warnings remain. Installation/reboot are complete.

Original hero SHA-256: `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91`. Sanitized receipts are under `docs/validation`, including `2026-09-13-integrated-unreal.json`, `2026-09-13-save-lifecycle.json`, `2026-09-13-PersistedContent.json` and `2026-09-13-SceneValidation.json`. Historical receipts preserve their earlier snapshots; older assertion counts or pending states are not the current result.

The earlier four-test run included a transient-world warning. The first journey attempt crashed in a fixture controller view-target recursion; marking that controller local before possession corrected the harness. The latest complete suite passes cleanly. The first package attempt was blocked by global Live Coding; the wrapper now passes `-ubtargs=-NoHotReloadFromIDE`, and package 2 succeeded without closing the owner's unrelated editor. Its rendered launch exposed a Lumen distance-field warning; enabling mesh distance fields and cooking package 3 removed that observed warning. The latest native menu has no observed station checkerboard.

The earlier package 3 smoke displayed Wave 1 with full hull/shield and the provisional pilot. With neutral controls, it reached Wave 4 and died; Results showed score 1,740, +105 XP, account level 1 and Heavy Cannon at 150 XP with 45 XP remaining. Selecting another run produced Wave 1, 0 credits, hull 100, shield 60, boost 100, brake heat 0 and Rapid Laser. A subsequent actual relaunch retained account 105 XP, highest wave 4, best score 1,740 and one completed run without a duplicate award. This verifies a real packaged death/results/fresh-run/account-retention route for package 3, **not active piloting, natural ten-wave acceptance, earned unlocks in packaged play or retry motivation**.

The finalized performance sample used package 4 at 2560×1440, DX12/SM6, quality 2 and a 120 FPS cap on the i7-14700F/RTX 5080 PC, with neutral flight controls. It includes 15,131 active-flight frames; the reported 14,530-frame sample excludes the first five seconds. Neither raw nor trimmed flight exceeded 16.667 ms. The separate startup maximum was 2,174.921 ms; process RAM/VRAM, both climaxes, docking/stations and full-run stability remain open. These measurements precede the HUD-label patch and are not a performance pass for the later executable.

## Package 7 native station lifecycle

Package 7 exercised actual prepared-station menus and process restarts. Station 1 Save & Quit/Continue retained 1,070 credits, Hull 145 and Hunter 0/6; departure entered Wave 6. Neutral Wave 7 death awarded 510 XP and both unlocks; a third launch retained 510 XP/highest wave 7/best score 11,800/one run, with Continue disabled. Station 2 Cooling cost exactly 150 credits (1,220 to 1,070), a repeated fitted click could not charge again, and the live summary/Save & Quit/relaunch retained Cooling and the build. The discard option was displayed, not invoked.

Both station profiles seeded station state, 100 kills, upgrades, utility and contract state. Native BugItGo positioning assisted access to physical terminals, followed by Walk to restore collision; interaction used keyboard E/mouse menus and master audio was zero. All five owned launches closed normally, no staging files remained, and owner production-save hashes stayed unchanged. This is not natural arrival, service discovery, full contract/upgrade coverage, earned-unlock pacing, physical controller feel, audio or retry appeal.

[Package 7 receipt](validation/2026-09-13-windows-station-package.json) binds executable `d29e127ce4760c1f1b25d8a9210b5fd06e0af381d4825fb9cbdf9fe029d7a55b`, source 6146e9f, logs and saves. Station 1 profile: `607ec92522354437b36481ae521c3a19`. Station 2 profile: `1a8189b79eb64c918bc338dd52ea89de`. The boundary displayed ten waves/live score 14,150/100 kills/zero events/one completed contract; those counters include prepared state, not a natural ten-wave achievement.

**New source milestone:** `442ff06aa88e64569155f099b2fd38a56450d11e` adds the authored exit, panorama, HUD interaction priority and prerequisite packaging guard. After correcting the initial floor/contact failure, all 13 Unreal tests passed with zero warnings/failures/not-run cases at 07:11:25 UTC in 2.263 seconds. See the [authored-exit receipt](validation/2026-09-13-authored-exit.json). Package 8 built in 86.44 seconds and passed the guarded native exit/service/departure smoke below. Both CI jobs passed in run 34744692538 with 524 strict and 524 sanitizer assertions. Bundled-runtime copying/signature/bytes passed; clean-PC startup and natural animation/sky acceptance remain open. Later starless-sky, ship and storage-test work is excluded from this package.

Package 7 exposed overlapping service/reward prompts and retains rig/procedural-exit defects. Its signed bundled CRT is 14.50 for compiler 14.51, with no app-local CRT. Package 8 corrects the bundle to Microsoft-signed 14.51.36247.0 and verifies copy/receipt/signature/bytes; clean-PC startup remains pending. `Build.ps1 -Target Test` now rejects a stale or empty report, warnings, failures, not-run cases or any non-Success test even if Unreal exits zero. The first new authored-exit run demonstrated why this report check is necessary.

The corrected exit test sampled 203,227 skinned LOD0 vertices against the actual deck. Minimum sole clearance was −0.016462 cm at contact and −0.012915 cm at walking handoff; restoring walking produced zero actor displacement, foot displacement under 0.011 cm and matching endpoints at 30/60/144 Hz. These geometric tolerances do not establish natural animation quality. The clip starts from Pilot time zero rather than a continuous idle-pose blend, and the existing derivative still has tail distortion.

## Package 8 native exit and artifact audit

Package 8's guarded SSReviewExit replay visibly reached seated, airborne, landing and full standing poses, suppressed interaction prompts during exit, then allowed service E and departure into Wave 6. It used a prepared station profile and Slomo 0.1, restored to 1 afterward; it does not establish natural docking/camera feel. Neutral Wave 7 death then displayed score 11,800, 510 XP, level 3 and both unlocks from the seeded 100-kill fixture. The owned launch closed normally and production-save hashes remained unchanged.

Profile: `Artifacts/SaveLifecycle/f0634e884b9c49c5977a56451f299ce1`. Launcher 66840 closed normally at 07:22:50 UTC; no agent game remained. Prepared state, seeded kills, slow motion and muted audio limit the result. Prompt suppression and post-exit service interaction were observed; this is not human keyboard/controller acceptance or a natural docking sequence.

UnrealPak returned 0 and listed 2,074 rows: all 62 committed project packages by Filename, plus Engine Cube. The initial read-only audit matched all 62 source content files to commit 442ff06. `.agent/local/Package8Audit.json` retains the five artifact hashes, 45 committed source/config/script hashes, all content hashes, index/log provenance and prerequisite checks. Later starless material/scripts and storage-test edits are explicitly excluded. The index tool emitted an existing EditorSettings.ini deletion Error Code 5 warning; no retry, security interaction or owner-file repair occurred.

Panorama v1 was loaded at 2048×1024, 12 mips, BGRA8; ListTextures reported 10,944 KB. The native observation found soft/oversized star points and a weak forward nebula; seam/pole behavior and gameplay readability remain unaccepted. See the [package 8 receipt](validation/2026-09-13-windows-exit-package.json). The later starless panorama/ship candidates are outside package 8.

## Exact Unreal test coverage

All 13 tests below returned **Success** in the authored-exit report at 07:11:25 UTC. The earlier package 7 report passed the other 12 tests; it did not contain AuthoredDisembark.

| Test | Executed scope |
| --- | --- |
| `SpaceSurvival.Flight.FrameRateTrajectories` | Real pawn ticks for a four-second maneuver at 30/60/120/144 Hz. Against 120 Hz: position within 25 cm, velocity within 15 cm/s, heading within 0.05 degrees at sampled seconds |
| `SpaceSurvival.Flight.BoostBrakeMovement` | Actual motion/resource drain and recharge, nonzero minimum braking speed, overheat release and cooling |
| `SpaceSurvival.Flight.DirectionalDodgeCollision` | Three requested direction cases, repeat-impulse rejection and swept wall impact that still damages shield |
| `SpaceSurvival.Flight.ManualWeaponImpacts` | Both manually triggered weapons, cooldown, laser single damage/tracer behavior, cannon travel/impact, off-axis control target and no self-hit |
| `SpaceSurvival.Integration.AcceleratedTenWaveJourney` | Actual world/Director/GameMode ten-wave route, both stations/climaxes/events, depot upgrade/shield/range actions, live boundary state preservation and exact-price/duplicate utility purchase guards |
| `SpaceSurvival.Integration.JourneyDeathAndFreshRun` | Actor death/account award/hangar and fresh in-memory run reset with disk persistence blocked |
| `SpaceSurvival.Integration.LateEventAcceptance` | Both event types accepted near offer expiry; real objective callbacks complete within the accepted deadline |
| `SpaceSurvival.Integration.StationWalkerRecovery` | Rotated hub, deck escapes/below-floor recovery and momentum reset |
| `SpaceSurvival.Integration.AuthoredDisembark` | Real imported clip, pilot-to-walker transform/scale, sampled contact/deck clearance, movement/collision restoration and 30/60/144 Hz endpoints; no native visual-quality claim |
| `SpaceSurvival.Integration.ObjectiveRouteAdmission` | Blocked route does not commit acceptance/objectives; bounded alternate placement can succeed when clear |
| `SpaceSurvival.Integration.RequiredClimaxAdmission` | Required Wave 10 gravity/asteroid/enemy composition respects budget, capacity and retry rules |
| `SpaceSurvival.Save.PayloadRoundTrip` | In-memory Unreal envelope/payload round trip |
| `SpaceSurvival.Save.PlatformDiskRoundTrip` | GUID-named QA slot write/readback/consumption and exact-slot cleanup; no production slot writes |

Flight fixtures call gameplay methods directly; they do not exercise physical mouse/gamepad polling. Actor fixtures use transient worlds and avoid GameInstance Init, with account persistence blocked. The journey uses **12-second waves, enlarged durability, forced objective completion, fixture bootstrap and assisted positioning**. Passing it establishes the exercised actor transitions and assertions, not natural pacing, fairness, human control, rendering or retry appeal.

## Fresh-process GameInstance save lifecycle

`Scripts/TestSaveLifecycle.ps1` passed the staged-save writer and real Windows failure/retry cases with result token `7ce1831d0fac419dacb90d47a1d17eec`. The earlier token `6636199c7dc44237a67439999a1f9e6e` remains a historical baseline. See [replacement receipt](validation/2026-09-13-save-replacement.json).

| Process phase | Observed result |
| --- | --- |
| Preflight, PID 23588 | Verified generic SaveGame backend and isolated directory before GameInstance Init or save writes |
| Suspend, PID 70016 | Real Init and station suspension persisted a fixture Wave 5 build, meters, credits, utility, contract, pending reward, temporary buff and settings |
| ResumeDeath, PID 34336 | Fresh Init restored/consumed the station suspension, launched Wave 6, persisted death once, awarded 475 XP / level 3 / one history entry and invalidated the dead checkpoint |
| FreshStart, PID 51120 | Another fresh Init retained account/settings and both early unlocks; new Swift/Heavy Cannon run had baseline tiers, zero credits and no utility |

The storage fixture deliberately seeds station state, 100 kills and 1,200 earned credits; it does not earn those through natural play. The harness uses a GUID `UserDir`, checks the generic backend and rejects reparse paths before writes. The receipt records `productionSaveHashesUnchanged: true` and hashes the three isolated save files. It runs preflight plus **three separate fresh Unreal processes**, not an in-memory reset.

ResumeDeath additionally held real Windows read handles denying both write and delete sharing on the isolated suspension/account destinations. Each attempted replacement failed with feedback, preserved every previous byte, cleaned its staging file, and retained the correct in-memory state. Releasing the handles allowed both retries; FreshStart verified exactly 475 XP and one completed run. Owner production-save hashes remained unchanged.

This closes the exercised GameInstance lifecycle and locked-destination failures/retries. That specific harness does not click station UI; the separate package 7 section records native station menus/quit/relaunch. Corrupt-account recovery, forced interruption, disk-full/short writes, staged-readback faults and hardware loss remain unverified.

## Acceptance gate matrix

“Automated partial” means specific source/actor behavior passed under the stated fixture limits; the full player requirement remains open.

| Gate | Current evidence | Remaining closure |
| --- | --- | --- |
| Build/content/package | Package 8 built; 62 project packages/Cube, committed hashes and compatible signed runtime verified; guarded exit smoke passed | Clean-PC/offline startup and later milestone coverage; native smoke is fixture-assisted |
| Keyboard/mouse and controller | Automated partial: real movement/resource/dodge/weapon adapters | Both physical inputs, soft targeting, live menus, hold/toggle, reconnects and feel |
| Survival/damage | Domain coverage plus physical dodge collision | Full contextual recovery, field/subsystem effects and damage feedback together in natural play |
| Waves/Director/hazards/enemies | Accelerated ten-wave actor route and admission regressions passed | Natural durations, persistence, behavior distinctions, fragments/passages, fairness and readable combinations |
| Economy/upgrades/utilities | 524-assertion domain coverage, journey depot guards and native Cooling/duplicate checks | All I–V paths and both utilities under natural affordability/replacement decisions |
| Events/depot/contracts | Event lifetime/route and journey actions passed; contract rules in domain | Natural success/failure, exactly-once depot experience and both disclosed contracts through resolution |
| Wave 5 / Station 1 | Automated climax/docking/exit; native package 7 station save/relaunch and package 8 slowed exit/service/departure | Natural approach/camera/animation, discovery/visit duration and complete service/contract walkthrough |
| Waves 6–10 / Wave 10 | Automated escalation route and required compound admission | Natural compound pressure/readability, arrival and services |
| Station 2/restart boundary | Native summary/vendor/Save & Quit/Continue retained state; no Wave 11 | Discard transaction and completion/retry acceptance; no completion XP awarded |
| Death/account/unlocks/hangar | Actor/storage tests, package 3 ordinary death/restart, package 7 resumed death and account/unlock readback | Natural progression to both unlocks and full loadout/retry appeal; package 7 includes 100 seeded kills |
| Save/settings | Fresh-process locked-file retries, package 6 sensitivity readback and package 7 station UI save/relaunch passed | Interruption/corrupt-data recovery, remaining preferences and physical sensitivity feel |
| Shell/accessibility/tutorial | Rendered packaged menu/launch/results and package 5 event-label/native-acceptance smoke; compiled controls/settings | Both-input navigation, every preference, text at all scales, learned prompts and actual audio response |
| Hybrid visuals/audio | Imported assets, fitted pilot and limited rendered smoke | **Owner rejected graphics**; major art replacement, animation/VFX/audio polish and listening/readability acceptance |
| Performance | Package 4 early-flight CPU/GPU/frame times measured; synthetic cross-rate movement agreement | Both climaxes/stations/full-run measurements, process RAM/VRAM and representative 60 FPS/higher-refresh scalability acceptance |
| Docs/Git | Source 442ff06 pushed with both CI jobs passing, 13 local Unreal passes and package 8 audit | Later worktree and final documentation identity pending; PR unmerged |

Remaining implementation is distinct from human acceptance: continuous exit/vendor/audio presentation, rejected art and broader content tuning need completion/verification. Compatible-runtime bundling passed; clean-PC verification remains open. Station 2 has an exercised live summary/save path; discard and completion appeal remain open. Storage faults/interruption and representative performance also need technical verification; these are not blocked solely on owner feedback.

The fixed roster remains two weapons/enemies/utilities/events/contracts and four hazard families. No multiplayer, Steamworks, cloud, inventory or later authored progression was added.

## Reproduce checks

From the repository root, using the engine/tooling described in [BUILD_RUN.md](BUILD_RUN.md):

```powershell
./Scripts/TestCore.ps1
./Scripts/Format.ps1 -Check
python Scripts/CheckProject.py
python -m compileall -q Scripts ContentSource
python ContentSource/ValidateSources.py
./Scripts/Build.ps1 -Target Editor
./Scripts/Build.ps1 -Target Content
./Scripts/Build.ps1 -Target Validate
./Scripts/Build.ps1 -Target Test
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'
./Scripts/Build.ps1 -Target Package
```

Record the source/build identity and actual result. Local logs/reports/packages are ignored; concise sanitized delivery receipts belong under `docs/validation`.

## Required hands-on protocol

No owner hands-on pass has been received. Follow the single sequential [PLAYTEST_TOMORROW.md](PLAYTEST_TOMORROW.md) log, keyboard/mouse first and physical controller second. Every checkbox remains unchecked despite the automated successes.

Record date, commit/build/hash, device/settings, expected versus observed behavior and evidence. Complete the natural two-block route, both stations, all scoped weapons/upgrades/utilities/events/contracts, live depot shield service and range rejection, settings, UI suspension/Continue, ordinary and resumed death, unlocks and fresh-run reset. Include the current Station 2 boundary friction.

Inspect animation/camera/feet, warning direction and non-color meaning, pickups, all UI scales and overlapping sounds. Follow [PERFORMANCE.md](PERFORMANCE.md) for measured performance. After death and the available boundary, record whether another run is immediately appealing and why. No automated count, package success or asset preview answers that question.
