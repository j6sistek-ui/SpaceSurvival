# Phase 1 validation record

Recorded 2026-09-13 UTC. Overall status: **PARTIAL**.

`GAME_SCOPE.md` remains the authoritative design and `../IMPLEMENT.md` remains the execution contract. The portable domain has executed test evidence. The Unreal game has not opened, compiled, imported its content, packaged, or been played in this environment. Consequently none of the Unreal gameplay acceptance gates below is closed. Source implementations and deterministic tests are not evidence of flight feel, controller operation, collision correctness, Director fairness, art quality, audio quality, or a compelling restart loop.

## Evidence and limits

| Evidence | Result | What the result establishes |
| --- | --- | --- |
| Fresh container compile of `SurvivalCore.cpp` and `CoreTests.cpp`, `gcc:14-bookworm`, C++17, `-O2 -Wall -Wextra -Wpedantic -Werror` | **VERIFIED DOMAIN**: lead recorded successful compile and `PASS 266 portable gameplay-domain assertions` | The final recorded domain snapshot, including the Wave 10 malformed-state test, compiles without enabled warnings and satisfies its assertions. This excludes all Unreal translation units. |
| AddressSanitizer + UndefinedBehaviorSanitizer build, C++17, `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer` | **VERIFIED DOMAIN**: second `PASS 266`, no sanitizer diagnostic | The exercised portable test paths produced no reported address/undefined-behavior failure. This does not establish exhaustive memory safety or Unreal runtime correctness. |
| `Tests/CoreTests.cpp` | Eight executed domain test groups in the recorded container run | Damage/recovery; boost/brake/dodge/utilities; wave lifecycle/economy; all upgrade tiers/repair; contracts; death/progression/reset; versioned payloads/invalid input; deterministic and defensive inputs. |
| `ContentSource/source_validation.json` | **VERIFIED SOURCE FORMATS ONLY**: 26 OBJ meshes and 10 PCM WAVs recorded valid | OBJ indices, normals, finite geometry and nonzero triangle areas; WAV format/headroom/loop boundaries; supplied GLB hash. These checks do not run Unreal import, rendering, animation, collision, or audio playback. |
| Content specialist's source checks, detailed in `CONTENT_PIPELINE.md` | Five Python scripts passed syntax compilation; generation matched across 39 source/manifest files | Python syntax and deterministic generation only. Source geometry preview is not a gameplay screenshot. |
| `Scripts/CheckProject.py`; Python `compileall` for scripts/source generators | **VERIFIED SOURCE ONLY**: 19 structural checks passed; syntax compilation passed | Project/module/config/header structure and source syntax only; no UHT, Unreal compilation, engine Python API execution or rendering. |
| Supplied hero source | Preserved SHA-256 `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91` | The supplied `model-rigged.glb` was not replaced. Skeletal import and visible piloting remain unverified. |
| Unreal tooling inspection | **ENVIRONMENT BLOCKED** | A directory named `UE_5.8` contains plugin material, but the inspected engine installation lacks usable editor binaries, UnrealBuildTool, Build.bat/RunUAT and the Windows C++/SDK toolchain needed for this project. A directory name is not an installed, runnable engine. |
| Docker availability | Earlier daemon connection failures were superseded by the successful portable container run | Docker now supplies portable test tooling. It does not supply the licensed Unreal Windows build environment. No host system packages were installed for these checks. |
| Unreal save automation | **UNVERIFIED UNREAL** | `SSAutomationTests.cpp` registers `SpaceSurvival.Save.PayloadRoundTrip`. It has not run; it covers memory serialization when run, not the entire disk/crash/resume transaction. |
| Packaged Windows artifact | **NOT PRODUCED** | No executable, cooked content, stage directory or claimed package checksum is available. |
| `Scripts/Build.ps1 -Target Editor` | **BLOCKED AT PREFLIGHT** | Failed because `C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat` is absent. Compilation did not start; this is not a compiler test result. |
| Human experience and performance | **UNVERIFIED UNREAL** | No keyboard/mouse play, controller play, ten-wave playthrough, station walkthrough, listening test, CPU/GPU capture or 60 FPS result was obtained. |

The recorded final test image manifest is `sha256:7d300ba9cd9bec9e2df64005aafc07449f50be0866835ac650614386bc181f3b`; its `gcc:14-bookworm` base is `sha256:5e927c284bf55a7dc796262e311a0703344f62f41f5621eb56843111b1d37e15`. These identify the domain test environment, not a Windows game package. The working tree was still being reconciled when this record was written; bind delivery claims to the lead's final commit and preserve the test outputs.

The absent engine/toolchain concretely blocks executing Unreal build/package/playback checks here. Unfinished art, animation, NPC presentation, tutorial behavior and content authoring depth are implementation/quality gaps; they are not described as impossible because an engine is missing.

## Reproduce the available checks

Run from the repository root with Docker Desktop's Linux engine running:

```powershell
./Scripts/TestCore.ps1
```

The wrapper rebuilds the image before executing it. Its direct equivalent is:

```powershell
docker build --progress plain -t spacesurvival-core-checks .
docker run --rm spacesurvival-core-checks
```

With existing Python 3, source checks are:

```powershell
python Scripts/CheckProject.py
python ContentSource/ValidateSources.py
```

The presence of the check commands is not itself a pass record. Preserve the full output and exact commit SHA for release-candidate runs. Run engine steps using `Scripts/Build.ps1 -Target Editor`, then `Content`, `Test` and `Package` with the actual full `-EngineRoot`; consult the build instructions and `CONTENT_PIPELINE.md`. `-NullRHI` automation cannot establish graphics or performance results.

## IMPLEMENT.md gate matrix

In this matrix, **DOMAIN VERIFIED / UNREAL OPEN** means relevant deterministic assertions executed while the integrated requirement remains unverified. **SOURCE ONLY / UNREAL OPEN** means there is an implementation path but no executed gameplay evidence. **BLOCKED** identifies a concrete environment dependency, not acceptance.

Source map abbreviations:

- **Core**: `Source/SpaceSurvival/Domain/SurvivalCore.h/.cpp`; tests in `Tests/CoreTests.cpp`.
- **Ship**: `Private/SSShip.cpp`; **Controller/GameMode**: `Private/SSGameMode.cpp`.
- **World**: `Private/SSWorldActors.cpp` and `Public/SSWorldActors.h`.
- **Station**: `Private/SSStation.cpp`; **HUD**: `Private/SSHUD.cpp`.
- **Save**: `Private/SSGameInstance.cpp`; **UE automation**: `Private/SSAutomationTests.cpp`.
- **Content/Tuning**: `Scripts/AuthorContent.py`, `ContentSource/`, `Public/SSPhase1Data.h`.

All abbreviated source paths are beneath `Source/SpaceSurvival/` unless a different root is shown.

### Build gate

| Required criterion | Status | Source/evidence and remaining verification |
| --- | --- | --- |
| Unreal project opens cleanly | BLOCKED | `SpaceSurvival.uproject`, module/targets/config and content authoring script exist; open the real project and retain its log. |
| C++ project compiles cleanly | BLOCKED | Portable Core compiles; UHT, reflected headers, Unreal adapters, generated classes and linking have not compiled. |
| Required maps/assets resolve | BLOCKED | Canonical `/Game/SpaceSurvival/` paths are declared; real `.uasset`/`.umap` import and packaged reference resolution remain open. |
| Packaged Windows build succeeds | BLOCKED | `Scripts/Build.ps1 -Target Package` provides BuildCookRun routing. Run it after content import, launch the resulting executable outside Editor, and record artifact path/hash. |

### Flight and survival/damage gates

| Required criterion | Status | Source/evidence and remaining verification |
| --- | --- | --- |
| Keyboard/mouse works | SOURCE ONLY / UNREAL OPEN | Controller key polling, mouse steering and station movement; test all bindings and menu focus physically. |
| Controller works | SOURCE ONLY / UNREAL OPEN | Stick, trigger, shoulder, face-button and menu bindings; test actual device, dead zones, trigger toggles, sensitivity and reconnect behavior. |
| Pitch/yaw, banking, throttle, inertia | SOURCE ONLY / UNREAL OPEN | Ship substepped steering, acceleration-limited velocity and visual banking; assess weight and response at several frame rates. |
| Rechargeable boost | DOMAIN VERIFIED / UNREAL OPEN | Core `TickFlight`; Ship applies speed change. Verify meter/feedback, exhaustion and recharge together. |
| Partial brake, heat and overheat | DOMAIN VERIFIED / UNREAL OPEN | Core heat/lockout/recovery; Ship minimum forward speed and brake factor. Verify braking cannot park indefinitely. |
| Directional dodge without invulnerability | DOMAIN VERIFIED / UNREAL OPEN | Core cooldown and damage-during-dodge assertions; Ship directional impulse. Validate all directions against actual obstacles. |
| Readable high-speed chase camera | SOURCE ONLY / UNREAL OPEN | Ship spring arm, limited boost pullback/FOV and impact shake. Check pilot visibility, clipping and hazard lead time. |
| Shield-first damage, no automatic shield regeneration | DOMAIN VERIFIED / UNREAL OPEN | Core overflow/energy/recovery tests; Ship/World source damage adapters. Verify collisions, projectiles and pickups agree. |
| Hull recovers to full; slow under danger, fast after delay | DOMAIN VERIFIED / UNREAL OPEN | Core recovery tests; GameMode determines danger from active threats. Validate actual danger classification, interruption and station repair value. |
| Wave damage scaling and lightweight damage types | DOMAIN VERIFIED / UNREAL OPEN | Core scaling/helpers and kinetic/energy/electrical/gravity/thermal rules; verify actual source damage, force and presentation. |
| Rare temporary subsystem impairment | DOMAIN VERIFIED / UNREAL OPEN | Core effective-tier reduction and repair preserve purchased tiers. Verify frequency, warning, duration and handling impact. |
| Waves 1–10 complete in order | DOMAIN VERIFIED / UNREAL OPEN | Core tests traverse two five-wave blocks and stations. No physical run has traversed them. |
| Hidden variable duration and bounded breathing | DOMAIN VERIFIED / UNREAL OPEN | Core deterministic RNG/timers and ≤20-second bound; HUD omits countdown. Verify pressure reduces naturally while flight continues. |
| Director pressure escalates | SOURCE ONLY / UNREAL OPEN | Core multiplier and World pressure budget/composition. Test resulting encounter density, behavior and variety, not just numeric growth. |
| No routine unavoidable spawn states | SOURCE ONLY / UNREAL OPEN | World safe-lane, lead-time and active-threat limits. Requires observed survival across varied headings, speed, upgrades and compound pressure. |
| Selected hazards persist over wave boundaries | SOURCE ONLY / UNREAL OPEN | World normal Configure avoids clearing the world; station/death ResetEncounter clears actors. Verify hazard persistence and no transition hitches. |

### Content gate

| Required criterion | Status | Source/evidence and remaining verification |
| --- | --- | --- |
| Four hazard families | SOURCE ONLY / UNREAL OPEN | World asteroids, wreckage, electrical storms and gravity. Test each independently and overlapping. |
| Asteroid sizes/destruction/fragmentation | SOURCE ONLY / UNREAL OPEN | Small/medium destruction, bounded debris and drops; massive obstacles. Verify physical radii, weapon response, fragments and dangerous aftermath. |
| Wreckage authored passages | SOURCE ONLY / UNREAL OPEN | World passage placement and generated debris geometry. Verify navigable clearance and destructible/non-destructible distinction. |
| Electrical warning/secondary effect | SOURCE ONLY / UNREAL OPEN | World warning rings, delayed electrical hazard and Core interference. Verify warning lead time and control consequences. |
| Gravity affects ship and debris | SOURCE ONLY / UNREAL OPEN | World force application and Ship external-force handling. Verify controllability and readable direction/strength. |
| Both enemy archetypes | SOURCE ONLY / UNREAL OPEN | Pursuer and Flanker behavior in World. Verify distinct behavior, hazard interaction and behavioral escalation rather than inflated health. |
| Both weapon classes; manual aim plus soft assistance | DOMAIN VERIFIED / UNREAL OPEN | Core weapon stats/replacement/tier effects; Ship trace/projectile firing and target assistance. Verify rates, damage, line-of-sight and manual aim. |
| Both utilities | DOMAIN VERIFIED / UNREAL OPEN | Core Vector Thrusters/Overdrive Cooling tests; GameMode deliberate fitting/reward menus. Verify input, meter and handling effects; one slot replaces the previous utility. |
| Both optional events | SOURCE ONLY / UNREAL OPEN | World explicit acceptance/objectives/failure and GameMode reward choice. Verify approach does not accept, success/failure is correct and rewards cannot repeat. |
| Exactly one guaranteed mobile depot | SOURCE ONLY / UNREAL OPEN | World Wave 3 breathing offer, three randomized upgrade offers/deal and saved `depotSeen`; GameMode checks live proximity and offered track before purchase. Verify one encounter per run/resume. |
| Both contract types | DOMAIN VERIFIED / UNREAL OPEN | Core modifier/objective success, failure, exclusivity and resolution tests; station terms/acceptance. Verify gameplay handicap and counted objectives. |
| Pickups and risk/value placement | SOURCE ONLY / UNREAL OPEN | World credits/repair/rare shield/buff actors and GameMode collection; generated distinct silhouettes. Verify collection radii, risk, rarity and feedback. |
| Credits and 2–3 meaningful station purchases | DOMAIN VERIFIED / UNREAL OPEN | Default survival baseline yields 425 credits by Station 1; three initial 130-credit upgrades leave 35 repair credits. This arithmetic is tested; competent-player economy, depot spending, rewards and Station 2 choices are not balanced by playtest. |

### Climax and station gates

| Required criterion | Status | Source/evidence and remaining verification |
| --- | --- | --- |
| Wave 5 wormhole → combat → station | DOMAIN VERIFIED / UNREAL OPEN | Core Flight→Wormhole→Climax→Approach order; World wormhole passage and GameMode spawning/routing. Verify actual pull, traversal, hostile arrival and continuity. |
| Wave 10 gravity + asteroid storm + enemy pressure | SOURCE ONLY / UNREAL OPEN | Core climax routing; World's compound encounter configuration. Verify all pressures actually overlap with readable, survivable escape space. |
| Both climaxes lead cleanly into stations | DOMAIN VERIFIED / UNREAL OPEN | Core approach/docking/station states; GameMode actor/pawn transitions. Verify no stranded pawn, duplicate actors or lost run state. |
| Player approach and assisted landing | SOURCE ONLY / UNREAL OPEN | Heading-aligned station, corridor, 12 m assistance threshold and Ship docking interpolation. Test arbitrary pitch/yaw, low/high speed and aborted approach. |
| Acornaut exits correctly | SOURCE ONLY / UNREAL OPEN; PRESENTATION GAP | Ship destruction/pawn possession creates the walker. This is an instantaneous change, not a finished exit animation. Validate character mesh, orientation, floor contact and camera. |
| All five upgrades through I–V | DOMAIN VERIFIED / UNREAL OPEN | Core purchase/cost/tier bounds and effective-stat tests; guaranteed station panel. Verify installed changes in actual ship behavior and repeated purchases. |
| Repair | DOMAIN VERIFIED / UNREAL OPEN | Core paid hull/shield repair and subsystem reset; station console. Verify funds, feedback and no unnecessary charge at full service. |
| Contract board | DOMAIN VERIFIED / UNREAL OPEN | Core rules and GameMode disclosed terms; Station physical terminal. Verify one active contract and no unreachable Station 2 contract. |
| Save & Quit | DOMAIN VERIFIED / UNREAL OPEN | Core payloads; Save disk wrapper and station terminal. Requires closing/relaunching the packaged executable and restoring the same run. |
| Relaunch | DOMAIN VERIFIED / UNREAL OPEN | Station 1 starts Wave 6 with current build; Station 2 intentionally stops authored flight. See boundary decision below. |
| Walk/run/interact and compact 1–3-minute visit | SOURCE ONLY / UNREAL OPEN | Walker input/animation hooks and diegetic station services. Requires physical walkthrough and timing. |
| Vendor/NPC, servicing, machinery, announcements and story detail | SOURCE ONLY / UNREAL OPEN; QUALITY GAPS | Mica text/vendor interaction, service arm, ambience and beacon log exist. No separate skeletal NPC/vendor character or recorded spoken station announcements have been integrated. |
| Optional station interaction/reward | SOURCE ONLY / UNREAL OPEN | Beacon restoration grants 25 credits once per station via `stationRewardClaimed`; verify repeat/restore behavior. |

### Progression and save gates

| Required criterion | Status | Source/evidence and remaining verification |
| --- | --- | --- |
| Death ends run | DOMAIN VERIFIED / UNREAL OPEN | Core fatal damage/EndRun and active flag. Verify every physical damage source and removal of flight control. |
| Score and XP awarded once | DOMAIN VERIFIED / UNREAL OPEN | Core score, XP, run ID idempotency and duplicate-EndRun tests. Verify Results and durable account write after actual death. |
| Account progression persists | DOMAIN VERIFIED / UNREAL OPEN | Account codec round trip; Save write/readback wrapper. Requires process restart and disk-error checks. |
| Second starting weapon unlock | DOMAIN VERIFIED / UNREAL OPEN | Level 2 at 150 XP; tests verify Heavy Cannon selection becomes available. Verify UI feedback and actual next-run weapon. |
| Second ship unlock/sidegrade | DOMAIN VERIFIED / UNREAL OPEN | Level 3 at 450 XP; tests verify greater speed/maneuver/response and lower hull. Verify model selection and actual playstyle. |
| New run retains unlocks and resets run power | DOMAIN VERIFIED / UNREAL OPEN | Core resets tiers, credits, utility, contracts, encounter flags and wave. Verify the full death→Results→hangar→loadout→launch path. |
| Hangar ship/weapon/progression/launch | SOURCE ONLY / UNREAL OPEN | Station home variant, GameMode selections and shortcuts. Persistent stats show last/best run; a richer run-history list is not implemented. |
| Separate account/settings/suspension domains | DOMAIN VERIFIED / UNREAL OPEN | Three strict codecs and three SaveGame slots. Verify actual platform paths and settings persistence. |
| Station suspended run survives application close/relaunch | DOMAIN VERIFIED / UNREAL OPEN | Payload round trip preserves run values, contract, utility, pending reward and buff duration. Actual UE SaveGame disk round trip has not executed. |
| Death after resume cannot reload checkpoint | DOMAIN VERIFIED / UNREAL OPEN | Save consumes suspended slot before exposing resumed state; account run ID rejects the latest awarded run. Portable replay tests prevent duplicate XP, but disk order/crash behavior needs process-level validation. |
| Invalid data and persistence failures | DOMAIN VERIFIED / UNREAL OPEN | Codecs reject malformed/versioned/nonfinite/out-of-range/inconsistent state without mutating output; adapter protects unreadable existing accounts and verifies writes. Exercise real failure/recovery paths with disposable test profiles. |

### Shell, presentation, performance and delivery gates

| Required criterion | Status | Source/evidence and remaining verification |
| --- | --- | --- |
| Continue/New Run/Hangar/Settings/Graphics/Audio/Controls/Stats/Quit | SOURCE ONLY / UNREAL OPEN | GameMode panels and HUD. Verify navigation, enabled states, focus, pause/resume and quit behavior with both input devices. |
| Subtitles, UI scale, non-color warnings/pickups, shake/blur, hold/toggle | SOURCE ONLY / UNREAL OPEN | Settings codec, HUD distinction, shape assets and runtime toggles. Verify actual effects, legibility and persisted values. |
| Tutorial | SOURCE ONLY / UNREAL OPEN | Wave 1–3 guidance and resettable persistent flags exist. Observed steering, throttle, boost, brake, dodge, firing, pickup and explicit event acceptance now clear corresponding hints. This source behavior does not prove comfortable teaching or player mastery. |
| Hybrid visuals and visibly piloting Acornaut | SOURCE ONLY / UNREAL OPEN; QUALITY GAP | Supplied hero import path, open-cockpit source hull, materials and camera exist. Primitive generated geometry/materials have not met the approved Hybrid commercial-quality bar; seated/reactive animation remains unfinished. |
| VFX, warning audio, music layers and world audio | SOURCE ONLY / UNREAL OPEN; QUALITY GAP | World/Ship hooks and ten synthesized WAVs exist. Verify playback, mix, spatialization, stem synchronization and feedback quality; spoken reactions are not recorded audio. |
| Gradual visual regions independent of stations/waves | SOURCE ONLY / UNREAL OPEN | Ambient-region/world presentation code requires in-engine inspection; visual change must remain independent of gameplay composition and block cadence. |
| Performance measured against 60 FPS | UNVERIFIED UNREAL | No CPU/GPU/frame-time measurements exist; no FPS or hardware capability claim is made. |
| Bottlenecks documented and 120+ FPS scalability path | SOURCE ONLY / UNREAL OPEN | Active-threat limits, bounded fragments, substeps and quality/frame-limit settings exist. Profile actual cost and validate reduced visual settings preserve simulation/readability. |
| Transition/spawn/docking hitches and frame-rate independence | DOMAIN VERIFIED / UNREAL OPEN | Portable meter/recovery step comparisons executed; physical flight, actor spawning, map assets, docking and frame pacing remain unmeasured. |
| Documentation/clean implementation branch/PR | DELIVERY CHECK REQUIRED | Reconcile project state, architecture, issues, Phase 2 notes, build instructions and performance record with the final commit; branch/PR state is recorded by the lead. This document does not claim a PR exists or is merged. |
| No deferred Phase 2 implementation | SOURCE REVIEW ONLY | Scoped runtime contains two enemies/weapons/utilities/events/contracts and four hazard families; no multiplayer, Steamworks, cloud or inventory implementation is intended. Final diff review remains required. |

## Independent source review and corrections

An independent specialist inspected Core integration in GameMode, GameInstance, Ship, HUD and Station. The lead applied the following corrections, which were then confirmed in current source. These are static confirmations, not executed Unreal regression passes:

- Preserve handled death phase when showing the hangar, avoiding the Results→hangar→Results loop.
- Gate new-run launch on completed death persistence; validate a candidate run before consuming an existing suspension.
- Protect unreadable existing account saves against automatic overwrites; refuse resumed play when the account is blocked.
- Destroy an existing walker during resume/station entry; retain the approach hub rather than rebuilding it unnecessarily.
- Read relevant flight/economy/Director tuning from `DA_Phase1`; apply Engine acceleration to the physical velocity step.
- Use `Stats().weaponDamage` once, avoiding duplicate Heavy Cannon and temporary-buff multipliers.
- Align station arrival to ship heading, open the inbound corridor, transform service/dock positions with the hub, and correct the assistance message to 12 m.
- Pause normal flight shell panels while keeping depot/reward panels live; enable controller ticking while paused.
- Wire subtitle preference to dialogue rendering, preserve critical warnings, and apply master/effects volume to station ambience.
- Add explicit Station 2 abandonment/restart routing.
- Tighten Core decoding to reject normal Flight at Wave 10; the climax phase is mandatory.

Tuning remains a limited common `UDataAsset` plus C++ definitions. A full designer-authored library of separate hazard, encounter, utility, contract and station assets is not complete. This is a remaining architecture/content-authoring requirement, not evidence that exposing a few values fulfills every Data Asset expectation.

## Station 2 slice-boundary decision

The full-game design is indefinite; Phase 1 authors ten waves. Station 2 therefore remains a live station, not victory or death. It offers the station services and Save & Quit. `LaunchFromStation()` refuses Wave 11. The shell explicitly offers abandonment of this slice and return to hangar launch, discarding run state and any suspension without awarding death XP. A new launch receives a fresh run ID and fresh run upgrades. This is the bounded Phase 1 interpretation; it does not validate indefinite survival or a Station 2→Wave 11 flight loop.

## Required integrated manual protocol

Use a built/cooked candidate with a recorded commit, package hash, engine/toolchain versions, hardware, graphics settings, resolution, input-device model and test date. Back up existing personal saves outside the game save directory; use disposable test profiles for destructive/failure tests. Keep shipping-like gameplay separate from any temporary development acceleration or injected state. Do not credit a cheated/accelerated run as the natural ten-wave experience.

1. **Cold launch and shell:** Launch the packaged executable offline with no saves. Verify hangar, starting locks, graphics/audio/controls/accessibility menus, controller navigation, mouse clicks, text scaling and Quit. Change settings, close/relaunch and verify persistence. Exercise pause/return during flight and confirm depot/reward menus remain live.
2. **Fresh keyboard/mouse run:** Launch Wave 1 with starter/Rapid Laser. Use pitch, yaw, bank, throttle, strafe, boost to exhaustion/recharge, sustained braking to overheat/cool, and all dodge directions. Collide while dodging and confirm damage. At 30/60/120 FPS caps compare the same maneuver route and stopping/turning response. Check chase camera and visible pilot.
3. **Damage and weapons together:** Capture shield-only hits, overflow to hull, shield remaining depleted, regeneration delay, slow recovery while danger persists, fast safe recovery and repair. Use both weapons against small/medium/massive asteroids and both enemies. Check manual shots off target, assisted aim, obstruction handling, fragmentation, pickups, critical impairment and temporary buff expiry.
4. **Waves 1–5 and opportunity flow:** Play naturally through all waves while recording wave order and pacing. Confirm hidden duration, short breathing and persistent hazards. Approach the Salvage Cache without accepting, leave, return and explicitly accept; exercise success and failure on separate runs. Find the one Wave 3 depot, compare its offered subset/discount, purchase in range and reject an out-of-range purchase. Verify no second depot appears later or after suspension.
5. **Wave 5 and Station 1:** Record wormhole warning, increasing pull, actual passage, hostile combat and station detection. Approach from varied heading/pitch, enter the marked corridor and observe assisted landing. Walk/run/interact through all five upgrade tracks, repair, Mica, contract board, beacon story reward, Save & Quit and launch. Record ordinary visit duration and affordability; test beacon reward cannot repeat.
6. **Suspension and process restart:** Before saving, record ship/weapon, hull/shield, tiers, utility, credits, wave, contract/progress, depot/event flags and any unclaimed reward/buff. Save & Quit, restart the executable, Continue, compare state and relaunch into Wave 6. Close without making a new suspension and confirm consumed data is not offered again. Repeat with each contract type. Verify corrupt/truncated/version-mismatched saves fail closed and preserved unreadable accounts are not overwritten.
7. **Waves 6–10 and Station 2:** Record stronger compositions and more aggressive enemies using the same roster. Complete the Distress event and choose its reward explicitly. Prove Vector Thrusters and Overdrive Cooling change handling/meter behavior, then deliberately replace one. Verify Wave 10 overlaps gravity, asteroid storm and enemy pressure with fair warnings and an achievable escape path. Enter Station 2, resolve success/failure contracts, use station services and suspension, then test the explicitly labelled abandonment/new-run route without death XP.
8. **Death and restart:** Die before a station and after resuming a suspension. Verify run termination, one XP/score award, unlock progress, no reloadable consumed checkpoint, Results→hangar review, loadout selection and fresh Wave 1 state. Progress normally through weapon and agile-ship unlock thresholds and use both. Simulate failed account write and failed suspension invalidation with a disposable test environment; confirm launch remains gated until retry succeeds and XP is not awarded twice.
9. **Controller end-to-end run:** Repeat the entire ten-wave route and station/save/restart loop using a physical controller, including each menu, flight capability, weapon, dodge direction, event acceptance, utility/reward choice and on-foot action. Record device/connection and test trigger hold/toggle plus disconnect/reconnect. Keyboard emulation is not a controller pass.
10. **Presentation and performance:** Inspect imported hero skeleton/texture/animation, pilot pose/tail clearance, silhouette readability, ring transparency, collision boundaries, NPC/station activity and region transitions. Listen with all music layers and hazards overlapping. Capture CPU/GPU/frame-time traces during ordinary flight, dense scenes, Wave 5, docking, stations, Wave 10 and origin rebasing. Record median and tail frame times, spikes, resolution/settings and bottlenecks; compare 60 FPS baseline and reduced settings with higher-refresh targets. Reduced settings must preserve simulation, response and warning clarity.
11. **Replay motivation:** After an ordinary death and after reaching the authored boundary, have the tester decide whether to launch immediately and record the reason. Identify friction in flight feel, pacing, rewards, progression, readability or downtime. This qualitative gate cannot be inferred from test assertions, code size or an attractive source preview.

For every manual case, record PASS/FAIL/BLOCKED, observed result, exact build/hash, supporting screenshot/video/log/trace, defect reference and retest outcome. Keep unexecuted cells open. Phase 1 remains PARTIAL until the required integrated player experience and delivery artifacts meet both authoritative documents.
