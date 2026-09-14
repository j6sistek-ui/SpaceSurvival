# Asset needs, procurement and specialist briefs

**Proposal, 2026-09-13. Nothing purchased, commissioned, licensed or imported by this planning task.** Read [quality plan](QUALITY_PLAN.md) and [work packages](WORK_PACKAGES.md). The following counts are proposed production quantities, not additions to the gameplay roster.

## Current catalog

The [whole-project solution catalog](SOLUTION_CATALOG.md) is the current register for owned resources, assessed candidates, wishlist leads, unmet needs and useful later options. Its whole-game value/timing assessments supersede narrower immediate-task rankings below. The dated production quantities, candidate screening and procurement/outsourcing briefs here remain planning references; they do not establish current acquisition or acceptance.

## Asset bill of needs

| Element / WBS | Minimum useful delivery | Reuse / buy / custom | What still needs integration |
| --- | --- | --- | --- |
| Acornaut / 7.1-7.3 | One accepted hero with editable sculpt/mesh, deformation topology, UVs/bakes, fur/cloth/metal/glass separation, rig/weights, LODs, physics asset and continuous animation set | Refine supplied AI source; specialist cleanup/rig/animation preferred | Pilot grip/seat/tail clearance, capsule/camera fit, Animation Blueprint, transitions, event hooks and lighting |
| Starter ship / 7.4 | One identity craft, cockpit/canopy, pilot-visible rear silhouette, landing/exit contact points, muzzle/engine anchors, textured runtime mesh and LOD/collision | Custom/refine existing; do not replace identity with generic fighter pack | Flight/camera envelope, seat and controls, hardpoints, exhaust/shield/damage FX, boarding timing |
| Agile ship / 7.5 | One coherent lower-hull agile alternative using shared production conventions | Derivative commission after starter fit approval | Actual handling tradeoff, same weapon interface, unlock presentation and pilot fit |
| Weapons / 5.3-5.4 | Two readable emitter/mount designs if visible; projectile/muzzle/impact VFX and sound families | Custom attachments or reuse ship sections; avoid unnecessary handheld models | Fire rhythm, aim/soft target, cover/range, impact timing, tiers and hit feedback |
| Two enemy craft / 5.1-5.2 | Two distinguishable silhouettes, engine/muzzle sockets, damaged/death presentation, LODs and simple collision | One compatible licensed family or small custom pair | Pursuit/flank behavior, attack cues, environmental collisions, offscreen warnings and difficulty composition |
| Asteroids / 3.1-3.3 | Proposed starter library: 6-10 reusable profiles spread across small/medium/massive roles, 2-3 surface variations, medium fracture interiors/fragments, LOD/collision; sample three roles first | Highest-value early environment buy; quantity tested before expanding | Encounter arrangements, safe reaction volume, destructibility, bounded fragmentation, drops and far-field instances |
| Wreckage / 3.4 | Proposed 6-10 reusable beams/panels/hull pieces and 2-3 authored passage arrangements | Reuse station kit material language; only buy extra pack if missing broken silhouettes | Walk/flight collision differs; traversable gaps, destructible classification, salvage route/clearance and fading/culling |
| Storm/gravity/wormhole / 3.5-3.6,4.2 | Three signature presentations: electrical buildup/discharge, directional gravity distortion/debris motion, wormhole transit; low-cost quality variants | Niagara specialist or agent with authored examples; reusable effects can seed work | Authoritative damage/force timeline, warning lead time, camera readability and bounded screen coverage |
| Pickups/utilities / 6.1,6.3 | Cohesive credit/repair/shield/buff icons and silhouettes, two utility icons, reward sound/FX; optional simple module props only where useful | Custom identity set; simple geometry adequate | Risk-value placement, collection, feedback, full-slot/replacement rules and UI consistency |
| Station shell / 8.1-8.2 | One compact reusable hub: bay/corridor/deck/walls/ceiling/door/window/truss kit, materials, trim sheets, lighting and identity decals | One coherent modular interior pack, normalized | Actual ship dock footprint, camera clearance, boundaries, services route, load/performance and safe exit |
| Station services / 8.3 | Repair, five upgrade access points or grouped terminal, contract board, save/quit, vendor/utility and launch; reusable console bodies with custom screens | Kit consoles plus custom readable displays | Existing service transactions and input focus; no generic menu replacing the hub |
| Station life / 8.4 | 1-2 NPC/vendor interactions, servicing arm/tool activity, machinery loops, announcements, one story detail and one side reward | Licensed NPC base and compatible prop kit; commissioned/retargeted short loops | Collision/navigation, timing and audio; no combat, platforming or branching narrative system |
| Home hangar / 8.5 | Distinct home dressing using station kit, ship bay, loadout/rack, progress/history point and launch | Reuse shell/materials; preserve small footprint | Selection/unlocks, repeat shortcut and first-time clarity |
| Depot / 6.6 | One recognizable beacon-marked merchant with a ship-sized suspended mooring zone and lock/release cues | Kitbash compatible station/ship modules | Exactly-once appearance, optional gravity/magnetic mooring, aboard-ship subset services/deals and quick departure |
| Optional events / 6.4-6.5 | Salvage marker/cache/objective props and distress beacon/wreck cue | Reuse wreckage/enemy/pickup library | Explicit acceptance, difficulty/reward disclosure, objective/expiry/result state |
| HUD/shell / 9.1-9.3 | Consistent typography, iconography, device glyphs, target/radar/warnings, menus, progression/unlock/result layouts | Custom identity; source fonts with suitable rights | Real data bindings, scale/resolution/focus, non-color differentiation, subtitles and tutorial flow |
| Space regions / 10.3 | Gradual background/light/color treatments from shared sky/nebula/lighting resources | Reuse existing sky plus compatible secondary resources | No strong biome rules, no wave-block lock, collision-free backdrop and readable foreground contrast |
| Audio/music / 10.1-10.2 | Engine and maneuver layers, pass-bys, kinetic/shield hits, laser/cannon, hazard cues, rewards, stations, UI, restrained reactions; adaptive music stems | License source library; sound designer/composer for final identity and mix | Trigger/state map, spatialization, warning priority, concurrency, loop crossfades and compression |
| Release / 11.3 | Source/runtime/provenance manifest, license record, reproducible import, performance report and packaged evidence | Agent-owned pipeline | Private licensed source handling, clean-PC dependency install and itch update/save test |

A five-tier upgrade tree does not require five completely different ship models. Initial tier differentiation can use honest handling/weapon effects and UI feedback. Extra cosmetic geometry is optional polish, not a new production obligation.

## Focused candidate shortlist

These are **screening candidates, not purchase recommendations**. Publisher listings were checked 2026-09-13. Exact current price, selected license tier, UE5.8 compatibility, downloaded contents and in-game performance have not been verified. Demo screenshots are not proof of integration quality.

| Candidate | Work it might remove | Fit assessment and remaining checks |
| --- | --- | --- |
| [Asteroids 1 - Makemake](https://www.fab.com/listings/104b0750-c90d-435e-8862-6217775174f6) | Listing describes 15 static asteroid meshes with four LOD levels and configurable materials | Promising first sample for 3.1; use barren rock direction first. Inspect close-pass silhouettes, collision, material cost, fracture compatibility and modern UE import; do not adopt its fog/particles indiscriminately |
| [Modular Space Hangar - Game Stuff Studio](https://www.fab.com/listings/aa78e50b-f1f9-4169-897c-3020ef3d14d0) | Listing describes 39 Blueprint components, walls/floors/ceilings, cargo crane, doors, props and decals | Strong functional shortlist for compact station/hangar reuse; inspect actual third-person walkthrough and fit to the industrial reference, then test pilot camera/bay dimensions. Does not supply Acornaut services or game logic |
| [Modular Space Station Kit - Pavel Inozemtsev](https://www.fab.com/listings/632e21ca-1e22-4ee2-bff6-dddb32ea7c36?lang=en) | Station structural sections, customizable materials, decals and examples | Exterior/station silhouette candidate for approach or depot. Confirm walkable interior coverage before considering it instead of the hangar kit; its listing attributes some planet/star textures separately |
| [Modular Space Station Pack - Brandon Westlake](https://www.fab.com/listings/1e752498-191a-4f64-9a56-fc709afdf1fd) | Listing describes 45 modules and two poseable armatures for a dish/robotic arm | Primarily a hard-science exterior alternative, not the strongest stylistic match for the pictured industrial interior. Listing says no baked animation and lists DCC/interchange formats; expect more Unreal setup. Lower priority |
| [Sci-Fi sounds - Gamemaster Audio](https://www.gamemasteraudio.com/product/sci-fi-sounds-and-sci-fi-weapons/) | Publisher describes 287 sci-fi effects spanning weapons, shields, UI and atmosphere | Audition a laser/cannon/impact/engine combination against the benchmark. A large library alone will not supply adaptive engine layers or a finished mix |
| [SCI-FI - BOOM Library](https://www.boomlibrary.com/sound-effects/sci-fi/) | Source material for engines, mechanisms, impacts and futuristic effects | Alternative sound-design source for a specialist, not an automatic second purchase. Check package edition, license/team access and usable loops/stems |

Do not buy both station candidates or both sound libraries by default. Shortlist one primary and one fallback per gap. VFX packs should be chosen after reading their Niagara setup and testing screen coverage; no random effect bundle is currently endorsed.

## Acquisition and integration gate

For each candidate complete one scorecard before purchase: reference/style fit, required component coverage, UE5.8/package compatibility, editable sources, LOD/collision, texture/material cost, rig/animation coverage where relevant, plugin dependencies, seller support, license and total integration effort. Mark unknowns rather than assuming marketplace approval guarantees these properties.

If a demo/source sample is legally available, test a single rock close pass or service corner before committing to the full kit. Otherwise require a detailed technical listing and budget an initial import/evaluation checkpoint; do not assume a refund will be available. The owner approves the actual purchase and license tier. No budget is inferred from the willingness to use Fab.

Then import into an isolated content area, preserve vendor originals, normalize units/materials/pivots, assign explicit collision roles, inspect shaders/LODs, validate cook references and capture frame time. Only accepted derivatives enter the integration build. A successful import is one step, not a finished work package.

**Repository boundary:** the gameplay repository has been public in current delivery context; verify visibility before adding licensed files. Fab's published Standard License summary permits sharing with project collaborators (including a private repository) and prohibits standalone redistribution. Keep purchased raw source assets in private project storage, with only license-safe manifests/import instructions in public code. Cooked game distribution and sharing editable source are different uses. Review the license actually attached to each item, including legacy/CC-BY/plugin terms. [Fab license summary](https://www.fab.com/eula), checked 2026-09-13.

Several listed items display “Allows usage with AI: No.” Do not feed acquired assets to generative tools without checking their actual applicable terms and permissions. Epic documents NoAI as a restriction on generative-AI data collection; it should not be treated as either a blanket permission or a blanket prohibition on every scripted import operation. Record provenance and use conventional DCC/Unreal processing where appropriate. [Epic licensing documentation](https://dev.epicgames.com/documentation/fab/licenses-and-pricing-in-fab), checked 2026-09-13.

No change to repository privacy, no paid asset sharing, and no legal agreement acceptance is part of this plan.

## Outsourcing packets that can be quoted

### A. Acornaut and cockpit fit: highest-priority specialist packet

**Brief:** turn the supplied first-pass AI character into a production-ready Hybrid hero while preserving its recognizable identity. Use PDF3 as the presentation reference and the agreed flight/dock alignment scene, not independent proportions inferred from different concept pictures.

**Provide:** permitted original source, reference images, current runtime mesh/rig audit, UE version, camera captures, socket naming and the shared ship alignment scene. The current implementation record reports about 196,920 hero triangles, one 2K atlas and 52 joints; these are audit inputs, not target budgets. Verify them on the actual delivered source before quoting. Topology reduction alone does not solve fur/cloth/metal shading, tail construction, skin weights or grip contact.

**Quote separately:** (A1) material/topology and deformation diagnosis; (A2) accepted head/body/tail sample in UE; (A3) complete runtime mesh/rig; (A4) pilot/exit sample; (A5) locomotion and interaction/reaction set. Preserve a source high-resolution master for rebaking.

**Deliver:** editable DCC files, textures/bakes and material masks, skeletal export, skeleton/weight documentation, agreed LODs, physics asset guidance, animation clips with names/rates/root-motion policy, reference pose and tested import instructions. Animation list: idle, walk/run, starts/stops/turns as required by chosen blending, interact, pilot steering/lean, restrained reactions and board/disembark. Do not commission platforming/combat animation.

**Accept:** frame-by-frame hand/grip/foot/tail and shoulder checks in actual flight and station cameras; no foot slide, planted-contact drift, metallic fur or transition pops. Approval of a turntable does not approve the rig. Include revisions and source rights in the written contract; nothing is commissioned today.

### B. Two spacecraft: identity and technical handoff

**Brief:** refine the starter acorn craft first, then build a visually coherent agile/lower-hull alternative. Keep the pilot visible in the approved chase silhouette. Match metal/glass response and believable manufacturing detail without obscuring the survival route.

**Provide:** PDF4/7 and ship art, current ship source, shared rig alignment, seat/grips/tail volume, weapon/engine sockets, collision envelope, landing contacts and camera capture. Establish the fit before either artist finalizes cockpit or animation.

**Deliver:** one accepted starter before second-ship production; editable hard-surface source, UVs/bakes/PBR textures, separate canopy/interior where useful, socket/pivot diagram, optimized runtime assets and collision/LOD strategy. Provide a stable proxy so agent gameplay work can continue during modeling.

**Accept:** front/side/rear and continuous chase captures, steering/boost effects, pilot pose and exit clearance, shadow/material quality and measured cost. Do not pay for invisible internal detail at the expense of the rear silhouette. Weapon mounts only need geometry visible at the gameplay camera; functional fire effects matter more than elaborate hidden gun machinery.

### C. Station kit assembly and art direction

**Brief:** finish one compact industrial hub layout used at both station visits and adapt the same visual kit for the home hangar. The artist supplies a convincing place; the lead retains docking, save, economy and interaction authority.

**Provide:** locked deck/bay/corridor dimensions, interaction locations, character/ship alignment, service flow and PDF12-13/station art. Supply licensed kit only through permitted private collaborator access.

**Deliver:** sample repair/upgrade corner first, then shell, coherent lighting/material instances, signage, machinery/servicing setup, 1-2 NPC/vendor placements/loops, announcements hooks and optional story/reward detail. No expanded station archetype or sprawling exploration map.

**Accept:** walk from landing to required services and launch with both controls, stable rear camera, legible signs and 1-3 minute typical visit; profile the actual station with hero and UI. An exterior kit alone does not meet this brief.

### D. Sound and signature feedback

**Brief:** make weight, speed, contact, danger and reward audible in the short benchmark, then extend the palette across four hazards, two weapons, stations and climaxes.

**Provide:** normal gameplay clips, actual event/parameter list, priority rules and reference direction; no need for a large finished cinematic. Commission a small timed sample before a complete library.

**Deliver:** dry source and runtime-ready files, loops with start/sustain/end where appropriate, alternate intensity layers, loudness/peak notes, event map, warning priority/concurrency guidance and adaptive score stems. Verify rights for music and any voice recordings, including contractor source material.

**Accept:** listen in active play on headphones and speakers; warnings remain directional/distinguishable, engine does not become tiring, laser/cannon differ, transitions crossfade and reward cues are clear. More volume is not the acceptance criterion. Agent integrates state control, mixing and performance hooks.

## Handoff card used by every contributor

Record WBS ID; objective; authoritative references; exact input revision; included/excluded work; dependency contract; files owned; proposed performance budget; review sample; editable-source requirements; runtime deliverables; rights/provenance; acceptance scene; validation evidence; known issues; revision/approval owner. Request quotes for that packet rather than “make the game look AAA.”

Performance budgets are agreed after the G1 profile, not guessed from triangle counts alone. Measure on-screen size, material slots, shader/overdraw cost, texture memory, bone/deformation cost, collision and total scene load. The first milestone is a working sample at the intended view and speed; only then commit to the complete asset family.
