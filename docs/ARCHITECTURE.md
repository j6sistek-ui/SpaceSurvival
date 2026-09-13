# SpaceSurvival Phase 1 architecture

**Delivery status: PARTIAL.** This describes current source ownership, not a declaration that the integrated player experience is complete. The editor module and Windows package build, persisted content validates, the newer authored-exit source passes 13 Unreal tests without test warnings/failures, and the isolated fresh-process GameInstance storage lifecycle passes. See [VALIDATION.md](VALIDATION.md) for snapshots and limits.

## Ownership

The UE 5.8 project has one C++20 runtime module. Its deterministic domain also compiles independently as C++17 for portable tests. Durable rules live in C++; tunable hazard/enemy/pickup/encounter content lives in a reflected Data Asset.

| Owner | Responsibility and boundary |
| --- | --- |
| `SS::Session`, `Run`, `Account`, `Settings`, `Tuning` | Authoritative run phases, resource/damage rules, effective stats, economy, upgrades, utilities, contracts, score/XP/unlocks and strict codecs. No actors, rendering or file I/O |
| `USSGameInstance` / `USSStoredData` | Session lifetime, three compatible SaveGame domains, serialization verification, suspension consumption and settings application |
| `SSLocalSave` | Windows generic-backend staging, flushed byte verification and native replacement of an existing slot |
| `ASSGameMode` | Run/hangar/station orchestration, pawn possession, phase reactions, shell actions, music and warning/reaction coordination |
| `ASSPlayerController` | Keyboard/mouse and gamepad polling, menu consumption, sensitivities, inversion and hold/toggle latches |
| `ASSShip` | Swept flight, inertia, visual banking, external forces, dodge, chase camera, manual/soft aim, laser/cannon and ship audio |
| `USSSurvivalDirectorComponent` | Budget/composition, spatial admission, eligible content, guaranteed encounters and threat cleanup; it does not advance the authoritative wave timer |
| `ASSWorldBody` | Physical radius, lifetime, relative swept contact, fields, target contract, fragmentation and drops |
| `ASSEnemy`, `ASSProjectile` | Pursuer/flanker behavior, committed shot telegraph, shared environmental interaction and swept projectile delivery |
| `ASSWormholePassage` | Wave 5 ring/force presentation. GameMode/domain own phase transition |
| `ASSPickup`, `ASSEncounterBeacon` | Physical collection; explicit event/depot acceptance; actual salvage/combat objectives, timeout and reward eligibility |
| `ASSStation`, `ASSWalker` | Compact native hub/service geometry, selected ship, servicing/vendor motion; third-person movement, authored disembark/deck recovery |
| `ASSHUD` | Canvas meters, targeting, radar, encounter/docking/threat cues, subtitles, menu layout and mouse hit rectangles |
| `USSPhase1Data` / `SSContentTypes.h` | Core exposed tuning, fixed content rosters and Director configuration |

The boundaries are real but initial. GameMode still combines substantial UI/orchestration/input code, and several world families share one translation unit. Native factories, weapon/utility/contract policy, menus and station layout remain refactoring points; there is no arbitrary content-class registry.

## Run and world flow

GameInstance loads account/settings; GameMode loads `DA_Phase1`, applies its values, starts aligned music layers and opens the home hangar/shell. Starting a run validates a candidate loadout/run ID and durably invalidates an older suspension before exposing the fresh run.

Normal waves follow `Flight → Breathing → next Flight`. Hidden durations vary and breathing is bounded to 20 seconds. Wave 5 follows `Flight → Wormhole → Climax → Approach → Docking → Station`; Wave 10 starts in `Climax` and then uses the same station path. Ordinary wave changes retain world actors. Stations/death reset the encounter.

Station approach uses the same flight model; heading/distance engage final assistance inside 12 m. Validated package 7 retains the ship in the bay, hides its pilot, stops engine/collision/tick and possesses the original walker through a 1.4-second procedural exit. Resume reconstructs hub/display ship/walker from logical state. Deck escape recovery returns the walker to a safe station-local spawn. New source 442ff06 replaces that exit with A_Disembark and reuses SK_AcornautPilot at constant scale 1.5 for A_Walk. It starts from the actual pilot component transform, samples the 2.4-second clip through one actor clock, moves between 0.82–1.6 seconds, then remains planted until handing off to A_Walk at 0.308333 seconds. Sole-based fit includes UE's normal walking floor gap. Collision and movement are restored after the clip. All 13 tests pass, including contact/handoff and 30/60/144 Hz endpoint checks; package 8's guarded slowed replay and post-exit interaction passed, while natural docking/camera/motion acceptance remain open. The initial pose resets to Pilot time zero rather than blending the current idle.

Station 1 launch retains the run and starts Wave 6; package 7 exercised this after native suspension/relaunch. Station 2 remains a live boundary: AtSliceBoundary/LaunchFromStation prohibit Wave 11. Its summary shows live score/counters and reuses services/save/discard actions; closing it or rejecting departure preserves run/account. Native summary/save/relaunch passed. Discard execution and completion appeal remain open; no victory phase or completion XP was added.

World-origin rebasing occurs at large displacement. Ship docking targets, wormhole entry, relative-contact positions, walker exit endpoints and threat cue positions account for origin shifts.

## Flight, defense and input

The ship combines pitch/yaw, coupled visual banking, throttle and lateral/vertical movement. Exponential response and acceleration limits integrate through bounded movement substeps with swept collision. Boost and partial braking use domain resource/heat rules; braking retains forward movement. Dodge adds directional velocity and never grants invulnerability.

Shield absorbs first and has no automatic recharge. Hull can recover fully, with delay and different safe/danger rates. Lightweight damage-type effects and temporary effective-tier impairment preserve purchased upgrade tiers. Automated adapters verify boost/brake motion, dodge collision damage and manual weapon impacts; domain tests cover the resource rules. Natural overlapping contacts/forces, contextual recovery and feel still need gameplay verification.

Manual camera-forward aim always exists. Soft targeting checks an angular cone, range and line of sight, then partly assists firing toward a valid target. Rapid Laser uses trace damage with a visual tracer; Heavy Cannon uses a damaging physical projectile. Effective weapon/buff scaling is applied once.

PlayerController resets toggle latches when possession changes. Ordinary flight menus pause; depot/reward panels stay live and consume navigation/confirmation input separately while allowing flight controls. Mouse axis sensitivity/FOV behavior and legacy scaling were normalized after the first launch. Graphics application uses non-resolution settings so explicit development window requests remain intact. GameInstance reapplies settings in OnStart because Init runs before engine scalability initialization. Fresh package 4 verification shows all 11 scalability groups applied at quality 2 on frame 0 after engine initialization. Separate mouse/controller sensitivities are adjustable from 0.3–2.9. Synthetic movement agrees within test tolerances at 30/60/120/144 Hz; these paths are not a physical input or controller acceptance pass.

## Director and content definitions

`DA_Phase1` feeds core flight/camera/combat/wave/economy values plus:

- Six hazard entries representing four authorized families: small/medium/massive asteroids, wreckage, electrical storm and gravity.
- Two enemy entries: Pursuer and Flanker.
- Four pickup entries: credits, hull repair, shield and temporary weapon buff.
- Three encounter entries: Salvage Cache, Distress/Combat and Mobile Depot.
- Director composition, budget, timing, pressure and enemy-cap values.

Arrays are fixed-size and identities read-only in ordinary editing. Fields expose mesh names, eligibility, costs, radii, health/damage, drift, telegraph/field/fragment/drop behavior, enemy approach/shot/avoidance, and event placement/objectives. Existing native behavior types remain fixed; adding a new family needs C++/serialization integration.

Admission uses closing-speed lead time, clearance, a reserved lane, separated field envelopes and a threat cap. Shared clearance checks support both spawn points and objective route segments. Event acceptance tries nine bounded placement offsets and commits only after the route and objective positions pass; an obstructed offer stays unaccepted. Gravity influences the ship and eligible debris/enemies. Electrical fields telegraph before pulses. Enemies commit aim before discharge and share obstacles. These constraints and their regression tests are preventative, not proof of natural fairness.

Defaults offer salvage during Wave 2, exactly one depot during the Wave 3 breathing window and distress during Wave 7. Acceptance creates real caches/wreckage or attackers. Accepted beacon lifetime now spans its own objective duration; completion grants credits and a deliberate utility/weapon choice. Depot purchases additionally check live proximity and offered upgrade subset. Wave 5 prioritizes combat. Wave 10 admits gravity, a medium asteroid and an enemy through the existing budget/cap/clearance rules before random composition; blocked required admissions retry without spending their cost. It does not bypass capacity to force an unsafe spawn.

## Economy and progression

Five I–V tiers derive effective stats. Purchases improve capability/capacity without secretly repairing meters. Station repair restores durability and temporary systems. The live depot offers explicit shield-only recharge at ceil(60% of the station repair price), with a one-credit minimum: 21 credits at the default 35-credit full-service price. It restores shield only to current effective capacity, including a contract handicap; it never repairs hull or temporary systems. The domain checks a live flight phase, depot encounter eligibility, missing shield and funds; the UI adapter additionally rechecks the active depot and physical range before charging. A single utility slot supports deliberate replacement. CanPurchaseUtility/PurchaseUtility require an active station, a different valid utility and the shared 150-credit price before changing only credits/the slot. Rows use the same eligibility; commit-time checks reject stale state and duplicate purchases. Free event EquipUtility remains separate. Domain, journey and package 7 native checks cover this correction. The agile ship trades starting hull for speed, maneuverability and response.

One contract is active at a time. Pressure applies shield capacity ×0.65 and adds 0.15 pressure; Hunter counts kills. The board discloses these terms and current target/reward. Resolution at the next station pays only success; standard failure loses the reward.

Death ends the active run and awards score/XP once for a retained run identity. Level 2 (150 XP) unlocks the Heavy Cannon starting option; level 3 (450 XP) unlocks Swift. Results announce newly earned options and the next XP milestone. New runs reset run-specific power while preserving account options.

Account history retains ten completed runs, newest first, with run ID, wave, score, XP, kills, total earned credits, ship and final active weapon. Eviction preserves cumulative progression. Abandonment adds neither XP nor history.

## Local save protocol

| Slot | Payload | Behavior |
| --- | --- | --- |
| `SS_Account_v1` | ACCOUNT v2; reads v1 | Progression, tutorial flags, summary, awarded ID and bounded history |
| `SS_Settings_v1` | SETTINGS v1 | Audio, controls, accessibility and graphics preferences |
| `SS_Suspend_v1` | RUN v1 | Active station run, build/meters/counters, contract/flags, pending reward and domain RNG |

The Unreal envelope remains version 1. Strict codecs reject malformed, oversized, nonfinite, out-of-range, trailing and inconsistent data without changing the destination. Account v1 migration preserves available fields and leaves new history empty rather than inventing details.

`WriteDomain` uses Unreal's `SaveGameToMemory`, the same serialization used by `SaveGameToSlot`, and checks the deserialized envelope version, validity and payload before storage. Existing saves remain compatible: all three slot names, payload versions and envelope version are unchanged. Reads still use Unreal's generic SaveGame backend.

`SSLocalSave` accepts only those three slots on the game thread under Windows, and only when the active platform backend is the engine's exact generic singleton. Configured alternative backends fail closed. It maps `ProjectSavedDir/SaveGames/<slot>.sav` through the platform file layer, including the external write path used for the native replacement.

Each write creates a unique `<slot>.sav.<GUID>.tmp` beside the destination. It writes the serialized bytes, calls `Flush(true)`, closes the handle, reloads the staging file and compares every byte. The installed Windows file handle uses `FlushFileBuffers`; see Microsoft's [FlushFileBuffers documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers), updated 2021-10-13. Only verified staging bytes proceed to `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`. There is no pre-delete of the live slot and no `MOVEFILE_COPY_ALLOWED` fallback; source and destination are in the same directory for a same-volume replacement. See Microsoft's [MoveFileExW flag documentation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw), updated 2023-06-01.

Staging/verification/replacement failure returns an error and attempts to delete only that temporary file. A process interruption or failed cleanup can leave an orphan `.tmp`; it is neither loaded as a `.sav` slot nor automatically promoted. Successful replacement is the write acknowledgement. There is no later live-file read that could report a transient failure after the action already committed.

Suspension persists account/settings before the run. Resume validates a candidate, replaces the suspended slot with a consumed tombstone, and exposes the candidate only after replacement succeeds. Death persists account/run identity before invalidating suspension; failed persistence blocks restart. Latest/retained awarded IDs exclude stale completed suspensions. Unreadable accounts are protected from overwrite.

This protects the live file from truncation during staging; it does not provide an atomic transaction across slots, an unlimited anti-replay ledger, automatic backups or cloud conflict handling. Hardware/power-loss durability is not guaranteed by the current evidence. Station snapshots serialize logical run state, not live actor scenes.

The updated `TestSaveLifecycle.ps1` passed GameInstance Init/Suspend/Resume/PersistDeath through a preflight plus three fresh processes, including settings, once-only XP/unlocks and fresh-run reset. Real Windows deny-write/delete handles caused suspension/account replacement failures: previous bytes survived, staging was cleaned and released-lock retries succeeded. A fresh process retained exactly 475 XP and one completed run. Its GUID UserDir, backend/path guards and unchanged owner save hashes establish isolation. The writer also passed the editor build, source checks and all 12 Unreal regressions; see the [save replacement receipt](validation/2026-09-13-save-replacement.json). Process interruption/hardware-loss behavior remain unverified. Separate package 7 profiles passed native station Save & Quit/Continue at both stations, utility retention, Station 1 departure/resumed death and third-process account/unlock readback. Seeded state, assisted terminal positioning and muted audio limit these observations; see [package 7 receipt](validation/2026-09-13-windows-station-package.json).

## Presentation and authoring

`AuthorContent.py` imports original OBJ/WAV sources, the preserved rigged hero and animation derivatives, then authors canonical assets/map/data. It preserves existing authored assets and rejects partial/wrong-type imports. `ValidateContent.py` and `ValidateScene.py` provide fresh-process readback; the latter supports explicit repair of owned background collision and skeletal/instanced material usage. Actual startup found collision and material faults; corrected authoring and the full saved-asset Validate target have passed fresh-process readback.

Package 7 uses SK_AcornautPilot/A_Pilot in flight and the preserved original walking mesh/A_Walk on foot. Pilot-specific weight corrections do not close remaining tail distortion, scale handoff or motion-quality gaps. Its procedural exit, primitive Mica, generated geometry/materials and Canvas HUD remain provisional; the owner rejected the graphics.

Source milestone 442ff06 contains the imported 2.4-second A_Disembark clip and tested runtime handoff, panorama and shared HUD prompt changes. The editor build and all 13 tests pass; package 8 built and its guarded Slomo 0.1 exit/service/departure smoke passed. Panorama v1 loaded at 2048×1024/12 mips; seam/pole/readability acceptance remains open. Later starless-sky/ship changes are outside that package. A separate tail candidate is not imported or accepted. The supplied original source is preserved.

Windows defaults use DX12/SM6 with DX11/SM5 fallback. Packaging includes /Game/SpaceSurvival and /Engine/BasicShapes for runtime dependencies; distance fields support Lumen. Package 7 adds prepared-station/vendor/save/death evidence to earlier settings/event smoke. Package 4 alone supplies the measured Waves 1–3 capture; natural active piloting and representative climax/station performance remain open. See [PERFORMANCE.md](PERFORMANCE.md).

Package 8 has no app-local CRT and bundles Microsoft-signed x64 runtime 14.51.36247.0 for compiler 14.51. BundlePrerequisites selects from the actual VS installation and records UAT/link/game/runtime provenance after archive replacement. Copying, receipt generation, signature and byte identity passed; clean-PC launch remains open. See [BUILD_RUN.md](BUILD_RUN.md#runtime-prerequisite-boundary).

Music layers begin aligned and their volumes follow pressure/phase. Critical hull, predicted collision-course and environmental warnings drive explicit text/directional cues and a spatial Alarm with a six-second cooldown. Separate subtitle reactions have an 18-second cooldown and do not replace warnings. The original sound synthesis and actual mix still need listening tests.

Architecture extension work is described in [PHASE2_INTEGRATION.md](PHASE2_INTEGRATION.md). Performance risks and measurement protocol are in [PERFORMANCE.md](PERFORMANCE.md).
