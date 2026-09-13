# Phase 1 validation record

**Overall status: PARTIAL.** Updated 2026-09-13 UTC. [GAME_SCOPE.md](GAME_SCOPE.md) is authoritative design; [IMPLEMENT.md](../IMPLEMENT.md) is the execution contract. A Windows package and automated integration/storage evidence now exist. Natural ten-wave play, physical controller acceptance, final art/audio, representative performance acceptance and immediate desire to retry remain open. The owner explicitly rejected the current graphics.

## Executed evidence

| Evidence | Result | Boundary / location |
| --- | --- | --- |
| Editor builds | HUD-label rebuild: success, 6.91 seconds. Settings: 44.82 seconds. Earlier journey builds: 26.38 and 6.37 seconds | `.agent/local/EditorLabelsBuild.log`, `EditorSettingsBuild.log`, `EditorJourneyBuild3.log`, `EditorJourneyBuild4.log`; HUD-label package and native label/acceptance smoke passed |
| Portable domain checks | 404 strict GCC 14 C++17 assertions and 404 ASan/UBSan assertions passed locally and in CI | CI run `34741749101`, core job `103682494677`: two PASS 404 results; includes paid depot shield service. These do not run Unreal adapters |
| Source CI | Both jobs succeeded for source head `1ff473f2d37aa4c8e717fea75664eb2dd29dfa31`; source job `103682494581` passed all steps | PR merge ref `b81c7a54236f2a79eccc822fe3c2c88368177359`, base `0cf0ca6c17fe1febe6aa5c3640189152dcefaf96`; receipt `docs/validation/2026-09-13-source-ci.json` |
| Structural/Python checks | 20 structural checks and Python syntax passed | Source shape/syntax, not execution of every script |
| Source assets | 26 OBJ and 10 WAV formats validated; original GLB hash preserved | Source integrity, not quality approval |
| Gameplay content | Survival map and Phase 1 Data Asset authored; import receipt has no errors | `Saved/Validation/ContentImport.json`: `IMPORTED_NOT_GAMEPLAY_VALIDATED` |
| Persisted validation | Full fresh-editor Validate target passed, including latest material usage flags | `.agent/local/PersistedValidation2.log`; saved map/class/rosters, backgrounds NoCollision, hero skeletal and station instanced-material usage |
| Unreal automation | 12 succeeded; 0 succeeded with warnings; 0 failed; 0 not run | `.agent/local/JourneyFlightAutomation2.log`, `Artifacts/UnrealTests/index.json`; report created 2026-09-13 05:30:57 |
| Fresh-process storage lifecycle | Preflight plus three fresh Unreal processes succeeded; owner save hashes unchanged | `Artifacts/SaveLifecycle/6636199c7dc44237a67439999a1f9e6e/result.json`; exact scope below |
| Pilot derivative | Imported, preview-fitted and wired into actual game; original walking mesh/source retained | `ContentSource/PilotMeshFitReview.json`; preview fit and limited smoke, not animation/art acceptance |
| Editor-game smoke | Shell, visible pilot and New Run flight observed; backdrop/material defects found and repaired | Limited observation, not a complete controls or natural gameplay pass |
| Windows package | Package 5 BuildCookRun succeeded in 67.06 seconds, exit 0; 59/59 project packages and runtime Cube verified | `.agent/local/WindowsPackage5.log`; archive `Artifacts/Windows`. Current identity in [BUILD_RUN.md](BUILD_RUN.md); performance remains tied to package 4 |
| Current package 5 smoke | Native New Run rendered; Wave 2 Salvage Cache label at 21 m wrapped inside dark backing near the right edge, with legible E/A prompt. Native E accepted it; text changed to 3 OBJECTIVES REMAIN, prompt disappeared and flight continued | `Artifacts/PackageSmoke/5fedd7a0c1964923bd3937e4b159f21a`; label/acceptance smoke only, not objective completion or human feel |
| Earlier package 4 smoke | Fresh native menu/New Run at Wave 1 rendered; all 11 scalability groups applied at quality 2 on frame 0 after Game Engine Initialized | `Artifacts/PackageSmoke/57579fdb25bd449ba907598454c4fed4/Saved/Logs/PackagedFinal.log`; startup correction verified |
| Earlier package 3 smoke | Neutral-controls Wave 4 death/results, another fresh run and account retention after relaunch observed | `Artifacts/PackageSmoke/f1721585eb9544fbb8eb02181a06e528`; launch PID 23348. No full ten-wave or active-piloting claim |
| Settings UI smoke | Mouse sensitivity changed from 1.0 to 1.2 by native click; settings file created | UI value/write observed; sensitivity readback after UI relaunch remains open |
| Early-flight performance | Package 4 Waves 1–3: approximately 119.96 FPS, p99 9.119 ms, maximum 10.898 ms; zero active-flight frames above 16.667 ms | 14,530 frames after five-second warmup, 120 FPS cap; representative gate remains open. [Finalized analysis](PERFORMANCE.md), [receipt](validation/2026-09-13-final-performance.json) |
| Encounter-label readability repair | Contrast backing and bounded wrapping compiled in 6.91 seconds | Actual glow washed out the prior label; package 5 Salvage Cache backing/wrapping and native acceptance are now observed. Busiest-scene readability still requires acceptance |

Package 3 capture review found effective scalability quality 3 while the session/menu held quality 2. GameInstance Init ran before engine scalability initialization. The OnStart reapplication now builds and is verified in fresh package 4: Game Engine Initialized precedes all 11 quality-2 groups on frame 0. The 12-test suite, storage harness and earlier package 3 smoke remain evidence for their recorded snapshots; the startup correction has separate build/packaged verification.

Editor builds used UE 5.8.2, MSVC 14.51.36257 and SDK 10.0.26100.0. Newer-than-preferred compiler and engine-header C4996 warnings remain. Installation/reboot are complete.

Original hero SHA-256: `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91`. Sanitized receipts are under `docs/validation`, including `2026-09-13-integrated-unreal.json`, `2026-09-13-save-lifecycle.json`, `2026-09-13-PersistedContent.json` and `2026-09-13-SceneValidation.json`. Historical receipts preserve their earlier snapshots; older assertion counts or pending states are not the current result.

The earlier four-test run included a transient-world warning. The first journey attempt crashed in a fixture controller view-target recursion; marking that controller local before possession corrected the harness. The latest complete suite passes cleanly. The first package attempt was blocked by global Live Coding; the wrapper now passes `-ubtargs=-NoHotReloadFromIDE`, and package 2 succeeded without closing the owner's unrelated editor. Its rendered launch exposed a Lumen distance-field warning; enabling mesh distance fields and cooking package 3 removed that observed warning. The latest native menu has no observed station checkerboard.

The earlier package 3 smoke displayed Wave 1 with full hull/shield and the provisional pilot. With neutral controls, it reached Wave 4 and died; Results showed score 1,740, +105 XP, account level 1 and Heavy Cannon at 150 XP with 45 XP remaining. Selecting another run produced Wave 1, 0 credits, hull 100, shield 60, boost 100, brake heat 0 and Rapid Laser. A subsequent actual relaunch retained account 105 XP, highest wave 4, best score 1,740 and one completed run without a duplicate award. This verifies a real packaged death/results/fresh-run/account-retention route for package 3, **not active piloting, natural ten-wave acceptance, earned unlocks in packaged play or retry motivation**.

The finalized performance sample used package 4 at 2560×1440, DX12/SM6, quality 2 and a 120 FPS cap on the i7-14700F/RTX 5080 PC, with neutral flight controls. It includes 15,131 active-flight frames; the reported 14,530-frame sample excludes the first five seconds. Neither raw nor trimmed flight exceeded 16.667 ms. The separate startup maximum was 2,174.921 ms; process RAM/VRAM, both climaxes, docking/stations and full-run stability remain open. These measurements precede the HUD-label patch and are not a performance pass for the later executable.

## Exact Unreal test coverage

Every test below returned **Success** in the latest 12-test report.

| Test | Executed scope |
| --- | --- |
| `SpaceSurvival.Flight.FrameRateTrajectories` | Real pawn ticks for a four-second maneuver at 30/60/120/144 Hz. Against 120 Hz: position within 25 cm, velocity within 15 cm/s, heading within 0.05 degrees at sampled seconds |
| `SpaceSurvival.Flight.BoostBrakeMovement` | Actual motion/resource drain and recharge, nonzero minimum braking speed, overheat release and cooling |
| `SpaceSurvival.Flight.DirectionalDodgeCollision` | Three requested direction cases, repeat-impulse rejection and swept wall impact that still damages shield |
| `SpaceSurvival.Flight.ManualWeaponImpacts` | Both manually triggered weapons, cooldown, laser single damage/tracer behavior, cannon travel/impact, off-axis control target and no self-hit |
| `SpaceSurvival.Integration.AcceleratedTenWaveJourney` | Actual world/Director/GameMode route through both stations and climaxes, events, upgrade choices, depot purchase, shield-only recharge and stale out-of-range action rejection |
| `SpaceSurvival.Integration.JourneyDeathAndFreshRun` | Actor death/account award/hangar and fresh in-memory run reset with disk persistence blocked |
| `SpaceSurvival.Integration.LateEventAcceptance` | Both event types accepted near offer expiry; real objective callbacks complete within the accepted deadline |
| `SpaceSurvival.Integration.StationWalkerRecovery` | Rotated hub, deck escapes/below-floor recovery, momentum reset and procedural exit |
| `SpaceSurvival.Integration.ObjectiveRouteAdmission` | Blocked route does not commit acceptance/objectives; bounded alternate placement can succeed when clear |
| `SpaceSurvival.Integration.RequiredClimaxAdmission` | Required Wave 10 gravity/asteroid/enemy composition respects budget, capacity and retry rules |
| `SpaceSurvival.Save.PayloadRoundTrip` | In-memory Unreal envelope/payload round trip |
| `SpaceSurvival.Save.PlatformDiskRoundTrip` | GUID-named QA slot write/readback/consumption and exact-slot cleanup; no production slot writes |

Flight fixtures call gameplay methods directly; they do not exercise physical mouse/gamepad polling. Actor fixtures use transient worlds and avoid GameInstance Init, with account persistence blocked. The journey uses **12-second waves, enlarged durability, forced objective completion, fixture bootstrap and assisted positioning**. Passing it establishes the exercised actor transitions and assertions, not natural pacing, fairness, human control, rendering or retry appeal.

## Fresh-process GameInstance save lifecycle

`Scripts/TestSaveLifecycle.ps1` passed with result token `6636199c7dc44237a67439999a1f9e6e`.

| Process phase | Observed result |
| --- | --- |
| Preflight, PID 21936 | Verified generic SaveGame backend and isolated directory before GameInstance Init or save writes |
| Suspend, PID 79976 | Real Init and station suspension persisted a fixture Wave 5 build, meters, credits, utility, contract, pending reward, temporary buff and settings |
| ResumeDeath, PID 18120 | Fresh Init restored/consumed the station suspension, launched Wave 6, persisted death once, awarded 475 XP / level 3 / one history entry and invalidated the dead checkpoint |
| FreshStart, PID 47644 | Another fresh Init retained account/settings and both early unlocks; new Swift/Heavy Cannon run had baseline tiers, zero credits and no utility |

The storage fixture deliberately seeds station state, 100 kills and 1,200 earned credits; it does not earn those through natural play. The harness uses a GUID `UserDir`, checks the generic backend and rejects reparse paths before writes. The receipt records `productionSaveHashesUnchanged: true` and hashes the three isolated save files. It runs preflight plus **three separate fresh Unreal processes**, not an in-memory reset.

This closes the exercised GameInstance storage lifecycle gate. It does **not** validate station menu selection, UI quit/relaunch, packaged save behavior, corrupt-account recovery, interrupted writes or subjective gameplay.

## Acceptance gate matrix

“Automated partial” means specific source/actor behavior passed under the stated fixture limits; the full player requirement remains open.

| Gate | Current evidence | Remaining closure |
| --- | --- | --- |
| Build/content/package | Compiled, persisted Validate, Windows archive and limited rendered launch passed | Broader offline/reference coverage and final artifact identity |
| Keyboard/mouse and controller | Automated partial: real movement/resource/dodge/weapon adapters | Both physical inputs, soft targeting, live menus, hold/toggle, reconnects and feel |
| Survival/damage | Domain coverage plus physical dodge collision | Full contextual recovery, field/subsystem effects and damage feedback together in natural play |
| Waves/Director/hazards/enemies | Accelerated ten-wave actor route and admission regressions passed | Natural durations, persistence, behavior distinctions, fragments/passages, fairness and readable combinations |
| Economy/upgrades/utilities | Domain and journey coverage, paid depot shield/range assertions | All I–V paths and both utilities under real affordability/replacement decisions |
| Events/depot/contracts | Event lifetime/route and journey actions passed; contract rules in domain | Natural success/failure, exactly-once depot experience and both disclosed contracts through resolution |
| Wave 5 / Station 1 | Automated wormhole/climax/docking/station route and walker recovery | Natural approach/exit/service discovery, visit duration, purchases and UI Save & Quit/Continue |
| Waves 6–10 / Wave 10 | Automated escalation route and required compound admission | Natural compound pressure/readability, arrival and services |
| Station 2/restart boundary | Services/suspension exist; further launch disabled | Resolve successful-slice/retry behavior; abandonment currently gives no XP/history |
| Death/account/unlocks/hangar | Actor death/reset, actual fresh-process storage and package 3 death/results/restart/account retention passed | Natural progression to both unlocks, complete loadout/UI route and repeatability |
| Save/settings | Actual fresh-process lifecycle/settings and package 4 startup scalability passed; native sensitivity value/write observed | UI sensitivity readback after relaunch, packaged station lifecycle, real failure/interruption recovery |
| Shell/accessibility/tutorial | Rendered packaged menu/launch/results and package 5 event-label/native-acceptance smoke; compiled controls/settings | Both-input navigation, every preference, text at all scales, learned prompts and actual audio response |
| Hybrid visuals/audio | Imported assets, fitted pilot and limited rendered smoke | **Owner rejected graphics**; major art replacement, animation/VFX/audio polish and listening/readability acceptance |
| Performance | Package 4 early-flight CPU/GPU/frame times measured; synthetic cross-rate movement agreement | Both climaxes/stations/full-run measurements, process RAM/VRAM and representative 60 FPS/higher-refresh scalability acceptance |
| Docs/Git | Independent source audit found and corrected admission/depot gaps; reconciliation in progress | Final documentation commit/push and final commit/receipt identity; source through 1ff473f is pushed with both CI jobs passing. PR remains unmerged |

Remaining implementation is distinct from human acceptance: the Station 2 boundary, authored exit/vendor/audio presentation and broader data-driven content workflow are unfinished. Storage fault/interruption behavior and representative performance also need technical verification; they are not blocked solely on owner feedback.

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
