# Open work and owner review

**Start here. This is the single active issues, follow-up and priority log.** Updated September 14, 2026. Phase 1 remains PARTIAL.

## Current instruction: capture feedback, hold bug fixes

Owner direction, September 14: collect reports for now; do not start bug fixes or another broad enhancement pass. The owner subsequently authorized an editor workshop with ten material presets and scalable asset placement. This authoring implementation is active; see [Station editing](STATION_EDITING.md). The bug-fix pause remains in effect.

### Newly reported bugs — open, capture only

These are paraphrases of the owner's reports, not reproduced findings. Report context follows the 0.1.16 release, but the exact launched build and device/settings are UNCONFIRMED. No fix, retest or acceptance closure is claimed.

| Report ID | Owner observation | Tracking / later verification |
| --- | --- | --- |
| RPT-20260914-01 | Inverting flight controls also inverts character controls. | ISS-05; PT-05,10,15–17. Later verify independent flight/on-foot pitch preferences and persistence. |
| RPT-20260914-02 | Can walk through nearly every station object, but movement is blocked at the words/labels. | ISS-03; PT-10,17. Later map visible geometry to actual collision and service reachability; the report does not prove text geometry itself is the blocker. |
| RPT-20260914-03 | An NPC is stuck in a table. | ISS-03; PT-10,18. Later identify the NPC/location and check body/furniture overlap in natural play. |

Additional owner reports (capture only; same unconfirmed build/device boundary):

| Report ID | Owner observation | Tracking / later verification |
| --- | --- | --- |
| RPT-20260914-04 | The base weapon barely shows anything coming out of the front. | ISS-01/06; PT-06,18. Later review muzzle/projectile visibility from the normal chase camera. |
| RPT-20260914-05 | Combat feels like Space Invaders: enemies line up ahead to shoot rather than create a dynamic space fight. | ISS-06; PT-06,12. Later review approaches, lateral/vertical motion, maneuvering and pressure in natural combat before choosing changes. |
| RPT-20260914-06 | Backgrounds still look graphically weak and fuzzy, like low-resolution artwork. | ISS-01; PT-03,18. Later compare actual runtime resolution, filtering and source imagery; cause unconfirmed. |

Owner subsequently authorized building the editor workshop with approximately ten material presets and scalable placement. This authoring work is active; the bug-fix pause remains in force.

Lead maintains these reports here while the owner continues listing observations. Existing acceptance cases remain open. Reproduction and repair are paused until the owner resumes them.

## Review route when playtesting resumes

The new local visual build is ready for owner review: **Package 4, source `cf6296f`**, at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`. Keep the entire folder. It includes the provisional Havolk starter hull, refreshed space/combat presentation and furnished, editable station. The [project state](PROJECT_STATE.md#source-build-and-release) identifies this build and the now-published itch 0.1.16-alpha.1 / build 1979965. Close the game and update through the itch app on windows-alpha to review that version.

1. **Check the flight view first.** Open the executable, set controller sensitivity and preferred pitch direction, then launch and try ordinary turns, boost and brake. Judge the new starter silhouette, exhaust attachment, camera framing and hazard visibility against the space lighting. Relevant cases: PT-01,03–05,15,18.
2. **Check combat cues.** Fire at a target and look for a clear distinction between a shot, a hit and a confirmed death while hazards are present. Report the single most confusing moment, with a clip or screenshot if useful. Relevant cases: PT-06,12,18.
3. **Try one lasting station edit.** Open `C:/Users/j6sis/SpaceSurvival/SpaceSurvival.uproject`, then use **Tools > Station Workshop** and the [first-edit guide](STATION_EDITING.md#first-edit). Move or add one prop, Save + Apply, then open the normal Survival map and restart Play to see it in the station. Keep the marked corridor and fixed service anchors clear; check furnishings, robot staff and service-label readability from both sides. This editing check does not close the natural station cases PT-09,10,17,18.

When the owner resumes structured review, start with item 1; the lead records your build, device/settings and observations against the corresponding IDs, then brings you back to the next unresolved step. You do not need to edit Markdown or remember the full checklist. Partial observations leave the corresponding acceptance case open.

Technical validation: 49 Unreal tests passed cleanly at 23:57:10 UTC on September 14, covering the unchanged C++ implementation. The subsequent star-material change was authored, cooked and rendered separately. Package 4 passed its actual IoStore export/import audit and both packaged visual captures: 4 Wave 1 images and 16 Station 5 images. [Current validation](validation/2026-09-14-visual-enhancement-stars.json) binds the source, private inputs and actual package. Scripted captures and automated checks do not close natural play, visual quality or representative performance acceptance.

## Current priority and ownership

| Order | Work | Owner | State / next action |
| --- | --- | --- | --- |
| 1 | Capture incoming owner feedback | Lead | Append reports to the existing issue groups; no fixes or forced retesting during this collection period. |
| 2 | Review the implemented Station Workshop | Owner + lead | PR14 has a built editor, ten presets, 677 matching placeable assets and verified save/apply/export. Owner tries one prop edit; lead follows up on authoring feedback. See ISS-09 and the station guide. Bug repairs remain paused. |
| 3 | Resume reproduction, fixes and acceptance after owner direction | Lead + owner for feel | Paused. Preserve all existing cases and use the relevant report IDs when work resumes. |

No other document maintains a separate active priority order. Solution catalog value/timing is research context, not purchase authorization or a competing schedule. Phase 2 ideas stay in the catalog/integration notes.

## Art ownership

Owner decision, September 14: the regular 3D contributor owns the hero and iconic starter ship long term. The lead owns Unreal integration, collision/scale/socket/material checks, gameplay testing and packaging. Supplied AI models and kitbash alternatives are provisional, not replacements for that contributor's design ownership.

The owner purchased catalog C23, Space Ship 02 Modular Pack (Havolk). Its prepared assembly now supplies the default closed-cockpit starter, with the seated pilot hidden during flight, plus matching tier/utility hardware and the existing enemy-role derivatives. This is a provisional kit interpretation awaiting owner art review; Phase 1 still contains only the starter and scoped second ship. Future ship content stays deferred. ISS-02 owns art follow-up and ISS-14 the collaboration/storage setup; the owner confirmed the collaborator delivers model/texture/animation files only, not Unreal project edits. A private versioned Drive handoff is the proposed starting workflow; destination/access setup remains open.

## Implementation and verification issues

These are grouped problems, not extra game features or a completion percentage. Related PT cases below describe how to validate them. **All rows remain open.** A status of *Needs owner retest* means a bounded repair exists, not that the issue is accepted.

| ID | Issue and evidence boundary | Status / owner | Next action and closure evidence |
| --- | --- | --- | --- |
| <a id="iss-01"></a>ISS-01 | Space depth, lighting, VFX and wormhole arrival remain unaccepted against the visual target. The packaged pass includes three blended owned nebula cubemaps, warm key light, eight ambient rock shapes, smaller dust grains, distant structures and bounded combat effects. The final package audit and both packaged visual captures passed. Owner feedback identified overpowering stars; Package 4 lowers their brightness and adds fixed variation without changing nebula or object lighting. The new balance remains for owner review. Nozzle/exhaust appearance, bounded parallax and unfamiliar arrival feel (F08) still need owner judgment. [Combined record](production/COMBINED_SPACE_LOOK.md). | Needs owner review / lead follows up | Use owner comparison to select the next visual change; verify in moving combat and both climaxes. Close with accepted Hybrid presentation/readability, not a screenshot alone. PT-03,09,12,13,18. |
| <a id="iss-02"></a>ISS-02 | Hero/ships and continuous animation remain provisional. The default starter is now the purchased Havolk closed-cockpit assembly with matching upgrade/utility hardware; the seated pilot is hidden in flight. The optional Ludo trial remains separate. Repaired walk/exit clips and planted-foot tests pass, but pinched-leg report F11 still needs natural-motion retest; paused HeroAlpha experiments remain unadopted. [Current validation](VALIDATION.md), [earlier refresh](ASSET_REFRESH.md). | Needs owner retest + art work / regular 3D contributor; lead integrates | Judge the new default hull's identity, framing, exhaust/muzzle placement and hardware, then compare neutral/walking/turning/exit poses. Preserve the contributor's long-term design ownership and original sources. PT-01,03,10,18. |
| <a id="iss-03"></a>ISS-03 | Station composition and ambience remain unaccepted. New capture-only reports RPT-20260914-02/03 describe walk-through props, blockage near labels and an NPC intersecting a table; causes remain unconfirmed. The saved 380-component Blueprint contains corridor dressing, real terminals, furnished workbenches, stocked storage, two idle robot staff and task lighting. Create-once authoring preserves manual edits. Native collision/service anchors remain fixed; tests cover the visible deck/sole fit and readable front-facing service-label orientation. Labels now face the active camera, use a cooked unlit font material and cast no shadows; the wall plaque stays fixed. Two broad fill lights correct the underlit walkway/pilot. Cooked dependencies and packaged station images were checked; owner composition and natural-use acceptance remain open. Station4 retains its conservative exterior collision envelope. [Station editing](STATION_EDITING.md). | Needs owner review / lead follows up | Use the final packaged capture, then verify one saved workshop edit and natural approach, walk/exit, label readability and service reachability. Improve the largest reported presentation problem. PT-09,10,17,18. |
| <a id="iss-04"></a>ISS-04 | Station 2 services/save/discard boundary needs usability and replay-appeal acceptance. Actual failure/retry persistence tests exist; no Wave 11 or completion XP is authorized. [Boundary evidence](STATION2_DISCARD.md). | Needs owner/QA verification / lead | Natural arrival, service/save/discard and next-run review. Preserve disclosed zero-death-XP discard. PT-13,14,17,19. |
| <a id="iss-05"></a>ISS-05 | Input comfort, camera framing and full physical-device parity remain unaccepted. New capture-only report RPT-20260914-01 says flight inversion also changes character controls; independent preferences need later verification. Station rear-camera, inversion and flight framing fixes exist. Owner feedback F01/F09/F10 says starter handling is decent but inverse mouse was a barrier; controller is preferred. [Camera](STATION_CAMERA.md), [environment](ENVIRONMENT_REFRESH.md). | Needs owner retest / lead | Calibrate preferred inversion/sensitivity before retuning; verify KBM and controller, reconnect and menu focus. PT-02–05,15–17. |
| <a id="iss-06"></a>ISS-06 | Natural combat, hit/death certainty, target identification, reward cadence and Director fairness need integrated play. F05/F06 report easy aiming and unclear kills; new bolt/muzzle/impact/explosion effects and deterministic projectile/fragment/admission repairs do not settle feel or balance. The real-kill fixture verifies explosion activation, but a visible fire/smoke plume remains unverified; existing wreckage bars are not explosion-render evidence. [Gameplay repairs](GAMEPLAY_QUALITY.md), [combat cues](COMBAT_CUES.md). | Needs verification/tuning / lead | Play both weapons and enemy patterns amid hazards; capture unclear deaths/unfair hits; tune from evidence while preserving manual aim and scoped rosters. PT-06,07,09,12–14,19. |
| <a id="iss-07"></a>ISS-07 | Save safety is verified only within bounded fault cases. Disk-full/short-write, arbitrary binary corruption and hardware-loss remain untested; generic Windows backend only, no multi-slot transaction/automatic backup. [Fault](validation/2026-09-13-storage-faults.json) and [corruption](validation/2026-09-13-corrupt-account.json) evidence. | Needs qualification / lead | Isolated profiles and guarded reproducible failure tests; preserve owner saves. Record unsupported cases honestly. PT-11,14,17 for natural UI path. |
| <a id="iss-08"></a>ISS-08 | UI/audio/music need actual listening and busy-scene review. Current voice bounds/spatial cues and settings tests are not a finished mix, recorded NPC dialogue or full accessibility validation. [Audio hooks](AUDIO_HOOKS.md). | Needs implementation/acceptance / lead | Improve and listen to engine, weapons, impacts, rewards, warnings and pressure/station music; verify scaling, subtitles and focus. PT-05,06,10,16,18. |
| <a id="iss-09"></a>ISS-09 | The owner-authorized editor workshop adds asset-browser placement/rotation/scaling/deletion, ten materials and saved-map application/export in PR14; Editor build, nine save/apply/export checks and the visible asset-browser capture pass; [receipt](validation/2026-09-15-station-workshop.json). [Station editing](STATION_EDITING.md) describes the controls and supported-content boundary. Current station visual composition is owner-editable in a preserved workshop map that applies to the runtime Blueprint; gameplay collision/service anchors and some other content authoring remain native/synchronous. Utility/contract/economy parameters are editable, but native menus/layout/behavior and loading need assessment against the promised extension boundaries. [Architecture](ARCHITECTURE.md), [Phase 2 notes](PHASE2_INTEGRATION.md). | Needs review / lead | Identify a concrete Phase 1 authoring/performance gap before refactoring; verify changed data round-trips and existing play. No framework migration or deferred system implementation by default. |
| <a id="iss-10"></a>ISS-10 | Representative 60 FPS/full-run CPU/GPU/RAM/VRAM acceptance is open. Older RTX 5080 scripted samples are bounded; current Wave1 capture includes readback/startup stalls, and standard analyzer rejects that scenario. [Performance](PERFORMANCE.md), [combined diagnostic](production/COMBINED_SPACE_LOOK.md). | Needs qualification / lead | Fix/extend scenario analysis where justified, profile a natural busy run and scaling; report frame-time distributions and hardware. No claim of “120 FPS accepted” from capped screenshot fixtures. |
| <a id="iss-11"></a>ISS-11 | Distribution: clean-PC startup and real itch A-to-B update/save preservation remain unverified. The new local Package 4 passed its actual archive/dependency audit and both packaged visual captures. The owner authorized PR11/12 merges and the itch update on September 14. Release preparation found runtime saves/config/logs in the archive; the publisher now filters them and rejects unsafe prepared payloads. The clean 0.1.16-alpha.1 payload is verified ready as itch build1979965; the release record owns its full identity. The new devlog remains a draft pending browser security/sign-in. [Release workflow](ITCH_RELEASES.md). | Needs release/QA follow-up / lead | Finish the devlog after browser sign-in, then test clean install/update with preserved saves and version identity. Merge is not publication. |
| <a id="iss-12"></a>ISS-12 | Continuous contact uses linear per-frame player/shot motion; enemy/world-cover queries use current transforms. Nonlinear paths inside a hitch are not reconstructed. [Gameplay follow-up](validation/2026-09-13-gameplay-fairness-followup.json). | Known approximation / lead | Reproduce an unfair contact before broad redesign; retain first-contact/cover-order regressions and document practical hitch limits. PT-04,06,12. |
| <a id="iss-13"></a>ISS-13 | Event/depot/contract/beacon clarity and live input need retest. F02/F03/F04/F07/D01 map here: following distraction, unclear objective/beacon/allegiance, and optional magnetic parking. Mooring/feedback repairs exist. Issue #7 additionally flags live reward device differences and synchronous tutorial saves; runtime impact is not established. [Feedback provenance](production/OWNER_FEEDBACK.md), [review issue](https://github.com/j6sistek-ui/SpaceSurvival/issues/7). | Needs owner retest/investigation / lead | Verify explicit acceptance, objective/progress/outcome, 20-second aboard-ship lock/release and no lingering follower; reproduce input/write risks before claiming a fix. PT-07,08,10,16,17. |
| <a id="iss-14"></a>ISS-14 | GitHub is not a complete backup of local licensed derivatives, raw downloads, manual tuning, art experiments or saves. Source-export checks do not reproduce the current licensed look from Git alone. [Storage map](PROJECT_STATE.md#where-files-live), [source integrity](SOURCE_INTEGRITY.md). | Needs collaborator handoff/backup plan / lead + owner for storage choice | Choose the shared handoff destination, then inventory unique inputs and document private backup/reacquisition, versioned upload, import and restore paths. See the proposed asset collaboration workflow in Project State. Verify a fresh development setup without publishing paid source assets. No cleanup/deletion is implied. |
| <a id="iss-15"></a>ISS-15 | PR documentation enforcement: template/CI check merged through PR11; last ruleset audit requires PRs but no successful status checks. A running check is not yet a server merge requirement. | Needs repository setting / lead | After explicit repository-setting approval, add the verified documentation job to required checks while preserving existing rules. Confirm a failed check blocks merging. No branch-rule change is claimed by this PR. |

## Hands-on acceptance cases

**19 open / 0 passed** at consolidation. All 19 previously unchecked cases were moved here from PLAYTEST_TOMORROW.md; none was accepted by this edit. They are acceptance scenarios related to the issues above, not 19 additional features or a required single sitting.

Structured review and defect fixes are currently paused under the capture-only instruction above. When resumed, use the short review route and the relevant unresolved case. Controller cases can be done first. For each case record the actual build, date, device/settings, observation and result: not tried, partial, failed, needs retest or passed. Check the box only after the full case passes with owner/tester evidence. A defect report or automated fixture is useful evidence but not a pass.

Session date/time: __________
Build/receipt: __________
Resolution / quality / cap: __________
Device / connection / sensitivity / pitch direction: __________

<a id="pt-01"></a>
1. [ ] **Launch the recorded executable and open the home hangar.**\
   Expected: usable game window, visible Acornaut/ship and readable shell; no black view, missing assets or unwanted fullscreen switch.\
   Observation / screenshot / issue: ______________________________________

<a id="pt-02"></a>
2. [ ] **Set a comfortable mouse steering dial before judging flight.**\
   Open **Settings → Controls → Mouse sensitivity**. The dial is adjustable from 0.3–2.9 in 0.2 steps, with an upper clamp and wrap to 0.3. The lead verified a change from 1.0 to 1.2 and a later packaged relaunch displaying mouse 1.2/controller 1.0. Your preferred values and their feel still need checking. Record the actual displayed value above. Launch a run, make small horizontal/vertical corrections, and adjust again if too slow or too sharp.\
   Expected: a visible change in response and usable fine corrections. Sensitivity is a preference to tune, not a fixed value the tester must accept.\
   Observation / preferred value: _________________________________________

<a id="pt-03"></a>
3. [ ] **Check keyboard/mouse flight and chase camera.**\
   Mouse steers; W/S changes throttle; A/D and R/F move sideways/up/down. Try gentle weaving and a stronger turn.\
   Expected: responsive control with momentum/banking, ongoing forward movement, a fully framed ship and readable hazards without excessive camera swing.\
   Observation — loose, stiff, sluggish, twitchy or comfortable: ____________

<a id="pt-04"></a>
4. [ ] **Try boost, sustained brake and all dodge directions.**\
   Shift exhausts boost; release to recharge. Hold Space until overheating, then cool. Use Q with lateral/vertical direction, including one deliberate obstacle clip during a dodge.\
   Expected: useful boost, meaningful partial braking without permanent parking, obvious resource states, sharp directional dodge and damage on collision.\
   Observation: _________________________________________________________

<a id="pt-05"></a>
5. [ ] **Tune comfort/accessibility and return to flight.**\
   Test sensitivity, invert pitch, boost/brake hold versus toggle, camera shake, motion blur, subtitles, UI scale, Graphics and Audio.\
   Expected: ordinary menus pause, settings visibly apply, text stays inside panels, warnings remain understandable without color, and return does not leave stuck inputs.\
   Observation / preferred settings: ______________________________________

<a id="pt-06"></a>
6. [ ] **Feel damage, recovery, pickups and Rapid Laser combat.**\
   Observe shield/hull damage and recovery in danger versus clear space. Collect each reward shape; use manual aim/soft brackets against debris/enemies and try an obstructed shot.\
   Expected: shield does not refill automatically; hull can recover; damage/critical state is clear. Pickups justify route risk; laser/destruction/fragments are readable; assistance never fires automatically.\
   Observation — hit feel, aim, recovery, reward clarity: ___________________

<a id="pt-07"></a>
7. [ ] **Follow the first block and deliberately accept Salvage Cache.**\
   Approach before pressing E; complete a diversion when comfortable. On another attempt let an event fail.\
   Expected: approach alone does not commit; objectives/reward/failure are clear; event UI leaves the live ship controllable.\
   Observation: _________________________________________________________

<a id="pt-08"></a>
8. [ ] **Choose a depot stop and use its magnetic mooring.**\
   Approach voluntarily and interact; remain aboard while the service panel shows the lock. Inspect the upgrade subset/deal; with missing shield try the paid shield-only recharge (21 credits at defaults). Close the panel to release, and observe the 20-second service boundary.\
   Expected: no physical pad/on-foot scene, clear stop/release, no wave progress while moored, limited offers and no distracting follower after departure. Check that failed/stale purchases do not spend credits.\
   Observation: _________________________________________________________

<a id="pt-09"></a>
9. [ ] **Play Wave 5 and approach Station 1.**\
   Watch the wormhole emerge, counter the pull, survive hostile arrival, approach manually and enter landing assistance. If the run ends earlier, record death/retry notes in Step 14 and resume this route on another run.\
   Expected: continuous journey, noticeable climax, useful warnings, consistent controls and understandable/satisfying docking.\
   Observation — tension, fairness, visibility, docking: ____________________

<a id="pt-10"></a>
10. [ ] **Walk Station 1 and choose meaningful purchases.**\
    WASD/Shift/E walk/run/interact. Visit all five upgrade paths, repair, Mica, contracts, the story beacon and launch. Buy what you want; try the beacon reward twice.\
    Expected: coherent feet/camera/exit, easy service discovery, roughly 2–3 useful purchases, compact visit and once-only side reward. Pressure discloses reduced shield/added pressure; Hunter explains target/reward.\
    Observation / purchases / visit length: ________________________________

<a id="pt-11"></a>
11. [ ] **Save & Quit, relaunch, Continue and leave for Wave 6.**\
    First record ship/weapon, wave, credits, tiers, hull/shield, utility and contract. Compare after relaunch.\
    Expected: same station run/build, retained contract, Wave 6 departure and a consumed suspension that cannot act as a reusable checkpoint.\
    Before / after / discrepancy: _________________________________________

<a id="pt-12"></a>
12. [ ] **Play Waves 6–10, Distress and both utility choices across attempts.**\
    Compare Vector Thrusters with Overdrive Cooling and try Heavy Cannon when rewarded/unlocked. Observe electrical/gravity pressure with debris and both enemies.\
    Expected: stronger compositions without unreadable hits, deliberate rewards, distinct weapons/utilities and time to respond to warning direction/sound.\
    Observation — weapon/utility feel, enemy distinction, unfair moment: _____

<a id="pt-13"></a>
13. [ ] **Reach Wave 10's compound climax and Station 2.**\
    Look for simultaneous gravity, asteroids and enemies; inspect second-station services and contract resolution.\
    Expected: difficult but readable pressure and clean landing. Current slice behavior has no Wave 11; services/suspension remain and labelled abandonment gives no death XP. That boundary remains under review.\
    Observation — climax, reward and boundary friction: _____________________

<a id="pt-14"></a>
14. [ ] **Inspect ordinary death, resumed death, progression and another run.**\
    Review XP/score, unlock messages, history and loadout. Use Heavy Cannon and Swift after their early unlocks; compare Swift agility/durability.\
    Expected: one award, permanently ended run, no reloadable dead checkpoint, clear next milestone, retained account options and fresh run-specific power.\
    Observation — clarity and immediate desire to relaunch: _________________

<a id="pt-15"></a>
15. [ ] **Switch to a physical controller and calibrate its own dial.**\
    **Settings → Controls → Controller sensitivity** is separately adjustable from 0.3–2.9. Right stick steers, left stick moves laterally/vertically, D-pad up/down changes throttle.\
    Expected: comfortable fine control and a stable resting stick; mouse preference does not force the controller value.\
    Observation / preferred value / drift: _________________________________

<a id="pt-16"></a>
16. [ ] **Repeat controller actions and live menus.**\
    RT boost, LT brake, LB directional dodge, RB fire, A interact, Menu shell and B back. Test hold/toggle, live depot/reward choices and disconnect/reconnect.\
    Expected: keyboard/mouse capability parity, no lost steering, accidental selection/fire or stuck inputs.\
    Observation: _________________________________________________________

<a id="pt-17"></a>
17. [ ] **Complete the two-block station/save/death route on controller.**\
    Left stick walks, X runs, A interacts. Repeat services, events, contracts, utility/reward choices, both climaxes, Save & Quit/Continue and next-run selection across natural attempts.\
    Expected: no keyboard rescue; comfortable combat/walking and usable menus/terminals.\
    Observation / keyboard rescue needed: _________________________________

<a id="pt-18"></a>
18. [ ] **Listen and judge readability in the busiest scenes.**\
    Compare engine/weapon/impact/pickup cues, alarm frequency/direction, pressure music and station decompression. Check the hero/tail/feet while on foot, the closed Starter hull in flight, bloom, hazards, telegraphs and maximum UI scale.\
    Expected: essential sounds/cues remain distinct without constant alarms/chatter or a hidden route. Rejected provisional art still requires replacement regardless of functional readability.\
    Observation / wave or timestamp: ______________________________________

<a id="pt-19"></a>
19. [ ] **Record the decisive player verdict and next adjustment.**\
    After ordinary death and the available boundary, record whether another run is immediately appealing. Identify one biggest source of friction. Perceived smoothness is useful; measured FPS belongs in the separate performance record.\
    Immediate retry: __________  Why / why not: ____________________________\
    Biggest next adjustment: ______________________________________________\
    First unchecked step / next place to resume: ___________________________

## Updating and closing work

The lead maintains this file after material changes and owner feedback, and links the relevant IDs in every PR. Keep a stable ID until closure; update the existing item instead of creating a duplicate. Each new active task needs scope/WBS basis, an owner, next action and an observable closure condition. Do not add speculative purchases or Phase 2 features as current tasks.

On closure retain the item with **Closed**, date, revision/build and evidence; owner-experience items additionally require the owner's reported outcome. Failed or incomplete retests remain open with the next action. Superseded duplicates point to the surviving ID. Do not silently remove unfinished work or mark it done because a PR merged.

Closed/superseded work at this consolidation: no open acceptance case was closed. Earlier technical repairs and their exact test limits remain in [validation records](VALIDATION.md) and immutable `docs/validation/` receipts. Removed stale running commentary remains recoverable in Git history.

Other documents have distinct roles: [Project State](PROJECT_STATE.md) for build/storage status; [solution catalog](production/SOLUTION_CATALOG.md) for candidate resources; [work packages](production/WORK_PACKAGES.md) for needs/dependencies; [game scope](GAME_SCOPE.md) and [IMPLEMENT](../IMPLEMENT.md) for authority. None is a second active task list.
