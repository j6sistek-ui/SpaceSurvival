# SpaceSurvival: Phase 1 quality recovery plan

**Planning proposal - 2026-09-13. No gameplay changes, purchases, contractor engagements or new releases are authorized by this document alone.**

The next milestone should prove an exciting short stretch of SpaceSurvival in its intended chase view. We should then extend that quality through the first five-wave loop and finally the complete ten-wave slice. Increasing asset count before that proof risks producing a more expensive version of the same flat experience.

The owner reports that the game feels generic and stale and that the current graphics are below expectation. Existing implementation and regression coverage are useful foundations, but the intended excitement has not been accepted. This plan preserves the architecture where it works and puts player experience ahead of feature-count completion.

## Start here

- [Whole-project solution catalog](SOLUTION_CATALOG.md): current resource/candidate register across all 47 work packages, including useful later options. This quality plan's September 13 baseline remains historical; use the catalog and project state for later resource/integration evidence.

- [Owner playtest findings](OWNER_FEEDBACK.md): entry-level handling baseline and unresolved event, contract, station and combat clarity reports.

- [47 work packages](WORK_PACKAGES.md): each element's needs, proposed owner, source strategy, dependencies and acceptance.
- [CSV work register](WORK_PACKAGES.csv): the same packages for importing into a task board or spreadsheet.
- [Asset sourcing and outsourcing briefs](SOURCING.md): what to buy, commission, reuse and integrate internally.
- [Owner briefing](../../artifacts/SpaceSurvival-Briefing.pdf) and [asteroid reference](../../art/asteroids.jpg).

The recommended split is: **owner directs and playtests; lead agent owns systems and integration; specialists produce the hardest identity art/animation and distinctive audio; curated kits supply secondary environments.** Buying models reduces production labor, but does not supply encounter design, feel, coherent lighting or integration.

## Baseline and source authority

This plan is based on the implementation branch at `d5533027a979d73420a7b99dad6b1c3dd9a82e96` and the owner reference upload on main at `1116715`. These are separate branches; this documentation PR does not merge implementation PR3. Current gameplay binary remains Package14/source `f4bfec8`, distributed as itch `0.1.14-alpha`.

The complete 18-page raster PDF was visually inspected; text extraction returned no text. The supplied download and repository PDF have identical SHA256 `6ab43fd115cb563c9f61490e09e881c6e89998aa22200d1b7bfcd46180d9257d`. Page9's bottom hazard cards are clipped in the source page; the written scope supplies the electrical/gravity requirements. The `art/asteroids.jpg` and `art/station.jpg` originals were also inspected. Other named art files support the same presentation direction visible throughout the briefing; the uploaded `art/hero.mp4` is indexed but has not been motion-reviewed in this planning pass. No fresh gameplay or listening session was performed today.

[GAME_SCOPE](../GAME_SCOPE.md) is authoritative and [IMPLEMENT](../../IMPLEMENT.md) supplies the execution contract. The briefing is the owner's expectation reference. The following are **paraphrases and proposed production translations**, not replacements for those documents:

| Reference | Expectation to carry into production | Guard against accidental scope change |
| --- | --- | --- |
| PDF1,7-9; asteroids art | Ship surrounded by convincing large/small rocky forms, close lateral passes, deep field and strong forward motion | Do not convert a still image's rock count into simultaneous collision count; preserve reachable reaction space |
| PDF3-4; hero/ship art | Recognizable Acornaut, believable suit/materials, visible piloting and dominant acorn craft | Current AI model is a starting point, not presumed production-ready; approve cockpit/character scale together |
| PDF8,16 | Unpredictable combinations and memorable continuous climaxes | No separate arena mode, unlimited elite roster or new hazard families |
| PDF12-14; station art | Compact industrial station, readable physical service points, NPC/machinery life | Concept board entries are illustrative; no escort/supply mission library or new faction systems |
| PDF15,18 | Desire for another attempt; purchases and unlocks that change choices | Keep death-ended runs, death XP, soft upgrade pressure and distinct lower-hull agile ship |
| PDF9 HUD artwork | Readable information around intense space action | Fuel, chaingun/ammunition/reload, sector labels and jump-gate objective in generated art do not authorize those mechanics |

The reference station includes ship-servicing staging, while flight art varies in pilot visibility. Freeze one approved flight framing and one docked alignment scene before commissioning final assets. Concept pictures can show different poses; artists should not infer a new ship flight mode or vertical-landing mechanic.

## What is known versus what needs diagnosis

Known from repository records: integrated flight/Director/damage/economy/station/save systems; two weapons/enemies; four hazard families; packaged Windows release; 38 Package14 Unreal tests passed. These bounded tests are not proof of natural balance, input comfort, final visuals, rendered sound or replay appeal. The current owner rejection is a quality finding, even where code functions.

Likely contributors to the flat experience are **hypotheses to test**, not a new runtime audit:

| Hypothesis | Cheap discriminating test | Work packages |
| --- | --- | --- |
| Apparent speed and depth are weak | Same flight values with a controlled near/mid/far field and stronger directional pass-by sound | 2.3,3.2,10.1 |
| Hazards create little decision pressure | Compare authored encounter compositions at equal overall pressure; log maneuver choices and damage causes | 1.3,3.2,4.1 |
| Movement verbs feel interchangeable | Ask player to use boost, brake and dodge to solve distinct situations; compare novice versus familiar input | 2.1-2.2 |
| Shooting/hits lack consequence | Compare laser/cannon response with representative muzzle, hit, breakup and audio timing | 2.4,3.3,5.3-5.4 |
| Builds do not create anticipation | Naturally earn first station purchases, ask what pressure motivated each choice, then replay with that upgrade | 6.2,9.3 |
| Constant activity lacks contrast | Review quiet-to-warning-to-threat-to-recovery rhythm over an actual block | 4.1,10.2 |

No exact cause is declared until the comparison produces evidence. A polished screenshot alone cannot close any of these tests.

## Work breakdown tree

```text
0  Accepted Phase 1 ten-wave experience
   1  Direction and shared contracts
      1.1 reference benchmark   1.2 asset/interface contract   1.3 tuning evidence
   2  Flight and survival feel
      2.1 input/authority   2.2 boost/brake/dodge   2.3 chase view   2.4 damage/recovery
   3  Hazards and space traversal
      3.1 rock assets   3.2 field compositions   3.3 breakup
      3.4 wreckage   3.5 electrical storm   3.6 gravity
   4  Director and run pacing
      4.1 variety/relief   4.2 Wave5   4.3 Waves6-10/compound climax
   5  Combat
      5.1 pursuer   5.2 flanker   5.3 rapid laser   5.4 heavy cannon
   6  Risk/reward and build decisions
      6.1 pickups   6.2 five upgrade tracks   6.3 utilities
      6.4 salvage   6.5 distress   6.6 depot   6.7 contracts
   7  Acornaut and ships
      7.1 surface/topology   7.2 rig   7.3 animation   7.4 starter   7.5 agile ship
   8  Station and hangar
      8.1 layout/dock   8.2 shell   8.3 services   8.4 life   8.5 home hangar
   9  Player communication
      9.1 HUD/shell   9.2 tutorial/accessibility   9.3 death/unlocks   9.4 saves/boundary
  10  Sound and visual coherence
      10.1 soundscape   10.2 adaptive score   10.3 materials/VFX/regions
  11  Qualification
      11.1 natural QA   11.2 performance   11.3 clean-PC/update/release/rights
```

This is a deliverable tree, not a claim that each branch can finish independently. For example, station geometry depends on docking and camera clearance; finished pilot animation depends on ship contacts; Director density depends on control authority and visibility.

## Milestones and sequencing

| Gate | Integrated deliverable | Work allowed in parallel | Exit decision |
| --- | --- | --- | --- |
| G0: shared target | Annotated reference, current comparison clip, agreed framing/scale and normal-run test protocol | Asset audit, marketplace shortlist, specialist sample briefs | Owner agrees what closer-to-target means; no bulk buying |
| G1: feel benchmark | Proposed 60-90 second representative flight/asteroid sequence with real maneuver, damage, reward and sound feedback; testing fixture inside current systems, not a new game mode | One rock family, proxy-to-final ship fit, small sound pass; character production sample after dimensions agreed | Owner wants another attempt and can identify decisions, hit causes and usable escape choices on both devices |
| G2: first complete block | Natural Waves1-5, meaningful purchases, optional diversion, wormhole/combat, manual docking and purposeful Station1 | Character/ship production, station kit assembly, UI/music work against frozen contracts | Pacing and 2-3 purchase economy work without test cheats; station visit roughly 1-3 minutes |
| G3: coherent production content | Accepted hero pair, character movement, normalized station/hazard art, readable HUD and audio mix | Agents integrate bounded deliveries; specialists revise from in-game evidence | Real gameplay capture resembles references in material/scale/energy while preserving readability |
| G4: full ten-wave quality | Stronger second block, compound climax, Station2 boundary, natural death/XP/unlocks/retry and save flow | Performance and regression QA throughout | Gameplay, station, progression and save gates have evidence; release/performance qualification closes at G5 and unresolved owner acceptance remains explicit |
| G5: tester qualification | Clean-PC install, actual itch update from A to B, settings/account/suspension checks, representative performance | Release notes and focused tester cohort | Owner selects release; no automatic push from an art delivery or commit |

G3 art work can begin during G1/G2 once its own contracts are stable; the entire art team should not wait for all gameplay to be final. Conversely, G1 must contain representative audio and visual cues because they influence the apparent mechanics. Avoid both an all-graybox phase and a broad beautification phase with no player checkpoint.

**Critical path:** flight authority + camera envelope -> fair/intense asteroid benchmark -> varied Director block + reward choices -> Wave5/station -> coherent full ten-wave candidate -> player and release qualification. Character/ship dimensions and station docking layout feed that path early; final decoration does not need to block every code task.

## Asteroid intensity acceptance card

Reference: [asteroids](../../art/asteroids.jpg), PDF7-9. Proposed test conditions must be logged: build, ship/tier, weapon, sensitivity/inversion, resolution, UI scale, frame cap and audio device. Use normal health and normal-time flight for acceptance; any controlled fixture is labeled separately.

1. Near field: large readable silhouettes cross peripheral view and communicate close passage; collision shape agrees with perceived surface.
2. Decision field: a player can choose a route, see it early enough and execute it using actual ship authority. Tune speed, spacing and overlap together; a minimum distance alone cannot ensure fairness.
3. Far field: cheaper distant instances/particles provide density and parallax. Non-colliding decoration stays outside reachable decision space and never impersonates a nearby solid hazard.
4. Threat rhythm: approach, commitment, consequence, brief recovery. Do not hold maximum clutter throughout the wave.
5. Feedback: pass-by direction, engine effort, bank, restrained boost trail, hit/shield/breakup and reward response connect to real state. No near-miss scoring feature is implied.
6. Fairness evidence: review damage clips for initial visibility, reaction time, occupied escape volume, chosen input and competing warnings. Record rejected Director spawns and the cause, not just total actor count.
7. Player evidence: proposed short paired sessions ask control confidence, intensity, fairness, visual clarity and desire to repeat on a 1-5 scale plus one sentence. Compare to the same player's baseline; scores are discussion aids, not a statistical completion claim.
8. Performance: capture frame times and hitches in the same sequence. Establish the minimum test PC with the owner; the development RTX5080 is not assumed representative of tester hardware. Scale effects first, not input or collision fidelity.

If G1 remains dull, revise composition, cue timing and consequence before commissioning a larger asteroid library. If exciting but unreadable, reduce overlapping demands and masking effects rather than removing control or weakening collision rules silently.

## Parallel workflows and ownership

| Lane | Can own | Must hand back to lead | Good bounded assignment |
| --- | --- | --- | --- |
| Gameplay agent | Flight/device tuning, Director rules/chunks, enemy behavior, economy, test instrumentation | Rule/tuning diffs and deterministic regression evidence | One input defect or one encounter composition with before/after clip |
| Technical art agent | Asset audits, import automation, material normalization, collision/LOD diagnostics, profiling, sockets/Blueprint hookups | Asset manifest, performance/readability evidence and known compromises | Integrate an approved rock kit into three scale roles |
| Character/vehicle specialist | Production topology, UVs/bakes, rig/weights, animation polish, cockpit pair | Editable source, export presets, alignment scene and in-engine sample | Acornaut plus pilot contact/exit sample before complete animation set |
| Environment specialist | Cohesive modular station, purposeful lighting, props/servicing staging | Cookable content and collision/layout compliance | Finish one service corner in the approved hub footprint |
| Sound/VFX specialist | Distinctive engine/weapon/hazard sounds, layered score, signature effects | Dry/stem source, trigger map, concurrency/performance settings | Score and sound the G1 benchmark, with warning audibility review |
| QA agent/tester | Reproduction, coverage, natural input runs, performance and update checks | Source/build-bound findings; never self-approve owner feel | One normal first block or one install/update save-retention case |
| Owner | Vision, budget, priority and player acceptance | Short concrete feedback and accept/revise decision | One focused comparison, then lead schedules the resulting work |

Use one task owner per work package and one lead integrator. Up to three bounded specialist lanes can work alongside lead integration; more simultaneous agents do not help when they compete for the same Editor/GPU or change shared classes. Separate branches or isolated content folders, declared ownership and short handoffs avoid overwriting binary assets. One integration queue owns shared gameplay APIs and final builds. No specialist reinterprets the Director or progression to make their demonstration look better.

Agent capability is strongest for repeatable systems, tooling, integration and verifiable diagnosis. I can attempt cleanup, procedural content and presentation, but should not promise that repeated generation will reliably replace a skilled character animator, hard-surface artist or sound designer. Human playtest judgment remains necessary even when all implementation work is internal.

## Spend decisions and workload realism

There is no approved cash budget, contractor availability or reliable calendar estimate yet. The S/M/L labels in the register are relative complexity only; do not sum them into days or assign a percentage complete. Obtain comparable quotes only after a small accepted sample demonstrates the pipeline.

| Resourcing option | What it buys | Tradeoff |
| --- | --- | --- |
| Mostly internal | Agent systems/integration, existing assets, one curated environment/rock source; owner playtests | Lowest external spend, highest risk of repeated art/animation iteration |
| Recommended targeted specialists | Character rig/animation and hero ship pair; one station kit; focused sound pass | Buys the labor most difficult to automate while retaining one gameplay owner |
| Broader art support | Add environment assembly/lighting and dedicated VFX/composer after G1 | Faster parallel polish only if contracts, budget and review capacity are established |

First sourcing priorities: (1) reusable asteroid surfaces/silhouettes and representative sound for G1; (2) character/ship alignment sample; (3) one station interior kit after layout; (4) full character/ship production and signature audio; (5) extra dressing only if a measured gap remains. A model commission is not necessarily the earliest critical-path job, even when it is the largest art cost.

## Scope guard and completion tracking

Retain four hazard families, Pursuer/Flanker, Rapid Laser/Heavy Cannon with one active slot, two named utilities/events/contracts, one active contract, exactly one depot, five I-V purchased tracks, two ships, one station archetype visited twice, compact home hangar, local save domains and both input devices. Full-game infinite survival does not authorize Wave11 in this slice. Station2 presentation must respect current services/save/discard and death-only XP behavior.

Do not add multiplayer, Steamworks, cloud/leaderboards, reputation, inventory, bosses, additional hazard/enemy/weapon rosters, extra station archetypes or a campaign. Camera/feedback polish must not introduce a separate flight mode, invulnerable dodge or indefinite braking. Region art does not become a biome rules system.

For each work package record four separate outcomes: **implemented; integrated in current build; technically verified; owner quality accepted**. Attach commit/build, normal versus assisted conditions, device, clip/log and known limits. An asset import is not art acceptance; an automated test is not a fun test. On completion, reconcile every applicable IMPLEMENT gate, not merely this WBS checklist.

## Owner workload when work resumes

First session: review one short baseline/reference comparison and choose the biggest feel gap. Lead proposes a small change, builds it and gives one paired test. Owner reports where control felt wrong, what caused a hit, whether a purchase felt useful and whether they wanted another attempt. The lead translates that into tasks; the owner does not need to coordinate modelers, debug imports or manage ten simultaneous technical checklists.

No playtest is requested today. The immediate deliverable is this plan and its reviewable task/asset briefs.
