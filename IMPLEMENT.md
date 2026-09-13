# SpaceSurvival — Phase 1 Codex Execution Order

This file is the execution contract for the first implementation pass.

The authoritative game design is [`docs/GAME_SCOPE.md`](docs/GAME_SCOPE.md). Read it in full before making implementation decisions. If this file and `docs/GAME_SCOPE.md` ever conflict, `docs/GAME_SCOPE.md` wins unless a later explicit owner decision says otherwise.

## Mission

Build a near-alpha-quality, 10-wave Windows PC vertical slice of SpaceSurvival in Unreal Engine 5 that is strong enough to become the actual foundation of the game.

The target is not a throwaway prototype. Core architecture, save state, progression, flight, Director logic, stations, events, hazards, enemies and content definitions should be structured for continued development.

Success means the complete loop is already compelling enough to make the player want to launch another run after dying.

## Non-negotiable constraints

- Unreal Engine 5.
- Windows PC first; Steam is the intended commercial destination, but do not add Steamworks in Phase 1.
- Single-player only in Phase 1. Do not implement networking.
- Hybrid Unreal architecture: durable systems in C++; tunable content in Blueprints/Data Assets.
- 10-wave vertical slice only.
- Every fifth wave is a guaranteed climax followed by a major station.
- Wave 5 climax: wormhole pull -> hostile combat -> station.
- Wave 10 climax: gravity anomaly + asteroid storm + enemy pressure -> station.
- One active weapon slot.
- Two Phase 1 weapon classes only: Rapid Laser and Heavy Cannon.
- Two enemy archetypes only: Pursuer and Flanker.
- Four hazard families only: Asteroids, Wreckage/Debris, Electrical Storm, Gravity Anomaly.
- Two utility modules only: Vector Thrusters and Overdrive Cooling.
- Two optional event types only: Salvage Cache and Distress/Combat.
- Two contract types only: one difficulty modifier and one objective contract.
- Exactly one guaranteed mobile depot encounter in the 10-wave slice.
- Five core upgrade tracks, each I-V: Hull, Shield, Engine, Thrusters, Weapon.
- Core upgrades are mainly purchased at stations/depots with credits, not granted randomly during hazards.
- Stations always provide all five core upgrade paths; mobile depots provide a random subset plus special variants/deals.
- Shield does not regenerate automatically; shield pickups are rare.
- Hull health can regenerate to 100%, quickly when out of danger and slowly under pressure.
- Directional dodge has no invulnerability frames.
- Station saves are suspend/resume only; death permanently ends the run.
- Phase 1 permanent progression is real: death awards XP and early account levels unlock the second starting weapon and a second ship.
- Second ship is faster/more agile and slightly less durable than the starter ship.
- Keyboard/mouse and controller are both first-class Phase 1 inputs.
- Target 60 FPS minimum gameplay baseline with scalable support for 120+ FPS on capable PCs.
- Phase 1 visual target is the approved Hybrid style: realistic materials/lighting and cinematic space, with deliberately readable hazards, pickups and combat silhouettes.

## Scope discipline

Codex has limited creative discretion.

You may:
- fill small implementation gaps;
- choose sound technical patterns;
- improve transitions, animation, VFX, audio and feedback;
- add minor polish necessary for coherence;
- tune parameters where the design specifies behavior but not exact values.

You may not silently:
- redesign the core loop;
- change the five-wave station cadence;
- add major mechanics;
- expand the enemy, hazard, event, weapon or utility roster beyond Phase 1;
- replace the progression philosophy;
- add multiplayer, Steamworks, cloud services, faction reputation, deep inventory, challenge modes or post-Wave-10 authored content.

If a design requirement is technically problematic, implement the closest architecture-compatible version and document the deviation and reason.

## Implementation sequence

### 0. Repository and project bootstrap

Before gameplay work:

1. Read `docs/GAME_SCOPE.md` completely.
2. Inspect all existing repository content and issues for additional context.
3. Create the Unreal Engine 5 project structure if not already present.
4. Establish a clean C++ module and content-folder layout.
5. Set up source control-friendly Unreal project settings.
6. Add initial build/run documentation.
7. Create `docs/PROJECT_STATE.md` and keep it current during implementation.

Do not begin by mass-generating content. Establish the architecture first.

### 1. Core flight vertical slice

Implement and tune the player spacecraft before building the Director around it.

Required controls:
- pitch/yaw;
- banking;
- throttle;
- rechargeable boost;
- partial brake with heat/overheat behavior;
- directional dodge without invulnerability;
- arcade-responsive handling with visible inertia and spacecraft weight.

Camera:
- tight chase camera by default;
- only limited contextual pullback/widening at high speed or extreme density.

Validate both keyboard/mouse and controller before proceeding.

### 2. Survival and damage foundation

Implement:
- Hull health;
- non-regenerating Shield meter;
- hull regeneration behavior;
- damage scaling hooks by wave;
- kinetic/energy/electrical/gravity/thermal secondary behaviors where applicable;
- rare subsystem critical-damage framework;
- collision feedback that is mostly damage-focused, with stronger disruption when impacts become severe.

Build these as reusable systems, not hazard-specific hacks.

### 3. Wave state + Survival Director

Implement the wave system and pressure-budget Director.

Director responsibilities:
- wave timing hidden from the player;
- variable duration, generally trending longer deeper in the run;
- short variable breathing windows, never more than about 20 seconds outside stations;
- wave-based pressure budgets;
- progressive expansion of available hazard/enemy/event combinations;
- lightweight fairness constraints that block unavoidable or unreadable states;
- ability for selected hazards to persist across wave boundaries;
- fifth-wave climax routing.

The player should experience one continuous flight, not isolated level resets.

### 4. Phase 1 environmental systems

Implement exactly four hazard families:

1. Asteroids
   - multiple sizes;
   - small debris destructible;
   - medium asteroids destructible with controlled fragmentation;
   - massive bodies treated as navigation obstacles;
   - destroyed medium bodies may reveal useful drops or create additional debris.

2. Wreckage/Debris
   - large readable debris;
   - traversal pressure;
   - destructible and non-destructible elements;
   - authored chunks blended into procedural space.

3. Electrical Storm
   - visual/weather pressure;
   - electrical secondary effects;
   - readability/fair-warning rules.

4. Gravity Anomaly
   - physically influences ship movement and debris;
   - remains controllable rather than arbitrary.

### 5. Combat and enemies

Implement manual aim + soft-lock assistance.

Weapons:
- Rapid Laser;
- Heavy Cannon.

One active weapon slot only.

Enemies:
- Pursuer;
- Flanker.

Enemy difficulty should scale mainly through behavior, speed, composition, accuracy and pressure rather than bullet-sponge health inflation.

Enemies must interact with environmental hazards where practical rather than being immune scenery actors.

### 6. Pickups, credits and economy

Implement:
- Credits;
- repair pickups;
- rare shield pickups;
- temporary buffs;
- readable arcade-first pickup presentation;
- value/risk-aware spawn placement.

Credits come from both survival and active play.

Tune Phase 1 so a competent run usually supports approximately 2-3 meaningful purchases per station.

### 7. Core run upgrades

Implement Hull, Shield, Engine, Thrusters and Weapon tiers I-V.

Core upgrades:
- purchased deliberately;
- always available at major stations;
- predictable baseline pricing;
- soft capability pressure only, never hard hidden wave gates.

### 8. Utilities and special rewards

Implement exactly:
- Vector Thrusters;
- Overdrive Cooling.

Utilities are deliberate rewards from events/depots/stations and are not surprise active-hazard pickups.

Do not build a general inventory system.

### 9. Optional events

Implement exactly two optional event types:

- Salvage Cache Event;
- Distress/Combat Event.

Events:
- are clearly announced;
- require explicit acceptance;
- may appear during lighter moments early and overlap active pressure later;
- can award utilities or rare weapon replacements.

### 10. Mobile depot

Implement exactly one guaranteed mobile depot encounter somewhere in the 10-wave Phase 1 path.

It should:
- be encountered seamlessly in flight;
- offer a random subset of core upgrades;
- support special variants/deals;
- not duplicate the full-service station experience.

Keep the system data-driven so the guarantee can later be replaced with randomized appearance logic.

### 11. Wave 5 authored climax

Build the first major authored sequence:

Normal survival -> wormhole disturbance -> increasing pull -> seamless transition through wormhole -> hostile combat survival -> station detected -> player-controlled approach -> assisted final docking.

This is the first major quality benchmark. It should feel like part of the same continuous run rather than a separate minigame.

### 12. Major station

Create a compact lived-in 3D station hub.

Required:
- player-controlled approach;
- assisted final landing;
- Acornaut exits ship;
- simplified third-person walk/run/interact controls;
- diegetic repair console;
- diegetic core-upgrade terminals or stations;
- contract board;
- Save & Quit terminal;
- launch interaction;
- 1-2 NPC/vendor interactions;
- visible ship servicing;
- machinery/ambient activity;
- announcements/audio;
- small environmental-storytelling detail;
- one minor optional interaction/reward point.

A normal station visit should take roughly 1-3 minutes, not become a secondary exploration game.

### 13. Contracts

Implement exactly:
- one difficulty-modifier contract;
- one objective contract.

Phase 1 supports one active contract at a time.

Standard contract failure may simply remove the reward. Any contract with a penalty must disclose it before acceptance.

### 14. Save/resume

Implement local-first save domains for:
- account progression;
- settings/input;
- suspended run state.

Station Save & Quit must resume the active run correctly.

Death after resuming must permanently end that run; do not allow checkpoint reload after death.

### 15. Permanent progression + hangar

Implement real account XP.

On death:
1. end the run;
2. calculate XP and score;
3. update account level;
4. display progression/unlocks;
5. return player to the home hangar.

Early progression must prove:
- second starting weapon unlock;
- second ship unlock.

Second ship:
- higher base speed;
- better maneuvering;
- quicker response;
- slightly lower starting hull;
- distinct playstyle, not an objectively dominant late-run ship.

Hangar:
- compact third-person space;
- ship selection at ship bay;
- weapon selection at rack/loadout point;
- progression/unlocks at terminal;
- launch at ship;
- permit repeat-player shortcuts where useful.

### 16. Waves 6-10 escalation

Use the same systems, but increase Director intensity and combination complexity.

Do not add new Phase 1 hazard or enemy families merely to make the second block different.

Prove variety through composition, timing, intensity and progression.

### 17. Wave 10 compound climax

Wave 10 must stress-test system interaction using:

- Gravity Anomaly;
- Asteroid Storm;
- Enemy Pressure.

The resulting encounter must be difficult, chaotic and readable.

Completion transitions to Station 2.

### 18. Game shell and settings

Build a proper near-alpha PC shell:

- Continue Suspended Run;
- New Run;
- Hangar;
- Settings;
- Graphics;
- Audio;
- keyboard/controller controls;
- Run Stats / Progression;
- Quit.

Basic accessibility:
- subtitles;
- UI scaling;
- critical warnings/pickups distinguishable without color alone;
- camera-shake toggle;
- motion-blur toggle;
- hold/toggle behavior where relevant.

### 19. Presentation pass

Do not leave the game as a gray-box prototype.

Target the approved Hybrid visual direction:
- realistic materials and lighting;
- cinematic space;
- highly readable hazards/pickups/enemies;
- polished HUD;
- strong VFX;
- strong audio feedback;
- adaptive layered music;
- Acornaut visibly piloting the ship.

If supplied, use the existing rigged Acornaut source asset as the visual starting point rather than unnecessarily recreating the character.

Custom hero identity elements should be prioritized. Curated high-quality external assets may be used for secondary environmental dressing if licensing permits and the result is visually unified.

### 20. Performance and polish

Before declaring implementation complete:
- profile CPU/GPU/frame time;
- validate 60 FPS minimum target on the available representative PC configuration;
- preserve simulation and readability before VFX density;
- remove avoidable hitches during wave transitions, spawning, docking and station transitions;
- verify frame-rate-independent flight/input behavior;
- fix obvious collision/spawn/readability issues;
- remove debug UI and broken placeholders from normal play.

## Architecture expectations

Prefer data-driven definitions for content and tuning.

At minimum, keep clean boundaries between:
- Player/Ship;
- Flight;
- Damage/Defense;
- Weapons;
- Enemy AI;
- Survival Director;
- Wave State;
- Hazard Definitions;
- Encounter Definitions;
- Economy;
- Upgrades;
- Utilities;
- Events;
- Contracts;
- Stations/Depots;
- Account Progression;
- Run State;
- Save System;
- UI/HUD;
- Audio/VFX hooks.

Avoid giant monolithic actors or Blueprints that own unrelated systems.

Do not hardcode Phase 1 content in ways that force future Phase 2 additions to rewrite the architecture.

## Required validation gates

Do not report Phase 1 complete until all applicable gates pass.

### Build gate
- Unreal project opens cleanly.
- C++ project compiles cleanly.
- required maps/assets resolve.
- packaged Windows build succeeds.

### Flight gate
- keyboard/mouse works;
- controller works;
- boost works;
- brake/overheat works;
- dodge works;
- camera remains readable under high speed.

### Survival gate
- Waves 1-10 complete in order;
- hidden-duration waves transition correctly;
- breathing windows remain bounded;
- Director pressure escalates;
- no routine unavoidable spawn states found during validation.

### Content gate
- four hazard families work;
- two enemy archetypes work;
- two weapon classes work;
- two utilities work;
- two optional events work;
- one mobile depot works;
- two contract types work.

### Climax gate
- Wave 5 wormhole/combat/station sequence works;
- Wave 10 compound climax works;
- both lead cleanly into stations.

### Station gate
- landing works;
- Acornaut exits correctly;
- all five core upgrade paths work;
- repair works;
- contract board works;
- Save & Quit works;
- relaunch works.

### Progression gate
- death ends run;
- run score calculated;
- XP awarded;
- account progression persists;
- second starting weapon unlocks;
- second ship unlocks;
- new run reflects unlock state while run-specific upgrades reset.

### Save gate
- suspended run saves at station;
- application can close/relaunch;
- run resumes correctly;
- death after resume cannot reload the consumed run as a checkpoint.

### Performance gate
- performance measured;
- target is 60 FPS minimum baseline;
- major bottlenecks documented;
- scalability path exists for 120+ FPS capable systems.

## Required automated tests where practical

Add automated/unit/functional coverage where Unreal supports it cleanly for high-risk deterministic systems such as:
- upgrade tier application;
- damage routing Shield -> Hull;
- regeneration rules;
- wave progression state;
- fifth-wave climax routing;
- XP/unlock progression;
- save serialization/deserialization;
- contract success/failure;
- utility behavior;
- run reset behavior.

Do not substitute automated tests for manual gameplay validation of flight feel, Director fairness, visual readability or station flow.

## Required documentation before completion

Create/update:

### `docs/PROJECT_STATE.md`
Current implementation state, working systems, active limitations and exact Phase 1 completion status.

### `docs/ARCHITECTURE.md`
Major classes/subsystems, ownership boundaries, data flow, extension points and content authoring workflow.

### `docs/KNOWN_ISSUES.md`
Every known meaningful bug, compromise, incomplete polish item or performance concern.

### `docs/PHASE2_INTEGRATION.md`
Explain how the architecture supports later additions described in `docs/GAME_SCOPE.md`, including additional hazards, enemies, weapons, utilities, events, challenge modes, inventory, Steam/cloud features and eventual co-op.

Do not implement these deferred systems merely to demonstrate the extension point.

## Delivery requirements

Return all of the following:

1. Complete Unreal Engine source project.
2. Packaged Windows build.
3. Clean implementation branch and PR against the intended base branch.
4. Build/run instructions.
5. `docs/PROJECT_STATE.md`.
6. `docs/ARCHITECTURE.md`.
7. `docs/KNOWN_ISSUES.md`.
8. `docs/PHASE2_INTEGRATION.md`.
9. Test/validation record covering the gates above.
10. Performance findings against the 60 FPS baseline.

## Completion rule

Do not say "complete" because the requested files or systems merely exist.

Phase 1 is complete only when the integrated 10-wave loop has been built, packaged and validated end-to-end against this document and `docs/GAME_SCOPE.md`.

If anything in the required delivery cannot be achieved, report the implementation as **PARTIAL**, state exactly which acceptance gates remain open, and continue prioritizing closure of those gates over new features.

## Final quality question

Before final delivery, evaluate the build as a player rather than only as its implementer:

**After dying, is there a credible urge to launch another run immediately?**

If not, prioritize flight feel, pacing, reward cadence, progression feedback, hazard readability and Director composition before adding anything outside Phase 1.
