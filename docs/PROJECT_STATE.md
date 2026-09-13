# SpaceSurvival project state

**Phase 1: PARTIAL.** Updated 2026-09-13 UTC. The compiled Unreal implementation, imported content and Windows Development package exist. Automated integration and storage milestones have passed. The complete player experience and near-alpha quality requirements in [IMPLEMENT.md](../IMPLEMENT.md) and [GAME_SCOPE.md](GAME_SCOPE.md) remain unmet.

**The owner rejected the current graphics as far below acceptable.** Generated spacecraft, station and secondary art are provisional, not final selections. A substantial art replacement pass remains open; preserve the supplied Acornaut. No owner touch/feel, audio or replay-motivation result has been received.

Branch: `codex/phase1-implementation`. Draft [PR #3](https://github.com/j6sistek-ui/SpaceSurvival/pull/3) is open and unmerged. Source milestones: `1464c1df365b89492f27bfe418400dd338b098d3` for integrated gameplay/presentation/storage and `1ff473f2d37aa4c8e717fea75664eb2dd29dfa31` for encounter-label readability. Source is pushed through `1ff473f2d37aa4c8e717fea75664eb2dd29dfa31`; CI run `34741749101` passed both jobs. Final documentation commit/push is pending; final delivery must identify the final PR head and validation boundary.

## Verified evidence

| Item | Observed result | Boundary |
| --- | --- | --- |
| Toolchain | UE 5.8.2 at `C:/Program Files/EpicGames2/UE_5.8`; MSVC 14.51.36257; SDK 10.0.26100.0 | Installation/reboot complete; no missing-toolchain blocker |
| Current editor builds | Latest HUD-label rebuild succeeded in 6.91 seconds; settings rebuild in 44.82 seconds; preceding journey builds in 26.38 and 6.37 seconds | UHT/C++/link passed, including the OnStart settings correction. Nonpreferred compiler and engine-header deprecation warnings remain |
| Portable checks | 404 strict GCC 14 C++17 assertions and 404 ASan/UBSan assertions passed locally and in CI run 34741749101; source-check job also passed | CI tests the PR merge ref for source head 1ff473f; rules/source validation, not Unreal or player acceptance |
| Unreal automation | 12 succeeded, 0 succeeded with warnings, 0 failed, 0 not run | Four flight tests; accelerated ten-wave journey; death/fresh run; event/recovery/admission regressions; two Save tests |
| Ten-wave actor journey | Both stations/climaxes, both events, depot upgrade purchase, paid shield recharge and out-of-range rejection passed | 12-second waves, enlarged durability, forced objectives, fixture bootstrap and assisted positioning; no natural run or device input |
| Fresh-process storage | Preflight plus three fresh processes passed actual GameInstance Init/Suspend/Resume/PersistDeath; 475 XP, both unlocks and fresh run verified | Isolated profile; owner production save hashes unchanged. Station UI/quit interaction and interruption recovery remain separate |
| Persisted content | Full Validate target passed; saved map/classes/rosters, backdrop NoCollision, hero skeletal and station instanced-material flags checked | Asset integrity, not art approval |
| Pilot integration | Corrected-tail pilot derivative imported and wired with `A_Pilot`; original GLB/walking mesh preserved | Preview fit and limited actual-game observation; moving animation/readability still require acceptance |
| Windows package | Package 5 BuildCookRun succeeded in 67.06 seconds, exit 0; archive at `Artifacts/Windows`; 59/59 project packages and runtime Cube verified | Native New Run rendered; Wave 2 Salvage Cache label/acceptance smoke passed. Package 4 separately verified startup quality and supplies the performance identity |
| Package 5 encounter-label smoke | At 21 m, the long Salvage Cache label wrapped within dark backing near the right edge; E/A prompt legible. Native E changed text to 3 OBJECTIVES REMAIN, removed the prompt and retained live flight | Label/acceptance observation only; no objective completion or human feel claim |
| Package 4 startup settings | All 11 scalability groups applied at quality 2 on frame 0 after Game Engine Initialized | Verified OnStart correction; package 4 has separate measured performance identity |
| Actual editor-game smoke | Home shell, visible pilot and New Run flight observed; backdrop/material defects repaired | Limited smoke observation, not complete controls, balance or gameplay acceptance |
| Earlier package 3 smoke | Neutral-controls Wave 4 death: score 1,740 / 105 XP / 45 XP to Heavy Cannon; another run reset to Wave 1; relaunch retained account 105 XP / highest wave 4 / best score 1,740 / one run | Real packaged death/results/restart and account retention for that snapshot. No active-piloting, full ten-wave or owner feel result |
| Settings UI smoke | Native mouse-sensitivity click changed 1.0 to 1.2; settings file created | UI change/write observed; sensitivity readback after UI relaunch remains open |
| Early-flight performance | Package 4, Waves 1–3, 14,530 frames after five-second warmup: approximately 119.96 FPS, p99 9.119 ms, maximum 10.898 ms; zero active-flight frames above 16.667 ms | 2560×1440, DX12/SM6, quality 2, 120 FPS cap, i7-14700F/RTX 5080; neutral controls. Climaxes/stations/full-run gate remains open |

GameInstance now reapplies settings in OnStart because Init precedes engine scalability initialization. The corrected editor/package builds pass; the fresh package 4 log shows all 11 scalability groups at quality 2 on frame 0 after Game Engine Initialized. Automated suite/storage results and earlier package 3 smoke retain their recorded snapshot boundaries.

The early-flight performance sample is bound to package 4, before the later encounter-label patch. A separate 2,174.921 ms startup frame is retained in [PERFORMANCE.md](PERFORMANCE.md); no hitch-free startup or representative 60 FPS gate is claimed.

Exact test coverage, receipts and fixture limits are in [VALIDATION.md](VALIDATION.md). Package paths/hashes and reproduction commands are in [BUILD_RUN.md](BUILD_RUN.md). Older receipts retain historical results; current status comes from the latest evidence above.

## Implemented source and recent corrections

Source covers flight, combat/damage, pressure-budget Director, four hazard families, two enemies and weapons, two events, one guaranteed depot, five upgrade tracks, two utilities/contracts, wave/climax routing, station/hangar services, settings, account XP/unlocks/history and separate local save domains.

Integration fixes retain flight controls in live depot/reward menus, recover walkers leaving the deck, keep accepted events alive through their objective deadlines, normalize mouse input and preserve requested window resolution. Feedback discloses unlock milestones and complete contract terms, with restrained Acornaut captions and directional/spatial threat warnings. Separate steering sensitivity dials span 0.3–2.9.

Wave 10 now admits gravity, an asteroid and an enemy through existing budget/cap/clearance rules before random composition. Event acceptance checks objective routes before committing. The live depot offers paid shield-only recharge at 21 credits by default, with range rechecked when selected. Automated coverage verifies these bounded regressions; natural fairness and usability are still open.

Windows defaults explicitly use DX12/SM6 with DX11/SM5 fallback support. Runtime primitive dependencies under `/Engine/BasicShapes` are included in cooking. Mesh distance fields are enabled after the first rendered package exposed a Lumen warning; the latest package menu has no such warning or station checkerboard. Renderer support is not a performance result.

## Remaining implementation work

The remaining job is not limited to owner playtesting. Station 2's completion/restart boundary remains unresolved; the procedural exit, primitive vendor/station activity, synthesized audio, VFX and rejected art need further implementation/polish. Utility/contract/weapon policies, station layout and reward/menu content still require native changes rather than the intended broader content-authoring workflow. Storage has no atomic multi-slot transaction or automatic recovery manager; interruption/corrupt-data behavior needs fault-injection verification before stronger durability claims. These boundaries are detailed in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Remaining delivery gates

1. Extend packaged coverage beyond the verified HUD-label/acceptance smoke, including offline startup and storage failures; measure both climaxes, station transitions and full-run memory/frame times beyond the completed early-flight sample.
2. Complete the unchecked [hands-on playtest log](PLAYTEST_TOMORROW.md): natural ten-wave runs, keyboard/mouse and physical controller, station services, contracts/utilities, UI Save & Quit/Continue, progression, listening and immediate desire to retry.
3. Replace rejected provisional art and evaluate the supplied hero, animation, VFX, HUD, audio and hazard readability against the Hybrid direction.
4. Resolve Station 2's successful-slice/restart behavior without silently introducing later waves or changing locked progression.
5. Reconcile final evidence/docs, commit the tested snapshot, update the existing PR and leave a clean implementation branch. Do not auto-merge.

Station 2 currently remains a live services/suspension boundary. Further launch is disabled; labelled abandonment returns to a fresh hangar without death XP/history. This is an unresolved scope interpretation, not an owner-approved final-wave redesign or a completed retry-appeal gate.

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PERFORMANCE.md](PERFORMANCE.md) and [PHASE2_INTEGRATION.md](PHASE2_INTEGRATION.md).
