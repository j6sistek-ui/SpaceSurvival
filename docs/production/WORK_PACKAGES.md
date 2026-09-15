# Phase 1 work package dictionary

This is the **September 13 historical proposal baseline**, retained as a work/asset dictionary alongside [the production rationale](QUALITY_PLAN.md). Every `State: Planned` field below and in [WORK_PACKAGES.csv](WORK_PACKAGES.csv) describes that proposal; it is not live scheduling, a claim that existing systems are missing, or a current completion verdict. [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) alone tracks active priorities, work and owner acceptance; [PROJECT_STATE.md](../PROJECT_STATE.md) records current source/build/storage.

Existing systems should be repaired/refined, not recreated merely because they appear here. Implementation, integration, technical verification and owner quality acceptance are separate outcomes recorded in the active ledger, not maintained again in this dictionary.

Effort: S = bounded definition task; M = several coupled deliverables; L = repeated cross-discipline iteration. These are relative planning sizes, not days, prices or additive schedule estimates. Assignments below were proposed and unscheduled at the September 13 baseline. Dependencies refer to package IDs required for integrated acceptance, not strict finish-to-start scheduling. Samples start when their interfaces are stable. Instrumentation, benchmark audio, QA and profiling start at G0/G1 and recur throughout production; the CSV includes start_guidance.

## 1. Direction and shared contracts

### 1.1 Experience benchmark and reference contract

**Needs:** Annotate asteroid reference with ship framing, scale hierarchy, readable route, near passes and feedback; capture current baseline at same view.

**Proposed owner:** Lead + owner. **Source strategy:** No purchase.

**Acceptance predecessors:** None. **Relative effort:** S.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Owner selects the comparison view and names the missing sensations.

**Basis:** Briefing pp1,7-9,18. **State:** Planned; quality acceptance open.

### 1.2 Shared content integration contract

**Needs:** Freeze units, axes, camera envelope, pilot/seat/grip/tail space, collision hull, sockets, asset names, export/import settings and source handoff rules.

**Proposed owner:** Lead technical artist/agent. **Source strategy:** Specialist reviews contract.

**Acceptance predecessors:** 1.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** One alignment scene opens correctly in Blender and UE; both artists sign off dimensions.

**Basis:** Briefing pp3-4,17. **State:** Planned; quality acceptance open.

### 1.3 Test and tuning workbench

**Needs:** Record approach speed, time to possible contact, damage cause, encounter composition, frame time and exact build; expose safe Data Asset tuning controls.

**Proposed owner:** Agent. **Source strategy:** Build internally.

**Acceptance predecessors:** 1.1. **Relative effort:** M.

**Start guidance:** Start G0/G1; instrument first comparisons and extend through qualification.

**Accept when:** Two settings can be compared reproducibly without changing canonical run rules or shipping debug overlays.

**Basis:** Scope 5,45-49. **State:** Planned; quality acceptance open.

## 2. Flight and survival feel

### 2.1 Flight authority and devices

**Needs:** Tune forward motion, pitch/yaw/bank, acceleration, inertia, mouse and stick curves, sensitivity dial and inversion; preserve frame independence.

**Proposed owner:** Agent + owner playtest. **Source strategy:** Build internally.

**Acceptance predecessors:** 1.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Owner can intentionally weave and recover with mouse and controller; no unexplained reversal or drift.

**Basis:** Briefing p7. **State:** Planned; quality acceptance open.

### 2.2 Boost brake and dodge decisions

**Needs:** Tune resource cadence, heat-limited partial brake, directional burst and recovery; add clear cooldown/overheat/boost feedback with no invulnerability.

**Proposed owner:** Agent + owner playtest. **Source strategy:** Sound sources possible.

**Acceptance predecessors:** 2.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Each maneuver solves a different danger; braking cannot bypass the field; dodging into a rock still hurts.

**Basis:** Scope 6. **State:** Planned; quality acceptance open.

### 2.3 Flight chase framing

**Needs:** Tight stable rear view composed around actual ship/pilot; modest pullback and bank response; reticle visibility and optional shake/blur.

**Proposed owner:** Agent + technical artist. **Source strategy:** Build internally.

**Acceptance predecessors:** 1.2;2.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Near obstacles and pilot remain readable at high speed on both devices without camera mode changes.

**Basis:** Briefing pp7-9. **State:** Planned; quality acceptance open.

### 2.4 Damage and recovery feedback

**Needs:** Shield versus hull response, impact direction and weight, contextual hull regeneration, severe impact/subsystem warnings, repair feedback.

**Proposed owner:** Agent + audio/VFX specialist. **Source strategy:** License source sounds; custom final mix.

**Acceptance predecessors:** 2.2;2.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Player explains what hit them and what recovered; shield never passively refills and purchases survive temporary impairment.

**Basis:** Briefing p11. **State:** Planned; quality acceptance open.

## 3. Asteroids and environmental hazards

### 3.1 Asteroid mesh and surface family

**Needs:** Source small/medium/massive rocky silhouettes; irregular profiles, fracture interiors, roughness/normal detail, LODs and collision proxies.

**Proposed owner:** Environment artist + agent. **Source strategy:** Buy curated rock kit then normalize.

**Acceptance predecessors:** 1.1;1.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** At chase distance bodies read by scale and avoid/destroy role; surface detail holds during close pass.

**Basis:** Briefing p9; art/asteroids.jpg. **State:** Planned; quality acceptance open.

### 3.2 Asteroid field composition

**Needs:** Author safe but threatening arrangements, foreground framing, mid-distance decisions, far non-colliding density, moving scale/depth cues.

**Proposed owner:** Agent + encounter designer. **Source strategy:** Custom layouts using kit.

**Acceptance predecessors:** 2.1;2.3;3.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Short natural-play benchmark evokes reference intensity while leaving a visible reachable escape choice.

**Basis:** Briefing pp7-9. **State:** Planned; quality acceptance open.

### 3.3 Destruction and fragments

**Needs:** Small destruction, medium break states and bounded dangerous fragments, hit flashes/debris/audio, useful drops; massive rocks stay avoid-only.

**Proposed owner:** Agent + VFX artist. **Source strategy:** Kit fracture meshes can help.

**Acceptance predecessors:** 2.4;3.1;3.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Shoot-versus-avoid decision is meaningful; fragments are warned/reactable and cannot spawn unavoidable hits.

**Basis:** Scope 10. **State:** Planned; quality acceptance open.

### 3.4 Wreckage passages

**Needs:** Coherent torn hull beams/panels/large structures, collision-aware passage chunks, salvage route geometry and background dressing.

**Proposed owner:** Environment artist + agent. **Source strategy:** Reuse station kit or one compatible wreckage pack.

**Acceptance predecessors:** 1.2;3.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Passages read before commitment; silhouette matches collision; optional risky route is distinct.

**Basis:** Briefing p9; art/wreckage.jpg. **State:** Planned; quality acceptance open.

### 3.5 Electrical storm

**Needs:** Readable buildup and discharge synchronized to actual damage/interference; spatial cue, bounded flash/visibility, aftermath.

**Proposed owner:** Agent + Niagara/audio specialist. **Source strategy:** License reusable elements; custom behavior.

**Acceptance predecessors:** 2.4;3.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Tester anticipates pulse and understands electrical consequence; no opaque or constant flash wall.

**Basis:** Briefing p9; art/storm.jpg. **State:** Planned; quality acceptance open.

### 3.6 Gravity anomaly

**Needs:** Visible force direction, ship/debris response, approach/escape cues, controllable disturbance and scalable distortion.

**Proposed owner:** Agent + Niagara specialist. **Source strategy:** Custom signature effect.

**Acceptance predecessors:** 2.1;3.2. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Player can predict pull and countersteer; screen distortion never hides the route.

**Basis:** Briefing p9; art/gravity.jpg. **State:** Planned; quality acceptance open.

## 4. Director and ten-wave experience

### 4.1 Director pacing and variety

**Needs:** Tune pressure composition, arrival directions, overlap caps, reaction space, persistence and short release windows using existing four families.

**Proposed owner:** Agent + encounter designer + owner. **Source strategy:** Build internally.

**Acceptance predecessors:** 3.2;3.4;3.5;3.6;5.1;5.2. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Repeated same-wave runs differ perceptibly; threat changes have readable lead-in; relief stays around 20s maximum.

**Basis:** Briefing pp5-8. **State:** Planned; quality acceptance open.

### 4.2 Wave 5 sequence

**Needs:** Disturbance/pull/transit effect, audio progression, hostile combat entry, surviving exit into station approach; retain one flight model.

**Proposed owner:** Agent + VFX/audio specialist. **Source strategy:** Custom wormhole presentation.

**Acceptance predecessors:** 4.1;5.3;5.4;8.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Natural unassisted run reaches station through a continuous sequence; no apparent loading/minigame switch.

**Basis:** Briefing p16. **State:** Planned; quality acceptance open.

### 4.3 Waves 6-10 and compound climax

**Needs:** Escalate speed/composition/overlap; Wave10 gravity plus asteroid storm plus enemy pressure under common fairness budgets.

**Proposed owner:** Agent + owner. **Source strategy:** Build internally.

**Acceptance predecessors:** 4.1;4.2;6.2;6.3. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Normal durability/loadout survives by decisions; later block feels harder without extra roster or health inflation.

**Basis:** Briefing pp8,16. **State:** Planned; quality acceptance open.

## 5. Combat and enemies

### 5.1 Pursuer

**Needs:** Recognizable silhouette and engine trail, closing trajectory, attack windup/shot cue, hazard interaction, damaged/death presentation.

**Proposed owner:** Agent AI + vehicle artist. **Source strategy:** License secondary craft if style-compatible.

**Acceptance predecessors:** 1.2;2.3;3.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Player identifies closing threat and a response without reading a label.

**Basis:** Briefing p10. **State:** Planned; quality acceptance open.

### 5.2 Flanker

**Needs:** Distinct silhouette and wider flight path, lateral attention cues, committed attack and disengagement; preserve environment interaction.

**Proposed owner:** Agent AI + vehicle artist. **Source strategy:** Pair with same enemy art family.

**Acceptance predecessors:** 5.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Player recognizes flanking behavior and divides attention; not a recolored pursuer.

**Basis:** Briefing p10. **State:** Planned; quality acceptance open.

### 5.3 Rapid Laser

**Needs:** Ship-mounted visual/emitter if visible, muzzle socket, rapid shot/hit VFX, fire/impact audio and tier response; manual aim and soft targeting.

**Proposed owner:** Agent + VFX/audio specialist. **Source strategy:** No separate handheld gun model needed.

**Acceptance predecessors:** 1.2;2.3;3.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Fast forgiving fire useful for fighters/small debris; assistance never removes manual intent or shoots through cover.

**Basis:** Briefing p10. **State:** Planned; quality acceptance open.

### 5.4 Heavy Cannon

**Needs:** Mount/barrel silhouette where visible, heavy projectile and muzzle/impact timing, strong restrained recoil/audio, slower firing rhythm.

**Proposed owner:** Agent + VFX/audio specialist. **Source strategy:** Custom shared ship attachment family.

**Acceptance predecessors:** 5.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Shots feel and function heavier; medium-rock choice differs from laser; projectiles obey range and cover.

**Basis:** Briefing p10. **State:** Planned; quality acceptance open.

## 6. Risk reward and build decisions

### 6.1 Pickups and reward legibility

**Needs:** Credit/repair/rare shield/temporary buff icon-silhouette and FX/audio family; risk-value placement and collection timing.

**Proposed owner:** Agent + UI/VFX artist. **Source strategy:** Custom identity icons; simple meshes sufficient.

**Acceptance predecessors:** 2.4;3.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Player identifies reward type without color alone and knowingly leaves safe line for value.

**Basis:** Scope 12,15. **State:** Planned; quality acceptance open.

### 6.2 Five I-V upgrade tracks and economy

**Needs:** Hull Shield Engine Thrusters Weapon; truthful previews, deliberate purchases, differentiated felt benefits and survival/risk income tuning.

**Proposed owner:** Agent + owner. **Source strategy:** Build internally; shared icon family.

**Acceptance predecessors:** 2.2;5.3;5.4;6.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Competent natural run supports about 2-3 meaningful station purchases; choice addresses an experienced problem.

**Basis:** Briefing p12. **State:** Planned; quality acceptance open.

### 6.3 Two utilities

**Needs:** Vector Thrusters and Overdrive Cooling effects, icons, clear acquisition/replacement/active feedback and saved identity.

**Proposed owner:** Agent + UI/VFX artist. **Source strategy:** No inventory or elaborate physical models.

**Acceptance predecessors:** 6.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Player can feel each benefit under pressure; no surprise utility pickups or duplicate purchase charges.

**Basis:** Briefing p12. **State:** Planned; quality acceptance open.

### 6.4 Salvage Cache event

**Needs:** Explicit offer/accept point, wreckage diversion, objectives, reward reveal/choice and expiry/failure communication.

**Proposed owner:** Agent encounter designer. **Source strategy:** Reuse wreckage and reward assets.

**Acceptance predecessors:** 3.4;6.1;6.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Approaching does not commit player; risk is understood and payout feels worthwhile.

**Basis:** Briefing p14. **State:** Planned; quality acceptance open.

### 6.5 Distress/combat event

**Needs:** Distinct distress marker/prop, accepted combat pressure, success/failure cues and higher-quality reward.

**Proposed owner:** Agent encounter designer. **Source strategy:** Reuse two enemies and signal prop.

**Acceptance predecessors:** 5.1;5.2;6.4. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Optional combat has understandable stakes and result without becoming a new game mode.

**Basis:** Briefing p14. **State:** Planned; quality acceptance open.

### 6.6 Mobile depot

**Needs:** Beacon-marked optional merchant stop with suspended gravity/magnetic mooring, aboard-ship service menu, subset upgrades/deals and clear lock/release cues; no landing pad or disembarkation..

**Proposed owner:** Agent + environment artist. **Source strategy:** Kitbash existing station/ship modules.

**Acceptance predecessors:** 6.2;6.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Exactly one depot appears; player deliberately approaches and opts into a suspended mooring, uses quick services while aboard, then releases into flight; passing does not commit the player..

**Basis:** Owner depot clarification 2026-09-13; Briefing p14. **State:** Planned; quality acceptance open.

### 6.7 Two contracts

**Needs:** One modifier and one objective contract; physical board, clear terms/penalties, progress and station settlement feedback.

**Proposed owner:** Agent + UI writer. **Source strategy:** Reuse terminal kit.

**Acceptance predecessors:** 6.2;8.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** One active contract; player understands extra pressure and actual reward/failure at next station.

**Basis:** Briefing pp12-14. **State:** Planned; quality acceptance open.

## 7. Character and player ships

### 7.1 Acornaut surface and topology

**Needs:** Audit AI source, preserve recognizable identity, retopology where deformation needs it, UV/bakes and separate fur/cloth/metal/glass response; optimized tail silhouette.

**Proposed owner:** Character artist + agent integration. **Source strategy:** High-priority specialist commission.

**Acceptance predecessors:** 1.2. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Approved reference comparison in real chase and station lighting; no metallic fur or silhouette damage from decimation.

**Basis:** Briefing p3; art/acornaut-full.jpg. **State:** Planned; quality acceptance open.

### 7.2 Rig and deformation

**Needs:** Stable export skeleton, skin weights, shoulders/hands/tail/face controls, collision/physics asset and LOD deformation; paired cockpit fit.

**Proposed owner:** Character rigger + agent. **Source strategy:** High-priority specialist commission.

**Acceptance predecessors:** 7.1;7.4. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Hands/feet/tail hold contact through extreme steering and transitions; editable source supplied.

**Basis:** Briefing pp3-4. **State:** Planned; quality acceptance open.

### 7.3 Animation and personality

**Needs:** Idle walk run turns stop interact pilot steering/lean reactions disembark/reboard; blending and event timing; restrained facial/tail motion.

**Proposed owner:** Animator + agent Animation Blueprint. **Source strategy:** Retarget base locomotion only if rig fits; polish custom pilot/exit.

**Acceptance predecessors:** 7.2;8.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Continuous in-game clip has no foot sliding, grasp failure, tail clipping or exit-to-walk pop.

**Basis:** Briefing pp3,6,13. **State:** Planned; quality acceptance open.

### 7.4 Starter acorn spacecraft

**Needs:** Approved silhouette, cockpit/canopy with visible pilot, hard-surface topology/UV/PBR, engine/muzzle anchors, landing/exit contacts, LODs and collision.

**Proposed owner:** Vehicle artist + agent. **Source strategy:** Specialist identity asset; refine existing source first.

**Acceptance predecessors:** 1.2. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Read as the reference in actual rear chase view; pilot fits, no faceting or route occlusion.

**Basis:** Briefing pp1,4,7; art/ship-hero.jpg. **State:** Planned; quality acceptance open.

### 7.5 Agile second spacecraft

**Needs:** Coherent but distinct agile lower-hull silhouette and handling; reuse agreed cockpit/sockets/material language where practical.

**Proposed owner:** Vehicle artist + agent. **Source strategy:** Commission derivative after starter acceptance.

**Acceptance predecessors:** 7.4;2.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Unlock feels like a different handling choice; equal-tier comparison proves tradeoff.

**Basis:** Briefing pp4,15; art/ship-interceptor.jpg. **State:** Planned; quality acceptance open.

## 8. Station and home hangar

### 8.1 Station layout and docking envelope

**Needs:** One compact hub archetype reused for both visits; bay/corridor geometry, manual entry/landing assistance, safe exit/boarding and walking camera clearance.

**Proposed owner:** Agent + environment artist. **Source strategy:** Layout internally before buying shell.

**Acceptance predecessors:** 1.2;2.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Approach and service route work at actual ship/character scale without teleport/test assistance.

**Basis:** Briefing pp13,16. **State:** Planned; quality acceptance open.

### 8.2 Station shell and materials

**Needs:** Modular deck/walls/ceiling/doors/window/trusses, lighting/material normalization, acorn identity decals, collision and streaming setup.

**Proposed owner:** Environment artist + agent. **Source strategy:** One coherent modular interior kit.

**Acceptance predecessors:** 8.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Compact industrial place matches reference material/scale/lighting and supports camera/navigation.

**Basis:** Briefing pp12-13; art/station.jpg. **State:** Planned; quality acceptance open.

### 8.3 Station services and interfaces

**Needs:** Repair console, five upgrades, contract board, vendor/utility access, save/quit and launch controls, clear prompts and navigation.

**Proposed owner:** Agent UI/gameplay + prop artist. **Source strategy:** Use kit console variants with custom screens.

**Acceptance predecessors:** 8.1;6.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** All services discovered and usable with both devices in a typical 1-3 minute visit.

**Basis:** Scope 17,43. **State:** Planned; quality acceptance open.

### 8.4 Station life and story

**Needs:** 1-2 NPC/vendor interactions, visible servicing arm/tool activity, ambient machinery/announcements, restrained flavor and one optional side reward.

**Proposed owner:** Environment/animation/audio specialists + agent. **Source strategy:** Kit machinery and licensed NPC base; custom identity dressing.

**Acceptance predecessors:** 8.2;8.3;7.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Hub feels occupied and offers decompression; optional interaction does not become exploration/combat.

**Basis:** Scope 43. **State:** Planned; quality acceptance open.

### 8.5 Home hangar and fast return

**Needs:** Reuse shell/material kit for home bay; ship selection, weapon/loadout point, progression/history/unlocks, launch and repeat shortcuts.

**Proposed owner:** Agent + environment artist. **Source strategy:** Reuse station investment.

**Acceptance predecessors:** 8.2;8.3;9.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Returning player can choose and relaunch quickly while first-time flow remains understandable.

**Basis:** Briefing pp6,15,18. **State:** Planned; quality acceptance open.

## 9. Player communication and progression

### 9.1 HUD and game shell

**Needs:** Moderate persistent HUD plus target/event/docking/subsystem cues, contextual radar; menu/continue/new/hangar/settings/stats/quit hierarchy.

**Proposed owner:** Agent + UI artist. **Source strategy:** Custom visual system and icon set.

**Acceptance predecessors:** 2.3;6.1. **Relative effort:** L.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Readable in dense scene across supported UI scales/resolutions; no disconnected overlay style.

**Basis:** Scope 27,44. **State:** Planned; quality acceptance open.

### 9.2 Tutorial and accessibility

**Needs:** Short controls introduction, learn in Waves1-3, reset/replay prompts, device glyphs, subtitles, non-color cues, shake/blur and relevant hold/toggle.

**Proposed owner:** Agent + owner/new tester. **Source strategy:** Build internally.

**Acceptance predecessors:** 2.2;9.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** New player can launch and use core maneuvers without developer coaching; device capabilities match.

**Basis:** Scope 32,44-45. **State:** Planned; quality acceptance open.

### 9.3 Death XP unlock and retry

**Needs:** Clear cause/result, highest wave, secondary score, death-only XP, weapon and ship unlock progress, reset and immediate return path.

**Proposed owner:** Agent + UI/audio designer. **Source strategy:** Build internally.

**Acceptance predecessors:** 6.2;7.5;9.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Natural death earns correct persistent progress; next run starts clean and presents a reason to try again.

**Basis:** Briefing pp15,18. **State:** Planned; quality acceptance open.

### 9.4 Local saves and Station2 boundary

**Needs:** Account/settings/suspension compatibility, consume-before-play/death behavior; clear services/save/discard at slice boundary without Wave11 or victory XP.

**Proposed owner:** Agent. **Source strategy:** Build internally.

**Acceptance predecessors:** 8.3;9.3. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Fresh-process save/resume/death verified; player understands slice boundary and no checkpoint exploit.

**Basis:** Scope 18,47; current implementation. **State:** Planned; quality acceptance open.

## 10. Audio VFX and visual cohesion

### 10.1 Flight combat and hazard soundscape

**Needs:** Engine idle/accel/boost/brake/dodge, pass-bys, impacts, shield, two weapons, hazard buildup and discharge; spatial priority and concurrency.

**Proposed owner:** Sound designer + agent. **Source strategy:** License raw SFX; commission distinctive mix.

**Acceptance predecessors:** 2.2;3.2;5.3;5.4. **Relative effort:** L.

**Start guidance:** Start G1 with benchmark engine/pass-by/impact sample; extend to weapons and full soundscape.

**Accept when:** Audio communicates mass, speed and danger direction without alarm fatigue in natural play.

**Basis:** Briefing p17; Scope 28. **State:** Planned; quality acceptance open.

### 10.2 Adaptive music and ambient life

**Needs:** Low-pressure bed/intensity layers/climax transitions; hangar/station decompression, UI rewards and occasional character reactions.

**Proposed owner:** Composer/sound designer + agent. **Source strategy:** Layered licensed score or small custom stem set.

**Acceptance predecessors:** 4.1;8.4;10.1. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Musical energy follows pressure without constant peaks, abrupt loops or masking warnings.

**Basis:** Scope 8,28-29. **State:** Planned; quality acceptance open.

### 10.3 Visual cohesion and VFX budget

**Needs:** Shared exposure/palette/roughness, readable thrusters/trails/hits, gradual region backdrops, per-effect screen coverage and quality tiers.

**Proposed owner:** Technical/VFX artist + agent. **Source strategy:** Reuse components; custom defining effects.

**Acceptance predecessors:** 3.5;3.6;7.4;8.2. **Relative effort:** L.

**Start guidance:** Start G1 with representative material/FX rules; extend as each hazard and station sample arrives.

**Accept when:** Flight and station look like one game; spectacle remains legible with shake/blur disabled.

**Basis:** Briefing p17; Scope 24,26. **State:** Planned; quality acceptance open.

## 11. Qualification and delivery

### 11.1 Natural-play QA and evidence

**Needs:** Small tester cohort, exact build/scenario/control record, clip/timestamps and cause/response/retry questions; separate automated versus human acceptance.

**Proposed owner:** Lead agent + owner/testers. **Source strategy:** Optional independent playtest help.

**Acceptance predecessors:** 4.3;8.4;9.2;9.4;10.2;10.3. **Relative effort:** L.

**Start guidance:** Start G0 baseline and G1 paired tests; repeat natural QA at every milestone.

**Accept when:** Two blocks, both stations, all roster and unlock/save/death cases exercised at normal settings; open defects retained.

**Basis:** IMPLEMENT validation gates. **State:** Planned; quality acceptance open.

### 11.2 Performance and optimization

**Needs:** Profile CPU/GPU/frame pacing/RAM/VRAM at representative dense moments and station transitions; LOD/material/overdraw/collision/load budget based on evidence.

**Proposed owner:** Agent + technical artist. **Source strategy:** Specialist profiling if measured bottleneck persists.

**Acceptance predecessors:** 3.2;8.2;10.3. **Relative effort:** L.

**Start guidance:** Start G1 baseline profile; repeat on each integrated content batch and qualify at G5.

**Accept when:** Representative PC meets 60FPS baseline; scalability retains simulation/control/readability first.

**Basis:** Scope 46. **State:** Planned; quality acceptance open.

### 11.3 Release and content provenance

**Needs:** Cook/package receipts, rights manifest, clean-PC prerequisite test, itch A-to-B update and save retention, known issues and manual release approval.

**Proposed owner:** Agent + owner publisher. **Source strategy:** Keep paid sources private; cooked builds for testers.

**Acceptance predecessors:** 11.1;11.2. **Relative effort:** M.

**Start guidance:** Start once required interfaces/reference decisions are stable; integrated acceptance requires listed predecessors.

**Accept when:** Selected candidate installs/updates and retains appropriate saves on tester PC; no raw licensed asset leak.

**Basis:** IMPLEMENT delivery; current itch workflow. **State:** Planned; quality acceptance open.
