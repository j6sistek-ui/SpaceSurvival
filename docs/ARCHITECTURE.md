# SpaceSurvival Phase 1 architecture

**Delivery status: PARTIAL.** This describes current source ownership, not a declaration that the integrated player experience is complete. The editor module and Windows package build, persisted content validates, 12 Unreal tests pass without test warnings/failures, and the isolated fresh-process GameInstance storage lifecycle passes. See [VALIDATION.md](VALIDATION.md) for snapshots and limits.

## Ownership

The UE 5.8 project has one C++20 runtime module. Its deterministic domain also compiles independently as C++17 for portable tests. Durable rules live in C++; tunable hazard/enemy/pickup/encounter content lives in a reflected Data Asset.

| Owner | Responsibility and boundary |
| --- | --- |
| `SS::Session`, `Run`, `Account`, `Settings`, `Tuning` | Authoritative run phases, resource/damage rules, effective stats, economy, upgrades, utilities, contracts, score/XP/unlocks and strict codecs. No actors, rendering or file I/O |
| `USSGameInstance` / `USSStoredData` | Session lifetime, three local SaveGame domains, write/readback, suspension consumption and settings application |
| `ASSGameMode` | Run/hangar/station orchestration, pawn possession, phase reactions, shell actions, music and warning/reaction coordination |
| `ASSPlayerController` | Keyboard/mouse and gamepad polling, menu consumption, sensitivities, inversion and hold/toggle latches |
| `ASSShip` | Swept flight, inertia, visual banking, external forces, dodge, chase camera, manual/soft aim, laser/cannon and ship audio |
| `USSSurvivalDirectorComponent` | Budget/composition, spatial admission, eligible content, guaranteed encounters and threat cleanup; it does not advance the authoritative wave timer |
| `ASSWorldBody` | Physical radius, lifetime, relative swept contact, fields, target contract, fragmentation and drops |
| `ASSEnemy`, `ASSProjectile` | Pursuer/flanker behavior, committed shot telegraph, shared environmental interaction and swept projectile delivery |
| `ASSWormholePassage` | Wave 5 ring/force presentation. GameMode/domain own phase transition |
| `ASSPickup`, `ASSEncounterBeacon` | Physical collection; explicit event/depot acceptance; actual salvage/combat objectives, timeout and reward eligibility |
| `ASSStation`, `ASSWalker` | Compact native hub/service geometry, selected ship, servicing/vendor motion; third-person movement and procedural disembark/deck recovery |
| `ASSHUD` | Canvas meters, targeting, radar, encounter/docking/threat cues, subtitles, menu layout and mouse hit rectangles |
| `USSPhase1Data` / `SSContentTypes.h` | Core exposed tuning, fixed content rosters and Director configuration |

The boundaries are real but initial. GameMode still combines substantial UI/orchestration/input code, and several world families share one translation unit. Native factories, weapon/utility/contract policy, menus and station layout remain refactoring points; there is no arbitrary content-class registry.

## Run and world flow

GameInstance loads account/settings; GameMode loads `DA_Phase1`, applies its values, starts aligned music layers and opens the home hangar/shell. Starting a run validates a candidate loadout/run ID and durably invalidates an older suspension before exposing the fresh run.

Normal waves follow `Flight → Breathing → next Flight`. Hidden durations vary and breathing is bounded to 20 seconds. Wave 5 follows `Flight → Wormhole → Climax → Approach → Docking → Station`; Wave 10 starts in `Climax` and then uses the same station path. Ordinary wave changes retain world actors. Stations/death reset the encounter.

Station approach uses the same flight model. The heading/distance check engages final assistance inside 12 m. On landing the physical ship remains in the bay, its pilot hides, engine/collision/tick stop, and possession changes to a walker using a 1.4-second procedural exit. Resume reconstructs the safe hub/display ship/walker from logical run state. A walker outside the finite station deck is returned to its safe station-local spawn without ending the run.

Station 1 launch retains the run and starts Wave 6. Station 2 is an unresolved live slice boundary: `AtSliceBoundary` and `LaunchFromStation` prohibit Wave 11; services/suspension remain, with labelled abandonment without death XP. This does not implement indefinite survival or establish owner approval of the interpretation.

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

Five I–V tiers derive effective stats. Purchases improve capability/capacity without secretly repairing meters. Station repair restores durability and temporary systems. The live depot offers explicit shield-only recharge at ceil(60% of the station repair price), with a one-credit minimum: 21 credits at the default 35-credit full-service price. It restores shield only to current effective capacity, including a contract handicap; it never repairs hull or temporary systems. The domain checks a live flight phase, depot encounter eligibility, missing shield and funds; the UI adapter additionally rechecks the active depot and physical range before charging. A single utility slot supports deliberate replacement. The agile ship trades starting hull for speed, maneuverability and response.

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

Writes use Unreal SaveGame plus readback comparison. Suspension persists account/settings before the run. Resume validates a candidate, writes a consumed tombstone, then exposes it. Death persists account/run identity before invalidating suspension; failed persistence blocks restart. Latest/retained awarded IDs exclude stale completed suspensions. Unreadable accounts are protected from overwrite.

There is no atomic multi-slot transaction, unlimited anti-replay ledger, automatic backup or cloud conflict policy. Station snapshots serialize logical run state, not live actor scenes. The separate `TestSaveLifecycle.ps1` harness verifies the actual GameInstance Init/Suspend/Resume/PersistDeath flow through a preflight plus three fresh processes, including settings, once-only XP/unlocks and fresh-run reset. A GUID UserDir, backend/path guards and unchanged owner save hashes establish test isolation. Station UI/quit interaction, packaged lifecycle and interrupted-write recovery remain separate gates.

## Presentation and authoring

`AuthorContent.py` imports original OBJ/WAV sources, the preserved rigged hero and animation derivatives, then authors canonical assets/map/data. It preserves existing authored assets and rejects partial/wrong-type imports. `ValidateContent.py` and `ValidateScene.py` provide fresh-process readback; the latter supports explicit repair of owned background collision and skeletal/instanced material usage. Actual startup found collision and material faults; corrected authoring and the full saved-asset Validate target have passed fresh-process readback.

The ship uses the imported `SK_AcornautPilot` derivative and seated `A_Pilot` animation. The derivative corrects pilot tail weights/fit while preserving the supplied source and original walking mesh. Walker animation uses `A_Walk`; its procedural exit, primitive Mica motion, generated geometry/materials and Canvas HUD are provisional. The owner rejected the current graphics; completed import/wiring and preview fit do not meet the commercial Hybrid quality target.

Windows defaults explicitly use DX12/SM6, with DX11/SM5 fallback support. Packaging includes `/Game/SpaceSurvival` and `/Engine/BasicShapes`; the latter supplies runtime primitive dependencies such as the station cube floor. Mesh distance fields are enabled for the Lumen configuration. Package 5 builds and renders its menu/New Run plus the backed/wrapped event label and native acceptance transition. Package 4 separately verifies startup scalability and supplies the limited Waves 1–3 performance capture. Earlier package 3 smoke records death/restart and account retention. Active piloting, climaxes/stations and representative performance remain open; see PERFORMANCE.md.

Music layers begin aligned and their volumes follow pressure/phase. Critical hull, predicted collision-course and environmental warnings drive explicit text/directional cues and a spatial Alarm with a six-second cooldown. Separate subtitle reactions have an 18-second cooldown and do not replace warnings. The original sound synthesis and actual mix still need listening tests.

Architecture extension work is described in [PHASE2_INTEGRATION.md](PHASE2_INTEGRATION.md). Performance risks and measurement protocol are in [PERFORMANCE.md](PERFORMANCE.md).
