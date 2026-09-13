# Phase 2 integration notes

This is an extension assessment of the current source, not a Phase 2 implementation or a declaration that Phase 1 is complete. The existing Unreal build/import, integrated gameplay, input, save-relaunch, presentation and performance gates must be closed before expanding content. `GAME_SCOPE.md` defines both the intended future and the explicit Phase 1 deferrals.

## Preserve the established loop

Keep one continuous survival journey, hidden wave duration, short breathing windows, a climax and station every fifth wave, deliberate core-upgrade purchases, non-regenerating shield and death-ended runs. Permanent progression should continue unlocking choices rather than making early survival automatic. Added content must fit the Director's budget/readability and shared damage/flight rules.

The current Phase 1 endpoint is an active run at Station 2. `Session::AtSliceBoundary`, `LaunchFromStation`, `ValidateRun`, `DecodeAccount`, Director wave clamps and contract eligibility explicitly assume Waves 1–10. Supporting ongoing waves requires a coordinated change to those rules, codecs/tests, wave/climax definitions and shell wording. Simply enabling the disabled launch menu item would create unsupported state.

## Extension points and work still required

| Future area | Reusable current boundary | Required later integration; not implemented now |
| --- | --- | --- |
| Additional hazards, structures and regions | `ASSWorldBody` weapon/contact contract, bounded external forces, Director admission and lifetimes | Replace `ESSWorldKind` switch-based construction with data definitions/class references, cost/eligibility rules and presentation assets. Extend warning/readability policy and combinations before adding new families |
| Additional enemies and elites | `ASSEnemy`, physical projectiles, shared obstacle interaction and event-objective callbacks | Introduce archetype definitions and behavior policies; spawn classes are currently native. Preserve committed telegraphs and behavior/composition scaling rather than only adding health |
| Additional weapons | One active `SS::Weapon`, `Session::Stats`, `ASSShip::Fire`, target eligibility and `ASSProjectile` | Introduce weapon definitions/firing strategies, declared replacements and validated serialization identities. Existing laser/cannon logic is a native branch, not a plug-in weapon catalog |
| Utilities | One `SS::Utility` slot, explicit equip/replacement and effective-stat composition | Add definitions/effect policies and disclosed slot behavior; current utilities are enum branches. Keep deliberate reward/equip flow and avoid turning temporary pickups into surprise modules |
| Optional events | `ASSEncounterBeacon` acceptance, proximity, objective registration/timeout and pending reward | Introduce encounter definitions/classes and objective interfaces. Current salvage/distress construction, timing and reward menu are native. Generalize without weakening explicit acceptance or rewarding proximity alone |
| Contracts | Domain acceptance, one active contract, progress/resolve boundary and station board | Add contract definitions and explicit modifier/reward/failure terms; current code only supports pressure/objective contracts accepted at Station 1. Additional simultaneous contracts require new state and UI, not more enum values alone |
| Merchants and station content | Depot subset/proximity validation; `ASSStation` service lookup; common panels | Move offer policy and hub layout to authored data/Blueprint content. Current depot guarantee is specifically tied to the Wave 3 breathing window; a later randomized policy must replace that guarantee intentionally |
| Account unlocks and ships | `Account`, XP-derived level, `StartRun` lock checks and per-run effective stats | Replace fixed level checks/native ship multipliers with a migration-safe unlock catalog and selectable definitions. Preserve reset behavior and run-earned power |
| Challenge modes | A canonical `SS::Tuning`, `PressureMultiplier`, reset and score calculation | Add explicit ruleset identity and dedicated stat/save/record provenance. Do not silently mutate canonical difficulty or mix incompatible high-wave records |
| Inventory/storage | Current explicit utility/weapon replacement and one-slot run state | Design a new bounded inventory domain, item identity, persistence and station equip UI. There is no hidden inventory implementation to activate |
| Richer presentation, animation and audio | Material parameters, source/import path contract, supplied skeletal asset, separate audio components | Author production mesh/texture/LOD assets, animation states/poses, VFX and mix curves. Canvas HUD, fixed native labels and raw wave layers are current implementations, not finished widget/animation/audio middleware systems |
| Steam, cloud and online records | `USSGameInstance` owns local storage; payload codecs do not depend on a service | Add service adapters after entitlement/privacy/offline/conflict decisions. No Steamworks SDK, cloud calls, online identity or leaderboard backend exists |
| Eventual co-op | Engine-independent rules, world-body interfaces and separate presentation owners | Substantial authority/session/input/save redesign is required. Single-player assumptions are explicit throughout; networking is not presently implemented |

## Data and content evolution

The existing `USSPhase1Data` is a practical tuning seam for a subset of Phase 1 settings. It is not yet a complete hazard/enemy/weapon/event registry. A later content definition should include stable identity, eligibility, cost, class/asset references, collision/presentation scale, warnings and validation constraints appropriate to its type. Preserve shared admission logic instead of letting every new actor bypass reaction distance, clearance, field separation or capacity checks.

Native `SpawnActor<...>` calls and hardcoded asset paths currently construct the world. Supporting designer-authored subclasses requires explicit class references/factories and a verified cook/reference strategy. Several actors are Blueprintable and some configuration methods are BlueprintCallable, but those annotations alone do not cause the current Director to instantiate a Blueprint subclass. Avoid claiming content can already be added without touching C++.

Move production layout/presentation authoring toward Blueprint/Data Asset content while preserving current ownership: the session owns outcomes, the Director owns admission/composition, encounter actors own live objective execution, and UI presents choices. A station art replacement should not acquire responsibility for XP or save consumption. A new projectile presentation should not bypass common damage/target logic.

The source generators establish reproducible provisional assets and canonical import paths. Replacing those assets in place can preserve callers, but class/type/material-slot and collision assumptions must still be checked. `AuthorContent.py` preserves existing authored assets on rerun and rejects partial initial imports; use deliberate Editor reimport/migration for later production content instead of bulk deletion.

## Save evolution and account safety

Version 1 uses fixed text field order, numeric enum values, exact headers and bounded validation. It rejects unknown versions and unexpected data. Keep versioned migration functions and fixtures when extending fields/identities; do not change field order or enum numbering and expect old suspensions to decode safely. Broader wave ranges also require revisiting highest-wave and station/contract invariants in account/run validation.

Retain separate account, settings and suspended-run domains. Current station suspension contains logical run state and pending rewards, not a serialized actor scene. If future content introduces objectives that can survive docking or multiple visited hubs, define what persists explicitly before attempting to store arbitrary actor pointers.

Maintain consume-before-play semantics: successfully validate the candidate suspension, durably mark it consumed, then expose the run. Preserve the awarded-run marker so an interrupted death-persistence sequence cannot reopen the same completed run. `Session::EndRun` is idempotent for the recorded run ID; storage idempotency is a separate adapter responsibility.

The current adapter uses synchronous Unreal SaveGame writes plus readback and separate calls for account/tombstone updates. It does not provide an atomic transaction across domains, history of every awarded ID, automatic backups or multi-device conflict resolution. Future cloud integration needs generation/revision metadata, conflict policy and safe handling of stale suspended-run copies. A simple file upload/download wrapper would not preserve the local death/consumption rule under conflicting devices.

Account read failures currently block overwrites and new progression instead of silently replacing the account with defaults. Carry that protection into migrations and service error recovery. Settings can fall back independently; account data and an active run have different loss consequences. Fault-inject interruption after each write/consume stage and test process restart, corrupt/truncated payloads, full disk and denied access before advertising robust persistence.

## Multiplayer is a future architectural project

The current game has one `USSGameInstance::Session`, one active ship/walker, player index `0`, GameMode-local menus/announcements, per-client input polling, direct `GetAuthGameMode` lookups and no replicated state, RPCs or network prediction. Physics contacts, spawn randomness and world rebasing are authored for local play. The portable domain is reusable logic, not a synchronized multiplayer simulation.

Before future 2–4 player co-op, decide host/server authority for wave timing, Director spending, damage, rewards, contracts and suspension. Introduce explicit player/session identities and per-player durability/loadout/resource state. Separate shared encounter state from player account progression and local settings. Define whether station transitions are collective, how disconnect/rejoin behaves, who can suspend a session and how death-ended runs apply to a group.

Move client-visible shared state to appropriate replicated actors/state containers; keep authoritative mutations on the server. Add input prediction/reconciliation where necessary to preserve flight responsiveness, and test relative collision, projectile ownership and world-origin behavior under latency. Replace single-controller lookups in targeting, UI and world actors with an explicit set of participants. None of these network systems is included in Phase 1.

## Performance and validation sequence for expansion

Start by building/cooking/importing and playing the current ten-wave slice, including both inputs, both station visits, resumed death, unlocks and immediate restart. Measure CPU/GPU/frame time on the available Windows PC before content expansion. Source tests and Blender previews cannot establish Unreal frame rate or the motivation to replay.

Then profile bounded problem areas: targeting/radar/body iteration, enemy obstacle scans, gravity scans, actor creation/destruction, synchronous asset loads, station component construction, supplied hero geometry/LOD cost and rendering scalability. Introduce spatial queries, pooling, preloading or LOD work in response to measured bottlenecks. Preserve simulation/input and readable hazard warnings before increasing VFX density.

For each later system, add deterministic domain tests where rules can be isolated, Unreal integration tests where actors/storage are involved, and manual overlap scenarios where fairness/readability/feel are decisive. Particularly test new hazard combinations with upgraded and under-upgraded ships, controller input, reduced graphics/UI accessibility settings, station suspension and account unlock resets. The present native enum/branch architecture gives concrete refactoring points; it does not eliminate the work of extending them safely.
