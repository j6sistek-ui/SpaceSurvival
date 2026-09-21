# Open work and owner review

**Start here. This is the single active issues, follow-up, action and priority log.** Latest owner direction: September 21, 2026. Phase 1 remains PARTIAL. Older dated records below retain their original evidence and are superseded where explicitly noted.

## September 21: rebuild the flight-to-station loop

**RPT-20260921-01 — OPEN; lead owns implementation and verification, owner supplies feel acceptance.** Owner feedback, paraphrased: only boost seems to work; ship turning and supplied animations are absent; weapons have no convincing firing/damage; landing ends in crashes/death; the run feels like passive coasting. The owner explicitly requested setting up the entire gameplay loop from scratch. This supersedes earlier capture-only/paused instructions for flight, combat, landing and station arrival. Preserve the locked Phase 1 mechanics, five-wave cadence, progression, saves and supplied hero content.

Source review confirmed that the native pawn bypassed the purchased ship Blueprint, held the flight clip at its last frame, used an obsolete muzzle inside the larger hull, marked the station hub instead of the pad, retained a minimum forward speed while landing, and respawned on launch. Raw boost also added force after the domain rejected it. The first new input-path test reached real mouse/gamepad rotation but exposed the vendor Blueprint's missing demo projectile/occupant references. These are separate findings; they do not prove the owner's exact original input failure, whose runtime/build remains unconfirmed.

The repair is isolated on `codex/flight-loop-reset` in the [candidate checkout](PROJECT_STATE.md#september-21-gameplay-reset-candidate). It integrates a clean derivative of the full authored ship hierarchy; native steering/aim/damage; explicit E/A pad admission with shared guidance; hover/descent; a safe walker handoff; and takeoff in the same ship, with the next wave held until station-zone exit. Validation is recorded in [the reset receipt](validation/2026-09-21-flight-loop-reset.md). An automated pass does not close this report.

**Review candidate ready; reports remain OPEN.** Package3/source `7a63b03` passes the expanded cooked-dependency audit and both final Station5/Wave10 fixtures, with zero Error/Fatal log entries and preserved saves. Open `C:/Users/j6sis/.codex/worktrees/flight-loop-reset/SpaceSurvival/Play Packaged Review.cmd`; it uses a separate review profile. First check steering/braking/firing, then pad admission and walking/customization. The [reset receipt](validation/2026-09-21-flight-loop-reset.md) binds the build, images and retained failures. **Still open:** lead owns the remaining station composition/signage work and capability gaps below; owner feel and visual acceptance remain separate. Build21 passed all 91 Unreal tests, including the subsequent mouse/stick pitch parity, live-reward capture and incoming-docking pause regressions. Earlier repairs cover physics/update ordering, the zero-trim braking loop and solid-pad readiness during editor mesh compilation. Automated input does not establish physical-device feel. Physical keyboard/mouse/controller feel, listening, natural Waves 1–10, a clean-PC launch and representative performance require their own evidence. The measured Phoenix hull/query implementation passed native collision/admission tests: eleven supplied-body/nacelle shapes weld into the existing calibrated mass body, with deployed feet and cargo-ramp envelopes excluded during flight. Dock admission follows the full hull through alignment above the pad and fixed-heading descent. A rear-door boarding animation is not supplied by this reset. Phoenix paint customization remains unavailable: the three supplied materials expose no vector/color controls for the four sections. The service now declares factory finish and rejects unavailable/stale choices without changing saved classic colors; new paint material authoring remains lead-owned follow-up. Existing station art/layout and unrelated reports stay open. No merge or itch publication is authorized by this repair.

**RPT-20260921-02 — OPEN; lead owns the station and asteroid-colony redesign.** Later owner feedback, paraphrased: the entire station can be walked through, assets are ungrounded, ship legs are non-solid, services/customization are missing, the layout looks like random scrap rather than a high-tech station, and the sky is white. The owner explicitly requests a total station redesign. This supersedes preserving the old layout as the active design and keeping wardrobe unavailable at home; the old layout/assets remain backups. The replacement is a separately authored `StationReset/BP_StationReset` with a coherent concourse, grounded service bays, shared physical/visual geometry, and customization in home and midrun hubs. Prices, progression and scoped service transactions remain unchanged. The latest owner direction supersedes a separate white-sky investigation: integrate the atmosphere into the rebuilt composition. Five supplied references establish an industrial steel/grated interior with amber task lights, a circular illuminated landing pad, connected colony buildings/bridges and a distant skyline, inside or supported by the hollow asteroid already in the asset library. The playable district needs physical boundaries; surrounding colony massing may provide background scale. Measure the large, high-triangle asteroid before placement; world scale alone does not reduce geometry cost. Preserve the original and author an optimized private derivative if required.

**Rendered outcome, September 21 08:41 UTC: improved, reference target NOT MET.** Lead and independent review of packaged capture `76061c816e81494899f2c1cb5eda502f` confirm clearer pad/bridge surfaces, corrected colony materials, solid roof/entry trim, readable amber consoles and dark space. The exterior still has a sparse, symmetric hall and two small ring habitats against a large empty rock face; it lacks the layered building heights and connected colony skyline in the references. The broad hall uses repeated panels/consoles, floating labels are oversized, and the floor under the ship remains dark. These are **lead-owned art/design gaps**, not acceptance work delegated to the owner. Three artistic assessment cycles are recorded, with no further lighting/design iteration in this pass. Next art work must address the composition and signage as a coherent design, preserving the verified physical routes and services. Package2 also exposed a missing portal light-mask asset: the exact cook fix is in source `7a63b03`; Package3 and both final runtime fixtures passed with that error absent. No fixture success closes this owner report.

## Current instruction: ACT-11 purchased-module execution pass, hero first; ACT-03 hold lifted by new owner direction

**Latest owner direction, September 16 10:40 UTC (ACT-11; lead):** the owner reported ten further defects in how the already-purchased modules are executed in game, recorded as RPT-20260916-11 to RPT-20260916-20, and authorized a correction pass. **The September 16 hold on ACT-03 environment iteration is lifted**, superseded by concrete direction plus five reference images showing fog, volumetric light rays and layered depth; the stated design goal is that the field should feel like there are only some right ways to go. The owner also authorized porting **Ship Core PRO** from the 5.6 engine install, dialling it in inside a small test environment, and carrying those settings across. Owner instruction on process, recorded verbatim in effect: every one of these tasks is to be tracked here and individually confirmed complete before the work is called done. Three parallel investigations are running over AGENTS.md and the reported defects, the environment brief, and the danger and impact brief; none of their conclusions are recorded as fact until verified. Facts already established by direct inspection are noted on the individual RPT rows above. Nothing in this entry is a fix or an acceptance.

**September 16 09:20 UTC: published on owner direction.** `0.1.17-alpha` is live on `windows-alpha` as upload 19226459, build **1984728** (from 1979965), packaged source `a77010e`. Butler reports a 398.75 MiB patch (84.60% savings) with 77.19% of old data re-used; these are publisher figures, not measured client results. The lead recommended holding twice because the gallery entry defect (RPT-20260916-10) is open and undiagnosed; the owner reaffirmed publication, noting the page is restricted to the owner and one tester. **The shipped build therefore contains a known intermittent defect: the station ALIEN WORLD doorway can ignore the interact key until the game is relaunched.** Tell the tester. [Release receipt](validation/2026-09-16-itch-0.1.17-release.json).

**Latest follow-up, September 16 09:05 UTC (ISS-11; RPT-20260916-10; lead):** owner hands-on play of the packaged `0.1.17-alpha` candidate found the station ALIEN WORLD doorway silently unresponsive, then working after a reload. In the failing session the `E / A   ALIEN WORLD` interaction hint was displayed and other station consoles responded, but the key produced no transition, no on-screen message and no log line. The packaged session log for 08:34-08:50 UTC contains no `ALIEN_GALLERY_LOAD_FAILED`, no `ALIEN_GALLERY_VIEW_FAILED` and no level-instance load, so `USSAlienGallery::Enter` returned false before `StartLoad` at one of its five silent rejection conditions. Missing content is excluded: the IoStore audit index for this exact package lists both `L_Showcase_level` and `L_assets`. Proximity is excluded because the displayed hint and the interact path share one `ASSStation::NearestService` call at the same radius. The September 16 input-isolation fix cannot explain this, because it applies only while the gallery is already active and here no gallery state ever existed. **This is a second, distinct intermittent defect on the gallery entry path and it is NOT diagnosed.** The scripted fixture cannot observe it: `ASSWave10Soak::TickGallery` teleports the walker to the doorway and calls `ASSGameMode::Interact` directly, never walking and never pressing a key, so the 14 passing packaged round trips do not cover the owner's path. `Enter` has no diagnostic on its rejection path. **Superseded 09:20 UTC: the owner directed publication anyway; see the entry above.** Next bounded operation: log which rejection condition fired, repackage, and capture one owner press. **Owner check:** was the failing attempt at the home hangar, or at a mid-run station after docking? That single fact removes most of the remaining conditions.

**Latest follow-up, September 16 07:55 UTC (ISS-11; lead):** the intermittent packaged gallery exit is reproduced, diagnosed and fixed. Twelve packaged round trips of the unchanged instrumented build failed six times, and every single failure logged `ALIEN_GALLERY_INPUT_RETURN automated=1` immediately before `ALIEN_GALLERY_LEAVE state=2`, at randomly spread points inside the ten-second hold, on both the showcase and asset-layout stages. The cause is input isolation, as the earlier source-backed hypothesis suggested: `ASSPlayerController::PlayerTick` handled gallery return/switch/reset keys before the `bAutomatedSoakInput` guard, and a connected XInput controller is registered and polled inside the offscreen `-unattended` fixture process. Stray `Gamepad_FaceButton_Right` presses called `Leave()`. Load failure, view failure and missing maps are ruled out by marker evidence. The guarded fixture now owns gallery input as it owns other input and records the suppressed key; normal play is unchanged because the flag is set only by the soak fixture, which is absent from Shipping builds. After the fix, 14 of 14 packaged round trips passed while five stray controller presses were suppressed and recorded. 32 source checks, the C++ format audit, the Editor build (27.70s), 51/51 Unreal tests and the Win64 package (184.45s) all pass. Packaged Wave 1 flight, the 16-image Station 5 transition set and a passing IoStore dependency audit (1,604 described exports, zero unresolved imports) are recorded, and the `0.1.17-alpha` payload is prepared locally at 51 files / 2,715,833,034 bytes. Production saves, private assets and the previous archive are unchanged. [Exact evidence](validation/2026-09-16-gallery-input-isolation.json). **Owner check:** the payload is prepared and locally verified but not uploaded, and no merge was performed; publication needs your explicit go-ahead. Hands-on play, natural input, audio, performance and ACT-03 visual acceptance remain open.

**Original packaging failure, September 16 06:22 UTC (historical):** package from `ade88ee` built, but capture `bedaedd587f141f5919ae793245718aa` failed after the doorway. Its first cause was masked by test finalization; the later stage-5 reproduction above is separate evidence. All recorded packaged fixtures preserved production saves. Current candidate and preserved previous archive locations are in PROJECT_STATE. Existing ACT-03 art hold remains in force.

**Owner direction, September 16:** hold further environment/area iteration for now. The owner considers the current scenes improved enough to pause, but did not accept the visual target or close ACT-03. The earlier instruction was to continue until target agreement; stopping at a documented NOT MET checkpoint did not fulfill it. Preserve the current scene and remaining acceptance gaps. Other issues remain in the existing queue; ACT-01 flight/input/propulsion is the next listed production action. No new repair, merge or publication is claimed by this status update.

**September 16 implementation checkpoint: PARTIAL; flight target remains NOT MET after independent review, with the lead agreeing.** Four real area recipes now exist: Obsidian Wreck, Mineral Reach, Alien Causeway and Amber Derelict. World-fixed cells choose coherent authored groups and weighted clutter from the persistent run identity; preview recipes/variations remain reproducible. Three private broken assemblies use the owned alien kit's solid pieces. Richer distant asteroid bands continue through quieter local space. Lighting/haze palettes vary by area. This supersedes the prior proposal-only/fixed-twelve-placement state; it does not change wave durations, progression or Director hazards.

**Art target and closure rule:** the supplied dark metallic wreckfield plus accepted orbital-wreck concept govern scale, irregular structure silhouettes, receding debris, thin depth haze and readable ship/aim space. Dense distant fields should usually remain visible even when foreground space opens up. Lead and independent agent must agree against actual game captures. Counts, build passes and concepts cannot close ACT-03. First area renders were rejected for flat panels, sparse backgrounds and weak depth; their evidence is retained. Current receipt: [area/gallery review](validation/2026-09-16-space-areas-gallery.json).

**Lead-owned acceptance work when ACT-03 resumes:** replace isolated distant scatter with overlapping receding clusters and depth-dependent contrast; assemble alien slabs/arcs into thick architectural groups; remove large masses from the turned ship/aim backdrop. The spherical far distribution improved angular coverage but did not meet the target. Four area previews and a second wreck arrangement exist; compare their final candidate against its target; then demonstrate sustained approach, sparse/dense transition, actual cell crossings and revisit. New cells currently appear/disappear immediately. World-fixed decorative structures have no collision and can be approached through arbitrary routes; the cell-center clearance test is not safe near-surface traversal evidence. Resolve visible boundary changes and the visual/physical mismatch before calling the long-zone experience complete. Continuous motion, natural combat readability and representative performance remain unverified. Do not add collision hazards or alter balance merely to hide a scenery problem.

**Station alien evaluation doorway:** implemented and independently accepted for the bounded rendered entry → full vendor showcase → full asset-layout map → return path. In the rebuilt development game, use E/A at **ALIEN WORLD**; Tab/Y switches maps, Esc/B returns. Run/account and station position are preserved in the scripted round trip. Both vendor maps remain unchanged on disk. First asset-view capture showed only floor; corrected framing visibly includes the modular inventory. Physical input, close inspection/reset and a packaged launch remain open. [Controls and authoring](STATION_EDITING.md). This is an evaluation space, not a new gameplay planet or station rebuild.

PR17 remains draft and unmerged. **Itch 0.1.16-alpha.1/build1979965 does not contain these changes; the shared local Artifacts/Windows EXE now contains the blocked PR17 candidate.** The earlier flight/combat slice, cubic-thruster report, natural audio/input checks and wormhole-plugin pilot remain open under their existing ACT/ISS/RPT entries. The Station Workshop remains available for owner composition work.


### Newly reported bugs — open, capture only

These are paraphrases of the owner's reports, not reproduced findings. Report context follows the 0.1.16 release, but the exact launched build and device/settings are UNCONFIRMED. No fix, retest or acceptance closure is claimed.

| Report ID | Owner observation | Tracking / later verification |
| --- | --- | --- |
| RPT-20260914-01 | Inverting flight controls also inverts character controls. | ISS-05; PT-05,10,15–17. Later verify independent flight/on-foot pitch preferences and persistence. |
| RPT-20260914-02 | Can walk through nearly every station object, but movement is blocked at the words/labels. | ISS-03; PT-10,17. Later map visible geometry to actual collision and service reachability; the report does not prove text geometry itself is the blocker. |
| RPT-20260914-03 | An NPC is stuck in a table. | ISS-03; PT-10,18. Later identify the NPC/location and check body/furniture overlap in natural play. |
| RPT-20260916-11 | The wormhole is just blue rings in a circle and looks bad. | Open / lead; ISS-01; ACT-11 and the wormhole pilot. Capture only for appearance. Related verified fact: the Wormhole Portal plugin ships C++ source and is already installed for 5.8 at EpicGames2/UE_5.8/Engine/Plugins/Marketplace/Wormhole8c083dd18940V1, so adopting it has no engine-version blocker. It was enabled in the working tree on September 16 but not committed. |
| RPT-20260916-12 | When it is time to go to the station you are not guided to it, there is no clear docking, and flying into it kills you even through the window opening. | Open / lead; ISS-03/06; ACT-05. Extends RPT-20260915-07. Capture only: exact approach speed, angle and hull state UNCONFIRMED. Next establish whether Approach draws any waypoint at all, what triggers docking, and the exact code path that turns station contact into death. |
| RPT-20260916-13 | The space station is available before the wave 5 enemies are cleared. | Open / lead; ISS-12; ACT-05. AGENTS.md locks the every-five-wave station cadence, so this is a correctness defect and not a design question. Next find the condition that enters Approach and determine whether it tests remaining enemies at all. |
| RPT-20260916-14 | The lighting effect is not using the Nerves package. | Open / lead; ISS-01/02; ACT-03/11. A23 Nerves sits at Content/NERVES/FX with private derivatives under Licensed/Combat. Next establish which specific lighting effect the owner means and what currently drives it. |
| RPT-20260916-15 | There is a new hero in the downloaded files to try in game; its rigging and animations need fixing, and the tail is probably not rigged. | **Closed for the model and the clips on September 17**, shipped in 0.1.19-alpha: rebuilt, rigged with a real tail, seated, lit, and given an idle, two fidgets, a jog and a run beside its authored walk. The owner later stated the model is their own work ("squirrel is homemade, no license"), so "purchased files" above was the working assumption at the time and is not its provenance. Turn-in-place, head and wrist motion, and the climb-out (RPT-20260917-01) stay open. Previously: Open / lead; ACT-11; ISS-16. **Owner confirmed target:** User downloaded assets/astronaut+squirrel+3d+model.glb, to replace the player walker at the station. **Verified by direct GLB inspection on September 16, not capture only:** 42-joint biped armature, ZERO animations, NO tail bones and NO finger bones, plus a stray neutral_bone. The tail is the largest mesh at 324,940 vertices and is skinned to Waist 62%, R_ThighTwist01 27%, L_ThighTwist01 8% and Spine01 3%, so it will shear with the legs during any walk cycle. Bone names are not UE mannequin names, so retargeting needs an explicit mapping. Model height is about 0.9 m against the current trooper it replaces. |
| RPT-20260916-16 | All the objects in space can literally be flown through. | Open / lead; ISS-01/03; ACT-03. **Partly verified:** SSSpaceScenery.cpp and SSDistantAsteroids.cpp set ECollisionEnabled::NoCollision on all decorative geometry by design, and hittable hazards are separate ASSWorldBody actors. Next decide which reachable objects must become solid without making thousands of instances a physics cost. |
| RPT-20260916-17 | Most objects in the space station are poorly placed and can be walked through. | Open / lead; ISS-03/16; ACT-05. **Partly verified:** ASSStation::AddMesh takes a Solid flag that selects QueryAndPhysics or NoCollision, and several decorative callers pass false, including the alien doorway frame. Next audit every AddMesh call site and separate real geometry from floor paint and signage. |
| RPT-20260916-18 | The menus and prompts do not use input glyphs. | Needs owner retest / lead; ISS-05/13; ACT-08. B23 EasyInputPrompts is copied into `Content/EasyInputPrompts` (gitignored, same as every other licensed pack) and cooked via a narrow `DirectoriesToAlwaysCook` entry scoped to `Datas/IconsData` only, never the vendor demo content or the unused PlayStation/Switch icon sets. `ASSPlayerController::PlayerTick` now latches a keyboard/mouse-vs-gamepad `ESSInputFamily` from the same keys it already polls, updated above every early return (including the alien gallery's) at `SSGameMode.cpp:1476`. `ASSHUD::Glyph()` reads the vendor `PDA_KeysIconsMapping` Blueprint asset's `KeysIcons` map through reflection (no native mirror of its schema) and draws the matching texture, falling back to the key's own display name if the icon pack is absent from a build. Wired at the three single-key interact prompts (beacon, station service hint, ship reward hint); the long paragraph-style control lists in the Settings panel and event announcements still spell out both device names as plain text, since giving those true inline icon runs is the vendor's own RichText-decorator scope, not this pass. Gamepad glyphs default to the Xbox set; PS/Switch brand detection and real per-controller hardware identification are still undecided, per `IMPLEMENT.md`'s Windows-first scope. Editor build, 32 source checks and 51/51 automation pass; the icon textures rendering correctly at actual HUD scale in a live session has not been eyeballed. |
| RPT-20260916-19 | The asteroids do not give the fill effect wanted; the owner's reference scenes use fog and rays of light. There are too few asteroids you can actually hit and the difficulty needs to be higher. The goal is to feel like there are only some right ways to go. | Open / lead; ISS-01/02/12; ACT-03. **Supersedes the September 16 owner hold on ACT-03 environment iteration.** Five owner reference images supplied. **Verified:** SSAmbientPresentation.cpp creates a volumetric fog component and then disables it, with density 0.000001, black inscattering and albedo, extinction scale 0 and SetVisibility(false). Next translate the references into concrete fog and light-shaft values without repeating the rejected excessive-fog trial, and design readable lanes rather than an even scatter. |
| RPT-20260916-20 | The game is supposed to feel like survival and danger. A random rock flies near you and enemies jump in front of you and sit there. Asteroid impact has no effect visually or haptically. The owner wants visible ship damage and impacts that knock the ship around true to physics in a game way. | Open / lead; ISS-02/03/06/08; ACT-02/11. **Verified:** a repository-wide search finds ZERO uses of ForceFeedback, CameraShake or PlayHapticEffect anywhere in Source/, and no OnHit, NotifyHit or AddImpulse in gameplay. The ship is kinematic: SSShip.cpp integrates a custom Velocity and calls SetActorLocation, and a Forces accumulator already exists clamped to 4500. Damage is applied numerically through Session::ApplyDamage with no momentum change. Next decide the knockback model and the full feedback chain, and label which parts change survivability. |
| RPT-20260917-01 | The hero floats high above the ship when leaving it: not a suitable animation. The ship has no door yet, so a character climbing out would phase through the hull anyway. **Owner direction, September 17:** stop work on the exit animation and log the gap. Leaving the ship should be the docking motion to landing, and when that animation finishes the hero simply appears outside the ship. | Open / lead; ISS-02/03; ACT-05/06. **Cause confirmed, not capture only:** `ASSWalker::Tick` drives the actor itself between 0.82 s and 1.6 s of the 2.4 s disembark and adds `FMath::Sin(Travel * PI) * 125.f` cm of arc to the interpolated position (`SSStation.cpp`), so the pawn is lifted 125 cm over the hull at the midpoint regardless of what the clip does. The frame the owner saw is `Artifacts/EndgameSoak/9856021450074177907d2a8789a67467/Exit3.png`. The authored clip is not the fault: the arc is the game's own motion. Next, on the owner's direction: replace the arc and the exit clip with docking-to-landing followed by placing the walker outside the ship, and keep the seated-to-standing pose handoff out of it until the ship has a door. **The squirrel hero's disembark clip is therefore not being authored**; its walk and seated clips are. |

Additional owner reports (capture only; same unconfirmed build/device boundary):

| Report ID | Owner observation | Tracking / later verification |
| --- | --- | --- |
| RPT-20260914-04 | The base weapon barely shows anything coming out of the front. | ISS-01/06; PT-06,18. Later review muzzle/projectile visibility from the normal chase camera. |
| RPT-20260914-05 | Combat feels like Space Invaders: enemies line up ahead to shoot rather than create a dynamic space fight. | ISS-06; PT-06,12. Later review approaches, lateral/vertical motion, maneuvering and pressure in natural combat before choosing changes. |
| RPT-20260914-06 | Backgrounds still look graphically weak and fuzzy, like low-resolution artwork. | ISS-01; PT-03,18. Later compare actual runtime resolution, filtering and source imagery; cause unconfirmed. |
| RPT-20260915-07 | The ship died while pulling into the station after catching an entrance edge, bouncing off several times and taking repeated collision damage. | ISS-03/06; PT-09,12,13. Capture only. Later reproduce with the exact build, approach speed/angle and hull state; review entrance snag points, repeated-impact cadence and docking-assist recovery before changing collision. |
| RPT-20260915-08 | Thrusters look like cubes. | Open / lead; ISS-01/02; ACT-01; PT-03,18. Cause confirmed: literal Cube cores plus one recoloured ribbon. Shape/emission/scale are now switchable via ss.ThrusterShape, ss.ThrusterEmission, ss.ThrusterScale and twelve candidates were captured for owner choice; a cone rotation discarded by the attach pass was fixed and the axial variants re-captured. Still open: owner has not picked a shape, and a basic shape is a stopgap. Real fix is a layered plume from owned Pyro, RPG and Sci-Fi systems, sized as its own task. Verify idle, acceleration, boost, brake and damage in motion before closing. |
| RPT-20260916-09 | Owner dislikes the shooting audio and wants it improved. | Open / lead; ISS-08/06; ACT-02/08; PT-06,18. Three causes confirmed: the .125s laser cue retriggers every .12s so every shot is truncated; no pitch or gain varied between one-shots; the cue was picked by name from 208 candidates and is the thinnest of the only seven short enough to fit the fire rate. Per-shot pitch variation is implemented (ss.ShotPitchVariation, 51 tests pass). A 59s labelled audition of 19 candidates at the real fire cadence was delivered; owner picks are outstanding, as is the decision on moving the rapid weapon to a firing loop. Close only after listening and owner review. |
| RPT-20260916-10 | The alien world portal did not respond at the station; after reloading it worked. | Open / lead; ISS-11; ACT-03; PT-18. Reproduced by the owner on the packaged 0.1.17-alpha candidate. The interaction hint was shown and other consoles worked, so proximity and menu capture are excluded; packaged maps are present in the IoStore audit. Cause UNCONFIRMED: `USSAlienGallery::Enter` rejects silently. Next add rejection logging, repackage and capture one press; record whether the attempt was at the home hangar or a mid-run station. |

Owner subsequently authorized the editor workshop and this bounded presentation slice. The unrelated bug-fix pause remains in force.

Lead maintains these reports here while the owner continues listing observations. Existing acceptance cases remain open. Reproduction and repair are paused until the owner resumes them.


#### September 16 verified root causes (read before attempting any of these)

Produced by a 22-agent read-only audit in which every root cause was adversarially re-checked and a completeness
critic then attacked the resulting plan. **Six of nine proposed fixes did not survive that critic.** The diagnoses
below are evidence-backed. The fixes are NOT yet trustworthy and none has been implemented.

**The structural trap that recurs in almost all of these.** The project has two parallel construction paths: a
procedural fallback builder and an authored Blueprint layout. Several obvious-looking fixes edit code that does not
run in the configuration the owner actually plays. `SSStation.cpp:163` short-circuits so `BuildLicensedShell()` is
never called when the authored Blueprint loads, and both `SSStationVisualLayout.cpp:56` and `SSSpaceScenery.cpp:38`
call `SetActorEnableCollision(false)` at ACTOR level, which silently overrides every per-component collision setting
beneath it. Establish which branch executes before editing anything here.

| Report | Verified mechanism | Trap that defeats the obvious fix |
| --- | --- | --- |
| RPT-20260916-13 station before wave 5 | `SurvivalCore.cpp:611-614` advances phase on the timer plus `run.wave % 5 == 0` alone, with no enemies-remaining test. Entering Approach only calls `Director->SetActive(false)` at `SSGameMode.cpp:581`, which stops further admission but leaves already-spawned `ASSEnemy` alive. **Root cause and fix both survived verification; the only one that did.** | Clear survivors with `Destroy()`, never `OnDefeated`, which would award kills, credits, XP and objective progress the player never earned. The projectile half of the proposed fix does not compile: `bPlayerShot` and `SourceActor` are private with no accessor at `SSWorldActors.h:150-152`. |
| RPT-20260916-11 wormhole blue rings | Four mechanisms proven in `SSWorldActors.cpp`: one shared material instance applied to slot 0 only at `:1020`, so the second slot renders untinted self-lit cyan; far rings scaled LARGER than near ones at `:1018` via `Lerp(1700.f, 2300.f, Alpha)`, cancelling perspective; a single global emission at `:1072` instead of distance falloff; and the spin at `:1068-1071` rolling an axisymmetric untextured torus about its own axis, producing no visible motion. | The Niagara mouth, the only non-ring element, was NOT diagnosed and is not in the fix list. Fixing all four ring mechanisms may still leave blue rings. Keep the WormholePortal plugin out of this; that is ACT-04's separate pilot. |
| RPT-20260916-12 no docking guidance | The entire Approach HUD is one static label with no distance, arrow or corridor cue at `SSHUD.cpp:361-372`, and it points at `GM->StationTarget`, the hub origin, rather than at the corridor mouth. | `Hub->CanAssistDocking(Ship)` cannot serve as the alignment cue: `SSStation.cpp:102` returns false whenever hub-local X is below -1675, and the approach begins near X = -17150, so it is false for the entire flight and flips true only once the ship is already inside the doorway. |
| RPT-20260916-12 death through the window | The drawn frame is authored WIDER than the collision gap. `SSStationPresentation.cpp:240-244` places `SM_Groove01` at local Y plus or minus 732 while the solid inbound wall leaves only 700 at `SSStation.cpp:272-273`. With the ship's 105 cm collision sphere the pilot must hold within 595, leaving at least 105 cm of invisible solid inside the visible opening on each side. **Most likely cause of the reported death.** | NOT a one-number fix. That frame is built by `BuildLicensedShell()`, which never runs when the authored Blueprint loads, so narrowing it changes only the fallback hub. Widening the gap instead touches `SSStation.cpp:272-273`, the hardcoded `700.f - Radius` at `SSStation.cpp:102`, `Guide_KeepDockingLaneClear` at `SSStationVisualLayout.cpp:18-19` and pinned assertions at `SSIntegrationAutomationTests.cpp:76-83`. SM_Groove01's real bounds were never measured. |
| RPT-20260916-17 station props | Two distinct halves. Walk-through: the authored Blueprint disables collision at actor level via `SSStationVisualLayout.cpp:56`, so all 367 authored props are non-solid and every per-component setting beneath it is inert. Blocked-at-labels: `SSStation.cpp:69-71` builds each of the eight `SM_Console` service stands with Solid true and then hides it with `SetVisibility(!VisualLayout)`, leaving an invisible solid beside every label. | The crate-proxy fix proposed for this breaks `SSStationEditableLayoutAutomationTests.cpp:99` and `:128`, which assert that fallback and authored collision shapes match one for one. Gate collision symmetrically or plan the test edit. |
| RPT-20260916-16 fly-through space | `SSSpaceScenery.cpp:38` calls `SetActorEnableCollision(false)` in the constructor, which overrides the per-component setting at `:288`. The ship also blocks only `ECC_WorldStatic` at `SSShip.cpp:35-36`, and no WorldStatic geometry exists in the flight world. | There is no small fix. Making landmarks WorldStatic also stops cannon projectiles on them, because the sweeps at `SSWorldActors.cpp:916/924` filter by object type so a response container cannot isolate weapons, while the laser still passes through and enemies move unswept at `:490`, meaning only the player is blocked. Needs authored invisible envelopes per placement. Medium to large. |
| RPT-20260916-14 Nerves lighting | **Referent UNDETERMINED and the investigation's root cause was rejected.** `SSVFXPresentation.cpp:349-351` deliberately disables every Niagara light renderer on every private system, per `docs/ARCHITECTURE.md:133` and `docs/CONTENT_PIPELINE.md:70`. That is a documented architectural decision, not a wiring bug. | Do not start until the owner names the effect. Re-enabling a light renderer reverses documented policy and bypasses the 20-light budget at `SSVFXPresentation.cpp:199`. RPT-20260916-19 is a rival referent, since its subject is also lighting, as fog and light rays. |
| RPT-20260916-18 input glyphs | Two gaps: the B23 pack was never copied out of the gitignored staging root into `Content/`, and nothing in the game tracks the active input device, so every prompt must print both names. | Must carry a `DirectoriesToAlwaysCook` entry or the glyphs ship blank in the package while every test still passes, a failure mode `docs/CONTENT_PIPELINE.md:80` already documents. The device latch must sit ABOVE the gallery early-return in `ASSPlayerController::PlayerTick` or gallery prompts never update. Leave `USSAlienGallery::Status()` alone; it is asserted at `SSAlienGalleryAutomationTests.cpp:97`. |
| RPT-20260916-15 hero | The engine-side swap is NOT a mesh path change. `SSStation.cpp:481-483` sets `bTemporarySpaceHero` from `DoesPackageExist` on the two SciFITrooper paths; both exist on this machine, so the flag is TRUE, the trooper branch at `:485-489` is taken and the fallback branch at `:492-496` is DEAD CODE. A second hero is hardcoded at `SSShip.cpp:110` as the seated pilot `SK_AcornautTailV2`. The authored seated-to-standing blend requires walker and pilot to be the SAME asset, because `SSStationPoseTransition.cpp:61` rejects the pose unless the skeletal mesh names match. The auto-fit scale and sole-offset block at `SSStation.cpp:499-510` is itself gated behind `bTemporarySpaceHero`. | A mesh dropped into the other slot inherits the constructor constants at `:466-471`: 1.5 scale, -90 yaw, 62.9 cm sole offset. The squirrel is 1,958,812 triangles against the current hero's roughly 197,000, with no LODs, on the pawn closest to camera; it needs decimation and an owner triangle budget. Retargeting from the Acornaut clips was the September 16 recommendation; it is **superseded**. Measured on September 17: the two skeletons share four bone names out of 52 and 46, and those four mean different things, so the clips must be authored fresh against the squirrel rig. The constants named here are no longer literals: see the September 17 hero-slot entry below. |

**AGENTS.md verdict.** The audit's own initial claim that the validation section is a stale restatement of
IMPLEMENT.md was REJECTED by its verifier. `AGENTS.md:76` reads "validate every applicable requirement in
`IMPLEMENT.md`, including at minimum", so the bullets are a floor on top of it, and they restate
`docs/GAME_SCOPE.md` section 53, which `AGENTS.md:13` ranks first. Do not delete them; they are the rules file's
only operational statement of the five-wave, two-station cadence. The genuine gaps are narrow. No rule governs
`.uproject` plugin state, which is how four plugin decisions landed in one session with no paperwork.
`AGENTS.md:129` tells contributors to commit content under `Content` without qualifying that `.gitignore` excludes
eighteen roots, which nearly put a 243 MB untracked asset into history. `AGENTS.md:143` cites a bare
`PLAYTEST_TOMORROW.md` that does not exist at the repository root.



#### September 16 verified danger and impact causes (RPT-20260916-20, RPT-20260914-05)

Produced by an 11-agent read-only audit with adversarial verification. **Two earlier statements in this session were
wrong and are corrected here.** An initial grep for the Unreal API names `AddImpulse`, `CameraShake` and
`ForceFeedback` returned nothing and was reported as "no knockback and no shake exist". Both actually exist in
hand-rolled form and the grep missed them. They are not absent; they are imperceptible.

| Finding | Verified mechanism |
| --- | --- |
| Knockback EXISTS but is arithmetically invisible | `SSShip.cpp:347` applies `Velocity += AwayFromContact.GetSafeNormal() * FMath::Min(1400.f, Amount * 20.f)`. The impulse is derived from the hazard's fixed `CollisionDamage`, so it is speed-blind: grazing a rock and ramming it at boost produce an identical nudge. At wave 1 that is 340 cm/s, which the integrator's own restoring law at `:258-259` converts to 81 cm of travel, less than the ship's own 120 cm contact radius. |
| Camera shake EXISTS but is sub-perceptual | `SSShip.cpp:281-283` peaks at 1.5 cm on a single axis, which at the 900 cm camera boom is 0.0955 degrees. Its phase is driven by world time, so the oscillation does not begin at the moment of impact. |
| Controller force feedback is genuinely absent | No rumble anywhere. This part of the earlier report was correct. |
| The contact site is the only damage path with no visual response | `SSWorldActors.cpp:529` calls `Ship->ReceiveImpact(...)` and spawns nothing, while an enemy bolt striking the same ship at `:944-945` gets both a contact-point Niagara burst and a light pulse. |
| The rock is usually not on a collision course BY CONSTRUCTION | `SSWorldActors.cpp:1537` sets hazard velocity to `-Ship->GetActorForwardVector() * drift`, exactly anti-parallel to the ship, so closest approach equals the random spawn offset drawn at `:1505` from a plus-or-minus 2600 by 1700 rectangle. `:1506` additionally refuses any non-field solid spawn near a per-wave `SafeLane` defined at `:1457`. **The game actively guarantees a clear corridor down the player's own axis.** This is the direct opposite of the owner's stated goal in RPT-20260916-19 that there should be only some right ways to go, and the two reports must be resolved together. |
| Enemies "jump in front of you and sit there", verbatim | `ASSEnemy::Tick` at `SSWorldActors.cpp:690-711` has exactly one movement path; Pursuer and Flanker are the same five lines with different floats. It targets a point in FRONT of the player at `:702` and then slaves enemy velocity to the player's own at `:710-711`, so in the player's reference frame the enemy is stationary. Already logged as RPT-20260914-05. |

**Highest-leverage first change, and it is free.** Amplify the existing camera shake and phase it from the hit rather
than from world time. That lifts a hit from 0.0955 degrees to between 0.40 and 0.796 degrees on two axes, a 4.2x to
8.3x increase, with no new asset, no new API, no new serialized field and no new call site. It is provably
survivability-neutral because it writes only `Camera->SetRelativeLocation` on a spring-arm camera while thrust and
shot origin are both actor-based. It breaks no test, because the flight fixture disables camera shake at
`SSFlightAutomationTests.cpp:52`. It also covers five damage sources at once, because `ASSShip::ReceiveDamage` at
`SSShip.cpp:330-338` is the single funnel for asteroid contact, enemy ram, enemy bolt, electrical storm and wreckage.
Severity must be set in that funnel and not in `ReceiveImpact`, because `Session::ApplyDamage` re-arms
`run.damageFeedback` on every damage event at `SurvivalCore.cpp:438`, so a severity stored only on contact would fire
a full-strength shake for a laser graze arriving seconds later.

**Enemy fix is data-only and carries no test risk.** `docs/GAME_SCOPE.md:1218` requires the Pursuer to aggressively
close distance and `:1221` requires the Flanker to use wider approach paths; neither does either today. Changing
`FSSEnemyDefinition(Pursuer)` `LongitudinalAmplitude` from 900 to 2600 and `LongitudinalRateRatio` from 0.43 to 0.9
makes the station-keeping point sweep through and behind the player instead of parking ahead of it. Both floats are
required: at ratio 0.43 the sweep period is 20.7 s at wave 1, far too slow to read as a pass. The Flanker already
sweeps and should be left alone.

**Scope boundary, stated plainly.** The owner's two requests land on opposite sides of the line.
Visible hull damage is **presentation**: a material driven by hull fraction writes only pixels, and deleting the
feature leaves every number bit-identical. Knockback magnitude is a **mechanic change** and needs explicit owner
acceptance plus a Waves 1 to 10 retest. The arithmetic reason in one sentence: the Director guarantees 420 cm of
surface-to-surface separation between solid hazards at `SSWorldActors.cpp:100`, today's maximum displacement is
396 cm which sits just inside that guarantee, and the proposed maximum of 569 cm sits outside it, so a hard hit could
carry the player into a legally spawned neighbour it previously could not reach. It is NOT a new mechanic and not a
scope violation: `docs/GAME_SCOPE.md:384-389` authorizes deflection, momentum loss and control instability, and `:398`
authorizes Kinetic knockback by name. One consequence to accept deliberately rather than discover: a braking ship
rammed head-on by a wave-3 enemy would briefly be pushed backwards.

**Held for owner sign-off, not in this pass.** A three-phase approach, attack-run and break cycle; moving enemy
spawns to an off-frame bearing, whose proposed audio mitigation does not work because `WarnThreat` sits behind a
single global six-second alarm lockout at `SSGameMode.cpp:218` already consumed by hazard warnings; and any cut to
enemy `Health`, which is rejected outright because `docs/production/OWNER_FEEDBACK.md:21` records F05, that shooting
enemies already felt too easy.

**Trap for any future spawn work.** `ASSEncounterBeacon::Accept` at `SSWorldActors.cpp:1364-1370` spawns DistressCombat
enemies with a direct `SpawnActor` that never calls `FindSafeSpawn`: seven enemies in a rank abreast, dead ahead,
alternating Pursuer and Flanker. Any fix routed through `FindSafeSpawn` bypasses it entirely.



#### September 16 RPT-20260916-14 referent RESOLVED by the owner, and the diagnosis inverted

The owner identified the effect: **the blue circles of electricity that appear as a hazard to avoid around wave 4**,
described as "39 second slop art". That is `ESSWorldKind::ElectricalStorm`. The report title says the lighting is not
using Nerves. Direct inspection shows the opposite, and the real problem is different from what the report implies.

**Nerves is already wired.** `Scripts/AuthorCombatVisualPass.py:36` binds the `ElectricalField` effect to
`Content/NERVES/FX/NS_ElectircBeams_Blue`, the owned A23 Nerves system, using the vendor's own misspelling of
"Electirc" that `docs/CONTRIBUTOR_ONBOARDING.md` warns about. `SSWorldActors.cpp:202-204` attaches it at runtime, and
the comment immediately above it at `:199-201` records why the attach is deferred: otherwise "every storm silently
keeps the small-rock default and never receives its owned Nerves beam."

**The slop art is a second, separate visual rendering at the same time.** `ASSWorldBody::UpdateVisual` at
`SSWorldActors.cpp:223` sets the storm's static mesh to `SM_ElectricalFieldCandidateV3`, a procedural mesh with a
hand-written shader authored by `Scripts/AuthorFieldCandidatesV3.py:19` and `:194` from `ElectricalField.hlsl`. That
ring, not the Nerves beams, is almost certainly the blue circle the owner is describing. The storm therefore draws a
procedural shader ring AND an owned Nerves beam system on top of each other.

**A third factor suppresses what Nerves contributes, and the earlier characterisation of it was WRONG.**
`SSVFXPresentation.cpp:349-351` disables every renderer whose class name contains "LightRenderer" on every private
Niagara system. This was first recorded here as a deliberate architectural decision. **The owner states it was not
their policy and was probably introduced by an agent while working on skybox art, and the evidence supports that.**

Corrected findings, all verified directly:
- It is an **authoring-time bake, not a runtime switch**. `Scripts/AuthorCombatVisualPass.py:103` and `:135` call
  `prepare_private_system`, which is the editor-only `USSVFXPresentationLibrary::PreparePrivateSystem` declared at
  `SSVFXPresentation.h:154`. It calls `Modify()` on the emitter, disables the renderer, then `RequestCompile` and
  waits. The light is therefore switched off permanently inside the derived private assets, including the Nerves
  storm beams. Undoing it means re-running the combat visual authoring pass with the transform changed, not flipping
  a flag at runtime.
- **No rationale was ever recorded.** It entered in commit `189d565`, dated 2026-09-14, "Integrate owned space,
  station, ship and combat presentation assets", a bulk integration commit whose message body is empty.
  `docs/ARCHITECTURE.md:133` and `docs/CONTENT_PIPELINE.md:70` describe it as a fact of the pipeline, in the words
  "dynamic-light renderers are disabled" and "light renderers disabled", with no reason and no owner decision behind
  it. A documented side effect is not a design policy.
- **The 20-light budget warning was wrong and should be disregarded.** The cap at `SSVFXPresentation.cpp:195-200`
  counts `ASSCombatLightPulse` actors, which are this project's own hand-rolled light pulses spawned at `:201`. That
  is a completely separate system from Niagara light renderers, so re-enabling one does not bypass the other.

**Consequence: the Nerves fix is cheaper than first recorded.** It is not a reversal of a considered architectural
decision requiring owner sign-off. It is the removal of a blanket transform for one effect. The remaining real work
is choosing between the two overlapping storm visuals, re-running the authoring pass, and measuring the light cost
of the beams on their own.

**Consequence for the fix.** This is not a wiring job. It is a decision about which of two overlapping visuals is the
storm, plus a documented policy question about the light renderer. The smallest correct change is to make the Nerves
beams the storm's actual read and either remove `SM_ElectricalFieldCandidateV3` or reduce it to a faint containment
boundary, then decide separately and explicitly whether this one effect is allowed a light renderer against the
existing budget. Removing the mesh outright needs checking against the hazard's collision and its telegraph, because
`SSWorldActors.cpp:250-251` sources the catalog mesh for solid hazards and fields alike, and the storm's readable
danger radius is what the player avoids.

**Status:** referent CONFIRMED by the owner, mechanism VERIFIED by inspection, fix NOT implemented and not yet chosen.
The earlier note on this row that the referent was undetermined is now superseded.



#### September 16 verified environment, difficulty and lane causes (RPT-20260916-19)

An 11-agent read-only audit with adversarial verification, which then measured actual captured pixels rather than
describing them. Full working copy retained locally at `.agent/local/audit2-field.md`. Nothing implemented.

**The fog is off by three orders of magnitude, and this is proved rather than inferred.**
`Scripts/AuthorSpaceAreas.py:161` authors `fog_density` as 0.000025, `SSAmbientPresentation.cpp:112` feeds it
straight to `SetFogDensity`, and the engine then divides it by 1000 at
`Engine/Source/Runtime/Renderer/Private/SceneCore.cpp:404`. The result is roughly one percent opacity across the
entire six kilometre grid. Its colour at `SSAmbientPresentation.cpp:312` is a near-black near-neutral. There are no
light rays because no `LightShaft` setting exists anywhere in `Source/`, `Scripts/` or `Config/`, so both
`bEnableLightShaftOcclusion` and `bEnableLightShaftBloom` sit at their false defaults.

**Why the earlier fog trial was rejected, measured rather than recalled.** The background of every flight frame is
opaque unlit geometry, not sky: `Scripts/AuthorContent.py:452` spawns a 50 km backdrop sphere and
`ContentSource/GenerateGeometry.py:287` places the starfield at 40 km, and neither is flagged as sky. Height fog
therefore paints every background pixel. A pixel measurement of the rejected capture against the current one shows
the failure signature is not brightness but collapsed contrast:

| | current | rejected fog trial |
| --- | --- | --- |
| luminance p5 | 11.2 | 42.3 |
| p95 minus p5 | 47.8 | **13.1** |
| blue-to-red ratio | 1.33 | 1.22 |

**The untried lever that makes this proposal different.** `FogCutoffDistance` and `FogMaxOpacity` both sit at their
disabled and unbounded defaults and have never been used in this project. Bounding fog at 20 km excludes the 40 km
starfield and 50 km backdrop entirely, so true blacks and the stars survive. That is the structural difference from
the rejected trial, which raised density with no bound.

**Two consequences that overturn the obvious approach.** First, with fog bounded it can only veil pixels that have
geometry inside the bound, so fog CANNOT fill empty negative space; the blue between rocks in the owner's references
must come from the sky, not the fog. Second, brightness is not the discriminator: the reference images measure a
median luminance near 23, effectively identical to the current game frame. **Chroma is.** The references sit at a
blue-to-red ratio between 2.0 and 7.4 against the game's 1.33.

**Difficulty: the cap is not the limiter, the cadence is.** Modelled from verified constants and cross-checked by two
agents, concurrent hittable asteroids FALL as a run progresses: roughly 12 at wave 1, 6 to 7 at wave 5, 5 to 6 at
wave 10. Raising `MaximumActiveThreats` from 24 to 40 alone moves wave 5 from 6.3 to 6.5 rocks. The spawn interval at
`SSContentTypes.h:495-497` is 0.65 to 1.2 seconds and is constant at every wave. Separately the most common rock is
smaller than the ship: `SSContentTypes.h:127` sets `Radius` 95 against `ShipRadius` 120 at `SSWorldActors.cpp:24`,
which is why the 48 percent weighted hazard reads as grit rather than as a rock.

**A real bug, not tuning, and it explains the empty wave 5.** The spawn roll chain at `SSWorldActors.cpp:1721-1765`
is a strict if/else-if with no fall-through. When the roll picks the enemy branch but `SpawnEnemy` returns null
because the enemy cap is full, the entire opportunity is burned, and the cooldown was already re-armed at `:1688`
before the attempt, so a full interval is lost. At wave 5 the climax at `:1722` forces the enemy branch 100 percent
of the time, so once five enemies exist the wave admits nothing at all for roughly 29 of its 40 seconds. Adding a
fall-through to the asteroid branch fixes it without touching the authored beat. **Do not delete the wave 5 clause
itself**; it implements `docs/GAME_SCOPE.md:1166-1176`.

**Lanes: the guaranteed clear hole follows the player's nose.** `SSWorldActors.cpp:1495-1496` builds the spawn window
from the ship's own right and up vectors and `:1506` tests candidates against `SafeLane` in that same ship-local
basis. Every direction the player points is a right way by construction, so the owner's stated goal is currently
impossible. `docs/production/COMBINED_SPACE_LOOK.md:60` already condemns this pattern.
Three options, and the middle one needs an explicit owner decision:
L1, free tuning with no sign-off, rebalance the decorative depth bands so the near field clumps into masses with lit
voids between them; 86 percent of the decorative budget currently sits in the farthest band with 0.12 parallax, a
near-static backdrop that can never form a wall the player flies past.
L2, delete the `SafeLane` test, one line. **Ruled a MECHANIC CHANGE, not tuning**, because `SafeLane` implements
`docs/GAME_SCOPE.md:81`, the guarantee against unavoidable hits. Named, not done.
L3, a real world-space lane field, is three new systems and fights `docs/GAME_SCOPE.md:916` "there is no fixed path".
Phase 2.
Off the table regardless: making decorative scenery collidable to form corridors, per `docs/KNOWN_ISSUES.md:23`.

**Boost currently halves the rock density.** `BoostMultiplier` raises closing speed and the spawn `Lead` scales with
it at `SSWorldActors.cpp:1502`, pushing the spawn plane from roughly 104 m to 206 m. Owner decision: fix it, which
weakens the 3.5 second reaction guarantee, or accept that boosting clears the field.

**Build order matters and is not optional.** With the fog bounded, fog only veils geometry, so adding rocks increases
apparent fog and adding fog increases apparent rock count. Landing both at once makes a bad result unattributable,
which is the exact pattern behind all five prior rejected trials. **One change per capture, never two**, with numeric
accept-or-revert thresholds recorded in the working copy.

**Nothing here closes ACT-03.** `docs/production/COMBINED_SPACE_LOOK.md:64` requires lead plus independent agreement
across three recipes, two run variations, multiple cell crossings, a sparse-to-dense change and a revisit. Four good
cruise stills will not close that gate, and presenting them as closure would repeat the pattern behind every previous
rejection.



#### September 16 owner design model for hazards, and the mechanism behind it

**The owner's model, in their words, supersedes the earlier "lanes" framing.** "You can freely fly through space, but
the dangers, the intensity of each wave does not change, so if you turn around, the same amount of dangerous
asteroids would spawn after you, and ultimately the same level. It is not a single path, it is a single intensity."
Refined immediately after: "close objects do not drift with you, but the other objects in space, the big ones, are
also hazards as turning, even if not scripted. The new ones spawning in, new direction. Make sure it is not every
single thing turns with you."

Read as a specification, that is four requirements. Already-spawned hazards are world objects and stay where they
are. New admissions use the player's current heading, so intensity is preserved whichever way they fly. The large
decorative masses are themselves dangerous to turn into, without being scripted encounters. And the world must not
rotate with the ship.

**This supersedes the L1/L2/L3 lane options recorded above.** The earlier framing treated the goal as carving
corridors and asked whether to delete the `SafeLane` guarantee. That was the wrong question. The goal is uniform
intensity in a persistent world, not an authored route.

**The mechanism, verified directly, is the retention test rather than the spawner.**
`SSWorldActors.cpp:590-592` reads
`if (FVector::DotProduct(GetActorLocation() - Ship->GetActorLocation(), Ship->GetActorForwardVector()) < -16000.f) Destroy();`
The cull projects each hazard's offset onto the ship's **current** forward vector. Nothing moves when the player
turns, but the retention rule rotates with them, so turning around reclassifies the field ahead as "behind" and
destroys it. New admissions then refill ahead of the new heading. The net effect is exactly what the owner describes:
the threat structure is always in front of you and never persists. This is a small, well-localised fix. **It is NOT the highest-value
change, and the earlier claim here that it was has been refuted with numbers; see the correction below.**

**What already matches the owner's model and must not be "fixed".**
- Non-field hazard velocity is set once at spawn, `SSWorldActors.cpp:1537-1540`, and the body then moves in world
  space. It does not track the ship. Close objects genuinely do not drift with the player.
- `ASSSpaceScenery` is world-stable while `AreaRecipes` are in use: `SSSpaceScenery.cpp:68` and `:129` pin the actor
  to `OriginOffset` and cells are computed in world space from the viewer's position minus that origin. Turning does
  not move or reseed near and middle scenery. Its legacy non-recipe path at `:155` does follow the viewer, but
  recipes are active, so that path is not live.
- New admissions already use the current heading, `SSWorldActors.cpp:1494-1496`. That part is correct and is what
  preserves intensity after a turn.

**What does not match and is in scope.**
- The heading-relative cull above.
- `ASSDistantAsteroids` re-poses every instance each tick relative to the viewer with per-band parallax and radial
  shell wrapping, and 86 percent of its 2048 instances sit in the farthest band at parallax 0.12, so the background
  reads as a painted image rather than as geometry.
- The large masses are not hazards at all: `SSSpaceScenery.cpp:38` disables collision at actor level, overriding the
  per-component setting at `:288`, and the ship blocks only `ECC_WorldStatic` at `SSShip.cpp:35-36`.
- Boost thins the field. `SSWorldActors.cpp:1502` derives `Lead` from `ClosingSpeed`, which includes the ship's own
  velocity, so accelerating pushes the spawn plane out.

**Owner rulings recorded this session.**
- **Boost must not reduce difficulty.** It is a strategic tool, not an escape from density. The speed-to-spawn-distance
  coupling is to be removed or compensated. This answers the open boost decision.
- **Fog and rays should vary as the player travels.** The owner's words: "it is not permanent, it is space, there are
  different effects that blend together to make an experience as you travel through." That favours per-region
  atmosphere driven by the existing `AreaRecipes` transition rather than one global setting.
- **More asteroids on screen is wanted, with proper levels of detail**, and the owner has purchased blueprints and
  tools toward it. The earlier note that raising `MaximumActiveThreats` alone barely moves the count stands, but it
  was never a claim that more cannot be rendered; the limiter is arrival rate, not the ceiling.
- **Two Fab sky assets are under owner evaluation, neither installed.** A Volumetric Space Nebula Procedural
  Generator, volumetric shader plus procedural blueprint, UE 5.0 to 5.8, whose own listing warns it is
  computationally intensive and quotes 60 to 80 FPS on an RTX 3060 at 1080p; and Space Skybox Backgrounds 3 by
  Ambient GraphX, nine HDR skyboxes, one material, nine instances, twelve textures at 8192x4096, each nebula's light
  source placed on the +X axis. The second gives a defined sun direction per sky, which is what light shafts need in
  order to point somewhere believable. **Neither removes the underlying defect**: the current backdrop sphere and
  starfield are not flagged as sky, which is why fog paints them, so a better texture on the same unflagged sphere
  keeps the bug. Evaluate against `docs/production/SOLUTION_CATALOG.md` before acquisition; both may already hold
  catalog entries written for a different intended use.



#### September 16 intensity model: implementable plan, and a correction to the claim above

An 11-agent audit with adversarial verification and a 60 Hz simulation of the actual admission code, 30 trials of
180 seconds per case. Full working copy at `.agent/local/audit4-intensity.md`. Nothing implemented. Simulated body
counts are INFERRED, not measured on hardware.

**CORRECTION, recorded against this project's own log.** The heading-relative cull was recorded above as the single
highest-value change in the environment effort. **That is not supported.** The rule only acts beyond 16,000 cm and
the playable field sits inside 10,000, so near-field density is unchanged by it:

| | bodies within 100 m ahead, before | after |
| --- | --- | --- |
| cruise | 4.10 | 4.10 |
| boost | 2.29 | 2.29 |

Fixing retention yields +2.5 percent live bodies at cruise and +20 percent at boost, plus correctness. A discrete
180 degree turn at cruise peaks at 16.1 live bodies and recovers under both the old and new rules; neither empties
the field. **The visible intensity defect is the 44 percent near-field drop under boost, from 4.10 to 2.29**, which
is the boost coupling the owner independently identified. The owner's instinct was right and the earlier ranking here
was wrong. Retention is a precondition that makes every density number mean the same thing at every heading, not a
felt win on its own.

**Ordered plan. Steps are dependency-ordered because retention changes the steady state every later number is
measured against.**

| Step | Change | Scope | Sign-off |
| --- | --- | --- | --- |
| 0 | `SSDistantAsteroids.cpp:260` passes `bMarkRenderStateDirty = true`, which destroys and rebuilds 15 scene proxies every frame for nothing. Set it false. Free saving, no behaviour change. | presentation | none |
| 1a | Replace the heading cull with a per-body world radius fixed at `ASSWorldBody::Configure`, `RetentionRadius = max(16000, spawn distance + 2800)`. One assignment covers all six spawn sites. Rotation-invariant by construction. | **mechanic change** | retest |
| 1b | `SSGameMode.cpp:242` `Earliest` 2.5 to 3.5 so the existing omnidirectional rear-threat warning matches the reaction promise. | tuning | none |
| 2 | Boost admission pace: scale budget accrual and cooldown by forward speed over `Stats().speed`, clamped to 1.85. **This is the step that fixes the felt defect.** | **mechanic change** | retest |
| 3 | Distant field parallax 0.35 and 0.12 to 0.50 and 0.25 so the background reads as geometry. | tuning | none |
| 4 | Big-mass envelopes: hidden boxes on a new object channel, authored inscribed inside the visible mesh. | **mechanic change** | **acceptance + retest** |

**Two of this log's own recorded verdicts are inverted by direct engine evidence.**
- The note above that a response container "cannot isolate weapons" is true and irrelevant. The weapon sweeps use
  `SweepMultiByObjectType`, and the engine's narrow filter consults only the shape's object type, never the response
  container. A shape typed to a new channel is invisible to those sweeps with **zero** edits to the weapon code. That
  is why the object-channel approach was chosen over making landmarks `WorldStatic`.
- The retention flat-radius idea does not work. A flat radius must exceed the maximum spawn radius, 46,220 cm at top
  tier with boost and full throttle, and a flat 46,000 roughly doubles the body count by raising cruise residence
  from 11.24 s to 22.8 s. Per-body, set at configure time, is the only workable form.

**What the big-mass envelopes actually buy, stated before anyone calls it done.** At the built 650,000 cm cell size
and the even/even/even landmark rule, that is one eight-mass group per 13 km cubed, against about 12.6 km of flight
per ten-wave run. Contact probability is **4.0 to 8.8 percent per run, roughly one contact every 15 runs.** Envelopes
fix the visual and physical mismatch. They do NOT make the masses a per-wave threat; that needs about 170 times the
cross-section, which is a density decision for the owner and not tuning.

**Fairness.** Steps 1 and 2 do not relax the no-unavoidable-hits guarantee: that guarantee constrains admission,
step 1 changes only retention and admits nothing, and step 2 raises the rate while leaving the spawn lead untouched,
so the 3.5 second reaction window is identical at every speed. A pure sphere in fact retains **less** to the rear and
flank than today's plane. Step 4 is where the owner is choosing to relax something: a landmark envelope is static
geometry with no telegraph and no admission lead, so hitting one at boost hurts with no warning beyond the mesh being
visible. That is what "the big ones are also hazards as turning" asks for, and it needs explicit acceptance.

**Testing.** Step 1 breaks **zero** tests, and that is the problem: no coverage exists for the invariant it creates.
Three tests must be ADDED, including a full 360 degree yaw asserting that no body is destroyed by rotation alone, and
the first automated assertion of the 3.5 second reaction guarantee anywhere in the suite. The ten-wave journey test is
at risk of flakiness rather than a definite break and must be run repeatedly. The scenery safety test keeps passing
but stops being coverage and must be rewritten to the new invariant.



#### September 16 owner direction: run rhythm, difficulty method and composition targets

**The run should feel like whiplash.** The owner's stated rhythm, in their own words: dodging fast asteroids in a
dense field, then "you think you're out and get ambushed by enemies, battle, then a wormhole yanks you away and
you're somewhere else". Explicitly: **hazards are not always stacking**. Density is a rhythm, not a level.

Consequences that follow directly and are now design constraints rather than preferences:
- **Sparse regions are combat space.** "Less dense areas are great for space combat time." Open volume is where
  fights are legible, so low-density zones are functional, not filler, and must not be treated as empty.
- **A wreck field is a moment, not a biome.** "Flying through broken ships should happen, but it doesn't have to be
  a full scene." The four area recipes should not each become a full-scene wreck.
- **The alien city is a candidate traversal sequence.** "You could probably make it fly through the alien mega city,
  and dodge the pillars and there's the doors." This is reachable rather than speculative: `USSAlienGallery` already
  streams the complete vendor maps `L_Showcase_level` and `L_assets` into the live world through
  `ULevelStreamingDynamic::LoadLevelInstance`, and both are cooked into the package. Today it is an evaluation
  doorway with the run frozen. Turning it into a flown sequence is a scope decision, not a technology problem, and
  it is NOT authorized by the remarks above; record it and ask.

**Difficulty method, owner-stated and now the working rule.** "I think maybe it's harder, and work and dialing it
down, is proof of concept, where easy and dialing up can be weak." So the environment and hazard passes tune toward
the hard end first and are reduced against real play, rather than starting safe and creeping upward. Combined with
the fog rule below, the general principle is: **build it in, then take it away.**

**Fog is per-zone, and some zones are fogless.** "There should be fogless zones too, but it's easier to take it away
than it is to add it." Implemented: `FSSSpaceAreaRecipe::FogDensity` carries height fog per region, blended between
the two nearest recipes on the same smoothing as haze and key light, so crossing a boundary fades one zone's fog out
and the next one's in. Authored as ObsidianWreck 0.0042 as the eerie one, AlienCauseway 0.0030, MineralReach 0.0012,
and **AmberDerelict at zero, genuinely fogless**, for hard edges and full contrast.

**Megastructure must be solid and some pieces must be hazards.** Owner: "megastructure needs to be solid too, not
fly through, and some of those can become debris themselves, bigger, maybe faster, the more it feels like you
actually have to dodge." Two separate pieces of work. Solidity is the envelope approach already designed under the
intensity plan. Making structural pieces into admitted hazards that move is new: it puts region content into the
hazard budget, which `docs/GAME_SCOPE.md:919-923` currently separates from the Director. **Not authorized by the
remark alone; it needs an explicit decision and a retest.**

**Wave one is not exempt.** "Yes it's wave one, but somehow we need to scale it." The first wave should already
demand dodging rather than serving as a tutorial lull.

**Composition targets.** Six further reference images were supplied and one is labelled COMPOSITION TARGET, NOT
GAMEPLAY. Read as a brief rather than a specification, and the owner notes these are some targets and not all of
them. What they show that the current build does not:
- **Scale.** Structures dominate the frame and the ship is small against them. Current landmarks are large but never
  dominating.
- **A cropped foreground.** A structural piece enters from the frame edge, very close. The current field has no
  extreme foreground element.
- **A warm and cool split.** A visible sun on one side, cool tones on the other. The current look is monochrome blue.
- **A dark centre.** Deep blacks survive in the middle of the frame despite atmosphere. The first fog pass went
  uniformly pale, which is the specific defect to fix.
- **A distant landmark for scale reference**, such as a far ring station silhouette.
- **Navigation markers.** One mockup carries glowing waypoint hexes and an objectives list. That is directly
  relevant to the open report that the station gives no approach guidance.



#### September 16 per-system concept art located, and what it changes

The owner's concept set is **already in this repository** at `art/`, dated September 14, and was not being used.
Eighteen files named per game system: `asteroids`, `wormhole`, `storm`, `gravity`, `station`, `wreckage`, `depot`,
`climax-10`, `between-waves`, `combat`, `hangar`, `key-art`, `ship-hero`, `ship-interceptor`, plus `hero.mp4` and
the Acornaut portraits. The same set plus `teaser.mp4` sits in the owner's Drive under AI/art, with a pitch deck in
AI/screenshots. **Owner framing, September 16: these are concept images, not specifications. "Closer we get the better."** They are directional references for mood, scale and palette. They do not define any system, and at least one of them, the wormhole, is explicitly not the target. The owner also notes the set lacks a dangerous asteroid field, because density and threat read from motion rather than from a still, and that a separate AI-generated motion video was supplied for that feel. Treat every entry below as a direction to move toward, never as an acceptance bar. Three
were read this session and each changes a currently open item.

**`art/wormhole.jpg` is a mood reference, NOT the wormhole target. Owner, September 16: "no the wormholes won't be like that".** The paragraph below was written before that correction and overstated the image's authority; it is retained only as a record of what the concept art shows. **Do not re-scope the wormhole against it.** The four recorded rendering faults under RPT-20260916-11 stand on their own evidence and remain the actionable work. Superseded reading follows. The target is a vast luminous **spiral vortex** that
fills most of the frame, with a bright warm gold and cream core, rock and debris caught in the arms and drawn inward,
deep black space to one side, and enemy silhouettes against it. It is a funnel with flow, at enormous scale.
The implementation is concentric blue rings. That is not a tuning gap, it is a different object. The four rendering
faults recorded against RPT-20260916-11, single-slot material, far rings larger than near, one global emission and a
roll that renders nothing, are all real, but fixing them yields a better ring stack rather than this. **Re-scope the
wormhole against this image before spending effort on the rings.** It also strengthens the case for evaluating the
owned Wormhole Portal plugin under ACT-04, since a flowing funnel with captured debris is closer to what that plugin
does than to what the current primitive does.

**`art/storm.jpg` confirms the Nerves referent and the pack choice.** The target is the ship engulfed in a web of
branching blue-white lightning with a visible spherical containment shell around the hull, arcs forking outward in
every direction, against deep blue cloud. That is electrical arcs enveloping the player, not a ring on a plane.
`NS_ElectircBeams_Blue` from the owned A23 Nerves pack is the correct source and is already bound. This makes the
recorded fix concrete: the procedural `SM_ElectricalFieldCandidateV3` ring should stop being the storm's read, the
Nerves beams should become it, and the arcs need to reach the ship rather than sit at a radius. It also settles the
light question in favour of restoring the renderer for this one effect, because the target is lit by its own arcs.

**`art/asteroids.jpg` corrects the fog assignment for the rock zone, and it is a HUD reference too.** The background
is deep blue-black with only a faint nebula wash, not pale fog. Rocks span an enormous size range, from one filling a
quarter of the frame to specks, and the near ones carry heavy **motion blur** that sells speed. So the asteroid field
target is closer to the fogless and light-fog zones than to the eerie one, and the missing cue is scale variance plus
motion blur rather than atmosphere. The shot also carries a speed readout, a threat count on the radar, an objectives
list and weapon ammunition, which is a reference for the open input-glyph and station-guidance reports.

**Method note for whoever works these next.** The art was sitting in the repository unused while this project
iterated on the look from general reference. Check `art/` for a per-system target before starting any visual work.



#### September 16 concept motion video: what the stills could not show

The owner supplied a 47 second AI-generated concept video, 1920x1080 at 24 fps, because the still art "lacks a
dangerous asteroid field" and density and threat only read from motion. Frames were extracted locally at six second
intervals with the ffmpeg that ships alongside this machine's Lian Li software. **Directional reference, not a
specification, and the owner notes it is AI video.**

**The single largest gap it exposes: motion blur is implemented and defaults to OFF.**
`Source/SpaceSurvival/Domain/SurvivalCore.h:192` reads `bool subtitles = true, cameraShake = true, motionBlur =
false;` and `SSGameInstance.cpp:153-154` sets `r.MotionBlurQuality` to 3 when on and 0 when off. In the video, heavy
radial streaking on the near rocks is the dominant cue for speed and danger; every capture this project has ever
produced is razor sharp and therefore reads as slow no matter how many rocks are present. That is a default value,
not missing work. **It is a player-facing accessibility setting and must not be flipped silently**, since motion
blur off is a common accessibility default and this project already exposes the toggle in its own menu. Two options
for the owner: change the shipped default, or leave the default alone and enable it for scripted captures so that
evidence frames represent the intended look instead of contradicting it.

**What the frames show, consistently across the space beats.**
- Density well beyond anything currently authored: rock fills the frame from the near edges to a vanishing point,
  with no empty background visible at all in the dense beats.
- A radial, tunnel-like composition. Debris converges toward a point ahead, so the player reads as flying *into*
  something rather than *past* it.
- Large masses passing very close to the frame edges, near-miss framing rather than clearance.
- Deep blacks between the rocks with bright rim lighting, high contrast. Not the pale wash of the first fog pass.
- A chase camera close behind the ship, with the ship occupying a substantial part of the frame.
- Combat happening inside the dense field, with enemy craft flanking and tracers crossing, rather than only in open
  space. Note this sits in tension with the owner's earlier remark that sparse regions are combat space; both may be
  true at different beats, and it is not resolved here.
- Navigation markers rendered as small coloured hexes ahead of the ship, orange and blue, and a targeting indicator.
  Another data point for the open station-guidance and glyph reports.

**The station interior beat is warmer and far denser than the current station.** Amber industrial hangar, overhead
lighting strips, gantries, stacked crates and machinery filling the volume, with the ship parked inside. The current
station reads cool, grey and sparse by comparison.

**Working copy of the extracted frames is not retained in the repository.** The source video is the owner's, at
`C:/Users/j6sis/Downloads/Game concept video.mov`, and the Drive original is in AI/. ffmpeg is available at
`C:/Program Files/Lian-Li/L-Connect 3/ffmpeg.exe` for anyone repeating this.



#### September 16 effect inventory: 193 owned Niagara systems, and a purpose-built fog bank set

Prompted by the owner asking whether other owned effects suit distant work. They do, and the current effort was
hand-rolling things the library already provides.

**193 Niagara systems are owned and outside the private derivative folder.** By pack: Sci-Fi Weapons VFX 84,
Niagara Examples 67, Pyro 22, RPG Environment VFX 13, Nerves 7. The project's combat visual data binds eleven roles.

**`Content/NiagaraExamples/FX_Fog` is a purpose-built fog bank set and is the direct answer to the owner's request
for distant fog pockets.** It contains `BP_FogBankVolume` and `BP_FogBankCard`, a presets asset, and **three seeds
each of `SVT_FogBank` and `SVT_FogBank_Whisps` as sparse volume textures**. Three seeds means built-in variation,
which matches the owner's requirement that zones differ per playthrough. This is Epic's own authored solution and it
supersedes the hand-built cloud-bank approach currently in `ASSAmbientPresentation`, which places two static meshes
carrying a volume material and which the current pass could not get to render at distance.

**Other candidates found for distant and ambient use, none currently used:**
- **Fourteen** `NS_Simpl_Lightning_1` to `_14` in the Sci-Fi Weapons pack. A family of simple lightning systems,
  far more likely to suit distant flanking arcs than the Nerves beams, which are authored for close work and are
  what three failed placement attempts were fighting.
- `NS_MagicalGlowRays` in RPG Environment VFX. Directly relevant to the still-unimplemented light shafts.
- `NS_Player_Electricity_Looping` in the Niagara examples, a looping electrical system.
- `NS_Ground_Energy`, `_1`, `_2` for energy fields, and `NS_Smoke_Plume` and `NS_Chimney_Smoke` for drifting volume.
- `NS_Boundary`, `_Box`, `_Cylinder`, `_Sphere` for visualising volumes, useful when authoring lane or hazard bounds.

**`Content/NiagaraExamples/GalleryLevel.umap` exists**, which is the pack's own showcase level. Opening it is the
fastest way to audition any of these at real scale before wiring anything, and nobody has done so.

**Consequence for the ambient storm work.** The Nerves beams are wired, load and compile, and do not render at any
of the three placements tried. Rather than a fourth placement attempt, the next step is to audition the simple
lightning family and the fog bank volumes in the gallery level, pick what actually reads at distance, and wire that.
This is the same lesson already recorded twice: check what is owned before building, and audition in the vendor's
own showcase before integrating.



#### September 16 thruster cause: a literal engine cube, and a rotation that never survived

RPT-20260915-08 said the thrusters look like cubes. They are cubes.
`SSAmbientPresentation.cpp` loaded `/Engine/BasicShapes/Cube.Cube` and assigned it to `EngineCores`, one per nozzle,
scaled long on X and lit by an emissive dynamic material. Nothing tapered anywhere. The only other layer is a single
recoloured ribbon, `NS_DeepSpaceExhaust`, which `Scripts/AuthorDeepSpaceExhaust.py` derives from Epic's
`NS_SimpleRibbonTrail`. So the whole exhaust is one box plus one thin ribbon.

**Shape is now switchable and twelve candidates were captured for the owner.** Three console variables were added,
`ss.ThrusterShape` (0 cube, 1 cone, 2 sphere, 3 cylinder), `ss.ThrusterEmission` and `ss.ThrusterScale`, with matching
parameters on `Scripts/CaptureSpaceLook.ps1`. Twelve variants were captured at full boost on one seed and camera and
tiled into a labelled contact sheet, so the choice is the owner's rather than the implementer's taste.

**A second defect surfaced from those captures: the cone rendered point-first.** The cone and cylinder orientation was
being set in `BeginPlay`, but the later attach pass unconditionally called `SetRelativeRotation(FRotator::ZeroRotator)`
on every core and silently threw it away. The mesh kept its default +Z axis, which reads as a cone standing on end
with its apex at the nozzle and its base flaring away, the reverse of a real plume. Fixed by moving the orientation
into the attach pass behind shared `ThrusterCoreIsAxial` / `ThrusterCoreRotation` helpers, so the rotation and the
axis swap in `Tick` cannot drift apart again. An axial mesh also straddles its own origin, so half its flare sat
inside the hull; it is now shifted aft by half its length to seat the wide end at the nozzle lip. The axial variants
were re-captured after the fix, since the first sheet showed them inverted.

**This is a stopgap, and the owner has said so.** A basic shape with an emissive material is not a thruster; it is a
placeholder that stops reading as a box. The owner supplied a store-page reference for a dedicated thruster VFX pack
(Shogun Games, not owned, "might be too far without the bundle") and noted that the owned explosion kit mixed with the
RPG effects could get closer. That is the right instinct, and the reference decomposes into four layers, all of which
have owned candidates:

| Layer in the reference | Owned candidate | Note |
| --- | --- | --- |
| Hot inner core with hard bloom | current emissive mesh plus `NS_DeepSpaceExhaust` | the only layer that exists today |
| Turbulent billowy shell, widest at the nozzle, tapering | `PyroVFX/NS_Fire_FX_System_01..03`, `MI_Fire_*`, `T_Fire_*`; Sci-Fi `M_Smoke_Ribbon`, `T_Smoke_Light` | the layer that actually sells it |
| Spark spray shedding downstream | `RPGEnvironmentVFX/NS_ForgeSparks`; `PyroVFX/NS_Debris_FX` | cheap, high perceived detail |
| Nozzle glow and rays | `RPGEnvironmentVFX/NS_MagicalGlowRays` | same asset already wanted for light shafts |

**Honest sizing.** This is not a script one-liner. The Pyro fire systems are authored for ground explosions and rise
rather than travel: the pack names its own material instances `MI_Atomic_Ex_RiseUp`, `MI_Car_riseup01`,
`MI_LargEx_riseup1`, `MI_MEx_Rise_Up_02` and so on, so the upward drift is deliberate and pervasive. Used as a plume each needs its velocity redirected along the ship's aft axis, buoyancy
zeroed, lifetime cut to the plume length and colour driven from the existing `ExhaustColor` vector parameter pattern.
That is real Niagara emitter work per layer, in the editor, with a capture pass per iteration. It is worth doing and
it is reachable with assets already owned, but it should be scheduled as its own task rather than folded into the
shape swap.

**Also found while inventorying: `Content/Vefects` contains `Cam_Shake` and `Cam_Shake_Slight`.** Owned camera shake
assets, unused. Relevant to the open impact-feedback work, which currently hand-rolls a sine offset on the camera.



#### September 16 shooting audio cause: the sample is longer than the gap between shots, and nothing varies

RPT-20260916-09 said the shooting audio was an awful choice. Three separate causes were confirmed by reading the
code and measuring the source recordings; none of them needed a listening session to establish.

**1. The Rapid Laser retriggers before its own sample finishes.** `SSPhase1Data.h:230` sets `LaserInterval = 0.12f`
and `SSShip.cpp:368` reloads the cooldown from it, so the weapon fires 8.3 times a second. The bound cue,
`aliengun001singleshot`, measures **0.125 s**. Every shot is cut off by the next one. Nothing ever rings out, and the
result is a continuous stutter rather than a sequence of shots.

**2. Nothing varies between shots.** `SetPitchMultiplier` appeared nowhere in `SSAudio.cpp`; every one-shot played at
exactly the same pitch and gain. Eight bit-identical, phase-locked copies per second is what makes a weapon read as
a mechanical buzz rather than a gun. **Fixed:** `CreateVoice` now applies a per-shot pitch deviation to one-shots
only, walking a fixed twelve-entry table rather than drawing at random so that captures and the automation suite stay
reproducible. Depth is `ss.ShotPitchVariation`, default .055. Loops are untouched. 51 automation tests pass.

**3. The sample was chosen by name, not by ear, out of 208 candidates.** The binding lives in a dictionary in
`Scripts/PrepareOwnedAssetPass.py`. The weapons library holds 208 sounds; **only seven are 0.125 s or shorter**, and
of those seven `aliengun001singleshot` has the highest zero-crossing rate, meaning it is the thinnest and most
beep-like of the only options that fit the fire rate. The pack also ships `Laser001`-`Laser007`, ten `gatling*`
bursts and three `Laser*loop` files, none of which were ever considered.

**The architectural point.** A weapon firing every .12 s is not a one-shot weapon. The pack shipping `Laser008loop`,
`Laser009loop`, `Laser010loop` and ten gatling bursts is the vendor saying the same thing. A start / loop / stop
firing voice would fix the truncation, the repetition and the voice-count pressure at once, and it is how rapid
weapons are normally built. That is a design change, not a sample swap, so it is the owner's call.

**Audition delivered to the owner.** The raw WAV is embedded verbatim inside each `.uasset`, so all 208 were
extracted directly with no editor round-trip, measured for duration, peak and brightness, and rendered into a 59
second labelled video: eight laser one-shot candidates each played as eight shots at the real .12 s cadence, first
flat and then with the new pitch variation; five firing-loop candidates; six heavy cannon candidates at the real
.85 s cadence. Candidates are played at the in-game rate rather than in isolation, because the rate is most of the
complaint. The current bindings are included as controls. **Awaiting the owner's picks.**



#### September 16 thruster material audition: the owner chose the wide cone, then asked for distinctive materials

The owner picked `05-cone-big` off the shape sheet, so cone at emission 6 and scale 2.6 are now the shipped defaults
in `SSAmbientPresentation.cpp`. The console variables stay, because further review passes need them.

They then asked to "play with mixing colors/materials to get unique effects", naming the galaxy shaders in
particular. **Two hundred and twenty-two owned master materials are plausible for a glowing plume**, found by
scanning every `.uasset` under `Content/` for the blend mode, shading model and two-sided flags left in the package
name table. That is a fast and unprivileged read, and it is inference rather than proof, but every candidate it
produced did load and render, which is the only confirmation that matters here.

**Seventeen were wired into an audition table** behind a new `ss.ThrusterMaterial` index, with a matching
`-ThrusterMaterial` parameter on `Scripts/CaptureSpaceLook.ps1`, and captured on one seed and camera at boost.

**A borrowed material needed one piece of real work, not just a path swap.** The core is driven by
`SetVectorParameterValue(TEXT("Tint"))` and `SetScalarParameterValue(TEXT("Emission"))`, and a parameter a material
does not declare **fails silently**. A borrowed VFX material names its parameters whatever its author liked, so every
one of them would have sat at its authored colour and ignored the drive state entirely, which reads as a bug rather
than as a look. `BeginPlay` now asks the chosen material what it exposes, via `GetAllVectorParameterInfo` and
`GetAllScalarParameterInfo`, keeps the names that match a known colour or strength vocabulary, and `Tick` drives
whatever was found. A material that loads but declares nothing usable is a legitimate outcome and simply keeps its
authored look; a material that fails to load falls back to the project emissive and logs a warning rather than
leaving the nozzles unlit.

**What the audition showed.** Genuinely distinctive: `M_BrightCore` (hot orange chemical burn), `M_Deadly_Beam`
(cyan crystalline), `M_Star` (clean vivid blue), `M_Skybox_Nebula` (dark navy, unlike anything else in the set),
`M_Cosmic_Master` (purple marbled), `M_FresnelGlow` (green with a lit rim), and `M_VFX_Lush_Galaxy_Shader`, the one
the owner named. Two failed honestly: `M_Cable_Glow` blows out the whole frame, and `M_ElectricalFieldCandidateV3`
renders nothing from this angle. Both are presentable as defects rather than as omissions, and neither is worth
chasing unless the owner wants that entry.

**Still a stopgap.** This is a single mesh wearing one material. The layered plume recorded above, core plus
turbulent shell plus spark spray plus nozzle glow, is unchanged by this work and remains the real fix.



#### September 16 correction: the material switch shipped with two defects, both found by adversarial review

An eight-agent survey with an adversarial verification pass was run over the material work after it was committed.
It refuted two claims the implementation rested on. Both were real and both are now fixed. Recording them because
each is the same failure mode that produced the cone-rotation bug earlier the same day: **a write that silently does
nothing, or silently does too much, and looks plausible in a screenshot either way.**

**Defect one, a regression introduced by the material switch: the drive colour was being squared.**
`Scripts/AuthorContent.py:138-139` authors `M_Emissive` with **two** vector parameters, `Tint` and `Color`, and the
graph multiplies them into emissive. The original code drove `Tint` each tick and pinned `Color` to white once. The
new code matched **both** names and drove both with `DriveColor` every tick, so the shipped default thruster was
rendering `DriveColor` squared. Every capture in the first audition sheet carries that error.

**Defect two, the one the change existed to prevent: the name list matched almost nothing.** Vendors do not write
`Emission`. Read out of the packages directly, the real parameter names are `Emissive Gain` and `Glow Exponent`
(`M_BrightCore`), `Main Color`, `Main Glow`, `Glow Boost` (`M_Cable_Glow`), `Additive_Color` (`M_Skybox_Nebula`),
`Galaxy Tint` and `Galaxy Emission Intensity` (`M_VFX_Lush_Galaxy_Shader`), `Base Color` (`M_FresnelGlow`). An
exact-name list matches none of those, so the drive state silently did not reach most of the table.

**The fix.** Names are normalised, lowercased with spaces and underscores dropped, then scored. **Exactly one**
colour parameter and one strength parameter are claimed, highest score wins, which is what stops `Tint` and `Color`
both being driven. Shape and animation controls are rejected outright by substring, so `Glow Exponent` and
`Distortion Gain` are not mistaken for brightness. The chosen names are written to the log on every run, so a
capture is self-documenting and a silent no-op can no longer be mistaken for an authored look:

```
Thruster material 0 drives colour 'Tint' and strength 'Emission'.
Thruster material 3 drives colour 'None' and strength 'Emissive Gain'.
Thruster material 4 drives colour 'Base Color' and strength 'None'.
```

**A third finding, and the reason index 12 rendered nothing.** `M_ElectricalFieldCandidateV3` splits behaviour on a
packed UV role channel: `ContentSource/FieldCandidates/V3/ElectricalField.hlsl` reads
`float role = floor(UV.x * 0.25 + 0.00001)` and takes a dim grey-blue extent-shell branch when `role < 0.5`. A stock
`/Engine/BasicShapes/Cone` has U in [0,1], so role is always zero and the shell branch always wins. The material is
not broken; it simply cannot be auditioned on a stock primitive. Index 12 is now
`/Game/NiagaraExamples/Materials/MI_RocketFlareCore`, which is a rocket flare core by authorship rather than by
hopeful repurposing.

**Honest outcomes that are not defects.** `M_Mesh_Add`, `M_Energy`, `M_Simple_Beam_Aura` and `M_Deadly_Beam` bind
nothing at all, because they take their colour from Niagara particle data rather than from a material parameter, and
a static mesh supplies none. They keep their authored look. `M_Master` (index 16) declares no emission-style
parameter of any kind and cannot be made to glow through this plumbing. These are reported rather than hidden.

**Candidates the survey found that are not yet auditioned**, all verified to exist on disk: `MI_Boundary_TechGrid`,
`M_Sphere` and `MI_Shield` (translucent unlit with panner and fresnel), the project's own `M_WormholeMouth_*` which
already carries a `CombatTint` parameter, the six Vefects galaxy instances with animated star panning, and **the ten
`SpaceNebulaFantasy` nebula instances, which are ten ready-made colour families** and are the most direct answer to
the owner's request to mix colours rather than only materials.



#### September 16 layered drive mock-up, specified by the owner

Having picked materials off the audition sheet, the owner specified a stack rather than a single core: remove the
long ribbon from the wing nozzles and put one much smaller plume on the centreline of the rear booster, then on each
side nest five shells, sized relative to the current core so ninety per cent means ten per cent smaller.

| Shell | Material | Size | Note |
| --- | --- | --- | --- |
| 1 | `M_DeepSpaceExhaust` (01M) | 90% | |
| 2 | `M_FresnelGlow` (04M) | 100% | the reference size |
| 3 | `M_Deadly_Beam` (08M) | 110% | raised from 95% on owner review |
| 4 | `M_BrightCore` (03M) | 105% | raised from 93%; rolled 90 degrees about the exhaust axis, still firing aft |
| 5 | `M_Fire_Rays` (09M) | 130% | raised from 110% |

**The centre plume was then removed entirely on owner review**, after a pass that halved it and moved it onto the
large lit ring in the middle of the hull face. `ss.ThrusterTrailScale` now defaults to zero, and zero means the
ribbon is not shown at all rather than shown very small. `ss.ThrusterTrailHeight` survives at -20 for whenever it
comes back; the sweep that chose it put the small spine panel at zero, the ring at -20 and the hull's lower lip
near -50.

**The shells sit 12 cm higher than the nozzle the ship reports.** The owner marked up a capture showing the stack
riding low against the nacelle rather than centred on it. `ss.ThrusterHeight` defaults to 12, chosen by sweeping 0,
12, 22 and 32: zero is the low placement they marked, and past twenty the plume climbs above the housing instead.
The nozzle position itself is left alone, since `USSShipPresentation::TryGetExhaustLocalPosition` is shared with the
flight automation tests and with the ribbon.

Built behind `ss.ThrusterLayered`, default off, so the shipped game is unchanged until the owner accepts it. Ribbon
size is `ss.ThrusterTrailScale`. Both are exposed on `Scripts/CaptureSpaceLook.ps1`. Every engine always constructs
its full stack, because components cannot be created outside the constructor; off the mock-up the shells after the
first are simply hidden.

**The roll is not decorative.** A cone is rotationally symmetric, so rolling it about its own axis changes nothing
geometrically. What it changes is the material's mapping, which is the whole point: it stops two shells that share a
texture orientation from reading as one surface.

**A bug of my own, caught by looking at the capture rather than trusting the code.** The ribbon was to move to the
midpoint of the two nozzles, but the midpoint was being computed inside the loop that reads the nozzles, so on the
first iteration the second nozzle had not been read yet, the guard failed, and the relocation silently never
happened. The first capture still showed the long beam on the left wing. Nozzle positions are now gathered in a pass
of their own before the ribbon loop runs. **This is the third instance today of the same failure mode**, after the
discarded cone rotation and the silently unmatched material parameters: a write that quietly does nothing and leaves
a screenshot that looks plausible enough to accept. Reading the capture, not the diff, is what caught all three.

**Per-shell parameter binding is logged**, so a capture says exactly what each shell received:

```
Thruster shell 0 (M_DeepSpaceExhaust) drives colour 'ExhaustColor' and strength 'None'.
Thruster shell 1 (M_FresnelGlow)      drives colour 'Base Color'   and strength 'None'.
Thruster shell 2 (M_Deadly_Beam)      drives colour 'None'         and strength 'None'.
Thruster shell 3 (M_BrightCore)       drives colour 'None'         and strength 'Emissive Gain'.
Thruster shell 4 (M_Fire_Rays)        drives colour 'None'         and strength 'None'.
```

Three of the five shells take no drive colour at all, because they colour from Niagara particle data that a static
mesh does not supply. They hold their authored colours, which is why the stack reads as teal, white and orange at
once rather than as five copies of the drive colour. That is a happy accident rather than a design, and it is worth
saying so: if the owner wants the stack to follow boost, brake and damage state, those three shells need material
instances with real colour parameters, which is authoring work, not a code change.



#### September 16 thrust-reactive inventory, asked for by the owner

The owner asked what effects exist to react to thrust. Surveyed in code and in owned content, then adversarially
verified; the verification refuted several claims, including one this log had already published, and the corrections
are folded in below rather than appended.

**Reacts to thrust today.** Drive state is `ASSShip::GetDrivePresentation`, which has **exactly one caller**,
`SSAmbientPresentation.cpp`. In flight, `DrivePresentationPower = clamp(.42 + .28*max(0,Throttle) +
.3*(|Velocity|/2400), .25, 1.35)`.

| Effect | Where | Behaviour |
| --- | --- | --- |
| Camera field of view | `SSShip.cpp:281` | 80 to 86 degrees on boost, `FInterpTo` speed 3 |
| Camera boom length | `SSShip.cpp:278` | 900 to 1010 cm on boost, same interp speed, so the two read as one gesture |
| Engine audio pitch | `SSShip.cpp:96` | `.9 + .15*Throttle`, flat 1.3 on boost |
| Drive colour | `SSAmbientPresentation.cpp` | idle deep blue, boost cyan-blue, brake orange, damage red pulse |
| Core size | same | length `clamp(18 + VisualPower*42, 14, 95)` cm, width `clamp(7 + VisualPower*4, 6, 18)` |
| Core emissive | same | `(.45 + VisualPower*1.15) * ss.ThrusterEmission / 3` |
| Engine light | same | intensity `35 + VisualPower*180` lm, radius `170 + VisualPower*90` cm |
| Ribbon scale | same | `clamp(.65 + VisualPower*.55, .55, 1.8)`, the only drive input the ribbons take |

**The structural finding: boost and brake are flat steps, not ramps.** `VisualPower = (Boosting ? 1.75 : Braking ?
.55 : DrivePower) * Pulse`. While boosting, the actual throttle and speed are discarded entirely. Every effect above
therefore jumps to a fixed value and sits there. That is the mechanical reason boost reads as a state change rather
than as acceleration, and it is one expression, not an architecture.

**Nothing is transient.** Every reactive effect in the table is a sustained level. Nothing punches on engagement and
nothing decays. `Pulse = .85 + .15*sin(t*9)` is the only time-varying term and it runs constantly, even at idle.

**Reacts to speed but never sees thrust.** The dust field: 320 instanced cubes in a 4800 cm box, each rotated to
`Velocity.ToOrientationQuat()` and stretched along travel by `1 + SpeedFraction*3` where `SpeedFraction =
clamp(|Velocity|/4200, 0, 1.5)`, so up to 5.5x elongation. It is handed velocity alone; the drive state never
reaches it.

**Exists but fires only on damage.** The hand-rolled camera shake, `SSShip.cpp:282`, gated on
`settings.cameraShake && run.damageFeedback > 0`. `damageFeedback` is run state, hard-set to `0.5` by
`Session::ApplyDamage` and decayed per step, not a settings value. Peak deflection against the 900 cm boom is
0.796 degrees at the heaviest hit and 0.20 at the lightest. **The in-code comment claiming 0.40 for the lightest hit
is wrong by a factor of two**; the heaviest figure is correct.

**Correction to an earlier statement in this session: the flight map DOES have a post-process volume.**
`Scripts/AuthorContent.py:478-488` spawns an unbound volume labelled `ReadableSpaceExposure` into the Survival map
and authors it: auto-exposure clamped to 1.0/1.0 in both directions, bloom intensity 0.35. It was reported here as
absent. It is not, and the difference matters for cost: adding chromatic aberration, vignette or a radial effect is
editing an existing authored volume, not placing a new one. Its pinned exposure is also why brightening the thruster
actually reads as brighter, since nothing auto-compensates.

**Genuinely absent**, each checked for by name across `Source/` and `Config/`: chromatic aberration, vignette, scene
fringe, film grain, radial blur, depth of field, tonemapper override, lens flare, heat haze or refraction, speed
lines, time dilation, any HUD speed readout, and **force feedback or controller rumble of any kind**.

**Owned and unused: three camera shake assets.** `Content/NiagaraExamples/FX_Explosions/CameraShake/CS_Explosion_01`,
and `Content/Vefects/Stylized_Galaxy_Shader/Demo/Shared/Cam/Cam_Shake` and `Cam_Shake_Slight`. `CS_Explosion_01` is
referenced by its own pack's explosion emitters, so it is not wholly unreferenced, but nothing in this game uses any
of them. The project has an `ASSPlayerController` subclass already, so a real `UCameraShakeBase` path has somewhere
to live.

**Cheapest first, for whenever this is picked up.** A thrust term on the shake that already exists: it runs every
tick, already honours an accessibility toggle, and would give boost a physical kick. Then the dust, which already
knows speed and could take drive state for a denser, longer streak under thrust. Then making boost ramp instead of
step. Post-process effects are now known to be cheaper than assumed because the volume exists.



#### September 16 thrust feedback, first pass

Four changes, taken in the order the inventory ranked them. All are in `SSShip.cpp` and `SSAmbientPresentation.cpp`;
nothing touches the settings UI, which is being reworked in parallel.

**1. Boost now has a transient.** `BoostPunch` is set to one on the frame boost engages and decays over about a
third of a second. Squared so it eases out. It moves the camera 16 cm back along the boom and adds a 9 cm shake
that fades, on top of a 2.2 cm rumble held for as long as boost is. The rumble runs at 34 and 27 hertz against the
damage shake's 70 and 53, so a hit taken while boosting still reads as a separate, sharper event rather than
merging into the rumble. Both sit inside the existing `settings.cameraShake` gate, so the accessibility toggle that
already exists covers the new motion too, which is why this was the cheapest of the four.

**2. The dust field is finally handed the drive state.** It had been given velocity alone, so accelerating changed
nothing about the field the player flies through. Thrust now stretches grains a further 2.4x on top of the existing
speed stretch, and pulls the near-culling limit in from 200 to 130 cm so grains that were held clear of the ship at
cruise come past the camera under power. Density near the eye is what actually reads as speed.

**3. Boost ramps instead of stepping.** `VisualPower = (Boosting ? 1.75 : Braking ? .55 : DrivePower) * Pulse`
discarded throttle and speed outright while boosting, so every drive effect jumped to a fixed value and sat there.
It now interpolates toward `Boosting ? 1.35 + .4*DrivePower : Braking ? .55 : DrivePower` at speed 7, which keeps
the throttle in the signal and gives the transition a shape. Boost still dominates; it just arrives.

**4. Speed post-process, on the player camera rather than the level volume.** Chromatic fringe rises to 1.6 and the
vignette from the engine default of .4 to .75, both following the boost punch and the held boost rather than the
damage clock. Put on `UCameraComponent::PostProcessSettings` so it follows the player and cannot disturb the
authored `ReadableSpaceExposure` volume. Behind `ss.SpeedPostFX`.

**The accessibility gap, stated plainly.** Chromatic aberration and vignette both have real accessibility
implications and belong behind a player-facing toggle next to the existing subtitles, camera shake and motion blur
switches. They are behind a console variable instead, which is not good enough as a shipping answer. The settings UI
is being reworked in parallel, so adding a menu entry now would collide; **this must be revisited once that work
lands.** The camera shake additions do not have this gap, because they reuse the toggle that already exists.

**Evidence and its limits.** 51 automation tests pass. A dense 89 frame sequence was captured and assembled into a
clip, and chromatic fringing is plainly visible on high-contrast rock edges in the thrusting frames and absent in
the cruising ones, which confirms the post-process path works end to end. **A still frame cannot demonstrate a .36
second transient**, and there is no matched before-clip, because producing one would mean rebuilding at the previous
commit. The punch, the rumble and the dust response are asserted from the code and from the clip, not from a
controlled comparison.



#### September 16 asteroid field continuity: the shell recycled far rocks to the near edge

The owner reported that the field looks right ahead but empties the moment they turn, that rocks then appear very
close, and that in a comparable game the field is simply there in every direction. **Root cause found and fixed, in
`ASSDistantAsteroids`, and it is four lines.**

Each depth band is a spherical shell around the player with a parallax offset, and an instance that leaves the shell
is recycled to the antipode. The rule as written sent an instance that drifted past the **outer** edge back in at the
**inner** one:

```cpp
if (Distance < Band.MinimumDistance)        Center = -normal * Band.MaximumDistance;   // near -> far, fine
else if (Distance > Band.MaximumDistance)   Center = -normal * Band.MinimumDistance;   // far -> NEAR, the defect
```

Sustained travel pushes every instance toward the back of its shell, so in forward flight the dominant case is the
second one. Each rock that fell out of the back returned at the **near** edge in front, where `ShellFade` scales an
instance to zero within 3500 units of either boundary. So the forward field filled up with invisible rocks stacked
at the inner radius, which then became visible only as they drifted outward: **that is the "spawn so close"**. And
because instances only ever left the back and returned to the front, the rear hemisphere drained: **that is the
"field is empty when I turn"**. One rule, both symptoms.

**Measured rather than argued.** The recycling rule was reimplemented in a standalone simulation and run over
cruise at 2400 cm/s, counting instances ahead and behind and weighting them by `ShellFade`, i.e. by whether they
could actually be seen:

| | ahead | behind | **visible ahead** | visible behind | at the near edge |
| --- | --- | --- | --- | --- | --- |
| Shipped rule, band 0, after 35 s | 704 | 796 | **0** | 112 | 704 of 704 |
| Shipped rule, band 1, after 35 s | 649 | 851 | **0** | 87 | 649 of 649 |
| Fixed rule, band 0, after 35 s | 777 | 723 | **653** | 590 | 161 |
| Fixed rule, band 1, after 35 s | 719 | 781 | **589** | 638 | 145 |

Zero visible instances ahead, in two of four bands, after thirty-five seconds of ordinary cruising. Band 3 survives
because its parallax is .12 and it drains twelve times slower.

**The fix is to re-enter through the edge the instance left through**, so a rock that recedes past the outer
boundary comes back at the outer boundary on the opposite side and approaches from a distance, fading in where
nobody can see it happen.

**Confirmed in game, not only in the model.** Two captures of the same scripted run, identical seed and camera, at
frame ~2,800: the old build shows a handful of scattered fragments, the new one a full field of near and mid bodies
in every part of the frame.

**What this does NOT address.** The hittable hazards are a separate system admitted by the survival Director, and
whether *they* are forward-biased is not answered here. The owner has previously reported too few hittable rocks,
which is its own open row. This fix is set dressing density and continuity only.

**The owner's design question stands unanswered on purpose.** They asked how other games give "the only way out is
through" without feeling scripted, and then said the free-will side can be tabled, that they would accept drifting
in a field beyond sight and being able to slow, and that if continuity cannot be fixed the player must be
restricted. Continuity *was* the defect, so the restriction may no longer be necessary; that judgement is theirs
and should be made after they fly the fixed build rather than before.



#### September 16 field continuity, second pass: two more causes, one of them mine

An eight-agent diagnosis with adversarial verification was run over the same symptom after the recycle fix landed.
It found two further causes. The verifiers also refuted a good deal of what the diagnosing agents claimed, including
one agent that diagnosed code the fix had already replaced, so what follows is only what was checked by hand
against the tree.

**Cause two, and it is a regression I introduced earlier today.** `ASSSpaceScenery` takes its clutter budget as
whatever is left of a shared 3072 instance cap: `Clamp(AreaClutterBudget, 0, 3072 - ss.DistantAsteroidCount)`.
Commit `9dcd144` raised that cvar's default from 2048 to **3072**, which is the cap exactly, so the remainder is
zero and **every cell has been building zero clutter ever since**. `AreaClutterBudget` is authored at 1024 and none
of it was reaching the world. The irony is direct: that commit was called "Raise field density" and it silently
switched off the only near-field system that is world-stable and direction-independent, which is precisely the
content a player sees when they turn around.

The count is back to 2048, which leaves the authored 1024. The density that raising it was meant to buy came from
the recycle fix instead, which made instances that already existed visible rather than adding more. The remainder is
now computed explicitly and **logs a warning when an authored budget resolves to nothing**, so this cannot recur
silently. `SSSpaceSceneryAutomationTests` deliberately drives the starved case, so that test now declares the
warning as expected rather than failing on it.

**Cause three: hazards were retired by where the player was looking.** `ASSWorldBody::Tick` ended with

```cpp
if (FVector::DotProduct(GetActorLocation() - Ship->GetActorLocation(), Ship->GetActorForwardVector()) < -16000.f)
    Destroy();
```

a live dot product against the ship's **current** forward vector, reached by every subclass: enemies, encounter
beacons and pickups included. Turning retired everything that had been more than 16,000 ahead, in the frame the turn
completed. **The magnitude claimed by the diagnosing agent was overstated and the verifier was right to refute it**:
a body 10,000 ahead scores -10,000 after a 180 degree turn and survives; only bodies beyond the threshold are lost.
It is a partial cull, not an annihilation. It is still wrong, because it contradicts the owner's stated model in
which the danger around the player is one intensity rather than one direction. Retirement is now radial at 22,000,
which is further than the old threshold, so nothing disappears sooner than it used to in any direction.

**Still open, and a design question rather than a defect.** Admission is placed only along the ship's current
forward vector, `Forward * (Lead + rand(0,5500)) + Right * rand(-2600,2600) + Up * rand(-1700,1700)`, a narrow
window ahead. Keeping hazards once admitted is a fix; deciding whether they should also be *admitted* to the sides
and behind is the owner's call, not an obvious bug.

51 tests pass. Captures of the same scripted run at the turn frame show the three stages in order.



#### September 16 making the field hittable: the plumbing is trivial, the blocker is the meshes

The owner's direction: "all asteroids of a certain size should be hittable... the existing ones aren't safe havens
to steer into. the dust and small rocks should bounce off of you, but anything mid size or higher should hurt", with
the Director reduced to governing how many are thrown at the player, at what speed, and how closely aligned to the
flight path.

**The size threshold the owner asked for turns out to be moot, and that is the interesting part.** Measured against
the authored data: scenery clutter radii run **850 to 14,000**, landmark structures **13,500 to 19,000**, and the
largest hazard the Director can admit is `MassiveAsteroid` at **650**. Every single piece of set dressing in the game
is larger than the largest thing the player is currently allowed to hit. By the owner's own rule there is nothing to
threshold: all of it qualifies, and the grain-sized dust field in `ASSAmbientPresentation` is the only tier that
should stay passable.

**The impact path already exists in full.** `ASSShip` roots on a query-only sphere that already blocks
`ECC_WorldStatic`, already moves swept with `AddActorWorldOffset(..., true, &Hit)`, and on a blocking hit already
calls `ReceiveDamage(15 * DamageScale)` behind a .8 second cooldown and deflects with
`VectorPlaneProject(Velocity, Hit.Normal) * .65`. Nothing had to be built. The scenery was simply
`SetCollisionEnabled(NoCollision)`, plus `SetActorEnableCollision(false)` at the actor level, which would have
silently neutered any per-component setup on its own.

**The blocker, found by writing a test that sweeps rather than one that checks settings.** With collision enabled
the settings assertions all passed and **the sweep still reported no hit**. Reading the packages directly:
`Content/Asteroid_Library/Static_Meshes` and `Content/Megastructure_Scifi_World/Meshes` are **uniformly authored
`CTF_UseComplexAsSimple`** — every one of them, in both packs. That flag means the mesh carries no simple collision
primitives and falls back to its render triangles, and **an instanced static mesh component cannot use complex
collision at all**. So the clutter, which is the dense near-field content and the whole point of the exercise, is
unhittable no matter what the component says.

**What unlocks it is a content pass, not code.** Derivative copies of the meshes actually used by the scenery need
real simple collision generated, convex decomposition or an n-DOP hull per rock, and the look data repointed at
them. Derivative copies rather than edits in place, because the project's standing convention for purchased content
is to duplicate into the private licensed folder rather than modify a vendor asset, as `AuthorDeepSpaceExhaust.py`
does. Landmarks are single `UStaticMeshComponent`s rather than instances, so they may work from complex collision
alone and should be re-tested separately once the clutter path is real.

**State of the change.** The collision plumbing is in and correct, behind `ss.SceneryCollision`, **defaulted off**,
because switching it on today makes the field query-only against nothing and would look like the work was done. The
actor-level flag follows the same switch. 51 tests pass with the switch off.

**Not started: the Director's side of the owner's direction** — governing count, speed, and alignment to the flight
path rather than being the only source of hittable content. That depends on the content pass landing first.



#### September 16 the field is solid: content pass landed

The blocker recorded above is cleared. `Scripts/AuthorSolidScenery.py` builds collision-bearing derivatives of
every mesh the scenery places, 45 of them, into `/Game/SpaceSurvival/Licensed/SolidScenery`. Vendor assets are not
modified in place, per the project's standing convention for purchased content.

**The diagnosis above was half wrong, and the correction matters.** It said the vendor meshes carry no simple
collision. Probing one directly showed the opposite: a fresh copy of `SM_Asteroid_Barren_1` already has **one convex
element**. `CTF_UseComplexAsSimple` was simply telling the engine to ignore it. For twenty-four of the forty-five
meshes the entire fix is a flag flip.

**Why the wrong conclusion was reached, which is worth knowing before anyone repeats it.**
`StaticMeshEditorSubsystem.get_simple_collision_count` **does not count convex elements** — only boxes, spheres and
capsules. Used as a success check it reports zero on a mesh that is fully collidable, which is exactly what it did
here, twice: first making the meshes look empty, then making a successful convex decomposition look like a failure.
The script now counts the aggregate geometry itself, and the docstring says so.

**Twenty-one meshes genuinely had nothing**, all of them from the architectural kit. `set_convex_decomposition_collisions`
returns True on those while producing no primitives, so the generator is judged by what it leaves behind rather than
by what it returns, and falls through convex to an 18-DOP hull to a box until something actually lands. Final split:
7 by convex decomposition, 14 by 18-DOP.

**Both authoring paths were repointed**, not only the obvious one. `AuthorSpaceAreas.py` resolves every mesh through
the derivative folder, and `AuthorOrbitalWreck.py` does the same for the legacy `StructureComposition`, its wreck
pieces and the station exterior. Missing the second one left the sweep test failing while everything else passed,
which is how it was caught.

**`ss.SceneryCollision` is on.** The test that matters sweeps the ship's own 105 cm sphere through a real structure
and requires a blocking hit; it fails if the meshes ever regress. 51 tests pass.

**What the player gets.** Every rock and every megastructure is now solid and blocks weapon and sight traces, so
shots stop at cover and soft aim cannot lock through a rock. The existing impact path applies unchanged: 15 damage
behind a .8 second cooldown, and the velocity deflected along the surface. The dust field stays passable, which is
the owner's "dust and small rocks should bounce off you" tier.

**Still open, and now unblocked:** the Director's side of the direction, governing how many bodies it throws, at what
speed, and how closely aligned to the flight path, rather than being the only source of hittable content.



#### September 16 the Director's three dials

The owner's direction: the Director governs "how many he hurls at you, higher speed, more in line with your flight
path". Each is now a dial, because this is a feel change and feel is dialled rather than argued.

**Speed was the real problem and it is arithmetic, not opinion.** Authored drift is 40 to 350 cm/s against a
2400 cm/s cruise, so a hazard supplied between 2 and 13 per cent of the closing speed. The player was not being hit
by anything; the player was driving into stationary rocks. `ss.HazardSpeed` defaults to 3, taking drift to 120-1050
and the hazard's share of closing speed to 5-30 per cent.

**Reaction distance had to move with it.** `FindSafeSpawn` computes the spawn lead from closing speed times
`MinimumReactionSeconds`, using the largest authored drift. Multiplying drift without multiplying that term would
have spawned faster hazards at the old distance, arriving inside the reaction budget. That is unfair rather than
hard, and it is the kind of change that reads as a difficulty increase while actually being a bug. The multiplier is
applied in both places from one shared function so they cannot drift apart.

**Alignment.** Velocity was `-Ship->GetActorForwardVector()`, the heading the ship happened to hold at the instant
of spawn, so any turn afterwards sent the hazard sailing past. That is what made hazards read as scenery going by.
They now lead the ship's predicted position, blended against the old behaviour by `ss.HazardAim`, default .55.
Partial on purpose: a field in which everything intercepts is not harder, it is unavoidable, and the owner asked for
danger rather than for a tax.

**Count.** `MaximumActiveThreats` was a fixed 24 checked in two places. Both now read `ss.HazardCount`, default 40.

All three are console variables so the owner can dial them in a session rather than wait on a build. 51 tests pass.

**Unverified by play.** These are the right levers and the arithmetic is checked, but whether 3x, .55 and 40 are the
right values is a judgement that needs someone flying it. They are starting points chosen to be too much rather than
too little, per the owner's own standing preference that harder and dialling down is proof of concept where easy and
dialling up is weak.

#### September 17 the speed dial was deleting what it admitted

Found by the packaged Wave 10 fixture while preparing `0.1.18-alpha`, not by play. It failed with
`compoundActorPresenceSeconds=0`: through a full 40-second Wave 10 climax, gravity, asteroids and enemies never
coexisted, and the peak threat count was 15 where Package 13 had recorded 23.

**Cause, also arithmetic.** The two September 16 changes each held on their own and broke each other. Retirement became
a fixed 22,000 from the ship. The speed dial multiplied the drift term inside the spawn lead, so at a 2,400 cruise the
lead is 13,125 plus the body's radius plus 350, and candidates land up to 5,500 beyond that. For the 4,300 climax
gravity field that is 17,775-23,275 ahead before any lateral offset. A body admitted past 22,000 was spawned, charged
to the budget, counted as the compound front's required gravity well, and destroyed on its first tick. The compound
flags are set once and never retried, so the front silently never formed. Boosting widens the overlap to ordinary
asteroids and enemies: the faster the player flew, the more of the field was deleted at birth, which is the opposite of
the direction the dials were built for.

**Fix.** One rule, held by the body rather than by whoever places it: a body is never retired for being where it was
placed. The first tick that sees a ship raises that body's `RetireDistance` to at least its distance plus 4,000, so
hazards, enemies, wreckage passages, salvage caches and their debris, distress attackers and offered signals are all
covered, and so is any placer written later. The default stays 22,000.

An independent review of the first version of this fix, which had patched only the Director's three spawn calls, found
the rest, and each is corrected here:

- **Encounters had the same defect on their own lead formula.** Accepting the Wave 2 salvage signal during any boost put
  the third cache at 22,740; it was deleted unseen, the objective could only reach two of three, and the signal was
  lost after 26 seconds with nothing to tell the player why. Distress attackers crossed the radius from engine tier 2.
  The accepted signal itself now also outlives its course, since the objectives report to it.
- **A field could outrun the ship.** Fields carry a share of the ship's velocity at admission: .65 in a climax, and
  boost is 1.85 of cruise, so a field admitted during a boost travelled at 1.2 of cruise and could never be reached once
  the boost ran out. The carried velocity is now a share of at most cruise speed.
- **The required gravity well was asked for once.** Fields are not drawn at random during a climax, so a turn of a few
  seconds that carried the ship out of reach ended the compound front for the rest of the climax. The Director now
  tracks that body and asks again if it is lost.
- **Storms admitted past 22,000 had no beam.** The Nerves beam is requested once and the presentation refuses requests
  beyond the same 22,000. Such storms used to be deleted anyway; now that they live, the body asks again until granted.

`SpaceSurvival.Integration.AdmittedBodiesOutliveAdmission` places the three required Wave 10 bodies, a wreckage
passage, a salvage course and a distress pair beyond the default radius, requires each to survive its next tick, then
destroys the gravity field and requires a replacement. With the rule and the re-arm disabled it fails 37 expectations
across every one of those paths; with them it passes.

**Measured after.** Editor Wave 10 fixture `10e0bfc0df774d65839265d1999e057d`: compound presence 40.0 of 40.0 seconds
(0 before, 23.7 on Package 10), peak threats 24 (15 before), and the Compound frame shows the gravity well, the asteroid
front and three hostiles together. 54 of 54 Unreal tests pass through `Scripts/Build.ps1 -Target Test`; the alien
gallery lifecycle test now declares the three rejection warnings it provokes on purpose, which had been marking the
run as passed-with-warnings. Not tested by play: boost-then-release and turn-around were reasoned from the code and
checked by the review, not flown.

**What this changes for the owner's judgement of the dials.** Every impression of 3x, .55 and 40 formed before this fix
was formed with part of the field missing, more so at speed. The field is now as dense as the dials asked for. Note
also that the admission tick still stops at `MaximumActiveThreats` (24); only the per-spawn checks read
`ss.HazardCount`, so 40 is not reachable yet. That is left alone until someone has flown the corrected field.



#### September 18 the Stellar Phoenix, measured rather than read off the store page

The owner bought the Stellar Phoenix Shuttle and made it the new main ship. Before anything is built on it,
here is what it actually is. Every number came from loading the asset in 5.8 under
`.agent/local/StellarPhoenix/`, where the probe scripts live and are re-runnable.

**It imports clean.** Built for UE 5.3, loads into 5.8 with zero failures: 165 bones, 3 material slots
(`Spaceship_1`, `Spaceship_2`, `Spaceship_Glass`) all resolving, 13 textures all present, no integrity
issues. It lives at `Content/Stellar_Phoenix/`, git-ignored as licensed Fab content, because every
reference inside the pack is by the package path `/Game/Stellar_Phoenix` and moving it under `Fab/` would
break all of them. Only the 71 MB `Spaceship/`, `Data/` and `FirstPerson/Input/` subset was taken; the
94 MB demo map and 33 MB of Epic first-person arms were left out.

**Size, and the owner's worry about it.** `1243.9 x 2484.0 x 704.8 cm` - 12.4 m wide, **24.8 m long**,
7.0 m tall, standing on Z = 0. Its authored forward is **+Y, not +X**, so it needs a -90 degree yaw when
mounted, exactly as the squirrel hero did. The hull it replaces, `SM_SwiftCandidateV1`, is 4.82 m, so the
Phoenix is **5.2x longer** than the ship the whole game is calibrated around. The owner raised this
himself: "the ship is larger than the old one, so scale or something has to adjust to accommodate the
gameplay element being the same." That decision is open and is the first thing to settle.

**The animations are not what their names suggest.** Measured by asking all 165 bones how far each travels
between a clip's first and last frame:

| Clip | Length | Bones moved | What it actually does |
|---|---|---|---|
| `Landing_On` | 2.067 s | 31 | Gear down **and rear ramp open** |
| `Landing_Off` | 1.567 s | 36 | Gear up **and rear ramp shut** |
| `BattleMode_Enter` | 2.6 s | 8 | 4 airbrake flaps at 4.4 deg, 4 fairings at ~3 cm |
| `BattleMode_Exit` | 2.3 s | 10 | Engines rotate 8.7 deg, fairings return |
| `AirBrake` | 1.633 s | 3 | 3 airbrake flaps at 4.5 deg |

The landing clips are the good news and are exactly the launch behaviour the owner described:
`Cargo_Door_Bone` swings **83.7 degrees** in both, alongside `Foot_Bone` at 90.3 and the
`Chasis_Back_Left/Right_2/4/7/8_Bone` set with `Leg_B_Bone` and `Leg_D_Bone`. Gear and ramp are one
motion, already authored, free.

**`BattleMode` is not the wings.** All 16 `Wing_Up/Down_A/B_Left/Right` bones are unanimated in every clip
the pack ships. The owner's "wings fold out when the pilot sits down" has nothing behind it yet. They can
be authored - the bones sit at component origin, so they are rotation-only controls and a deploy clip is
the same operation as `Scripts/AuthorHeroTailSway.py` - but what the deployed pose should look like is the
owner's eye, not an engineering question. Author a candidate and have it approved; do not ship a guess.

**Read the bones, not the names.** An earlier pass sampled `Cargo_Door` rather than `Cargo_Door_Bone` and
concluded the ramp was never animated, which was wrong. The gear bones are `Chasis_*` with one **s**,
while the `Chassis-_Door_A/B` bones with two are something else and barely move. The pack also spells
interior `Interiro` and has a Cyrillic C in `Сountermeasures`. Ask a bone how far it moves; never infer
from what it is called.

**Walking aboard is the big one.** The layout supports it - `Cockpit_Mesh` at Y +882.8 Z +451.8 at the
front, a rear ramp from `Cargo_Door` at Y -957.8 Z +195.4 down to `Cargo_Door_A` at Y -1130.2 Z +133.4,
`Interior_Mesh` and `Interiro_Doors_L/R_Mesh` between them. But **there is no walkable collision**:
per-poly is off, and a skeletal mesh's physics asset is per-bone primitives for simulation, not an
interior floor. "The hero walks into it, to the pilot chair" was one sentence and is the largest single
item in the whole request; it needs collision that does not exist yet, either per-poly on the mesh or
authored invisible floor geometry.

**The advertised damage is an impact flash.** `M_Hit` and `T_Hit_Impact` only - no damage bones, no
destruction meshes, no crush zones. `Data/Spaceship.uasset` is a `NiagaraEffectType` performance baseline,
not a damage config. The owner has deferred damage work regardless.

#### September 18 flight moves to Ship Core, and what the plugin does not tell you

**Owner direction, verbatim:** "use ship core 100% nothing i have today is good. at least i didn't test the
latest if its used at all.. but all flight mechanics use ship core." Also: the Stellar Phoenix shuttle is
the new main ship, landing gear is automatic on the docking button rather than a separate control, the hero
must be able to walk into the ship and sit in the pilot chair, and the station gets a landing zone OUTSIDE
it rather than the ship flying into the bay.

**Why this is a large change rather than a swap.** `ASSShip` is fully kinematic: a `USphereComponent` root
with `QueryOnly` collision, a hand-integrated `Velocity`, a fixed 1/120 loop and `AddActorWorldOffset` with
a sweep. Ship Core is force-based on a simulating rigid body - `UThrusterManagerComp` casts the owner's root
to a `UPrimitiveComponent`, reads `GetMass()` and calls `AddForce`. Nothing in this project has ever used
rigid-body physics; a grep for `SetSimulatePhysics`, `AddImpulse` and `OnComponentHit` across
`Source/SpaceSurvival` returns nothing. So about a third of `SSShip.cpp` is replaced, and it is the
load-bearing third.

**Step zero was invisible.** The plugin has been `"Enabled": true` in the uproject for some time, so it
compiled - but `SpaceSurvival.Build.cs` never listed it, meaning no game file could include its headers and
the module never linked against it. It was present and unreachable. That is why "is it used at all" had no
observable answer.

**The mass is a measurement, not a preference.** Ship Core divides thrust by mass to get acceleration. Its
default `MaxThrustPosX` is 15,000,000 and the game's base acceleration is 3200 cm/s^2
(`SurvivalCore.h:125`), so 15,000,000 / 3200 = **4687.5 kg** is the mass at which the plugin's stock force
set reproduces today's flight. Measured in the new test: **3173.3 cm/s^2**, 0.8% off. Nothing had to be
re-derived.

**Three silent traps, each of which cost a red test to find.** All three produce a ship that looks correctly
configured and does not move, which is the worst failure mode to debug behind a half-migrated flight model:

- **The plugin's components never activate themselves.** `UThrusterManagerComp` and `UGyroManagerComp` set
  `bCanEverTick` and a `TG_PostPhysics` group in their constructors but never set `bAutoActivate`, and
  neither `TickComponent` checks `IsActive()`. A component added from C++ sits inactive. This is invisible
  in the Blueprint workflow the plugin was written for, where the editor activates components for you.
- **A world with no GameMode never dispatches BeginPlay.** `UWorld::BeginPlay` goes through the authority
  GameMode's `StartPlay`. The plugin resolves its `ShipMesh` pointer in `BeginPlay` and its `TickComponent`
  returns immediately while that pointer is null. Active, ticking, configured, motionless.
- **Physics world teardown order is not local.** `EndPlay` then `DestroyWorld` then `DestroyWorldContext`;
  skipping `EndPlay` leaves the Chaos solver attached to a world being torn down and kills the editor
  **eighteen tests later**, inside an unrelated test's cleanup.

**What the plugin gets right, verified by reading it rather than trusting the name.** Its authority gating
works in standalone - the pawn is `ROLE_Authority`, so `if (!Owner->HasAuthority())` passes and the autopilot
ticks; the run confirms it with `THRUSTER BeginPlay Owner=Actor_0 Role=3 ShipMesh=OK SimPhys=1`. It has a
`PRECISE` mode documented as "assists with docking but allows manual input", and a
`ComputeSafeApproachSpeed_V2` that accounts for reaction time, thruster ramp and alignment time - which is a
purpose-built answer to the owner's report of not being able to slow down before hitting the station.

**Two real defects in the vendor code, to patch or route around rather than discover at runtime.**
`UThrusterManagerComp::SetInertialDampeners` dereferences `ShipMesh` with no null check, while its `_Server`
twin guards it - and `ShipMesh` is set to null on the self-disable path, so the crash lands on exactly the
path a Brake input would call. And `UAutopilotManagerComp` fires an `AddOnScreenDebugMessage` **every tick**
while following a spline, ungated by any debug flag, which would paint every capture PNG.

**State when that was written:** stage 1 only, `ASSShip` untouched, the new test running against a bare
`AActor` rather than the game's ship so that a failure accuses the plugin and not the game. 62 of 62
automation tests passing with zero warnings. That is no longer where this stands - see the next entry.

#### September 18 the Phoenix's stick was wired to the wrong gyro axes, and how that was found

The Phoenix had stopped docking - approach ran the full 126-second timeout with `sawDocking=false` - after
the measured pivot commit shrank the admission radius from 2442 cm to 2301 cm. The first theory was the
fixture's proportional steering oscillating on a body with inertia; rate damping was added and the ship
went from weaving across a 30 km box to sitting dead still at 5.8 cm/s. The CSV only carries the camera, so
the ship's state was being inferred. A once-per-second `SOAK_APPROACH` line was added to the fixture -
station-local position, distance versus radius, physics velocity, the simulating flag, heading error and
command, `CanAssistDocking`, and the blocking actor if the clearance sweep fails - and it read:

- `t=1..3`: the fixture commands nose-down (`pitchErr -8.8 -> -42.7`, `steer.Y` saturated) and the ship
  **climbs** from Z 289 to 2029.
- `t=116..125`: both commands saturated at -0.75 for a hundred seconds and **neither error closes** - yaw
  stuck at -175 degrees, pitch at -80. A saturated command whose error never moves is going to the wrong
  axis.
- It ended pinned 43 m above the pad, one collision radius outside the station's Disc box, thrusting into
  `SSStation_1/StaticMeshComponent_12` at 6 cm/s. That was the standstill.

**The cause.** ShipCore's `GyroManagerComp.h:47` documents its input as `(Pitch, Yaw, Roll)`. Its code
applies the vector as a body-frame torque - `ApplyFinalTorque` does `AddTorqueInRadians(
Xf.TransformVectorNoScale(FinalLocalTorque))`, and `CalculateFinalTorque` scales `.X` by `RollMultiplier`
"roll input shaping only" - so physically X is roll, Y is pitch, Z is yaw. `ASSShip::DriveShipCore` trusted
the comment, so the pitch stick rolled the Phoenix and the yaw stick pitched it. Nothing had ever exercised
it: the classic hull's kinematic path never touches the gyros and the Wave 10 captures steer with a zero
vector, so every gate stayed green.

**The old check was passing falsely.** `ShipCoreBodyContract` applied Y input for a full second at max
torque and asserted `|delta yaw| > 1 degree`. Y is pitch; a body pitched past ninety degrees reports a 180
degree Euler yaw flip. It passed on a rotation it never asked for.

**Measured, not reasoned.** `SpaceSurvival.Flight.ShipCoreGyroAxes` gives each axis a fresh level body
and a burst of full input that stops as soon as any angle passes fifteen degrees, then asserts which
rotator angle dominated, that the other two stayed under a third of it, and the sign:

| input | roll | pitch | yaw |
|---|---|---|---|
| +X | **-15.06** | 0.00 | 0.00 |
| +Y | 0.00 | **-15.32** | 0.00 |
| +Z | 0.00 | 0.00 | **+15.32** |

Zero leakage. The order is (Roll, Pitch, Yaw), and the signs are not uniform: yaw follows the torque's
sign, pitch and roll oppose it. The first sign hypothesis was +/+/+; the test refuted two of them by name,
and the measurement became the table. `DriveShipCore` now sends `(Lean, Pitch, Yaw)` with yaw `+Steer.X`,
pitch `-Steer.Y`, lean `-Steer.X * .35`, so the stick means the same thing on both hulls. The lean's sign
is a feel dial, flagged as such in the code.

**Verified:** 67 automation tests, zero warnings, zero failed, zero not-run - the axis test, a second pass of it
from a rotated start that reads the turn as a body-frame quaternion so a world-frame torque could not hide,
and `ShipStickToGyro`, which pins the game's stick-to-vector translation as a pure function so the whole chain
from stick to rotator sign is measured. The rendered Station5 capture
with `-SSPhoenix` is `success=True`, `sawDocking=True`, approach **4.22 s** (from a 126 s timeout, and
faster than the classic hull's 4.42), docking 3.01 s, onDeck 14.55 of 15.00, zero off-deck rescues. The
diagnostic lines on that run show yaw error -0.6 to -0.1 degrees, pitch error zero, commands near zero,
altitude level, distance closing 12,621 to 2,376 cm in four seconds.

**The lesson is the same one as the 105 cm radius, the `Cargo_Door` bone and the centred pivot: a name
is a claim, a measurement is a fact.** The header comment was wrong about order and silent about sign,
and the only test that could have caught it was itself written against the comment.

Kept: the fixture's rate-damped steering - right for a body with inertia even though it was not the bug -
and the `SOAK_APPROACH` diagnostics, because the next time the ship does something inexplicable the
question should be answered by reading, not inferring.

#### September 18 the landing pad is a thing, not three numbers on the station

The owner's requirement, verbatim: "a landing pad anywhere in the game, ever, future features anything,
all docks and launches the same exact way" and "make sure this is a prefab type concept or feature so if
we add landing pads anywhere else, they all work exactly the same."

Before this the pad was `PadCenterX`, `PadDeckTop` and `PadHalfExtent` as `static constexpr` on
`ASSStation`, plus a lambda that assembled cubes in station-local space. Exactly one pad could exist, at
one station, and the docking sequence had nowhere to be written against except that station.

**`ASSLandingPad` is now an actor.** Placeable on its own, at any transform, with no station behind it.
Its origin IS the landing spot - the centre of the deck's top surface - so `DeckPoint()` is the actor's
location and nothing is derived from a slab centre and a thickness. It answers every question a landing
needs in its own frame: `DockPoint(clearance)`, `WalkSpawn()`, `ExitPoint()`, `Covers(world)`, and it owns
the lit indicator. `ASSStation` spawns one at its placement constants, attaches it so it rides through
origin rebasing, and keeps `PadDockPosition()` / `PadWalkSpawn()` / `PadExit()` as thin delegates so every
existing caller still works. The walkway that joins the pad to the hangar mouth stays the station's,
because it is the station that has a mouth.

**The dock clearance is the ship's number, not the pad's.** `DockPoint(230.f)` is the classic hull's
clearance and the default. `OriginToBelly` for the Phoenix is 0.25 cm - it stands on its own pivot - so it
should park at deck + gear height, not deck + 230. That per-hull clearance is the next thing to move; until
it does the Phoenix still hangs 220 cm above the pad. Recorded, measured, not guessed.

**Two things had to stop being static.** `ASSStation::WalkableLocal(Local)` became `Walkable(World)` on
the instance, because the pad has its own transform and the only honest answer comes from asking it. It
keeps a geometric fallback for a station whose pad has not been built - a fixture that spawned it without
`BuildHub` - so the envelope never silently shrinks to the interior because an actor pointer is null. And
the soak fixture's "is the hero on the deck" check accepted only `GM->Hub` as the floor actor; on the pad
the floor is the pad, and a check that would have certified a correct landing as a failure was the exact
shape of the stale-envelope bug fixed two entries ago.

**Proof it works with nothing around it:** `SpaceSurvival.Station.LandingPadStandsAlone` spawns a pad at
(-38000, 21000, -6500) yawed 137 degrees with no station, builds it, and checks a solid deck under the dock
point, the walk spawn and the exit; that coverage follows the pad's rotation and not the world axes; that
building twice builds once; and that the indicator starts lit and goes out.

**Counts moved with the structure.** The station's solid-cube count is 17 rather than 18 - the deck belongs
to the pad now, which is the point.

**Verified:** Editor build clean; 65 automation tests succeeded, 0 warnings, 0 failed, 0 notRun, including the new standalone pad test. A rendered Station5 capture on the classic hull is success=True with sawDocking=True, approach 4.42 s, docking 3.00 s, onDeck 14.55 of 15.00 and zero off-deck rescues - the hero lands on the pad actor deck and is never rescued. The same capture with -SSPhoenix does NOT dock on this commit: telemetry shows the soak fixture P-only steering oscillating on the ShipCore body across a 30 km box with 45 km vertical swings. The refactor did not cause that - the dock point is unchanged and the classic control docks - and the fixture fix is the next entry.

#### September 18 Ship Core actually takes the controls

The owner pressed on the honest gap: "what are you using ship core for if not the controls?" The answer at
the time was the chase camera and nothing else. The plugin was linked, enabled, contract-tested and
attached to no ship. This entry is the swap itself.

`ASSShip`'s `USphereComponent` root now simulates, and `UThrusterManagerComp` plus `UGyroManagerComp` move
it. The hand-written substepped integrator is still in the file and still runs - **every build that does not
pass `-SSPhoenix` flies exactly as it always did.** The two paths never both run.

**The dials are not a straight translation, and one of them is a re-purposing.** Worth knowing before
tuning, because the upgrade screen still sells all four:

| Stat | Where it lands | Note |
|---|---|---|
| `acceleration` | thruster force, times mass | Same number on all six axes on purpose |
| `speed` | the speed limiter | Defaults **off**; without switching it on the upgrade is inert |
| `maneuver` | `MaxTotalTorque` | |
| `response` | `ProportionalGain` | Was a rate constant on **linear** velocity error; a rigid body has no such dial, so it is re-homed onto **angular** error |

The plugin ships Z thrust at 20e6 against 15e6 for X and Y. Left alone that makes vertical strafe a third
livelier than horizontal for no reason anybody chose, so all six axes are set to the same figure.

**Two things that would have broken quietly rather than loudly.** Both are the same shape - the old flight
model was the only writer of a value the rest of the game reads:

- **`GetVelocity` had to move to the physics body.** Sixteen production sites read it: Director spawn lead,
  enemy aim lead, hazard intercept, the collision-course warning, the dust field. Under Ship Core the
  hand-kept `Velocity` member is never written, so leaving it as the answer would have frozen all sixteen at
  the `BeginPlay` cruise seed. Nothing would have errored; the game would just have got easier.
- **Collision damage had to move to `OnComponentHit`.** The old integrator took its hits off the swept
  move's `FHitResult`, and a simulating body never runs that path - so ramming an asteroid in the Phoenix
  was free until this was bound. Same 15 damage on the same .8 s cooldown; physics handles the bounce.
  Bound and building, but **not yet proven at runtime**: the Wave 10 soak never collided, so nothing has
  actually hit anything under the new path.

**Inertial dampeners are on.** Release the stick and the ship settles rather than coasting forever, which is
the single biggest contributor to the feel being chased. `SetInertialDampeners` is called only once the body
is confirmed simulating, because of the vendor defect recorded above - it dereferences `ShipMesh` unguarded
while its own `_Server` twin checks, and standalone always takes the unguarded path.

**CCD is on** because a 24.84 m hull at boost crosses more than a station wall's thickness in one frame, and
this game had never had a swept rigid body before. Without it the ship tunnels.

**Verified:** 63 of 63 automation tests, zero warnings, zero failed, zero not-run. A rendered Wave 10
capture returns `success=True` with `SSHull: ShipCore driving, mass 4687.5 kg` in the log, peak speed
6748 cm/s under 24 active threats.

**Still open:** the feel itself. Making the parameters reachable is not the same as dialling them in, and
nobody has flown this with hands on a controller yet. Docking through `UAutopilotManagerComp`, the station
landing zone, the sit-to-launch sequence and the walkable interior are all still ahead.

#### September 17 the squirrel is the hero: seated, lit, animated, and audible

The owner's ask was "my ask is for hero to be squirrel and have its animations added". This is what that
took, in the order it happened, and what it cost.

**It is in the game.** `USSPhase1Data::Heroes` lists the squirrel first, so it is what
`ASSWalker`/`ASSShip` resolve; the trooper and the Acornaut stay behind it as the fallbacks. Its assets live
under `Content/SpaceSurvival/Licensed/Hero/`, which is git-ignored. The tracked tree carries only the paths
and the measurements.

**That path is wrong, and it is the owner's own art that is sitting in it.** The folder was chosen on the
assumption that the model came from a pack. It did not: the owner stated on September 17, "squirrel is
homemade, no license", and the evidence on disk agrees - the source GLB's header reads
`{"generator": "Tripo", "version": "2.0"}` and the model sits in the owner's own Tripo bridge output at the
ignored `Content/TripoModels/astronaut_squirrel_3d_model_Clone1_Clone1/`.

**How that error nearly hardened into fact.** A review of this question was asked to weigh the owner's
statement against the written record, and found two documents calling the model purchased: a comment in
`SSContentTypes.h` and a line in `.agent/local/HeroSquirrel/Stage1_Clean/ImportSource.py`. Neither was
independent corroboration. Both were written during the September 17 hero work by the same author who made
the original assumption - one guess, cited twice, and `git log -S` on the comment points straight back at
commit `0d47c4c`. Where provenance is concerned, check who wrote the record before weighing it against the
person who made the thing.

**What is genuinely licence-restricted, verified rather than assumed.** Read as raw bytes, each of the five
retargeted clips still embeds MoCap Online's own master path - for example
`W:/MoCap Packs/UE4/_FBX_MASTERS/Mobility_PRO_v27/PRO/IPC/MOB1_Jog_F_IPC.fbx` - with the source FBX's
timestamp and MD5 beside it. `A_SquirrelWalk` and `A_SquirrelPilot` carry no such strings. The split is
therefore 9 first-party packages, 70.7 MB, against 5 licence-derived clips, 1.95 MB. Only the idle, the two fidgets, the jog and the run are licence-restricted, and those
derive from the MoCap Online pack. So `SK_SquirrelHero`, its three textures, `SquirrelSuit`, `A_SquirrelWalk`
and `A_SquirrelPilot` are first-party work stored in an ignored directory named Licensed - which means they
are not in the repository and exist only on the owner's drive, with no history and no backup. Nothing shipped
depends on this, because the cooked packages carry the art either way, and moving them was deliberately not
done inside the 0.1.19 release because it would have invalidated the audited package.

**It is blocked on one question, and only one.** This repository is public, so tracking the art publishes it
permanently and irreversibly, and whether that is permitted depends on the owner's Tripo plan. The owner is
checking. Nothing moves until they answer: a wrong call here cannot be taken back out of git history.

**Seated.** It inherited the Acornaut's `PilotMountOffset` of `(-15, 0, 72)` and floated 44.067 cm over the
cushion - a third of its own height, which is the float the owner reported. That number was measured for a
body whose origin sits 62.9 cm above its boots; this body's origin *is* its boots. The replacement
`(-12.5, 0, 27.933)` is measured against the cockpit geometry in `Stage6_Clips/SeatFit.json`, not adjusted by
eye, and puts the hips on the cushion with the boots in the footwell.

**Lit.** The suit's base colour averages 0.046 linear albedo, about half of fresh asphalt, with 73% of its
texels under 0.05, and every lamp in the hangar hangs above head height. It was a silhouette on a bright
floor. It now carries a warm key and a cool rim of its own on lighting channel 1, scaled per hero
(`ReadabilityLightScale`: squirrel 2.5, trooper and Acornaut 0.5, because the same rig on a light suit would
blow it out). At 2.5 the suit reads at 0.75 of the deck beside it, up from 0.12. A first attempt at this was
rejected in review for measuring contrast against floor pixels rather than the character, and for a rig that
would have been ~3x too hot on the trooper. **Lighting channels do not contain a Lumen scene**: with
`r.DynamicGlobalIlluminationMethod=1` and `r.ReflectionMethod=1` the channel mask is respected by direct
lighting only, so the hero's own lamps were bouncing off the deck and glinting in the hull - it read as a
lantern, which the owner called out. `SetAffectGlobalIllumination(false)` and `SetAffectReflection(false)` on
both lights close that; the overhead lamps are untouched and still bounce.

**Facing.** The hero was being placed on the deck at world yaw 0 regardless of the heading it flew in on. The
old climb-out arc had been hiding it. Reverting the fix misses the station heading by exactly 73 degrees in
the test.

**It stands in a real idle.** Standing still had been one frozen frame of the walk. `MOB1_Stand_Relaxed_Idle_v2`
from the MoCap Online pack is retargeted onto the squirrel's own skeleton as `A_SquirrelIdle`, with two stand
fidgets that cut in every 12.266666 s - two whole idle loops, which is not a taste: the fidgets' first pose
matches the idle's first pose to 0.004 cm across all 46 bones, so a cut on a loop boundary costs nothing.
`ASSWalker` now chooses a clip rather than playing one: idle when standing, a gait chosen by speed, a
hysteresis band so a pawn creeping across a threshold cannot flicker, and a short blend off whatever pose it
was holding. A hero that declares no idle behaves exactly as it always did - walk frozen at the handoff
second - and the tests pin that.

**It has a jog and a run.** The first retarget pass looked unusable: the fast gaits put the boot 3 cm through
the deck and the stand clips skated 10.8 cm per foot with the feet never leaving the ground. The animation was
not the problem. Unreal's Python hands out *copies* of an op's chain array, so `for chain in chains` mutated
nothing and `set_editor_property` then stored the unchanged array - silently, because the scalars on the same
struct did take. Every chain was still on INTERPOLATED, both floor constraints were off, and the op stack had
no IK Chains op at all, so the leg goals were never given a target and every foot was pure FK. The script now
assigns by index and reads each value back off the op, and a setting that did not take is an error in the
receipt rather than a step claiming success. With that corrected the gaits ground correctly and are wired in
at their measured speeds (jog 205.5, run 384.3 cm/s against the walk's 180): at the pawn's 320 cm/s the run
plays at 0.83x rather than the walk being stretched to 1.78x, and at a sprint 1.46x rather than 3.11x.

**Footsteps exist.** There were none; the station was walked in silence. `ContentSource/Audio/Footstep.wav` is
generated the way this project generates all its provisional audio - deterministic, tracked, no licence - a
boot on deck plate at 0.3 s, deliberately the quietest and shortest sound in the set, because at a walk it
fires twice a second. It is triggered from the feet rather than from notifies on the clips: `ASSWalker` reads
the hero's own foot bones, named by its hero data, and sounds a step when one comes down near where that
hero's ankle rests in its reference pose, with a randomised pitch and a 0.12 s cooldown. That works for the
authored walk, the retargeted gaits and anything added later, and survives re-importing a clip, which a notify
would not.

**The tail, on the owner's instruction.** Nothing retargeted from a human carries tail motion, and no chain in
the retargeter touches `Tail_01..05` - measured, their local transforms deviate from frame 0 by 0.000 in every
clip the script produces. That deferral was the owner's ("differ more tail work outside of the current walk for
later"), then narrowed to "a subtle wobble to each for now, leave walk as is, and idle no wobble", then to
"can dial it in more later". `Scripts/AuthorHeroTailSway.py` writes one slow cycle per loop across the five
tail bones, 7 degrees at the tip on the fidgets and 4 on the gaits, amplitude growing toward the tip and each
bone lagging the one above it.

**Dialling it in later is the requirement, so it has to be idempotent, and the first version was not.** The
sway is composed onto the rotation the bone already has, so running it twice stacked two sways: asking for 4
after 7 would have given 11. The script now records each clip's untouched tail tracks to a baseline file
beside the clips on its first run and composes from that recording ever after, and it refuses to take a first
baseline from a tail that is already moving - which would bake an existing sway in permanently - telling you
to rebuild the clips with `AuthorHeroMocapRetarget.py` instead. Measured across two consecutive runs, every
tail rotation in all four clips agrees to 0.000002 degrees. The sway that lands is 13.89 degrees of travel on
the fidgets and 7.93 on the gaits, and `A_SquirrelIdle` measures 0.000 while `A_SquirrelWalk` keeps its own
authored 13.62 - both left exactly as the owner asked. The idle's tail is therefore still a motionless plume
from directly behind; the fidgets are what break that up.

**What is not adopted, and why.** Three of the eight retargeted clips are written to
`Licensed/MocapSource/` and referenced by nothing: the run-to-stop ends on a pose nothing returns from and its
sole reaches -2.20; the crouch idle folds a character that is mostly helmet and backpack into a pile; and the
MoCap walk exists only to be looked at beside the authored one, which stays, because the authored walk is
calibrated to this game's 180 cm/s and grounded to half a millimetre. `Config/DefaultGame.ini` names that
folder under `DirectoriesToNeverCook`, so the raw pack files and the unused derivatives stay out of the
shipping package while `/Game/SpaceSurvival` around them is always cooked - the pack's terms allow use, not
redistribution, and a cook is a redistribution. `THIRD_PARTY.md` records it as a retarget source with no mesh,
material or texture adopted.

**What is honestly wrong with the fidgets.** Measured as contact-patch path - per frame, the smallest
horizontal movement among the touching sole markers, summed, so a pivot scores zero and only a sliding flat
foot scores - the idle is 0.76/0.71 cm over 6.1 s and its toe never leaves a 0.17 cm circle, but fidget A is
7.73/10.84 cm with the toe wandering 4.07 cm on the deck, and that wander is invented by the retarget (the
source's feet move 1.41 cm, which at this body's 0.3935 height ratio should be 0.55). It survives because 4 cm
across five seconds is slower than the eye tracks. Fidget B's 3.46 cm step is real and in the capture. One
clearance to trip over if the mesh is re-exported: in the idle the glove passes the lower torso with 3.3 mm to
spare on the deck, and the idle is the pose held longest.

61 of 61 automation tests pass with no warnings, and Station 5 capture `f9fb7a985dd54b2882baf09f80907258`
certifies. Still open: no climb-out (RPT-20260917-01, below), no turn-in-place, and the walk moves neither head
nor wrists.

#### September 17 the exit animation is a gap, on the owner's direction

The owner watched the walker leave the ship and said it floats high above the hull, which it does. The 125 cm
arc is the game's, not the clip's: `ASSWalker::Tick` lerps the pawn from the ship to the deck between 0.82 s and
1.6 s and adds `sin(t * PI) * 125 cm` on top. With no door on the ship, any climb-out would pass through the hull,
so there is nothing an animation can do here yet.

**Direction taken, verbatim:** "let's not work about exit animation yet, we don't have a door on the ship yet, so
it'll just phase through anyways. Exit ship just have docking motion to landing, and after animation finishes.
appear outside of ship for now", and "log the animation gap for now".

So the exit becomes: the ship's docking motion plays to landing, and when it finishes the hero is placed outside
the ship, standing. No arc, no climb-out, no seated-to-standing pose handoff until there is a door to come out
of. The squirrel's disembark clip is not being authored; its walk and its seated pilot clip are, because the
owner's ask is the squirrel wearing its own animations. The pose-handoff machinery
(`SSStationPoseTransition`) stays in the code and keeps its tests: it is correct, it is just not what this
moment needs.

Recorded as RPT-20260917-01. What replaces the arc is not written yet.

#### September 17 the hero slot is described by data, and what the squirrel measured against it

Two things happened to the hero on September 17. The model itself is built, Blender-only, under the ignored
`.agent/local/HeroSquirrel/`: cleaned, re-rigged symmetric on 46 bones with five real tail bones and a straightened
tail, brought from 1,958,812 triangles to **198,994** with three LODs under it, and frozen as a base GLB with a
receipt and a validator. None of it is in the game.

**What Unreal says about it** (`.agent/local/HeroSquirrel/Stage5_Unreal/PROBE_FINDINGS.md`, measured in two probe
imports into the ignored, never-cooked `/Game/Blender/_HeroProbe`, deleted after): the import is clean. 46 bones,
`Root` at index 0, the glTF skin order kept index for index, no inserted root, no rename, no mirror, correct
centimetres, standing on Z = 0, facing +Y — which is the direction the −90° yaw on the mesh component already
expects. A test clip authored with the stage-4 composition poses the wrist, elbow, tail and head in Unreal to
within **0.0005 mm** of what Blender measured, so clips will play as they look. The engine's own render of the
imported asset is `Stage5_Unreal/ImportedPreview.png`.

**The obstacle is the slot, not the model.** `SK_AcornautTailV2` has 52 bones and shares only four names with the
squirrel — `Head`, `Pelvis`, `L_Foot`, `R_Foot` — and they do not mean the same thing: the Acornaut's `Pelvis` is
its root and its `L_Foot` is a toe, where the squirrel's `L_Foot` is the ankle. Every existing clip is bound to
`geometry_0_Skeleton`, so all three must be re-authored; `SSStationPoseTransition` would refuse a pose snapshot
across them, correctly. `SSWave10Soak` asked for `L_Wrist`/`R_Wrist`, which the squirrel does not have, and a
missing socket returns the component transform without complaining.

**So the hero is now data.** `FSSHeroDefinition` in `SSContentTypes.h` carries a hero's mesh, its three clips, the
sole offset that stands it on the deck, its scale or fit-height, its mesh yaw, the pilot mount, the walk handoff
second, the walk speed and the bone names the code asks for by hand; `USSPhase1Data::Heroes` holds the trooper,
the Acornaut and an inert squirrel entry whose assets do not exist yet, and `SelectHero(slot)` picks the first one
actually installed, exactly as the old `bTemporarySpaceHero` test did. The literals are gone from `ASSWalker`,
`ASSShip` and the soak. **Nothing the player sees changes**: four new tests in
`SSHeroSlotAutomationTests.cpp` pin today's numbers as literals so a later edit to the data cannot move the
current hero, 58 of 58 automation tests pass, and the Station 5 exit capture `9856021450074177907d2a8789a67467`
shows the walker riding the disembark arc and landing with its boots on the deck as before.

Two silences were also given a voice: `BeginDisembark` no longer discards the pose-snapshot result and says which
of the seven reasons refused it, and asking for a bone a hero does not have now returns false instead of quietly
reading the component transform.

**Still open:** the three clips (upright walk — the owner's instruction, "upright walk, not the scamper" — plus
pilot and disembark) are being authored against the frozen base; the seat fit that replaces the Acornaut-shaped
`(-15, 0, 72)` pilot mount is not measured yet; and nothing has been imported into the game.

#### September 17 the station target: what a pit stop looks like in this game

The owner: the station is "an odd box in front of a bigger object, with little detail, despite tons of purchased
assets... Make it fancy. Generate a mental target for what a space station pit stop should look like in this game,
and don't stop until you have it." This is the target. Everything that follows is measured against it.

**What it is in the fiction.** The exhale. The run is a field, an ambush, a wormhole, then this. It is the one lit,
working thing in a dead field: a garage in space, not a city. Approaching it should feel like coming into harbour at
night, and the eye should find it before the HUD does, because nothing else out there is lit.

**From three kilometres, on approach.** One silhouette, not two objects. A dark mass with a single bright slot cut
into it, a lane of blinking approach lights converging on the slot, and beacons on the extremities so the shape
reads against the field. Warm light spills out of the mouth onto the surrounding hull. The body is four to six times
the hangar in every dimension, so the hangar is a notch in the station and not the station itself: ship ten metres,
hangar thirty-four, body one hundred and fifty to two hundred and fifty.

**From three hundred metres, docking.** The mouth is cut into the body. The pilot flies under an overhang into a bay
whose walls are the station's own structure, not a box parked in front of it. Gantry lights frame the mouth and the
lane lights run on into the deck strip inside. **Visible equals solid**: the lit frame is exactly the collision gap,
which retires the death-through-the-window defect by construction rather than by tuning.

**Inside, the hangar.** Amber and dense, the concept video's beat. Overhead light strips. The ship parked centre
stage under a gantry, a real service arm over it. A mezzanine walkway along both long walls with railings and
equipment on it. Stacked containers, machinery and cabling filling the corners so the floor is never empty. Each
service is a physical thing: Launch Control is a booth with screens, the Engineer has a workbench, Contracts is a
wall of displays, Upgrades is a rack, and the new Paint Bay is a lift stand with a colour gantry over it. The loader
robot and the scout drone work the floor as ambient crew. The open mouth at the far end frames the field you came
in from, which is already the single best thing about the current room and stays.

**What does not move.** The docking corridor and its admission volume, the deck collision, the thirty-four by
twenty-eight metre floor, the service anchor positions, the save and service rules. All of it is gameplay-owned by
`ASSStation` and pinned by automation. The redesign wraps it; it does not renegotiate it.

**How it is judged.** From at least three angles every time, because a single view lets a floating object read as
attached; and contact is checked from bounds, not from a picture. In game, the Station5 scripted route provides
Approach, Docking, Idle, Services and Overview frames on one seed, so before and after are the same route.

**Assets, from the catalogue rendered today.** `Space_Station` A is mislabelled and is an asteroid cluster. B is a
ring-and-spire station, twelve units across, and is the strongest single silhouette in the set. 3 is two small rings.
4 is the H-shaped hulk currently in use. `TheCorner` is a fifty-seven metre landing disc. `Container_04` is a hard
case for interior dressing. The kitbash is **ten complete station designs in one Blender file, 1,268 objects, 12.7
million triangles, sixty-three materials**, and is the asset the owner meant. Nanite is already in use in this
project, so its density is usable rather than a problem.

#### September 17 the station target: what was built

**Exterior.** `Scripts/AuthorStationPitStop.py` (Blender, headless) composes the body from kitbash station 3 at
6.5x: a 180 m disc with its tower, and under its rim a dock module built as slabs around the hangar volume, so the
bay is open by construction and each slab is one collision box. The bow plate's inner edge is the admission gap
exactly (|Y| <= 700, Z -10..967.5 at X = -1700); a warm frame and bar mark it; window rows, cyan edge strips,
outrigger fins with nav lights and thirty kitbash greebles (size-capped, kept out of the mouth by test) make it read
as a lit, inhabited thing. Approach lane and beacons are part of the mesh. Every run renders nine views (approach,
front, under, side, quarter, ghost-through-the-mouth, keel under/side) and prints checks: zero body vertices inside
the hangar, mouth opening, enclosure margins. `Scripts/ImportStationPitStop.py` brings the glTF in at 0.01 scale as
one Nanite mesh, checks its size and centre against the receipt and records that the round trip mirrors Y;
`Scripts/GenerateStationPitStopBoxes.py` writes the thirteen collision boxes into `SSStationPitStopBoxes.inl` with
that sign, and `ASSStation::BuildHub` places body and boxes natively when the asset exists (the old exterior is the
fallback). Interior: `Scripts/PrepareStationPitStopLayout.py` writes the hangar recipe (mezzanines, gantry, stacks,
pipes, banners, the paint bay, amber overhead and mouth spill) and asserts the flight lane stays empty.

**Verification.** The Station5 route must be captured with `Scripts/CaptureEndgame.ps1 -Scenario Station5 -Editor
-CaptureVisuals`: the default mode runs the packaged build in `Artifacts/Windows`, which still holds the old
exterior until the next package. The layout library now logs which rule rejected a recipe instead of returning
nothing (the first failure was a licensed screen mesh with an empty material slot).

**Ship painter (owner request).** `PAINT BAY` service at (-1400, -1000) in every hub; panel cycles four sections
(body, wings, engines, weapons; found from each slot's material name, glass and lights excluded) over ten flat
finishes plus factory. Choices live on the account (`ACCOUNT` payload version 3; version 2 loads as factory) and
repaint the flying ship and the bay ship at once. `SSShipPaint.cpp`; tests `SpaceSurvival.Paint.*`.

**Prefab library and Blender live link (owner request).** See [PREFAB_LIVE_LINK.md](PREFAB_LIVE_LINK.md): every
owned static mesh catalogued by category with a glTF proxy, prefabs as `Prefabs/<Category>/<Name>.json`, the
`SS Prefabs` editor menu, and a Blender add-on that pushes, pulls and follows live over the engine's Python remote
execution. Both sides have headless self-tests.


## Review route when playtesting resumes

**For the new area/gallery work:** open `C:/Users/j6sis/SpaceSurvival/Play Development Build.cmd`. Its separate development profile keeps the installed game's saves apart. First visit **ALIEN WORLD** in the hangar, inspect the showcase, Tab/Y to the asset layout and Esc/B back. Current scene quality and lead-owned remaining checks are at the top of this log. The older packaged route below remains for release-specific PT checks.

The prior audited visual build remains available for owner review: **Package 4, source `cf6296f`**, at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows-before-0.1.17-20260916/SpaceSurvival.exe`. Keep the entire folder. It includes the provisional Havolk starter hull, refreshed space/combat presentation and furnished, editable station. The [project state](PROJECT_STATE.md#source-build-and-release) distinguishes this build, the blocked PR17 candidate and published itch 0.1.16-alpha.1 / build 1979965. Close the game and update through the itch app on windows-alpha to review the published version.

1. **Check the flight view first.** Open the executable, set controller sensitivity and preferred pitch direction, then launch and try ordinary turns, boost and brake. Judge the new starter silhouette, exhaust attachment, camera framing and hazard visibility against the space lighting. Relevant cases: PT-01,03–05,15,18.
2. **Check combat cues.** Fire at a target and look for a clear distinction between a shot, a hit and a confirmed death while hazards are present. Report the single most confusing moment, with a clip or screenshot if useful. Relevant cases: PT-06,12,18.
3. **Try one lasting station edit.** Open `C:/Users/j6sis/SpaceSurvival/SpaceSurvival.uproject`, then use **Tools > Station Workshop** and the [first-edit guide](STATION_EDITING.md#first-edit). Move or add one prop, Save + Apply, then open the normal Survival map and restart Play to see it in the station. Keep the marked corridor and fixed service anchors clear; check furnishings, robot staff and service-label readability from both sides. This editing check does not close the natural station cases PT-09,10,17,18.

When the owner resumes structured review, start with item 1; the lead records your build, device/settings and observations against the corresponding IDs, then brings you back to the next unresolved step. You do not need to edit Markdown or remember the full checklist. Partial observations leave the corresponding acceptance case open.

Technical validation: 49 Unreal tests passed cleanly at 23:57:10 UTC on September 14, covering the unchanged C++ implementation. The subsequent star-material change was authored, cooked and rendered separately. Package 4 passed its actual IoStore export/import audit and both packaged visual captures: 4 Wave 1 images and 16 Station 5 images. [Current validation](validation/2026-09-14-visual-enhancement-stars.json) binds the source, private inputs and actual package. Scripted captures and automated checks do not close natural play, visual quality or representative performance acceptance.

The new slice is absent from Package 4 and itch. Historical editor/VFX evidence is recorded in the [September 15 validation section](VALIDATION.md#september-15-flight-combat-and-space-slice); the newer local package remains blocked by the intermittent gallery failure recorded above. Package 4 remains the last published game payload.

## Current action queue and ownership

The sequence below is the active execution order. It covers the whole Phase 1 experience and keeps station work from hiding flight, combat, space, UI, audio, persistence and release gaps. An action starts only after owner direction; later actions remain visible while the active action is being reviewed. The lead owns integration and evidence. The owner supplies feel/art decisions after a concrete review build, and the regular 3D contributor owns the long-term hero and iconic starter.

| Order | Action | Scope and linked issues | Lead next action | Observable closure |
| --- | --- | --- | --- | --- |
| 0 | **ACT-00 — Asset Lab and evidence gate** | ISS-01/02/03/06/08/09/16 | After the owner starts implementation, establish one lightweight audition level, inventory the exact candidate dependencies and record each selection as **owned → imported → referenced → visible → accepted**. Use UAsset Browser if acquired; it is a selection aid, not acceptance. | At least one rejected and one selected candidate are shown for each role in the first slice; selected dependencies and license/source boundaries are recorded; no full pack is copied merely to browse it. |
| 1 | **ACT-01 — Flight, camera and propulsion** | ISS-02/05/08/10/12; PT-01–05,15,16,18 | Compare the current chase view and Havolk assembly against the target in ordinary turns, boost, brake and dodge. Audition owned trail/exhaust candidates and separate ship, camera and on-foot input settings. | Ship remains framed and readable; thrust states are visually/audibly distinct; KBM and controller settings behave independently; natural-play and packaged evidence pass. |
| 2 | **ACT-02 — Weapons and dynamic combat** | ISS-01/06/08/10/12; RPT-20260914-04/05, RPT-20260916-09; PT-06,12,18 | Build one complete Rapid Laser and Heavy Cannon cue chain: muzzle, travel, impact, shield/hull response, kill and synchronized sound. Audition owned shooting cues in repeated firing and combat against the owner's audio report. Exercise lateral/vertical pursuit, approach, evasion and cover instead of front-line formations. | Both weapons and enemy roles remain distinct in a busy fight; shots, hits and deaths are unmistakable; enemies maneuver in three dimensions; readability, listening/owner audio review and frame-time checks pass. |
| 3 | **ACT-03 — Asteroid field, debris and regional depth** | ISS-01/06/10/12/16; RPT-20260914-06; PT-03,06,09,12,18 | Compare the current custom field with Asteroid Library's Linear, Globular and Arch Blueprints; evaluate unused mineral/fragment families, close/mid/far materials, dust and ambient landmarks. Diagnose actual background resolution/filtering before replacement. | Different area scenes have deliberate near/mid/far silhouettes, distinct structures/materials, lighting and thin local haze. Open foregrounds reveal rich distant fields; approach, sparse/dense transitions and revisits remain coherent across run variations. Independent multi-area visual review and separate performance evidence pass; hazards stay readable. |
| 4 | **ACT-04 — Wormhole and distinct destination** | ISS-01/06/10/16; PT-09,12,13,18 | Run a controlled Wormhole Portal plugin pilot against the custom system, then combine the selected transition with owned nebula/galaxy/cosmic resources and a clearly different destination composition. | Approach, transit and exit read as one continuous event; the destination is immediately unfamiliar through structure, light, particles and landmarks; plugin cost/dependencies and fallback are documented. |
| 5 | **ACT-05 — Station arrival, exterior, interior and services** | ISS-03/04/09/10/13; RPT-20260914-02/03 and RPT-20260915-07; PT-09–13,17,18 | Reproduce entrance damage and collision reports, define a compact floor plan, connect the exterior to a believable entrance, and compose modular architecture before decorative props. Preserve service/save rules. | Arrival, docking, entrance, walking, services and departure form one coherent route; visible solids have suitable collision; labels do not block movement; service anchors remain reachable; Station 1 and 2 natural-play cases pass. |
| 6 | **ACT-06 — Character, NPC and station-life pass** | ISS-02/03/08/10/16; PT-01,10,18 | Validate temporary hero locomotion and exit animation; give robots/troopers/drone safe anchors and a small number of purposeful idle, patrol or work loops using owned animations. | Hero motion has no major deformation or foot/turn errors; NPCs do not intersect furniture; station activity has clear roles and stays within navigation, collision and performance limits. |
| 7 | **ACT-07 — Workshop semantics and reusable composition** | ISS-03/09/14/16 | Extend the existing decorative bridge only where needed for collision role, grouping/prefabs, snapping and repeatable Level Instance/Blueprint composition. Keep gameplay anchors guarded. | Owner can place and revise a representative room or exterior module, apply/export it, reopen it without drift, and identify which objects are decorative, blocking or interactive. |
| 8 | **ACT-08 — Audio, UI and input glyph integration** | ISS-05/08/13/16; RPT-20260916-09; PT-05–08,10,15–18 | Audition the selected audio by role, tune loops/mix/concurrency, and implement one shared action-to-input prompt path with device switching and text fallback. Carry ACT-02's shooting-audio selection into the full mix rather than create a separate repair. | Flight, combat, warnings, rewards, wormhole and station cues remain distinct; prompts match actual bindings/controller family and remain legible in busy scenes. |
| 9 | **ACT-09 — Progression, objectives, save and release safety** | ISS-04/07/11/13/14/15; PT-07–17,19 | Exercise the two-block loop, objective acceptance/outcome, depot, contracts, upgrades, death/unlock/retry and suspend/resume; finish private-asset backup and clean install/update checks. | Phase 1 progression and persistence cases pass without state loss; clean-machine/itch update identity is verified; paid/private assets remain out of Git; repository documentation enforcement is active. |
| 10 | **ACT-10 — Representative performance and final acceptance** | ISS-01–16; PT-01–19 | Profile the selected content in a natural busy run, complete Waves 1–10 and both stations with physical devices, and package the exact reviewed source. | All applicable PT cases have build/device/evidence records; representative 60 FPS target is assessed with frame-time distributions; remaining limitations are explicit; only then may Phase 1 move from PARTIAL. |
| 11 | **ACT-11 — Purchased module execution pass** | ISS-01/02/03/05/06/08/12/13/16; RPT-20260916-11 to RPT-20260916-20; PT-01,03,05,06,09,12,18 | Owner-directed September 16. Correct how already-purchased modules are actually executed in game rather than acquiring anything new. Four authorized threads, hero first by owner instruction: (a) bring the astronaut squirrel hero in as the player walker, which requires adding tail bones, removing the stray neutral_bone, a UE-compatible skeleton and retargeted locomotion; (b) port **Ship Core PRO** from the 5.6 install at EpicGames3/UE_5.6/Engine/Plugins/Marketplace/ShipCore46e00129d486V4 into the project's own Plugins directory, build it against 5.8, stand up a small isolated test environment, dial the settings in there and carry the tuned settings across to the game; (c) the environment fill pass against the owner's five reference images: restore usable volumetric fog and light shafts, raise hittable hazard density, and compose readable lanes so only some routes are right; (d) the danger pass: impact knockback, camera shake, controller force feedback, impact VFX at the contact point, visible hull damage, and enemy approach behaviour. Ship Core carries no engine-version blocker: it ships 26 C++ source files across two modules, so its 5.6 EngineVersion field is a launcher gate rather than a technical lock; its 5.6 Binaries and Intermediate folders must be discarded. Do not downgrade the engine. | Each thread closes only on hands-on owner confirmation in a rebuilt game, not on a compile, a fixture pass or a screenshot. Ship Core closes when its settings are dialled in a test environment AND carried into the real game and observed there. Every RPT-20260916-11 to -20 row must be individually retested and marked before ACT-11 is called complete. |

For each action, component count, successful import, Blueprint compilation, automated tests and a still image are intermediate evidence. Player-visible motion, sound, collision, interaction, representative performance and the exact packaged build determine acceptance. Fixed comparison cameras and short natural-play captures should use the visual target before/after whenever presentation changes.

### September 15 ACT-00–ACT-04 checkpoint

| Action | Implementation/evaluation checkpoint (`b6c58b8`, ACT-03 updated at `16007ab`) | State that remains open |
| --- | --- | --- |
| ACT-00 | Audited Asteroid Library's three construction-script field Blueprints, five sky candidates, Cosmic Material instances, Nerves, Niagara Examples, Sci-Fi Weapons VFX and the installed Wormhole Portal plugin. Fixed capture rejected the two Free Galaxy cubemaps from the region rotation after they produced a weaker sparse black/red scene; the three NebulaFantasy regions remain selected. | The audit is not a reusable audition level and no candidate is accepted from inventory alone. Private/vendor content remains outside Git. |
| ACT-01 | Drive state now reaches presentation; two nozzle cores, localized lights, trail scaling and speed-oriented dust distinguish idle/acceleration/boost/braking/damage in code. A first capture exposed hull washout; reduced emission and light radius restore readable ship surfaces. | RPT-20260915-08 records unfinished cubic thrusters. Fixed Boost/Brake stills do not show enough state distinction for acceptance. Natural motion, listening, package cooking, physical controls and owner judgment remain open. |
| ACT-02 | Rapid Laser, Heavy Cannon and enemy bolts have distinct native cores and bounded projectile lights even when optional Niagara is absent. Muzzle/impact/explosion light pulses are bounded. Pursuer/Flanker motion gains vertical/lateral/longitudinal variation and banking. The Nerves-derived electrical field and Sci-Fi Weapons discharge are authored private effects. | The scripted real-kill frame shows a visible spark/fire impact but cannot establish complete muzzle/travel/hit/death chains, audio sync, allegiance readability, dynamic combat feel or representative cost. RPT-20260914-04/05 and PT-06/12/18 remain open. |
| ACT-03 | Constructed and rendered all three native fields (336 instances each); baked their positions into private presentation data. Runtime uses 15 barren/mineral/fragment/debris meshes, four bands and the unchanged 384-instance budget. Sustained-travel parallax no longer saturates; dust is 320 smaller grains with less stretch. Fixed 2K/4K sky comparison selects 2K BC6H from the existing 8192x4096 source panoramas. [Evidence](validation/2026-09-15-asteroid-depth.json). | PARTIAL. Continuous-motion review of scale fading/recycling, natural near/mid/far depth, focal contrast, early hazard pressure, background fidelity and representative performance remain open. Native auditions are composition references, not matched-density gameplay benchmarks. No new package or owner acceptance. |
| ACT-04 | Wormhole Portal 1.0 is installed for UE5.8/Win64; 309 plugin assets and its runtime/sample/renderer/editor modules plus EnhancedInput/StateTree dependencies were inventoried. | Plugin is not enabled, spawned, cooked or timed. Current captures still show the custom ring transition, so approach/transit/destination acceptance remains open. |

### Owned-first purchase gate

Do not recommend or purchase another flight, combat, VFX, environment, audio, UI or workflow pack until the active action records all four points below:

1. The exact missing player-facing capability, with a target frame, clip or reproducible scenario.
2. The owned candidates already examined and their **owned/imported/referenced/visible/accepted** states.
3. Why each plausible owned candidate failed the role after a bounded audition, including quality, control, compatibility, dependency or performance evidence.
4. What the proposed purchase uniquely supplies, where it enters the action, and how it will be accepted in natural play.

A listing's screenshots, feature list or similarity to the target is discovery evidence only. Overlap belongs in the solution catalog. A purchase is justified by a demonstrated capability gap, not by incomplete use of an existing pack.

### Transfer packet for another model or contributor

Work on only one ACT item at a time unless its row explicitly requires a paired slice. Before handing it off, leave this compact packet in `.agent/CONTINUITY.md` and the PR's **Open / Check / Still open** section:

- **Action and objective:** ACT ID, linked ISS/RPT/PT IDs, and the exact player-facing result.
- **Authority and limits:** relevant GAME_SCOPE/IMPLEMENT requirements, explicit owner decisions, protected behavior and excluded work.
- **Current state:** branch, exact head, open PR, source/package/itch distinction, and whether private licensed content is required.
- **Inputs:** owned asset IDs/paths, target references, relevant skills to read, and the last accepted fallback.
- **Evidence:** baseline captures or reproduction, commands already run, receipts, observed failures and acceptance still missing.
- **Next operation:** one concrete bounded step, expected outputs and the condition for stopping or asking the owner to review.

The receiving model should begin from this packet and current files, then verify drift cheaply. It should not repeat the whole library audit, reinterpret scope or start a later action because the active action is difficult. Partial work updates the same ACT/ISS rows and remains open.

No other document maintains a separate active priority order. The [solution catalog](production/SOLUTION_CATALOG.md) records candidate value and utilization, not purchase authorization or scheduling. Work-package and Phase 2 documents provide context only; the action IDs above own current order.

## Art ownership

Owner decision, September 14: the regular 3D contributor owns the hero and iconic starter ship long term. The lead owns Unreal integration, collision/scale/socket/material checks, gameplay testing and packaging. Supplied AI models and kitbash alternatives are provisional, not replacements for that contributor's design ownership.

The owner purchased catalog C23, Space Ship 02 Modular Pack (Havolk). Its prepared assembly now supplies the default closed-cockpit starter, with the seated pilot hidden during flight, plus matching tier/utility hardware and the existing enemy-role derivatives. This is a provisional kit interpretation awaiting owner art review; Phase 1 still contains only the starter and scoped second ship. Future ship content stays deferred. ISS-02 owns art follow-up and ISS-14 the collaboration/storage setup; the owner confirmed the collaborator delivers model/texture/animation files only, not Unreal project edits. A private versioned Drive handoff is the proposed starting workflow; destination/access setup remains open.

## Implementation and verification issues

These are grouped problems, not extra game features or a completion percentage. Related PT cases below describe how to validate them. **All rows remain open.** A status of *Needs owner retest* means a bounded repair exists, not that the issue is accepted.

| ID | Issue and evidence boundary | Status / owner | Next action and closure evidence |
| --- | --- | --- | --- |
| <a id="iss-01"></a>ISS-01 | Space depth, lighting, VFX and wormhole arrival remain unaccepted against the visual target. The packaged pass includes three blended owned nebula cubemaps, warm key light, eight ambient rock shapes, smaller dust grains, distant structures and bounded combat effects. Package 4 reduces the previously overpowering stars, but RPT-20260914-06 still describes fuzzy, low-quality backgrounds. The native Asteroid Library field Blueprints, broader Niagara library, Free Galaxy Shader, Cosmic Materials and installed Wormhole Portal plugin have not been accepted as an integrated moving experience. Nozzle/exhaust response, parallax, directional variety and unfamiliar arrival feel remain open. [Combined record](production/COMBINED_SPACE_LOOK.md). | Needs integrated visual review / lead | Execute ACT-01/03/04 from fixed target cameras and natural combat. Close only with accepted motion, focal contrast, depth, destination differentiation and packaged performance, not asset presence or a screenshot alone. PT-03,09,12,13,18. |
| <a id="iss-02"></a>ISS-02 | Hero/ships and continuous animation remain provisional. The default starter is the purchased Havolk closed-cockpit assembly; only a small subset of the modular ship pack is visible in normal progression despite its value for tier silhouettes, enemy roles, ambient traffic, wreckage and hangar previews. When the owned Sci-Fi Space Character packages are present, the station walker uses that temporary hero with matching walk and exit animation; missing/incompatible content falls back to Acornaut. Automation covers both routes, but rendered/package review and natural motion remain open. The regular contributor still owns the long-term hero and iconic starter. [Current validation](VALIDATION.md), [earlier refresh](ASSET_REFRESH.md). | Needs owner retest + art work / regular 3D contributor; lead integrates | Use ACT-01/06 to judge the hull, fitted modules and temporary hero in motion; validate scale, sockets, collision, materials, animation and package cooking. Preserve contributor ownership and original sources. PT-01,03,10,18. |
| <a id="iss-03"></a>ISS-03 | Station arrival, composition, physical coherence and ambience remain unaccepted. Capture-only reports RPT-20260914-02/03 and RPT-20260915-07 describe walk-through props, blockage near labels, an NPC intersecting a table and repeated collision damage after catching an entrance edge; causes remain unconfirmed. The saved 380-component Blueprint demonstrates dressing breadth, but much of that dressing is nonblocking and the main exterior mass does not yet establish a continuous exterior-to-interior route. Owned modular architecture, screens, electronic-prop Blueprints, station GLBs, robots and character animation remain lightly used. Native services/save rules stay authoritative. [Station editing](STATION_EDITING.md). | Needs reconstruction and natural review / lead; owner composes/reviews | Execute ACT-05/06/07: reproduce defects, establish floor plan/entrance/collision roles, then add purposeful architecture, activity, lighting and sound. Close with natural approach, traversal, services, exit and package evidence. PT-09,10,12,13,17,18. |
| <a id="iss-04"></a>ISS-04 | Station 2 services/save/discard boundary needs usability and replay-appeal acceptance. Actual failure/retry persistence tests exist; no Wave 11 or completion XP is authorized. [Boundary evidence](STATION2_DISCARD.md). | Needs owner/QA verification / lead | Natural arrival, service/save/discard and next-run review. Preserve disclosed zero-death-XP discard. PT-13,14,17,19. |
| <a id="iss-05"></a>ISS-05 | Input comfort, camera framing and full physical-device parity remain unaccepted. B23 glyphs have local artwork/dependency inspection and a [selective integration record](production/SOLUTION_CATALOG.md#new-local-audio-and-glyphs-evaluation-and-selective-integration); glyphs, device switching and mapping changes remain unimplemented. New capture-only report RPT-20260914-01 says flight inversion also changes character controls; independent preferences need later verification. Station rear-camera, inversion and flight framing fixes exist. Owner feedback F01/F09/F10 says starter handling is decent but inverse mouse was a barrier; controller is preferred. [Camera](STATION_CAMERA.md), [environment](ENVIRONMENT_REFRESH.md). | Needs owner retest / lead | Calibrate preferred inversion/sensitivity before retuning; verify KBM and controller, reconnect and menu focus. PT-02–05,15–17. |
| <a id="iss-06"></a>ISS-06 | Natural combat, hit/death certainty, target identification, reward cadence and Director fairness need integrated play. RPT-20260914-04 says the base shot is barely visible; RPT-20260914-05 says combat feels front-lined rather than like a dynamic space fight. Existing bolt/muzzle/impact/explosion effects and deterministic projectile/fragment/admission repairs do not settle feel or balance. The real-kill fixture verifies explosion activation, but a visible fire/smoke plume remains unverified. Hundreds of owned weapon/Niagara candidates have not been compared as complete role-based cue chains. [Gameplay repairs](GAMEPLAY_QUALITY.md), [combat cues](COMBAT_CUES.md). | Needs integrated combat slice / lead | Execute ACT-02: compare owned effects for muzzle/travel/impact/kill, synchronize audio/light, and test both enemy roles with lateral/vertical maneuvering amid hazards. Preserve manual aim and scoped rosters. PT-06,07,09,12–14,18,19. |
| <a id="iss-07"></a>ISS-07 | Save safety is verified only within bounded fault cases. Disk-full/short-write, arbitrary binary corruption and hardware-loss remain untested; generic Windows backend only, no multi-slot transaction/automatic backup. [Fault](validation/2026-09-13-storage-faults.json) and [corruption](validation/2026-09-13-corrupt-account.json) evidence. | Needs qualification / lead | Isolated profiles and guarded reproducible failure tests; preserve owner saves. Record unsupported cases honestly. PT-11,14,17 for natural UI path. |
| <a id="iss-08"></a>ISS-08 | UI/audio/music need actual listening and busy-scene review. RPT-20260916-09 records the owner's dislike of the shooting audio; exact cue/build and cause remain unconfirmed. The A21/A22 inventory covers 1,410 recordings plus cue wrappers. The separate `cplomedia_spaceship` source supplies ten selected roles for engine, weapons, impact, pickup, alarm, station ambience and enemy/debris events; runtime references prefer the private licensed assets and fall back to generated sources when absent. Historical Editor build and 49-test automation evidence do not establish listening, loop-seam/mix judgment or package cooking. Glyph integration is still pending. [Audio hooks](AUDIO_HOOKS.md). | Needs audio improvement and acceptance / lead | Through ACT-02/08, reproduce both weapon cues, compare owned candidates during repeated fire and combat, then tune distinction, levels, looping and concurrency. Require listening and owner review for the shooting report. Evaluate the limited glyph sample without coupling it to inversion repair. PT-05,06,10,16,18. |
| <a id="iss-09"></a>ISS-09 | The owner-authorized editor workshop adds asset-browser placement/rotation/scaling/deletion, ten materials and saved-map application/export in PR14; Editor build, nine save/apply/export checks and the visible asset-browser capture pass; [receipt](validation/2026-09-15-station-workshop.json). The owned-asset follow-up validates **708** filtered placeables: 702 under `/Game` plus six engine basic shapes, including 26 Sci-Fi Space Character, two Heavy Space Trooper, two Cosmic Material and one private drone entries. Material assets remain available through the Details panel; the curated preset list stays at ten. [Station editing](STATION_EDITING.md) describes the controls and supported-content boundary. Gameplay collision/service anchors and native menus/behavior remain separate. | Needs review / lead | Place, transform, material-swap, delete, export and apply a representative new asset; verify the saved scene in play. Keep unsupported behavior actors and gameplay anchors outside the decorative bridge. |
| <a id="iss-10"></a>ISS-10 | Representative 60 FPS/full-run CPU/GPU/RAM/VRAM acceptance is open. Older RTX 5080 scripted samples are bounded; current Wave1 capture includes readback/startup stalls, and standard analyzer rejects that scenario. [Performance](PERFORMANCE.md), [combined diagnostic](production/COMBINED_SPACE_LOOK.md). | Needs qualification / lead | Fix/extend scenario analysis where justified, profile a natural busy run and scaling; report frame-time distributions and hardware. No claim of “120 FPS accepted” from capped screenshot fixtures. |
| <a id="iss-11"></a>ISS-11 | **Published 0.1.17-alpha (build 1984728) on owner direction WITH an open defect: owner hands-on entry to the alien gallery failed once and then succeeded after a reload (RPT-20260916-10); the entry-path defect is undiagnosed and ships in this build.** The earlier intermittent packaged gallery *exit* is fixed at its demonstrated cause (scripted fixtures now isolated from physical controller input) and 14 of 14 packaged round trips pass. Packaged flight, Station 5 transitions and the IoStore dependency audit pass, and `0.1.17-alpha` is prepared and locally verified at 51 files / 2,715,833,034 bytes. Prior 0.1.16-alpha.1 (build 1979965) is superseded; release preparation filters runtime saves/config/logs. Upload, clean-PC startup and real itch A-to-B update/save preservation remain unverified. Devlog remains a draft pending browser sign-in. [Release workflow](ITCH_RELEASES.md); [evidence](validation/2026-09-16-gallery-input-isolation.json). | Published with open defect | Diagnose the shipped entry-path defect: add rejection logging to `USSAlienGallery::Enter`, repackage and capture one owner press. Tell the tester the doorway may need a relaunch. Upload and merge still require owner direction. Retain clean-install/update and devlog follow-ups. |
| <a id="iss-12"></a>ISS-12 | Continuous contact uses linear per-frame player/shot motion; enemy/world-cover queries use current transforms. Nonlinear paths inside a hitch are not reconstructed. [Gameplay follow-up](validation/2026-09-13-gameplay-fairness-followup.json). | Known approximation / lead | Reproduce an unfair contact before broad redesign; retain first-contact/cover-order regressions and document practical hitch limits. PT-04,06,12. |
| <a id="iss-13"></a>ISS-13 | Event/depot/contract/beacon clarity and live input need retest. F02/F03/F04/F07/D01 map here: following distraction, unclear objective/beacon/allegiance, and optional magnetic parking. Mooring/feedback repairs exist. Issue #7 additionally flags live reward device differences and synchronous tutorial saves; runtime impact is not established. [Feedback provenance](production/OWNER_FEEDBACK.md), [review issue](https://github.com/j6sistek-ui/SpaceSurvival/issues/7). | Needs owner retest/investigation / lead | Verify explicit acceptance, objective/progress/outcome, 20-second aboard-ship lock/release and no lingering follower; reproduce input/write risks before claiming a fix. PT-07,08,10,16,17. |
| <a id="iss-14"></a>ISS-14 | GitHub is not a complete backup of local licensed derivatives, raw downloads, manual tuning, art experiments or saves. Source-export checks do not reproduce the current licensed look from Git alone. [Storage map](PROJECT_STATE.md#where-files-live), [source integrity](SOURCE_INTEGRITY.md). | Needs collaborator handoff/backup plan / lead + owner for storage choice | Choose the shared handoff destination, then inventory unique inputs and document private backup/reacquisition, versioned upload, import and restore paths. See the proposed asset collaboration workflow in Project State. Verify a fresh development setup without publishing paid source assets. No cleanup/deletion is implied. |
| <a id="iss-15"></a>ISS-15 | PR documentation enforcement: template/CI check merged through PR11; last ruleset audit requires PRs but no successful status checks. A running check is not yet a server merge requirement. | Needs repository setting / lead | After explicit repository-setting approval, add the verified documentation job to required checks while preserving existing rules. Confirm a failed check blocks merging. No branch-rule change is claimed by this PR. |
| <a id="iss-16"></a>ISS-16 | Owned-asset utilization and selection discipline are unaccepted. A September 15 offline inventory found 3,603 third-party files (about 9.87 GiB) already inside project Content, while the largest packs are represented by only a small number of runtime selections. External owner-project and VaultCache copies add substantial duplicated storage, but deletion is unauthorized. Asset presence, a generated derivative or a component count has too often stood in for player-visible acceptance. [Solution catalog utilization](production/SOLUTION_CATALOG.md#owned-library-utilization-audit) records roles without becoming a second queue. | Needs controlled pipeline / lead | Execute ACT-00, then require owned/imported/referenced/visible/accepted status and role-based candidate comparisons for later actions. After accepted migration, audit dependencies and package size before proposing any deletion. |
| <a id="iss-17"></a>ISS-17 | **Editor build broken by an enabled plugin.** `Tripo3DUEBridge` was enabled in `SpaceSurvival.uproject` in the working tree and every `./Scripts/Build.ps1 -Target Editor` then fails in 0.61 s with `Expecting to find a type to be declared in a module rules named 'Tripo3DUEBridge'` and `Result: Failed (RulesError)`. The plugin is installed at `EpicGames2/UE_5.8/Engine/Plugins/Tripo3DUEBridge-UE5.8-Win64` and does contain a correct `Tripo3DUEBridge.Build.cs` declaring `public class Tripo3DUEBridge : ModuleRules`, so the file exists but its type is absent from the compiled UE5Rules assembly. It is marked `"Installed": true` with prebuilt Win64 binaries, which is the likely conflict when the project's editor target is built from source. This was NOT caused by the Ship Core port; it predates it and blocks all editor compilation. | Open / lead; blocks ACT-11 | The plugin is disabled in the uproject with an inline comment so the editor builds again. Editor-only import convenience, so the game is unaffected and the squirrel hero does not need it because that asset is already exported as GLB. Next decide whether to repair it (move it under `Engine/Plugins/Marketplace`, or clear its Installed flag and let it build from source) or leave it disabled. Closure evidence: a passing `./Scripts/Build.ps1 -Target Editor` with the plugin enabled. |

## Hands-on acceptance cases

**19 open / 0 passed** at this update. All 19 previously unchecked cases remain here; none was accepted by this planning edit. They are acceptance scenarios related to the issues and actions above, not 19 additional features or a required single sitting.

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

## 2026-09-20 owner playtest — unactioned, several game-breaking

Reported by the owner after playing. **Nothing here was investigated, reproduced or fixed** — logged
verbatim so it survives the session. Ordered as reported, not by severity.

### Flight

- **Cannot tell whether the ship is firing.** No readable feedback that a shot happened.
- **Controls are wrong.** *"there's no pitch or rotation in flight or i don't understand the
  controls"* — either the axes are missing or they are undiscoverable. Both are failures.
- The owner's own diagnosis, and it should be the first thing checked:
  **"this is like the should have used the blueprint thing again."** `BP_Spaceship` ships a
  128-node EventGraph, nine tunable flight variables and its own input mappings
  (`Thrust`, `MoveRight`, `Roll`, `MoveUp`, `TakeOff`, `BattleMode`, `Landing`, `EnterExitShip`),
  none of which are registered in project input settings. `ASSShip` re-implements flight in C++.
  See the Phoenix section of the blueprint-first rule.

### Approaching the station

- **Very hard to slow down** on approach.
- **The background went 100% white** near the station — a full white sky, not the space backdrop.
- **No way to tell how to land.** No affordance, prompt or cue.
- Outcome: **crashed and died.**

### Inside the station

- Floor coverage is fine; the dressing is not. **"an absolute MESS. objects floating everywhere,
  disorganized as hell."**
- Note this contradicts the staged captures taken the same day. Those were composed shots with an
  added light rig at chosen angles; they are not evidence about the station a player walks into.
  The owner: *"how you had one good cinematic scene earlier blows my mind."* Treat every previous
  capture of the station interior as unrepresentative until a playthrough says otherwise.

- **Cameras visible everywhere** in the station. Source unknown - not investigated. Worth ruling out
  first: the capture actors used for development were removed from `Survival` and the map was saved
  clean at six actors, so these are more likely to be coming from a pack's demo content or from
  something the station spawns at runtime.
- **The player stands half inside the floor.**

  A measured lead, found the same day while placing characters and never applied to the player:
  **the deck surface is not at z=0.** `SM_Floor_C` is placed at z=0 but its geometry spans
  `-10.00 .. +10.70`, and `SM_FloorDiv_A` reaches `+11.46`. A character grounded to z=0 is buried to
  roughly the ankle. That is smaller than "half in the floor", so it is a contributing cause at most
  and something else is likely wrong as well - but it is a real number and the first thing to check.
  `ASSWalker::MeshLift` computes its lift from `ScaledSoleOffset`, the capsule half height and the
  walking floor gap, with no term for the floor mesh sitting above its own placement Z.

- **Most objects have no collision - the player walks through them, almost nothing is attached.**

### What a live PIE session ruled out

Observed directly in a running PIE session, 31 actors. These narrow the search rather than solve
anything:

- **There is no `SkyAtmosphere` actor in the level.** The white sky is therefore not a stray sky
  actor. The remaining candidates are `ReadableSpaceExposure` auto-adapting to a dark station and
  blowing out the backdrop, or the backdrop material itself.
- **There are no camera actors in the level.** "Cameras everywhere" is not stray capture or cine
  actors - it is meshes that read as cameras, or HUD.
- `DeepSpaceBackdrop` and `DistantStarfield` sit at the player's exact position and track the viewer,
  which is how a skybox is supposed to behave. Not a bug.
- The screenshot was taken on the **landing pad** (`SSLandingPad_3`, z = -10), not on the station
  deck, so the sunk-player and floating-prop reports should be confirmed in both places separately.
- The station itself is present and built: `SSStation_3` with `BP_StationVisualLayout_C_3`.

Confirmed visually in that screenshot: the player is buried to roughly the knee, and the sky is a
bright daylight-like gradient rather than space.

### The "cameras" are mine, and so is the mess - identified

A second PIE screenshot, inside the station, identified the objects the owner read as cameras:
they are **`SM_Monitor`, a wall-mounted mesh, placed free-floating in open air by
`Scripts/MakeStationRecipe.py`.** From behind, a boxy monitor on a stalk reads as a studio camera on
a boom. Not stray capture actors - recipe output.

Counted from `Artifacts/StationRecipe/station_recipe.json`, **164 props are placed at mid-air heights
with nothing to attach to** (deck is z=0, ceiling 307):

| Asset | Count | Z range | Belongs |
|---|---|---|---|
| `SM_CorridorCable01` | 74 | 51 .. 165 | along a wall |
| `SM_Hook_01` | 42 | 143 .. 357 | wall or ceiling |
| `SM_Monitor` | 22 | 144 .. 189 | **wall-mounted** |
| `SM_Crate_Part` | 17 | 0 .. 221 | on a surface |
| `SM_Flag_02` | 9 | 108 .. 240 | hung on a wall |

The generator has a `MONITOR` constant whose own comment reads *"centred, wall-mounted"*. It was
placed by coordinate anyway, with no check that a wall exists behind it. The same applies to the
hooks, flags and cables.

This is the direct cause of *"objects floating everywhere disorganized as hell"*, and it is a
generator bug, not a content problem - the fix belongs in `MakeStationRecipe.py`, which must place a
wall-mounted prop against an actual wall face or not at all.

It also explains why the staged captures looked fine: every one of them was framed to avoid these.

### The wardrobe kiosk does not exist in the home hangar

Reported 2026-09-20 as *"kiosk blocked by something."* **Resolved 2026-09-21: it is not blocked, it
is absent.** Diagnosed live in PIE.

`CREW WARDROBE` is added only at a station (`SSStation.cpp:385`):

```cpp
if (!Home)
    AddService(FVector(-1400, 500, 0), TEXT("CREW WARDROBE"), ESSPanel::Wardrobe);
```

The owner was in the **home hangar**, confirmed two ways: the deck showed `PILOT RECORD`, which is
the home-only label for the kiosk that reads `CONTRACT BOARD` at a station (`:379`); and the station
actor sat at the world origin, which is where the home path spawns it (`SSGameMode.cpp:301`) rather
than at `StationTarget` (`:424`). So the kiosk was never in `Services`, and Interact at its
coordinates resolved to Pilot Record instead - the nearest service that exists.

**This is working as written.** The comment above the gate states the intent: the home hangar is
where a run is prepared, not where the crew get changed. Whether that is the right call is an open
design question, not a defect. **Not changed.**

**What is a defect** is that it is indistinguishable from a broken kiosk. Three things compound:

- Interact gives **no feedback when nothing is in range.** `NearestService` uses a 280 cm radius
  (`SSStation.cpp:577`) and returns `ESSPanel::None` silently past it.
- There is **no proximity prompt** on a service, so a kiosk that is 6 m away and one that does not
  exist look identical - the player is standing in the right area either way.
- The walkable box is **35 x 29 m** (`:554`) while the station art is 108 x 86 m, so hunting for a
  service across what looks like open deck teleports the player to spawn with no message.

Measured during the same session: the owner believed they were at `LAUNCH CONTROL` while standing at
(950, 140); it is at (950, -450). Same x, **5.9 m off on y** - more than twice the interact radius,
with nothing on screen to say so.

The eighth body wired in on 2026-09-20 therefore **still has never been seen in the wardrobe panel.**
The automation proves the roster holds eight and that the alien fits the deck; it does not prove the
panel opens or lists them. That check needs a station, not the hangar.

### Why this list exists

`CLAUDE.md` already says *"Treat '67 tests pass' as saying nothing about what a player receives."*
This is that, demonstrated: the suite was green, the build succeeded, and the game was unplayable.
Playtest before claiming any of this works.
