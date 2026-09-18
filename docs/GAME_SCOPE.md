# SpaceSurvival

## Game Scope and Phase 1 Implementation Specification

**Status:** Initial game direction locked for Phase 1  
**Engine:** Unreal Engine 5  
**Primary platform:** Windows PC, with Steam as the intended commercial destination  
**Phase 1 objective:** Near-alpha-quality 10-wave vertical slice that can become the foundation of the full game

---

# 1. Game Identity

SpaceSurvival is a third-person 3D space survival game built around the psychological loop of wave-based survival games such as Zombies:

**How long can I survive, how strong can I make my build, and can I beat my previous run?**

The player controls Acornaut piloting an advanced acorn spacecraft through continuously changing space.

The game should not feel like a sequence of isolated asteroid levels, combat arenas, minigames, or missions.

It should feel like **one uninterrupted journey through increasingly hostile space**.

Asteroids arrive. Enemy ships interfere. A storm develops. A gravity anomaly changes flight behavior. The player survives, collects credits, finds opportunities, upgrades the ship, and keeps moving.

The player should frequently feel uncertain about what will happen next.

The central fantasy is:

> Survive an unpredictable universe long enough to build an increasingly capable spacecraft, knowing that eventually the universe will overwhelm you.

---

# 2. Core Game Pillars

## Continuous survival

The player is always fundamentally doing one thing:

**Stay alive.**

Waves organize progression and difficulty, but should minimally interrupt the continuous-flight illusion.

Environmental hazards, enemies, events, pickups, merchants, anomalies and opportunities enter and leave the journey naturally.

## Escalating survival pressure

Higher waves become harder through multiple dimensions:

- faster hazards
- denser hazards
- increasing collision damage
- stronger environmental forces
- new hazard families
- additional enemy archetypes
- more intelligent combinations
- shorter reaction windows
- overlapping pressures
- increasingly dangerous Director compositions

Late-game difficulty should not rely primarily on enormous enemy health pools.

## Build progression

Survival requires the ship to improve.

A ship capable of surviving Wave 1 should eventually become dangerously underpowered.

For example, an unupgraded hull might survive several major early collisions but become vulnerable to one-hit destruction around significantly later waves.

Likewise, inadequate thrusters or engines should eventually make certain high-speed fields extremely difficult to navigate.

The player is therefore racing both the environment and their own progression curve.

## Unpredictability with fairness

The player should not know exactly what combination is coming next.

However, unpredictable should not mean procedurally unfair.

The Survival Director should prevent obviously impossible combinations, unavoidable hits, unreadable visual overload and hazard spawning directly on the player.

Target feeling:

**Brutal sometimes. Unfair rarely.**

---

# 3. Run Structure

A run starts from the player's home hangar.

The player chooses:

- unlocked ship
- one starting weapon

Higher-level ships may eventually support one starting utility/module slot.

The player launches and begins Wave 1.

A normal run follows:

**Survival → credits/rewards → upgrades/opportunities → increasing danger → fifth-wave climax → station → launch → harder survival → repeat until death.**

There is no formal final wave.

The run continues indefinitely.

Major milestone waves can provide achievements, account progression rewards, ships, cosmetics or other prestige unlocks, but they do not end the run.

Highest wave reached remains the game's primary prestige measure.

---

# 4. Waves

Normal waves use survival duration rather than kill counts or finish lines.

The player does not see a countdown timer.

Early waves trend shorter. Later waves trend longer, but duration remains variable.

Internally, the Director controls wave duration within tuned ranges.

The player should not think:

> 12 seconds left.

They should think:

> Keep surviving.

A wave may end naturally as pressure diminishes rather than feeling mechanically terminated.

## Between-wave breathing windows

Normal wave transitions provide brief reductions in pressure while flight continues.

Typical downtime should be short.

Maximum downtime should generally remain around **20 seconds**.

These windows may contain:

- credits
- repairs
- shield pickups
- unusual signals
- merchants
- event announcements
- atmospheric foreshadowing

There is no long-term parking outside actual stations.

## Fifth-wave cadence

Every fifth wave is a guaranteed climax.

Wave 5, 10, 15, 20, etc. should feel important.

The type of climax varies, but reaching it should create anticipation.

Successfully completing the fifth-wave climax leads to a guaranteed major station checkpoint.

---

# 5. Survival Director

The Survival Director is one of the central systems of the game.

Each wave receives a hidden pressure budget.

The Director can spend that budget across variables such as:

- asteroid density
- asteroid velocity
- enemy pressure
- enemy composition
- environmental intensity
- visibility
- hazard overlap
- elite presence
- event frequency
- reaction windows

Two waves at the same numerical level can therefore be comparably difficult while feeling very different.

## Director progression

The Director's toolkit expands as wave level increases.

Early waves use:

- simpler hazards
- fewer overlaps
- smaller enemy groups
- fewer event possibilities

Later waves unlock:

- stronger hazard variants
- additional environmental systems
- more complex enemy combinations
- elite threats
- compound hazards
- persistent environmental events
- rare catastrophic events

Randomness remains throughout the run.

Later waves simply have a much larger possibility space.

## Hazard persistence

Most hazards resolve within their current wave.

Some can persist across wave boundaries, including:

- storms
- nebula effects
- gravity anomalies
- wreckage regions
- enemy pursuit
- major environmental conditions

Wave transitions should not magically reset the universe.

---

# 6. Flight Model

The target is:

**Arcade responsiveness with spacecraft weight.**

The player should have responsive enough controls to survive fast asteroid sequences while still feeling inertia, banking and momentum.

The game should not feel like either a cursor flying through space or a hardcore spacecraft simulator.

## Core flight capabilities

The flight system supports:

- pitch
- yaw
- banking
- throttle
- boost
- partial braking
- directional dodge
- momentum/inertia
- contextual maneuvering

Normal traversal has strong forward momentum.

**Inside a wave**, the player should be progressing through space rather than freely parking or backtracking.

**Inside the station zone** (see Zones, below), the ship may slow to a stop. That is not a second flight
model - it is the same model with the wave's speed floor lifted, because there is nothing to survive there
and because a ship that must always cruise cannot be landed on a pad.

There should not be a visible switch between "forward survival mode" and "combat mode."

The environment should naturally determine how the player uses the same flight model. The station zone is the
one place the rules themselves differ, and it is meant to read as arriving somewhere rather than as a mode
being announced.

Dense asteroids encourage forward weaving.

Combat opens maneuvering opportunities.

Gravity anomalies alter the flight envelope.

Wormholes pull the ship into different situations.

Everything should blend seamlessly.

## Boost

Boost uses a rechargeable meter.

It drains while active and regenerates automatically.

Future upgrades may improve capacity, efficiency or recharge speed.

## Brake

Braking provides meaningful partial deceleration rather than allowing the player to stop indefinitely.

Using the brake generates heat.

Continuous braking eventually overheats or weakens the braking system until it cools.

This prevents players from defeating high-speed survival by crawling through space.

That rule exists to protect survival, so it applies where survival is happening. Inside the station zone the
ship may hold station or stop, because crawling there defeats nothing.

## Dodge

A dedicated directional dodge produces a sharp movement burst.

There are **no invulnerability frames** in the base implementation.

Dodging into an obstacle still causes damage.

---

# 6b. Zones

A run alternates between two zones. Same ship, same controls, different rules.

**Wave zone.** Survival. Forward momentum, the Director active, the brake-heat rule in force.

**Station zone.** A large free-roam bubble around a station, entered when a fifth-wave climax is completed.
Inside it the ship may slow or stop, there is no survival pressure, and docking, landing and launching happen.

Leaving the station zone is what starts the next block. The next wave begins because the player flew out,
not because a timer expired.

Normal (non-fifth) wave transitions are unchanged: brief breathing windows, flight continues, no parking.
The station zone is a fifth-wave feature, not a between-every-wave one.

---

# 7. Camera

The default is a relatively tight third-person chase camera.

The spacecraft and Acornaut should remain visually prominent.

Limited dynamic camera behavior is allowed:

- modest pullback at very high speed
- slight widening during exceptionally dense hazards
- small adaptation during major combat encounters

Avoid dramatic mode-switching camera behavior.

---

# 8. Acornaut Presentation

Acornaut is visibly piloting the ship on open-cockpit hulls.

On a closed-canopy hull the pilot is not drawn in flight. Acornaut is then seen on the landing pad, walking
the station, and in hangars and cinematics. This is a deliberate consequence of the hull roster carrying
closed-cockpit ships, not an omission.

Match the approved Hybrid concept direction:

- on open hulls, Acornaut's head/body/tail silhouette remains visible
- the spacecraft remains the dominant gameplay object
- Acornaut is more prominent in stations, hangars and cinematics

A high-quality rigged Acornaut source asset is available separately and should be integrated rather than unnecessarily recreated if supplied to the implementation environment.

Acornaut has light reactive personality.

Use occasional short reactions to:

- critical damage
- rare rewards
- major anomalies
- elite enemies
- close calls
- station arrival
- unusual events

Avoid constant chatter.

---

# 9. Damage and Survival

The player has two primary durability layers:

## Shield

Shield is a conventional health meter above hull health.

Damage normally drains shield first.

Shield:

- does not automatically regenerate
- is replenished through relatively rare pickups
- can be repaired at stations/depots
- gains increased capacity through upgrades

Shield pickups should be valuable enough that players may intentionally risk dangerous routes to collect them.

## Hull / Health

Hull health can naturally regenerate to 100%.

Regeneration is contextual:

**Out of danger:** after a delay, regeneration becomes relatively fast.

**During active danger:** regeneration remains possible but is much slower.

Fresh damage can interrupt or reduce recovery.

## Damage scaling

Environmental and combat damage increases as waves progress.

This means defensive upgrades become necessary.

Collision response is mostly damage-based rather than constantly spinning the ship out of control.

However, later-wave impacts and hits against badly under-upgraded ships can cause more:

- deflection
- momentum loss
- control instability
- critical-system damage

## Damage-type differentiation

Use one core damage model with lightweight secondary behavior.

Examples:

**Kinetic**  
Normal shield/hull damage with possible knockback.

**Energy**  
Normal damage with heavier shield pressure.

**Electrical**  
Possible shield disruption or temporary subsystem interference.

**Gravity**  
Flight/control distortion.

**Thermal/plasma**  
Potential brief heat or damage-over-time effects.

Do not build a deep resistance spreadsheet.

## Critical subsystem damage

Subsystem damage is rare.

Severe impacts, elite attacks or special hazards can temporarily impair an upgraded system.

For example:

Thrusters IV may temporarily function closer to Thrusters II until repaired.

The purchased upgrade is not permanently lost.

---

# 10. Asteroids and Destruction

Asteroids have multiple scales.

**Small debris**  
Can usually be destroyed.

**Medium asteroids**  
Can be destroyed with sufficient weapon power.

**Massive asteroids**  
Function as environmental geometry and must be avoided.

Destroyed medium asteroids can produce controlled fragmentation.

Results can include:

- smaller dangerous debris
- credits
- temporary buffs
- repairs
- other useful pickups

Sometimes destroying an asteroid makes the situation worse.

That creates a meaningful decision between shooting and avoiding.

---

# 11. Combat

Weapons are contextual survival tools.

The game should not become continuous shooting.

Combat naturally appears inside survival.

The player may move through:

**dodge → shoot → evade → collect → survive**

without feeling that the game changed modes.

## Aiming

Use hybrid aiming:

- manual aim is always available
- nearby valid targets can receive soft-lock assistance
- assistance can become more useful during high-speed combat
- combat never becomes completely automatic

## Enemy scaling

Difficulty scales mostly through enemy behavior and composition rather than enormous health inflation.

A fighter remains recognizably a fighter even at high waves.

Later danger comes from:

- more dangerous archetypes
- stronger coordination
- higher speed
- more aggressive pursuit
- more accurate fire
- mixed formations
- elite variants
- environmental overlap

## Elite threats

Use rare elite threats rather than formal boss arenas.

Possible future examples include:

- capital ships
- elite fighter aces
- heavy alien ships
- large hostile drones
- environmental super-events

They stay integrated into survival.

---

# 12. Credits and Economy

Credits are the primary run currency.

They come from a combination of:

- surviving waves
- enemy kills
- pickups
- optional events
- contracts
- salvage
- risky actions

Survival provides a reliable baseline.

Aggressive/risky play produces significantly better income.

The economy should create tension between:

**play safely and potentially survive longer**

versus

**take risks and build power faster.**

Core upgrade pricing remains mostly predictable.

Situational vendors, factions and events can alter prices or provide special deals.

---

# 13. Core Ship Upgrades

Five primary upgrade tracks exist:

- Hull
- Shield
- Engine
- Thrusters
- Weapon

Phase 1 uses **five tiers each: I–V**.

Core upgrade tiers are primarily purchased rather than randomly awarded.

The player should use credits earned during survival to make deliberate build decisions.

## System purpose

**Hull**  
Keeps increasingly strong impacts survivable.

**Shield**  
Adds expendable protection.

**Engine**  
Improves acceleration, forward capability and resilience against movement pressure.

**Thrusters**  
Improve maneuverability and response.

**Weapon**  
Improves combat capability and destructible-hazard handling.

Upgrade gating must be soft rather than binary.

A highly skilled pilot may survive with an under-upgraded ship.

The game should not secretly enforce requirements such as "Wave 12 requires Thrusters III."

---

# 14. Utilities

Core upgrades stack normally.

Special utilities use limited utility slots.

Utilities are **not randomly thrown at the player during active hazard sequences**.

Temporary buffs can be.

Utilities come from deliberate interactions:

- special events
- depots
- merchants
- station rewards
- contracts
- rare encounters

Reward structure varies by event quality.

Some events provide one known utility.

Higher-quality events may offer several choices.

If a full inventory system is introduced later, utilities can be stored and equipped at stations.

Do not implement that inventory system in Phase 1.

---

# 15. Pickups

Phase 1 should initially prioritize gameplay readability over realism.

Pickups can use:

- bright visual effects
- recognizable icons
- strong silhouettes
- obvious differentiation

Later testing can determine how far presentation can move toward more diegetic objects without hurting high-speed readability.

Pickup placement follows risk/value logic:

- common resources can appear naturally
- stronger rewards appear in more dangerous positions
- rare opportunities often require deliberately leaving the safest line

---

# 16. Special Events

Optional events are clearly announced.

Use:

- explicit HUD marker
- event label
- direction/distance
- clear interaction point

Optional events require explicit acceptance.

The player can approach without being involuntarily committed.

Early/mid-game events generally appear during lighter pressure.

Later waves can introduce them during active danger.

Events can vary in duration:

- short event within one wave
- multi-wave event
- contract-style event lasting until the next station

Reward quality scales with event difficulty/rarity.

Phase 1 special event rewards include utilities and rare weapon replacement opportunities.

---

# 17. Stations

Every fifth-wave climax leads to a guaranteed station.

The player:

1. approaches manually, **from any direction** - there is no required corridor, lane or heading
2. gets close to a landing pad, slowly enough that a landing is plausible, and is offered docking
3. **presses a button to engage it** - docking is never automatic
4. the ship slows to a hover over the pad, then lowers onto it as the landing gear opens
5. on contact the rear door opens, Acornaut stands, and control returns
6. walks out onto the pad and into the station, and accesses its services
7. launches: door shuts, gear stows, the ship lifts off the pad, control returns
8. flies clear of the station zone, which begins the next block

Steps 2-7 are the same at every landing pad in the game, now and later. A pad carries its own dock point and
approach volume; the sequence is written against pads rather than against any one station.

Approach is gated on **proximity and speed**, not on angle. A ship cannot dock at full thrust.

## Station gameplay

Stations are compact 3D hubs.

Typical visit duration: approximately 1–3 minutes.

Acornaut uses simplified third-person controls:

- walk
- run
- interact

No station combat, platforming or complex traversal.

## Station interaction

Interactions should be primarily diegetic.

Examples:

- physical repair console
- upgrade terminal
- contract board
- save terminal
- vendor
- launch control

Avoid replacing the entire station with one generic floating menu.

## Guaranteed services

Every major station provides:

- Hull upgrade
- Shield upgrade
- Engine upgrade
- Thruster upgrade
- Weapon upgrade
- repair
- Save & Quit
- contract access
- relaunch

Special inventory varies.

Stations should feel lived-in with:

- NPCs
- machinery
- ship servicing
- ambient announcements
- environmental details
- faction visual flavor

Factions remain mostly flavor for now rather than a reputation/diplomacy system.

---

# 18. Save and Death Rules

Station saves are **suspend/resume only**.

The player can save a live run and quit.

On return, the run resumes.

If the player later dies, the run is over.

The station cannot be repeatedly reloaded after death.

Normally:

**Hull reaches zero → run ends.**

Rare future utilities/perks may create one-time exceptions such as emergency survival effects.

---

# 19. Mobile Depots and Merchants

Friendly ships or mobile depots can occasionally appear during survival.

They offer:

- random subset of the five core upgrade families
- special variants
- unusual deals
- variable services

They do not replace guaranteed stations.

Phase 1 guarantees exactly **one mobile depot encounter** so the system can be evaluated.

The full game later uses randomized appearances.

---

# 20. Contracts

Contracts are accepted at stations.

Early account progression allows **one active contract**.

Higher player levels can eventually unlock the ability to hold one major + one minor contract.

Contracts can combine:

- objectives
- difficulty modifiers
- reward multipliers
- encounter changes

Failure behavior depends on contract type.

Standard contracts may simply lose their reward.

High-risk contracts can declare explicit penalties before acceptance.

---

# 21. Permanent Progression

Death removes run-specific upgrades.

Account-level progression persists.

The permanent progression philosophy is primarily:

**unlock more possibilities rather than permanently trivialize the game.**

Persistent unlocks can include:

- ships
- weapons
- utilities
- upgrade families
- contracts
- cosmetic content
- rare artifact pools
- starting options

Higher-level ships may have meaningful advantages.

For example:

- slightly faster chassis
- more starting health
- different handling
- utility slot

But no unlock should turn Waves 1–20 into autopilot.

Most end-run power still needs to be earned during that run.

## Starting configuration

Early ships:

- Ship
- 1 starting weapon

Higher-level ships may eventually support:

- Ship
- 1 starting weapon
- 1 utility slot

---

# 22. Score and XP

Use two parallel run performance measures.

## Primary prestige

**Highest wave reached**

This is the number players should immediately understand and compare.

## Secondary score

Composite performance score can incorporate:

- kills
- contracts
- credits
- salvage
- elite threats
- risk bonuses
- optional challenges

## Account XP

Account XP is hybrid:

- wave progression supplies reliable XP
- strong performance accelerates XP gain

---

# 23. Home Hangar

After death, the player returns to a compact home hangar.

The hangar contains:

- ship selection
- starting weapon selection
- account progression
- unlocks
- run history
- highest-wave information
- cosmetics
- launch

Interaction is hybrid/diegetic:

- ship selection at ship bay
- weapons at rack/loadout point
- progression at terminal
- launch at spacecraft

Repeat-player shortcuts can reduce unnecessary walking.

---

# 24. Regions and Space Presentation

Space visually transitions through distinct regions, but:

- region changes are gradual
- they are not tied to station cadence
- they are not tied to wave blocks
- there is no fixed path
- the same region type may appear differently across runs

For now, regions are primarily visual.

They should not introduce strong biome-specific gameplay rules.

The Survival Director controls gameplay hazard composition independently.

---

# 25. Full-Game Environmental Families

The full design should support expansion into environmental families such as:

- asteroids
- wreckage fields
- electrical/ion storms
- nebulae
- gravity anomalies
- black-hole-class events
- artificial mine/defense fields
- stellar/solar events
- comets/high-velocity objects
- large structures and derelicts

Each family should scale internally through:

- intensity
- speed
- density
- frequency
- duration
- secondary effects
- overlap potential

More dangerous variants unlock at later waves.

Late-game hazards should develop recognizable reputations among players—for example, a severe lightning event becoming something players dread once they reach deep runs.

---

# 26. Visual Direction

Use the approved **Hybrid** visual direction.

The target combines:

- realistic materials
- cinematic lighting
- high-quality space VFX
- convincing scale
- readable gameplay silhouettes
- intentionally visible hazards
- clear pickups
- commercial polish

The visual target should favor gameplay readability when realism and readability conflict.

Phase 1 should aim for strong visual fidelity immediately rather than relying on gray-box presentation.

## Asset strategy

Use custom/game-specific assets for important identity elements:

- Acornaut
- hero acorn spacecraft
- HUD
- signature pickups
- utilities
- defining VFX

High-quality compatible external assets may be used for secondary environment content where licensing permits:

- asteroids
- debris
- station dressing
- structures
- props

Everything must be visually normalized through lighting, materials, scale and art direction.

The game must not resemble an unrelated collection of asset packs.

---

# 27. HUD

Use moderate HUD density.

Persistent information includes:

- wave
- hull health
- shield
- boost
- weapon
- credits
- target/soft-lock indicator

Contextual information includes:

- pickups
- event markers
- contract progress
- subsystem warnings
- major hazard warnings
- docking guidance

## Radar

Normally keep threat indicators minimal.

During combat/high-threat conditions, a compact contextual radar can appear or expand.

## Warnings

Use hybrid warning communication:

- directional visual indicator
- spatial audio
- explicit alarms for severe threats

Do not create constant warning spam.

---

# 28. Audio and Music

World audio should be cinematic.

Gameplay-critical reward feedback can remain more arcade-readable.

Use:

- heavy engine audio
- strong impacts
- convincing weapons
- atmospheric environmental audio
- clear pickup/reward sounds
- distinctive warnings

Music is adaptive and layered.

A persistent low-level score gains layers as pressure increases and strips back during breathing windows.

Stations and the home hangar provide decompression through different musical treatment.

---

# 29. Narrative

Use a light lore layer rather than a campaign.

Delivery methods include:

- environmental storytelling
- station chatter
- brief NPC conversations
- station announcements
- logs/messages
- ship/item descriptions
- Acornaut reactions

Avoid long dialogue trees and major campaign dependencies in Phase 1.

---

# 30. Difficulty Philosophy

Launch around one canonical survival mode.

Do not create Easy / Normal / Hard variants initially.

Future challenge variants can introduce special rules such as:

- Hardcore
- No Shields
- increased hazard density
- elite-heavy survival
- other modifier modes

This keeps main-mode wave records comparable.

---

# 31. Procedural Generation

Use a hybrid procedural strategy.

Procedural systems handle:

- broad space distribution
- debris
- background environment
- weather
- general traversal
- Director composition

Authored chunks handle situations where quality/readability matters:

- dangerous asteroid arrangements
- wreckage passages
- major structures
- stations
- special encounters
- climax setups

The player should not perceive obvious tiled chunks.

No explicit seeded-run system is required for Phase 1.

---

# 32. Tutorial

Use a hybrid tutorial.

Begin with a very short control introduction.

Then teach through the actual first run.

Suggested progression:

**Initial launch**  
Steering, throttle, brake, boost, dodge.

**Wave 1**  
Asteroid avoidance, health/shield basics, pickups.

**Wave 2**  
Weapons, destructible debris, credits.

**Wave 3**  
Enemies, soft-lock aiming, upgrades/opportunities.

Tutorial prompts disappear once learned and can be reset/replayed later.

---

# 33. Phase 1 — Exact Content Scope

Phase 1 is a **10-wave near-alpha vertical slice**.

It must prove the full loop twice.

## Waves 1–5

Progressively escalating survival.

### Wave 5 authored climax

**Wormhole pull → hostile combat → station**

The wormhole should emerge naturally from survival.

The player is drawn through.

A hostile combat sequence follows.

Survival leads into the first major station.

## Station 1

Full Phase 1 station experience.

Player repairs, upgrades, interacts, potentially selects a contract, saves/quits if desired, and relaunches.

## Waves 6–10

Stronger survival pressure, upgraded Director compositions and more aggressive enemy/hazard combinations.

### Wave 10 Director compound climax

**Gravity anomaly + asteroid storm + enemy pressure**

This tests several systems interacting simultaneously.

The result must be chaotic but fair.

Completion leads to Station 2.

---

# 34. Phase 1 Hazard Roster

Implement exactly four core hazard families:

1. Asteroids
2. Wreckage/debris
3. Electrical storm
4. Gravity anomaly

The architecture must support adding the broader hazard library later without rewriting the Director.

---

# 35. Phase 1 Enemy Roster

Implement exactly two enemy archetypes:

## Pursuer
Aggressively closes distance and applies direct pressure.

## Flanker
Uses wider approach paths and forces the player to divide attention.

Do not implement a broader enemy library in Phase 1.

---

# 36. Phase 1 Weapons

One active weapon slot.

Implement two weapon classes:

## Rapid Laser
Fast, forgiving weapon effective against fighters and small debris.

## Heavy Cannon
Slower, heavier weapon better against medium asteroids and heavier targets.

Weapons can be upgraded through Weapon I–V or replaced when appropriate.

---

# 37. Phase 1 Utilities

Implement exactly two utilities:

## Vector Thrusters
Improves lateral/vertical movement authority and maneuverability under hazard pressure.

## Overdrive Cooling
Improves boost/brake heat management and emergency sustained maneuvering.

Utilities are obtained through deliberate event/depot/station interactions, not surprise hazard pickups.

---

# 38. Phase 1 Optional Events

Implement exactly two non-climax event types.

## Salvage Cache Event
Optional dangerous diversion through debris/wreckage for a meaningful reward.

## Distress / Combat Event
Optional combat challenge producing a higher-quality reward.

Events require explicit acceptance.

Reward pools may include:

- utilities
- rare weapon replacement

---

# 39. Phase 1 Contracts

Implement exactly two contract types:

## Difficulty-modifier contract
Example structure: reduced shields or another survival handicap in exchange for increased reward.

## Objective contract
Example structure: destroy a specified number of enemies or collect a target resource before the next station.

---

# 40. Phase 1 Mobile Depot

Guarantee exactly one mobile depot/friendly merchant encounter during the first 10-wave experience so the mechanic can be evaluated.

It offers:

- random subset of core upgrades
- special variants/deals

Full-game appearance becomes randomized later.

---

# 41. Phase 1 Economy

A competent run should generally allow approximately **2–3 meaningful purchases per major station**.

Economy should force prioritization without starving progression.

Repair availability is moderate:

- mistakes can be recovered from
- repeated poor play compounds
- stations remain reliable recovery points

---

# 42. Phase 1 Ships and Permanent Progression

Implement real XP/account progression.

After death:

- calculate XP
- increase account progression
- show unlock progression
- return to hangar

Early progression should prove two unlock categories:

1. second starting weapon option
2. second spacecraft

## Ship roster

Ships are data. Each hull declares its own size, collision, framing, handling and tolerances, and every gate
reads those rather than assuming one base model. Adding a ship is a data row, not a rewrite, and a hull that
fails to declare a value fails loudly rather than inheriting another ship's numbers.

Bigger hulls may be less agile. That is a property of the hull, not an exception to the flight model.

## Second ship

The first unlockable ship is faster and more agile than the starter ship:

- higher base speed
- stronger maneuvering
- quicker response
- slightly lower starting hull

It represents a different playstyle rather than a pure upgrade.

---

# 43. Phase 1 Station

Station should exceed a bare prototype.

Include:

- full repair
- five core upgrade paths
- contract board
- Save & Quit
- launch
- 1–2 NPC/vendor interactions
- visible ship servicing
- ambient machinery
- announcements/audio
- small amount of environmental storytelling
- one optional side interaction/reward point

Keep footprint compact.

---

# 44. Phase 1 Game Shell

The build should include a proper near-alpha PC shell:

- Continue suspended run
- New Run
- Hangar
- Settings
- Graphics
- Audio
- keyboard/controller controls
- run stats/progression
- Quit

Basic accessibility:

- subtitles
- UI scale
- pickup/warning differentiation that does not rely only on color
- camera shake toggle
- motion blur toggle
- hold/toggle behavior where relevant

---

# 45. Input

Support both from Phase 1:

- keyboard + mouse
- controller

Both must expose the same gameplay capabilities.

Tune input response independently where appropriate rather than forcing identical sensitivity behavior.

---

# 46. Performance

PC-first.

Target:

**60 FPS minimum acceptable gameplay baseline**

Architecture/settings should allow capable hardware to reach **120+ FPS**.

Core simulation, flight and input must be frame-rate independent.

When performance must scale down, preserve:

1. gameplay simulation
2. responsiveness
3. hazard readability

before visual excess.

---

# 47. Saves

Phase 1 saves are local-first.

Separate:

- account progression
- player settings
- suspended run state

Architecture should allow cloud synchronization later.

No online connection is required to play.

---

# 48. Online / Multiplayer Future

Phase 1 is strictly single-player.

Do not implement networking.

Architecture should avoid unnecessary assumptions that make future 2–4 player co-op prohibitively expensive.

Potential future online features:

- cloud saves
- highest-wave leaderboard
- highest-score leaderboard
- challenges/events
- eventual co-op

The full game should remain playable offline.

---

# 49. Unreal Architecture

Use **Unreal Engine 5**.

Use a hybrid implementation.

## C++ owns durable systems

Examples:

- flight model
- Survival Director
- wave state
- damage
- shield/health
- boost
- brake
- dodge
- run state
- account progression
- save/resume
- upgrade framework
- event framework
- contract framework
- enemy-system foundations

## Blueprints / Data Assets own tunable content

Examples:

- hazards
- wave-pressure values
- enemy archetype tuning
- encounter chunks
- pickup definitions
- contracts
- station content
- utilities
- VFX hooks
- audio hooks
- environmental visuals

The architecture should allow designers/agents to tune gameplay without rewriting core C++.

---

# 50. Phase 1 Explicit Deferrals

Do **not** implement:

- multiplayer networking
- Steamworks
- cloud saves
- online leaderboards
- faction reputation/diplomacy
- inventory/storage system
- full environmental hazard library
- additional enemy archetypes
- more than two weapon classes
- more than two utilities
- more than two optional event types
- additional station archetypes
- extensive narrative systems
- full accessibility suite
- challenge modes
- large authored progression beyond Wave 10

These systems may be documented architecturally where useful.

They should not consume Phase 1 implementation effort.

If core Phase 1 finishes early, effort goes into:

- polish
- game feel
- bug fixing
- performance
- balancing
- animation
- VFX/audio
- QA
- documentation

—not scope expansion.

---

# 51. Implementation Discretion

Codex has limited creative discretion.

It may:

- resolve minor implementation gaps
- improve transitions
- improve VFX/audio/animation
- add necessary polish
- choose technically sound low-level architecture
- make small coherence improvements

It may not silently:

- redesign the core loop
- introduce major mechanics
- change the progression philosophy
- alter the every-five-wave station cadence
- replace established systems
- expand Phase 1 into Phase 2

Any material deviation must be documented.

---

# 52. Phase 1 Quality Bar

The target is **near-alpha quality**, not a proof-of-concept.

The build should demonstrate:

- compelling flight
- readable hazards
- satisfying survival pressure
- coherent upgrade economy
- meaningful progression
- convincing station cadence
- polished Hybrid visual direction
- strong audio/VFX feedback
- stable game shell
- limited obvious bugs
- usable performance
- coherent architecture

Core gameplay must not rely on obvious placeholder behavior.

Secondary assets may remain replaceable.

---

# 53. Definition of Done

Phase 1 is not complete merely because source code exists.

Completion requires:

- Unreal project opens and builds cleanly
- complete Waves 1–10 flow works
- Wave 5 climax works
- Station 1 works
- Waves 6–10 work
- Wave 10 compound climax works
- Station 2 works
- keyboard/mouse validated
- controller validated
- both weapons validated
- both enemies validated
- four hazard families validated
- mobile depot validated
- two optional events validated
- two contracts validated
- five upgrade trees functional through intended Phase 1 progression
- utilities functional
- save/resume tested
- death correctly ends the run
- death → XP → unlock → hangar → next run tested
- second weapon unlock tested
- second ship unlock tested
- packaged Windows build produced
- performance reviewed against the 60 FPS baseline
- major known bugs documented
- no deferred Phase 2 systems quietly introduced

---

# 54. Required Codex Delivery Package

Codex must return:

**Complete Unreal source project**

**Packaged Windows build**

**Validated core gameplay**

**Clean implementation branch / PR**

**PROJECT_STATE.md**

**Architecture documentation**

**Known Issues / Limitations**

**Phase 2 Integration Notes**

**Build/run instructions**

**Testing record covering:**

- keyboard/mouse
- controller
- full 10-wave run
- station flow
- save/resume
- death
- account XP
- unlocks
- restart loop
- performance

The implementation should be treated as the intended foundation for continued game development rather than disposable prototype code.

---

# 55. Phase 1 Success Test

The decisive test is not simply:

> Does it run?

It is:

> Does completing a run—or dying during one—make the player want to immediately launch again?

SpaceSurvival Phase 1 succeeds when the combination of unpredictable survival, ship handling, progressive difficulty, credit collection, upgrades, events, stations and permanent unlock progression already creates that loop.
