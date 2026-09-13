# Phase 1 validation record

Latest gameplay source: **35/35 Unreal tests**, zero warnings/failures/not-run at 14:39:19 UTC, Editor 12.79s. See [gameplay pass](GAMEPLAY_QUALITY.md) and [source-bound record](validation/2026-09-13-gameplay-quality.json). The prior station/sky assets are byte-identical; package/native checks remain separate.

**Phase 1: PARTIAL.** The latest integrated station/sky source built in **27.70 seconds** and passed **25 Unreal tests** at **13:43:51 UTC** (2.552166 seconds, zero warnings/failures/not-run cases). Full content authoring and fresh rendering-enabled validation passed; all build-snapshot bytes stayed unchanged. The [runtime receipt](validation/2026-09-13-sky-station-runtime.json) binds DLL `01906d3f...`, source files, logs and the rendered Station 1 journey.

This milestone adds the authored station shell with original collision/services and a complete fallback, the native 8K Milky Way sky, an on-foot HUD, and Settings asset acknowledgements. The [station regression receipt](validation/2026-09-13-station-shell-integration.json) retains the earlier 25-test build and resolved test-only channel-sentinel error. The latest rendered run reached docking, exit and Station 1; the sky was fully resident at 8192x4096 / 43,712 KiB and the hero at 2048x2048. Screenshot runs establish discrete appearance and residency, not performance or continuous animation quality. Current content has 120 project packages.

**The current audited Windows archive remains Package 11**, source `6912684223f4a93f4010cd12201aee7fb42395f3`; the newer station/sky milestone is not packaged yet. Package 11 contains 110 project packages, passed BuildCookRun and independent source/artifact checks, and has separate normal-timing Station 5 and Wave 10 performance captures. Its inner executable SHA256 is `10b9b664c9a9d7480d96412999dd9da0b33215bc423eaae77a395fde8c9ed32c`. See the [package receipt](validation/2026-09-13-windows-integrated-presentation-package.json) and [performance findings](PERFORMANCE.md). Draft PR #3 remains open and unmerged.

**Graphics remain below acceptance.** The owner clarified that the supplied Acornaut is a first-pass AI starting point: derivative topology, rigging and materials may be improved substantially. The original is retained as a reference, while three coordinated workstreams now address mesh cleanup/reduction, rigging/animation and material rendering. The current source asset has 196,920 triangles, 202,507 vertices, one 2K atlas/material and 52 joints; no reduced or newly rigged hero has been adopted yet. The next package is deferred until the character work can be integrated, avoiding another intermediate repack for presentation-only changes.

All 19 [hands-on checks](PLAYTEST_TOMORROW.md) remain unchecked. Physical keyboard/mouse/controller comfort, natural full-run balance, listening, retry appeal, clean-PC startup and representative minimum-spec performance remain open. Station 2 remains live services/save/discard with no Wave 11 or completion XP. Achievable asset and integration work continues.

## Executed evidence

| Evidence | Result | Boundary / location |
| --- | --- | --- |
| Earlier committed source/build | a 9 combined Editor passed in 32.22 seconds; 17 tests passed at 08:50:18 UTC in 2.1949746609 seconds, zero test warnings/failures/not run | Historical [contract](validation/2026-09-13-contract-tuning.json), [electrical](validation/2026-09-13-electrical-telegraph.json) and [discard](validation/2026-09-13-station2-discard.json) receipts |
| Previously pushed source CI | HEAD 2e4ad847, run 34753934432 passed; PR #3 remains draft/unmerged | Historical result; source 691 later passed CI34757004533 and documentation head dcc passed CI34758102026 |
| Package 11 source build/tests | Editor 22.40 seconds; 24 Unreal successes at 12:00:54 UTC in 2.4328885078430176 seconds, zero test warnings/failures/not run | DLL fd6c66a33b225b453745a0df96a2d1c0fcca4d5875ae0034641942d512ea1e57; `.agent/local/ChaseAim-tests.json`. Earlier this integration pass:744 strict/744ASan/UBSan, 23 structural; Package 11 subsequently built and passed artifact/native audits |
| Package 11 content | Combined authoring and 110-file byte-idempotent rerun; fresh rendering-enabled Validate passed 11:48:03 UTC | `.agent/local/VisualIntegrationContentIdempotence.json` and `VisualIntegrationValidate2.log`; first NullRHI failure lacked field shader stats, so the full check now runs with real RHI |
| Actual runtime presentation | Same Tail V2 at 1.5 scale, paired GripFit clips, all-bone snapshot handoff/contact/30-144 Hz tests; real Starter/Swift bay/flight selection and reused Electrical-Gravity-Electrical parent/radius/collision checks pass | Current 24-test suite checks actual selected assets. Historical 203227-vertex sole values remain separate numeric evidence; no natural animation/art acceptance |
| Fresh-process storage | Locked replacement/retry, eight-process staging/interruption and four-process corrupt-account protection passed | Strict GUID profiles, real Windows files/processes, owned cleanup, production hashes unchanged; detailed scopes below |
| Station 2 discard | Five fresh processes passed real account/checkpoint replacement failures, older Wave 5 checkpoint resume, actual action 51 retry and final reload | Highest wave 10, zero XP/completed runs/history, no Continue; not native UI usability or completion appeal |
| Current Windows artifact | Package 11/source 691, 87.75-second BuildCookRun; 110 project exports plus Cube, 2,171 index rows, seven archive files and compatible Microsoft-signed runtime verified | [Package receipt](validation/2026-09-13-windows-integrated-presentation-package.json); normal station/endgame captures and separate full-2K hero visual readback passed. Clean-PC startup remains open |
| Package 9 station residency | Native prepared Station 1 Continue and ListTextures showed all three deck maps at 2048x2048 (13.44 MiB total) | Repaired residency is verified; prepared state does not establish natural arrival/service/visual approval |
| Package 9 rendered endgame | 15,770 foreground frames, 40.007-second climax, 23.719-second compound actor presence, 5.006-second approach; mean 8.337 ms, p99 8.505 ms, max 8.818 ms | 1440p/DX12/quality 2/cap 120; seeded Tier V/enlarged durability/scripted controls. No representative FPS or natural fairness claim |
| Package 10 Station 5 | 16,872 total/16,871 marked foreground frames; 8.006323-second wormhole, 40.005359-second climax, 3.000141-second docking, 2.392316-second sampled exit and 15.006435-second idle | [Independent receipt](validation/2026-09-13-station-transition-performance.json): p99 8.461/max 8.8284 ms, zero >16.667 ms. Seeded/scripted; transition appearance not observed |
| Package 10 Wave 10 | 15,768 total/15,767 marked foreground frames; 40.001767-second climax, 23.727849-second compound presence, 5.003874-second approach; peak 23 threats | [Independent receipt](validation/2026-09-13-audio-rock-endgame-performance.json): p99 8.5187/max 8.8226 ms, zero >16.667 ms. Lead observed Wave 9/compound scene; no natural readability/listening/FPS acceptance |
| Earlier packaged UI/lifecycle | Package 3 death/restart/account; package 4 quality 2 startup; package 5 event label/acceptance; package 6 settings readback; package 7 prepared station saves/vendor/death; package 8 slowed exit/service/departure | Separate immutable receipts and assisted/neutral/muted limits below; not current-source full gameplay acceptance |
| Earlier flight performance | Package 4 Waves 1–3, 14,530 frames after five-second warmup: about 119.96 FPS, p99 9.119 ms, max 10.898 ms, zero above 16.667 ms | Predates later assets; startup reached 2,174.921 ms. [Performance](PERFORMANCE.md) distinguishes the later endgame fixture and measured Station 5 fixture and open natural full-run gate |

## Current integrated visual evidence

The [Station 5 audit](validation/2026-09-13-integrated-station-visuals.json) binds GUID `5b79fefe839d498880e876405b982b30`, editor-game DLL 12b8 and the earlier 23-test report. The process closed normally at 11:52:21 UTC, all 12 2560x1440 PNGs and 19 evidence-file hashes verified, all 16358 marked frames were foreground, 155 source/content entries and both runtime artifacts stayed unchanged during capture, fixture saves stayed empty and production save hashes matched. The later camera/arrival-caption correction and fd6c66 DLL are excluded.

Actual exit requests occurred at 0.008333,0.408333,0.793872,1.150664,1.486674,1.822287 and 2.350988 seconds. Only the first samples the 0.18-second blend; readback stalls overshot the intended early checkpoints. Tail/seat hide early hands, caption text obscures part of the lower body, and these perspective stills cannot measure sole contact or continuous camera/motion quality. Airborne/descent/landed/idle regions and suppression of the walking footer during exit are visible. StationIdle ListTextures reports the hero at 2048x2048/2752 KiB; earlier images have no per-image residency proof. The premature floor-arrival caption was subsequently changed, but that wording is unseen here. These diagnostic screenshots and their CSV are explicitly not a performance result.

The newer Wave 10 visual capture GUID `e45054047fc4447abfd5bc1eed698d63` closed normally with four PNGs on the tested fd6c66 DLL. The lead and independent auditor viewed hull below the reticle, with V3 fields, rocks and enemies visible together. Broad field bubbles and thin dark enemies remain quality limits. Only the Compound ListTextures snapshot establishes hero 1024x1024/704 KiB against 2048x2048/2752 KiB maximum; all three rock maps were 2048x2048 and sky 2048x1024. The later warning wording and component-only hero residency correction are excluded. The [independent endgame receipt](validation/2026-09-13-integrated-endgame-visuals.json) verifies all four images, 155 captured source/content files, both artifacts and 15,240 foreground fixture frames. This is coverage evidence, not owner acceptance, physical-control or performance.

## Historical source and package milestones

Font sourceccfc91400ca10168dba7471fa5a2f3c888a32d6e passed CI 34751987095; its native1920x1080 menu/settings/Controls 100-120% inspection is recorded in [font evidence](validation/2026-09-13-hud-font-menu.json). Candidate preservation source 0eeab8d646a07fa49cc1bb1ca8dcfd9f2a9f65d3 includes rejected Field V1. The outgoing-pilot snapshot handoff built 28.25 seconds and passed 21 tests at 10:51:12 UTC; [pose evidence](validation/2026-09-13-pilot-pose-transition.json) retains that identity. Combined enemy author/fresh validation passed 11:11 UTC; [enemy evidence](validation/2026-09-13-enemy-integration.json) retains those selections/tuning. These earlier checks do not claim the new integrated assets were packaged or owner-approved.

Historical 0fc CI 34749934317 succeeded at merge `1edad7a7bf11d2e7717086e16aa49e00c3df8022` against base `0cf0ca6c17fe1febe6aa5c3640189152dcefaf96`, jobs 103704525961/103704526074,744 strict/744ASan/UBSan. Later combat-cue tests passed 21/21 at 09:55:33 UTC before narrow layout fixes; a 6.43-second build and [native preview record](validation/2026-09-13-combat-cue-preview.json) retain their separate limits.

Historical 0fc economy/audio/Station 5 capture source compiled in 21.30 seconds. Portable checks pass 744 strict/744 sanitizer assertions, 22 structural checks and ten parser tests. The first expanded suite returned 20 Success/1 Fail: EconomyRewardBridge's manually spawned offers omitted the Director-owned seen flags, so strict run decoding correctly rejected accepted-but-unseen state. Both audio tests passed. The test now sets those actual offer prerequisites before acceptance; no runtime/codec requirement was relaxed. After a 4.71-second incremental build, the full rerun passed 21/21 at 09:29:16 UTC in 2.31878519058 seconds with zero warnings/failures/not-run cases. The first failure log is retained; its raw report and pre-correction DLL were not archived before replacement and are not claimed as retained artifacts. The initial generic material validator also rejected the three deliberately adopted asteroid materials; a narrow exact-asset/metadata/material-path exception retains all other checks and the independent geometry fingerprint validator. Fresh combined Validate passed at 09:26:42 UTC with economy defaults 12/35/90/25, encounter rewards 70/100/0, 16 sounds, adopted rock guards and repaired ship graphs. See the [audio receipt](validation/2026-09-13-audio-hooks.json) and [economy receipt](validation/2026-09-13-economy-tuning.json) for final source/DLL/report binding and the retained first-attempt limits.

Historical receipts keep their original snapshots and failure history. Both Package 10 rendered fixtures passed independent audit: [Station 5](validation/2026-09-13-station-transition-performance.json) includes the normal wormhole, climax, docking, authored exit and station idle; [Wave 10](validation/2026-09-13-audio-rock-endgame-performance.json) includes the full climax and compound threat presence. Station 5 recorded 16,872 total / 16,871 marked foreground frames (140.648611 seconds total), p99 8.461 ms and maximum 8.8284 ms. Wave 10 recorded 15,768 total / 15,767 marked foreground frames (131.473918 seconds total), p99 8.5187 ms and maximum 8.8226 ms. Neither capture has a frame above 16.667 ms. Seeded Tier V, enlarged durability and scripted controls limit these measurements; natural play, listening and final visual approval remain open. The 21-test pass remains bound to Editor DLL `d01c97e80433c17acee7711254a7639ab075fe8bbe22e96b2b85c92a9d4ef037`. UAT later relinked it to `5a9a65180bb3af68d2277ec428e1aca1136991200bd7eddd9289bf4cb8698600`; that binary is not separately claimed retested. No newer source/assets inherit Package 9 results. Natural ten-wave play, physical-device acceptance, final art/audio, clean-PC portability, representative performance and retry appeal remain open; the owner rejected the graphics and all 19 human checks remain unchecked.

Package 3 capture review found effective scalability quality 3 while the session/menu held quality 2. GameInstance Init ran before engine scalability initialization. The OnStart reapplication now builds and is verified in fresh package 4: Game Engine Initialized precedes all 11 quality-2 groups on frame 0. The 12-test suite, storage harness and earlier package 3 smoke remain evidence for their recorded snapshots; the startup correction has separate build/packaged verification.

Editor builds used UE 5.8.2, MSVC 14.51.36257 and SDK 10.0.26100.0. Newer-than-preferred compiler and engine-header C4996 warnings remain. Installation/reboot are complete.

Original hero SHA-256: `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91`. Sanitized receipts are under `docs/validation`, including `2026-09-13-integrated-unreal.json`, `2026-09-13-save-lifecycle.json`, `2026-09-13-PersistedContent.json` and `2026-09-13-SceneValidation.json`. Historical receipts preserve their earlier snapshots; older assertion counts or pending states are not the current result.

The earlier four-test run included a transient-world warning. The first journey attempt crashed in a fixture controller view-target recursion; marking that controller local before possession corrected the harness. The latest complete 24-test suite passed cleanly before the explicitly separate wording/residency builds. The first package attempt was blocked by global Live Coding; the wrapper now passes `-ubtargs=-NoHotReloadFromIDE`, and package 2 succeeded without closing the owner's unrelated editor. Its rendered launch exposed a Lumen distance-field warning; enabling mesh distance fields and cooking package 3 removed that observed warning. The latest native menu has no observed station checkerboard.

The earlier package 3 smoke displayed Wave 1 with full hull/shield and the provisional pilot. With neutral controls, it reached Wave 4 and died; Results showed score 1,740, +105 XP, account level 1 and Heavy Cannon at 150 XP with 45 XP remaining. Selecting another run produced Wave 1, 0 credits, hull 100, shield 60, boost 100, brake heat 0 and Rapid Laser. A subsequent actual relaunch retained account 105 XP, highest wave 4, best score 1,740 and one completed run without a duplicate award. This verifies a real packaged death/results/fresh-run/account-retention route for package 3, **not active piloting, natural ten-wave acceptance, earned unlocks in packaged play or retry motivation**.

The finalized performance sample used package 4 at 2560×1440, DX12/SM6, quality 2 and a 120 FPS cap on the i7-14700F/RTX 5080 PC, with neutral flight controls. It includes 15,131 active-flight frames; the reported 14,530-frame sample excludes the first five seconds. Neither raw nor trimmed flight exceeded 16.667 ms. The separate startup maximum was 2,174.921 ms. Package 9 later measured Wave 10 separately; Package 10 measured both the Station 5 transition and Wave 10 fixtures. Natural full-run stability, physical inputs and process RAM/VRAM remain open. Each measurement retains its own executable identity; later combat-cue edits are excluded.

## Package 7 native station lifecycle

Package 7 exercised actual prepared-station menus and process restarts. Station 1 Save & Quit/Continue retained 1,070 credits, Hull 145 and Hunter 0/6; departure entered Wave 6. Neutral Wave 7 death awarded 510 XP and both unlocks; a third launch retained 510 XP/highest wave 7/best score 11,800/one run, with Continue disabled. Station 2 Cooling cost exactly 150 credits (1,220 to 1,070), a repeated fitted click could not charge again, and the live summary/Save & Quit/relaunch retained Cooling and the build. The discard option was displayed, not invoked.

Both station profiles seeded station state, 100 kills, upgrades, utility and contract state. Native BugItGo positioning assisted access to physical terminals, followed by Walk to restore collision; interaction used keyboard E/mouse menus and master audio was zero. All five owned launches closed normally, no staging files remained, and owner production-save hashes stayed unchanged. This is not natural arrival, service discovery, full contract/upgrade coverage, earned-unlock pacing, physical controller feel, audio or retry appeal.

[Package 7 receipt](validation/2026-09-13-windows-station-package.json) binds executable `d29e127ce4760c1f1b25d8a9210b5fd06e0af381d4825fb9cbdf9fe029d7a55b`, source 6146e9f, logs and saves. Station 1 profile: `607ec92522354437b36481ae521c3a19`. Station 2 profile: `1a8189b79eb64c918bc338dd52ea89de`. The boundary displayed ten waves/live score 14,150/100 kills/zero events/one completed contract; those counters include prepared state, not a natural ten-wave achievement.

**Historical package 8 source milestone:** `442ff06aa88e64569155f099b2fd38a56450d11e` adds the authored exit, panorama, HUD interaction priority and prerequisite packaging guard. After correcting the initial floor/contact failure, all 13 Unreal tests passed with zero warnings/failures/not-run cases at 07:11:25 UTC in 2.263 seconds. See the [authored-exit receipt](validation/2026-09-13-authored-exit.json). Package 8 built in 86.44 seconds and passed the guarded native exit/service/departure smoke below. Both CI jobs passed in run 34744692538 with 524 strict and 524 sanitizer assertions. Bundled-runtime copying/signature/bytes passed; clean-PC startup and natural animation/sky acceptance remain open. Later starless-sky, ship and storage-test work is excluded from this package.

Package 7 exposed overlapping service/reward prompts and retains rig/procedural-exit defects. Its signed bundled CRT is 14.50 for compiler 14.51, with no app-local CRT. Package 8 corrects the bundle to Microsoft-signed 14.51.36247.0 and verifies copy/receipt/signature/bytes; clean-PC startup remains pending. `Build.ps1 -Target Test` now rejects a stale or empty report, warnings, failures, not-run cases or any non-Success test even if Unreal exits zero. The first new authored-exit run demonstrated why this report check is necessary.

The corrected exit test sampled 203,227 skinned LOD0 vertices against the actual deck. Minimum sole clearance was −0.016462 cm at contact and −0.012915 cm at walking handoff; restoring walking produced zero actor displacement, foot displacement under 0.011 cm and matching endpoints at 30/60/144 Hz. These geometric tolerances do not establish natural animation quality. The clip starts from Pilot time zero rather than a continuous idle-pose blend, and that historical derivative still has tail distortion. Later Tail V2 uses actual-runtime mesh selection in the same contact regression; thin fragments and natural motion remain unaccepted.

## Package 8 native exit and artifact audit

Package 8's guarded SSReviewExit replay visibly reached seated, airborne, landing and full standing poses, suppressed interaction prompts during exit, then allowed service E and departure into Wave 6. It used a prepared station profile and Slomo 0.1, restored to 1 afterward; it does not establish natural docking/camera feel. Neutral Wave 7 death then displayed score 11,800, 510 XP, level 3 and both unlocks from the seeded 100-kill fixture. The owned launch closed normally and production-save hashes remained unchanged.

Profile: `Artifacts/SaveLifecycle/f0634e884b9c49c5977a56451f299ce1`. Launcher 66840 closed normally at 07:22:50 UTC; no agent game remained. Prepared state, seeded kills, slow motion and muted audio limit the result. Prompt suppression and post-exit service interaction were observed; this is not human keyboard/controller acceptance or a natural docking sequence.

UnrealPak returned 0 and listed 2,074 rows: all 62 committed project packages by Filename, plus Engine Cube. The initial read-only audit matched all 62 source content files to commit 442ff06. `.agent/local/Package8Audit.json` retains the five artifact hashes, 45 committed source/config/script hashes, all content hashes, index/log provenance and prerequisite checks. Later starless material/scripts and storage-test edits are explicitly excluded. The index tool emitted an existing EditorSettings.ini deletion Error Code 5 warning; no retry, security interaction or owner-file repair occurred.

Panorama v1 was loaded at 2048×1024, 12 mips, BGRA8; ListTextures reported 10,944 KB. The native observation found soft/oversized star points and a weak forward nebula; seam/pole behavior and gameplay readability remain unaccepted. See the [package 8 receipt](validation/2026-09-13-windows-exit-package.json). The later starless panorama/ship candidates are outside package 8.

## Exact Unreal test coverage

All 24 tests below returned **Success** at 12:00:54 UTC, duration 2.4328885078430176 seconds, with zero test warnings/failures/not-run cases. This report is bound to DLL fd6c66; subsequent wording and hero-residency changes are not a repeated 24-test execution. Historical a 9/17-test and 0fc / 21-test reports retain their original source/binary identities.

| Test | Executed scope |
| --- | --- |
| `SpaceSurvival.Flight.FrameRateTrajectories` | Real pawn ticks for a four-second maneuver at 30/60/120/144 Hz. Against 120 Hz: position within 25 cm, velocity within 15 cm/s, heading within 0.05 degrees at sampled seconds |
| `SpaceSurvival.Flight.BoostBrakeMovement` | Actual motion/resource drain and recharge, nonzero minimum braking speed, overheat release and cooling |
| `SpaceSurvival.Flight.DirectionalDodgeCollision` | Three requested direction cases, repeat-impulse rejection and swept wall impact that still damages shield |
| `SpaceSurvival.Flight.ManualWeaponImpacts` | Both weapons hit an independently placed target on the settled default camera ray with SoftAimDegrees=0; cooldown, tuned laser damage/tracer behavior, cannon travel, off-axis control and no self-hit |
| `SpaceSurvival.Flight.CameraAimMuzzleObstruction` | Both weapons physically destroy real muzzle cover while the independently verified camera-visible target survives; no assist or collision immunity |
| `SpaceSurvival.Integration.AcceleratedTenWaveJourney` | Actual world/Director/GameMode ten-wave route, both stations/climaxes/events, depot upgrade/shield/range actions, live boundary state preservation and exact-price/duplicate utility purchase guards |
| `SpaceSurvival.Integration.JourneyDeathAndFreshRun` | Actor death/account award/hangar and fresh in-memory run reset with disk persistence blocked |
| `SpaceSurvival.Integration.LateEventAcceptance` | Both event types accepted near offer expiry; real objective callbacks complete within the accepted deadline |
| `SpaceSurvival.Integration.StationWalkerRecovery` | Rotated hub, deck escapes/below-floor recovery and momentum reset |
| `SpaceSurvival.Integration.AuthoredDisembark` | Actual selected Tail V2/paired clips, every-bone live Pilot 1.137s snapshot and authored brace at 0.4s, scale/CPU sole contact, world offset, collision/input handoff and 30/60/144 Hz endpoints; no native motion-quality claim |
| `SpaceSurvival.Integration.ShipPresentationSelection` | Actual Starter/Swift BeginPlay hull/pilot mount plus home/station bay switching; preserved transforms and nonblocking display collision |
| `SpaceSurvival.Integration.FieldPresentationSelection` | Actual Electrical-Gravity-Electrical reuse selects the correct mesh and MID parent, exact normalized radius and NoCollision while preserving the wormhole assets |
| `SpaceSurvival.Integration.ObjectiveRouteAdmission` | Blocked route does not commit acceptance/objectives; bounded alternate placement can succeed when clear |
| `SpaceSurvival.Integration.RequiredClimaxAdmission` | Required Wave 10 gravity/asteroid/enemy composition respects budget, capacity and retry rules |
| `SpaceSurvival.Content.UtilityDataAssetBridge` | Actual fixed-row prices/effects reach domain eligibility/payment/stats; malformed values/identities and unchanged serialized utility identity |
| `SpaceSurvival.Content.ContractDataAssetBridge` | Persisted/default/custom/malformed contract magnitudes and independent rewards map to the actual domain |
| `SpaceSurvival.Integration.ElectricalPulseCadence` | Actual field actors and material charge share pulse damage timing over interval/frame-rate combinations |
| `SpaceSurvival.Integration.ElectricalPulseBoundaries` | Final Director telegraph override, fractional overshoot and one damage pulse on a long frame |
| `SpaceSurvival.Content.EconomyDataAssetBounds` | Persisted defaults, identity-correct legacy unset migration, custom values and malformed/extreme arithmetic/codec bounds |
| `SpaceSurvival.Integration.EconomyRewardBridge` | Actual GameMode mapping, custom repair/upgrade/station menu payments, real event completion/failure/free choices and pending reward codec; assisted offer/objective setup |
| `SpaceSurvival.Integration.AudioFirstPlayMix` | Loaded muted/unmuted component gains before Play; actual initial Hangar, pressure/breathing/climax/station and live mute |
| `SpaceSurvival.Integration.SpatialThreatAudio` | Actual electrical/enemy/asteroid hooks, role overrides, bounded allocation, gain, owner and lifetime cleanup; no audio-renderer/listening assertion |
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

This closes the exercised GameInstance lifecycle and locked-destination failures/retries. That specific harness does not click station UI; the separate package 7 section records native station menus/quit/relaunch. Later bounded staging/interruption and corrupt-account protection scenarios are recorded below. Disk-full/short writes, arbitrary binary-envelope corruption, every interruption boundary and hardware loss remain unverified.

## Subsequent isolated storage failure coverage

[Eight-process storage fault validation](validation/2026-09-13-storage-faults.json) uses GUID 855cfd7fdc124eb0a1bcb97cf9c78530. Real test-owned access controls deny staging creation and readback for each of the three slots. For interruption, the parent retains a required-acknowledgement oplock until the owned writer is confirmed terminated while replacement is blocked. The old live bytes survive; fresh Init ignores the abandoned stage and retains the checkpoint. Later released-lock resume/death retries retain exactly 475 XP and one history entry. Test ACLs are restored, temporary files cleaned, owned processes gone and production hashes unchanged. Initial ACL-restoration repair history is retained; no disk-full/short-write/hardware-loss claim is made.

[Four-process corrupt-account protection](validation/2026-09-13-corrupt-account.json) uses GUID 497ffd64dd6d4699bc277fa7d7b70155. A real version-1 USSStoredData envelope contains invalid account domain text. Fresh Init protects its exact bytes, displays failure and blocks Resume, PersistAccount and actual GameMode New Run. The test manually restores its exact fixture copy; only fresh Init clears protection and accepts normal persistence. No checkpoint is consumed or XP/history awarded. Legitimate re-save may reorder Unreal custom-version headers, so exact bytes are required through protection/restoration, and logical identity after deliberate re-save. This is protection plus manual fixture restoration, not arbitrary binary corruption or a recovery/backup feature.

[Five-process Station 2 discard](validation/2026-09-13-station2-discard.json) uses GUID a 7f697ebbecb4f48bd7b318fe9756321. Actual account lock prevents discard without mutation. A checkpoint lock permits account-highest-wave 10 persistence but preserves live run/suspension. Fresh Init resumes the older Wave 5 checkpoint without reducing the durable record; actual action 51 retry reaches hangar only after successful persistence/invalidation. Final fresh Init retains highest wave 10, zero XP/completed runs/history and disabled Continue. All five processes exited; three slots, zero staging leftovers and unchanged production hashes were verified. The native packaged discard menu still needs usability acceptance.

## Acceptance gate matrix

“Automated partial” means specific source/actor behavior passed under the stated fixture limits; the full player requirement remains open.

| Gate | Current evidence | Remaining closure |
| --- | --- | --- |
| Build/content/package | 24-test integration suite, 110-asset idempotent content validation, 744/744 domain checks; Package 11/source 691 audited and both normal-timing fixtures passed | 677-file Git export and CI 34757004533 passed. Later label/residency builds retain their own identities; clean-PC/offline startup remains open |
| Keyboard/mouse and controller | Automated partial: real movement/resource/dodge/weapon adapters | Both physical inputs, soft targeting, live menus, hold/toggle, reconnects and feel |
| Survival/damage | Domain coverage plus physical dodge collision | Full contextual recovery, field/subsystem effects and damage feedback together in natural play |
| Waves/Director/hazards/enemies | Accelerated ten-wave actor route and admission regressions passed | Natural durations, persistence, behavior distinctions, fragments/passages, fairness and readable combinations |
| Economy/upgrades/utilities | a 9 641-assertion coverage, actual utility Data Asset and journey/depot/native duplicate checks; newer economy 744/744 portable and two actual engine tests passed | All I–V paths and both utilities under natural affordability/replacement decisions |
| Events/depot/contracts | Event lifetime/route/journey plus actual contract Data Asset bridge and independent reward resolution passed | Natural success/failure, exactly-once depot experience and both disclosed contracts through resolution |
| Wave 5 / Station 1 | Automated climax/docking/exit; Package 10 normal-timing rendered transition through 15-second hub idle; historical native save/relaunch and slowed exit/service/departure | Natural approach/camera/animation, discovery/visit duration and complete service/contract walkthrough; counters do not establish transition visual quality |
| Waves 6–10 / Wave 10 | Automated escalation/required admission; Package 9 and Package 10 full 40-second rendered scripted climaxes passed | Natural compound pressure/readability, Station 2 arrival and services |
| Station 2/restart boundary | Native summary/vendor/save/continue plus five-process actual discard failure/retry/reload passed; no Wave 11/XP/history | Native discard usability and completion/retry acceptance |
| Death/account/unlocks/hangar | Actor/storage tests, package 3 ordinary death/restart, package 7 resumed death and account/unlock readback | Natural progression to both unlocks and full loadout/retry appeal; package 7 includes 100 seeded kills |
| Save/settings | Locked/staging faults, blocked-replacement interruption, corrupt-domain protection and discard retries passed; native settings/station save readback | Disk-full/short-write/arbitrary binary corruption/hardware loss; remaining preferences and physical sensitivity feel |
| Shell/accessibility/tutorial | Rendered packaged menu/launch/results and package 5 event-label/native-acceptance smoke; compiled controls/settings | Both-input navigation, every preference, text at all scales, learned prompts and actual audio response |
| Hybrid visuals/audio | Imported assets, fitted pilot and limited rendered smoke | **Owner rejected graphics**; major art replacement, animation/VFX/audio polish and listening/readability acceptance |
| Performance | Package 4 early flight, Package 9 Wave 10 and Package 10 Station 5/Wave 10 fixtures measured; cross-rate movement agreement | Natural full-run/process RAM/VRAM, second-station transition and representative 60 FPS/higher-refresh acceptance; later source excluded |
| Docs/Git | Source 691 pushed; CI 34757004533 passed; PR #3 draft and unmerged; Package 11 and current performance receipts bound | New source-only station/sky candidates are not packaged or approved; all 19 human checks remain unchecked |

Remaining implementation is distinct from human acceptance: continuous exit quality, vendor/audio presentation and rejected art need completion/verification. Compatible-runtime bundling passed; clean-PC verification remains open. Station 2 has exercised summary/save and fresh-process discard protection; native usability and completion appeal remain open. Storage coverage has the bounded limits above. Package 10 Station 5 and Wave 10 receipts are finalized. Representative performance and the remaining implementation work still need closure; these are not blocked solely on owner feedback.

The fixed roster remains two weapons/enemies/utilities/events/contracts and four hazard families. No multiplayer, Steamworks, cloud, inventory or later authored progression was added.

## Reproduce checks

From the repository root, using the engine/tooling described in [BUILD_RUN.md](BUILD_RUN.md):

```powershell
./Scripts/TestCore.ps1
./Scripts/Format.ps1 -Check
python Scripts/CheckProject.py
python -m compileall -q Scripts ContentSource
python ContentSource/ValidateSources.py
python Tests/TestSourceDigests.py
python Scripts/TestFreshCheckout.py
./Scripts/Build.ps1 -Target Editor
./Scripts/Build.ps1 -Target Content
./Scripts/Build.ps1 -Target Validate
./Scripts/Build.ps1 -Target Test
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'
./Scripts/TestSaveLifecycle.ps1 -StorageFaults
./Scripts/TestSaveLifecycle.ps1 -CorruptAccount
./Scripts/TestSaveLifecycle.ps1 -Station2Discard
python Tests/TestAnalyzePerformance.py
./Scripts/Build.ps1 -Target Package
```

Record the source/build identity and actual result. Local logs/reports/packages are ignored; concise sanitized delivery receipts belong under `docs/validation`.

## Required hands-on protocol

No owner hands-on pass has been received. Follow the single sequential [PLAYTEST_TOMORROW.md](PLAYTEST_TOMORROW.md) log, keyboard/mouse first and physical controller second. Every checkbox remains unchecked despite the automated successes.

Record date, commit/build/hash, device/settings, expected versus observed behavior and evidence. Complete the natural two-block route, both stations, all scoped weapons/upgrades/utilities/events/contracts, live depot shield service and range rejection, settings, UI suspension/Continue, ordinary and resumed death, unlocks and fresh-run reset. Include the current Station 2 boundary friction.

Inspect animation/camera/feet, warning direction and non-color meaning, pickups, all UI scales and overlapping sounds. Follow [PERFORMANCE.md](PERFORMANCE.md) for measured performance. After death and the available boundary, record whether another run is immediately appealing and why. No automated count, package success or asset preview answers that question.
